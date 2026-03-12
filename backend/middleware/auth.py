"""Authentication middleware and helpers."""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models.database import get_db


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception as e:
            return jsonify({"error": "Invalid or missing token", "detail": str(e)}), 401
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                verify_jwt_in_request()
                identity = get_jwt_identity()
                db = get_db()
                user = db.users.find_one({"username": identity})
                if not user or user.get("role") not in roles:
                    return jsonify({"error": "Insufficient permissions"}), 403
            except Exception as e:
                return jsonify({"error": str(e)}), 401
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_current_user():
    identity = get_jwt_identity()
    db = get_db()
    return db.users.find_one({"username": identity}, {"password_hash": 0})
