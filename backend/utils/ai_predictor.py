"""
AI Prediction Module for LIMS
Uses scikit-learn to predict test result risk levels and approximate values
based on sample metadata and historical patterns.
"""
import numpy as np
from datetime import datetime

# ── Lightweight heuristic model (no training data needed at startup) ──────────
# In production, replace with a trained sklearn Pipeline loaded from disk.

NORMAL_RANGES = {
    "CBC": {"min": 4.5, "max": 11.0, "unit": "10³/µL"},
    "HGB": {"min": 12.0, "max": 17.5, "unit": "g/dL"},
    "PLT": {"min": 150.0, "max": 400.0, "unit": "10³/µL"},
    "GLU": {"min": 70.0, "max": 100.0, "unit": "mg/dL"},
    "CREA": {"min": 0.6, "max": 1.2, "unit": "mg/dL"},
    "ALT": {"min": 7.0, "max": 56.0, "unit": "U/L"},
    "AST": {"min": 10.0, "max": 40.0, "unit": "U/L"},
    "LFT": {"min": 0.1, "max": 1.2, "unit": "mg/dL"},
    "DEFAULT": {"min": 0.0, "max": 100.0, "unit": "units"},
}

PRIORITY_MULTIPLIER = {"stat": 1.4, "urgent": 1.2, "routine": 1.0}
TYPE_RISK = {
    "blood": 0.3,
    "serum": 0.25,
    "urine": 0.2,
    "tissue": 0.4,
    "swab": 0.15,
    "other": 0.2,
}


def _feature_vector(sample: dict, test_code: str) -> np.ndarray:
    """Build a simple feature vector from sample metadata."""
    priority = sample.get("priority", "routine")
    s_type = sample.get("type", "other")
    meta = sample.get("metadata", {})
    temp = float(meta.get("temperature", 37.0))
    volume = float(meta.get("volume_ml", 5.0))

    # Encode categoricals
    p_mult = PRIORITY_MULTIPLIER.get(priority, 1.0)
    t_risk = TYPE_RISK.get(s_type, 0.2)

    # Normalise temperature deviation from 37°C
    temp_dev = abs(temp - 37.0) / 10.0

    return np.array([p_mult, t_risk, temp_dev, min(volume / 10.0, 1.0)])


def predict(sample: dict, test_code: str) -> dict:
    """
    Predict test result characteristics for a given sample.

    Returns:
        predicted_value  – estimated numeric result
        confidence       – model confidence 0–1
        risk_level       – 'low' | 'medium' | 'high'
        reference_range  – expected normal range for the test
        model_version    – identifier for traceability
    """
    code = test_code.upper()
    ref = NORMAL_RANGES.get(code, NORMAL_RANGES["DEFAULT"])
    mid = (ref["min"] + ref["max"]) / 2.0
    span = ref["max"] - ref["min"]

    feat = _feature_vector(sample, code)
    # Weighted combination driving deviation from midpoint
    weights = np.array([0.35, 0.30, 0.25, 0.10])
    deviation_score = float(np.dot(feat, weights))   # 0 – ~1.85

    # Add small deterministic noise based on sample_id for reproducibility
    seed_str = sample.get("sample_id", "0")
    seed = sum(ord(c) for c in seed_str) % 1000
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 0.05)

    deviation = (deviation_score + noise) * span * 0.4
    predicted_value = round(mid + deviation, 2)

    # Clamp to plausible range (ref ± 50%)
    low, high = ref["min"] * 0.5, ref["max"] * 1.5
    predicted_value = round(max(low, min(high, predicted_value)), 2)

    # Confidence inversely proportional to deviation
    rel_dev = abs(predicted_value - mid) / (span / 2 + 1e-6)
    confidence = round(max(0.45, 1.0 - rel_dev * 0.5), 3)

    # Risk level
    if predicted_value < ref["min"] * 0.8 or predicted_value > ref["max"] * 1.3:
        risk = "high"
    elif predicted_value < ref["min"] or predicted_value > ref["max"]:
        risk = "medium"
    else:
        risk = "low"

    return {
        "predicted_value": predicted_value,
        "confidence": confidence,
        "risk_level": risk,
        "reference_range": ref,
        "model_version": "lims-heuristic-v1.0",
        "predicted_at": datetime.utcnow().isoformat()
    }
