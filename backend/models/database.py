"""MongoDB connection manager."""
import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure


_client = None
_db = None


def get_db():
    global _client, _db
    if _db is None:
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/lims_db")
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        db_name = uri.split("/")[-1].split("?")[0]
        _db = _client[db_name]
        _ensure_indexes(_db)
    return _db


def _ensure_indexes(db):
    db.users.create_index([("username", ASCENDING)], unique=True)
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.samples.create_index([("sample_id", ASCENDING)], unique=True)
    db.samples.create_index([("status", ASCENDING)])
    db.samples.create_index([("created_at", DESCENDING)])
    db.test_results.create_index([("sample_id", ASCENDING)])
    db.test_results.create_index([("status", ASCENDING)])
    db.test_results.create_index([("created_at", DESCENDING)])


def ping():
    try:
        get_db().command("ping")
        return True
    except ConnectionFailure:
        return False
