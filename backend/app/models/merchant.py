from datetime import datetime

from app.extensions import db


class MerchantProfile(db.Model):
    __tablename__ = "merchant_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    shop_name = db.Column(db.String(160), nullable=True)
    shop_category = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(32), nullable=True)

    state = db.Column(db.String(64), nullable=True)
    city = db.Column(db.String(64), nullable=True)
    locality = db.Column(db.String(96), nullable=True)
    lga = db.Column(db.String(96), nullable=True)

    # Ranking metrics (MVP)
    total_sales = db.Column(db.Float, nullable=False, default=0.0)
    total_orders = db.Column(db.Integer, nullable=False, default=0)
    successful_deliveries = db.Column(db.Integer, nullable=False, default=0)
    cancelled_orders = db.Column(db.Integer, nullable=False, default=0)
    disputes = db.Column(db.Integer, nullable=False, default=0)

    avg_rating = db.Column(db.Float, nullable=False, default=0.0)
    rating_count = db.Column(db.Integer, nullable=False, default=0)

    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    is_suspended = db.Column(db.Boolean, nullable=False, default=False)
    is_top_tier = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def badge(self) -> str:
        # Badge logic: simple + investor friendly
        if self.is_suspended:
            return "Suspended"
        if (self.avg_rating or 0.0) >= 4.7 and (self.successful_deliveries or 0) >= 50:
            return "Elite"
        if (self.avg_rating or 0.0) >= 4.3 and (self.successful_deliveries or 0) >= 15:
            return "Trusted"
        if (self.total_orders or 0) >= 5:
            return "Rising"
        return "New"

    def score(self) -> float:
        # Weighted score: delivery success + rating + volume - disputes/cancels
        orders = float(self.total_orders or 0)
        deliveries = float(self.successful_deliveries or 0)
        cancels = float(self.cancelled_orders or 0)
        disputes = float(self.disputes or 0)
        rating = float(self.avg_rating or 0.0)
        rating_cnt = float(self.rating_count or 0)

        success_rate = (deliveries / orders) if orders > 0 else 0.0
        volume = min(orders, 200.0) / 200.0  # cap influence
        rating_weight = min(rating_cnt, 50.0) / 50.0

        penalty = (cancels * 0.02) + (disputes * 0.05)
        base = (success_rate * 50.0) + (rating * 8.0 * rating_weight) + (volume * 20.0)
        return max(base - penalty, 0.0)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "shop_name": self.shop_name or "",
            "shop_category": self.shop_category or "",
            "phone": self.phone or "",
            "state": self.state or "",
            "city": self.city or "",
            "locality": self.locality or "",
            "lga": self.lga or "",
            "total_sales": float(self.total_sales or 0.0),
            "total_orders": int(self.total_orders or 0),
            "successful_deliveries": int(self.successful_deliveries or 0),
            "cancelled_orders": int(self.cancelled_orders or 0),
            "disputes": int(self.disputes or 0),
            "avg_rating": float(self.avg_rating or 0.0),
            "rating_count": int(self.rating_count or 0),
            "is_featured": bool(self.is_featured),
            "is_suspended": bool(self.is_suspended),
            "is_top_tier": bool(self.is_top_tier),
            "badge": self.badge(),
            "score": float(self.score()),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class MerchantReview(db.Model):
    __tablename__ = "merchant_reviews"

    id = db.Column(db.Integer, primary_key=True)
    merchant_user_id = db.Column(db.Integer, nullable=False)

    rater_name = db.Column(db.String(120), nullable=True)
    rating = db.Column(db.Integer, nullable=False, default=5)  # 1..5
    comment = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "merchant_user_id": self.merchant_user_id,
            "rater_name": self.rater_name or "",
            "rating": int(self.rating or 0),
            "comment": self.comment or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DisabledUser(db.Model):
    __tablename__ = "disabled_users"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True, index=True)
    reason = db.Column(db.Text, nullable=True)
    disabled = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "reason": self.reason or "",
            "disabled": bool(self.disabled),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DisabledListing(db.Model):
    __tablename__ = "disabled_listings"

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, nullable=False, unique=True, index=True)
    reason = db.Column(db.Text, nullable=True)
    disabled = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "listing_id": self.listing_id,
            "reason": self.reason or "",
            "disabled": bool(self.disabled),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
