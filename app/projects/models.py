from datetime import datetime
from app.core.database import db

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    color_hex = db.Column(db.String(7), default='#4a5568')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Nota: la relación se definirá en el modelo Task para evitar importaciones circulares, o podemos usar backref aquí.
    # Usaremos back_populates o backref. Definiremos la relación backref en Task para que la carga sea más limpia.
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color_hex': self.color_hex,
            'created_at': self.created_at.isoformat()
        }
