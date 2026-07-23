from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.core.database import db
from app.auth.models import User, SystemConfig, Group
from app.auth.utils import admin_required, login_required, current_user

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/', methods=['GET'])
@login_required
@admin_required
def index():
    users = User.query.order_by(User.created_at.desc()).all()
    config = SystemConfig.get_config()
    return render_template('admin/index.html', users=users, config=config, current_user=current_user())

@admin_bp.route('/toggle-registration', methods=['POST'])
@login_required
@admin_required
def toggle_registration():
    config = SystemConfig.get_config()
    mode = request.form.get('registration_mode')
    if mode in ['PUBLIC', 'ADMIN_ONLY']:
        config.registration_mode = mode
        db.session.commit()
        flash(f"Modo de registro configurado a: {'Público' if mode == 'PUBLIC' else 'Restringido (Solo Admin)'}", 'success')
    return redirect(url_for('admin.index'))

@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user_to_delete = db.session.get(User, user_id)
    curr_user = current_user()
    
    if not user_to_delete:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('admin.index'))
        
    if user_to_delete.id == curr_user.id:
        flash('No puedes eliminar tu propia cuenta de administrador.', 'danger')
        return redirect(url_for('admin.index'))
        
    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f"Usuario {user_to_delete.email} eliminado con éxito.", 'success')
    return redirect(url_for('admin.index'))

# --- GESTIÓN DE GRUPOS ---

@admin_bp.route('/groups', methods=['GET', 'POST'])
@login_required
@admin_required
def groups():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('El nombre del grupo es obligatorio.', 'danger')
            return redirect(url_for('admin.groups'))
            
        existing_group = Group.query.filter_by(name=name).first()
        if existing_group:
            flash('Ya existe un grupo con ese nombre.', 'danger')
            return redirect(url_for('admin.groups'))
            
        new_group = Group(name=name, description=description)
        db.session.add(new_group)
        db.session.commit()
        flash(f"Grupo '{name}' creado con éxito.", 'success')
        return redirect(url_for('admin.groups'))
        
    groups_list = Group.query.order_by(Group.name.asc()).all()
    return render_template('admin/groups.html', groups=groups_list)

@admin_bp.route('/groups/delete/<int:group_id>', methods=['POST'])
@login_required
@admin_required
def delete_group(group_id):
    group_to_delete = db.session.get(Group, group_id)
    if not group_to_delete:
        flash('Grupo no encontrado.', 'danger')
        return redirect(url_for('admin.groups'))
        
    db.session.delete(group_to_delete)
    db.session.commit()
    flash(f"Grupo '{group_to_delete.name}' eliminado con éxito.", 'success')
    return redirect(url_for('admin.groups'))

# --- EDICIÓN DE USUARIO Y ASIGNACIÓN DE GRUPOS ---

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user_to_edit = db.get_or_404(User, user_id)
    
    if request.method == 'POST':
        role = request.form.get('role')
        selected_groups_ids = request.form.getlist('groups')
        
        # Un admin no puede quitarse su propio rol de ADMIN para no quedar bloqueado
        if user_to_edit.id == current_user().id and role != 'ADMIN':
            flash('No puedes quitarte el rol de Administrador a ti mismo.', 'warning')
        else:
            user_to_edit.role = role
            
        # Actualizar grupos
        user_to_edit.groups = []  # Limpiar asociaciones anteriores
        for g_id in selected_groups_ids:
            group_obj = db.session.get(Group, int(g_id))
            if group_obj:
                user_to_edit.groups.append(group_obj)
                
        db.session.commit()
        flash(f"Usuario {user_to_edit.email} actualizado con éxito.", 'success')
        return redirect(url_for('admin.index'))
        
    all_groups = Group.query.order_by(Group.name.asc()).all()
    user_group_ids = [g.id for g in user_to_edit.groups]
    return render_template('admin/edit_user.html', user_to_edit=user_to_edit, groups=all_groups, user_group_ids=user_group_ids)
