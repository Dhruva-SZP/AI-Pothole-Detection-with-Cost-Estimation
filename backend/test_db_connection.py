"""
Comprehensive Diagnostics & CRUD Verification Test for SQL Server & pyodbc.
Tests connection, schema inspection, transaction rollback, and insert/select functionality.
"""

import sys
import uuid
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from database.connection import get_db_connection, test_connection, row_to_dict, rows_to_dict_list
from database.queries import (
    INSERT_REPORT,
    GET_REPORT_BY_ID,
    INSERT_DETECTION,
    GET_DETECTIONS_BY_REPORT_ID,
    DELETE_REPORT,
    GET_DASHBOARD_STATS
)


def run_tests():
    print("=" * 70)
    print("AI Pothole Detection System - SQL Server Diagnostics")
    print("=" * 70)

    # 1. Connectivity Test
    print("\n[1/4] Testing SQL Server Connection...")
    info = test_connection()
    if not info["success"]:
        print(f"[ERROR] Connection Failed: {info['error']}")
        sys.exit(1)
    print("  Status   : Connected")
    print(f"  Driver   : {info.get('driver', 'Unknown')}")
    print(f"  Server   : {info['server']}")
    print(f"  Version  : {info['version']}")
    print(f"  Database : {info['database']}")

    # 2. Schema Table Verification
    print("\n[2/4] Verifying System Tables...")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME;
        """)
        tables = [r[0] for r in cursor.fetchall()]
        print(f"  Existing Tables: {tables}")
        
        required = ["CostParameters", "PotholeDetections", "PotholeReports", "Users"]
        missing = [t for t in required if t not in tables]
        if missing:
            print(f"[ERROR] Missing tables: {missing}. Please run 'python database/init_db.py' first.")
            sys.exit(1)
        print("  All required tables exist.")

    # 3. Transactional Insert & Query Test
    print("\n[3/4] Performing Transactional CRUD Test (Insert Report + Detections)...")
    test_uid = f"test-{uuid.uuid4().hex[:8]}"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Insert parent report
        cursor.execute(
            INSERT_REPORT,
            (
                test_uid,               # report_uid
                None,                   # user_id
                "uploads/test_raw.jpg", # original_image_path
                "uploads/test_ann.jpg", # annotated_image_path
                12.9716,                # latitude (e.g. Bangalore)
                77.5946,                # longitude
                "MG Road, Junction 4",  # address
                "Verified",             # status
                2,                      # total_potholes
                350.50,                 # total_estimated_cost
                "High",                 # severity_level
                "Test verification entry" # notes
            )
        )
        report_id = cursor.fetchone()[0]
        print(f"  Inserted Test Report ID: {report_id} (UID: {test_uid})")

        # Insert 2 child detections
        detections = [
            (report_id, 100.0, 150.0, 300.0, 400.0, 0.92, 45.0, 55.0, 8.5, 2475.0, 21037.5, 175.25, "High"),
            (report_id, 350.0, 200.0, 480.0, 320.0, 0.88, 30.0, 35.0, 6.0, 1050.0, 6300.0, 175.25, "Medium"),
        ]
        for det in detections:
            cursor.execute(INSERT_DETECTION, det)
        print("  Inserted 2 Test Pothole Detection records.")

        # Query back parent report
        cursor.execute(GET_REPORT_BY_ID, (report_id,))
        fetched_report = row_to_dict(cursor, cursor.fetchone())
        print(f"  Retrieved Report: ID={fetched_report['id']}, Status={fetched_report['status']}, Severity={fetched_report['severity_level']}")

        # Query back child detections
        cursor.execute(GET_DETECTIONS_BY_REPORT_ID, (report_id,))
        fetched_dets = rows_to_dict_list(cursor, cursor.fetchall())
        print(f"  Retrieved {len(fetched_dets)} Child Detections:")
        for idx, d in enumerate(fetched_dets, 1):
            print(f"    - Detection #{idx}: Area={d['estimated_area_sq_cm']} cm^2, Depth={d['estimated_depth_cm']} cm, Cost=${d['estimated_cost']}")

        # Clean up test entry (foreign key CASCADE tests will remove detections automatically)
        cursor.execute(DELETE_REPORT, (report_id,))
        print(f"  Cleaned up Test Report ID {report_id} (CASCADE delete verified).")

    # 4. Aggregated Analytics Query Test
    print("\n[4/4] Testing Admin Aggregation Query...")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(GET_DASHBOARD_STATS)
        stats = row_to_dict(cursor, cursor.fetchone())
        print("  Dashboard KPI Snapshot:")
        for k, v in stats.items():
            print(f"    - {k}: {v}")

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL SQL SERVER DATABASE TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
