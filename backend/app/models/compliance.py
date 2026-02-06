from datetime import datetime
from app.extensions import db

class KYCRecord(db.Model):
    __tablename__ = "kyc_records"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    status = db.Column(db.String(20))
    document_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer)
    action = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
