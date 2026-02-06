from app.models import Wallet, Transaction, Payout
from app.extensions import db

def credit_wallet(user_id, amount, ref):
    wallet = Wallet.query.filter_by(user_id=user_id).first()
    wallet.balance += amount
    db.session.add(Transaction(
        wallet_id=wallet.id,
        amount=amount,
        direction="credit",
        reference=ref
    ))
    db.session.commit()
