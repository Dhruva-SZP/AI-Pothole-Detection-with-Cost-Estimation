"""
Flask Application Factory Module.
Initializes the Flask application, registers blueprints, sets up CORS, static file serving, and error handling.
"""

import os
from pathlib import Path
from flask import Flask, send_from_directory
from flask_cors import CORS

from app.config import config_by_name, Config
from app.logger import setup_logger
from app.errors import register_error_handlers
from app.utils.storage import ensure_storage_directories
from app.routes.health import health_bp


def create_app(config_name: str = None) -> Flask:
    """
    Creates and configures an instance of the Flask application.
    """
    app = Flask(__name__)

    # 1. Load configuration
    env_mode = config_name or os.getenv("FLASK_ENV", "development")
    selected_config = config_by_name.get(env_mode, Config)
    app.config.from_object(selected_config)

    # 2. Setup Centralized Logging
    app_logger = setup_logger(
        name="PotholeApp",
        log_dir=app.config["LOG_FOLDER"]
    )
    app.logger = app_logger
    app_logger.info("Starting AI Pothole Detection Service in [%s] mode...", env_mode)

    # 3. Ensure Storage Directories Exist
    ensure_storage_directories(
        upload_folder=app.config["UPLOAD_FOLDER"],
        annotated_folder=app.config["ANNOTATED_FOLDER"]
    )
    app_logger.info("Upload storage paths verified: %s, %s", 
                    app.config["UPLOAD_FOLDER"], 
                    app.config["ANNOTATED_FOLDER"])

    # 4. Enable Cross-Origin Resource Sharing (CORS)
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True
    )
    app_logger.info("Configured CORS for origins: %s", app.config["CORS_ORIGINS"])

    # 5. Static File Route for Uploaded Images
    base_uploads = Path(__file__).resolve().parent.parent / "uploads"
    base_uploads.mkdir(parents=True, exist_ok=True)

    @app.route("/uploads/<path:subpath>", methods=["GET"])
    def serve_upload(subpath: str):
        """
        Serves uploaded raw and annotated images back to the frontend.
        """
        return send_from_directory(str(base_uploads), subpath)

    # 6. Register Global Error Handlers
    register_error_handlers(app)

    # 7. Register API Blueprints
    from app.routes.reports import reports_bp
    from app.routes.map import map_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(map_bp)
    app.register_blueprint(admin_bp)

    app_logger.info("Registered API Blueprints: health, reports, map, admin")
    app_logger.info("Flask Application initialization complete.")
    return app

