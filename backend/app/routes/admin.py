"""
Admin Dashboard Analytics & Cost Configuration REST API Blueprint.
"""

from flask import Blueprint, request
from app.errors import api_response, api_error, APIError
from database.connection import get_db_connection, row_to_dict, rows_to_dict_list
from database.queries import (
    GET_DASHBOARD_STATS,
    GET_RECENT_REPORTS,
    GET_ACTIVE_COST_PARAMETERS,
    UPDATE_COST_PARAMETERS
)

admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")


@admin_bp.route("/stats", methods=["GET"])
def get_stats():
    """
    Returns aggregated KPIs, status breakdown, and severity metrics for admin dashboard.
    """
    raw_stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(GET_DASHBOARD_STATS)
            raw_stats = row_to_dict(cursor, cursor.fetchone()) or {}
    except Exception as exc:
        raw_stats = {}

    total_rep = raw_stats.get("total_reports") or 0
    repaired_rep = raw_stats.get("repaired_reports") or 0
    resolution_rate = round((repaired_rep / total_rep * 100), 1) if total_rep > 0 else 0.0

    stats = {
        "kpis": {
            "total_reports": total_rep,
            "total_potholes_detected": raw_stats["total_potholes_detected"] or 0,
            "total_repair_cost": float(raw_stats["total_repair_cost"] or 0.0),
            "pending_reports": raw_stats["pending_reports"] or 0,
            "repaired_reports": repaired_rep,
            "resolution_rate_percent": resolution_rate
        },
        "status_distribution": {
            "Reported": raw_stats["pending_reports"] or 0,
            "Verified": raw_stats["verified_reports"] or 0,
            "In_Progress": raw_stats["in_progress_reports"] or 0,
            "Repaired": repaired_rep
        },
        "severity_distribution": {
            "Critical": raw_stats["critical_severity_count"] or 0,
            "High": raw_stats["high_severity_count"] or 0,
            "Medium": raw_stats["medium_severity_count"] or 0,
            "Low": raw_stats["low_severity_count"] or 0
        }
    }

    return api_response(data=stats, message="Admin analytics statistics retrieved.")


@admin_bp.route("/recent", methods=["GET"])
def get_recent():
    """
    Returns recent reports feed for dashboard activity table.
    """
    limit = int(request.args.get("limit", 10))
    recent = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(GET_RECENT_REPORTS, (limit,))
            recent = rows_to_dict_list(cursor, cursor.fetchall())
    except Exception as exc:
        recent = []

    return api_response(data=recent, message=f"Retrieved {len(recent)} recent reports.")


@admin_bp.route("/cost-parameters", methods=["GET"])
def get_cost_parameters():
    """
    Retrieves the active municipal cost profile.
    """
    params = {
        "id": 1,
        "material_cost_per_cu_meter": 220.0,
        "labor_cost_base": 75.0,
        "labor_cost_per_sq_meter": 45.0,
        "equipment_overhead": 85.0,
        "currency": "USD"
    }
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(GET_ACTIVE_COST_PARAMETERS)
            row = cursor.fetchone()
            if row:
                params = row_to_dict(cursor, row)
    except Exception as exc:
        pass

    return api_response(data=params, message="Active cost parameters retrieved.")


@admin_bp.route("/cost-parameters", methods=["PUT"])
def update_cost_parameters():
    """
    Updates the active municipal cost parameters.
    """
    payload = request.get_json(silent=True) or {}
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(GET_ACTIVE_COST_PARAMETERS)
        current = row_to_dict(cursor, cursor.fetchone())
        if not current:
            raise APIError("No active cost parameters record found in database.", status_code=404)

        param_id = current["id"]
        material_rate = float(payload.get("material_cost_per_cu_meter", current["material_cost_per_cu_meter"]))
        labor_base = float(payload.get("labor_cost_base", current["labor_cost_base"]))
        labor_sqm = float(payload.get("labor_cost_per_sq_meter", current["labor_cost_per_sq_meter"]))
        overhead = float(payload.get("equipment_overhead", current["equipment_overhead"]))
        currency = payload.get("currency", current["currency"])

        cursor.execute(
            UPDATE_COST_PARAMETERS,
            (material_rate, labor_base, labor_sqm, overhead, currency, param_id)
        )

        cursor.execute(GET_ACTIVE_COST_PARAMETERS)
        updated = row_to_dict(cursor, cursor.fetchone())

    return api_response(data=updated, message="Cost parameters updated successfully.")
