from app.core.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='USER') # 'USER', 'ADMIN'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class SystemConfig(db.Model):
    __tablename__ = 'system_config'

    id = db.Column(db.Integer, primary_key=True)
    registration_mode = db.Column(db.String(20), default='PUBLIC') # 'PUBLIC', 'ADMIN_ONLY'

    @classmethod
    def get_config(cls):
        config = cls.query.first()
        if not config:
            config = cls(registration_mode='PUBLIC')
            db.session.add(config)
            db.session.commit()
        return config
