from datetime import datetime
from app.extensions import db


class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer)
    amount = db.Column(db.Float)
    gross_amount = db.Column(db.Float, default=0.0)
    net_amount = db.Column(db.Float, default=0.0)
    commission_total = db.Column(db.Float, default=0.0)
    purpose = db.Column(db.String(32), default='sale')
    direction = db.Column(db.String(10))
    reference = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Payout(db.Model):
    __tablename__ = "payouts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    amount = db.Column(db.Float)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
