"""
==================================================
FLIPTRYBE SEGMENT 3
NOTIFICATION + ALERT ENGINE
Realtime • SMS • WhatsApp • Email • Broadcast
==================================================
Do not merge yet.
"""

from datetime import datetime
import uuid

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, Order, Transaction

# ==================================================
# DATABASE TABLES
# ==================================================

class Notification(db.Model):
    __tablename__ = "system_notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True)
    title = db.Column(db.String(120))
    message = db.Column(db.Text)
    channel = db.Column(db.String(20))  # app/sms/email/whatsapp
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Broadcast(db.Model):
    __tablename__ = "admin_broadcasts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    message = db.Column(db.Text)
    target_role = db.Column(db.String(20))  # all, drivers, merchants
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ==================================================
# DELIVERY CHANNELS
# ==================================================

def push_realtime(user_id, payload):
    try:
        from app.extensions import socketio  # type: ignore
    except Exception:
        socketio = None  # type: ignore

    if socketio is None:
        # Realtime disabled; keep DB notification as source of truth.
        current_app.logger.info("socketio disabled; realtime notification skipped")
        return

    socketio.emit("notification", payload, room=f"user_{user_id}")


def send_sms(phone, message):
    print(f"📲 SMS to {phone}: {message}")
    # Termii integration hook


def send_whatsapp(phone, message):
    print(f"💬 WhatsApp to {phone}: {message}")
    # Termii WhatsApp hook


def send_email(email, subject, message):
    print(f"📧 Email to {email}: {subject}")
    # SMTP / Sendgrid hook


# ==================================================
# CORE NOTIFICATION DISPATCHER
# ==================================================

def dispatch_notification(
    *,
    user: User,
    title: str,
    message: str,
    channels=("app",),
):

    for ch in channels:

        n = Notification(
            user_id=user.id,
            title=title,
            message=message,
            channel=ch,
        )

        db.session.add(n)

        if ch == "app":
            push_realtime(user.id, {"title": title, "message": message})

        if ch == "sms":
            send_sms(user.phone, message)

        if ch == "whatsapp":
            send_whatsapp(user.phone, message)

        if ch == "email":
            send_email(user.email, title, message)

    db.session.commit()


# ==================================================
# EVENT HOOKS
# ==================================================

def payment_received(tx: Transaction):

    dispatch_notification(
        user=tx.user,
        title="Payment Received 💳",
        message=f"₦{tx.amount:,.0f} credited to your wallet.",
        channels=("app", "sms"),
    )


def order_delivered(order: Order):

    dispatch_notification(
        user=order.buyer,
        title="Order Delivered 📦",
        message=f"Order #{order.id} completed successfully.",
        channels=("app", "whatsapp"),
    )


def risk_freeze(user: User):

    dispatch_notification(
        user=user,
        title="Account Restricted ⚠️",
        message="Unusual activity detected. Support is reviewing your account.",
        channels=("app", "email"),
    )


# ==================================================
# ADMIN BROADCAST
# ==================================================

admin_notify = Blueprint(
    "admin_notify",
    __name__,
    url_prefix="/api/admin/notify"
)


@admin_notify.route("/broadcast", methods=["POST"])
@login_required
def broadcast():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    data = request.json or {}

    target = data.get("target", "all")

    b = Broadcast(
        title=data["title"],
        message=data["message"],
        target_role=target,
    )

    db.session.add(b)
    db.session.commit()

    if target == "all":
        users = User.query.all()
    else:
        users = User.query.filter_by(is_driver=(target == "drivers")).all()

    for u in users:
        dispatch_notification(
            user=u,
            title=b.title,
            message=b.message,
            channels=("app",),
        )

    return jsonify({"status": "sent", "count": len(users)})


# ==================================================
# USER INBOX
# ==================================================

user_notify = Blueprint(
    "user_notify",
    __name__,
    url_prefix="/api/notifications"
)


@user_notify.route("/")
@login_required
def inbox():

    rows = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc())

    return jsonify([
        {
            "id": n.id,
            "title": n.title,
            "msg": n.message,
            "channel": n.channel,
            "read": n.is_read,
        }
        for n in rows
    ])


@user_notify.route("/read/<int:notif_id>", methods=["POST"])
@login_required
def mark_read(notif_id):

    n = Notification.query.get_or_404(notif_id)

    if n.user_id != current_user.id:
        return jsonify({"error": "Forbidden"}), 403

    n.is_read = True
    db.session.commit()

    return jsonify({"status": "ok"})


print("🔔 Segment 3 Loaded: Notification Engine Online")