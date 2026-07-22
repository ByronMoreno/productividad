from flask import Blueprint, render_template, request, redirect, url_for
from app.core.database import db
from app.calendar.models import TimeBlock
from app.tasks.models import Task
from datetime import datetime, date

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route('/', methods=['GET'])
def index():
    selected_date_str = request.args.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    blocks = TimeBlock.query.filter_by(date=selected_date).order_by(TimeBlock.start_time).all()
    tasks = Task.query.filter(Task.status != 'DONE').all()

    if request.headers.get('HX-Request'):
        return render_template('calendar/partials/list.html', blocks=blocks, selected_date=selected_date)
    return render_template('calendar/index.html', blocks=blocks, tasks=tasks, selected_date=selected_date)

@calendar_bp.route('/add', methods=['POST'])
def add():
    title = request.form.get('title')
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')
    date_str = request.form.get('date')
    task_id_str = request.form.get('task_id')

    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    start_time = datetime.strptime(start_time_str, '%H:%M').time() if start_time_str else None
    end_time = datetime.strptime(end_time_str, '%H:%M').time() if end_time_str else None
    task_id = int(task_id_str) if task_id_str and task_id_str.strip() else None

    if start_time and end_time:
        block = TimeBlock(
            title=title.strip() if title else None,
            start_time=start_time,
            end_time=end_time,
            date=selected_date,
            task_id=task_id
        )
        db.session.add(block)
        db.session.commit()

    return redirect(url_for('calendar.index', date=selected_date.isoformat()))

@calendar_bp.route('/delete/<int:block_id>', methods=['POST', 'DELETE'])
def delete(block_id):
    block = db.get_or_404(TimeBlock, block_id)
    selected_date = block.date
    db.session.delete(block)
    db.session.commit()

    blocks = TimeBlock.query.filter_by(date=selected_date).order_by(TimeBlock.start_time).all()
    if request.headers.get('HX-Request'):
        return render_template('calendar/partials/list.html', blocks=blocks, selected_date=selected_date)
    return redirect(url_for('calendar.index', date=selected_date.isoformat()))

@calendar_bp.route('/autogenerate', methods=['POST'])
def autogenerate():
    date_str = request.form.get('date')
    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()

    from app.core.models import UserStatus
    from app.ai.services import AIService
    
    status = UserStatus.get_status()
    energy_limit = status.current_energy_limit if status else 3

    
    # Obtener las tareas del día
    tasks = Task.query.filter(Task.status.in_(['TODAY', 'PROGRESS'])).all()
    
    # Generar bloques con IA o Simulador
    ai_blocks = AIService.generate_time_blocking(energy_limit, tasks, selected_date)
    
    # Eliminar bloques anteriores para este día
    TimeBlock.query.filter_by(date=selected_date).delete()
    
    # Insertar los nuevos bloques autogenerados
    for ab in ai_blocks:
        try:
            start_time = datetime.strptime(ab['start_time'], '%H:%M').time()
            end_time = datetime.strptime(ab['end_time'], '%H:%M').time()
        except (ValueError, TypeError):
            continue
            
        task_id = ab.get('task_id')
        if task_id:
            db_task = db.session.get(Task, task_id)
            if not db_task:
                task_id = None
                
        block = TimeBlock(
            title=ab.get('title'),
            start_time=start_time,
            end_time=end_time,
            date=selected_date,
            task_id=task_id
        )
        db.session.add(block)
        
    db.session.commit()
    
    blocks = TimeBlock.query.filter_by(date=selected_date).order_by(TimeBlock.start_time).all()
    if request.headers.get('HX-Request'):
        src = request.args.get('src') or request.form.get('src')
        if src == 'dashboard':
            return render_template('calendar/partials/dashboard_list.html', blocks=blocks)
        return render_template('calendar/partials/list.html', blocks=blocks, selected_date=selected_date)
    return redirect(url_for('calendar.index', date=selected_date.isoformat()))


