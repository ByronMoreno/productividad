from flask import Blueprint, render_template, request, redirect, url_for, session
from app.core.database import db
from app.tasks.models import Task
from app.projects.models import Project
from datetime import datetime, date
from app.auth.utils import login_required
from app.auth.models import DailyObjective

tasks_bp = Blueprint('tasks', __name__)


def get_kanban_dict(u_id):
    tasks = Task.query.filter_by(user_id=u_id).all()
    return {
        'PENDING': [t for t in tasks if t.status == 'PENDING'],
        'TODAY': [t for t in tasks if t.status == 'TODAY'],
        'PROGRESS': [t for t in tasks if t.status == 'PROGRESS'],
        'WAITING': [t for t in tasks if t.status == 'WAITING'],
        'DONE': [t for t in tasks if t.status == 'DONE']
    }

@tasks_bp.route('/', methods=['GET'])
@login_required
def index():
    u_id = session['user_id']
    kanban = get_kanban_dict(u_id)
    projects = Project.query.filter_by(user_id=u_id).order_by(Project.name).all()
    daily_obj = DailyObjective.query.filter_by(user_id=u_id, date=date.today()).first()
    
    if request.headers.get('HX-Request'):
        return render_template('tasks/partials/kanban.html', kanban=kanban)
    return render_template('tasks/index.html', kanban=kanban, projects=projects, daily_objective=daily_obj)


@tasks_bp.route('/add', methods=['POST'])
@login_required
def add():
    u_id = session['user_id']
    title = request.form.get('title')
    description = request.form.get('description')
    project_id = request.form.get('project_id')
    energy = request.form.get('energy', default=3, type=int)
    priority = request.form.get('priority', default='MEDIUM')
    estimated_time = request.form.get('estimated_time', default=30, type=int)
    due_date_str = request.form.get('due_date')
    status = request.form.get('status', default='PENDING')
    
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
            
    if title and title.strip():
        p_id = int(project_id) if project_id and project_id.strip() else None
        task = Task(
            title=title.strip(),
            description=description,
            project_id=p_id,
            status=status,
            energy=energy,
            priority=priority,
            estimated_time=estimated_time,
            due_date=due_date,
            user_id=u_id
        )
        db.session.add(task)
        db.session.commit()

    return redirect(url_for('tasks.index'))

@tasks_bp.route('/update-status/<int:task_id>', methods=['POST'])
@login_required
def update_status(task_id):
    u_id = session['user_id']
    new_status = request.args.get('status')
    if new_status in ['PENDING', 'TODAY', 'PROGRESS', 'WAITING', 'DONE']:
        task = db.get_or_404(Task, task_id)
        if task.user_id == u_id:
            task.status = new_status
            db.session.commit()
        
    kanban = get_kanban_dict(u_id)
    return render_template('tasks/partials/kanban.html', kanban=kanban)

@tasks_bp.route('/delete/<int:task_id>', methods=['POST', 'DELETE'])
@login_required
def delete(task_id):
    u_id = session['user_id']
    task = db.get_or_404(Task, task_id)
    if task.user_id == u_id:
        db.session.delete(task)
        db.session.commit()
    
    kanban = get_kanban_dict(u_id)
    if request.headers.get('HX-Request'):
        return render_template('tasks/partials/kanban.html', kanban=kanban)
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/edit/<int:task_id>', methods=['POST'])
@login_required
def edit(task_id):
    u_id = session['user_id']
    task = db.get_or_404(Task, task_id)
    if task.user_id != u_id:
        return redirect(url_for('tasks.index'))

    title = request.form.get('title')
    description = request.form.get('description')
    project_id = request.form.get('project_id')
    status = request.form.get('status')
    energy = request.form.get('energy', type=int)
    priority = request.form.get('priority')
    estimated_time = request.form.get('estimated_time', type=int)
    due_date_str = request.form.get('due_date')

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    if title and title.strip():
        task.title = title.strip()
        task.description = description
        task.project_id = int(project_id) if project_id and project_id.strip() else None
        task.status = status
        task.energy = energy
        task.priority = priority
        task.estimated_time = estimated_time
        task.due_date = due_date
        db.session.commit()

    kanban = get_kanban_dict(u_id)
    if request.headers.get('HX-Request'):
        return render_template('tasks/partials/kanban.html', kanban=kanban)
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/<int:task_id>/notes/add', methods=['POST'])
@login_required
def add_note(task_id):
    u_id = session['user_id']
    content = request.form.get('content')
    task = db.get_or_404(Task, task_id)
    if task.user_id == u_id and content and content.strip():
        from app.tasks.models import TaskNote
        note = TaskNote(
            content=content.strip(),
            task_id=task.id
        )
        db.session.add(note)
        db.session.commit()
    
    if request.headers.get('HX-Request'):
        return render_template('tasks/partials/notes_list.html', task=task)
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/delegate/<int:task_id>', methods=['POST'])
@login_required
def delegate(task_id):
    u_id = session['user_id']
    task = db.get_or_404(Task, task_id)
    
    # Validar propiedad de la tarea
    if task.user_id == u_id:
        target_user_id = request.form.get('user_id', type=int)
        if target_user_id:
            task.user_id = target_user_id
            
            # Si estaba en progreso, detener el cronómetro
            if task.status == 'PROGRESS':
                task.status = 'TODAY'
                from app.analytics.models import FocusSession
                active_sessions = FocusSession.query.filter_by(task_id=task.id, end_time=None).all()
                for s in active_sessions:
                    s.end_time = datetime.utcnow()
            
            db.session.commit()
            
    kanban = get_kanban_dict(u_id)
    return render_template('tasks/partials/kanban.html', kanban=kanban)


@tasks_bp.route('/daily-objective', methods=['POST'])
@login_required
def set_daily_objective():
    u_id = session['user_id']
    content = request.form.get('content', '').strip()
    if not content:
        return "", 400
    
    today_date = date.today()
    obj = DailyObjective.query.filter_by(user_id=u_id, date=today_date).first()
    if not obj:
        obj = DailyObjective(user_id=u_id, date=today_date, content=content)
        db.session.add(obj)
    else:
        obj.content = content
    db.session.commit()
    
    return render_template('tasks/partials/daily_objective.html', daily_objective=obj)


@tasks_bp.route('/daily-objective/toggle', methods=['POST'])
@login_required
def toggle_daily_objective():
    u_id = session['user_id']
    today_date = date.today()
    obj = DailyObjective.query.filter_by(user_id=u_id, date=today_date).first()
    if obj:
        obj.completed = not obj.completed
        db.session.commit()
    return render_template('tasks/partials/daily_objective.html', daily_objective=obj)


@tasks_bp.route('/daily-objective', methods=['DELETE'])
@login_required
def delete_daily_objective():
    u_id = session['user_id']
    today_date = date.today()
    obj = DailyObjective.query.filter_by(user_id=u_id, date=today_date).first()
    if obj:
        db.session.delete(obj)
        db.session.commit()
    return render_template('tasks/partials/daily_objective.html', daily_objective=None)


