from datetime import datetime

from app.extensions import db


class KycRequest(db.Model):
    __tablename__ = "kyc_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    status = db.Column(db.String(32), nullable=False, default="unverified")  # unverified|pending|verified|rejected
    full_name = db.Column(db.String(140), nullable=True)
    id_type = db.Column(db.String(64), nullable=True)  # nin|bvn|passport|drivers_license
    id_number = db.Column(db.String(64), nullable=True)

    note = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "user_id": int(self.user_id),
            "status": self.status,
            "full_name": self.full_name or "",
            "id_type": self.id_type or "",
            "id_number": self.id_number or "",
            "note": self.note or "",
        }
