from datetime import datetime
from app.extensions import db

class AdCampaign(db.Model):
    __tablename__ = "ad_campaigns"
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer)
    budget = db.Column(db.Float)
    status = db.Column(db.String(20))

class AdClick(db.Model):
    __tablename__ = "ad_clicks"
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    cost = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AdAuction(db.Model):
    __tablename__ = "ad_auctions"
    id = db.Column(db.Integer, primary_key=True)
    slot = db.Column(db.String(50))
    winner_campaign_id = db.Column(db.Integer)
