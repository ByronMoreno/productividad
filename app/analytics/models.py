from datetime import datetime
from app.core.database import db

class FocusSession(db.Model):
    __tablename__ = 'focus_sessions'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    interruptions = db.Column(db.Integer, default=0)
    distractions = db.Column(db.Integer, default=0)
    block_reason = db.Column(db.String(50), nullable=True) # NOT_KNOW_HOW, DISTRACTED, TIRED
    is_completed = db.Column(db.Boolean, default=False)

    task = db.relationship('Task', backref=db.backref('focus_sessions', lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        duration = None
        if self.end_time:
            duration = int((self.end_time - self.start_time).total_seconds() / 60)
        return {
            'id': self.id,
            'task_id': self.task_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_minutes': duration,
            'interruptions': self.interruptions,
            'distractions': self.distractions,
            'block_reason': self.block_reason,
            'is_completed': self.is_completed
        }
