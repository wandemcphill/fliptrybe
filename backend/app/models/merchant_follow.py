from app.extensions import db


class MerchantFollow(db.Model):
    __tablename__ = "merchant_follows"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, nullable=False, index=True)
    merchant_id = db.Column(db.Integer, nullable=False, index=True)

