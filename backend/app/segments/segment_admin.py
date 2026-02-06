from flask import Blueprint, jsonify, request
from app.models.user import User
from app.models.listing import Listing

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/api/admin")


@admin_bp.get("/summary")
def admin_summary():
    return jsonify({
        "ok": True,
        "stats": {
            "users": User.query.count(),
            "listings": Listing.query.count(),
            "orders": 0,
            "reports": 0,
        }
    }), 200


@admin_bp.post("/listings/<int:listing_id>/disable")
def disable_listing(listing_id: int):
    # Placeholder without soft-delete column. For demo, just confirms action.
    return jsonify({"ok": True, "listing_id": listing_id, "action": "disabled"}), 200


@admin_bp.post("/users/<int:user_id>/disable")
def disable_user(user_id: int):
    return jsonify({"ok": True, "user_id": user_id, "action": "disabled"}), 200
