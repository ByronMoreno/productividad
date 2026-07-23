from functools import wraps
from flask import session, redirect, url_for, g

def current_user():
    if 'user_id' in session:
        from app.auth.models import User
        # Cachear en g para evitar múltiples consultas en la misma petición
        if not hasattr(g, 'current_user') or g.current_user is None:
            g.current_user = User.query.get(session['user_id'])
        return g.current_user
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or current_user() is None:
            # Limpiar sesión por si el usuario fue borrado de base de datos
            session.pop('user_id', None)
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user()
        if not user or user.role != 'ADMIN':
            return redirect(url_for('core.index'))
        return f(*args, **kwargs)
    return decorated_function
