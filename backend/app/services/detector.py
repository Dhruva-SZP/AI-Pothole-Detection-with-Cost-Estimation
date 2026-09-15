"""
YOLOv8 Computer Vision Inference Service with OpenCV Annotation & Measurement Pipeline.
Loads custom trained best.pt weights, performs pothole object detection,
calculates physical dimensions, depth, area, volume, and repair cost,
and renders high-contrast visual overlays with HUD metric tags.
"""

import os
import logging
from pathlib import Path
from typing import Union, Optional
import cv2
import numpy as np
from ultralytics import YOLO

from app.services.metrics import DimensionEstimator, CostPredictor

logger = logging.getLogger("PotholeApp.Detector")


class PotholeDetector:
    """
    Production-grade YOLOv8 inference engine with integrated dimension,
    depth, volume, and cost prediction pipelines.
    """

    def __init__(
        self,
        weights_path: Union[str, Path] = None,
        default_conf: float = 0.35,
        cost_parameters: dict = None
    ):
        self.weights_path = Path(weights_path) if weights_path else Path("models/weights/best.pt")
        self.default_conf = default_conf
        self.model = None
        self.is_loaded = False
        self.dimension_estimator = DimensionEstimator()
        self.cost_predictor = CostPredictor(cost_parameters=cost_parameters)
        self._load_model()

    def _load_model(self):
        """
        Loads the trained YOLOv8 model weights.
        """
        if not self.weights_path.exists() or self.weights_path.stat().st_size == 0:
            logger.warning(
                "Trained weights not found at [%s]. Initializing baseline detector.",
                self.weights_path
            )
            fallback_path = Path("yolov8n.pt")
            try:
                self.model = YOLO(str(fallback_path))
                self.is_loaded = True
                logger.info("Loaded base YOLO model from %s", fallback_path)
            except Exception as exc:
                logger.error("Failed to load base YOLO model: %s", exc)
                self.model = None
                self.is_loaded = False
            return

        try:
            logger.info("Loading custom pothole detection weights from: %s", self.weights_path)
            self.model = YOLO(str(self.weights_path))
            self.is_loaded = True
            logger.info("PotholeDetector model loaded successfully.")
        except Exception as exc:
            logger.exception("Failed to load YOLO model from [%s]: %s", self.weights_path, exc)
            self.model = None
            self.is_loaded = False

    def detect(
        self,
        image_input: Union[str, Path, np.ndarray],
        conf_threshold: float = None,
        save_annotated_path: Union[str, Path] = None
    ) -> dict:
        """
        Runs pothole detection, measures dimensions, depth, area, volume, and cost,
        and renders metric HUD overlays using OpenCV.
        """
        if not self.is_loaded or self.model is None:
            raise RuntimeError("YOLO model is not initialized or weights could not be loaded.")

        conf = conf_threshold if conf_threshold is not None else self.default_conf

        if isinstance(image_input, (str, Path)):
            img_path = Path(image_input)
            if not img_path.exists():
                raise FileNotFoundError(f"Input image not found: {img_path}")
            orig_img = cv2.imread(str(img_path))
            if orig_img is None:
                raise ValueError(f"Could not decode image at: {img_path}")
        else:
            orig_img = image_input.copy()

        img_height, img_width = orig_img.shape[:2]

        # Execute YOLOv8 prediction
        results = self.model.predict(
            source=orig_img,
            conf=conf,
            verbose=False
        )

        detections = []
        annotated_img = orig_img.copy()
        overlay = orig_img.copy()

        SEVERITY_COLORS = {
            "Low": (0, 200, 100),       # Green-Teal BGR
            "Medium": (0, 215, 255),    # Amber BGR
            "High": (0, 120, 255),      # Orange BGR
            "Critical": (30, 30, 240)   # Red BGR
        }

        for r in results:
            boxes = r.boxes
            if boxes is None or len(boxes) == 0:
                continue

            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                
                x1 = max(0, min(img_width - 1, x1))
                y1 = max(0, min(img_height - 1, y1))
                x2 = max(0, min(img_width - 1, x2))
                y2 = max(0, min(img_height - 1, y2))

                confidence = float(box.conf[0].cpu().numpy())
                class_name = "pothole"

                # 1. Compute Physical Metrics via DimensionEstimator
                metrics = self.dimension_estimator.estimate_dimensions([x1, y1, x2, y2], orig_img)

                # 2. Compute Individual Repair Cost via CostPredictor
                cost = self.cost_predictor.calculate_pothole_cost(
                    volume_cu_m=metrics["volume_cu_m"],
                    area_sq_m=metrics["area_sq_m"],
                    severity=metrics["severity"]
                )

                detection_item = {
                    "bbox": [x1, y1, x2, y2],
                    "confidence": round(confidence, 4),
                    "label": class_name,
                    "estimated_width_cm": metrics["width_cm"],
                    "estimated_length_cm": metrics["length_cm"],
                    "estimated_depth_cm": metrics["depth_cm"],
                    "estimated_area_sq_cm": metrics["area_sq_cm"],
                    "estimated_volume_cu_cm": metrics["volume_cu_cm"],
                    "estimated_cost": cost,
                    "severity": metrics["severity"]
                }
                detections.append(detection_item)

                # 3. OpenCV Visual Rendering with Color-Coded Severity
                theme_color = SEVERITY_COLORS.get(metrics["severity"], (0, 140, 255))

                # Semi-transparent fill
                cv2.rectangle(overlay, (x1, y1), (x2, y2), theme_color, -1)

                # High-contrast border
                box_thickness = max(2, int(min(img_width, img_height) / 320))
                cv2.rectangle(annotated_img, (x1, y1), (x2, y2), theme_color, box_thickness)

                # Corner brackets
                p_w = x2 - x1
                p_h = y2 - y1
                corner_len = max(8, int(min(p_w, p_h) * 0.18))
                accent_color = (255, 255, 255)
                accent_thick = box_thickness + 1

                cv2.line(annotated_img, (x1, y1), (x1 + corner_len, y1), accent_color, accent_thick)
                cv2.line(annotated_img, (x1, y1), (x1, y1 + corner_len), accent_color, accent_thick)
                cv2.line(annotated_img, (x2, y1), (x2 - corner_len, y1), accent_color, accent_thick)
                cv2.line(annotated_img, (x2, y1), (x2, y1 + corner_len), accent_color, accent_thick)
                cv2.line(annotated_img, (x1, y2), (x1 + corner_len, y2), accent_color, accent_thick)
                cv2.line(annotated_img, (x1, y2), (x1, y2 - corner_len), accent_color, accent_thick)
                cv2.line(annotated_img, (x2, y2), (x2 - corner_len, y2), accent_color, accent_thick)
                cv2.line(annotated_img, (x2, y2), (x2, y2 - corner_len), accent_color, accent_thick)

                # Top Header Badge: Class + Confidence
                badge_text = f"POTHOLE {confidence * 100:.1f}% [{metrics['severity'].upper()}]"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = max(0.38, min(img_width, img_height) / 1300)
                font_thick = max(1, int(font_scale * 2))
                (text_w, text_h), _ = cv2.getTextSize(badge_text, font, font_scale, font_thick)

                badge_y1 = max(0, y1 - text_h - 8)
                cv2.rectangle(annotated_img, (x1, badge_y1), (min(img_width, x1 + text_w + 10), y1), theme_color, -1)
                cv2.putText(annotated_img, badge_text, (x1 + 5, y1 - 4), font, font_scale, (255, 255, 255), font_thick, cv2.LINE_AA)

                # Bottom Footer Badge: Physical Size + Depth + Repair Cost
                metric_text = f"{metrics['width_cm']:.0f}x{metrics['length_cm']:.0f}cm | D:{metrics['depth_cm']:.1f}cm | ${cost:.0f}"
                (m_w, m_h), _ = cv2.getTextSize(metric_text, font, font_scale * 0.9, 1)
                metric_y2 = min(img_height, y2 + m_h + 8)
                cv2.rectangle(annotated_img, (x1, y2), (min(img_width, x1 + m_w + 8), metric_y2), (20, 20, 20), -1)
                cv2.putText(annotated_img, metric_text, (x1 + 4, metric_y2 - 3), font, font_scale * 0.9, (0, 255, 255), 1, cv2.LINE_AA)

        # Blend semi-transparent highlight overlay
        cv2.addWeighted(overlay, 0.20, annotated_img, 0.80, 0, annotated_img)

        # Calculate multi-pothole report total cost
        total_estimated_cost = self.cost_predictor.calculate_report_total_cost(detections)

        # Overall severity
        severities = [d["severity"] for d in detections]
        if "Critical" in severities:
            overall_severity = "Critical"
        elif "High" in severities:
            overall_severity = "High"
        elif "Medium" in severities:
            overall_severity = "Medium"
        elif "Low" in severities:
            overall_severity = "Low"
        else:
            overall_severity = "None"

        # Save annotated image
        saved_path_str = None
        if save_annotated_path:
            out_path = Path(save_annotated_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(out_path), annotated_img)
            saved_path_str = str(out_path)

        top_conf = max([d["confidence"] for d in detections], default=0.0)

        return {
            "detections": detections,
            "total_potholes": len(detections),
            "total_estimated_cost": total_estimated_cost,
            "severity_level": overall_severity,
            "top_confidence": top_conf,
            "image_width": img_width,
            "image_height": img_height,
            "annotated_image_path": saved_path_str
        }


_detector_instance: PotholeDetector = None


def get_detector(weights_path: str = None, default_conf: float = 0.35, cost_parameters: dict = None) -> PotholeDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = PotholeDetector(weights_path=weights_path, default_conf=default_conf, cost_parameters=cost_parameters)
    return _detector_instance
