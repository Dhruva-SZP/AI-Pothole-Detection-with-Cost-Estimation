"""
Application Configuration Module.
Loads environment variables and provides structured configuration classes.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Root backend directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
env_file = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_file)


class Config:
    """Base Configuration."""
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # Server settings
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"
    PORT = int(os.getenv("PORT", 5000))
    
    # Database settings
    DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    DB_SERVER = os.getenv("DB_SERVER", r"localhost\SQLEXPRESS")
    DB_PORT = os.getenv("DB_PORT", "")
    DB_NAME = os.getenv("DB_NAME", "PotholeDetectionDB")
    DB_TRUSTED_CONNECTION = os.getenv("DB_TRUSTED_CONNECTION", "yes").lower() == "yes"
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    # File storage
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB max upload
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    UPLOAD_FOLDER = BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads/raw")
    ANNOTATED_FOLDER = BASE_DIR / os.getenv("ANNOTATED_FOLDER", "uploads/annotated")
    LOG_FOLDER = BASE_DIR / "logs"
    
    # CORS settings
    CORS_ORIGINS = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if origin.strip()
    ]
    
    # Machine Learning Settings
    MODEL_WEIGHTS_PATH = BASE_DIR / os.getenv("MODEL_WEIGHTS_PATH", "models/weights/best.pt")
    MODEL_CONFIDENCE_THRESHOLD = float(os.getenv("MODEL_CONFIDENCE_THRESHOLD", 0.35))


class DevelopmentConfig(Config):
    """Development Configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production Configuration."""
    DEBUG = False
    # In production, ensure strong secret key
    SECRET_KEY = os.getenv("SECRET_KEY", "change-in-production-random-key")


# Environment mapping
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
