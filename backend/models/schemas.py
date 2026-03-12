"""
MongoDB Schema Definitions for LIMS
All documents use snake_case field names.
"""

from datetime import datetime, timezone

# ─── User Schema ───────────────────────────────────────────────────────────────
USER_SCHEMA = {
    "_id": "ObjectId (auto)",
    "username": "str (unique)",
    "email": "str (unique)",
    "password_hash": "str (bcrypt)",
    "role": "str: admin | technician | viewer",
    "created_at": "datetime",
    "last_login": "datetime"
}

# ─── Sample Schema ─────────────────────────────────────────────────────────────
SAMPLE_SCHEMA = {
    "_id": "ObjectId (auto)",
    "sample_id": "str (unique, e.g. LIMS-2024-0001)",
    "name": "str",
    "type": "str: blood | urine | tissue | swab | serum | other",
    "patient_id": "str",
    "patient_name": "str",
    "collected_by": "str (username)",
    "collection_date": "datetime",
    "status": "str: received | processing | completed | rejected",
    "priority": "str: routine | urgent | stat",
    "notes": "str",
    "metadata": {
        "temperature": "float (°C at collection)",
        "volume_ml": "float",
        "container_type": "str"
    },
    "created_at": "datetime",
    "updated_at": "datetime",
    "created_by": "str (user_id)"
}

# ─── Test Result Schema ────────────────────────────────────────────────────────
TEST_RESULT_SCHEMA = {
    "_id": "ObjectId (auto)",
    "sample_id": "str (ref → Sample.sample_id)",
    "test_name": "str",
    "test_code": "str (e.g. CBC, LFT, RFT)",
    "category": "str: hematology | biochemistry | microbiology | immunology | urinalysis",
    "status": "str: pending | in_progress | completed | failed",
    "result_value": "float | str",
    "result_unit": "str",
    "reference_range": {"min": "float", "max": "float"},
    "is_abnormal": "bool",
    "ai_prediction": {
        "predicted_value": "float",
        "confidence": "float (0-1)",
        "risk_level": "str: low | medium | high",
        "model_version": "str"
    },
    "performed_by": "str (username)",
    "performed_at": "datetime",
    "verified_by": "str (username)",
    "verified_at": "datetime",
    "notes": "str",
    "created_at": "datetime",
    "updated_at": "datetime"
}


def get_default_user(username, email, password_hash, role="technician"):
    return {
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "role": role,
        "created_at": datetime.now(timezone.utc),
        "last_login": None
    }


def get_default_sample(data, created_by):
    now = datetime.now(timezone.utc)
    return {
        "sample_id": data.get("sample_id"),
        "name": data.get("name"),
        "type": data.get("type", "other"),
        "patient_id": data.get("patient_id", ""),
        "patient_name": data.get("patient_name", ""),
        "collected_by": data.get("collected_by", created_by),
        "collection_date": data.get("collection_date", now.isoformat()),
        "status": "received",
        "priority": data.get("priority", "routine"),
        "notes": data.get("notes", ""),
        "metadata": data.get("metadata", {}),
        "created_at": now,
        "updated_at": now,
        "created_by": created_by
    }


def get_default_test_result(data, performed_by):
    now = datetime.now(timezone.utc)
    return {
        "sample_id": data.get("sample_id"),
        "test_name": data.get("test_name"),
        "test_code": data.get("test_code", ""),
        "category": data.get("category", "biochemistry"),
        "status": data.get("status", "pending"),
        "result_value": data.get("result_value"),
        "result_unit": data.get("result_unit", ""),
        "reference_range": data.get("reference_range", {}),
        "is_abnormal": data.get("is_abnormal", False),
        "ai_prediction": data.get("ai_prediction"),
        "performed_by": performed_by,
        "performed_at": data.get("performed_at", now.isoformat()),
        "verified_by": None,
        "verified_at": None,
        "notes": data.get("notes", ""),
        "created_at": now,
        "updated_at": now
    }
