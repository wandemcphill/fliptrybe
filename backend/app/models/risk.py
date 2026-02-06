from datetime import datetime
from app.extensions import db

class Dispute(db.Model):
    __tablename__ = "disputes"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer)
    claimant_id = db.Column(db.Integer)
    reason = db.Column(db.String(100))
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FraudSignal(db.Model):
    __tablename__ = "fraud_signals"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    reason = db.Column(db.String(150))
    weight = db.Column(db.Float)
