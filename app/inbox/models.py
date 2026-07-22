from datetime import datetime
from app.core.database import db

class InboxItem(db.Model):
    __tablename__ = 'inbox_items'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    is_processed = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'is_processed': self.is_processed
        }
