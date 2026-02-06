"""
=====================================================
FLIPTRYBE SEGMENT 25
EXPANSION & REGULATORY CONTROL LAYER
=====================================================
Do not merge yet.
"""

from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db


# =====================================================
# BLUEPRINT
# =====================================================

expansion = Blueprint(
    "expansion",
    __name__,
    url_prefix="/admin/expansion",
)


# =====================================================
# MODELS
# =====================================================

class CountryConfig(db.Model):
    __tablename__ = "country_configs"

    id = db.Column(db.Integer, primary_key=True)
    country_code = db.Column(db.String(10), unique=True)
    currency = db.Column(db.String(10))
    tax_rate = db.Column(db.Float)
    kyc_required = db.Column(db.Boolean, default=True)
    active = db.Column(db.Boolean, default=False)


class CityLaunchPlan(db.Model):
    __tablename__ = "city_launch_plans"

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(80))
    country_code = db.Column(db.String(10))
    status = db.Column(db.String(20), default="planned")
    launch_date = db.Column(db.Date)


class RegulatoryNote(db.Model):
    __tablename__ = "regulatory_notes"

    id = db.Column(db.Integer, primary_key=True)
    country_code = db.Column(db.String(10))
    agency = db.Column(db.String(80))
    note = db.Column(db.Text)
    risk_level = db.Column(db.String(20))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# ROUTES
# =====================================================

@expansion.route("/countries")
@login_required
def list_countries():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    rows = CountryConfig.query.all()

    return jsonify([
        {
            "country": c.country_code,
            "currency": c.currency,
            "active": c.active,
        }
        for c in rows
    ])


@expansion.route("/countries", methods=["POST"])
@login_required
def add_country():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    data = request.json

    row = CountryConfig(**data)

    db.session.add(row)
    db.session.commit()

    return jsonify({"status": "added"})


@expansion.route("/city-launch", methods=["POST"])
@login_required
def create_city_plan():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    data = request.json

    row = CityLaunchPlan(**data)

    db.session.add(row)
    db.session.commit()

    return jsonify({"status": "planned"})


@expansion.route("/regulatory-note", methods=["POST"])
@login_required
def add_regulatory_note():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    data = request.json

    row = RegulatoryNote(**data)

    db.session.add(row)
    db.session.commit()

    return jsonify({"status": "saved"})


print("🌍 Segment 25 Loaded: Expansion & Regulation Online")