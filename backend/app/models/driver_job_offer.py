from datetime import datetime

from app.extensions import db


class DriverJobOffer(db.Model):
    __tablename__ = "driver_job_offers"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)
    driver_id = db.Column(db.Integer, nullable=False)

    status = db.Column(db.String(32), nullable=False, default="offered")  # offered|accepted|rejected|expired
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    decided_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": int(self.id),
            "order_id": int(self.order_id),
            "driver_id": int(self.driver_id),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
        }
