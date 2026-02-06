from flask import Blueprint, jsonify

from app.segments.segment_22_listings_routes import Listing

feed_bp = Blueprint("feed_bp", __name__, url_prefix="/api")


@feed_bp.get("/feed")
def get_feed():
    items = Listing.query.order_by(Listing.created_at.desc()).all()
    return jsonify([x.to_dict() for x in items]), 200