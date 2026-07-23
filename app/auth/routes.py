import os
import time
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from app.core.database import db
from app.auth.models import User, SystemConfig
from app.auth.utils import login_required, current_user

auth_bp = Blueprint('auth', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('core.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('core.index'))
            
        flash('Correo electrónico o contraseña incorrectos.', 'danger')
        
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    config = SystemConfig.get_config()
    
    user = current_user()
    is_admin = user and user.role == 'ADMIN'
    
    if config.registration_mode == 'ADMIN_ONLY' and not is_admin:
        flash('El registro de cuentas está deshabilitado por el administrador.', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', default='USER')
        
        if not is_admin:
            role = 'USER'
            
        if not email or not password:
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('auth/register.html', config=config)
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('El correo electrónico ya está registrado.', 'danger')
            return render_template('auth/register.html', config=config)
            
        new_user = User(email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Cuenta creada con éxito.', 'success')
        
        if is_admin:
            return redirect(url_for('admin.index'))
        else:
            session['user_id'] = new_user.id
            return redirect(url_for('core.index'))
            
    return render_template('auth/register.html', config=config)

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user())

@auth_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    user = current_user()
    current_pwd = request.form.get('current_password')
    new_pwd = request.form.get('new_password')
    confirm_pwd = request.form.get('confirm_password')
    
    if not current_pwd or not new_pwd or not confirm_pwd:
        flash('Todos los campos son obligatorios.', 'danger')
        return redirect(url_for('auth.profile'))
        
    if not user.check_password(current_pwd):
        flash('La contraseña actual es incorrecta.', 'danger')
        return redirect(url_for('auth.profile'))
        
    if new_pwd != confirm_pwd:
        flash('La nueva contraseña y su confirmación no coinciden.', 'danger')
        return redirect(url_for('auth.profile'))
        
    user.set_password(new_pwd)
    db.session.commit()
    flash('Contraseña actualizada con éxito.', 'success')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/profile/upload-pic', methods=['POST'])
@login_required
def upload_pic():
    user = current_user()
    if 'profile_pic' not in request.files:
        flash('No se seleccionó ningún archivo.', 'danger')
        return redirect(url_for('auth.profile'))
        
    file = request.files['profile_pic']
    if file.filename == '':
        flash('Nombre de archivo vacío.', 'danger')
        return redirect(url_for('auth.profile'))
        
    if file and allowed_file(file.filename):
        # Crear la carpeta de uploads si no existe
        upload_dir = os.path.join('app', 'static', 'uploads', 'profile_pics')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Eliminar la foto de perfil vieja si existía
        if user.profile_pic_filename:
            old_file_path = os.path.join(upload_dir, user.profile_pic_filename)
            if os.path.exists(old_file_path):
                try:
                    os.remove(old_file_path)
                except Exception as e:
                    print(f"Error al eliminar foto vieja: {e}")
        
        # Generar nombre nuevo seguro con marca de tiempo para evitar el cacheo del navegador
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"profile_user_{user.id}_{int(time.time())}.{file_ext}"
        file_path = os.path.join(upload_dir, filename)
        
        file.save(file_path)
        
        user.profile_pic_filename = filename
        db.session.commit()
        flash('Foto de perfil actualizada con éxito.', 'success')
    else:
        flash('Formato de archivo no permitido. Sube PNG, JPG o JPEG.', 'danger')
        
    return redirect(url_for('auth.profile'))
