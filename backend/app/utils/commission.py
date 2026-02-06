def compute_commission(amount: float, rate: float) -> float:
    try:
        a = float(amount or 0.0)
        r = float(rate or 0.0)
        if a < 0:
            a = 0.0
        if r < 0:
            r = 0.0
        return round(a * r, 2)
    except Exception:
        return 0.0


# Default platform commission rates (can be moved to ENV later)
RATES = {
    "listing_sale": 0.05,     # 5% (user listings)
    "delivery": 0.10,         # 10% (worker commission)
    "inspection": 0.10,       # 10% (inspector commission)
    "withdrawal": 0.0,        # free for merchant; role-based in payouts
    "shortlet_booking": 0.03, # 3% add-on
}


def resolve_rate(kind: str, state: str = "", category: str = "") -> float:
    """Resolve commission rate: DB rule (most specific) -> default RATES."""
    if (kind or "").strip() == "withdrawal":
        return 0.0
    try:
        from app.models import CommissionRule  # lazy import
        from app.extensions import db

        k = (kind or "").strip()
        s = (state or "").strip()
        c = (category or "").strip()

        q = CommissionRule.query.filter_by(kind=k, is_active=True)

        # Most specific: kind+state+category
        if s and c:
            r = q.filter(CommissionRule.state.ilike(s), CommissionRule.category.ilike(c)).first()
            if r:
                return float(r.rate or 0.0)

        # Next: kind+state
        if s:
            r = q.filter(CommissionRule.state.ilike(s), (CommissionRule.category.is_(None) | (CommissionRule.category == ""))).first()
            if r:
                return float(r.rate or 0.0)

        # Next: kind+category
        if c:
            r = q.filter(CommissionRule.category.ilike(c), (CommissionRule.state.is_(None) | (CommissionRule.state == ""))).first()
            if r:
                return float(r.rate or 0.0)

        # Fallback: kind only
        r = q.filter((CommissionRule.state.is_(None) | (CommissionRule.state == "")), (CommissionRule.category.is_(None) | (CommissionRule.category == ""))).first()
        if r:
            return float(r.rate or 0.0)
    except Exception:
        pass

    return float(RATES.get((kind or "").strip(), 0.0))
