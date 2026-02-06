from app.models.risk import FraudSignal, Dispute

def score_user(user_id):
    signals = FraudSignal.query.filter_by(user_id=user_id).count()
    disputes = Dispute.query.filter_by(claimant_id=user_id).count()
    return min(1.0, (signals + disputes) * 0.1)
