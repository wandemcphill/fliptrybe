import os
from datetime import datetime, date
from math import radians, sin, cos, sqrt, atan2

from flask import Blueprint, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from sqlalchemy import text

from app.extensions import db
from app.models.shortlet import Shortlet, ShortletBooking
from app.utils.commission import compute_commission, RATES
from app.utils.receipts import create_receipt
from app.utils.notify import queue_in_app, queue_sms, queue_whatsapp, mark_sent
from app.utils.wallets import post_txn
from app.models import User
import os
from app.utils.jwt_utils import decode_token
from app.utils.listing_caps import enforce_listing_cap

shortlets_bp = Blueprint("shortlets_bp", __name__, url_prefix="/api")

# Upload folder (shared): backend/uploads
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOAD_DIR = os.path.join(BACKEND_ROOT, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

_SHORTLETS_INIT_DONE = False


@shortlets_bp.before_app_request
def _ensure_tables_once():
    global _SHORTLETS_INIT_DONE
    if _SHORTLETS_INIT_DONE:
        return
    try:
        db.create_all()
    except Exception:
        pass
    _SHORTLETS_INIT_DONE = True


def _base_url():
    return request.host_url.rstrip("/")


def _platform_user_id() -> int:
    raw = (os.getenv("PLATFORM_USER_ID") or "").strip()
    if raw.isdigit():
        return int(raw)
    try:
        admin = User.query.filter_by(role="admin").order_by(User.id.asc()).first()
        if admin:
            return int(admin.id)
    except Exception:
        pass
    return 1


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


@shortlets_bp.get("/shortlet_uploads/<path:filename>")
def get_shortlet_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@shortlets_bp.get("/shortlets")
def list_shortlets():
    # location filters
    state = (request.args.get("state") or "").strip()
    city = (request.args.get("city") or "").strip()
    locality = (request.args.get("locality") or "").strip()
    lga = (request.args.get("lga") or "").strip()

    # geo filters
    raw_lat = (request.args.get("lat") or "").strip()
    raw_lng = (request.args.get("lng") or "").strip()
    raw_r = (request.args.get("radius_km") or "10").strip()

    lat = None
    lng = None
    radius_km = 10.0

    try:
        lat = float(raw_lat) if raw_lat else None
    except Exception:
        lat = None
    try:
        lng = float(raw_lng) if raw_lng else None
    except Exception:
        lng = None
    try:
        radius_km = float(raw_r) if raw_r else 10.0
    except Exception:
        radius_km = 10.0

    raw_limit = (request.args.get("limit") or "").strip()
    limit = 50
    try:
        limit = int(raw_limit) if raw_limit else 50
    except Exception:
        limit = 50
    if limit <= 0:
        limit = 50
    if limit > 200:
        limit = 200

    q = Shortlet.query
    if state:
        q = q.filter(Shortlet.state.ilike(state))
    if city:
        q = q.filter(Shortlet.city.ilike(city))
    if locality:
        q = q.filter(Shortlet.locality.ilike(locality))
    if lga:
        q = q.filter(Shortlet.lga.ilike(lga))

    items = q.order_by(Shortlet.created_at.desc()).limit(limit).all()

    # radius filter in python (sqlite)
    if lat is not None and lng is not None:
        filtered = []
        for it in items:
            if it.latitude is None or it.longitude is None:
                continue
            try:
                d = _haversine_km(lat, lng, float(it.latitude), float(it.longitude))
            except Exception:
                continue
            if d <= max(radius_km, 0.1):
                filtered.append(it)
        items = filtered

    base = _base_url()
    return jsonify([x.to_dict(base_url=base) for x in items]), 200


@shortlets_bp.get("/shortlets/<int:shortlet_id>")
def get_shortlet(shortlet_id: int):
    item = Shortlet.query.get(shortlet_id)
    if not item:
        return jsonify({"message": "Not found"}), 404
    return jsonify({"ok": True, "shortlet": item.to_dict(base_url=_base_url())}), 200


@shortlets_bp.post("/shortlets")
def create_shortlet():
    u = _current_user()
    if not u:
        return jsonify({"message": "Unauthorized"}), 401

    role = _role(u)
    ok, info = enforce_listing_cap(int(u.id), role, "shortlet")
    if not ok:
        return jsonify(info), 403

    title = ""
    description = ""
    image_rel = ""
    property_type = ""
    amenities = []
    house_rules = []
    verification_score = 20


    state = ""
    city = ""
    locality = ""
    lga = ""

    latitude = None
    longitude = None

    nightly_price = 0.0
    cleaning_fee = 0.0
    beds = 1
    baths = 1
    guests = 2

    available_from = None
    available_to = None

    # Multipart preferred
    if request.content_type and "multipart/form-data" in request.content_type:
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()

        state = (request.form.get("state") or "").strip()
        city = (request.form.get("city") or "").strip()
        locality = (request.form.get("locality") or "").strip()
        lga = (request.form.get("lga") or "").strip()

        property_type = (request.form.get("property_type") or "").strip()
        amenities_raw = (request.form.get("amenities") or "").strip()
        rules_raw = (request.form.get("house_rules") or "").strip()
        if amenities_raw:
            try:
                import json
                amenities = json.loads(amenities_raw) if amenities_raw.strip().startswith("[") else [x.strip() for x in amenities_raw.split(",") if x.strip()]
            except Exception:
                amenities = []
        if rules_raw:
            try:
                import json
                house_rules = json.loads(rules_raw) if rules_raw.strip().startswith("[") else [x.strip() for x in rules_raw.split(",") if x.strip()]
            except Exception:
                house_rules = []

        # Simple MVP: verification score baseline
        try:
            verification_score = int((request.form.get("verification_score") or "20").strip())
        except Exception:
            verification_score = 20

        def _f(name, default=0.0):
            raw = request.form.get(name)
            try:
                return float(raw) if raw is not None and str(raw).strip() != "" else float(default)
            except Exception:
                return float(default)

        nightly_price = _f("nightly_price", 0.0)
        cleaning_fee = _f("cleaning_fee", 0.0)

        def _i(name, default=0):
            raw = request.form.get(name)
            try:
                return int(raw) if raw is not None and str(raw).strip() != "" else int(default)
            except Exception:
                return int(default)

        beds = _i("beds", 1)
        baths = _i("baths", 1)
        guests = _i("guests", 2)

        raw_lat = request.form.get("latitude")
        raw_lng = request.form.get("longitude")
        try:
            latitude = float(raw_lat) if raw_lat is not None and str(raw_lat).strip() != "" else None
        except Exception:
            latitude = None
        try:
            longitude = float(raw_lng) if raw_lng is not None and str(raw_lng).strip() != "" else None
        except Exception:
            longitude = None

        def _d(name):
            raw = (request.form.get(name) or "").strip()
            if not raw:
                return None
            try:
                return date.fromisoformat(raw)
            except Exception:
                return None

        available_from = _d("available_from")
        available_to = _d("available_to")

        file = request.files.get("image")
        if file and file.filename:
            original = secure_filename(os.path.basename(file.filename))
            ts = int(datetime.utcnow().timestamp())
            safe_name = f"{ts}_{original}" if original else f"{ts}_shortlet.jpg"
            save_path = os.path.join(UPLOAD_DIR, safe_name)
            file.save(save_path)
            image_rel = f"/api/shortlet_uploads/{safe_name}"
    else:
        payload = request.get_json(silent=True) or {}
        title = (payload.get("title") or "").strip()
        description = (payload.get("description") or "").strip()

        state = (payload.get("state") or "").strip()
        city = (payload.get("city") or "").strip()
        locality = (payload.get("locality") or "").strip()
        lga = (payload.get("lga") or "").strip()

        property_type = (payload.get("property_type") or "").strip()
        amenities = payload.get("amenities") if isinstance(payload.get("amenities"), list) else []
        house_rules = payload.get("house_rules") if isinstance(payload.get("house_rules"), list) else []
        try:
            verification_score = int(payload.get("verification_score") or 20)
        except Exception:
            verification_score = 20

        try:
            nightly_price = float(payload.get("nightly_price") or 0.0)
        except Exception:
            nightly_price = 0.0
        try:
            cleaning_fee = float(payload.get("cleaning_fee") or 0.0)
        except Exception:
            cleaning_fee = 0.0

        try:
            beds = int(payload.get("beds") or 1)
        except Exception:
            beds = 1
        try:
            baths = int(payload.get("baths") or 1)
        except Exception:
            baths = 1
        try:
            guests = int(payload.get("guests") or 2)
        except Exception:
            guests = 2

        raw_lat = payload.get("latitude")
        raw_lng = payload.get("longitude")
        try:
            latitude = float(raw_lat) if raw_lat is not None and str(raw_lat).strip() != "" else None
        except Exception:
            latitude = None
        try:
            longitude = float(raw_lng) if raw_lng is not None and str(raw_lng).strip() != "" else None
        except Exception:
            longitude = None

        def _d_any(v):
            if v is None:
                return None
            s = str(v).strip()
            if not s:
                return None
            try:
                return date.fromisoformat(s)
            except Exception:
                return None

        available_from = _d_any(payload.get("available_from"))
        available_to = _d_any(payload.get("available_to"))

        image_rel = (payload.get("image_path") or payload.get("image") or "").strip()

    if not title:
        return jsonify({"message": "title is required"}), 400

    base_price = float(nightly_price or 0.0)
    if base_price < 0:
        base_price = 0.0
    platform_fee = round(base_price * 0.03, 2)
    final_price = round(base_price + platform_fee, 2)

    s = Shortlet(
        owner_id=int(u.id),
        title=title,
        description=description,
        state=state,
        city=city,
        locality=locality,
        lga=lga,
        latitude=latitude,
        longitude=longitude,
        nightly_price=final_price,
        base_price=base_price,
        platform_fee=platform_fee,
        final_price=final_price,
        cleaning_fee=cleaning_fee,
        beds=beds,
        baths=baths,
        guests=guests,
        available_from=available_from,
        available_to=available_to,
        image_path=image_rel,
        property_type=property_type,
        amenities=__import__('json').dumps(amenities or []),
        house_rules=__import__('json').dumps(house_rules or []),
        verification_score=verification_score,
    )

    try:
        db.session.add(s)
        db.session.commit()
        return jsonify({"ok": True, "shortlet": s.to_dict(base_url=_base_url())}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create shortlet", "error": str(e)}), 500



@shortlets_bp.get("/shortlets/popular")
def popular_shortlets():
    """Popular shortlets by booking count (investor demo)."""
    try:
        rows = db.session.execute(text("""
            SELECT s.id, s.title, s.state, s.city, COUNT(b.id) AS c
            FROM shortlets s
            LEFT JOIN shortlet_bookings b ON b.shortlet_id = s.id
            GROUP BY s.id, s.title, s.state, s.city
            ORDER BY c DESC, s.created_at DESC
            LIMIT 20
        """)).fetchall()
        items = []
        base = _base_url()
        for r in rows:
            sid = int(r[0])
            s = Shortlet.query.get(sid)
            if not s:
                continue
            d = s.to_dict(base_url=base)
            d["booking_count"] = int(r[4] or 0)
            items.append(d)
        return jsonify({"ok": True, "items": items}), 200
    except Exception:
        return jsonify({"ok": True, "items": []}), 200


@shortlets_bp.post("/shortlets/<int:shortlet_id>/book")
def book_shortlet(shortlet_id: int):
    payload = request.get_json(silent=True) or {}
    check_in_raw = (payload.get("check_in") or "").strip()
    check_out_raw = (payload.get("check_out") or "").strip()

    try:
        check_in = date.fromisoformat(check_in_raw)
        check_out = date.fromisoformat(check_out_raw)
    except Exception:
        return jsonify({"message": "Invalid check_in/check_out (use YYYY-MM-DD)"}), 400

    if check_out <= check_in:
        return jsonify({"message": "check_out must be after check_in"}), 400

    shortlet = Shortlet.query.get(shortlet_id)
    if not shortlet:
        return jsonify({"message": "Not found"}), 404

    nights = (check_out - check_in).days

    # enforce min/max nights
    try:
        mn = int(shortlet.min_nights or 1)
    except Exception:
        mn = 1
    try:
        mx = int(shortlet.max_nights or 30)
    except Exception:
        mx = 30
    if nights < max(mn, 1):
        return jsonify({"message": f"Minimum stay is {max(mn,1)} nights"}), 400
    if nights > max(mx, 1):
        return jsonify({"message": f"Maximum stay is {max(mx,1)} nights"}), 400

    base_price = float(getattr(shortlet, "base_price", 0.0) or 0.0)
    if base_price <= 0.0:
        base_price = float(shortlet.nightly_price or 0.0)
    subtotal = float(base_price) * float(nights) + float(shortlet.cleaning_fee or 0.0)
    platform_fee = compute_commission(subtotal, RATES.get("shortlet_booking", 0.03))
    total = float(subtotal) + float(platform_fee)

    rec = create_receipt(
        user_id=(_current_user_id() or 1),  # use auth if present; fallback demo
        kind="shortlet_booking",
        reference=f"shortlet:{shortlet_id}:{datetime.utcnow().isoformat()}",
        amount=subtotal,
        fee=platform_fee,
        total=total,
        description="Shortlet booking receipt (demo)",
        meta={"shortlet_id": shortlet_id, "nights": nights},
    )


    b = ShortletBooking(
        shortlet_id=shortlet_id,
        guest_name=(payload.get("guest_name") or "").strip(),
        guest_phone=(payload.get("guest_phone") or "").strip(),
        check_in=check_in,
        check_out=check_out,
        nights=nights,
        total_amount=total,
        status="pending",
    )

    try:
        db.session.add(b)
        db.session.commit()
        try:
            if platform_fee > 0:
                post_txn(
                    user_id=_platform_user_id(),
                    direction="credit",
                    amount=float(platform_fee),
                    kind="platform_fee",
                    reference=f"shortlet:{int(shortlet_id)}:{int(b.id)}",
                    note="Shortlet platform fee",
                )
        except Exception:
            pass
        return jsonify({"ok": True, "booking": b.to_dict(), "quote": {"nights": nights, "subtotal": subtotal, "platform_fee": platform_fee, "total": total}}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Booking failed", "error": str(e)}), 500



@shortlets_bp.post("/shortlet_bookings/<int:booking_id>/confirm")
def confirm_booking(booking_id: int):
    b = ShortletBooking.query.get(booking_id)
    if not b:
        return jsonify({"message": "Not found"}), 404
    b.status = "confirmed"
    try:
        db.session.commit()
        return jsonify({"ok": True, "booking": b.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Confirm failed", "error": str(e)}), 500


@shortlets_bp.post("/shortlets/<int:shortlet_id>/review")
def review_shortlet(shortlet_id: int):
    payload = request.get_json(silent=True) or {}
    rating = payload.get("rating")
    try:
        r = float(rating)
    except Exception:
        r = 0.0
    r = max(0.0, min(5.0, r))

    s = Shortlet.query.get(shortlet_id)
    if not s:
        return jsonify({"message": "Not found"}), 404

    # Simple aggregate update
    try:
        current_count = int(s.reviews_count or 0)
        current_rating = float(s.rating or 0.0)
        new_count = current_count + 1
        new_rating = ((current_rating * current_count) + r) / max(new_count, 1)
        s.reviews_count = new_count
        s.rating = float(new_rating)
        db.session.commit()
        return jsonify({"ok": True, "shortlet": s.to_dict(base_url=_base_url())}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Review failed", "error": str(e)}), 500


@shortlets_bp.get("/shortlets_dashboard/summary")
def shortlets_dashboard_summary():
    """Investor-friendly summary counters."""
    try:
        total_shortlets = db.session.query(Shortlet).count()
        total_bookings = db.session.query(ShortletBooking).count()
        confirmed = db.session.query(ShortletBooking).filter(ShortletBooking.status == "confirmed").count()
        pending = db.session.query(ShortletBooking).filter(ShortletBooking.status == "pending").count()
        return jsonify({
            "ok": True,
            "total_shortlets": int(total_shortlets),
            "total_bookings": int(total_bookings),
            "confirmed_bookings": int(confirmed),
            "pending_bookings": int(pending),
        }), 200
    except Exception:
        return jsonify({"ok": True, "total_shortlets": 0, "total_bookings": 0, "confirmed_bookings": 0, "pending_bookings": 0}), 200

def _bearer_token() -> str | None:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return header.replace("Bearer ", "", 1).strip() or None


def _current_user_id() -> int | None:
    token = _bearer_token()
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    sub = payload.get("sub")
    if not sub:
        return None
    try:
        return int(sub)
    except Exception:
        return None


def _current_user() -> User | None:
    uid = _current_user_id()
    if not uid:
        return None
    return User.query.get(int(uid))


def _role(u: User | None) -> str:
    if not u:
        return "guest"
    return (getattr(u, "role", None) or "buyer").strip().lower()
