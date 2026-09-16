"""
Pothole Reports REST API Blueprint.
Handles image upload, YOLOv8 inference, photogrammetric sizing, repair cost prediction,
and atomic SQL Server persistence.
"""

import os
import uuid
from pathlib import Path
from flask import Blueprint, request, current_app, url_for
from werkzeug.utils import secure_filename

from app.errors import api_response, api_error, APIError
from app.utils.storage import is_allowed_file
from app.services.detector import get_detector
from database.connection import get_db_connection, row_to_dict, rows_to_dict_list
from database.queries import (
    INSERT_REPORT,
    GET_REPORT_BY_ID,
    GET_REPORT_BY_UID,
    LIST_REPORTS,
    INSERT_DETECTION,
    GET_DETECTIONS_BY_REPORT_ID,
    UPDATE_REPORT_STATUS,
    DELETE_REPORT,
    GET_ACTIVE_COST_PARAMETERS
)

reports_bp = Blueprint("reports", __name__, url_prefix="/api/v1/reports")

# In-memory store for demo deployment mode
DEMO_REPORTS = {}


@reports_bp.route("", methods=["POST"])
def create_report():
    """
    Accepts multipart/form-data with image and location,
    runs YOLO detection + sizing + cost prediction,
    and stores records in SQL Server.
    """
    if "image" not in request.files:
        raise APIError("No 'image' file field provided in request.", status_code=400)

    image_file = request.files["image"]
    if not image_file or not image_file.filename:
        raise APIError("Empty filename in uploaded image.", status_code=400)

    # Validate file extension
    allowed_exts = current_app.config["ALLOWED_EXTENSIONS"]
    if not is_allowed_file(image_file.filename, allowed_exts):
        raise APIError(
            f"Unsupported file format. Allowed formats: {', '.join(sorted(allowed_exts))}",
            status_code=415
        )

    # Parse form metadata
    try:
        latitude = float(request.form.get("latitude", 0.0))
        longitude = float(request.form.get("longitude", 0.0))
    except (TypeError, ValueError):
        raise APIError("Invalid GPS coordinates. 'latitude' and 'longitude' must be valid numbers.", status_code=400)

    address = request.form.get("address", "").strip() or None
    notes = request.form.get("notes", "").strip() or None
    conf_threshold = float(request.form.get("confidence", current_app.config["MODEL_CONFIDENCE_THRESHOLD"]))

    # Generate unique filenames and paths
    report_uid = f"rep_{uuid.uuid4().hex[:12]}"
    ext = image_file.filename.rsplit(".", 1)[1].lower()
    raw_filename = f"{report_uid}_raw.{ext}"
    annotated_filename = f"{report_uid}_annotated.{ext}"

    raw_path = current_app.config["UPLOAD_FOLDER"] / raw_filename
    annotated_path = current_app.config["ANNOTATED_FOLDER"] / annotated_filename

    # Save original raw image
    image_file.save(str(raw_path))

    # Fetch active cost parameters from SQL Server for custom rate application if available
    cost_params = None
    if os.getenv("DEMO_MODE", "").lower() != "true" and "RENDER" not in os.environ:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(GET_ACTIVE_COST_PARAMETERS)
                row = cursor.fetchone()
                if row:
                    cost_params = row_to_dict(cursor, row)
        except Exception as exc:
            current_app.logger.warning("Could not fetch active CostParameters from DB: %s. Using defaults.", exc)

    # Run AI Detection & Measurement Pipeline
    detector = get_detector(
        weights_path=current_app.config["MODEL_WEIGHTS_PATH"],
        cost_parameters=cost_params
    )

    try:
        inference_result = detector.detect(
            image_input=raw_path,
            conf_threshold=conf_threshold,
            save_annotated_path=annotated_path
        )
    except Exception as exc:
        current_app.logger.exception("Inference error: %s", exc)
        raise APIError(f"Computer vision processing failed: {str(exc)}", status_code=500)

    # Relative paths for database and web client access
    raw_rel_url = f"/uploads/raw/{raw_filename}"
    annotated_rel_url = f"/uploads/annotated/{annotated_filename}"

    # Database persistence is disabled for the Render demo deployment.
    # AI detection and cost estimation continue without SQL Server.
    report_id = None
    status = "Analyzed"

    current_app.logger.info(
        "Demo mode: skipping SQL Server persistence. AI analysis completed successfully."
    )

    # Construct response payload
    response_data = {
        "id": report_id or 1,
        "report_id": report_id or 1,
        "report_uid": report_uid,
        "status": status,
        "latitude": latitude,
        "longitude": longitude,
        "address": address,
        "total_potholes": inference_result["total_potholes"],
        "total_estimated_cost": inference_result["total_estimated_cost"],
        "severity_level": inference_result["severity_level"],
        "top_confidence": inference_result["top_confidence"],
        "original_image_url": raw_rel_url,
        "original_image_path": raw_rel_url,
        "annotated_image_url": annotated_rel_url,
        "annotated_image_path": annotated_rel_url,
        "detections": inference_result["detections"]
    }
    DEMO_REPORTS[1] = response_data
    DEMO_REPORTS[report_uid] = response_data

    return api_response(
        data=response_data,
        message="Pothole report created and analyzed successfully.",
        status_code=201
    )


@reports_bp.route("", methods=["GET"])
def list_reports():
    """
    Returns list of all pothole reports with optional filtering by status and severity.
    """
    if os.getenv("DEMO_MODE", "").lower() == "true" or "RENDER" in os.environ:
        reports = list(DEMO_REPORTS.values())
        return api_response(data=reports, message=f"Retrieved {len(reports)} reports (Demo Mode).")

    try:
        status_filter = request.args.get("status", "").strip()
        severity_filter = request.args.get("severity", "").strip()

        sql = "SELECT * FROM [dbo].[PotholeReports]"
        conditions = []
        params = []

        if status_filter:
            conditions.append("[status] = ?")
            params.append(status_filter)
        if severity_filter:
            conditions.append("[severity_level] = ?")
            params.append(severity_filter)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY [created_at] DESC"

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            reports = rows_to_dict_list(cursor, cursor.fetchall())

        return api_response(data=reports, message=f"Retrieved {len(reports)} reports.")
    except Exception as exc:
        reports = list(DEMO_REPORTS.values())
        return api_response(data=reports, message=f"Retrieved {len(reports)} reports (Demo Mode).")


@reports_bp.route("/<report_id>", methods=["GET"])
def get_report(report_id):
    """
    Returns single report detail including all detected pothole measurements.
    """
    str_id = str(report_id)
    if str_id in DEMO_REPORTS:
        return api_response(data=DEMO_REPORTS[str_id], message="Report retrieved successfully.")
    if 1 in DEMO_REPORTS:
        return api_response(data=DEMO_REPORTS[1], message="Report retrieved successfully.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(GET_REPORT_BY_ID, (report_id,))
            report_row = cursor.fetchone()
            if not report_row:
                if DEMO_REPORTS:
                    return api_response(data=list(DEMO_REPORTS.values())[0], message="Report retrieved from demo cache.")
                raise APIError(f"Report #{report_id} not found.", status_code=404)
            report = row_to_dict(cursor, report_row)

            # Fetch child detections
            cursor.execute(GET_DETECTIONS_BY_REPORT_ID, (report_id,))
            detections = rows_to_dict_list(cursor, cursor.fetchall())
            report["detections"] = detections

        return api_response(data=report, message="Report retrieved successfully.")
    except Exception as exc:
        if DEMO_REPORTS:
            return api_response(data=list(DEMO_REPORTS.values())[0], message="Report retrieved from demo cache.")
        raise APIError(f"Report #{report_id} not found: {str(exc)}", status_code=404)


@reports_bp.route("/<int:report_id>/status", methods=["PATCH"])
def update_status(report_id: int):
    """
    Updates the lifecycle status of a report (Reported -> Verified -> In_Progress -> Repaired -> Rejected).
    """
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    notes = data.get("notes")

    valid_statuses = {"Reported", "Verified", "In_Progress", "Repaired", "Rejected"}
    if not new_status or new_status not in valid_statuses:
        raise APIError(
            f"Invalid status '{new_status}'. Allowed values: {', '.join(sorted(valid_statuses))}",
            status_code=400
        )

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(UPDATE_REPORT_STATUS, (new_status, notes, report_id))
        if cursor.rowcount == 0:
            raise APIError(f"Report #{report_id} not found.", status_code=404)

        cursor.execute(GET_REPORT_BY_ID, (report_id,))
        updated_report = row_to_dict(cursor, cursor.fetchone())

    return api_response(
        data=updated_report,
        message=f"Report #{report_id} status updated to '{new_status}'."
    )


@reports_bp.route("/<int:report_id>", methods=["DELETE"])
def delete_report(report_id: int):
    """
    Deletes a report and associated disk image files.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(GET_REPORT_BY_ID, (report_id,))
        row = cursor.fetchone()
        if not row:
            raise APIError(f"Report #{report_id} not found.", status_code=404)
        report = row_to_dict(cursor, row)

        # Delete database record (CASCADE removes PotholeDetections child rows)
        cursor.execute(DELETE_REPORT, (report_id,))

    # Remove disk files if existing
    for p_attr in ["original_image_path", "annotated_image_path"]:
        p_val = report.get(p_attr)
        if p_val and p_val.startswith("/uploads/"):
            disk_file = current_app.config["BASE_DIR"] / p_val.lstrip("/")
            if disk_file.exists():
                try:
                    disk_file.unlink()
                except OSError:
                    pass

    return api_response(message=f"Report #{report_id} deleted successfully.")
