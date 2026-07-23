from flask import Blueprint, render_template, request, redirect, url_for, session
from app.core.database import db
from app.core.models import UserStatus
from app.inbox.models import InboxItem
from app.tasks.models import Task
from app.calendar.models import TimeBlock
from datetime import date, datetime
from app.auth.utils import login_required

core_bp = Blueprint('core', __name__)

@core_bp.route('/')
@login_required
def index():
    u_id = session['user_id']
    status = UserStatus.get_status(user_id=u_id)
    inbox_items = InboxItem.query.filter_by(is_processed=False, user_id=u_id).order_by(InboxItem.created_at.desc()).all()
    today = date.today()
    today_blocks = TimeBlock.query.filter_by(date=today, user_id=u_id).order_by(TimeBlock.start_time).all()
    
    max_energy = 5
    if status.current_energy_limit == 1:
        max_energy = 2
    elif status.current_energy_limit == 2:
        max_energy = 4
        
    today_tasks = Task.query.filter(
        Task.status.in_(['TODAY', 'PROGRESS']),
        Task.energy <= max_energy,
        Task.user_id == u_id
    ).all()
    if not today_tasks:
        today_tasks = Task.query.filter(
            Task.status.in_(['TODAY', 'PROGRESS']),
            Task.user_id == u_id
        ).all()
    
    active_task = Task.query.filter(
        Task.status == 'PROGRESS',
        Task.user_id == u_id
    ).first()
    
    if not active_task:
        active_task = Task.query.filter(
            Task.status == 'TODAY',
            Task.energy <= max_energy,
            Task.user_id == u_id
        ).order_by(Task.priority.desc(), Task.energy.desc()).first()
        
    if not active_task:
        active_task = Task.query.filter(
            Task.status == 'TODAY',
            Task.user_id == u_id
        ).order_by(Task.energy.asc(), Task.priority.desc()).first()

    accumulated_seconds = 0
    is_focus_active = False
    active_session = None
    if active_task:
        from app.analytics.models import FocusSession
        sessions = FocusSession.query.filter_by(task_id=active_task.id).all()
        for s in sessions:
            if s.end_time:
                accumulated_seconds += int((s.end_time - s.start_time).total_seconds())
            else:
                active_session = s
                is_focus_active = True
                current_span = int((datetime.utcnow() - s.start_time).total_seconds())
                accumulated_seconds += current_span

    return render_template('index.html', 
                           inbox_items=inbox_items, 
                           today_blocks=today_blocks, 
                           today_tasks=today_tasks,
                           active_task=active_task,
                           accumulated_seconds=accumulated_seconds,
                           is_focus_active=is_focus_active,
                           active_session=active_session,
                           today=today,
                           status=status)

@core_bp.route('/set-energy', methods=['POST'])
@login_required
def set_energy():
    u_id = session['user_id']
    energy_limit = request.form.get('energy_limit', type=int)
    if energy_limit in [1, 2, 3]:
        status = UserStatus.get_status(user_id=u_id)
        status.current_energy_limit = energy_limit
        db.session.commit()
    return redirect(url_for('core.index'))
