from datetime import datetime

from app.extensions import db


class AutopilotSettings(db.Model):
    __tablename__ = "autopilot_settings"

    id = db.Column(db.Integer, primary_key=True)
    enabled = db.Column(db.Boolean, nullable=False, default=True)

    last_run_at = db.Column(db.DateTime, nullable=True)

    # Nightly jobs
    last_wallet_reconcile_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": int(self.id),
            "enabled": bool(self.enabled),
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "last_wallet_reconcile_at": self.last_wallet_reconcile_at.isoformat() if self.last_wallet_reconcile_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
