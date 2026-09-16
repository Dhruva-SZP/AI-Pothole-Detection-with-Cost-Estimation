"""
System & Database Health Check Endpoints Blueprint.
"""

import sys
import time
from datetime import datetime, timezone
from flask import Blueprint, current_app
from app.errors import api_response, api_error
from database.connection import test_connection

health_bp = Blueprint("health", __name__, url_prefix="/api/v1")
START_TIME = time.time()


@health_bp.route("/health", methods=["GET"])
def system_health():
    """
    Returns general system health, versioning, and uptime metrics.
    """
    uptime_seconds = round(time.time() - START_TIME, 2)
    data = {
        "status": "healthy",
        "service": "AI Pothole Detection API",
        "version": "1.0.0",
        "environment": current_app.config.get("FLASK_ENV", "development"),
        "python_version": sys.version.split()[0],
        "uptime_seconds": uptime_seconds,
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
    return api_response(data=data, message="System is running smoothly.")


@health_bp.route("/health/db", methods=["GET"])
def database_health():
    """
    Tests direct connectivity to Microsoft SQL Server via pyodbc.
    """
    start = time.perf_counter()
    result = test_connection()
    latency_ms = round((time.perf_counter() - start) * 1000, 2)

    if result["success"]:
        return api_response(
            data={
                "status": "connected",
                "server": result["server"],
                "database": result["database"],
                "version": result["version"],
                "driver": result.get("driver", "unknown"),
                "latency_ms": latency_ms
            },
            message="SQL Server connection is healthy and responsive."
        )
    else:
        return api_error(
            message="SQL Server database connection failed.",
            status_code=503,
            details={
                "error": result["error"],
                "server": result.get("server"),
                "database": result.get("database"),
                "driver": result.get("driver", "unknown"),
                "latency_ms": latency_ms
            }
        )
