import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.detector import PotholeDetector
from database.connection import get_db_connection, row_to_dict

weights_path = BACKEND_DIR / "models" / "weights" / "best.pt"
detector = PotholeDetector(weights_path=weights_path)

with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT id, original_image_path, annotated_image_path, total_potholes FROM PotholeReports")
    reports = cursor.fetchall()

    for row in reports:
        report_id = row[0]
        raw_rel = row[1]
        annotated_rel = row[2]
        old_count = row[3]

        raw_path = BACKEND_DIR / raw_rel.lstrip("/")
        annotated_path = BACKEND_DIR / annotated_rel.lstrip("/")

        if not raw_path.exists():
            print(f"Report #{report_id}: Raw image not found at {raw_path}")
            continue

        result = detector.detect(
            image_input=raw_path,
            conf_threshold=0.20,
            save_annotated_path=annotated_path
        )

        new_count = result["total_potholes"]
        cost = result["total_estimated_cost"]
        severity = result["severity_level"]

        print(f"Report #{report_id}: Old Count={old_count} -> New Count={new_count}, Cost=${cost:.2f}, Severity={severity}")

        cursor.execute("""
            UPDATE PotholeReports
            SET total_potholes = ?,
                total_estimated_cost = ?,
                severity_level = ?,
                updated_at = SYSUTCDATETIME()
            WHERE id = ?
        """, (new_count, cost, severity, report_id))

        cursor.execute("DELETE FROM PotholeDetections WHERE report_id = ?", (report_id,))

        for d in result["detections"]:
            cursor.execute("""
                INSERT INTO PotholeDetections (
                    report_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                    confidence, estimated_width_cm, estimated_length_cm,
                    estimated_depth_cm, estimated_area_sq_cm, estimated_volume_cu_cm,
                    estimated_cost, severity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id, d["bbox"][0], d["bbox"][1], d["bbox"][2], d["bbox"][3],
                d["confidence"], d["estimated_width_cm"], d["estimated_length_cm"],
                d["estimated_depth_cm"], d["estimated_area_sq_cm"], d["estimated_volume_cu_cm"],
                d["estimated_cost"], d["severity"]
            ))

print("All reports reprocessed successfully!")
