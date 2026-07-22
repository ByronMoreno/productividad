from datetime import datetime
from app.core.database import db

task_knowledge_association = db.Table('task_knowledge_association',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    db.Column('knowledge_id', db.Integer, db.ForeignKey('knowledge_nodes.id', ondelete='CASCADE'), primary_key=True)
)

class KnowledgeNode(db.Model):
    __tablename__ = 'knowledge_nodes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = db.relationship('Task', secondary=task_knowledge_association, backref=db.backref('knowledge_nodes', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
