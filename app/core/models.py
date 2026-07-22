from app.core.database import db

class UserStatus(db.Model):
    __tablename__ = 'user_status'

    id = db.Column(db.Integer, primary_key=True)
    current_energy_limit = db.Column(db.Integer, default=3) # 1=Baja, 2=Media, 3=Alta

    @classmethod
    def get_status(cls):
        status = cls.query.first()
        if not status:
            status = cls(current_energy_limit=3)
            db.session.add(status)
            db.session.commit()
        return status
