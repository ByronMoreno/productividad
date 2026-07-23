from datetime import datetime
from app.core.database import db

class TimeBlock(db.Model):
    __tablename__ = 'time_blocks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    date = db.Column(db.Date, nullable=False)

    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True)
    task = db.relationship('Task', backref=db.backref('time_blocks', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)


    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title or (self.task.title if self.task else 'Sin título'),
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'date': self.date.isoformat(),
            'task_id': self.task_id
        }
