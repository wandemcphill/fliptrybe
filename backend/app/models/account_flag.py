from datetime import datetime

from app.extensions import db


class AccountFlag(db.Model):
    __tablename__ = "account_flags"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    flag_type = db.Column(db.String(32), nullable=False, index=True)
    signal = db.Column(db.String(120), nullable=True)
    details = db.Column(db.Text(), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": int(self.id),
            "user_id": int(self.user_id),
            "flag_type": self.flag_type,
            "signal": self.signal or "",
            "details": self.details or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
