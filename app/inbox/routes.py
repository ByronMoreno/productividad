from flask import Blueprint, render_template, request, redirect, url_for, session
from app.core.database import db
from app.inbox.models import InboxItem
from app.auth.utils import login_required
from datetime import datetime

inbox_bp = Blueprint('inbox', __name__)

@inbox_bp.route('/', methods=['GET'])
@login_required
def index():
    u_id = session['user_id']
    items = InboxItem.query.filter_by(is_processed=False, user_id=u_id).order_by(InboxItem.created_at.desc()).all()
    if request.headers.get('HX-Request'):
        return render_template('inbox/partials/list.html', items=items)
    return render_template('inbox/index.html', items=items)

@inbox_bp.route('/add', methods=['POST'])
@login_required
def add():
    u_id = session['user_id']
    content = request.form.get('content')
    if content and content.strip():
        item = InboxItem(content=content.strip(), user_id=u_id)
        db.session.add(item)
        db.session.commit()
        
        # Invocar procesamiento asíncrono con IA
        from app.ai.tasks import process_inbox_item_task
        process_inbox_item_task.delay(item.id)
    
    items = InboxItem.query.filter_by(is_processed=False, user_id=u_id).order_by(InboxItem.created_at.desc()).all()

    if request.headers.get('HX-Request'):
        return render_template('inbox/partials/list.html', items=items)
    return redirect(url_for('core.index'))

@inbox_bp.route('/delete/<int:item_id>', methods=['POST', 'DELETE'])
@login_required
def delete(item_id):
    u_id = session['user_id']
    item = db.get_or_404(InboxItem, item_id)
    if item.user_id == u_id:
        db.session.delete(item)
        db.session.commit()
    
    items = InboxItem.query.filter_by(is_processed=False, user_id=u_id).order_by(InboxItem.created_at.desc()).all()
    if request.headers.get('HX-Request'):
        return render_template('inbox/partials/list.html', items=items)
    return redirect(url_for('inbox.index'))


@inbox_bp.route('/process/<int:item_id>', methods=['POST'])
@login_required
def process(item_id):
    u_id = session['user_id']
    item = db.get_or_404(InboxItem, item_id)
    if item.user_id != u_id:
        return redirect(url_for('core.index'))
    
    title = request.form.get('title')
    description = request.form.get('description')
    project_id = request.form.get('project_id')
    status = request.form.get('status', 'PENDING')
    estimated_time = request.form.get('estimated_time', type=int) or 30
    energy = request.form.get('energy', type=int) or 3

    # Crear la tarea
    from app.tasks.models import Task
    task = Task(
        title=title,
        description=description,
        project_id=int(project_id) if (project_id and project_id.strip()) else None,
        status=status,
        estimated_time=estimated_time,
        energy=energy,
        user_id=u_id
    )
    db.session.add(task)
    
    # Marcar el item del inbox como procesado
    item.is_processed = True
    item.processed_at = datetime.utcnow()
    
    db.session.commit()
    
    return redirect(url_for('core.index'))

