"""Sample management routes."""
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from datetime import datetime, timezone
from bson import ObjectId

from models.database import get_db
from models.schemas import get_default_sample
from middleware.auth import token_required
from utils.helpers import serialise, ok, err, paginate

samples_bp = Blueprint("samples", __name__, url_prefix="/api/samples")


def _next_sample_id(db):
    year = datetime.now().year
    prefix = f"LIMS-{year}-"
    last = db.samples.find_one(
        {"sample_id": {"$regex": f"^{prefix}"}},
        sort=[("sample_id", -1)]
    )
    if last:
        num = int(last["sample_id"].split("-")[-1]) + 1
    else:
        num = 1
    return f"{prefix}{num:04d}"


@samples_bp.get("")
@token_required
def list_samples():
    db = get_db()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    status = request.args.get("status")
    priority = request.args.get("priority")
    search = request.args.get("search", "").strip()

    query = {}
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if search:
        query["$or"] = [
            {"sample_id": {"$regex": search, "$options": "i"}},
            {"patient_name": {"$regex": search, "$options": "i"}},
            {"patient_id": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}},
        ]

    result = paginate(db.samples, query, page, per_page)
    return ok(result)


@samples_bp.post("")
@token_required
def create_sample():
    data = request.get_json(silent=True) or {}
    if not data.get("name") or not data.get("type"):
        return err("name and type are required")

    db = get_db()
    username = get_jwt_identity()
    data["sample_id"] = _next_sample_id(db)
    sample = get_default_sample(data, username)
    result = db.samples.insert_one(sample)
    sample["_id"] = result.inserted_id
    return ok(serialise(sample), "Sample created", 201)


@samples_bp.get("/<sample_id>")
@token_required
def get_sample(sample_id):
    db = get_db()
    sample = db.samples.find_one({"sample_id": sample_id})
    if not sample:
        return err("Sample not found", 404)
    tests = list(db.test_results.find({"sample_id": sample_id}))
    data = serialise(sample)
    data["test_results"] = serialise(tests)
    return ok(data)


@samples_bp.put("/<sample_id>")
@token_required
def update_sample(sample_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    sample = db.samples.find_one({"sample_id": sample_id})
    if not sample:
        return err("Sample not found", 404)

    allowed = {"name", "type", "patient_id", "patient_name", "status",
               "priority", "notes", "metadata", "collected_by", "collection_date"}
    update = {k: v for k, v in data.items() if k in allowed}
    update["updated_at"] = datetime.now(timezone.utc)

    if "status" in update and update["status"] not in ("received", "processing", "completed", "rejected"):
        return err("Invalid status value")

    db.samples.update_one({"sample_id": sample_id}, {"$set": update})
    updated = db.samples.find_one({"sample_id": sample_id})
    return ok(serialise(updated), "Sample updated")


@samples_bp.delete("/<sample_id>")
@token_required
def delete_sample(sample_id):
    db = get_db()
    sample = db.samples.find_one({"sample_id": sample_id})
    if not sample:
        return err("Sample not found", 404)

    db.samples.delete_one({"sample_id": sample_id})
    db.test_results.delete_many({"sample_id": sample_id})
    return ok(message="Sample and related tests deleted")


@samples_bp.get("/stats/summary")
@token_required
def stats():
    db = get_db()
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    sample_stats = {s["_id"]: s["count"] for s in db.samples.aggregate(pipeline)}

    test_pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    test_stats = {s["_id"]: s["count"] for s in db.test_results.aggregate(test_pipeline)}

    recent = list(db.samples.find({}, {"_id": 0, "sample_id": 1, "name": 1, "status": 1, "created_at": 1})
                  .sort("created_at", -1).limit(5))

    return ok({
        "samples": {
            "total": db.samples.count_documents({}),
            "by_status": sample_stats
        },
        "tests": {
            "total": db.test_results.count_documents({}),
            "completed": test_stats.get("completed", 0),
            "pending": test_stats.get("pending", 0) + test_stats.get("in_progress", 0),
            "failed": test_stats.get("failed", 0),
            "by_status": test_stats
        },
        "recent_samples": serialise(recent)
    })
