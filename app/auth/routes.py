from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.core.database import db
from app.auth.models import User, SystemConfig
from app.auth.utils import login_required, current_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya tiene sesión, redirigir al inicio
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
    
    # Si el registro es cerrado, solo permitimos si el que registra es un admin
    user = current_user()
    is_admin = user and user.role == 'ADMIN'
    
    if config.registration_mode == 'ADMIN_ONLY' and not is_admin:
        flash('El registro de cuentas está deshabilitado por el administrador.', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', default='USER')
        
        # El rol solo lo puede asignar un admin
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
        
        # Si fue creado por el admin, lo mandamos de vuelta al panel admin, sino inicia sesión
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
