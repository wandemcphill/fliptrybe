"""
=====================================================
FLIPTRYBE SEGMENT 46
AI DISPUTE ARBITRATION ENGINE
=====================================================
Wraps Segment 45 rule engine with ML-based scoring,
explainability and online learning hooks.
=====================================================
"""

import json
import math
import time
from pathlib import Path
from typing import Dict

from app.segments.segment_45_dispute_arbitration import arbitrate as rule_arbitrate
from app.segments.segment_44_compliance_engine import append_ledger


ROOT = Path.cwd()
MODEL_FILE = ROOT / "ai_dispute_model.json"
TRAINING_LOG = ROOT / "ai_training.log"


# =====================================================
# MODEL STORAGE
# =====================================================

def load_model():

    if MODEL_FILE.exists():
        return json.loads(MODEL_FILE.read_text())

    # Naive Bayesian-style weights
    return {
        "gps_missing": -1.5,
        "otp_failures": 1.8,
        "payment_missing": 2.0,
        "delivery_completed": -2.2,
        "bias_guard": 0.0,
    }


def save_model(model):
    MODEL_FILE.write_text(json.dumps(model, indent=2))


# =====================================================
# FEATURE EXTRACTION
# =====================================================

def vectorize(evidence: Dict):

    return {
        "gps_missing": 1 if not evidence["gps_path"] else 0,
        "otp_failures": len(evidence["otp_attempts"]),
        "payment_missing": 1 if not evidence["payments"] else 0,
        "delivery_completed": 1 if evidence["payments"] else 0,
    }


# =====================================================
# SCORING
# =====================================================

def score(model, features):

    total = 0.0

    for k, v in features.items():
        total += model.get(k, 0) * v

    probability_refund = 1 / (1 + math.exp(-total))

    return probability_refund


# =====================================================
# AI ARBITRATION
# =====================================================

def ai_arbitrate(order_id: int):

    rule_case = rule_arbitrate(order_id)

    evidence = rule_case["evidence"]

    model = load_model()

    features = vectorize(evidence)

    refund_prob = score(model, features)

    decision = rule_case["ruling"]

    if refund_prob > 0.7:
        decision = "refund_buyer"

    elif refund_prob < 0.3:
        decision = "release_escrow"

    ruling = {
        "order_id": order_id,
        "rule_based": rule_case["ruling"],
        "ai_decision": decision,
        "refund_probability": refund_prob,
        "features": features,
        "ts": time.time(),
    }

    append_ledger("ai_dispute_ruling", ruling)

    return ruling


# =====================================================
# ONLINE LEARNING
# =====================================================

def train(feedback: Dict):

    model = load_model()

    lr = 0.05

    for feature, outcome in feedback.items():
        model[feature] = model.get(feature, 0) + lr * outcome

    save_model(model)

    with open(TRAINING_LOG, "a") as f:
        f.write(json.dumps({"ts": time.time(), "feedback": feedback}) + "\n")

    append_ledger("ai_model_updated", feedback)


# =====================================================
# STANDALONE TEST
# =====================================================

if __name__ == "__main__":

    print("🤖 AI arbitration engine online")

    ruling = ai_arbitrate(101)
    print(ruling)

    train({"otp_failures": 1, "gps_missing": -1})