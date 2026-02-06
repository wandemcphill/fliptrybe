from datetime import datetime

from app.extensions import db


class RoleChangeRequest(db.Model):
    __tablename__ = "role_change_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    current_role = db.Column(db.String(32), nullable=False)
    requested_role = db.Column(db.String(32), nullable=False)
    reason = db.Column(db.String(400), nullable=True)

    status = db.Column(db.String(16), nullable=False, default="PENDING")  # PENDING|APPROVED|REJECTED
    admin_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    admin_note = db.Column(db.String(400), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": int(self.id),
            "user_id": int(self.user_id),
            "current_role": self.current_role or "",
            "requested_role": self.requested_role or "",
            "reason": self.reason or "",
            "status": self.status or "PENDING",
            "admin_user_id": int(self.admin_user_id) if self.admin_user_id is not None else None,
            "admin_note": self.admin_note or "",
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
