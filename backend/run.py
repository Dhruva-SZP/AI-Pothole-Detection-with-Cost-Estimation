"""
Backend Application WSGI Entrypoint.
Can be executed directly for development or served via WSGI server (Waitress/Gunicorn).
"""

import os
import sys
from pathlib import Path

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app

# Application instance for WSGI runners
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    print(f"\n==================================================================")
    print(f"  AI Pothole Detection Platform - Backend Server")
    print(f"  Listening on: http://127.0.0.1:{port}")
    print(f"  Health Check: http://127.0.0.1:{port}/api/v1/health")
    print(f"  DB Status   : http://127.0.0.1:{port}/api/v1/health/db")
    print(f"==================================================================\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
