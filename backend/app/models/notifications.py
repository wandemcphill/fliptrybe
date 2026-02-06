from datetime import datetime
from app.extensions import db

class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True, nullable=False)
    channel = db.Column(db.String(30), default="in_app")
    title = db.Column(db.String(150))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default="queued")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
