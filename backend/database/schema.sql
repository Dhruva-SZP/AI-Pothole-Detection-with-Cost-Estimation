-- ============================================================================
-- Pothole Detection & Cost Prediction System - SQL Server (SSMS 20) Schema
-- ============================================================================

-- 1. Database Creation
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'PotholeDetectionDB')
BEGIN
    CREATE DATABASE PotholeDetectionDB;
    PRINT 'Database PotholeDetectionDB created successfully.';
END
GO

USE PotholeDetectionDB;
GO

-- 2. Users Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Users]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Users] (
        [id]            INT IDENTITY(1,1) NOT NULL,
        [username]      NVARCHAR(100) NOT NULL,
        [email]         NVARCHAR(255) NOT NULL,
        [password_hash] NVARCHAR(255) NOT NULL,
        [role]          NVARCHAR(50) NOT NULL CONSTRAINT DF_Users_Role DEFAULT 'citizen',
        [created_at]    DATETIME2(7) NOT NULL CONSTRAINT DF_Users_CreatedAt DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_Users PRIMARY KEY CLUSTERED ([id] ASC),
        CONSTRAINT UQ_Users_Username UNIQUE NONCLUSTERED ([username] ASC),
        CONSTRAINT UQ_Users_Email UNIQUE NONCLUSTERED ([email] ASC)
    );
    PRINT 'Table Users created.';
END
GO

-- 3. PotholeReports (Parent Entity: Image Upload & Geo-Location Metadata)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[PotholeReports]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[PotholeReports] (
        [id]                   INT IDENTITY(1,1) NOT NULL,
        [report_uid]           NVARCHAR(64) NOT NULL,
        [user_id]              INT NULL,
        [original_image_path]  NVARCHAR(500) NOT NULL,
        [annotated_image_path] NVARCHAR(500) NULL,
        [latitude]             DECIMAL(10, 7) NOT NULL,
        [longitude]            DECIMAL(10, 7) NOT NULL,
        [address]              NVARCHAR(500) NULL,
        [status]               NVARCHAR(50) NOT NULL CONSTRAINT DF_PotholeReports_Status DEFAULT 'Reported',
        [total_potholes]       INT NOT NULL CONSTRAINT DF_PotholeReports_TotalPotholes DEFAULT 0,
        [total_estimated_cost] DECIMAL(12, 2) NOT NULL CONSTRAINT DF_PotholeReports_TotalCost DEFAULT 0.00,
        [severity_level]       NVARCHAR(20) NOT NULL CONSTRAINT DF_PotholeReports_Severity DEFAULT 'Low',
        [notes]                NVARCHAR(MAX) NULL,
        [created_at]           DATETIME2(7) NOT NULL CONSTRAINT DF_PotholeReports_CreatedAt DEFAULT SYSUTCDATETIME(),
        [updated_at]           DATETIME2(7) NOT NULL CONSTRAINT DF_PotholeReports_UpdatedAt DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_PotholeReports PRIMARY KEY CLUSTERED ([id] ASC),
        CONSTRAINT UQ_PotholeReports_UID UNIQUE NONCLUSTERED ([report_uid] ASC),
        CONSTRAINT FK_PotholeReports_Users FOREIGN KEY ([user_id]) 
            REFERENCES [dbo].[Users] ([id]) ON DELETE SET NULL
    );
    PRINT 'Table PotholeReports created.';
END
GO

-- 4. PotholeDetections (Child Entity: Individual Detected Potholes & Measurements)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[PotholeDetections]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[PotholeDetections] (
        [id]                     INT IDENTITY(1,1) NOT NULL,
        [report_id]              INT NOT NULL,
        [bbox_x1]                FLOAT NOT NULL,
        [bbox_y1]                FLOAT NOT NULL,
        [bbox_x2]                FLOAT NOT NULL,
        [bbox_y2]                FLOAT NOT NULL,
        [confidence]             FLOAT NOT NULL,
        [estimated_width_cm]     FLOAT NOT NULL,
        [estimated_length_cm]    FLOAT NOT NULL,
        [estimated_depth_cm]     FLOAT NOT NULL,
        [estimated_area_sq_cm]   FLOAT NOT NULL,
        [estimated_volume_cu_cm] FLOAT NOT NULL,
        [estimated_cost]         DECIMAL(10, 2) NOT NULL,
        [severity]               NVARCHAR(20) NOT NULL CONSTRAINT DF_PotholeDetections_Severity DEFAULT 'Low',
        [detected_at]            DATETIME2(7) NOT NULL CONSTRAINT DF_PotholeDetections_DetectedAt DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_PotholeDetections PRIMARY KEY CLUSTERED ([id] ASC),
        CONSTRAINT FK_PotholeDetections_Reports FOREIGN KEY ([report_id]) 
            REFERENCES [dbo].[PotholeReports] ([id]) ON DELETE CASCADE
    );
    PRINT 'Table PotholeDetections created.';
END
GO

-- 5. CostParameters (Admin Configurable Formula Multipliers)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[CostParameters]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[CostParameters] (
        [id]                          INT IDENTITY(1,1) NOT NULL,
        [material_cost_per_cu_meter]  DECIMAL(10, 2) NOT NULL DEFAULT 135.00,
        [labor_cost_base]             DECIMAL(10, 2) NOT NULL DEFAULT 40.00,
        [labor_cost_per_sq_meter]     DECIMAL(10, 2) NOT NULL DEFAULT 30.00,
        [equipment_overhead]          DECIMAL(10, 2) NOT NULL DEFAULT 25.00,
        [currency]                    NVARCHAR(10) NOT NULL DEFAULT 'USD',
        [is_active]                   BIT NOT NULL DEFAULT 1,
        [updated_at]                  DATETIME2(7) NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_CostParameters PRIMARY KEY CLUSTERED ([id] ASC)
    );
    PRINT 'Table CostParameters created.';
    
    -- Insert Default Cost Profile
    INSERT INTO [dbo].[CostParameters] 
        ([material_cost_per_cu_meter], [labor_cost_base], [labor_cost_per_sq_meter], [equipment_overhead], [currency], [is_active])
    VALUES 
        (135.00, 40.00, 30.00, 25.00, 'USD', 1);
    PRINT 'Default CostParameters seeded.';
END
GO

-- 6. Performance Indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_PotholeReports_Location' AND object_id = OBJECT_ID(N'[dbo].[PotholeReports]'))
    CREATE NONCLUSTERED INDEX IX_PotholeReports_Location 
    ON [dbo].[PotholeReports] ([latitude], [longitude]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_PotholeReports_Status' AND object_id = OBJECT_ID(N'[dbo].[PotholeReports]'))
    CREATE NONCLUSTERED INDEX IX_PotholeReports_Status 
    ON [dbo].[PotholeReports] ([status]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_PotholeReports_CreatedAt' AND object_id = OBJECT_ID(N'[dbo].[PotholeReports]'))
    CREATE NONCLUSTERED INDEX IX_PotholeReports_CreatedAt 
    ON [dbo].[PotholeReports] ([created_at] DESC);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_PotholeDetections_ReportId' AND object_id = OBJECT_ID(N'[dbo].[PotholeDetections]'))
    CREATE NONCLUSTERED INDEX IX_PotholeDetections_ReportId 
    ON [dbo].[PotholeDetections] ([report_id]);
GO

PRINT 'All indexes verified/created successfully.';
