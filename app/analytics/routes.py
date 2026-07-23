from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from app.core.database import db
from app.analytics.models import FocusSession
from app.tasks.models import Task
from app.projects.models import Project
from app.core.models import UserStatus
from app.ai.services import AIService
from app.auth.utils import login_required
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/', methods=['GET'])
@login_required
def index():
    u_id = session['user_id']
    today = datetime.utcnow()
    seven_days_ago = today - timedelta(days=7)

    # Filtrar sesiones pertenecientes a tareas del usuario
    sessions = FocusSession.query.join(Task).filter(
        Task.user_id == u_id,
        FocusSession.start_time >= seven_days_ago
    ).all()
    
    total_focus_minutes = sum([s.to_dict()['duration_minutes'] or 0 for s in sessions])
    total_interruptions = sum([s.interruptions for s in sessions])
    total_distractions = sum([s.distractions for s in sessions])
    
    tasks_created = Task.query.filter(Task.user_id == u_id, Task.created_at >= seven_days_ago).all()
    tasks_completed = [t for t in tasks_created if t.status == 'DONE']
    
    completion_rate = 0
    if len(tasks_created) > 0:
        completion_rate = int((len(tasks_completed) / len(tasks_created)) * 100)

    stress_level = "Bajo 🧘"
    if total_interruptions > 8 or total_distractions > 5:
        stress_level = "Alto ⚡ (Peligro de Burnout)"
    elif total_interruptions > 3 or total_distractions > 2:
        stress_level = "Medio ⚠️ (Carga mental elevada)"

    burnout_alert = ""
    projects = Project.query.filter_by(user_id=u_id).all()
    overloaded_projects = []
    for p in projects:
        pending_p_tasks = [t for t in p.tasks if t.status != 'DONE']
        if len(pending_p_tasks) > 3:
            overloaded_projects.append(p.name)

    if overloaded_projects:
        projects_str = ", ".join(overloaded_projects)
        burnout_alert = f"Alerta de Burnout: Estás aceptando demasiado trabajo en los proyectos: [{projects_str}]. Sugerencia del Coach: Di que 'no' a nuevos compromisos en estas áreas esta semana para recuperar el equilibrio."
    else:
        burnout_alert = "Tu carga mental está balanceada. Sigue así y recuerda tomar pausas cortas entre bloques."

    return render_template('analytics/index.html', 
                           total_focus_minutes=total_focus_minutes,
                           total_interruptions=total_interruptions,
                           total_distractions=total_distractions,
                           completion_rate=completion_rate,
                           stress_level=stress_level,
                           burnout_alert=burnout_alert,
                           completed_count=len(tasks_completed),
                           created_count=len(tasks_created))

def render_kanban_partial(u_id):
    tasks = Task.query.filter_by(user_id=u_id).all()
    kanban = {
        'PENDING': [t for t in tasks if t.status == 'PENDING'],
        'TODAY': [t for t in tasks if t.status == 'TODAY'],
        'PROGRESS': [t for t in tasks if t.status == 'PROGRESS'],
        'WAITING': [t for t in tasks if t.status == 'WAITING'],
        'DONE': [t for t in tasks if t.status == 'DONE']
    }
    return render_template('tasks/partials/kanban.html', kanban=kanban)

@analytics_bp.route('/start-focus/<int:task_id>', methods=['POST'])
@login_required
def start_focus(task_id):
    u_id = session['user_id']
    now = datetime.utcnow()
    
    # 1. Cerrar cualquier sesión de enfoque activa en la base de datos de este usuario
    active_sessions = FocusSession.query.join(Task).filter(
        Task.user_id == u_id,
        FocusSession.end_time == None
    ).all()
    for s in active_sessions:
        s.end_time = now
        if s.task:
            s.task.status = 'TODAY'
        
    # 2. Regresar cualquier otra tarea en PROGRESS del usuario a TODAY
    other_progress_tasks = Task.query.filter(Task.status == 'PROGRESS', Task.id != task_id, Task.user_id == u_id).all()
    for t in other_progress_tasks:
        t.status = 'TODAY'
        
    # 3. Establecer la nueva tarea en PROGRESS e iniciar su sesión
    task = db.session.get(Task, task_id)
    if task and task.user_id == u_id:
        task.status = 'PROGRESS'
        session_obj = FocusSession(task_id=task_id, start_time=now)
        db.session.add(session_obj)
        db.session.commit()
        session_id = session_obj.id
    else:
        session_id = None
    
    if request.headers.get('HX-Request'):
        src = request.args.get('src') or request.form.get('src')
        if src == 'kanban':
            return render_kanban_partial(u_id)
        response = jsonify({'status': 'success', 'session_id': session_id})
        response.headers['HX-Redirect'] = url_for('core.index')
        return response
    return redirect(url_for('core.index'))

@analytics_bp.route('/log-interruption/<int:session_id>', methods=['POST'])
@login_required
def log_interruption(session_id):
    u_id = session['user_id']
    focus_sess = db.session.get(FocusSession, session_id)
    if focus_sess and focus_sess.task and focus_sess.task.user_id == u_id:
        focus_sess.interruptions += 1
        db.session.commit()
        return jsonify({'interruptions': focus_sess.interruptions})
    return jsonify({'interruptions': 0})

@analytics_bp.route('/log-block/<int:session_id>', methods=['POST'])
@login_required
def log_block(session_id):
    u_id = session['user_id']
    reason = request.form.get('reason', 'DISTRACTED')
    focus_sess = db.session.get(FocusSession, session_id)
    coach_tip = "Tómate un respiro de 5 minutos. Bebe agua, camina y regresa."
    
    if focus_sess and focus_sess.task and focus_sess.task.user_id == u_id:
        focus_sess.distractions += 1
        focus_sess.block_reason = reason
        db.session.commit()
        
        status = UserStatus.get_status(user_id=u_id)
        tasks = Task.query.filter(Task.status != 'DONE', Task.user_id == u_id).all()
        
        user_queries = {
            'NOT_KNOW_HOW': "Estoy bloqueado porque no sé cómo continuar con la tarea.",
            'DISTRACTED': "Me distraje con otra cosa y procrastiné.",
            'TIRED': "Estoy muy cansado para continuar programando."
        }
        
        query = user_queries.get(reason, "Estoy bloqueado en mi tarea actual.")
        coach_tip = AIService.get_coach_response(
            user_message=query,
            energy_limit=status.current_energy_limit,
            pending_tasks=tasks
        )
        distractions_count = focus_sess.distractions
    else:
        distractions_count = 0

    return jsonify({'distractions': distractions_count, 'coach_tip': coach_tip})

@analytics_bp.route('/end-focus/<int:session_id>', methods=['POST'])
@login_required
def end_focus(session_id):
    u_id = session['user_id']
    focus_sess = db.session.get(FocusSession, session_id)
    if focus_sess and focus_sess.task and focus_sess.task.user_id == u_id:
        focus_sess.end_time = datetime.utcnow()
        focus_sess.is_completed = True
        task = focus_sess.task
        if task:
            task.status = 'DONE'
        db.session.commit()
    
    if request.headers.get('HX-Request'):
        return render_kanban_partial(u_id)
    return redirect(url_for('core.index'))

@analytics_bp.route('/pause-focus/<int:session_id>', methods=['POST'])
@login_required
def pause_focus(session_id):
    u_id = session['user_id']
    focus_sess = db.session.get(FocusSession, session_id)
    if focus_sess and focus_sess.task and focus_sess.task.user_id == u_id:
        focus_sess.end_time = datetime.utcnow()
        if focus_sess.task:
            focus_sess.task.status = 'TODAY'
        db.session.commit()
        
    if request.headers.get('HX-Request'):
        src = request.args.get('src') or request.form.get('src')
        if src == 'kanban':
            return render_kanban_partial(u_id)
        response = jsonify({'status': 'paused'})
        response.headers['HX-Redirect'] = url_for('core.index')
        return response
    return redirect(url_for('core.index'))

@analytics_bp.route('/complete-task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    u_id = session['user_id']
    task = db.session.get(Task, task_id)
    if task and task.user_id == u_id:
        task.status = 'DONE'
        # Cerrar sesiones abiertas
        active_sessions = FocusSession.query.filter_by(task_id=task_id, end_time=None).all()
        for s in active_sessions:
            s.end_time = datetime.utcnow()
        db.session.commit()
        
    if request.headers.get('HX-Request'):
        return render_kanban_partial(u_id)
    return redirect(url_for('core.index'))
