from datetime import datetime

from app.extensions import db


class MoneyBoxAccount(db.Model):
    __tablename__ = "moneybox_accounts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True, index=True)

    tier = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(16), nullable=False, default="CLOSED")  # ACTIVE|OPEN|MATURED|CLOSED

    principal_balance = db.Column(db.Float, nullable=False, default=0.0)
    bonus_balance = db.Column(db.Float, nullable=False, default=0.0)

    lock_days = db.Column(db.Integer, nullable=False, default=30)
    lock_start_at = db.Column(db.DateTime, nullable=True)
    auto_open_at = db.Column(db.DateTime, nullable=True)
    maturity_at = db.Column(db.DateTime, nullable=True)

    autosave_enabled = db.Column(db.Boolean, nullable=False, default=False)
    autosave_percent = db.Column(db.Float, nullable=False, default=0.0)

    bonus_eligible = db.Column(db.Boolean, nullable=False, default=True)
    bonus_awarded_at = db.Column(db.DateTime, nullable=True)
    last_withdraw_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        total = float(self.principal_balance or 0.0) + float(self.bonus_balance or 0.0)
        projected_bonus = 0.0
        try:
            from app.utils.moneybox import TIER_CONFIG
            cfg = TIER_CONFIG.get(int(self.tier or 1), None)
            if cfg and bool(self.bonus_eligible):
                projected_bonus = round(float(self.principal_balance or 0.0) * float(cfg.get("bonus_rate", 0.0) or 0.0), 2)
        except Exception:
            projected_bonus = 0.0
        expected_at_maturity = round(float(self.principal_balance or 0.0) + float(self.bonus_balance or 0.0) + float(projected_bonus), 2)
        return {
            "user_id": int(self.user_id),
            "tier": int(self.tier or 1),
            "status": self.status or "CLOSED",
            "principal_balance": float(self.principal_balance or 0.0),
            "bonus_balance": float(self.bonus_balance or 0.0),
            "total_balance": float(total),
            "projected_bonus": float(projected_bonus),
            "expected_at_maturity": float(expected_at_maturity),
            "lock_days": int(self.lock_days or 0),
            "lock_start_at": self.lock_start_at.isoformat() if self.lock_start_at else None,
            "auto_open_at": self.auto_open_at.isoformat() if self.auto_open_at else None,
            "maturity_at": self.maturity_at.isoformat() if self.maturity_at else None,
            "autosave_enabled": bool(self.autosave_enabled),
            "autosave_percent": float(self.autosave_percent or 0.0),
            "bonus_eligible": bool(self.bonus_eligible),
            "bonus_awarded_at": self.bonus_awarded_at.isoformat() if self.bonus_awarded_at else None,
            "last_withdraw_at": self.last_withdraw_at.isoformat() if self.last_withdraw_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class MoneyBoxLedger(db.Model):
    __tablename__ = "moneybox_ledger"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("moneybox_accounts.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    entry_type = db.Column(db.String(24), nullable=False)  # OPEN|AUTOSAVE|BONUS|WITHDRAW|PENALTY|AUTO_OPEN|LIQUIDATE|DISPUTE_PENALTY
    amount = db.Column(db.Float, nullable=False, default=0.0)
    balance_after = db.Column(db.Float, nullable=False, default=0.0)

    reference = db.Column(db.String(80), nullable=True, index=True)
    meta = db.Column(db.Text, nullable=True)
    idempotency_key = db.Column(db.String(160), nullable=True, unique=True, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": int(self.id),
            "account_id": int(self.account_id),
            "user_id": int(self.user_id),
            "entry_type": self.entry_type or "",
            "amount": float(self.amount or 0.0),
            "balance_after": float(self.balance_after or 0.0),
            "reference": self.reference or "",
            "meta": self.meta or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
