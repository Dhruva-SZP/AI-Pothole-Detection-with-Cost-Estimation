"""
Geospatial & Leaflet Map REST API Blueprint.
Provides optimized marker feeds and GeoJSON layers for frontend map visualization.
"""

from flask import Blueprint, request
from app.errors import api_response
from database.connection import get_db_connection, rows_to_dict_list
from database.queries import GET_MAP_MARKERS

map_bp = Blueprint("map", __name__, url_prefix="/api/v1/map")


@map_bp.route("/markers", methods=["GET"])
def get_markers():
    """
    Returns lightweight marker list optimized for Leaflet rendering.
    Supports optional status and severity filtering.
    """
    status = request.args.get("status", "").strip()
    severity = request.args.get("severity", "").strip()

    sql = """
    SELECT 
        [id], [report_uid], [latitude], [longitude], [address],
        [status], [severity_level], [total_potholes], [total_estimated_cost],
        [original_image_path], [annotated_image_path], [created_at]
    FROM [dbo].[PotholeReports]
    WHERE [latitude] IS NOT NULL AND [longitude] IS NOT NULL
    """
    conditions = []
    params = []

    if status:
        conditions.append("[status] = ?")
        params.append(status)
    if severity:
        conditions.append("[severity_level] = ?")
        params.append(severity)

    if conditions:
        sql += " AND " + " AND ".join(conditions)

    sql += " ORDER BY [created_at] DESC"

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = rows_to_dict_list(cursor, cursor.fetchall())
    except Exception as exc:
        current_app.logger.warning("Error querying map markers from DB (%s). Returning empty list.", exc)
        rows = []

    # Map to frontend-friendly marker objects
    markers = [
        {
            "id": r["id"],
            "report_uid": r["report_uid"],
            "lat": float(r["latitude"]),
            "lng": float(r["longitude"]),
            "address": r["address"],
            "status": r["status"],
            "severity": r["severity_level"],
            "total_potholes": r["total_potholes"],
            "total_estimated_cost": float(r["total_estimated_cost"]),
            "original_image_url": r["original_image_path"],
            "annotated_image_url": r["annotated_image_path"],
            "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"])
        }
        for r in rows
    ]

    return api_response(data=markers, message=f"Retrieved {len(markers)} map markers.")


@map_bp.route("/geojson", methods=["GET"])
def get_geojson():
    """
    Returns GeoJSON FeatureCollection formatted to RFC 7946 for GIS integration.
    """
    rows = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(GET_MAP_MARKERS)
            rows = rows_to_dict_list(cursor, cursor.fetchall())
    except Exception as exc:
        current_app.logger.warning("Error fetching GeoJSON markers from DB (%s). Returning empty list.", exc)

    features = []
    for r in rows:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(r["longitude"]), float(r["latitude"])]
            },
            "properties": {
                "id": r["id"],
                "report_uid": r["report_uid"],
                "address": r["address"],
                "status": r["status"],
                "severity": r["severity_level"],
                "total_potholes": r["total_potholes"],
                "estimated_cost": float(r["total_estimated_cost"]),
                "image_url": r["annotated_image_path"]
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    return api_response(data=geojson, message="GeoJSON feature collection generated.")
