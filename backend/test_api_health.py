"""
Automated Test Suite for Flask Application Factory, Health Endpoints & Error Handlers.
Uses Flask's built-in test client for zero-dependency API validation.
"""

import sys
import json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app


def run_api_tests():
    print("=" * 70)
    print("Flask Core Application & Health Endpoints Verification")
    print("=" * 70)

    # 1. Instantiate App via Application Factory
    print("\n[1/4] Initializing Flask App via Application Factory...")
    app = create_app("development")
    client = app.test_client()
    print("  Flask application instance created successfully.")

    # 2. Test System Health Endpoint
    print("\n[2/4] Testing GET /api/v1/health...")
    res = client.get("/api/v1/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    body = json.loads(res.data.decode("utf-8"))
    assert body["success"] is True
    assert body["data"]["status"] == "healthy"
    print(f"  Response [200 OK]:")
    print(f"    - Service    : {body['data']['service']}")
    print(f"    - Version    : {body['data']['version']}")
    print(f"    - Python     : {body['data']['python_version']}")
    print(f"    - Uptime     : {body['data']['uptime_seconds']}s")

    # 3. Test Database Health Endpoint
    print("\n[3/4] Testing GET /api/v1/health/db...")
    res_db = client.get("/api/v1/health/db")
    assert res_db.status_code == 200, f"Expected 200, got {res_db.status_code}"
    body_db = json.loads(res_db.data.decode("utf-8"))
    assert body_db["success"] is True
    assert body_db["data"]["status"] == "connected"
    print(f"  Response [200 OK]:")
    print(f"    - DB Status  : {body_db['data']['status']}")
    print(f"    - DB Server  : {body_db['data']['server']}")
    print(f"    - Database   : {body_db['data']['database']}")
    print(f"    - Latency    : {body_db['data']['latency_ms']} ms")

    # 4. Test Standardized Error Handling (404 Not Found)
    print("\n[4/4] Testing Global 404 Error Handler...")
    res_404 = client.get("/api/v1/does-not-exist")
    assert res_404.status_code == 404, f"Expected 404, got {res_404.status_code}"
    body_404 = json.loads(res_404.data.decode("utf-8"))
    assert body_404["success"] is False
    assert body_404["status_code"] == 404
    print(f"  Response [404 Not Found]:")
    print(f"    - Success    : {body_404['success']}")
    print(f"    - Message    : {body_404['message']}")

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL FLASK CORE & HEALTH ENDPOINT TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_api_tests()
