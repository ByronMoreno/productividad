from flask import Blueprint, render_template, request, redirect, url_for
from app.core.database import db
from app.tasks.models import Task
from app.projects.models import Project
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/', methods=['GET'])
def index():
    tasks = Task.query.all()
    projects = Project.query.order_by(Project.name).all()
    
    kanban = {
        'PENDING': [t for t in tasks if t.status == 'PENDING'],
        'TODAY': [t for t in tasks if t.status == 'TODAY'],
        'PROGRESS': [t for t in tasks if t.status == 'PROGRESS'],
        'WAITING': [t for t in tasks if t.status == 'WAITING'],
        'DONE': [t for t in tasks if t.status == 'DONE']
    }
    
    if request.headers.get('HX-Request'):
        return render_template('tasks/partials/kanban.html', kanban=kanban)
    return render_template('tasks/index.html', kanban=kanban, projects=projects)

@tasks_bp.route('/add', methods=['POST'])
def add():
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
            due_date=due_date
        )
        db.session.add(task)
        db.session.commit()

    return redirect(url_for('tasks.index'))

@tasks_bp.route('/update-status/<int:task_id>', methods=['POST'])
def update_status(task_id):
    new_status = request.args.get('status')
    if new_status in ['PENDING', 'TODAY', 'PROGRESS', 'WAITING', 'DONE']:
        task = db.get_or_404(Task, task_id)
        task.status = new_status
        db.session.commit()
        
    tasks = Task.query.all()
    kanban = {
        'PENDING': [t for t in tasks if t.status == 'PENDING'],
        'TODAY': [t for t in tasks if t.status == 'TODAY'],
        'PROGRESS': [t for t in tasks if t.status == 'PROGRESS'],
        'WAITING': [t for t in tasks if t.status == 'WAITING'],
        'DONE': [t for t in tasks if t.status == 'DONE']
    }
    return render_template('tasks/partials/kanban.html', kanban=kanban)

@tasks_bp.route('/delete/<int:task_id>', methods=['POST', 'DELETE'])
def delete(task_id):
    task = db.get_or_404(Task, task_id)
    db.session.delete(task)
    db.session.commit()
    
    tasks = Task.query.all()
    kanban = {
        'PENDING': [t for t in tasks if t.status == 'PENDING'],
        'TODAY': [t for t in tasks if t.status == 'TODAY'],
        'PROGRESS': [t for t in tasks if t.status == 'PROGRESS'],
        'WAITING': [t for t in tasks if t.status == 'WAITING'],
        'DONE': [t for t in tasks if t.status == 'DONE']
    }
    if request.headers.get('HX-Request'):
        return render_template('tasks/partials/kanban.html', kanban=kanban)
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/edit/<int:task_id>', methods=['POST'])
def edit(task_id):
    task = db.get_or_404(Task, task_id)
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

    tasks = Task.query.all()
    kanban = {
        'PENDING': [t for t in tasks if t.status == 'PENDING'],
        'TODAY': [t for t in tasks if t.status == 'TODAY'],
        'PROGRESS': [t for t in tasks if t.status == 'PROGRESS'],
        'WAITING': [t for t in tasks if t.status == 'WAITING'],
        'DONE': [t for t in tasks if t.status == 'DONE']
    }
    
    if request.headers.get('HX-Request'):
        return render_template('tasks/partials/kanban.html', kanban=kanban)
    return redirect(url_for('tasks.index'))

