"""
=====================================================
FLIPTRYBE SEGMENT 12
ADS & PROMOTED LISTINGS ENGINE
Sponsored Feeds • Bidding • CPC Billing
=====================================================
Do not merge yet.
"""

from datetime import datetime
import uuid

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Listing, Transaction, User

from app.segments.segment_wallet_engine import debit_wallet
from app.segments.segment_notifications_engine import dispatch_notification

# =====================================================
# MODELS
# =====================================================

class PromotionCampaign(db.Model):

    __tablename__ = "promotion_campaigns"

    id = db.Column(db.Integer, primary_key=True)

    campaign_ref = db.Column(db.String(36), unique=True)

    user_id = db.Column(db.Integer)

    listing_id = db.Column(db.Integer)

    daily_budget = db.Column(db.Float)

    bid_amount = db.Column(db.Float)

    total_spent = db.Column(db.Float, default=0.0)

    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AdImpression(db.Model):

    __tablename__ = "ad_impressions"

    id = db.Column(db.Integer, primary_key=True)

    campaign_id = db.Column(db.Integer)

    viewer_id = db.Column(db.Integer)

    cost = db.Column(db.Float)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# BLUEPRINT
# =====================================================

ads = Blueprint(
    "ads",
    __name__,
    url_prefix="/api/ads",
)

# =====================================================
# CREATE CAMPAIGN
# =====================================================

@ads.route("/campaign/create", methods=["POST"])
@login_required
def create_campaign():

    data = request.json

    campaign = PromotionCampaign(
        campaign_ref=str(uuid.uuid4()),
        user_id=current_user.id,
        listing_id=data["listing_id"],
        daily_budget=data["daily_budget"],
        bid_amount=data["bid_amount"],
    )

    db.session.add(campaign)
    db.session.commit()

    return jsonify({"campaign_ref": campaign.campaign_ref})


# =====================================================
# RECORD IMPRESSION
# =====================================================

def record_impression(campaign, viewer_id):

    if not campaign.is_active:
        return

    if campaign.total_spent >= campaign.daily_budget:
        campaign.is_active = False
        return

    debit_wallet(campaign.user_id, campaign.bid_amount)

    campaign.total_spent += campaign.bid_amount

    imp = AdImpression(
        campaign_id=campaign.id,
        viewer_id=viewer_id,
        cost=campaign.bid_amount,
    )

    db.session.add(imp)
    db.session.commit()


# =====================================================
# SPONSORED FEED PICKER
# =====================================================

def pick_sponsored_listing():

    return (
        PromotionCampaign.query
        .filter_by(is_active=True)
        .order_by(PromotionCampaign.bid_amount.desc())
        .first()
    )


print("📣 Segment 12 Loaded: Ads Engine Online")