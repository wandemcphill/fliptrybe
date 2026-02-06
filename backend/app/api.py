import os
import hmac
import hashlib
import requests
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Transaction, Wallet, User

api = Blueprint("api", __name__, url_prefix="/api")


# -----------------------------
# Feed (placeholder)
# -----------------------------
@api.get("/feed")
@login_required
def feed():
    # Placeholder: return simple feed; wire to real engine later.
    return jsonify({"items": [], "message": "Feed placeholder. Wire to segment feed engine next."})


# -----------------------------
# Wallet + Paystack
# -----------------------------
@api.post("/payments/paystack/initialize")
@login_required
def paystack_initialize():
    """Initialize Paystack transaction.
    Expects: amount (in kobo or naira), currency, email(optional)
    """
    key = os.getenv("PAYSTACK_SECRET_KEY")
    if not key:
        return jsonify({"error": "PAYSTACK_SECRET_KEY not set"}), 400

    data = request.get_json(force=True) or {}
    amount = data.get("amount")
    email = data.get("email") or getattr(current_user, "email", None) or "user@example.com"
    if not amount:
        return jsonify({"error": "amount required"}), 400

    # Paystack expects amount in kobo for NGN. If user sent naira float, convert safely if needed.
    try:
        amt_int = int(amount)
    except Exception:
        # try float naira -> kobo
        amt_int = int(float(amount) * 100)

    payload = {"email": email, "amount": amt_int}
    r = requests.post(
        "https://api.paystack.co/transaction/initialize",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload,
        timeout=10,
    )
    return jsonify(r.json()), r.status_code


@api.get("/payments/paystack/verify/<reference>")
@login_required
def paystack_verify(reference: str):
    key = os.getenv("PAYSTACK_SECRET_KEY")
    if not key:
        return jsonify({"error": "PAYSTACK_SECRET_KEY not set"}), 400

    r = requests.get(
        f"https://api.paystack.co/transaction/verify/{reference}",
        headers={"Authorization": f"Bearer {key}"},
        timeout=10,
    )
    data = r.json()

    # If successful, you may credit wallet here (idempotent checks needed for production).
    try:
        if data.get("status") and data.get("data", {}).get("status") == "success":
            # ensure wallet
            wallet = Wallet.query.filter_by(user_id=current_user.id).first()
            if not wallet:
                wallet = Wallet(user_id=current_user.id, balance=0)
                db.session.add(wallet)
                db.session.commit()

            amount_kobo = data["data"]["amount"]
            amount_naira = float(amount_kobo) / 100.0
            # create transaction if not exists
            exists = Transaction.query.filter_by(reference=reference).first()
            if not exists:
                tx = Transaction(wallet_id=wallet.id, amount=amount_naira, direction="in", reference=reference)
                wallet.balance = (wallet.balance or 0) + amount_naira
                db.session.add(tx)
                db.session.commit()
    except Exception:
        pass

    return jsonify(data), r.status_code


@api.post("/payments/paystack/webhook")
def paystack_webhook():
    """Webhook endpoint for Paystack.
    Render should expose this publicly. Configure Paystack to call it.
    """
    key = os.getenv("PAYSTACK_SECRET_KEY", "")
    signature = request.headers.get("x-paystack-signature", "")
    body = request.get_data() or b""
    expected = hmac.new(key.encode("utf-8"), body, hashlib.sha512).hexdigest() if key else ""

    if not key or not signature or signature != expected:
        return jsonify({"error": "invalid signature"}), 401

    event = request.get_json(silent=True) or {}
    # TODO: implement idempotent wallet crediting based on event['data']['reference']
    return jsonify({"ok": True})


# -----------------------------
# Listings (simple)
# -----------------------------
@api.post("/listings/create")
@login_required
def listings_create():
    from app.models import Listing
    title = request.form.get("title") or ""
    description = request.form.get("description") or ""
    price = request.form.get("price") or "0"
    try:
        price_val = float(price)
    except Exception:
        price_val = 0.0

    listing = Listing(
        title=title.strip(),
        description=description.strip(),
        price=price_val,
        seller_id=current_user.id,
    )
    db.session.add(listing)
    db.session.commit()

    # Optional image upload (stored locally). On Render this is ephemeral, so later you may use S3/Cloudinary.
    if "image" in request.files:
        f = request.files["image"]
        if f and f.filename:
            upload_dir = os.path.join(os.path.dirname(__file__), "static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            safe_name = f"listing_{listing.id}_{f.filename}".replace("..", ".")
            f.save(os.path.join(upload_dir, safe_name))

    return jsonify({"ok": True, "listing_id": listing.id}), 201


@api.get("/listings")
@login_required
def listings_list():
    from app.models import Listing
    q = Listing.query.order_by(Listing.id.desc()).limit(50).all()
    return jsonify([{
        "id": x.id,
        "title": x.title,
        "description": x.description,
        "price": x.price,
        "seller_id": x.seller_id,
    } for x in q])
