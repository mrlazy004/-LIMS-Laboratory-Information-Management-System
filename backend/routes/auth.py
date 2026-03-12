"""Authentication routes: register, login, profile."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity
import bcrypt
from datetime import datetime, timezone

from models.database import get_db
from models.schemas import get_default_user
from middleware.auth import token_required, get_current_user
from utils.helpers import serialise, ok, err

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "technician")

    if not all([username, email, password]):
        return err("username, email, and password are required")

    if len(password) < 6:
        return err("Password must be at least 6 characters")

    if role not in ("admin", "technician", "viewer"):
        role = "technician"

    db = get_db()
    if db.users.find_one({"$or": [{"username": username}, {"email": email}]}):
        return err("Username or email already exists", 409)

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = get_default_user(username, email, pw_hash, role)
    db.users.insert_one(user)

    token = create_access_token(identity=username)
    return ok({"token": token, "username": username, "role": role}, "Registered successfully", 201)


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not all([username, password]):
        return err("username and password are required")

    db = get_db()
    user = db.users.find_one({"username": username})
    if not user or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return err("Invalid credentials", 401)

    db.users.update_one({"_id": user["_id"]}, {"$set": {"last_login": datetime.now(timezone.utc)}})
    token = create_access_token(identity=username)
    return ok({"token": token, "username": username, "role": user.get("role", "technician")}, "Login successful")


@auth_bp.get("/me")
@token_required
def profile():
    user = get_current_user()
    if not user:
        return err("User not found", 404)
    return ok(serialise(user))


@auth_bp.get("/users")
@token_required
def list_users():
    db = get_db()
    users = list(db.users.find({}, {"password_hash": 0}))
    return ok(serialise(users))
