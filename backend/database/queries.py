"""
Parameterized Transact-SQL Queries and Data Access Layer for SQL Server.
Strictly separates SQL statements from business logic with SQL injection prevention.
"""

# ============================================================================
# 1. Pothole Reports Queries
# ============================================================================

INSERT_REPORT = """
INSERT INTO [dbo].[PotholeReports] (
    [report_uid], [user_id], [original_image_path], [annotated_image_path],
    [latitude], [longitude], [address], [status], [total_potholes],
    [total_estimated_cost], [severity_level], [notes], [created_at], [updated_at]
)
OUTPUT INSERTED.id
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME(), SYSUTCDATETIME());
"""

GET_REPORT_BY_ID = """
SELECT 
    r.[id], r.[report_uid], r.[user_id], r.[original_image_path], r.[annotated_image_path],
    r.[latitude], r.[longitude], r.[address], r.[status], r.[total_potholes],
    r.[total_estimated_cost], r.[severity_level], r.[notes], r.[created_at], r.[updated_at],
    u.[username] AS reporter_username
FROM [dbo].[PotholeReports] r
LEFT JOIN [dbo].[Users] u ON r.[user_id] = u.[id]
WHERE r.[id] = ?;
"""

GET_REPORT_BY_UID = """
SELECT 
    r.[id], r.[report_uid], r.[user_id], r.[original_image_path], r.[annotated_image_path],
    r.[latitude], r.[longitude], r.[address], r.[status], r.[total_potholes],
    r.[total_estimated_cost], r.[severity_level], r.[notes], r.[created_at], r.[updated_at],
    u.[username] AS reporter_username
FROM [dbo].[PotholeReports] r
LEFT JOIN [dbo].[Users] u ON r.[user_id] = u.[id]
WHERE r.[report_uid] = ?;
"""

LIST_REPORTS = """
SELECT 
    r.[id], r.[report_uid], r.[user_id], r.[original_image_path], r.[annotated_image_path],
    r.[latitude], r.[longitude], r.[address], r.[status], r.[total_potholes],
    r.[total_estimated_cost], r.[severity_level], r.[created_at], r.[updated_at]
FROM [dbo].[PotholeReports] r
ORDER BY r.[created_at] DESC;
"""

UPDATE_REPORT_STATUS = """
UPDATE [dbo].[PotholeReports]
SET [status] = ?, [notes] = ISNULL(?, [notes]), [updated_at] = SYSUTCDATETIME()
WHERE [id] = ?;
"""

DELETE_REPORT = """
DELETE FROM [dbo].[PotholeReports] WHERE [id] = ?;
"""

# ============================================================================
# 2. Pothole Detections (Child Entities) Queries
# ============================================================================

INSERT_DETECTION = """
INSERT INTO [dbo].[PotholeDetections] (
    [report_id], [bbox_x1], [bbox_y1], [bbox_x2], [bbox_y2], [confidence],
    [estimated_width_cm], [estimated_length_cm], [estimated_depth_cm],
    [estimated_area_sq_cm], [estimated_volume_cu_cm], [estimated_cost],
    [severity], [detected_at]
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME());
"""

GET_DETECTIONS_BY_REPORT_ID = """
SELECT 
    [id], [report_id], [bbox_x1], [bbox_y1], [bbox_x2], [bbox_y2], [confidence],
    [estimated_width_cm], [estimated_length_cm], [estimated_depth_cm],
    [estimated_area_sq_cm], [estimated_volume_cu_cm], [estimated_cost],
    [severity], [detected_at]
FROM [dbo].[PotholeDetections]
WHERE [report_id] = ?
ORDER BY [id] ASC;
"""

# ============================================================================
# 3. Geospatial / Map Queries (Leaflet Markers)
# ============================================================================

GET_MAP_MARKERS = """
SELECT 
    r.[id], r.[report_uid], r.[latitude], r.[longitude], r.[address],
    r.[status], r.[severity_level], r.[total_potholes], r.[total_estimated_cost],
    r.[original_image_path], r.[annotated_image_path], r.[created_at]
FROM [dbo].[PotholeReports] r
WHERE r.[latitude] IS NOT NULL AND r.[longitude] IS NOT NULL
ORDER BY r.[created_at] DESC;
"""

# ============================================================================
# 4. Admin Dashboard & Aggregation Analytics Queries
# ============================================================================

GET_DASHBOARD_STATS = """
SELECT
    COUNT(*) AS total_reports,
    ISNULL(SUM([total_potholes]), 0) AS total_potholes_detected,
    ISNULL(SUM([total_estimated_cost]), 0.0) AS total_repair_cost,
    ISNULL(SUM(CASE WHEN [status] = 'Reported' THEN 1 ELSE 0 END), 0) AS pending_reports,
    ISNULL(SUM(CASE WHEN [status] = 'Verified' THEN 1 ELSE 0 END), 0) AS verified_reports,
    ISNULL(SUM(CASE WHEN [status] = 'In_Progress' THEN 1 ELSE 0 END), 0) AS in_progress_reports,
    ISNULL(SUM(CASE WHEN [status] = 'Repaired' THEN 1 ELSE 0 END), 0) AS repaired_reports,
    ISNULL(SUM(CASE WHEN [severity_level] = 'Critical' THEN 1 ELSE 0 END), 0) AS critical_severity_count,
    ISNULL(SUM(CASE WHEN [severity_level] = 'High' THEN 1 ELSE 0 END), 0) AS high_severity_count,
    ISNULL(SUM(CASE WHEN [severity_level] = 'Medium' THEN 1 ELSE 0 END), 0) AS medium_severity_count,
    ISNULL(SUM(CASE WHEN [severity_level] = 'Low' THEN 1 ELSE 0 END), 0) AS low_severity_count
FROM [dbo].[PotholeReports];
"""

GET_RECENT_REPORTS = """
SELECT TOP (?)
    r.[id], r.[report_uid], r.[latitude], r.[longitude], r.[address],
    r.[status], r.[total_potholes], r.[total_estimated_cost],
    r.[severity_level], r.[created_at]
FROM [dbo].[PotholeReports] r
ORDER BY r.[created_at] DESC;
"""

# ============================================================================
# 5. Cost Parameters Queries
# ============================================================================

GET_ACTIVE_COST_PARAMETERS = """
SELECT TOP 1
    [id], [material_cost_per_cu_meter], [labor_cost_base],
    [labor_cost_per_sq_meter], [equipment_overhead], [currency], [is_active]
FROM [dbo].[CostParameters]
WHERE [is_active] = 1
ORDER BY [updated_at] DESC;
"""

UPDATE_COST_PARAMETERS = """
UPDATE [dbo].[CostParameters]
SET 
    [material_cost_per_cu_meter] = ?,
    [labor_cost_base] = ?,
    [labor_cost_per_sq_meter] = ?,
    [equipment_overhead] = ?,
    [currency] = ?,
    [updated_at] = SYSUTCDATETIME()
WHERE [id] = ?;
"""
