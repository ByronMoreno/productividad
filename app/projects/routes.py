from flask import Blueprint, render_template, request, redirect, url_for
from app.core.database import db
from app.projects.models import Project

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/', methods=['GET'])
def index():
    projects = Project.query.order_by(Project.name).all()
    if request.headers.get('HX-Request'):
        return render_template('projects/partials/list.html', projects=projects)
    return render_template('projects/index.html', projects=projects)

@projects_bp.route('/add', methods=['POST'])
def add():
    name = request.form.get('name')
    description = request.form.get('description')
    color_hex = request.form.get('color_hex', '#4a5568')
    
    if name and name.strip():
        project = Project(name=name.strip(), description=description, color_hex=color_hex)
        db.session.add(project)
        db.session.commit()
        
    projects = Project.query.order_by(Project.name).all()
    if request.headers.get('HX-Request'):
        return render_template('projects/partials/list.html', projects=projects)
    return redirect(url_for('projects.index'))

@projects_bp.route('/delete/<int:project_id>', methods=['POST', 'DELETE'])
def delete(project_id):
    project = db.get_or_404(Project, project_id)
    db.session.delete(project)
    db.session.commit()
    
    projects = Project.query.order_by(Project.name).all()
    if request.headers.get('HX-Request'):
        return render_template('projects/partials/list.html', projects=projects)
    return redirect(url_for('projects.index'))
