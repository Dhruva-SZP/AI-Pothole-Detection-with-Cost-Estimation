import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.detector import PotholeDetector
from database.connection import get_db_connection

weights_path = BACKEND_DIR / "models" / "weights" / "best.pt"
detector = PotholeDetector(weights_path=weights_path)

raw_path = BACKEND_DIR / "uploads" / "raw" / "rep_1ca0b8132904_raw.webp"
annotated_path = BACKEND_DIR / "uploads" / "annotated" / "rep_1ca0b8132904_annotated.webp"

result = detector.detect(
    image_input=raw_path,
    conf_threshold=0.25,
    save_annotated_path=annotated_path
)

print(f"Reprocessed: {result['total_potholes']} potholes detected, severity: {result['severity_level']}, cost: ${result['total_estimated_cost']}")

# Update SQL Server database for report 8
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE PotholeReports
        SET total_potholes = ?,
            total_estimated_cost = ?,
            severity_level = ?,
            updated_at = SYSUTCDATETIME()
        WHERE id = 8
    """, (result['total_potholes'], result['total_estimated_cost'], result['severity_level']))
    
    # Delete any old detections
    cursor.execute("DELETE FROM PotholeDetections WHERE report_id = 8")
    
    # Insert new detections
    for d in result['detections']:
        cursor.execute("""
            INSERT INTO PotholeDetections (
                report_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                confidence, estimated_width_cm, estimated_length_cm,
                estimated_depth_cm, estimated_area_sq_cm, estimated_volume_cu_cm,
                estimated_cost, severity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            8, d['bbox'][0], d['bbox'][1], d['bbox'][2], d['bbox'][3],
            d['confidence'], d['estimated_width_cm'], d['estimated_length_cm'],
            d['estimated_depth_cm'], d['estimated_area_sq_cm'], d['estimated_volume_cu_cm'],
            d['estimated_cost'], d['severity']
        ))
    print("Updated Report #8 in SQL Server successfully!")
