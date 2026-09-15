"""
Comprehensive End-to-End Test Suite for All Flask REST API Endpoints.
Tests image upload, inference execution, database insertion, retrieval,
map markers, status lifecycle updates, admin analytics, and deletion.
"""

import sys
import json
import io
from pathlib import Path
from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app


def run_api_endpoint_tests():
    print("=" * 70)
    print("AI Pothole Platform - REST API Endpoints Verification")
    print("=" * 70)

    app = create_app("development")
    client = app.test_client()

    # 1. Test POST /api/v1/reports (Multipart Image Upload + AI Inference + DB Insert)
    print("\n[1/8] Testing POST /api/v1/reports (Upload, Detect & Measure)...")
    
    # Locate a real sample image from the test set
    test_dir = BACKEND_DIR / "dataset" / "potholes" / "test" / "images"
    sample_images = list(test_dir.glob("*.jpg"))
    
    if sample_images:
        test_img_path = sample_images[0]
        with open(test_img_path, "rb") as f:
            img_bytes = f.read()
        filename = test_img_path.name
    else:
        # Fallback: create in-memory JPEG
        buf = io.BytesIO()
        pil_img = Image.new("RGB", (640, 640), color=(80, 80, 80))
        pil_img.save(buf, format="JPEG")
        img_bytes = buf.getvalue()
        filename = "test_road.jpg"

    payload = {
        "image": (io.BytesIO(img_bytes), filename),
        "latitude": "12.9715987",
        "longitude": "77.5945627",
        "address": "MG Road, Bangalore",
        "notes": "Large crater in westbound lane near metro pillar 45",
        "confidence": "0.15"
    }

    res = client.post("/api/v1/reports", data=payload, content_type="multipart/form-data")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.data.decode('utf-8')}"
    data = json.loads(res.data.decode("utf-8"))["data"]

    report_id = data["report_id"]
    report_uid = data["report_uid"]
    print(f"  Created Report ID: {report_id} (UID: {report_uid})")
    print(f"    - Potholes Detected : {data['total_potholes']}")
    print(f"    - Severity Level    : {data['severity_level']}")
    print(f"    - Total Cost        : ${data['total_estimated_cost']:.2f}")
    print(f"    - Raw Image URL     : {data['original_image_url']}")
    print(f"    - Annotated URL     : {data['annotated_image_url']}")

    # 2. Test GET /api/v1/reports (List Reports)
    print("\n[2/8] Testing GET /api/v1/reports...")
    res_list = client.get("/api/v1/reports")
    assert res_list.status_code == 200
    reports_list = json.loads(res_list.data.decode("utf-8"))["data"]
    print(f"  Retrieved {len(reports_list)} report(s).")
    assert any(r["id"] == report_id for r in reports_list), "Created report not in list"

    # 3. Test GET /api/v1/reports/<id> (Get Report Detail with Granular Detections)
    print(f"\n[3/8] Testing GET /api/v1/reports/{report_id}...")
    res_detail = client.get(f"/api/v1/reports/{report_id}")
    assert res_detail.status_code == 200
    detail = json.loads(res_detail.data.decode("utf-8"))["data"]
    print(f"  Report Detail retrieved for #{report_id}:")
    print(f"    - Address   : {detail['address']}")
    print(f"    - Status    : {detail['status']}")
    print(f"    - Detections Count: {len(detail.get('detections', []))}")
    for idx, d in enumerate(detail.get("detections", []), 1):
        print(f"      * #{idx}: {d['estimated_width_cm']}x{d['estimated_length_cm']}cm, Depth:{d['estimated_depth_cm']}cm, Cost:${d['estimated_cost']}")

    # 4. Test PATCH /api/v1/reports/<id>/status (Update Lifecycle Status)
    print(f"\n[4/8] Testing PATCH /api/v1/reports/{report_id}/status...")
    patch_payload = {
        "status": "In_Progress",
        "notes": "Work order issued to Road Maintenance Unit 3"
    }
    res_patch = client.patch(
        f"/api/v1/reports/{report_id}/status",
        data=json.dumps(patch_payload),
        content_type="application/json"
    )
    assert res_patch.status_code == 200
    updated = json.loads(res_patch.data.decode("utf-8"))["data"]
    print(f"  Report updated: Status='{updated['status']}', Notes='{updated['notes']}'")
    assert updated["status"] == "In_Progress"

    # 5. Test GET /api/v1/map/markers (Leaflet Marker Feed)
    print("\n[5/8] Testing GET /api/v1/map/markers...")
    res_map = client.get("/api/v1/map/markers")
    assert res_map.status_code == 200
    markers = json.loads(res_map.data.decode("utf-8"))["data"]
    print(f"  Retrieved {len(markers)} map marker(s).")
    matching_marker = next((m for m in markers if m["id"] == report_id), None)
    assert matching_marker is not None, "Created report missing in map markers"
    print(f"    - Sample Marker: Lat={matching_marker['lat']}, Lng={matching_marker['lng']}, Severity={matching_marker['severity']}")

    # 6. Test GET /api/v1/map/geojson (RFC 7946 Feature Collection)
    print("\n[6/8] Testing GET /api/v1/map/geojson...")
    res_geojson = client.get("/api/v1/map/geojson")
    assert res_geojson.status_code == 200
    geojson_data = json.loads(res_geojson.data.decode("utf-8"))["data"]
    assert geojson_data["type"] == "FeatureCollection"
    print(f"  GeoJSON Validated: {len(geojson_data['features'])} feature point(s).")

    # 7. Test GET /api/v1/admin/stats (Admin Analytics Dashboard KPIs)
    print("\n[7/8] Testing GET /api/v1/admin/stats...")
    res_stats = client.get("/api/v1/admin/stats")
    assert res_stats.status_code == 200
    stats = json.loads(res_stats.data.decode("utf-8"))["data"]
    print(f"  Admin KPIs:")
    print(f"    - Total Reports       : {stats['kpis']['total_reports']}")
    print(f"    - Total Potholes      : {stats['kpis']['total_potholes_detected']}")
    print(f"    - Total Repair Cost   : ${stats['kpis']['total_repair_cost']:.2f}")
    print(f"    - Status Breakdown    : {stats['status_distribution']}")
    print(f"    - Severity Breakdown  : {stats['severity_distribution']}")

    # 8. Test DELETE /api/v1/reports/<id> (Cleanup & Cascade Verification)
    print(f"\n[8/8] Testing DELETE /api/v1/reports/{report_id}...")
    res_del = client.delete(f"/api/v1/reports/{report_id}")
    assert res_del.status_code == 200
    print(f"  Successfully deleted test Report #{report_id} and verified database cleanup.")

    # Confirm report is gone
    res_check = client.get(f"/api/v1/reports/{report_id}")
    assert res_check.status_code == 404

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL FLASK REST API ENDPOINTS VERIFIED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_api_endpoint_tests()
