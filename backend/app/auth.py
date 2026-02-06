from __future__ import annotations

import os
import random
import string
from datetime import datetime, timedelta

import requests
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Blueprint, request, jsonify

from flask_login import login_user, logout_user, login_required
from app.models import User, OTPAttempt
from app.extensions import db, login_manager
from app.jwt_utils import create_access_token, decode_token, get_bearer_token

auth = Blueprint("auth", __name__, url_prefix="/auth")
api_auth = Blueprint("api_auth", __name__, url_prefix="/api/auth")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@login_manager.request_loader
def load_user_from_request(req):
    """Allow @login_required to work with Bearer tokens too.

    This keeps compatibility with Flask-Login sessions (web) and tokens (mobile).
    """
    token = get_bearer_token(req.headers.get("Authorization", ""))
    if not token:
        return None
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    try:
        user_id = int(payload.get("sub"))
    except Exception:
        return None
    return db.session.get(User, user_id)


# -----------------------------
# Web session login (optional)
# -----------------------------
@auth.post("/login")
def login():
    data = request.get_json(force=True) or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "email and password required"}), 400
    user = User.query.filter_by(email=email).first()
    if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401
    login_user(user)
    return jsonify({"ok": True, "user_id": user.id})


@auth.post("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})


# -----------------------------
# Mobile/API login (JWT)
# -----------------------------
@api_auth.post("/login")
def api_login_email():
    """Email + password login for API clients.

    Useful for admins or email-based login flows.
    """
    data = request.get_json(force=True) or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401

    token = create_access_token(user.id)
    return jsonify({"token": token, "user": {"id": user.id, "email": user.email, "phone": user.phone}})


@api_auth.get("/me")
@login_required
def api_me():
    # login_required now works via bearer token thanks to request_loader
    from flask_login import current_user
    return jsonify({
        "user": {
            "id": current_user.id,
            "email": getattr(current_user, "email", None),
            "phone": getattr(current_user, "phone", None),
        }
    })


def _random_otp() -> str:
    return "".join(random.choice(string.digits) for _ in range(6))


def _send_termii_sms(phone: str, message: str) -> tuple[bool, str]:
    api_key = os.getenv("TERMII_API_KEY")
    sender_id = os.getenv("TERMII_SENDER_ID", "FlipTrybe")
    if not api_key:
        # Dev/demo: do nothing
        return False, "TERMII_API_KEY not set; running in demo mode."

    # Termii "send sms" endpoint (basic). If your Termii plan uses a different route, adjust here.
    url = "https://api.ng.termii.com/api/sms/send"
    payload = {
        "to": phone,
        "from": sender_id,
        "sms": message,
        "type": "plain",
        "channel": "generic",
        "api_key": api_key,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code >= 200 and r.status_code < 300:
            return True, "sent"
        return False, f"termii_error:{r.status_code}"
    except Exception as e:
        return False, f"termii_exception:{e}"


@api_auth.post("/otp/request")
def otp_request():
    """Request OTP for phone login.

    In dev mode (no TERMII_API_KEY), returns the OTP in the response so you can test quickly.
    """
    data = request.get_json(force=True) or {}
    phone = (data.get("phone") or "").strip()
    if not phone:
        return jsonify({"error": "phone required"}), 400

    code = _random_otp()
    # store attempt
    attempt = OTPAttempt(phone=phone, code=code, success=False)
    db.session.add(attempt)
    db.session.commit()

    msg = f"Your FlipTrybe OTP is {code}. It expires in 10 minutes."
    sent, detail = _send_termii_sms(phone, msg)

    env = os.getenv("FLIPTRYBE_ENV", "dev").lower()
    demo = (not sent)  # if termii not configured, we treat as demo

    resp = {"ok": True, "sent": sent, "detail": detail}
    if demo and env != "prod" and env != "production":
        resp["demo_otp"] = code
    return jsonify(resp)


@api_auth.post("/otp/verify")
def otp_verify():
    data = request.get_json(force=True) or {}
    phone = (data.get("phone") or "").strip()
    code = (data.get("code") or "").strip()
    if not phone or not code:
        return jsonify({"error": "phone and code required"}), 400

    # last attempt in last 10 minutes
    ten_min_ago = datetime.utcnow() - timedelta(minutes=10)
    attempt = (OTPAttempt.query
               .filter_by(phone=phone, code=code)
               .filter(OTPAttempt.created_at >= ten_min_ago)
               .order_by(OTPAttempt.id.desc())
               .first())
    if not attempt:
        return jsonify({"error": "invalid or expired otp"}), 401

    attempt.success = True
    user = User.query.filter_by(phone=phone).first()
    if not user:
        user = User(phone=phone)
        db.session.add(user)
    db.session.commit()

    token = create_access_token(user.id)
    return jsonify({"ok": True, "token": token, "user": {"id": user.id, "phone": user.phone, "email": user.email}})
