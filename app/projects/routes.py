from flask import Blueprint, render_template, request, redirect, url_for, session
from app.core.database import db
from app.projects.models import Project
from app.auth.utils import login_required

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/', methods=['GET'])
@login_required
def index():
    u_id = session['user_id']
    projects = Project.query.filter_by(user_id=u_id).order_by(Project.name).all()
    if request.headers.get('HX-Request'):
        return render_template('projects/partials/list.html', projects=projects)
    return render_template('projects/index.html', projects=projects)

@projects_bp.route('/add', methods=['POST'])
@login_required
def add():
    u_id = session['user_id']
    name = request.form.get('name')
    description = request.form.get('description')
    color_hex = request.form.get('color_hex', '#4a5568')
    
    if name and name.strip():
        project = Project(name=name.strip(), description=description, color_hex=color_hex, user_id=u_id)
        db.session.add(project)
        db.session.commit()
        
    projects = Project.query.filter_by(user_id=u_id).order_by(Project.name).all()
    if request.headers.get('HX-Request'):
        return render_template('projects/partials/list.html', projects=projects)
    return redirect(url_for('projects.index'))

@projects_bp.route('/delete/<int:project_id>', methods=['POST', 'DELETE'])
@login_required
def delete(project_id):
    u_id = session['user_id']
    project = db.get_or_404(Project, project_id)
    if project.user_id == u_id:
        db.session.delete(project)
        db.session.commit()
    
    projects = Project.query.filter_by(user_id=u_id).order_by(Project.name).all()
    if request.headers.get('HX-Request'):
        return render_template('projects/partials/list.html', projects=projects)
    return redirect(url_for('projects.index'))
