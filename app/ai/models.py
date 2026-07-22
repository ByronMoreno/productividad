from datetime import datetime
from app.core.database import db

class AgentCollaborationLog(db.Model):
    __tablename__ = 'agent_collaboration_logs'

    id = db.Column(db.Integer, primary_key=True)
    debate_date = db.Column(db.Date, default=datetime.utcnow().date)
    transcript = db.Column(db.Text, nullable=False)
    recommendations = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'debate_date': self.debate_date.isoformat(),
            'transcript': self.transcript,
            'recommendations': self.recommendations
        }
