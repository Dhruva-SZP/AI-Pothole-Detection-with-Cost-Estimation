# AI-Based Pothole Detection with Size Measurement & Cost Prediction

An enterprise-grade, full-stack computer vision and geospatial road maintenance platform that detects potholes from pavement photography, calculates real-world cavity dimensions and depth, classifies pavement distress using the **ASTM D6433** standard, predicts asphalt repair costs, and renders geolocated hazard maps.

---

## Key Features

- **Custom YOLOv8 Deep Learning Detector**: Trained on specialized road damage datasets with high-precision bounding box localization.
- **Calibrated Monocular Dimension Estimation**: Utilizes monocular perspective geometry (Ground Sampling Distance) with Otsu contour thresholding to estimate cavity surface area ($m^2$) and realistic fill factors ($\eta$).
- **Shape-from-Shading Cavity Depth**: Computes localized luminance depression relative to the road surface combined with Sobel gradient magnitudes to infer cavity depth ($cm$) and paraboloid volume ($m^3$).
- **ASTM D6433 Distress Classification**: Automatically stratifies road defects into Low, Medium, High, and Critical severity classes based on depth thresholds and surface area distress.
- **Municipal Asphalt & Labor Cost Estimator**: Calculates repair expenditures considering material volume ($m^3$, 15% compaction factor), surface labor ($m^2$), equipment overhead, base mobilization, and severity multipliers.
- **Interactive GIS Map (Leaflet)**: Renders geolocated pothole markers with color-coded severity pulses, interactive popup inspection cards, and bounding box previews.
- **Admin Analytics Dashboard**: City-wide KPI cards, severity distribution charts, repair workflow tracking, and live SQL Server municipal cost parameters editor.
- **Single-Port Production Architecture**: Multi-threaded Waitress WSGI server serving both the REST API and compiled React SPA on a single port (`5000`).

---

## Technology Stack

- **Backend**: Python 3.10+, Flask 3.0+, Waitress WSGI (Multi-threaded)
- **Computer Vision & AI**: Ultralytics YOLOv8, OpenCV (`cv2`), NumPy
- **Database**: Microsoft SQL Server (SSMS 20 / SQL Server Express), `pyodbc`
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide React, Leaflet (`react-leaflet`), Axios

---

## System Architecture

```
pothole-ai-system/
+-- backend/
¦   +-- app/
¦   ¦   +-- routes/              # Health, Reports, GIS Map, Admin Endpoints
¦   ¦   +-- services/            # YOLOv8 Detector & ASTM D6433 Size/Cost Engine
¦   ¦   +-- utils/               # File Storage & Path Sanitizer
¦   ¦   +-- config.py            # Environment-Driven Application Settings
¦   ¦   +-- errors.py            # Centralized Error Handlers & JSON Envelopes
¦   ¦   +-- logger.py            # Structured Rotating Logging
¦   +-- database/
¦   ¦   +-- schema.sql           # Clustered Index, Foreign Key & Spatial Schema
¦   ¦   +-- connection.py        # Thread-Safe pyodbc Context Manager
¦   ¦   +-- init_db.py           # Database & Seed Script
¦   +-- models/weights/best.pt   # Pothole Detection Model Weights
¦   +-- uploads/                 # Storage for Raw & OpenCV Annotated Images
¦   +-- wsgi_server.py           # Multi-Threaded Waitress WSGI Server
¦   +-- test_e2e_production.py   # Automated Verification Test Suite
+-- frontend/
¦   +-- src/
¦   ¦   +-- components/Navbar    # Responsive Navigation + Real-Time SQL Status
¦   ¦   +-- pages/UploadPage     # Drag-and-Drop + Geolocation + Progress Bar
¦   ¦   +-- pages/ResultsPage    # Before/After Tabs + Depth Hazard Meter
¦   ¦   +-- pages/MapPage        # Leaflet GIS Map with Pulsing Severity Markers
¦   ¦   +-- pages/ReportsPage    # Sortable Data Table + CSV Export
¦   ¦   +-- pages/AdminPage      # KPI Metrics + Live Municipal Cost Editor
¦   ¦   +-- api/potholeService   # Axios Client with Global Error Handling
¦   +-- dist/                    # Compiled Production Single-Page Application
+-- start_dev.bat / .ps1         # One-Click Dual Development Launcher
+-- start_production.bat / .ps1  # One-Click Single-Port Production Launcher
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10 or higher
- Microsoft SQL Server 2019+ or SQL Server Express
- ODBC Driver 17 for SQL Server
- Node.js 18+ (for frontend development)

### 2. Database Initialization
Create database and seed initial parameters:
```bash
cd backend
python database/init_db.py
```

### 3. Environment Configuration
Copy `.env.example` to `.env` in `backend/` and update your SQL Server instance name if needed:
```ini
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_SERVER=localhost\SQLEXPRESS
DB_NAME=PotholeDetectionDB
DB_TRUSTED_CONNECTION=yes
```

### 4. Running the Platform

#### Production Mode (Single-Port: REST API + React SPA)
- **Windows Batch**: Double-click `start_production.bat`
- **PowerShell**:
  ```powershell
  .\start_production.ps1
  ```
- **Web Interface**: `http://localhost:5000`

#### Development Mode (Hot-Reloading)
- **Windows Batch**: Double-click `start_dev.bat`
- **PowerShell**:
  ```powershell
  .\start_dev.ps1
  ```
- **Frontend UI**: `http://localhost:5173` | **Backend API**: `http://localhost:5000`

---

## API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service uptime and system status |
| `GET` | `/api/v1/health/db` | Live SQL Server connectivity and query latency |
| `POST` | `/api/v1/reports` | Multipart upload with GPS coordinates & YOLO analysis |
| `GET` | `/api/v1/reports` | Paginated list of pothole reports |
| `GET` | `/api/v1/reports/:id` | Full inspection detail with individual cavity metrics |
| `PATCH`| `/api/v1/reports/:id/status` | Update workflow status (`Reported` $\rightarrow$ `Repaired`) |
| `DELETE`| `/api/v1/reports/:id` | Delete report and purge images from disk |
| `GET` | `/api/v1/map/markers` | Optimized coordinates and severity markers for GIS map |
| `GET` | `/api/v1/map/geojson` | GeoJSON FeatureCollection of all road distress points |
| `GET` | `/api/v1/admin/stats` | Aggregated KPIs and severity distributions |
| `GET/PUT` | `/api/v1/admin/cost-parameters` | View and edit dynamic municipal formula rates |

---

## License
MIT License. Free for personal, academic, and commercial use.
