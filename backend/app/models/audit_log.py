from datetime import datetime

from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)

    actor_user_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(64), nullable=False)
    target_type = db.Column(db.String(64), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    meta = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": int(self.id),
            "actor_user_id": int(self.actor_user_id) if self.actor_user_id else None,
            "action": self.action,
            "target_type": self.target_type or "",
            "target_id": int(self.target_id) if self.target_id else None,
            "meta": self.meta or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
