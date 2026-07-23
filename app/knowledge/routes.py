from flask import Blueprint, render_template, request, redirect, url_for, session
from app.core.database import db
from app.knowledge.models import KnowledgeNode
from app.tasks.models import Task
from app.auth.utils import login_required
import os
import time

knowledge_bp = Blueprint('knowledge', __name__)

@knowledge_bp.route('/', methods=['GET'])
@login_required
def index():
    u_id = session['user_id']
    query = request.args.get('q', '').strip()
    if query:
        nodes = KnowledgeNode.query.filter(
            KnowledgeNode.user_id == u_id,
            ((KnowledgeNode.title.ilike(f'%{query}%')) | 
             (KnowledgeNode.content.ilike(f'%{query}%')))
        ).order_by(KnowledgeNode.updated_at.desc()).all()
    else:
        nodes = KnowledgeNode.query.filter_by(user_id=u_id).order_by(KnowledgeNode.updated_at.desc()).all()

    if request.headers.get('HX-Request'):
        return render_template('knowledge/partials/list.html', nodes=nodes)
    return render_template('knowledge/index.html', nodes=nodes, query=query)

@knowledge_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    u_id = session['user_id']
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        task_ids = request.form.getlist('tasks')

        # Procesar archivo de imagen
        image_file = request.files.get('image')
        image_filename = None
        if image_file and image_file.filename:
            file_ext = image_file.filename.split('.')[-1].lower()
            if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                upload_dir = os.path.join('app', 'static', 'uploads', 'knowledge_images')
                os.makedirs(upload_dir, exist_ok=True)
                filename = f"note_{u_id}_{int(time.time())}.{file_ext}"
                image_file.save(os.path.join(upload_dir, filename))
                image_filename = filename

        if title and title.strip():
            node = KnowledgeNode(title=title.strip(), content=content, user_id=u_id, image_filename=image_filename)
            db.session.add(node)
            
            for t_id in task_ids:
                task = db.session.get(Task, int(t_id))
                if task and task.user_id == u_id:
                    node.tasks.append(task)
            
            db.session.commit()
            return redirect(url_for('knowledge.index'))

    tasks = Task.query.filter(Task.status != 'DONE', Task.user_id == u_id).all()
    return render_template('knowledge/edit.html', node=None, tasks=tasks)

@knowledge_bp.route('/edit/<int:node_id>', methods=['GET', 'POST'])
@login_required
def edit(node_id):
    u_id = session['user_id']
    node = db.get_or_404(KnowledgeNode, node_id)
    if node.user_id != u_id:
        return redirect(url_for('knowledge.index'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        task_ids = request.form.getlist('tasks')

        # Procesar archivo de imagen
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            file_ext = image_file.filename.split('.')[-1].lower()
            if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                upload_dir = os.path.join('app', 'static', 'uploads', 'knowledge_images')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Borrar imagen antigua si existe
                if node.image_filename:
                    old_path = os.path.join(upload_dir, node.image_filename)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception:
                            pass
                            
                filename = f"note_{u_id}_{int(time.time())}.{file_ext}"
                image_file.save(os.path.join(upload_dir, filename))
                node.image_filename = filename

        if title and title.strip():
            node.title = title.strip()
            node.content = content
            
            node.tasks.clear()
            for t_id in task_ids:
                task = db.session.get(Task, int(t_id))
                if task and task.user_id == u_id:
                    node.tasks.append(task)
            
            db.session.commit()
            return redirect(url_for('knowledge.index'))

    tasks = Task.query.filter(Task.status != 'DONE', Task.user_id == u_id).all()
    node_task_ids = [t.id for t in node.tasks]
    return render_template('knowledge/edit.html', node=node, tasks=tasks, node_task_ids=node_task_ids)


@knowledge_bp.route('/delete/<int:node_id>', methods=['POST', 'DELETE'])
@login_required
def delete(node_id):
    u_id = session['user_id']
    node = db.get_or_404(KnowledgeNode, node_id)
    if node.user_id == u_id:
        if node.image_filename:
            try:
                upload_dir = os.path.join('app', 'static', 'uploads', 'knowledge_images')
                old_path = os.path.join(upload_dir, node.image_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception:
                pass
        db.session.delete(node)
        db.session.commit()
    
    nodes = KnowledgeNode.query.filter_by(user_id=u_id).order_by(KnowledgeNode.updated_at.desc()).all()
    if request.headers.get('HX-Request'):
        return render_template('knowledge/partials/list.html', nodes=nodes)
    return redirect(url_for('knowledge.index'))

