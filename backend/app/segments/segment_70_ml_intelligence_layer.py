"""
=====================================================
FLIPTRYBE SEGMENT 70
MACHINE LEARNING INTELLIGENCE CORE
=====================================================
Responsibilities:
1. Feature store
2. Model registry
3. Risk scorer
4. Fraud classifier
5. Price optimizer
6. Recommender engine
7. Personalization layer
8. Retraining scheduler
9. Bias checks
10. Inference router
=====================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Callable
import uuid
import random


# =====================================================
# FEATURE STORE
# =====================================================

FEATURES: Dict[str, dict] = {}


def store_features(entity: str, entity_id: int, data: dict):

    key = f"{entity}:{entity_id}"
    FEATURES[key] = data


def get_features(entity: str, entity_id: int):

    return FEATURES.get(f"{entity}:{entity_id}", {})


# =====================================================
# MODEL REGISTRY
# =====================================================

@dataclass
class ModelArtifact:
    id: str
    name: str
    version: str
    task: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    predict_fn: Callable = None


MODEL_REGISTRY: Dict[str, ModelArtifact] = {}


def register_model(name: str, version: str, task: str, predict_fn):

    mid = str(uuid.uuid4())

    artifact = ModelArtifact(
        id=mid,
        name=name,
        version=version,
        task=task,
        predict_fn=predict_fn,
    )

    MODEL_REGISTRY[mid] = artifact
    return artifact


# =====================================================
# INFERENCE ROUTER
# =====================================================

def route_inference(task: str, features: dict):

    candidates = [
        m for m in MODEL_REGISTRY.values()
        if m.task == task
    ]

    if not candidates:
        raise RuntimeError(f"No model registered for {task}")

    model = sorted(candidates, key=lambda m: m.created_at)[-1]

    return model.predict_fn(features)


# =====================================================
# BASELINE MODELS
# =====================================================

def baseline_risk_model(features):

    return min(1.0, features.get("strike_count", 0) * 0.2)


def baseline_fraud_model(features):

    score = 0.0
    if features.get("velocity", 0) > 10:
        score += 0.4
    if features.get("new_user"):
        score += 0.3
    return min(score, 1.0)


def baseline_price_optimizer(features):

    base = features.get("base_price", 1000)
    demand = features.get("demand", 1.0)

    return round(base * demand, 2)


def baseline_recommender(features):

    return random.sample(features.get("catalog", []), k=min(5, len(features.get("catalog", []))))


# =====================================================
# PERSONALIZATION
# =====================================================

def personalize_feed(user_id: int):

    feats = get_features("user", user_id)

    return route_inference("recommender", feats)


# =====================================================
# RETRAINING
# =====================================================

def retrain_model(model_id: str, new_predict_fn):

    artifact = MODEL_REGISTRY[model_id]
    artifact.predict_fn = new_predict_fn
    artifact.version = f"{artifact.version}+1"
    artifact.created_at = datetime.utcnow()


# =====================================================
# BIAS CHECKS
# =====================================================

def run_bias_audit(model_id: str, samples: List[dict]):

    preds = [MODEL_REGISTRY[model_id].predict_fn(s) for s in samples]

    avg = sum(preds) / max(len(preds), 1)

    return {
        "model_id": model_id,
        "avg_prediction": avg,
        "samples": len(samples),
    }


# =====================================================
# BOOTSTRAP BASELINES
# =====================================================

if __name__ == "__main__":

    r = register_model("risk-v1", "1.0", "risk", baseline_risk_model)
    f = register_model("fraud-v1", "1.0", "fraud", baseline_fraud_model)
    p = register_model("price-v1", "1.0", "price", baseline_price_optimizer)
    rec = register_model("rec-v1", "1.0", "recommender", baseline_recommender)

    store_features("user", 5, {
        "strike_count": 2,
        "catalog": ["bike", "phone", "tv", "laptop"],
    })

    print("PERSONALIZED:", personalize_feed(5))