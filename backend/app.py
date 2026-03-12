"""LIMS Flask Application Entry Point."""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

load_dotenv()

from routes.auth import auth_bp
from routes.samples import samples_bp
from routes.tests import tests_bp
from models.database import ping


def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 86400  # 24 hours

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    JWTManager(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(samples_bp)
    app.register_blueprint(tests_bp)

    @app.get("/api/health")
    def health():
        db_ok = ping()
        return jsonify({
            "status": "ok" if db_ok else "degraded",
            "database": "connected" if db_ok else "disconnected",
            "version": "1.0.0"
        }), 200 if db_ok else 503

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    print(f"🧪 LIMS API running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "True") == "True")
