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
    profile_pic_filename = db.Column(db.String(255), nullable=True)


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

user_group_association = db.Table('user_group_association',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id', ondelete='CASCADE'), primary_key=True)
)

class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', secondary=user_group_association, backref=db.backref('groups', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }

