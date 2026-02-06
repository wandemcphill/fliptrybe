from datetime import datetime

from app.extensions import db


class OTPAttempt(db.Model):
    """Stores OTP requests/verification attempts."""

    __tablename__ = "otp_attempts"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(25), index=True)
    code = db.Column(db.String(6))
    success = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
