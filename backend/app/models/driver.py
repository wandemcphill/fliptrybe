from datetime import datetime

from app.extensions import db


class DriverProfile(db.Model):
    __tablename__ = "driver_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True, index=True)

    phone = db.Column(db.String(32), nullable=True)
    vehicle_type = db.Column(db.String(64), nullable=True)  # bike, car, van
    plate_number = db.Column(db.String(32), nullable=True)

    state = db.Column(db.String(64), nullable=True)
    city = db.Column(db.String(64), nullable=True)
    locality = db.Column(db.String(96), nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "user_id": int(self.user_id),
            "phone": self.phone or "",
            "vehicle_type": self.vehicle_type or "",
            "plate_number": self.plate_number or "",
            "state": self.state or "",
            "city": self.city or "",
            "locality": self.locality or "",
            "is_active": bool(self.is_active),
        }
