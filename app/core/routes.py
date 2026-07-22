from flask import Blueprint, render_template, request, redirect, url_for
from app.core.database import db
from app.core.models import UserStatus
from app.inbox.models import InboxItem
from app.tasks.models import Task
from app.calendar.models import TimeBlock
from datetime import date

core_bp = Blueprint('core', __name__)

@core_bp.route('/')
def index():
    status = UserStatus.get_status()
    inbox_items = InboxItem.query.filter_by(is_processed=False).order_by(InboxItem.created_at.desc()).all()
    today = date.today()
    today_blocks = TimeBlock.query.filter_by(date=today).order_by(TimeBlock.start_time).all()
    
    max_energy = 5
    if status.current_energy_limit == 1:
        max_energy = 2
    elif status.current_energy_limit == 2:
        max_energy = 4
        
    today_tasks = Task.query.filter(
        Task.status.in_(['TODAY', 'PROGRESS']),
        Task.energy <= max_energy
    ).all()
    if not today_tasks:
        today_tasks = Task.query.filter(
            Task.status.in_(['TODAY', 'PROGRESS'])
        ).all()
    
    active_task = Task.query.filter(
        Task.status == 'PROGRESS'
    ).first()
    
    if not active_task:
        active_task = Task.query.filter(
            Task.status == 'TODAY',
            Task.energy <= max_energy
        ).order_by(Task.priority.desc(), Task.energy.desc()).first()
        
    if not active_task:
        active_task = Task.query.filter(
            Task.status == 'TODAY'
        ).order_by(Task.energy.asc(), Task.priority.desc()).first()

    accumulated_seconds = 0
    if active_task:
        from app.analytics.models import FocusSession
        sessions = FocusSession.query.filter_by(task_id=active_task.id).all()
        for s in sessions:
            if s.end_time:
                accumulated_seconds += int((s.end_time - s.start_time).total_seconds())

    return render_template('index.html', 
                           inbox_items=inbox_items, 
                           today_blocks=today_blocks, 
                           today_tasks=today_tasks,
                           active_task=active_task,
                           accumulated_seconds=accumulated_seconds,
                           today=today,
                           status=status)



@core_bp.route('/set-energy', methods=['POST'])
def set_energy():
    energy_limit = request.form.get('energy_limit', type=int)
    if energy_limit in [1, 2, 3]:
        status = UserStatus.get_status()
        status.current_energy_limit = energy_limit
        db.session.commit()
    return redirect(url_for('core.index'))
