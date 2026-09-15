"""
Automated Test Verification for Dimension Measurement, Depth Estimation & Repair Cost Prediction.
Tests photogrammetric calibration, cavity depth heuristics, ASTM severity classification,
and municipal repair cost models.
"""

import sys
import numpy as np
import cv2
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.metrics import DimensionEstimator, CostPredictor, CameraCalibration
from app.services.detector import PotholeDetector


def run_metrics_tests():
    print("=" * 70)
    print("AI Pothole Dimension & Cost Prediction Verification")
    print("=" * 70)

    # 1. Test DimensionEstimator with Synthetic Pothole Cavity
    print("\n[1/4] Testing DimensionEstimator Photogrammetric Math...")
    estimator = DimensionEstimator()

    # Create a 640x640 synthetic test patch with a simulated 120x80px cavity
    dummy_img = np.full((640, 640, 3), 90, dtype=np.uint8)
    cv2.ellipse(dummy_img, (320, 400), (60, 40), 0, 0, 360, (25, 25, 25), -1)

    bbox = [260, 360, 380, 440]
    metrics = estimator.estimate_dimensions(bbox, dummy_img)

    print(f"  Physical Measurements:")
    print(f"    - Estimated Width  : {metrics['width_cm']:.1f} cm")
    print(f"    - Estimated Length : {metrics['length_cm']:.1f} cm")
    print(f"    - Estimated Depth  : {metrics['depth_cm']:.1f} cm")
    print(f"    - Surface Area     : {metrics['area_sq_cm']:.1f} cm^2 ({metrics['area_sq_m']:.4f} m^2)")
    print(f"    - Cavity Volume    : {metrics['volume_cu_cm']:.1f} cm^3 ({metrics['volume_cu_m']:.6f} m^3)")
    print(f"    - ASTM Severity    : {metrics['severity']}")

    assert metrics["width_cm"] > 0, "Width must be positive"
    assert metrics["length_cm"] > 0, "Length must be positive"
    assert 2.0 <= metrics["depth_cm"] <= 18.0, "Depth must fall within 2.0 - 18.0 cm"
    assert metrics["severity"] in ["Low", "Medium", "High", "Critical"], "Invalid severity"

    # 2. Test CostPredictor Formulas
    print("\n[2/4] Testing Municipal Repair Cost Prediction Formulas...")
    predictor = CostPredictor()

    single_cost = predictor.calculate_pothole_cost(
        volume_cu_m=metrics["volume_cu_m"],
        area_sq_m=metrics["area_sq_m"],
        severity=metrics["severity"]
    )
    print(f"  Single Pothole Repair Cost : ${single_cost:.2f}")
    assert single_cost >= 0, "Pothole repair cost must be non-negative"

    # Test report total with site mobilization
    sample_detections = [
        {"estimated_cost": single_cost, "severity": metrics["severity"]},
        {"estimated_cost": single_cost * 0.8, "severity": "Medium"}
    ]
    report_total = predictor.calculate_report_total_cost(sample_detections)
    print(f"  Report Total (2 Potholes + Mobilization & Equipment Overhead): ${report_total:.2f}")
    assert report_total >= predictor.rates["min_service_charge"], "Must meet minimum service charge"

    # 3. Test End-to-End Detector with Real Test Pothole Image
    print("\n[3/4] Running Integrated Detection, Sizing & Cost Prediction on Real Image...")
    test_dir = BACKEND_DIR / "dataset" / "potholes" / "test" / "images"
    sample_images = list(test_dir.glob("*.jpg"))
    test_img_path = sample_images[0] if sample_images else (BACKEND_DIR / "uploads" / "raw" / "unit_test_road.jpg")
    annotated_out_path = BACKEND_DIR / "uploads" / "annotated" / "metrics_test_annotated.jpg"

    detector = PotholeDetector()
    results = detector.detect(
        image_input=test_img_path,
        conf_threshold=0.15,
        save_annotated_path=annotated_out_path
    )

    print(f"  Full Pipeline Output Summary:")
    print(f"    - Source Image       : {test_img_path.name}")
    print(f"    - Total Detected     : {results['total_potholes']}")
    print(f"    - Overall Severity   : {results['severity_level']}")
    print(f"    - Total Repair Cost  : ${results['total_estimated_cost']:.2f}")
    print(f"    - Top Confidence     : {results['top_confidence'] * 100:.1f}%")

    # 4. Verify Individual Granular Pothole Detections
    print("\n[4/4] Verifying Granular Pothole Detection Items...")
    for idx, d in enumerate(results["detections"], 1):
        print(f"  Pothole #{idx}:")
        print(f"    - Bounding Box : {d['bbox']}")
        print(f"    - Confidence   : {d['confidence'] * 100:.1f}%")
        print(f"    - Dimensions   : {d['estimated_width_cm']}cm x {d['estimated_length_cm']}cm")
        print(f"    - Depth        : {d['estimated_depth_cm']} cm")
        print(f"    - Area         : {d['estimated_area_sq_cm']} cm^2")
        print(f"    - Volume       : {d['estimated_volume_cu_cm']} cm^3")
        print(f"    - Item Cost    : ${d['estimated_cost']:.2f}")
        print(f"    - Severity     : {d['severity']}")

    assert Path(annotated_out_path).exists(), "Annotated image was not written to disk"
    print(f"\n  Annotated HUD Image Saved: {annotated_out_path}")

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL DIMENSION, DEPTH & COST PREDICTION TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_metrics_tests()
