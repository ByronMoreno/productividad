from flask import Blueprint, render_template, request, redirect, url_for
from app.core.database import db
from app.knowledge.models import KnowledgeNode
from app.tasks.models import Task

knowledge_bp = Blueprint('knowledge', __name__)

@knowledge_bp.route('/', methods=['GET'])
def index():
    query = request.args.get('q', '').strip()
    if query:
        nodes = KnowledgeNode.query.filter(
            (KnowledgeNode.title.ilike(f'%{query}%')) | 
            (KnowledgeNode.content.ilike(f'%{query}%'))
        ).order_by(KnowledgeNode.updated_at.desc()).all()
    else:
        nodes = KnowledgeNode.query.order_by(KnowledgeNode.updated_at.desc()).all()

    if request.headers.get('HX-Request'):
        return render_template('knowledge/partials/list.html', nodes=nodes)
    return render_template('knowledge/index.html', nodes=nodes, query=query)

@knowledge_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        task_ids = request.form.getlist('tasks')

        if title and title.strip():
            node = KnowledgeNode(title=title.strip(), content=content)
            db.session.add(node)
            
            for t_id in task_ids:
                task = db.session.get(Task, int(t_id))
                if task:
                    node.tasks.append(task)
            
            db.session.commit()
            return redirect(url_for('knowledge.index'))

    tasks = Task.query.filter(Task.status != 'DONE').all()
    return render_template('knowledge/edit.html', node=None, tasks=tasks)

@knowledge_bp.route('/edit/<int:node_id>', methods=['GET', 'POST'])
def edit(node_id):
    node = db.get_or_404(KnowledgeNode, node_id)
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        task_ids = request.form.getlist('tasks')

        if title and title.strip():
            node.title = title.strip()
            node.content = content
            
            node.tasks.clear()
            for t_id in task_ids:
                task = db.session.get(Task, int(t_id))
                if task:
                    node.tasks.append(task)
            
            db.session.commit()
            return redirect(url_for('knowledge.index'))

    tasks = Task.query.filter(Task.status != 'DONE').all()
    node_task_ids = [t.id for t in node.tasks]
    return render_template('knowledge/edit.html', node=node, tasks=tasks, node_task_ids=node_task_ids)

@knowledge_bp.route('/delete/<int:node_id>', methods=['POST', 'DELETE'])
def delete(node_id):
    node = db.get_or_404(KnowledgeNode, node_id)
    db.session.delete(node)
    db.session.commit()
    
    nodes = KnowledgeNode.query.order_by(KnowledgeNode.updated_at.desc()).all()
    if request.headers.get('HX-Request'):
        return render_template('knowledge/partials/list.html', nodes=nodes)
    return redirect(url_for('knowledge.index'))
