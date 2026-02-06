import os
from datetime import datetime
from flask import Blueprint, jsonify, request, send_from_directory

from app.extensions import db

listings_bp = Blueprint("listings_bp", __name__, url_prefix="/api")

# One-time init guard (per process)
_LISTINGS_INIT_DONE = False

# Uploads directory (relative to backend folder)
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    image_path = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        image_url = self.image_path or ""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description or "",
            "price": self.price,
            "image": image_url,      # FeedItem expects this
            "image_path": image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@listings_bp.before_app_request
def _ensure_tables_once():
    global _LISTINGS_INIT_DONE
    if _LISTINGS_INIT_DONE:
        return
    try:
        db.create_all()
    except Exception:
        pass
    _LISTINGS_INIT_DONE = True


# Serve uploaded images
@listings_bp.get("/uploads/<path:filename>")
def get_uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@listings_bp.get("/listings")
def list_listings():
    items = Listing.query.order_by(Listing.created_at.desc()).all()
    return jsonify([x.to_dict() for x in items]), 200


@listings_bp.post("/listings")
def create_listing():
    """
    Supports BOTH:
    - multipart/form-data (recommended): fields + file "image"
    - JSON body (fallback): title, description, price, image_path
    """
    title = ""
    description = ""
    image_url = ""
    price = 0.0

    # 1) Multipart
    if request.content_type and "multipart/form-data" in request.content_type:
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()

        raw_price = request.form.get("price")
        try:
            price = float(raw_price) if raw_price is not None and str(raw_price).strip() != "" else 0.0
        except Exception:
            price = 0.0

        file = request.files.get("image")
        if file and file.filename:
            # Basic filename handling (keep it simple for dev)
            original = os.path.basename(file.filename)
            ts = int(datetime.utcnow().timestamp())
            safe_name = f"{ts}_{original}"

            save_path = os.path.join(UPLOAD_DIR, safe_name)
            file.save(save_path)

            # Public URL based on request host (emulator calls will set host correctly)
            base = request.host_url.rstrip("/")
            image_url = f"{base}/api/uploads/{safe_name}"

    # 2) JSON fallback
    else:
        payload = request.get_json(silent=True) or {}
        title = (payload.get("title") or "").strip()
        description = (payload.get("description") or "").strip()

        raw_price = payload.get("price")
        try:
            price = float(raw_price) if raw_price is not None and str(raw_price).strip() != "" else 0.0
        except Exception:
            price = 0.0

        image_url = (payload.get("image_path") or payload.get("image") or "").strip()

    if not title:
        return jsonify({"message": "title is required"}), 400

    listing = Listing(
        title=title,
        description=description,
        price=price,
        image_path=image_url,
    )

    try:
        db.session.add(listing)
        db.session.commit()
        return jsonify({"ok": True, "listing": listing.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create listing", "error": str(e)}), 500
