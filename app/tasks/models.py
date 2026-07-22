from datetime import datetime
from app.core.database import db

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='PENDING') # PENDING, TODAY, PROGRESS, WAITING, DONE
    energy = db.Column(db.Integer, default=3) # 1-5 estrellas
    priority = db.Column(db.String(20), default='MEDIUM') # LOW, MEDIUM, HIGH
    estimated_time = db.Column(db.Integer, default=30) # en minutos
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True)
    project = db.relationship('Project', backref=db.backref('tasks', lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'energy': self.energy,
            'priority': self.priority,
            'estimated_time': self.estimated_time,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'project_id': self.project_id,
            'created_at': self.created_at.isoformat()
        }
