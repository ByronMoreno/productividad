from datetime import datetime, timezone
from zoneinfo import ZoneInfo
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

    @property
    def created_at_local(self):
        if self.created_at:
            utc_dt = self.created_at.replace(tzinfo=timezone.utc)
            return utc_dt.astimezone(ZoneInfo('America/Guayaquil'))
        return None

    @property
    def started_at_local(self):

        active_session = None
        for s in self.focus_sessions:
            if s.end_time is None:
                active_session = s
                break
        if active_session and active_session.start_time:
            utc_dt = active_session.start_time.replace(tzinfo=timezone.utc)
            return utc_dt.astimezone(ZoneInfo('America/Guayaquil'))
        return None

    @property
    def completed_at_local(self):
        closed_sessions = [s for s in self.focus_sessions if s.end_time is not None]
        if closed_sessions:
            closed_sessions.sort(key=lambda x: x.end_time, reverse=True)
            last_session = closed_sessions[0]
            utc_dt = last_session.end_time.replace(tzinfo=timezone.utc)
            return utc_dt.astimezone(ZoneInfo('America/Guayaquil'))
        return None



    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True)
    project = db.relationship('Project', backref=db.backref('tasks', lazy=True, cascade="all, delete-orphan"))
    notes = db.relationship('TaskNote', backref='task', lazy=True, cascade="all, delete-orphan", order_by="TaskNote.created_at.desc()")
    attachments = db.relationship('TaskAttachment', backref='task', lazy=True, cascade="all, delete-orphan", order_by="TaskAttachment.created_at.desc()")
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)


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

class TaskNote(db.Model):
    __tablename__ = 'task_notes'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)

    @property
    def created_at_local(self):
        if self.created_at:
            utc_dt = self.created_at.replace(tzinfo=timezone.utc)
            return utc_dt.astimezone(ZoneInfo('America/Guayaquil'))
        return None

class TaskAttachment(db.Model):
    __tablename__ = 'task_attachments'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)

    @property
    def created_at_local(self):
        if self.created_at:
            utc_dt = self.created_at.replace(tzinfo=timezone.utc)
            return utc_dt.astimezone(ZoneInfo('America/Guayaquil'))
        return None


