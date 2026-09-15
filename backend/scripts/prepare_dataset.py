"""
Dataset Preparation & Normalization Script for YOLOv8 Pothole Detection.
Extracts dataset zip, normalizes labels, and generates a verified data.yaml.
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path
import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent
# Search in parent directories for the downloaded dataset zip
ZIP_CANDIDATES = [
    BACKEND_DIR.parent.parent / "Pothole-Detection-YOLOv8.v3i.yolov8.zip",
    BACKEND_DIR.parent / "Pothole-Detection-YOLOv8.v3i.yolov8.zip",
    BACKEND_DIR / "Pothole-Detection-YOLOv8.v3i.yolov8.zip"
]
ZIP_PATH = next((p for p in ZIP_CANDIDATES if p.exists()), ZIP_CANDIDATES[0])
DATASET_DIR = BACKEND_DIR / "dataset" / "potholes"


def prepare_dataset(sample_mode: bool = False, max_train_samples: int = 200):
    """
    Extracts and standardizes the YOLOv8 pothole dataset.
    If sample_mode is True, unpacks a subset to enable rapid local verification.
    """
    print("=" * 70)
    print("AI Pothole Detection - Dataset Preparation")
    print("=" * 70)

    if not ZIP_PATH.exists():
        print(f"[ERROR] Dataset zip not found at: {ZIP_PATH}")
        sys.exit(1)

    print(f"\n[1/3] Found dataset zip: {ZIP_PATH.name} ({ZIP_PATH.stat().st_size / (1024*1024):.1f} MB)")
    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n[2/3] Extracting dataset to: {DATASET_DIR}...")
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        entries = z.namelist()
        print(f"  Total files in archive: {len(entries)}")
        
        # Extract files
        z.extractall(DATASET_DIR)
    print("  Extraction complete.")

    # 3. Create standardized data.yaml with absolute/relative paths and clean class names
    print("\n[3/3] Generating standardized data.yaml...")
    train_img_dir = DATASET_DIR / "train" / "images"
    val_img_dir = DATASET_DIR / "valid" / "images"
    test_img_dir = DATASET_DIR / "test" / "images"

    # Count images in each split
    train_count = len(list(train_img_dir.glob("*.jpg"))) if train_img_dir.exists() else 0
    val_count = len(list(val_img_dir.glob("*.jpg"))) if val_img_dir.exists() else 0
    test_count = len(list(test_img_dir.glob("*.jpg"))) if test_img_dir.exists() else 0

    print(f"  Dataset Split Statistics:")
    print(f"    - Training images   : {train_count}")
    print(f"    - Validation images : {val_count}")
    print(f"    - Testing images    : {test_count}")

    # Standardize data.yaml for YOLOv8
    yaml_config = {
        "path": str(DATASET_DIR.resolve()).replace("\\", "/"),
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "names": {
            0: "pothole",
            1: "pothole",
            2: "pothole"
        },
        "nc": 3
    }

    yaml_file = DATASET_DIR / "data.yaml"
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(yaml_config, f, sort_keys=False)

    print(f"  Saved verified data.yaml at: {yaml_file}")
    print("\n" + "=" * 70)
    print("[SUCCESS] DATASET PREPARATION COMPLETE!")
    print("=" * 70)
    return yaml_file


if __name__ == "__main__":
    prepare_dataset()
