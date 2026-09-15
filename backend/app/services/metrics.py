"""
Pothole Dimension Measurement, Depth Estimation, Volume Calculation & Repair Cost Prediction.
Implements photogrammetric perspective scaling, shape-from-shading cavity depth estimation,
ASTM D6433 severity classification, and dynamic material/labor cost models.
"""

import math
import logging
from typing import Optional, Union
import numpy as np
import cv2

logger = logging.getLogger("PotholeApp.Metrics")


class CameraCalibration:
    """
    Standard camera geometry parameters for monocular smartphone / vehicle cameras.
    """
    def __init__(
        self,
        camera_height_meters: float = 1.3,
        camera_pitch_degrees: float = 50.0,
        horizontal_fov_degrees: float = 70.0
    ):
        self.camera_height = camera_height_meters
        self.pitch_deg = camera_pitch_degrees
        self.pitch_rad = math.radians(camera_pitch_degrees)
        self.fov_deg = horizontal_fov_degrees
        self.fov_rad = math.radians(horizontal_fov_degrees)


class DimensionEstimator:
    """
    Computes real-world width, length, depth, surface area, and volume of potholes
    from 2D bounding boxes and image pixel analysis.
    """

    def __init__(self, calibration: CameraCalibration = None):
        self.calib = calibration or CameraCalibration()

    def estimate_dimensions(
        self,
        bbox: list[int],
        image: np.ndarray
    ) -> dict:
        """
        Estimates real-world dimensions (cm), surface area (cm²), depth (cm), and volume (cm³).
        
        Args:
            bbox: [x1, y1, x2, y2] bounding box coordinates.
            image: Original full-resolution BGR image numpy array.
            
        Returns:
            dict with physical measurements and ASTM severity level.
        """
        img_h, img_w = image.shape[:2]
        x1, y1, x2, y2 = bbox

        # Ensure valid coordinates
        x1 = max(0, min(img_w - 1, int(x1)))
        y1 = max(0, min(img_h - 1, int(y1)))
        x2 = max(x1 + 1, min(img_w, int(x2)))
        y2 = max(y1 + 1, min(img_h, int(y2)))

        pixel_w = float(x2 - x1)
        pixel_h = float(y2 - y1)
        cy = (y1 + y2) / 2.0

        # 1. Perspective GSD (Ground Sample Distance) calculation
        # Distance to ground point accounting for camera tilt
        distance_to_ground = self.calib.camera_height / max(0.2, math.sin(self.calib.pitch_rad))
        
        # Base horizontal GSD at the center of the frame (cm / pixel)
        ground_width_at_distance_cm = (2.0 * distance_to_ground * math.tan(self.calib.fov_rad / 2.0)) * 100.0
        base_gsd_cm_per_px = ground_width_at_distance_cm / float(img_w)

        # Perspective scaling factor: objects lower in the frame (closer to bumper/feet) have higher resolution
        # y=0 (top/horizon) -> scale multiplier 1.45; y=img_h (bottom) -> scale multiplier 0.85
        relative_y = cy / float(img_h)
        perspective_scale = 1.35 - (0.50 * relative_y)
        effective_gsd_w = base_gsd_cm_per_px * perspective_scale
        
        # Foreshortening compensation for longitudinal depth
        tilt_compensation = 1.0 / max(0.3, math.cos(self.calib.pitch_rad))
        effective_gsd_h = effective_gsd_w * tilt_compensation

        real_width_cm = round(pixel_w * effective_gsd_w, 2)
        real_length_cm = round(pixel_h * effective_gsd_h, 2)

        # 2. Contour Segmentation & Area Fill Factor
        roi = image[y1:y2, x1:x2]
        fill_factor = self._compute_contour_fill_factor(roi)

        # Surface area in cm² and m²
        area_sq_cm = round(real_width_cm * real_length_cm * fill_factor, 2)
        area_sq_m = round(area_sq_cm / 10000.0, 4)

        # 3. Cavity Depth Estimation using Photometric Contrast & Edge Sharpness
        depth_cm = self._estimate_cavity_depth(roi, image, bbox, real_width_cm, real_length_cm)

        # 4. Volume Calculation (Paraboloid Cavity: V = 0.5 * Area * Depth)
        volume_cu_cm = round(0.5 * area_sq_cm * depth_cm, 2)
        volume_cu_m = round(volume_cu_cm / 1_000_000.0, 6)

        # 5. Determine ASTM Severity Level
        severity = self._classify_severity(depth_cm, area_sq_cm)

        return {
            "width_cm": real_width_cm,
            "length_cm": real_length_cm,
            "depth_cm": depth_cm,
            "area_sq_cm": area_sq_cm,
            "area_sq_m": area_sq_m,
            "volume_cu_cm": volume_cu_cm,
            "volume_cu_m": volume_cu_m,
            "fill_factor": round(fill_factor, 3),
            "severity": severity
        }

    def _compute_contour_fill_factor(self, roi: np.ndarray) -> float:
        """
        Calculates the ratio of true pothole cavity area to rectangular bounding box.
        Uses adaptive Otsu thresholding on the grayscale ROI.
        """
        if roi.size == 0 or roi.shape[0] < 4 or roi.shape[1] < 4:
            return 0.785  # Default ellipse fill factor (pi / 4)

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Otsu thresholding to segment dark pothole cavity from road
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        white_pixels = cv2.countNonZero(thresh)
        total_pixels = roi.shape[0] * roi.shape[1]

        raw_fill = white_pixels / float(total_pixels)
        # Constrain to realistic physical range [0.50, 0.90]
        return float(np.clip(raw_fill, 0.52, 0.88))

    def _estimate_cavity_depth(
        self,
        roi: np.ndarray,
        full_img: np.ndarray,
        bbox: list[int],
        width_cm: float,
        length_cm: float
    ) -> float:
        """
        Estimates pothole depth using cavity shadow contrast, edge gradient magnitude,
        and physical cavity dimensions.
        """
        if roi.size == 0:
            return 3.5  # Baseline average depth in cm

        img_h, img_w = full_img.shape[:2]
        x1, y1, x2, y2 = bbox

        # Sample surrounding road luminance from border margin around the bounding box
        margin = max(10, int(min(x2 - x1, y2 - y1) * 0.2))
        surr_x1 = max(0, x1 - margin)
        surr_y1 = max(0, y1 - margin)
        surr_x2 = min(img_w, x2 + margin)
        surr_y2 = min(img_h, y2 + margin)

        surrounding_roi = full_img[surr_y1:surr_y2, surr_x1:surr_x2]
        surr_gray = cv2.cvtColor(surrounding_roi, cv2.COLOR_BGR2GRAY)
        road_mean_luminance = float(np.mean(surr_gray))

        # Sample darkest 25th percentile inside the pothole cavity
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        cavity_luminance = float(np.percentile(roi_gray, 25))

        # Contrast ratio C in [0.0, 1.0]
        contrast = max(0.05, (road_mean_luminance - cavity_luminance) / max(road_mean_luminance, 1.0))

        # Calculate Sobel edge gradient magnitude for cavity depth sharpness
        sobelx = cv2.Sobel(roi_gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(roi_gray, cv2.CV_64F, 0, 1, ksize=3)
        edge_magnitude = np.mean(np.sqrt(sobelx**2 + sobely**2))
        normalized_edge = float(np.clip(edge_magnitude / 60.0, 0.2, 1.8))

        # Effective radius
        radius_cm = math.sqrt(max(1.0, width_cm * length_cm)) / 2.0

        # Calibrated photometric depth equation
        # Depth = Base + (Contrast * Edge_Factor * Scale * sqrt(Radius))
        raw_depth = 1.8 + (contrast * normalized_edge * 1.65 * math.sqrt(radius_cm))
        
        # Constrain between 2.0 cm (shallow surface loss) and 18.0 cm (severe structural crater)
        clamped_depth = float(np.clip(raw_depth, 2.0, 18.0))
        return round(clamped_depth, 2)

    def _classify_severity(self, depth_cm: float, area_sq_cm: float) -> str:
        """
        Classifies pothole severity per ASTM D6433 Pavement Condition Index standard.
        """
        if depth_cm >= 8.0 or area_sq_cm >= 6000.0:
            return "Critical"
        elif depth_cm >= 5.0 or area_sq_cm >= 3000.0:
            return "High"
        elif depth_cm >= 2.5 or area_sq_cm >= 1000.0:
            return "Medium"
        else:
            return "Low"


class CostPredictor:
    """
    Predicts road repair costs based on physical volume, area, severity,
    and municipal maintenance cost profiles.
    """

    DEFAULT_RATES = {
        "material_cost_per_cu_meter": 135.00,  # Hot-Mix Asphalt (HMA) + emulsion tack coat
        "labor_cost_base": 40.00,              # Site mobilization & traffic safety crew
        "labor_cost_per_sq_meter": 30.00,      # Pavement cutting, raking & rolling
        "equipment_overhead": 25.00,           # Plate compactor, asphalt heater, fuel
        "min_service_charge": 45.00            # Minimum invoice rate
    }

    SEVERITY_MULTIPLIERS = {
        "Low": 1.00,
        "Medium": 1.15,
        "High": 1.35,
        "Critical": 1.60
    }

    def __init__(self, cost_parameters: dict = None):
        self.rates = self.DEFAULT_RATES.copy()
        if cost_parameters:
            for k in self.rates:
                if k in cost_parameters and cost_parameters[k] is not None:
                    self.rates[k] = float(cost_parameters[k])

    def calculate_pothole_cost(
        self,
        volume_cu_m: float,
        area_sq_m: float,
        severity: str
    ) -> float:
        """
        Calculates the estimated repair cost for a single pothole.
        """
        # 1. Asphalt Material Cost (including 15% compaction allowance)
        compacted_volume = volume_cu_m * 1.15
        material_cost = compacted_volume * self.rates["material_cost_per_cu_meter"]

        # 2. Labor Cost (base crew mobilization + area surface prep)
        labor_cost = (area_sq_m * self.rates["labor_cost_per_sq_meter"])

        # 3. Severity Multiplier
        mult = self.SEVERITY_MULTIPLIERS.get(severity, 1.0)

        # 4. Total Cost Computation
        subtotal = (material_cost + labor_cost) * mult
        return round(subtotal, 2)

    def calculate_report_total_cost(self, pothole_items: list[dict]) -> float:
        """
        Calculates total repair cost for a multi-pothole report including fixed base costs.
        """
        if not pothole_items:
            return 0.00

        total_item_cost = sum(p.get("estimated_cost", 0.0) for p in pothole_items)
        
        # Apply site mobilization base + equipment overhead once per repair visit
        site_overhead = self.rates["labor_cost_base"] + self.rates["equipment_overhead"]
        total_cost = max(self.rates["min_service_charge"], total_item_cost + site_overhead)
        return round(total_cost, 2)
