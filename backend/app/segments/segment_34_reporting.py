"""
=====================================================
FLIPTRYBE SEGMENT 34
OBSERVABILITY, AUDIT & RELIABILITY LAYER
=====================================================
Do not merge yet.
"""

import time
from datetime import datetime

from flask import Blueprint, request, jsonify, g
from flask_login import current_user

from app.extensions import db


# =====================================================
# BLUEPRINT
# =====================================================

observability = Blueprint(
    "observability",
    __name__,
    url_prefix="/admin/observability",
)


# =====================================================
# MODELS
# =====================================================

class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)

    actor_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(100))
    target_type = db.Column(db.String(60))
    target_id = db.Column(db.String(60))

    metadata = db.Column(db.JSON)

    ip_address = db.Column(db.String(45))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MetricPoint(db.Model):
    __tablename__ = "metric_points"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(80))
    value = db.Column(db.Float)

    tags = db.Column(db.JSON)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AlertRule(db.Model):
    __tablename__ = "alert_rules"

    id = db.Column(db.Integer, primary_key=True)

    metric_name = db.Column(db.String(80))
    threshold = db.Column(db.Float)

    comparison = db.Column(db.String(10))  # > < >= <=
    severity = db.Column(db.String(20), default="warning")

    active = db.Column(db.Boolean, default=True)


class SLOTarget(db.Model):
    __tablename__ = "slo_targets"

    id = db.Column(db.Integer, primary_key=True)

    service = db.Column(db.String(80))
    objective = db.Column(db.Float)  # e.g. 99.9
    window_days = db.Column(db.Integer)

    active = db.Column(db.Boolean, default=True)


# =====================================================
# AUDIT LOGGER
# =====================================================

def log_action(action, target_type=None, target_id=None, metadata=None):

    ip = request.remote_addr if request else None

    row = AuditLog(
        actor_id=getattr(current_user, "id", None),
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else None,
        metadata=metadata,
        ip_address=ip,
    )

    db.session.add(row)
    db.session.commit()


# =====================================================
# METRICS
# =====================================================

def record_metric(name, value, tags=None):

    row = MetricPoint(
        name=name,
        value=value,
        tags=tags or {},
    )

    db.session.add(row)
    db.session.commit()


# =====================================================
# MIDDLEWARE TIMING
# =====================================================

def register_latency_hooks(app):

    @app.before_request
    def _start_timer():
        g._start_time = time.time()

    @app.after_request
    def _record_latency(resp):
        if hasattr(g, "_start_time"):
            latency = time.time() - g._start_time
            record_metric(
                "http_latency",
                latency,
                {
                    "path": request.path,
                    "status": resp.status_code,
                },
            )
        return resp


# =====================================================
# ALERT EVALUATOR
# =====================================================

def evaluate_alerts():

    rules = AlertRule.query.filter_by(active=True).all()

    for rule in rules:

        latest = (
            MetricPoint.query.filter_by(name=rule.metric_name)
            .order_by(MetricPoint.created_at.desc())
            .first()
        )

        if not latest:
            continue

        triggered = False

        if rule.comparison == ">" and latest.value > rule.threshold:
            triggered = True
        if rule.comparison == "<" and latest.value < rule.threshold:
            triggered = True
        if rule.comparison == ">=" and latest.value >= rule.threshold:
            triggered = True
        if rule.comparison == "<=" and latest.value <= rule.threshold:
            triggered = True

        if triggered:
            log_action(
                "alert_triggered",
                target_type="metric",
                target_id=rule.metric_name,
                metadata={
                    "value": latest.value,
                    "threshold": rule.threshold,
                    "severity": rule.severity,
                },
            )


# =====================================================
# ROUTES
# =====================================================

@observability.route("/metrics")
def metrics():

    rows = MetricPoint.query.order_by(
        MetricPoint.created_at.desc()
    ).limit(200)

    return jsonify([
        {
            "name": m.name,
            "value": m.value,
            "tags": m.tags,
            "ts": m.created_at.isoformat(),
        }
        for m in rows
    ])


@observability.route("/audits")
def audits():

    rows = AuditLog.query.order_by(
        AuditLog.created_at.desc()
    ).limit(200)

    return jsonify([
        {
            "actor": a.actor_id,
            "action": a.action,
            "target": a.target_type,
            "target_id": a.target_id,
            "ip": a.ip_address,
            "ts": a.created_at.isoformat(),
        }
        for a in rows
    ])


print("📡 Segment 34 Loaded: Observability & Audit Online")