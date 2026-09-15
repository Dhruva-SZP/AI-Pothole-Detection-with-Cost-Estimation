"""
Automated Test Verification for YOLOv8 Pothole Detector & OpenCV Annotation Engine.
Tests model initialization, detection inference on real-world pothole test images,
and visual overlay output generation.
"""

import sys
import numpy as np
import cv2
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.detector import PotholeDetector


def run_detector_tests():
    print("=" * 70)
    print("AI Pothole Detector & OpenCV Annotation Verification")
    print("=" * 70)

    # 1. Initialize Detector with best.pt weights
    print("\n[1/4] Initializing PotholeDetector Engine with best.pt...")
    weights_path = BACKEND_DIR / "models" / "weights" / "best.pt"
    detector = PotholeDetector(weights_path=weights_path)
    print(f"  Detector Status : {'Loaded' if detector.is_loaded else 'Failed'}")
    print(f"  Weights File    : {detector.weights_path}")
    assert detector.is_loaded is True, "Detector failed to load model weights"

    # 2. Locate Real Test Pothole Image
    print("\n[2/4] Selecting Real Pothole Test Image from Dataset...")
    test_dir = BACKEND_DIR / "dataset" / "potholes" / "test" / "images"
    sample_images = list(test_dir.glob("*.jpg"))
    
    if sample_images:
        test_input_path = sample_images[0]
        print(f"  Selected real test sample: {test_input_path.name}")
    else:
        # Fallback to creating a test image if dataset not unpacked
        test_input_path = BACKEND_DIR / "uploads" / "raw" / "unit_test_road.jpg"
        test_input_path.parent.mkdir(parents=True, exist_ok=True)
        img = np.full((640, 640, 3), 75, dtype=np.uint8)
        cv2.ellipse(img, (320, 420), (110, 65), 15, 0, 360, (30, 28, 25), -1)
        cv2.imwrite(str(test_input_path), img)
        print(f"  Created test image: {test_input_path.name}")

    # 3. Execute Detection & Annotation Pipeline
    print("\n[3/4] Running Inference & OpenCV Overlay Drawing...")
    annotated_output_path = BACKEND_DIR / "uploads" / "annotated" / "real_pothole_annotated.jpg"
    
    result = detector.detect(
        image_input=test_input_path,
        conf_threshold=0.15,
        save_annotated_path=annotated_output_path
    )

    print(f"  Inference Result Summary:")
    print(f"    - Input Resolution  : {result['image_width']}x{result['image_height']}")
    print(f"    - Total Detections  : {result['total_potholes']}")
    print(f"    - Top Confidence    : {result['top_confidence'] * 100:.1f}%")
    print(f"    - Annotated Output  : {result['annotated_image_path']}")

    # 4. Verify Annotated File Creation
    print("\n[4/4] Verifying Annotated File on Disk...")
    assert Path(result['annotated_image_path']).exists(), "Annotated image was not written to disk"
    file_size_kb = Path(result['annotated_image_path']).stat().st_size / 1024
    print(f"  Annotated file verified: {file_size_kb:.1f} KB")

    print("\n" + "=" * 70)
    print("[SUCCESS] YOLOv8 DETECTION & OPENCV ANNOTATION TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_detector_tests()
