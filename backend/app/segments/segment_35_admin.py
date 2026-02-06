"""
=====================================================
FLIPTRYBE SEGMENT 35
BACKGROUND JOBS & SCHEDULERS
=====================================================
Do not merge yet.
"""

from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.extensions import db
from app.models import Order
from app.payments.service import release_escrow

from app.segments.segment_merchant_growth import MerchantStat


# =====================================================
# SCHEDULER
# =====================================================

scheduler = BackgroundScheduler()


# =====================================================
# WEEKLY RESET
# =====================================================

def reset_weekly_leaderboards():

    MerchantStat.query.update(
        {"weekly_sales": 0}
    )

    db.session.commit()


# =====================================================
# ESCROW SWEEP
# =====================================================

def sweep_completed_orders():

    orders = Order.query.filter_by(
        status="Delivered"
    ).all()

    for o in orders:
        try:
            release_escrow(o.id)
        except Exception:
            pass


# =====================================================
# HOUSEKEEPING
# =====================================================

def purge_stale_orders():

    cutoff = datetime.utcnow() - timedelta(days=14)

    Order.query.filter(
        Order.created_at < cutoff,
        Order.status == "Cancelled",
    ).delete()

    db.session.commit()


# =====================================================
# STARTER
# =====================================================

def start_scheduler():

    scheduler.add_job(
        reset_weekly_leaderboards,
        "cron",
        day_of_week="mon",
        hour=0,
    )

    scheduler.add_job(
        sweep_completed_orders,
        "interval",
        minutes=15,
    )

    scheduler.add_job(
        purge_stale_orders,
        "cron",
        hour=3,
    )

    scheduler.start()


print("📦 Segment 35 Loaded: Background Workers Online")