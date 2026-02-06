from datetime import datetime

from app.extensions import db


class IdempotencyKey(db.Model):
    __tablename__ = "idempotency_keys"

    id = db.Column(db.Integer, primary_key=True)

    key = db.Column(db.String(128), nullable=False, unique=True)
    user_id = db.Column(db.Integer, nullable=True)
    route = db.Column(db.String(128), nullable=False, default="")
    request_hash = db.Column(db.String(64), nullable=False, default="")

    response_json = db.Column(db.Text, nullable=True)
    status_code = db.Column(db.Integer, nullable=False, default=200)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": int(self.id),
            "key": self.key,
            "user_id": int(self.user_id) if self.user_id is not None else None,
            "route": self.route,
            "request_hash": self.request_hash,
            "status_code": int(self.status_code),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
