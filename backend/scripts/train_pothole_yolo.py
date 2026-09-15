"""
Production YOLOv8 Pothole Model Training Pipeline.
Trains custom YOLOv8 model on the pothole dataset and saves weights to models/weights/best.pt.
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
import torch
from ultralytics import YOLO

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATASET_YAML = BACKEND_DIR / "dataset" / "potholes" / "data.yaml"
OUTPUT_WEIGHTS_DIR = BACKEND_DIR / "models" / "weights"


def train_pothole_detector(epochs: int = 30, batch_size: int = 8, img_size: int = 640, base_model: str = "yolov8n.pt"):
    """
    Executes transfer learning on YOLOv8 for pothole detection.
    """
    print("=" * 70)
    print("AI Pothole Detection - YOLOv8 Training Pipeline")
    print("=" * 70)

    if not DATASET_YAML.exists():
        print(f"[ERROR] Dataset configuration not found at: {DATASET_YAML}")
        print("Please run: python scripts/prepare_dataset.py first.")
        sys.exit(1)

    # Detect hardware acceleration
    device = "0" if torch.cuda.is_available() else "cpu"
    print(f"\n[1/4] Hardware Environment:")
    print(f"  - PyTorch Version : {torch.__version__}")
    print(f"  - Device Selected : {device} ({'GPU Acceleration' if device != 'cpu' else 'CPU Mode'})")

    # Initialize Base Model
    print(f"\n[2/4] Loading Base Architecture [{base_model}]...")
    model = YOLO(base_model)

    # Execute Training
    print(f"\n[3/4] Starting Training on Pothole Dataset:")
    print(f"  - Dataset Config  : {DATASET_YAML}")
    print(f"  - Target Epochs   : {epochs}")
    print(f"  - Batch Size      : {batch_size}")
    print(f"  - Image Resolution: {img_size}x{img_size}")

    train_results = model.train(
        data=str(DATASET_YAML),
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        device=device,
        project=str(BACKEND_DIR / "runs" / "train"),
        name="pothole_detector",
        exist_ok=True,
        patience=10,
        save=True,
        plots=True,
        verbose=True
    )

    # Locate and Deploy best.pt weights
    print(f"\n[4/4] Deploying Trained Weights...")
    trained_best_pt = BACKEND_DIR / "runs" / "train" / "pothole_detector" / "weights" / "best.pt"
    
    if trained_best_pt.exists():
        OUTPUT_WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
        destination_best_pt = OUTPUT_WEIGHTS_DIR / "best.pt"
        shutil.copy2(trained_best_pt, destination_best_pt)
        print(f"  [SUCCESS] Copied trained weights to: {destination_best_pt}")
        print(f"  Weight file size: {destination_best_pt.stat().st_size / (1024*1024):.2f} MB")
    else:
        print(f"[WARNING] Expected weight file not found at: {trained_best_pt}")

    print("\n" + "=" * 70)
    print("[SUCCESS] YOLOv8 POTHOLE MODEL TRAINING COMPLETE!")
    print("=" * 70)
    return str(destination_best_pt) if trained_best_pt.exists() else None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train custom YOLOv8 model for pothole detection.")
    parser.add_argument("--epochs", type=int, default=30, help="Number of training epochs (default: 30)")
    parser.add_argument("--batch", type=int, default=8, help="Batch size (default: 8)")
    parser.add_argument("--imgsz", type=int, default=640, help="Image resolution (default: 640)")
    parser.add_argument("--base", type=str, default="yolov8n.pt", help="Base model architecture (default: yolov8n.pt)")
    args = parser.parse_args()

    train_pothole_detector(
        epochs=args.epochs,
        batch_size=args.batch,
        img_size=args.imgsz,
        base_model=args.base
    )
