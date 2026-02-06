from __future__ import annotations

import io
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file

from app.extensions import db
from app.models import User, PayoutRequest
from app.utils.jwt_utils import decode_token

payout_pdf_bp = Blueprint("payout_pdf_bp", __name__, url_prefix="/api/wallet/payouts")

_INIT = False


@payout_pdf_bp.before_app_request
def _ensure_tables_once():
    global _INIT
    if _INIT:
        return
    try:
        db.create_all()
    except Exception:
        pass
    _INIT = True


def _bearer():
    h = request.headers.get("Authorization", "")
    if not h.startswith("Bearer "):
        return None
    return h.replace("Bearer ", "", 1).strip()


def _current_user():
    tok = _bearer()
    if not tok:
        return None
    payload = decode_token(tok)
    if not payload:
        return None
    sub = payload.get("sub")
    if not sub:
        return None
    try:
        uid = int(sub)
    except Exception:
        return None
    return User.query.get(uid)


@payout_pdf_bp.get("/<int:payout_id>/pdf")
def payout_pdf(payout_id: int):
    u = _current_user()
    if not u:
        return jsonify({"message": "Unauthorized"}), 401
    p = PayoutRequest.query.get(payout_id)
    if not p:
        return jsonify({"message": "Not found"}), 404

    is_admin = (u.role or "") == "admin" or int(getattr(u, "id", 0) or 0) == 1
    if not is_admin and int(p.user_id) != int(u.id):
        return jsonify({"message": "Forbidden"}), 403

    buf = io.BytesIO()
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        y = h - 60
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "FlipTrybe Payout Receipt")
        y -= 28
        c.setFont("Helvetica", 11)
        lines = [
            f"Payout ID: {p.id}",
            f"User ID: {p.user_id}",
            f"Amount: NGN {float(p.amount or 0.0):.2f}",
            f"Status: {p.status}",
            f"Bank: {p.bank_name or ''}",
            f"Account Number: {p.account_number or ''}",
            f"Account Name: {p.account_name or ''}",
            f"Requested At: {p.created_at.isoformat() if p.created_at else ''}",
            f"Updated At: {p.updated_at.isoformat() if p.updated_at else ''}",
            f"Generated: {datetime.utcnow().isoformat()}Z",
        ]
        for ln in lines:
            c.drawString(50, y, ln)
            y -= 18
        c.showPage()
        c.save()
        buf.seek(0)
        return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=f"payout_{p.id}.pdf")
    except Exception:
        txt = f"""FlipTrybe Payout Receipt\nPayout ID: {p.id}\nUser ID: {p.user_id}\nAmount: NGN {float(p.amount or 0.0):.2f}\nStatus: {p.status}\n"""
        buf.write(txt.encode("utf-8"))
        buf.seek(0)
        return send_file(buf, mimetype="application/octet-stream", as_attachment=True, download_name=f"payout_{p.id}.txt")
