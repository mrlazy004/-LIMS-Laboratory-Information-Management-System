"""Test result routes with AI prediction."""
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from datetime import datetime, timezone

from models.database import get_db
from models.schemas import get_default_test_result
from middleware.auth import token_required
from utils.helpers import serialise, ok, err, paginate
from utils.ai_predictor import predict

tests_bp = Blueprint("tests", __name__, url_prefix="/api/tests")


@tests_bp.get("")
@token_required
def list_tests():
    db = get_db()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    sample_id = request.args.get("sample_id")
    status = request.args.get("status")
    category = request.args.get("category")

    query = {}
    if sample_id:
        query["sample_id"] = sample_id
    if status:
        query["status"] = status
    if category:
        query["category"] = category

    result = paginate(db.test_results, query, page, per_page)
    return ok(result)


@tests_bp.post("")
@token_required
def create_test():
    data = request.get_json(silent=True) or {}
    if not data.get("sample_id") or not data.get("test_name"):
        return err("sample_id and test_name are required")

    db = get_db()
    sample = db.samples.find_one({"sample_id": data["sample_id"]})
    if not sample:
        return err("Sample not found", 404)

    username = get_jwt_identity()

    # Run AI prediction
    test_code = data.get("test_code", data["test_name"][:4].upper())
    ai = predict(sample, test_code)
    data["ai_prediction"] = ai

    test = get_default_test_result(data, username)
    result = db.test_results.insert_one(test)
    test["_id"] = result.inserted_id

    # Update sample status to processing if still "received"
    if sample.get("status") == "received":
        db.samples.update_one(
            {"sample_id": data["sample_id"]},
            {"$set": {"status": "processing", "updated_at": datetime.now(timezone.utc)}}
        )

    return ok(serialise(test), "Test result created", 201)


@tests_bp.get("/<test_id>")
@token_required
def get_test(test_id):
    from bson import ObjectId
    db = get_db()
    try:
        test = db.test_results.find_one({"_id": ObjectId(test_id)})
    except Exception:
        return err("Invalid test ID", 400)
    if not test:
        return err("Test not found", 404)
    return ok(serialise(test))


@tests_bp.put("/<test_id>")
@token_required
def update_test(test_id):
    from bson import ObjectId
    data = request.get_json(silent=True) or {}
    db = get_db()
    try:
        oid = ObjectId(test_id)
    except Exception:
        return err("Invalid test ID", 400)

    test = db.test_results.find_one({"_id": oid})
    if not test:
        return err("Test not found", 404)

    username = get_jwt_identity()
    allowed = {"status", "result_value", "result_unit", "reference_range",
               "is_abnormal", "notes", "category", "test_code"}
    update = {k: v for k, v in data.items() if k in allowed}
    update["updated_at"] = datetime.now(timezone.utc)

    # Auto-set verified info when completing
    if update.get("status") == "completed":
        update["verified_by"] = username
        update["verified_at"] = datetime.now(timezone.utc)
        update["performed_at"] = update.get("performed_at", datetime.now(timezone.utc).isoformat())

        # Check if all tests for this sample are done → mark sample completed
        sample_id = test["sample_id"]
        remaining = db.test_results.count_documents({
            "sample_id": sample_id,
            "status": {"$in": ["pending", "in_progress"]},
            "_id": {"$ne": oid}
        })
        if remaining == 0:
            db.samples.update_one(
                {"sample_id": sample_id},
                {"$set": {"status": "completed", "updated_at": datetime.now(timezone.utc)}}
            )

    db.test_results.update_one({"_id": oid}, {"$set": update})
    updated = db.test_results.find_one({"_id": oid})
    return ok(serialise(updated), "Test updated")


@tests_bp.delete("/<test_id>")
@token_required
def delete_test(test_id):
    from bson import ObjectId
    db = get_db()
    try:
        oid = ObjectId(test_id)
    except Exception:
        return err("Invalid test ID", 400)

    test = db.test_results.find_one({"_id": oid})
    if not test:
        return err("Test not found", 404)

    db.test_results.delete_one({"_id": oid})
    return ok(message="Test deleted")


@tests_bp.post("/predict")
@token_required
def ai_predict():
    """Standalone AI prediction endpoint."""
    data = request.get_json(silent=True) or {}
    sample_id = data.get("sample_id")
    test_code = data.get("test_code", "GLU")

    db = get_db()
    sample = db.samples.find_one({"sample_id": sample_id}) if sample_id else {}
    prediction = predict(sample or {}, test_code)
    return ok(prediction)
