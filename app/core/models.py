from app.core.database import db

class UserStatus(db.Model):
    __tablename__ = 'user_status'

    id = db.Column(db.Integer, primary_key=True)
    current_energy_limit = db.Column(db.Integer, default=3) # 1=Baja, 2=Media, 3=Alta
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)

    @classmethod
    def get_status(cls, user_id=None):
        if not user_id:
            status = cls.query.first()
        else:
            status = cls.query.filter_by(user_id=user_id).first()
        if not status:
            status = cls(current_energy_limit=3, user_id=user_id)
            db.session.add(status)
            db.session.commit()
        return status

