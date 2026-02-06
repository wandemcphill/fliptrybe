from datetime import datetime

from app.extensions import db


class DriverJob(db.Model):
    __tablename__ = "driver_jobs"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, index=True, nullable=True)
    pickup = db.Column(db.String(255), default="", nullable=False)
    dropoff = db.Column(db.String(255), default="", nullable=False)
    price = db.Column(db.Float, default=0.0, nullable=False)
    status = db.Column(db.String(24), default="open", nullable=False)  # open|assigned|picked|delivered
    driver_id = db.Column(db.Integer, index=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
