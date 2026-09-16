"""
Production Multi-Threaded WSGI Server for Microsoft Windows using Waitress.
Serves the Flask REST API and compiled React Single-Page Application on port 5000.
"""

import os
import sys
from pathlib import Path
from flask import send_from_directory
from waitress import serve

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

sys.path.insert(0, str(BACKEND_DIR))
from app import create_app

# Instantiate production app
app = create_app("production")

# If compiled React assets exist, serve them through Flask for single-port deployment
if FRONTEND_DIST.exists():
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path: str):
        # Do not intercept API or Uploads routes
        if path.startswith("api/") or path.startswith("uploads/"):
            from flask import abort
            abort(404)

        target_file = FRONTEND_DIST / path
        if path and target_file.exists():
            return send_from_directory(str(FRONTEND_DIST), path)
        return send_from_directory(str(FRONTEND_DIST), "index.html")
    app.logger.info("Serving compiled React frontend from: %s", FRONTEND_DIST)
else:
    app.logger.warning("Compiled React dist folder not found at [%s]. Running in API-only mode.", FRONTEND_DIST)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    threads = int(os.getenv("WSGI_THREADS", 8))

    from database.connection import test_connection, get_safe_db_summary
    db_summary = get_safe_db_summary()
    db_check = test_connection()

    print("\n" + "=" * 75)
    print("  AI Pothole Detection & Cost Prediction - Production WSGI Server")
    print("=" * 75)
    print(f"  Engine       : Waitress WSGI (Multi-Threaded Server)")
    print(f"  Listening on : http://0.0.0.0:{port} (Local: http://127.0.0.1:{port})")
    print(f"  Worker Pool  : {threads} threads")
    print(f"  API Health   : http://127.0.0.1:{port}/api/v1/health")
    print(f"  DB Endpoint  : http://127.0.0.1:{port}/api/v1/health/db")
    print(f"  DB Target    : {db_summary}")
    if db_check["success"]:
        print(f"  DB Status    : [CONNECTED] {db_check['database']} on {db_check['server']} ({db_check['driver']})")
    else:
        print(f"  DB Status    : [DISCONNECTED] {db_check['error']}")
    print(f"  Static Build : {'Mounted (Single-port UI)' if FRONTEND_DIST.exists() else 'API-only mode'}")
    print("=" * 75 + "\n")

    serve(app, host="0.0.0.0", port=port, threads=threads)
