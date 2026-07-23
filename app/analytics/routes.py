from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.core.database import db
from app.analytics.models import FocusSession
from app.tasks.models import Task
from app.projects.models import Project
from app.core.models import UserStatus
from app.ai.services import AIService
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/', methods=['GET'])
def index():
    today = datetime.utcnow()
    seven_days_ago = today - timedelta(days=7)

    sessions = FocusSession.query.filter(FocusSession.start_time >= seven_days_ago).all()
    
    total_focus_minutes = sum([s.to_dict()['duration_minutes'] or 0 for s in sessions])
    total_interruptions = sum([s.interruptions for s in sessions])
    total_distractions = sum([s.distractions for s in sessions])
    
    tasks_created = Task.query.filter(Task.created_at >= seven_days_ago).all()
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
    projects = Project.query.all()
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

def render_kanban_partial():
    tasks = Task.query.all()
    kanban = {
        'PENDING': [t for t in tasks if t.status == 'PENDING'],
        'TODAY': [t for t in tasks if t.status == 'TODAY'],
        'PROGRESS': [t for t in tasks if t.status == 'PROGRESS'],
        'WAITING': [t for t in tasks if t.status == 'WAITING'],
        'DONE': [t for t in tasks if t.status == 'DONE']
    }
    return render_template('tasks/partials/kanban.html', kanban=kanban)

@analytics_bp.route('/start-focus/<int:task_id>', methods=['POST'])
def start_focus(task_id):
    now = datetime.utcnow()
    
    # 1. Cerrar cualquier sesión de enfoque activa en la base de datos
    active_sessions = FocusSession.query.filter_by(end_time=None).all()
    for s in active_sessions:
        s.end_time = now
        if s.task:
            s.task.status = 'TODAY'
        
    # 2. Regresar cualquier otra tarea en PROGRESS a TODAY
    other_progress_tasks = Task.query.filter(Task.status == 'PROGRESS', Task.id != task_id).all()
    for t in other_progress_tasks:
        t.status = 'TODAY'
        
    # 3. Establecer la nueva tarea en PROGRESS e iniciar su sesión
    task = db.session.get(Task, task_id)
    if task:
        task.status = 'PROGRESS'
    
    session = FocusSession(task_id=task_id, start_time=now)
    db.session.add(session)
    db.session.commit()
    
    if request.headers.get('HX-Request'):
        src = request.args.get('src') or request.form.get('src')
        if src == 'kanban':
            return render_kanban_partial()
        response = jsonify({'status': 'success', 'session_id': session.id})
        response.headers['HX-Redirect'] = url_for('core.index')
        return response
    return redirect(url_for('core.index'))



@analytics_bp.route('/log-interruption/<int:session_id>', methods=['POST'])
def log_interruption(session_id):
    session = db.session.get(FocusSession, session_id)
    if session:
        session.interruptions += 1
        db.session.commit()
    return jsonify({'interruptions': session.interruptions if session else 0})

@analytics_bp.route('/log-block/<int:session_id>', methods=['POST'])
def log_block(session_id):
    reason = request.form.get('reason', 'DISTRACTED')
    session = db.session.get(FocusSession, session_id)
    coach_tip = "Tómate un respiro de 5 minutos. Bebe agua, camina y regresa."
    
    if session:
        session.distractions += 1
        session.block_reason = reason
        db.session.commit()
        
        status = UserStatus.get_status()
        tasks = Task.query.filter(Task.status != 'DONE').all()
        
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

    return jsonify({'distractions': session.distractions if session else 0, 'coach_tip': coach_tip})

@analytics_bp.route('/end-focus/<int:session_id>', methods=['POST'])
def end_focus(session_id):
    session = db.session.get(FocusSession, session_id)
    if session:
        session.end_time = datetime.utcnow()
        session.is_completed = True
        task = session.task
        if task:
            task.status = 'DONE'
        db.session.commit()
    
    if request.headers.get('HX-Request'):
        return render_kanban_partial()
    return redirect(url_for('core.index'))

@analytics_bp.route('/pause-focus/<int:session_id>', methods=['POST'])
def pause_focus(session_id):
    session = db.session.get(FocusSession, session_id)
    if session:
        session.end_time = datetime.utcnow()
        if session.task:
            session.task.status = 'TODAY'
        db.session.commit()
        
    if request.headers.get('HX-Request'):
        src = request.args.get('src') or request.form.get('src')
        if src == 'kanban':
            return render_kanban_partial()
        response = jsonify({'status': 'paused'})
        response.headers['HX-Redirect'] = url_for('core.index')
        return response
    return redirect(url_for('core.index'))

@analytics_bp.route('/complete-task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    task = db.session.get(Task, task_id)
    if task:
        task.status = 'DONE'
        active_sessions = FocusSession.query.filter_by(task_id=task_id, end_time=None).all()
        for s in active_sessions:
            s.end_time = datetime.utcnow()
            s.is_completed = True
        db.session.commit()
        
    if request.headers.get('HX-Request'):
        return render_kanban_partial()
    return redirect(url_for('core.index'))



