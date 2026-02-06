from datetime import datetime
from app.extensions import db

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    phone = db.Column(db.String(25), unique=True)
    password_hash = db.Column(db.String(255))
    wallet_balance = db.Column(db.Float, default=0)
    strike_count = db.Column(db.Integer, default=0)
    is_frozen = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OTPAttempt(db.Model):
    __tablename__ = "otp_attempts"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(25))
    code = db.Column(db.String(6))
    success = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MerchantFollow(db.Model):
    __tablename__ = "merchant_follows"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer)
    merchant_id = db.Column(db.Integer)
