from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.core.database import db
from app.auth.models import User, SystemConfig
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
