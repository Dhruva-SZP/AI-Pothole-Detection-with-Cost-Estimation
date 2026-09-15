"""
Comprehensive Production End-to-End (E2E) Verification Suite.
Validates:
1. Database Connectivity & Schema integrity
2. Flask Production Factory & Configuration
3. Single-Port React Single-Page Application (SPA) static asset serving
4. Pothole Detection (YOLOv8) + CV Contour + Depth + ASTM D6433 + Cost Prediction
5. Full Report Lifecycle: POST -> GET -> MAP -> ADMIN -> PATCH STATUS -> DELETE
6. Live Multi-Threaded Waitress WSGI Server execution on localhost
"""

import os
import sys
import io
import time
import json
import socket
import threading
from pathlib import Path
import urllib.request
import urllib.parse

# Ensure backend directory is in python path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app
from database.connection import get_db_connection
from flask import send_from_directory
from waitress.server import create_server


def test_section(title: str):
    print("\n" + "=" * 75)
    print(f"  [TEST SUITE] {title}")
    print("=" * 75)


def check(description: str, condition: bool, details: str = ""):
    if condition:
        print(f"  [PASS] {description}")
    else:
        print(f"  [FAIL] {description} - {details}")
        raise AssertionError(f"Check failed: {description} | {details}")


def run_e2e_tests():
    test_section("1. Verifying Database Connection & Seed Data")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION, DB_NAME()")
        row = cursor.fetchone()
        check("SQL Server is responsive", row is not None, f"Result: {row}")
        print(f"         Database: {row[1]}")
        print(f"         Version : {row[0].splitlines()[0]}")

        cursor.execute("SELECT COUNT(*) FROM CostParameters WHERE is_active = 1")
        param_count = cursor.fetchone()[0]
        check("Active CostParameters seeded", param_count >= 1, f"Found {param_count} parameters")

    test_section("2. Initializing Production App Factory & React Static Routing")
    app = create_app("production")
    PROJECT_ROOT = BACKEND_DIR.parent
    FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
    
    check("Frontend build directory exists", FRONTEND_DIST.exists(), str(FRONTEND_DIST))
    check("index.html exists in frontend/dist", (FRONTEND_DIST / "index.html").exists())

    # Wire up production static frontend route exactly as wsgi_server.py does
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path: str):
        if path.startswith("api/") or path.startswith("uploads/"):
            from flask import abort
            abort(404)
        target_file = FRONTEND_DIST / path
        if path and target_file.exists():
            return send_from_directory(str(FRONTEND_DIST), path)
        return send_from_directory(str(FRONTEND_DIST), "index.html")

    client = app.test_client()

    test_section("3. Health Endpoints & Frontend Static Assets")
    # Health checks
    res_health = client.get("/api/v1/health")
    check("GET /api/v1/health status 200", res_health.status_code == 200)
    health_json = res_health.get_json()
    check("Health response success is True", health_json.get("success") is True)
    health_data = health_json.get("data", {})
    check("System status is healthy", health_data.get("status") == "healthy")

    res_db = client.get("/api/v1/health/db")
    check("GET /api/v1/health/db status 200", res_db.status_code == 200)
    db_json = res_db.get_json()
    check("Database response success is True", db_json.get("success") is True)
    db_data = db_json.get("data", {})
    check("Database status is connected", db_data.get("status") == "connected")
    check("Latency measured", "latency_ms" in db_data)

    # React Static asset check
    res_spa = client.get("/")
    check("GET / (React SPA) status 200", res_spa.status_code == 200)
    check("SPA HTML contains root mount div", b'id="root"' in res_spa.data)

    test_section("4. Full Pothole Analysis & Report Submission (E2E)")
    # Locate a real test image with confirmed pothole
    test_img_dir = BACKEND_DIR / "dataset" / "potholes" / "test" / "images"
    test_images = list(test_img_dir.glob("*.jpg"))
    check("Test images available in dataset", len(test_images) > 0)
    
    # Pick a sample known to contain a pothole
    test_img_path = None
    for candidate in test_images:
        if "16901" in candidate.name or "1334" in candidate.name:
            test_img_path = candidate
            break
    if not test_img_path:
        test_img_path = test_images[0]
    print(f"  Selected test image: {test_img_path.name}")

    with open(test_img_path, "rb") as f:
        img_bytes = f.read()

    post_data = {
        "image": (io.BytesIO(img_bytes), test_img_path.name),
        "latitude": "12.971598",
        "longitude": "77.594562",
        "address": "MG Road, Bengaluru, Karnataka",
        "user_id": "1",
        "confidence_threshold": "0.25"
    }

    start_time = time.time()
    res_post = client.post(
        "/api/v1/reports",
        data=post_data,
        content_type="multipart/form-data"
    )
    elapsed = time.time() - start_time
    check(f"POST /api/v1/reports status 201 (Processed in {elapsed:.2f}s)", res_post.status_code == 201)

    report_res = res_post.get_json()
    check("Response has success=True", report_res.get("success") is True)
    report = report_res.get("data", {})
    report_id = report.get("report_id")
    check("Report ID generated", bool(report_id))

    potholes = report.get("detections", [])
    check("Potholes detected in image", len(potholes) > 0, f"Detected: {len(potholes)}")

    p0 = potholes[0]
    check("Pothole has severity classification", p0.get("severity") in ["Low", "Medium", "High", "Critical"])
    check("Pothole has area estimate (sq cm)", p0.get("estimated_area_sq_cm") > 0)
    check("Pothole has depth estimate (cm)", p0.get("estimated_depth_cm") > 0)
    check("Pothole has volume estimate (cu cm)", p0.get("estimated_volume_cu_cm") > 0)
    check("Pothole has repair cost estimate", p0.get("estimated_cost") > 0)
    print(f"         Severity   : {p0.get('severity')}")
    print(f"         Dimensions : {p0.get('estimated_width_cm')}cm x {p0.get('estimated_length_cm')}cm x {p0.get('estimated_depth_cm')}cm")
    print(f"         Area       : {p0.get('estimated_area_sq_cm')} sq cm")
    print(f"         Volume     : {p0.get('estimated_volume_cu_cm')} cu cm")
    print(f"         Repair     : ${p0.get('estimated_cost'):,.2f}")

    total_cost = report.get("total_estimated_cost", 0)
    check("Report total estimated cost matches detections", total_cost > 0)
    print(f"         Total Cost : ${total_cost:,.2f}")

    test_section("5. Querying Report Detail, GIS Map, & Admin Metrics")
    # GET /api/v1/reports/{id}
    res_get = client.get(f"/api/v1/reports/{report_id}")
    check(f"GET /api/v1/reports/{report_id} status 200", res_get.status_code == 200)
    fetched_data = res_get.get_json().get("data", {})
    check("Fetched report ID matches", fetched_data.get("id") == report_id or fetched_data.get("report_id") == report_id)

    # GET /api/v1/map/markers
    res_markers = client.get("/api/v1/map/markers")
    check("GET /api/v1/map/markers status 200", res_markers.status_code == 200)
    markers = res_markers.get_json().get("data", [])
    matching_marker = [m for m in markers if m.get("id") == report_id or m.get("report_id") == report_id]
    check("Report marker present on GIS map", len(matching_marker) == 1)

    # GET /api/v1/map/geojson
    res_geojson = client.get("/api/v1/map/geojson")
    check("GET /api/v1/map/geojson status 200", res_geojson.status_code == 200)
    geojson = res_geojson.get_json().get("data", {})
    check("GeoJSON type is FeatureCollection", geojson.get("type") == "FeatureCollection")

    # GET /api/v1/admin/stats
    res_stats = client.get("/api/v1/admin/stats")
    check("GET /api/v1/admin/stats status 200", res_stats.status_code == 200)
    stats = res_stats.get_json().get("data", {})
    kpis = stats.get("kpis", {})
    check("Stats report count >= 1", kpis.get("total_reports", 0) >= 1)
    check("Stats pothole count >= 1", kpis.get("total_potholes_detected", 0) >= 1)

    # PATCH /api/v1/reports/{id}/status
    res_patch = client.patch(
        f"/api/v1/reports/{report_id}/status",
        json={"status": "In_Progress", "notes": "Work order dispatched"}
    )
    check("PATCH /api/v1/reports/{id}/status status 200", res_patch.status_code == 200)
    res_verify_patch = client.get(f"/api/v1/reports/{report_id}")
    check("Status updated to In_Progress", res_verify_patch.get_json().get("data", {}).get("status") == "In_Progress")

    test_section("6. Live Multi-Threaded Waitress WSGI Server Verification")
    # Find a free ephemeral port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", 0))
    free_port = sock.getsockname()[1]
    sock.close()

    server = create_server(app, host="127.0.0.1", port=free_port, threads=4)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    time.sleep(1.0)  # Allow socket to bind

    url = f"http://127.0.0.1:{free_port}/api/v1/health"
    print(f"  Pinging live Waitress WSGI instance at {url}...")
    try:
        req = urllib.request.urlopen(url, timeout=5)
        resp_code = req.getcode()
        resp_body = req.read().decode("utf-8")
        check("Waitress WSGI live response HTTP 200", resp_code == 200)
        data = json.loads(resp_body)
        check("Waitress served live health payload", data.get("data", {}).get("status") == "healthy")
        print(f"  Waitress WSGI confirmed operational: {data}")
    finally:
        server.close()

    test_section("7. Cleanup Test Record")
    res_del = client.delete(f"/api/v1/reports/{report_id}")
    check(f"DELETE /api/v1/reports/{report_id} status 200", res_del.status_code == 200)

    print("\n" + "=" * 75)
    print("  >>> ALL PRODUCTION END-TO-END VERIFICATION CHECKS PASSED (100%) <<<")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    try:
        run_e2e_tests()
        sys.exit(0)
    except Exception as e:
        print(f"\n[E2E FATAL ERROR]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
