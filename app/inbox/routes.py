from flask import Blueprint, render_template, request, redirect, url_for
from app.core.database import db
from app.inbox.models import InboxItem
from datetime import datetime

inbox_bp = Blueprint('inbox', __name__)

@inbox_bp.route('/', methods=['GET'])
def index():
    items = InboxItem.query.filter_by(is_processed=False).order_by(InboxItem.created_at.desc()).all()
    if request.headers.get('HX-Request'):
        return render_template('inbox/partials/list.html', items=items)
    return render_template('inbox/index.html', items=items)

@inbox_bp.route('/add', methods=['POST'])
def add():
    content = request.form.get('content')
    if content and content.strip():
        item = InboxItem(content=content.strip())
        db.session.add(item)
        db.session.commit()
        
        # Invocar procesamiento asíncrono con IA
        from app.ai.tasks import process_inbox_item_task
        process_inbox_item_task.delay(item.id)
    
    items = InboxItem.query.filter_by(is_processed=False).order_by(InboxItem.created_at.desc()).all()

    if request.headers.get('HX-Request'):
        # Retorna el parcial con el input limpio gatillado por cliente
        return render_template('inbox/partials/list.html', items=items)
    return redirect(url_for('core.index'))

@inbox_bp.route('/delete/<int:item_id>', methods=['POST', 'DELETE'])
def delete(item_id):
    item = db.get_or_404(InboxItem, item_id)
    db.session.delete(item)
    db.session.commit()
    
    items = InboxItem.query.filter_by(is_processed=False).order_by(InboxItem.created_at.desc()).all()
    if request.headers.get('HX-Request'):
        return render_template('inbox/partials/list.html', items=items)
    return redirect(url_for('inbox.index'))
