from datetime import datetime
from app.extensions import db

class Withdrawal(db.Model):
    __tablename__ = "withdrawals"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    destination = db.Column(db.String(120))
    status = db.Column(db.String(20), default="pending")
    reference = db.Column(db.String(64), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
