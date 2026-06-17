"""
FastAPI Backend Server for IIoT Predictive Maintenance
Provides REST API endpoints for Next.js frontend
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from influxdb import InfluxDBClient
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uvicorn
import os
import shutil
import json
import pickle
import csv
import io
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# Import authentication (token validation only)
from src.auth import (
    get_current_user,
    get_current_active_admin,
)

# Configuration
INFLUX_HOST = os.getenv("INFLUX_HOST", "localhost")
INFLUX_PORT = int(os.getenv("INFLUX_PORT", "8086"))
INFLUX_DB = os.getenv("INFLUX_DB", "factory_data")
MEASUREMENT = "machine_telemetry"
MODEL_PATH = "/app/models/anomaly_model.pkl"
PREDICTIVE_MODEL_PATH = "/app/models/predictive_model.pkl"

# Expected sensor ranges (can be overridden via environment)
EXPECTED_MAX_VIBRATION = float(os.getenv("EXPECTED_MAX_VIBRATION", "100.0"))
EXPECTED_MAX_TEMPERATURE = float(os.getenv("EXPECTED_MAX_TEMPERATURE", "100.0"))
_calibrated_max_vibration: Optional[float] = None
_calibrated_max_temperature: Optional[float] = None
_calibration_ts: Optional[datetime] = None

def calibrate_expected_ranges() -> None:
    """Calibrate expected maxima from recent InfluxDB data (last 2h)."""
    global _calibrated_max_vibration, _calibrated_max_temperature, _calibration_ts
    if not influx_client:
        return
    try:
        query = f'''
            SELECT max("vibration") as max_vibration,
                   max("temperature") as max_temperature
            FROM "{MEASUREMENT}"
            WHERE time > now() - 2h
        '''
        result = influx_client.query(query)
        points = list(result.get_points())
        if points:
            mv = points[0].get('max_vibration')
            mt = points[0].get('max_temperature')
            if mv is not None and mt is not None:
                _calibrated_max_vibration = float(mv)
                _calibrated_max_temperature = float(mt)
                _calibration_ts = datetime.utcnow()
    except Exception:
        # Silent fail; keep previous values
        pass

def estimate_score(vibration: float, temperature: float) -> float:
    """Heuristic score in [-1, 1] based on normalized vib/temp.
    Higher vib/temp lowers the score. Uses expected max ranges for normalization.
    """
    try:
        # Optionally refresh calibration every 5 minutes
        if _calibration_ts is None or (datetime.utcnow() - _calibration_ts).total_seconds() > 300:
            calibrate_expected_ranges()

        max_vib = _calibrated_max_vibration if (_calibrated_max_vibration and _calibrated_max_vibration > 0) else EXPECTED_MAX_VIBRATION
        max_temp = _calibrated_max_temperature if (_calibrated_max_temperature and _calibrated_max_temperature > 0) else EXPECTED_MAX_TEMPERATURE

        # Normalize to [0, 1] using maxima; guard against zero
        vib_norm = 0.0 if max_vib <= 0 else min(max(vibration / max_vib, 0.0), 1.0)
        temp_norm = 0.0 if max_temp <= 0 else min(max(temperature / max_temp, 0.0), 1.0)
        # Weighted impact: vibration more important
        impact = 0.6 * vib_norm + 0.4 * temp_norm
        # Convert impact to score: high impact => lower score
        score = 1.0 - impact
        return float(max(-1.0, min(1.0, score)))
    except Exception:
        return 0.0

def normalize_score(score: float) -> float:
    """Normalize any incoming score to [0, 1] for UI consistency.
    If a model outputs in [-1, 1], map to [0, 1]; otherwise clamp."""
    try:
        if score <= 1.0 and score >= -1.0:
            norm = (score + 1.0) / 2.0
        else:
            norm = score
        if np.isnan(norm):
            return 0.0
        return float(max(0.0, min(1.0, norm)))
    except Exception:
        return 0.0

# Initialize FastAPI
app = FastAPI(
    title="IIoT Predictive Maintenance API",
    description="Real-time machine monitoring and anomaly detection API",
    version="1.0.0"
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Health check endpoint for Docker."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Initialize InfluxDB client
try:
    influx_client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    influx_client.switch_database(INFLUX_DB)
    print(f"✓ Connected to InfluxDB: {INFLUX_DB}")
except Exception as e:
    print(f"⚠️  Warning: Could not connect to InfluxDB: {e}")
    influx_client = None

# -----------------------------
# Note: Authentication endpoints moved to auth-service
# This service only validates JWT tokens for protected endpoints
# -----------------------------

# Import model registry and enhanced anomaly detection
try:
    from src.model_registry import (
        ModelRegistry, ModelType, ModelStatus, ModelMetrics, get_registry
    )
    from src.enhanced_anomaly_detection import (
        EnsembleAnomalyDetector, AnomalyPrediction
    )
    ENHANCED_ML_AVAILABLE = True
    print("✓ Enhanced ML modules loaded")
except ImportError as e:
    ENHANCED_ML_AVAILABLE = False
    print(f"⚠️  Enhanced ML modules not available: {e}")

# Initialize Chatbot
chatbot = None
chatbot_init_error = None
try:
    from src.chatbot import RAGChatbot
    chatbot = RAGChatbot()
    print("✓ Chatbot initialized")
except Exception as e:
    chatbot_init_error = str(e)
    print(f"⚠️  Warning: Could not initialize Chatbot: {e}")


# Pydantic models for request bodies
class TrainRequest(BaseModel):
    n_estimators: Optional[int] = 100
    contamination: Optional[float] = 0.1
    random_state: Optional[int] = 42

class ChatRequest(BaseModel):
    message: str

class MaintenanceTaskCreate(BaseModel):
    equipmentId: str
    title: str
    description: str
    dueDate: str
    nextDueDate: Optional[str] = None
    priority: str  # LOW, MEDIUM, HIGH
    anomalyId: Optional[str] = None
    aiDetectedCause: Optional[str] = None
    urgency: Optional[str] = None  # URGENT, NOT_URGENT
    importance: Optional[str] = None  # IMPORTANT, NOT_IMPORTANT

class MaintenanceTaskUpdate(BaseModel):
    status: Optional[str] = None  # NOT_STARTED, IN_PROGRESS, DONE
    assignedTo: Optional[str] = None
    completedBy: Optional[str] = None
    completionNotes: Optional[str] = None
    completedAt: Optional[str] = None
    nextDueDate: Optional[str] = None


def classify_eisenhower_matrix(priority: str, days_until_due: int, has_anomaly: bool) -> tuple[str, str, int]:
    """
    Classify task using Eisenhower Matrix and assign priority order
    Returns: (urgency, importance, order_priority)
    
    Quadrants:
    1. DO FIRST (Urgent + Important) - order 1
    2. SCHEDULE (Not Urgent + Important) - order 2
    3. DELEGATE (Urgent + Not Important) - order 3
    4. ELIMINATE (Not Urgent + Not Important) - order 4
    """
    # Determine urgency based on due date
    if days_until_due <= 2 or priority == "HIGH":
        urgency = "URGENT"
    else:
        urgency = "NOT_URGENT"
    
    # Determine importance based on anomaly detection and priority
    if has_anomaly or priority in ["HIGH", "MEDIUM"]:
        importance = "IMPORTANT"
    else:
        importance = "NOT_IMPORTANT"
    
    # Assign order priority based on quadrant
    if urgency == "URGENT" and importance == "IMPORTANT":
        order_priority = 1  # DO FIRST
        quadrant = "DO_FIRST"
    elif urgency == "NOT_URGENT" and importance == "IMPORTANT":
        order_priority = 2  # SCHEDULE
        quadrant = "SCHEDULE"
    elif urgency == "URGENT" and importance == "NOT_IMPORTANT":
        order_priority = 3  # DELEGATE
        quadrant = "DELEGATE"
    else:
        order_priority = 4  # ELIMINATE
        quadrant = "ELIMINATE"
    
    return urgency, importance, order_priority, quadrant


def auto_create_task_from_anomaly(equipment_id: str, vibration: float, temperature: float, 
                                   health_score: float, status: str) -> Optional[Dict[str, Any]]:
    """
    Automatically create maintenance task when AI detects anomaly or future failure
    """
    if status not in ["ANOMALY", "WARNING"]:
        return None
    
    # Check if task already exists for this equipment in last 24 hours
    recent_cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"
    existing_tasks = [t for t in _maintenance_tasks_db 
                     if t["equipmentId"] == equipment_id and t["createdAt"] > recent_cutoff]
    
    if existing_tasks:
        return None  # Don't create duplicate
    
    # Generate anomaly ID
    anomaly_id = f"A-{datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')}-{equipment_id}"
    
    # Determine cause and description
    causes = []
    if vibration > 85:
        causes.append(f"High vibration detected ({vibration:.1f})")
    if temperature > 70:
        causes.append(f"High temperature detected ({temperature:.1f}°C)")
    if health_score < 40:
        causes.append(f"Critical health score ({health_score:.1f}%)")
    
    ai_cause = ". ".join(causes) if causes else "Anomaly detected by AI system"
    
    # Determine priority and due date
    if status == "ANOMALY" or health_score < 40:
        priority = "HIGH"
        days_until_due = 1  # Urgent - 1 day
    elif health_score < 60:
        priority = "MEDIUM"
        days_until_due = 3  # Soon - 3 days
    else:
        priority = "MEDIUM"
        days_until_due = 7  # Schedule - 1 week
    
    due_date = (datetime.utcnow() + timedelta(days=days_until_due)).strftime("%Y-%m-%d")
    
    # Classify with Eisenhower Matrix
    urgency, importance, order_priority, quadrant = classify_eisenhower_matrix(
        priority, days_until_due, True
    )
    
    # Create task
    task_count = len(_maintenance_tasks_db) + 1
    task_id = f"T-{task_count:04d}"
    
    new_task = {
        "id": task_id,
        "equipmentId": equipment_id,
        "title": f"Investigate {status.lower()} on {equipment_id}",
        "description": f"AI system detected {status.lower()} requiring immediate attention. {ai_cause}",
        "dueDate": due_date,
        "priority": priority,
        "status": "NOT_STARTED",
        "assignedTo": None,
        "completedBy": None,
        "completionNotes": None,
        "completedAt": None,
        "anomalyId": anomaly_id,
        "aiDetectedCause": ai_cause,
        "urgency": urgency,
        "importance": importance,
        "orderPriority": order_priority,
        "eisenhowerQuadrant": quadrant,
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "autoCreated": True,
        "nextDueDate": None
    }
    
    _maintenance_tasks_db.append(new_task)
    return new_task


def map_status_code(status_code: str) -> str:
    """Map numeric status codes to human-readable strings"""
    status_mapping = {
        "0": "NORMAL",
        "1": "WARNING",
        "2": "ANOMALY",
        "NORMAL": "NORMAL",
        "WARNING": "WARNING",
        "ANOMALY": "ANOMALY"
    }
    return status_mapping.get(str(status_code), "UNKNOWN")


def calculate_health_score(vibration: float, temperature: float, ai_score: float) -> dict:
    """
    Calculate machine health score (0-100%) based on multiple factors
    Returns: health score, status, and next maintenance estimate
    """
    # Base score starts at 100
    health_score = 100.0
    
    # Vibration impact (0-85 = good, 85-95 = warning, >95 = critical)
    if vibration > 95:
        health_score -= 40
    elif vibration > 85:
        health_score -= 20
    elif vibration > 75:
        health_score -= 10
    
    # Temperature impact (0-70 = good, 70-80 = warning, >80 = critical)
    if temperature > 80:
        health_score -= 30
    elif temperature > 70:
        health_score -= 15
    elif temperature > 65:
        health_score -= 5
    
    # AI score impact (most important factor)
    if ai_score < -0.5:  # Anomaly
        health_score -= 35
    elif ai_score < 0.0:  # Warning
        health_score -= 15
    elif ai_score < 0.1:
        health_score -= 5
    
    # Ensure score is between 0-100
    health_score = max(0, min(100, health_score))
    
    # Determine health status
    if health_score >= 80:
        status = "EXCELLENT"
        color = "green"
    elif health_score >= 60:
        status = "GOOD"
        color = "green"
    elif health_score >= 40:
        status = "FAIR"
        color = "yellow"
    elif health_score >= 20:
        status = "POOR"
        color = "orange"
    else:
        status = "CRITICAL"
        color = "red"
    
    # Estimate days until maintenance (based on health score)
    # Higher score = more days until maintenance needed
    if health_score >= 80:
        days_until_maintenance = 14 + (health_score - 80) * 0.5
    elif health_score >= 60:
        days_until_maintenance = 7 + (health_score - 60) * 0.35
    elif health_score >= 40:
        days_until_maintenance = 3 + (health_score - 40) * 0.2
    elif health_score >= 20:
        days_until_maintenance = 1 + (health_score - 20) * 0.1
    else:
        days_until_maintenance = 0  # Immediate maintenance required
    
    return {
        "score": round(health_score, 1),
        "status": status,
        "color": color,
        "days_until_maintenance": round(days_until_maintenance, 1),
        "maintenance_urgency": "immediate" if days_until_maintenance < 1 else "soon" if days_until_maintenance < 3 else "scheduled"
    }

# -----------------------------
# Equipment & Maintenance APIs
# -----------------------------

# In-memory storage for equipment (replace with database in production)
_equipment_db: List[Dict[str, Any]] = [
    {"id": "MACHINE_002", "name": "Conveyor Belt", "type": "Conveyor", "status": "ONLINE", "location": "Line A", "mqtt_topic": "factory/plc/data"},
    {"id": "MACHINE_003", "name": "Industrial Motor", "type": "Motor", "status": "ONLINE", "location": "Line B", "mqtt_topic": "factory/plc/data"},
]

@app.get("/api/equipment")
def get_equipment() -> list[dict]:
    """Return a list of equipment with basic metadata."""
    return _equipment_db

@app.post("/api/equipment")
def add_equipment(equipment: dict) -> dict:
    """Register new equipment/PLC connection via ESP32/MQTT"""
    # Validate required fields
    required_fields = ["id", "name", "type", "location", "mqtt_topic"]
    for field in required_fields:
        if field not in equipment:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Check if equipment ID already exists
    if any(eq["id"] == equipment["id"] for eq in _equipment_db):
        raise HTTPException(status_code=409, detail=f"Equipment with ID {equipment['id']} already exists")
    
    # Add default status if not provided
    if "status" not in equipment:
        equipment["status"] = "ONLINE"
    
    # Add to database
    _equipment_db.append(equipment)
    
    return {
        "message": "Equipment registered successfully",
        "equipment": equipment,
        "mqtt_info": {
            "broker": "mqtt://mosquitto:1883",
            "topic": equipment["mqtt_topic"],
            "data_format": {
                "timestamp": "Unix timestamp or ISO 8601",
                "machine_id": equipment["id"],
                "equipment_name": equipment["name"],
                "vibration": "float (sensor reading)",
                "temperature": "float (°C)",
                "humidity": "float (% optional)"
            }
        }
    }

@app.delete("/api/equipment/{equipment_id}")
def delete_equipment(equipment_id: str) -> dict:
    """Remove equipment from registry"""
    global _equipment_db
    initial_count = len(_equipment_db)
    _equipment_db = [eq for eq in _equipment_db if eq["id"] != equipment_id]
    
    if len(_equipment_db) == initial_count:
        raise HTTPException(status_code=404, detail=f"Equipment {equipment_id} not found")
    
    return {"message": f"Equipment {equipment_id} removed successfully"}

# In-memory storage for maintenance tasks (replace with database in production)
_maintenance_tasks_db: List[Dict[str, Any]] = [
    {
        "id": "T-1001",
        "equipmentId": "PRESS_001",
        "title": "Lubrication & inspection",
        "description": "Regular scheduled maintenance for hydraulic press",
        "dueDate": "2025-12-15",
        "priority": "MEDIUM",
        "status": "NOT_STARTED",
        "assignedTo": None,
        "completedBy": None,
        "completionNotes": None,
        "completedAt": None,
        "anomalyId": None,
        "aiDetectedCause": None,
        "urgency": "NOT_URGENT",
        "importance": "IMPORTANT",
        "orderPriority": 2,
        "eisenhowerQuadrant": "SCHEDULE",
        "createdAt": "2025-12-01T10:00:00Z",
        "autoCreated": False,
        "nextDueDate": "2026-03-15"
    },
    {
        "id": "T-1002",
        "equipmentId": "CONV_014",
        "title": "Belt tension check",
        "description": "High vibration detected by AI system",
        "dueDate": "2025-12-12",
        "priority": "HIGH",
        "status": "IN_PROGRESS",
        "assignedTo": "John Smith",
        "completedBy": None,
        "completionNotes": None,
        "completedAt": None,
        "anomalyId": "A-2025-12-09-001",
        "aiDetectedCause": "Vibration levels exceeded normal range (85.3). Possible belt misalignment or bearing wear detected.",
        "urgency": "URGENT",
        "importance": "IMPORTANT",
        "orderPriority": 1,
        "eisenhowerQuadrant": "DO_FIRST",
        "createdAt": "2025-12-09T08:30:00Z",
        "autoCreated": True,
        "nextDueDate": "2026-01-12"
    },
    {
        "id": "T-1003",
        "equipmentId": "MOTOR_207",
        "title": "Bearing replacement",
        "description": "Scheduled bearing replacement",
        "dueDate": "2025-12-20",
        "priority": "LOW",
        "status": "NOT_STARTED",
        "assignedTo": None,
        "completedBy": None,
        "completionNotes": None,
        "completedAt": None,
        "anomalyId": None,
        "aiDetectedCause": None,
        "urgency": "NOT_URGENT",
        "importance": "NOT_IMPORTANT",
        "orderPriority": 4,
        "eisenhowerQuadrant": "ELIMINATE",
        "createdAt": "2025-12-05T14:00:00Z",
        "autoCreated": False,
        "nextDueDate": "2027-12-20"
    },
]

@app.get("/api/maintenance/tasks")
def get_maintenance_tasks(status: Optional[str] = None, sort_by_matrix: bool = True) -> list[dict]:
    """Return maintenance tasks with optional status filter, sorted by Eisenhower Matrix."""
    tasks = _maintenance_tasks_db
    
    if status:
        tasks = [task for task in tasks if task["status"] == status]
    
    # Sort by Eisenhower Matrix order priority
    if sort_by_matrix:
        tasks = sorted(tasks, key=lambda t: (t.get("orderPriority", 999), t.get("dueDate", "9999-12-31")))
    
    return tasks

@app.get("/api/maintenance/tasks/{task_id}")
def get_maintenance_task(task_id: str) -> dict:
    """Get a specific maintenance task by ID."""
    task = next((t for t in _maintenance_tasks_db if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/api/maintenance/tasks")
def create_maintenance_task(task: MaintenanceTaskCreate) -> dict:
    """Create a new maintenance task from an anomaly or manual entry."""
    # Generate task ID
    task_count = len(_maintenance_tasks_db) + 1
    task_id = f"T-{task_count:04d}"
    
    # Calculate days until due
    try:
        due_date_obj = datetime.strptime(task.dueDate, "%Y-%m-%d")
        days_until_due = (due_date_obj - datetime.utcnow()).days
    except:
        days_until_due = 7  # Default to 1 week
    
    # Classify with Eisenhower Matrix
    urgency, importance, order_priority, quadrant = classify_eisenhower_matrix(
        task.priority,
        days_until_due,
        task.anomalyId is not None
    )
    
    new_task = {
        "id": task_id,
        "equipmentId": task.equipmentId,
        "title": task.title,
        "description": task.description,
        "dueDate": task.dueDate,
        "priority": task.priority,
        "status": "NOT_STARTED",
        "assignedTo": None,
        "completedBy": None,
        "completionNotes": None,
        "completedAt": None,
        "anomalyId": task.anomalyId,
        "aiDetectedCause": task.aiDetectedCause,
        "urgency": urgency,
        "importance": importance,
        "orderPriority": order_priority,
        "eisenhowerQuadrant": quadrant,
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "autoCreated": False,
        "nextDueDate": task.nextDueDate
    }
    
    _maintenance_tasks_db.append(new_task)
    return new_task

@app.patch("/api/maintenance/tasks/{task_id}")
def update_maintenance_task(task_id: str, update: MaintenanceTaskUpdate) -> dict:
    """Update a maintenance task status, assignee, or completion."""
    task = next((t for t in _maintenance_tasks_db if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields if provided
    if update.status is not None:
        task["status"] = update.status
    if update.assignedTo is not None:
        task["assignedTo"] = update.assignedTo
    if update.completedBy is not None:
        task["completedBy"] = update.completedBy
    if update.completionNotes is not None:
        task["completionNotes"] = update.completionNotes
    if update.completedAt is not None:
        task["completedAt"] = update.completedAt
    
    # Also allow updating nextDueDate if passed (we can add it to MaintenanceTaskUpdate)
    if hasattr(update, "nextDueDate") and getattr(update, "nextDueDate", None) is not None:
        task["nextDueDate"] = update.nextDueDate
    
    # Auto-set completion timestamp if status changed to DONE
    if update.status == "DONE" and not task["completedAt"]:
        task["completedAt"] = datetime.utcnow().isoformat() + "Z"
    
    return task

@app.get("/api/maintenance/report/{task_id}")
def generate_maintenance_report_pdf(task_id: str):
    """Generate a detailed maintenance report in PDF format."""
    task = next((t for t in _maintenance_tasks_db if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Generate PDF
    pdf_buffer = io.BytesIO()
    pdf_content = generate_pdf_report(task, pdf_buffer)
    
    # Return PDF as response
    pdf_buffer.seek(0)
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=maintenance-report-{task_id}.pdf"
        }
    )

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat with the RAG chatbot (one-shot, returns full answer)."""
    if not chatbot:
        detail = f"Chatbot service not available. Error: {chatbot_init_error}" if chatbot_init_error else "Chatbot service not initialized"
        raise HTTPException(status_code=503, detail=detail)

    try:
        response = chatbot.query(request.message)
        return {"answer": response["answer"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Stream the RAG answer token-by-token as plain text."""
    if not chatbot:
        detail = f"Chatbot service not available. Error: {chatbot_init_error}" if chatbot_init_error else "Chatbot service not initialized"
        raise HTTPException(status_code=503, detail=detail)

    async def token_generator():
        async for tok in chatbot.stream_query(request.message):
            yield tok

    return StreamingResponse(
        token_generator(),
        media_type="text/plain; charset=utf-8",
        # Disable nginx response buffering so tokens reach the browser as they arrive.
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )

@app.post("/api/chat/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF document to the chatbot knowledge base."""
    if not chatbot:
        detail = f"Chatbot service not available. Error: {chatbot_init_error}" if chatbot_init_error else "Chatbot service not initialized"
        raise HTTPException(status_code=503, detail=detail)
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
    try:
        # Create temp file
        temp_dir = "data/uploads"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Ingest
        chatbot.ingest_data(file_path, is_directory=False)
        
        # Clean up (optional, keep for now or delete)
        # os.remove(file_path)
        
        return {"message": f"Successfully uploaded and ingested {file.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

def generate_pdf_report(task: dict, buffer: io.BytesIO) -> bytes:
    """Generate a comprehensive PDF maintenance report."""
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for PDF elements
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#0ea5e9'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    story.append(Paragraph(f"Maintenance Report", title_style))
    story.append(Paragraph(f"{task['title']}", styles['Heading2']))
    story.append(Spacer(1, 0.3*inch))
    
    # Task Information Table
    story.append(Paragraph("Task Information", heading_style))
    
    task_data = [
        ['Task ID:', task['id']],
        ['Equipment:', task['equipmentId']],
        ['Status:', task['status'].replace('_', ' ')],
        ['Priority:', task['priority']],
        ['Eisenhower Matrix:', task.get('eisenhowerQuadrant', 'N/A').replace('_', ' ')],
        ['Created:', task['createdAt'][:10]],
        ['Due Date:', task['dueDate']],
    ]
    
    task_table = Table(task_data, colWidths=[2*inch, 4*inch])
    task_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    story.append(task_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Description
    story.append(Paragraph("Description", heading_style))
    story.append(Paragraph(task['description'], styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    # AI Analysis Section
    if task.get('anomalyId'):
        story.append(Paragraph("AI Analysis & Anomaly Detection", heading_style))
        
        anomaly_data = [
            ['Anomaly ID:', task['anomalyId']],
            ['Auto-Created:', 'Yes' if task.get('autoCreated') else 'No'],
            ['Detection Time:', task['createdAt'][:16].replace('T', ' ')],
        ]
        
        anomaly_table = Table(anomaly_data, colWidths=[2*inch, 4*inch])
        anomaly_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fef3c7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        story.append(anomaly_table)
        story.append(Spacer(1, 0.1*inch))
        
        if task.get('aiDetectedCause'):
            story.append(Paragraph("<b>AI Detected Cause:</b>", styles['BodyText']))
            story.append(Paragraph(task['aiDetectedCause'], styles['BodyText']))
            story.append(Spacer(1, 0.1*inch))
            
            story.append(Paragraph(
                "The AI system detected abnormal behavior that triggered this maintenance task. "
                "The anomaly was automatically flagged based on sensor data analysis and predictive models.",
                styles['BodyText']
            ))
    else:
        story.append(Paragraph("Maintenance Type", heading_style))
        story.append(Paragraph(
            "This is a scheduled maintenance task. No anomaly was detected by the AI system.",
            styles['BodyText']
        ))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Eisenhower Matrix Classification
    story.append(Paragraph("Priority Classification (Eisenhower Matrix)", heading_style))
    
    matrix_data = [
        ['Urgency:', task.get('urgency', 'N/A')],
        ['Importance:', task.get('importance', 'N/A')],
        ['Quadrant:', task.get('eisenhowerQuadrant', 'N/A').replace('_', ' ')],
        ['Order Priority:', str(task.get('orderPriority', 'N/A'))],
    ]
    
    matrix_table = Table(matrix_data, colWidths=[2*inch, 4*inch])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#dbeafe')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    story.append(matrix_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Assignment & Execution
    story.append(Paragraph("Assignment & Execution", heading_style))
    
    exec_data = [
        ['Assigned To:', task.get('assignedTo') or 'Not yet assigned'],
        ['Completed By:', task.get('completedBy') or 'Not completed'],
        ['Completion Date:', task.get('completedAt', 'N/A')[:10] if task.get('completedAt') else 'N/A'],
    ]
    
    exec_table = Table(exec_data, colWidths=[2*inch, 4*inch])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    story.append(exec_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Completion Notes
    if task.get('completionNotes'):
        story.append(Paragraph("Completion Notes", heading_style))
        story.append(Paragraph(task['completionNotes'], styles['BodyText']))
        story.append(Spacer(1, 0.2*inch))
    
    # Recommendations
    story.append(Paragraph("Recommendations", heading_style))
    recommendations = [
        "Monitor equipment performance after maintenance completion",
        "Update maintenance schedule based on actual findings and AI predictions",
        "Document any parts replaced or repairs performed in the system",
        "Validate AI model predictions against actual findings to improve accuracy",
        "Review Eisenhower Matrix classification for future similar tasks"
    ]
    
    for rec in recommendations:
        story.append(Paragraph(f"• {rec}", styles['BodyText']))
    
    story.append(Spacer(1, 0.4*inch))
    
    # Footer
    story.append(Paragraph(
        f"<i>Report generated by IIoT Predictive Maintenance System<br/>"
        f"Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</i>",
        styles['Normal']
    ))
    
    # Build PDF
    doc.build(story)
    return buffer.getvalue()

def generate_markdown_report(task: dict) -> str:
    """Generate a Markdown maintenance report."""
    status_emoji = {
        "NOT_STARTED": "⏳",
        "IN_PROGRESS": "🔧",
        "DONE": "✅"
    }
    priority_emoji = {
        "LOW": "🟢",
        "MEDIUM": "🟡",
        "HIGH": "🔴"
    }
    
    report = f"""# Maintenance Report: {task['title']}

## Task Information
- **Task ID:** {task['id']}
- **Equipment:** {task['equipmentId']}
- **Status:** {status_emoji.get(task['status'], '❓')} {task['status'].replace('_', ' ')}
- **Priority:** {priority_emoji.get(task['priority'], '⚪')} {task['priority']}
- **Created:** {task['createdAt']}
- **Due Date:** {task['dueDate']}

## Description
{task['description']}

## AI Analysis
"""
    
    if task['anomalyId']:
        report += f"""
### Anomaly Detection
- **Anomaly ID:** {task['anomalyId']}
- **AI Detected Cause:** {task['aiDetectedCause'] or 'No specific cause identified'}

The AI system detected abnormal behavior that triggered this maintenance task. The anomaly was automatically flagged based on sensor data analysis and predictive models.
"""
    else:
        report += "\nThis is a scheduled maintenance task. No anomaly was detected by the AI system.\n"
    
    report += f"""
## Assignment & Execution
- **Assigned To:** {task['assignedTo'] or 'Not yet assigned'}
- **Completed By:** {task['completedBy'] or 'Not completed'}
- **Completion Date:** {task['completedAt'] or 'N/A'}

"""
    
    if task['completionNotes']:
        report += f"""## Completion Notes
{task['completionNotes']}

"""
    
    report += f"""## Recommendations
- Monitor equipment performance after maintenance
- Update maintenance schedule based on findings
- Document any parts replaced or repairs performed
- Validate AI model predictions against actual findings

---
*Report generated by IIoT Predictive Maintenance System*  
*Generated at: {datetime.utcnow().isoformat()}Z*
"""
    
    return report

def generate_latex_report(task: dict) -> str:
    """Generate a LaTeX maintenance report."""
    status_symbol = {
        "NOT_STARTED": r"$\circ$",
        "IN_PROGRESS": r"$\triangleright$",
        "DONE": r"$\checkmark$"
    }
    
    report = r"""\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{xcolor}
\geometry{a4paper, margin=1in}

\title{Maintenance Report: """ + task['title'].replace('_', r'\_') + r"""}
\author{IIoT Predictive Maintenance System}
\date{""" + datetime.utcnow().strftime("%B %d, %Y") + r"""}

\begin{document}

\maketitle

\section{Task Information}
\begin{itemize}
    \item \textbf{Task ID:} """ + task['id'] + r"""
    \item \textbf{Equipment:} """ + task['equipmentId'].replace('_', r'\_') + r"""
    \item \textbf{Status:} """ + status_symbol.get(task['status'], r"$\bullet$") + " " + task['status'].replace('_', r'\_') + r"""
    \item \textbf{Priority:} """ + task['priority'] + r"""
    \item \textbf{Created:} """ + task['createdAt'] + r"""
    \item \textbf{Due Date:} """ + task['dueDate'] + r"""
\end{itemize}

\section{Description}
""" + task['description'].replace('_', r'\_') + r"""

\section{AI Analysis}
"""
    
    if task['anomalyId']:
        report += r"""
\subsection{Anomaly Detection}
\begin{itemize}
    \item \textbf{Anomaly ID:} """ + task['anomalyId'] + r"""
    \item \textbf{AI Detected Cause:} """ + (task['aiDetectedCause'] or 'No specific cause identified').replace('_', r'\_') + r"""
\end{itemize}

The AI system detected abnormal behavior that triggered this maintenance task. The anomaly was automatically flagged based on sensor data analysis and predictive models.
"""
    else:
        report += r"""
This is a scheduled maintenance task. No anomaly was detected by the AI system.
"""
    
    report += r"""

\section{Assignment \& Execution}
\begin{itemize}
    \item \textbf{Assigned To:} """ + (task['assignedTo'] or 'Not yet assigned').replace('_', r'\_') + r"""
    \item \textbf{Completed By:} """ + (task['completedBy'] or 'Not completed').replace('_', r'\_') + r"""
    \item \textbf{Completion Date:} """ + (task['completedAt'] or 'N/A') + r"""
\end{itemize}
"""
    
    if task['completionNotes']:
        report += r"""
\section{Completion Notes}
""" + task['completionNotes'].replace('_', r'\_') + r"""
"""
    
    report += r"""

\section{Recommendations}
\begin{itemize}
    \item Monitor equipment performance after maintenance
    \item Update maintenance schedule based on findings
    \item Document any parts replaced or repairs performed
    \item Validate AI model predictions against actual findings
\end{itemize}

\vfill
\hrule
\vspace{0.2cm}
\textit{Report generated by IIoT Predictive Maintenance System}\\
\textit{Generated at: """ + datetime.utcnow().isoformat() + r"""Z}

\end{document}
"""
    
    return report

@app.get("/api/shifts")
def get_shifts() -> list[dict]:
    """Return shift schedule with operators and production metrics."""
    return [
        {"id": "S-1", "name": "Morning Shift", "startTime": "06:00", "endTime": "14:00", "operator": "John Smith", "status": "ACTIVE", "productionCount": 1247, "downtime": 12, "efficiency": 94.8},
        {"id": "S-2", "name": "Afternoon Shift", "startTime": "14:00", "endTime": "22:00", "operator": "Mike Johnson", "status": "SCHEDULED", "productionCount": 0, "downtime": 0, "efficiency": 0},
        {"id": "S-3", "name": "Night Shift", "startTime": "22:00", "endTime": "06:00", "operator": "Sarah Williams", "status": "COMPLETED", "productionCount": 1156, "downtime": 18, "efficiency": 92.3},
    ]

@app.get("/api/production/oee")
def get_oee(equipmentId: Optional[str] = None) -> dict:
    """Calculate OEE (Overall Equipment Effectiveness) metrics."""
    # Mock OEE calculation - in production would pull from real data
    availability = 94.5
    performance = 96.2
    quality = 98.8
    oee = (availability * performance * quality) / 10000
    
    return {
        "oee": round(oee, 2),
        "availability": round(availability, 2),
        "performance": round(performance, 2),
        "quality": round(quality, 2),
        "target": 85.0,
        "status": "EXCELLENT" if oee >= 85 else "GOOD" if oee >= 75 else "NEEDS_IMPROVEMENT"
    }

@app.get("/api/reports")
def get_reports() -> list[dict]:
    """Return available reports for download."""
    return [
        {"id": "R-001", "title": "Daily Production Report", "type": "DAILY", "date": "2025-12-09", "size": "2.4 MB", "status": "READY"},
        {"id": "R-002", "title": "Weekly Maintenance Summary", "type": "WEEKLY", "date": "2025-12-08", "size": "8.1 MB", "status": "READY"},
        {"id": "R-003", "title": "Monthly OEE Analysis", "type": "MONTHLY", "date": "2025-11-30", "size": "15.7 MB", "status": "READY"},
        {"id": "R-004", "title": "Custom Anomaly Report", "type": "CUSTOM", "date": "2025-12-09", "size": "N/A", "status": "GENERATING"},
    ]

@app.get("/api/compliance")
def get_compliance() -> dict:
    """Return compliance and audit information."""
    return {
        "lastAudit": "2025-11-15",
        "nextReview": "2026-02-15",
        "complianceScore": 98.5,
        "standards": ["ISO 9001", "Industry 4.0", "OSHA"],
        "issues": [],
        "status": "COMPLIANT"
    }


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "IIoT Predictive Maintenance API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": [
            "/api/live",
            "/api/history",
            "/docs"
        ]
    }


@app.get("/api/live")
async def get_live_data(machine_id: str = "MACHINE_001"):
    """
    Get the latest sensor reading and AI prediction for a specific machine
    
    Args:
        machine_id: Equipment identifier (default: MACHINE_001)
    
    Returns: Current vibration, temperature, AI score, and status
    """
    if not influx_client:
        raise HTTPException(
            status_code=503,
            detail="InfluxDB connection not available"
        )
    
    try:
        # Query for the most recent record for specific machine
        query = f'''
            SELECT last("vibration") as vibration,
                   last("temperature") as temperature,
                   last("humidity") as humidity,
                   last("ai_score") as score
            FROM "{MEASUREMENT}"
            WHERE "machine_id" = '{machine_id}'
            AND time > now() - 1h
        '''
        
        result = influx_client.query(query)
        points = list(result.get_points())
        
        if not points:
            raise HTTPException(
                status_code=404,
                detail=f"No data available for machine {machine_id}. Ensure the data ingestion pipeline is running."
            )
        
        data = points[0]
        
        # Get the latest status from tags (if available)
        status_query = f'''
            SELECT last("ai_score") as score
            FROM "{MEASUREMENT}"
            WHERE "machine_id" = '{machine_id}'
            AND time > now() - 1h
        '''
        status_result = influx_client.query(status_query)
        
        # Determine status based on AI score
        # Read raw values and guard against None/NaN
        raw_score = data.get('score', 0)
        raw_vibration = data.get('vibration', 0)
        raw_temperature = data.get('temperature', 0)
        raw_humidity = data.get('humidity', None)

        def _to_float_safe(val, default=0.0):
            try:
                if val is None:
                    return default
                f = float(val)
                if np.isnan(f):
                    return default
                return f
            except Exception:
                return default

        score = _to_float_safe(raw_score, 0.0)
        vibration = _to_float_safe(raw_vibration, 0.0)
        temperature = _to_float_safe(raw_temperature, 0.0)
        humidity = _to_float_safe(raw_humidity, 0.0)

        # Fallback score estimation if missing/zero and we have signals
        if (raw_score is None or score == 0.0) and (vibration > 0 or temperature > 0):
            score = estimate_score(vibration, temperature)
        # Normalize to [0,1]
        score = normalize_score(score)
        
        if score < 0.1:
            status = "ANOMALY"
        elif score < 0.3:
            status = "WARNING"
        else:
            status = "NORMAL"
        
        # Calculate health score
        health_data = calculate_health_score(vibration, temperature, score)
        
        # Auto-create maintenance task if anomaly or warning detected
        if status in ["ANOMALY", "WARNING"]:
            auto_task = auto_create_task_from_anomaly(
                machine_id,
                vibration,
                temperature,
                health_data['score'],
                status
            )
            if auto_task:
                print(f"✓ Auto-created maintenance task: {auto_task['id']} for {machine_id}")
        
        return {
            "machine_id": machine_id,
            "vibration": round(vibration, 2),
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
            "score": round(score, 4),
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "health": health_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error querying InfluxDB: {str(e)}"
        )


@app.get("/api/machines")
async def get_machines():
    """
    Get list of all machines with their latest status
    
    Returns: List of machines with current state
    """
    if not influx_client:
        raise HTTPException(
            status_code=503,
            detail="InfluxDB connection not available"
        )
    
    try:
        # Query for all unique machines
        query = f'''
            SHOW TAG VALUES FROM "{MEASUREMENT}" WITH KEY = "machine_id"
        '''
        
        result = influx_client.query(query)
        points = list(result.get_points())
        
        if not points:
            # Return default machines if no data
            return [
                {"machine_id": "MACHINE_001", "name": "Hydraulic Press", "status": "UNKNOWN"},
                {"machine_id": "MACHINE_002", "name": "Conveyor Belt", "status": "UNKNOWN"},
                {"machine_id": "MACHINE_003", "name": "Industrial Motor", "status": "UNKNOWN"}
            ]
        
        machines = []
        for point in points:
            machine_id = point.get('value')
            if machine_id:
                # Get latest status for this machine
                status_query = f'''
                    SELECT last("ai_score") as score, "equipment_name"
                    FROM "{MEASUREMENT}"
                    WHERE "machine_id" = '{machine_id}'
                    AND time > now() - 5m
                '''
                status_result = influx_client.query(status_query)
                status_points = list(status_result.get_points())
                
                if status_points:
                    score = status_points[0].get('score', 0)
                    equipment_name = status_points[0].get('equipment_name', machine_id)
                    
                    # Determine status
                    if score < 0.1:
                        status = "ANOMALY"
                    elif score < 0.3:
                        status = "WARNING"
                    else:
                        status = "NORMAL"
                else:
                    equipment_name = machine_id
                    status = "UNKNOWN"
                
                machines.append({
                    "machine_id": machine_id,
                    "name": equipment_name,
                    "status": status
                })
        
        return machines
        
    except Exception as e:
        # Return default machines on error
        return [
            {"machine_id": "MACHINE_001", "name": "Hydraulic Press", "status": "UNKNOWN"},
            {"machine_id": "MACHINE_002", "name": "Conveyor Belt", "status": "UNKNOWN"},
            {"machine_id": "MACHINE_003", "name": "Industrial Motor", "status": "UNKNOWN"}
        ]


@app.get("/api/history")
async def get_history(limit: int = 50, machine_id: str = None):
    """
    Get historical sensor readings for charting
    
    Args:
        limit: Number of records to return (default: 50, max: 500)
        machine_id: Optional filter for specific machine
    
    Returns: List of timestamped readings
    """
    if not influx_client:
        raise HTTPException(
            status_code=503,
            detail="InfluxDB connection not available"
        )
    
    # Limit to reasonable range
    limit = min(limit, 500)
    
    try:
        # Query for historical data with optional machine filter
        machine_filter = f'AND "machine_id" = \'{machine_id}\'' if machine_id else ''
        query = f'''
            SELECT "vibration", "temperature", "humidity", "ai_score", "machine_id"
            FROM "{MEASUREMENT}"
            WHERE time > now() - 1h {machine_filter}
            ORDER BY time DESC
            LIMIT {limit}
        '''
        
        result = influx_client.query(query)
        points = list(result.get_points())
        
        if not points:
            return []
        
        # Reverse to get chronological order
        points.reverse()
        
        # Format data for frontend
        history = []
        for point in points:
            raw_score = point.get('ai_score', 0)
            raw_vibration = point.get('vibration', 0)
            raw_temperature = point.get('temperature', 0)
            raw_humidity = point.get('humidity', None)

            def _to_float_safe(val, default=0.0):
                try:
                    if val is None:
                        return default
                    f = float(val)
                    if np.isnan(f):
                        return default
                    return f
                except Exception:
                    return default

            score = _to_float_safe(raw_score, 0.0)
            vibration = _to_float_safe(raw_vibration, 0.0)
            temperature = _to_float_safe(raw_temperature, 0.0)
            humidity = _to_float_safe(raw_humidity, 0.0)
            machine = point.get('machine_id', 'UNKNOWN')

            # Fallback score estimation if missing/zero but signals present
            if (raw_score is None or score == 0.0) and (vibration > 0 or temperature > 0):
                score = estimate_score(vibration, temperature)
            # Normalize to [0,1]
            score = normalize_score(score)
            
            # Determine status
            if score < 0.1:
                status = "ANOMALY"
            elif score < 0.3:
                status = "WARNING"
            else:
                status = "NORMAL"
            
            history.append({
                "timestamp": point.get('time'),
                "machine_id": machine,
                "vibration": round(vibration, 2),
                "temperature": round(temperature, 2),
                "humidity": round(humidity, 2),
                "score": round(score, 4),
                "status": status
            })
        
        return history
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error querying InfluxDB: {str(e)}"
        )


@app.get("/api/stats")
async def get_statistics(equipmentId: Optional[str] = None):
    """
    Get aggregated statistics for the dashboard
    Returns: Summary statistics over the last 24 hours
    """
    if not influx_client:
        raise HTTPException(
            status_code=503,
            detail="InfluxDB connection not available"
        )
    
    try:
        # Get statistics for last 24h
        query = f'''
            SELECT mean("vibration") as avg_vibration,
                   max("vibration") as max_vibration,
                   mean("temperature") as avg_temperature,
                   max("temperature") as max_temperature,
                   mean("ai_score") as avg_score,
                   min("ai_score") as min_score,
                   count("ai_score") as total_readings
            FROM "{MEASUREMENT}"
            WHERE time > now() - 24h
        '''
        
        result = influx_client.query(query)
        points = list(result.get_points())
        
        if not points or not points[0].get('total_readings'):
            return {
                "vibration": {"average": 0, "max": 0},
                "temperature": {"average": 0, "max": 0},
                "ai_score": {"average": 0, "min": 0},
                "uptime_percentage": 0,
                "total_readings": 0,
                "anomalies_today": 0,
                "warnings_today": 0
            }
        
        data = points[0]
        total_readings = int(data.get('total_readings', 0))
        
        # Count anomalies and warnings in last 24h
        anomaly_query = f'''
            SELECT count("ai_score") as count
            FROM "{MEASUREMENT}"
            WHERE time > now() - 24h AND "ai_score" < -0.5
        '''
        anomaly_result = influx_client.query(anomaly_query)
        anomaly_points = list(anomaly_result.get_points())
        anomalies = int(anomaly_points[0].get('count', 0)) if anomaly_points else 0
        
        warning_query = f'''
            SELECT count("ai_score") as count
            FROM "{MEASUREMENT}"
            WHERE time > now() - 24h AND "ai_score" >= -0.5 AND "ai_score" < 0.1
        '''
        warning_result = influx_client.query(warning_query)
        warning_points = list(warning_result.get_points())
        warnings = int(warning_points[0].get('count', 0)) if warning_points else 0
        
        # Calculate uptime (percentage of normal readings)
        normal_readings = total_readings - anomalies - warnings
        uptime_percentage = (normal_readings / total_readings * 100) if total_readings > 0 else 100
        
        # Slight per-equipment variation (mock) when scoped
        vib_adjust = 0.0
        temp_adjust = 0.0
        if equipmentId:
            if equipmentId.endswith("001"):
                vib_adjust = 1.5
            elif equipmentId.endswith("014"):
                temp_adjust = 1.0

        return {
            "vibration": {
                "average": round(float(data.get('avg_vibration', 0)) + vib_adjust, 2),
                "max": round(float(data.get('max_vibration', 0)) + vib_adjust, 2)
            },
            "temperature": {
                "average": round(float(data.get('avg_temperature', 0)) + temp_adjust, 2),
                "max": round(float(data.get('max_temperature', 0)) + temp_adjust, 2)
            },
            "ai_score": {
                "average": round(float(data.get('avg_score', 0)), 4),
                "min": round(float(data.get('min_score', 0)), 4)
            },
            "uptime_percentage": round(uptime_percentage, 1),
            "total_readings": total_readings,
            "anomalies_today": anomalies,
            "warnings_today": warnings
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error querying statistics: {str(e)}"
        )


@app.get("/api/pareto/anomalies")
async def get_anomaly_pareto(machine_id: Optional[str] = None, days: int = 30):
    """
    Get Pareto analysis data for anomaly causes
    
    Args:
        machine_id: Optional filter for specific machine
        days: Number of days to analyze (default: 30, max: 90)
    
    Returns: Pareto data showing anomaly causes ranked by frequency
    """
    if not influx_client:
        raise HTTPException(
            status_code=503,
            detail="InfluxDB connection not available"
        )
    
    days = min(days, 90)
    
    try:
        # Query anomalies and warnings from last N days
        machine_filter = f'AND "machine_id" = \'{machine_id}\'' if machine_id else ''
        query = f'''
            SELECT "vibration", "temperature", "ai_score", "machine_id"
            FROM "{MEASUREMENT}"
            WHERE time > now() - {days}d {machine_filter}
        '''
        
        result = influx_client.query(query)
        points = list(result.get_points())
        
        # Analyze and categorize anomalies
        causes = {
            'High Vibration': 0,
            'Temperature Spikes': 0,
            'Combined (Vib + Temp)': 0,
            'Bearing Wear Pattern': 0,
            'Low Health Score': 0,
            'Other': 0
        }
        
        for point in points:
            vib = point.get('vibration', 0)
            temp = point.get('temperature', 0)
            score = point.get('ai_score', 1)
            
            # Categorize based on sensor values
            high_vib = vib > 75
            high_temp = temp > 70
            low_score = score < 0.15
            
            if high_vib and high_temp:
                causes['Combined (Vib + Temp)'] += 1
            elif high_vib:
                # Check if it's bearing wear pattern (gradual increase)
                if 75 < vib < 90:
                    causes['Bearing Wear Pattern'] += 1
                else:
                    causes['High Vibration'] += 1
            elif high_temp:
                causes['Temperature Spikes'] += 1
            elif low_score:
                causes['Low Health Score'] += 1
            else:
                causes['Other'] += 1
        
        # Calculate percentages and cumulative
        total = sum(causes.values())
        if total == 0:
            # Return default data if no anomalies
            return [
                {"factor": "High Vibration", "count": 0, "percentage": 0, "cumulative": 0},
                {"factor": "Temperature Spikes", "count": 0, "percentage": 0, "cumulative": 0},
                {"factor": "Combined (Vib + Temp)", "count": 0, "percentage": 0, "cumulative": 0},
                {"factor": "Bearing Wear Pattern", "count": 0, "percentage": 0, "cumulative": 0},
                {"factor": "Other", "count": 0, "percentage": 0, "cumulative": 0}
            ]
        
        # Sort by count descending
        sorted_causes = sorted(causes.items(), key=lambda x: x[1], reverse=True)
        
        pareto_data = []
        cumulative = 0
        for factor, count in sorted_causes:
            if count > 0:  # Only include non-zero causes
                percentage = round((count / total) * 100, 1)
                cumulative += percentage
                pareto_data.append({
                    "factor": factor,
                    "count": count,
                    "percentage": percentage,
                    "cumulative": round(cumulative, 1)
                })
        
        return pareto_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating Pareto data: {str(e)}"
        )


@app.get("/api/pareto/maintenance")
async def get_maintenance_pareto(days: int = 90):
    """
    Get Pareto analysis for maintenance tasks
    
    Args:
        days: Number of days to analyze (default: 90)
    
    Returns: Pareto data showing most common maintenance types
    """
    try:
        # Analyze maintenance tasks from database
        task_types = {
            'Vibration Issues': 0,
            'Temperature Problems': 0,
            'Bearing Replacement': 0,
            'Lubrication': 0,
            'Belt Adjustment': 0,
            'Preventive Maintenance': 0,
            'Other': 0
        }
        
        # Categorize existing tasks
        for task in _maintenance_tasks_db.values():
            title = task['title'].lower()
            desc = task['description'].lower()
            
            if 'vibration' in title or 'vibration' in desc:
                task_types['Vibration Issues'] += 1
            elif 'temperature' in title or 'temperature' in desc or 'heat' in desc:
                task_types['Temperature Problems'] += 1
            elif 'bearing' in title or 'bearing' in desc:
                task_types['Bearing Replacement'] += 1
            elif 'lubrication' in title or 'lubrication' in desc or 'oil' in desc:
                task_types['Lubrication'] += 1
            elif 'belt' in title or 'belt' in desc:
                task_types['Belt Adjustment'] += 1
            elif 'schedule' in title or 'preventive' in desc:
                task_types['Preventive Maintenance'] += 1
            else:
                task_types['Other'] += 1
        
        total = sum(task_types.values())
        if total == 0:
            total = 1  # Avoid division by zero
        
        # Sort and calculate percentages
        sorted_types = sorted(task_types.items(), key=lambda x: x[1], reverse=True)
        
        pareto_data = []
        cumulative = 0
        for task_type, count in sorted_types:
            if count > 0:
                percentage = round((count / total) * 100, 1)
                cumulative += percentage
                pareto_data.append({
                    "factor": task_type,
                    "count": count,
                    "percentage": percentage,
                    "cumulative": round(cumulative, 1),
                    "cost_estimate": count * 500  # Estimated cost per task
                })
        
        return pareto_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating maintenance Pareto: {str(e)}"
        )


@app.get("/api/rul")
async def get_remaining_useful_life(machine_id: Optional[str] = None):
    """
    Calculate Remaining Useful Life (RUL) for machines using ML-based degradation analysis.
    
    RUL Calculation Method:
    1. Analyze historical health score degradation rate
    2. Calculate exponential decay based on current trajectory
    3. Factor in vibration and temperature trends
    4. Estimate days until critical threshold (20% health)
    
    Returns:
    - rul_days: Estimated days until maintenance required
    - confidence: Prediction confidence (0-100%)
    - degradation_rate: Daily health score decline
    - critical_factors: Key contributors to degradation
    - recommendation: Maintenance action suggestion
    """
    if not influx_client:
        raise HTTPException(status_code=503, detail="InfluxDB not connected")
    
    try:
        # Get list of machines to analyze
        machines_to_analyze = []
        if machine_id:
            machines_to_analyze = [machine_id]
        else:
            # Get all unique machines
            query = f'SHOW TAG VALUES FROM "{MEASUREMENT}" WITH KEY = "machine_id"'
            result = influx_client.query(query)
            machines_to_analyze = [point['value'] for point in result.get_points()]
            if not machines_to_analyze:
                machines_to_analyze = ['MACHINE_001', 'MACHINE_002', 'MACHINE_003']
        
        rul_predictions = []
        
        for mid in machines_to_analyze:
            # Query last 7 days of data for trend analysis
            query = f'''
                SELECT mean("vibration") as vibration,
                       mean("temperature") as temperature,
                       mean("humidity") as humidity,
                       mean("health_score") as health_score
                FROM "{MEASUREMENT}"
                WHERE "machine_id" = '{mid}'
                  AND time > now() - 7d
                GROUP BY time(6h)
                ORDER BY time DESC
            '''
            
            result = influx_client.query(query)
            points = list(result.get_points())
            
            if len(points) < 4:  # Need at least 24 hours of data
                # Insufficient data - use default estimates
                rul_predictions.append({
                    "machine_id": mid,
                    "rul_days": 30,
                    "confidence": 30,
                    "health_score": 85,
                    "degradation_rate": 0.5,
                    "critical_factors": ["Insufficient historical data"],
                    "recommendation": "Continue monitoring - collecting baseline data",
                    "status": "MONITORING",
                    "urgency": "LOW"
                })
                continue
            
            # Extract time series data
            health_scores = [p.get('health_score', 80) for p in reversed(points) if p.get('health_score') is not None]
            vibrations = [p.get('vibration', 50) for p in reversed(points) if p.get('vibration') is not None]
            temperatures = [p.get('temperature', 50) for p in reversed(points) if p.get('temperature') is not None]
            
            if not health_scores:
                health_scores = [80]
            
            current_health = health_scores[-1] if health_scores else 80
            
            # Calculate degradation rate using linear regression
            if len(health_scores) >= 4:
                x = np.arange(len(health_scores)).reshape(-1, 1)
                y = np.array(health_scores)
                
                # Simple linear regression for trend
                x_mean = x.mean()
                y_mean = y.mean()
                slope = np.sum((x.flatten() - x_mean) * (y - y_mean)) / np.sum((x.flatten() - x_mean) ** 2)
                
                # Convert slope to daily degradation rate (6h intervals to daily)
                degradation_rate = abs(slope * 4)  # 4 intervals per day
            else:
                degradation_rate = 0.5  # Default moderate degradation
            
            # Calculate RUL based on degradation rate
            critical_threshold = 20  # Health score below 20% requires immediate maintenance
            
            if degradation_rate > 0.1:
                rul_days = max(1, int((current_health - critical_threshold) / degradation_rate))
            else:
                rul_days = 90  # Stable system - predict 90 days
            
            # Analyze critical factors
            critical_factors = []
            avg_vibration = np.mean(vibrations[-8:]) if len(vibrations) >= 8 else np.mean(vibrations)
            avg_temperature = np.mean(temperatures[-8:]) if len(temperatures) >= 8 else np.mean(temperatures)
            
            if avg_vibration > 75:
                critical_factors.append(f"High vibration ({avg_vibration:.1f})")
            if avg_temperature > 70:
                critical_factors.append(f"Elevated temperature ({avg_temperature:.1f}°C)")
            if degradation_rate > 1.5:
                critical_factors.append(f"Rapid health decline ({degradation_rate:.2f}%/day)")
            
            # Check for accelerating degradation
            if len(health_scores) >= 8:
                recent_rate = abs((health_scores[-1] - health_scores[-4]) / 4)
                earlier_rate = abs((health_scores[-5] - health_scores[-8]) / 4)
                if recent_rate > earlier_rate * 1.5:
                    critical_factors.append("Accelerating degradation detected")
            
            if not critical_factors:
                critical_factors = ["Normal operating conditions"]
            
            # Calculate confidence based on data quality and consistency
            data_points = len(points)
            confidence = min(95, 30 + (data_points * 2))  # More data = higher confidence
            
            # Reduce confidence for erratic health scores
            if len(health_scores) >= 4:
                health_variance = np.std(health_scores)
                if health_variance > 15:
                    confidence -= 20
            
            confidence = max(30, confidence)
            
            # Determine status and recommendation
            if rul_days <= 3:
                status = "CRITICAL"
                urgency = "IMMEDIATE"
                recommendation = "Schedule emergency maintenance within 24 hours"
            elif rul_days <= 7:
                status = "WARNING"
                urgency = "HIGH"
                recommendation = "Schedule maintenance within this week"
            elif rul_days <= 14:
                status = "ATTENTION"
                urgency = "MEDIUM"
                recommendation = "Plan maintenance within 2 weeks"
            elif rul_days <= 30:
                status = "NORMAL"
                urgency = "LOW"
                recommendation = "Schedule routine maintenance next month"
            else:
                status = "HEALTHY"
                urgency = "LOW"
                recommendation = "Continue normal operations and monitoring"
            
            rul_predictions.append({
                "machine_id": mid,
                "rul_days": rul_days,
                "confidence": round(confidence, 1),
                "health_score": round(current_health, 1),
                "degradation_rate": round(degradation_rate, 2),
                "critical_factors": critical_factors,
                "recommendation": recommendation,
                "status": status,
                "urgency": urgency,
                "predicted_failure_date": (datetime.now() + timedelta(days=rul_days)).strftime("%Y-%m-%d"),
                "avg_vibration": round(avg_vibration, 1),
                "avg_temperature": round(avg_temperature, 1)
            })
        
        return rul_predictions
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating RUL: {str(e)}"
        )


@app.get("/api/alerts")
async def get_alerts(limit: int = 20):
    """
    Get recent alerts (anomalies and warnings) with timestamps
    Returns: List of alerts in reverse chronological order
    """
    if not influx_client:
        raise HTTPException(
            status_code=503,
            detail="InfluxDB connection not available"
        )
    
    # Limit to reasonable range
    limit = min(limit, 100)
    
    try:
        # Query for alerts (warnings and anomalies) in last 24h
        query = f'''
            SELECT "vibration", "temperature", "ai_score"
            FROM "{MEASUREMENT}"
            WHERE time > now() - 24h AND "ai_score" < 0.1
            ORDER BY time DESC
            LIMIT {limit}
        '''
        
        result = influx_client.query(query)
        points = list(result.get_points())
        
        if not points:
            return []
        
        # Format alerts for frontend
        alerts = []
        for point in points:
            score = float(point.get('ai_score', 0))
            vibration = float(point.get('vibration', 0))
            temperature = float(point.get('temperature', 0))
            
            # Determine severity
            if score < -0.5:
                severity = "ANOMALY"
                color = "red"
            else:
                severity = "WARNING"
                color = "yellow"
            
            # Create descriptive message
            reasons = []
            if vibration > 75:
                reasons.append(f"High vibration: {vibration:.1f}")
            if temperature > 70:
                reasons.append(f"High temperature: {temperature:.1f}°C")
            if score < -0.5:
                reasons.append(f"Low AI score: {score:.3f}")
            
            message = ", ".join(reasons) if reasons else f"AI score: {score:.3f}"
            
            alerts.append({
                "timestamp": point.get('time'),
                "severity": severity,
                "color": color,
                "message": message,
                "vibration": round(vibration, 2),
                "temperature": round(temperature, 2),
                "score": round(score, 4)
            })
        
        return alerts
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error querying alerts: {str(e)}"
        )


@app.get("/api/work-orders")
async def get_work_orders():
    """
    Get all maintenance work orders with status
    Returns: List of work orders sorted by priority and due date
    """
    # Mock work orders (in production, this would query a database)
    work_orders = [
        {
            "id": "WO-1245",
            "machine_id": "Press_001",
            "title": "High Vibration Alert",
            "description": "Investigate and resolve abnormal vibration levels detected at 10:45 AM",
            "priority": "HIGH",
            "status": "OPEN",
            "assigned_to": "John Smith",
            "created_at": "2025-12-06T10:47:00Z",
            "due_date": "2025-12-08T17:00:00Z",
            "estimated_hours": 4,
            "category": "Emergency Repair"
        },
        {
            "id": "WO-1246",
            "machine_id": "Press_001",
            "title": "Scheduled Preventive Maintenance",
            "description": "Routine inspection and lubrication based on health score prediction",
            "priority": "MEDIUM",
            "status": "IN_PROGRESS",
            "assigned_to": "Mike Johnson",
            "created_at": "2025-12-05T08:00:00Z",
            "due_date": "2025-12-10T12:00:00Z",
            "estimated_hours": 8,
            "category": "Preventive Maintenance"
        },
        {
            "id": "WO-1243",
            "machine_id": "Press_001",
            "title": "Temperature Sensor Calibration",
            "description": "Calibrate temperature sensors as part of quarterly maintenance",
            "priority": "LOW",
            "status": "SCHEDULED",
            "assigned_to": "Sarah Williams",
            "created_at": "2025-12-04T14:30:00Z",
            "due_date": "2025-12-15T16:00:00Z",
            "estimated_hours": 2,
            "category": "Calibration"
        },
        {
            "id": "WO-1240",
            "machine_id": "Press_001",
            "title": "Bearing Replacement",
            "description": "Replaced worn bearings causing vibration anomaly",
            "priority": "HIGH",
            "status": "COMPLETED",
            "assigned_to": "John Smith",
            "created_at": "2025-12-03T09:15:00Z",
            "due_date": "2025-12-03T18:00:00Z",
            "completed_at": "2025-12-03T16:30:00Z",
            "estimated_hours": 6,
            "actual_hours": 5.5,
            "category": "Repair"
        }
    ]
    
    # Sort: HIGH priority first, then by due date
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    work_orders.sort(key=lambda x: (priority_order.get(x["priority"], 3), x.get("due_date", "")))
    
    return work_orders


@app.get("/api/patterns")
async def get_anomaly_patterns():
    """
    Analyze historical data to detect recurring patterns and correlations
    Returns: List of detected patterns with confidence scores
    """
    if not influx_client:
        raise HTTPException(
            status_code=503,
            detail="InfluxDB connection not available"
        )
    
    try:
        # Check if InfluxDB has data
        check_query = f'''
            SELECT COUNT("vibration")
            FROM "{MEASUREMENT}"
            WHERE time > now() - 7d
        '''
        check_result = influx_client.query(check_query)
        check_points = list(check_result.get_points())
        
        if not check_points or check_points[0].get('count', 0) < 10:
            # Not enough data yet, return info pattern
            return [{
                "id": "PATTERN-000",
                "type": "NO_PATTERN",
                "title": "Insufficient Data for Analysis",
                "description": "System is still collecting data. Pattern analysis requires at least 7 days of continuous monitoring.",
                "confidence": 100,
                "occurrences": 0,
                "severity": "INFO",
                "recommendation": "Continue running the system. Check back in a few days for pattern detection results.",
                "detected_at": datetime.utcnow().isoformat() + "Z"
            }]
        
        # Analyze vibration patterns by hour of day
        hour_query = f'''
            SELECT mean("vibration") as avg_vibration, 
                   mean("temperature") as avg_temperature,
                   count("vibration") as count
            FROM "{MEASUREMENT}"
            WHERE time > now() - 7d
            GROUP BY time(1h)
        '''
        
        result = influx_client.query(hour_query)
        points = list(result.get_points())
        
        patterns = []
        
        # Pattern 1: Time-based vibration analysis
        if points and len(points) > 24:
            vibration_values = [float(p['avg_vibration']) for p in points if p.get('avg_vibration') is not None]
            avg_vibration = sum(vibration_values) / len(vibration_values) if vibration_values else 0
            
            # Find peaks (hours with significantly higher vibration)
            high_vibration_hours = []
            for i, point in enumerate(points[-24:]):  # Last 24 hours
                vib_val = point.get('avg_vibration')
                if vib_val is not None:
                    vib = float(vib_val)
                    if vib > avg_vibration * 1.2:  # 20% above average
                        hour = i % 24
                        high_vibration_hours.append(hour)
            
            if high_vibration_hours:
                most_common_hour = max(set(high_vibration_hours), key=high_vibration_hours.count)
                pattern_frequency = high_vibration_hours.count(most_common_hour) / len(points[-24:]) * 100
                
                patterns.append({
                    "id": "PATTERN-001",
                    "type": "TIME_BASED",
                    "title": f"Vibration Spikes During Hour {most_common_hour}:00-{most_common_hour+1}:00",
                    "description": f"Elevated vibration levels detected consistently around {most_common_hour}:00. This may correlate with shift changes, operator behavior, or scheduled production activities.",
                    "confidence": min(85 + pattern_frequency * 0.5, 95),
                    "occurrences": high_vibration_hours.count(most_common_hour),
                    "severity": "MEDIUM",
                    "recommendation": "Review production schedule and operator procedures during this time window. Consider adjusting maintenance windows to avoid peak production hours.",
                    "detected_at": datetime.utcnow().isoformat() + "Z"
                })
        
        # Pattern 2: Temperature correlation with vibration
        if points:
            temp_vib_correlation = []
            for point in points[-50:]:  # Last 50 readings
                temp_val = point.get('avg_temperature')
                vib_val = point.get('avg_vibration')
                if temp_val is not None and vib_val is not None:
                    temp = float(temp_val)
                    vib = float(vib_val)
                    if temp > 70 and vib > 75:
                        temp_vib_correlation.append((temp, vib))
            
            if len(temp_vib_correlation) > 5:
                correlation_strength = len(temp_vib_correlation) / min(50, len(points)) * 100
                
                patterns.append({
                    "id": "PATTERN-002",
                    "type": "CORRELATION",
                    "title": "Temperature-Vibration Correlation Detected",
                    "description": f"High temperature (>70°C) frequently occurs alongside high vibration (>75 units). Found {len(temp_vib_correlation)} co-occurrences in recent data.",
                    "confidence": min(70 + correlation_strength, 92),
                    "occurrences": len(temp_vib_correlation),
                    "severity": "HIGH",
                    "recommendation": "Investigate cooling system efficiency. Consider installing additional cooling or adjusting operating parameters to reduce thermal stress.",
                    "detected_at": datetime.utcnow().isoformat() + "Z"
                })
        
        # Pattern 3: Day-of-week analysis
        weekday_query = f'''
            SELECT mean("vibration") as avg_vibration,
                   count("vibration") as count
            FROM "{MEASUREMENT}"
            WHERE time > now() - 7d
            GROUP BY time(1d)
        '''
        
        weekday_result = influx_client.query(weekday_query)
        weekday_points = list(weekday_result.get_points())
        
        if len(weekday_points) >= 7:
            day_vibrations = [(i % 7, float(p['avg_vibration'])) for i, p in enumerate(weekday_points) if p.get('avg_vibration') is not None]
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            # Find day with highest average vibration
            if day_vibrations and len(day_vibrations) > 0:
                max_day_idx = max(day_vibrations, key=lambda x: x[1])[0]
                max_day_value = max(day_vibrations, key=lambda x: x[1])[1]
                avg_all_days = sum(v for _, v in day_vibrations) / len(day_vibrations)
                
                if max_day_value > avg_all_days * 1.15:  # 15% above average
                    patterns.append({
                        "id": "PATTERN-003",
                        "type": "WEEKLY_CYCLE",
                        "title": f"Elevated Activity on {day_names[max_day_idx]}s",
                        "description": f"Vibration levels on {day_names[max_day_idx]}s average {max_day_value:.1f} units, which is {((max_day_value/avg_all_days - 1) * 100):.1f}% higher than other days.",
                        "confidence": 78,
                        "occurrences": len([d for d, _ in day_vibrations if d == max_day_idx]),
                        "severity": "LOW",
                        "recommendation": f"Review {day_names[max_day_idx]} production schedules. This pattern may indicate higher workload or different operational procedures on this day.",
                        "detected_at": datetime.utcnow().isoformat() + "Z"
                    })
        
        # If no patterns detected, return helpful message
        if not patterns:
            patterns.append({
                "id": "PATTERN-000",
                "type": "NO_PATTERN",
                "title": "No Significant Patterns Detected",
                "description": "Analysis of the last 7 days shows consistent operation without recurring anomaly patterns. This indicates stable machine performance.",
                "confidence": 95,
                "occurrences": 0,
                "severity": "INFO",
                "recommendation": "Continue monitoring. Patterns typically emerge over longer time periods (2-4 weeks).",
                "detected_at": datetime.utcnow().isoformat() + "Z"
            })
        
        return patterns
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing patterns: {str(e)}"
        )


# ==========================================
# HEALTH & AI ADMIN ENDPOINTS
# ==========================================

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "service": "ai-engine"}


@app.get("/model-info")
async def get_model_info():
    """Get information about the trained model and uploaded data"""
    try:
        model_exists = os.path.exists(MODEL_PATH)
        data_path = "/app/data/training_data.csv"
        column_mapping_path = "/app/data/column_mapping.json"
        
        # Get uploaded data info
        data_info = {}
        if os.path.exists(column_mapping_path):
            with open(column_mapping_path, 'r') as f:
                data_info = json.load(f)
        
        if not model_exists:
            return {
                "exists": False,
                "is_trained": False,
                "type": None,
                "n_estimators": None,
                "contamination": None,
                "last_trained": None,
                "sample_count": data_info.get('total_rows', 0),
                "features": data_info.get('original_columns', []),
                "feature_count": data_info.get('feature_count', 0),
                "uploaded_file": data_info.get('filename', None)
            }
        
        # Load model to get parameters
        with open(MODEL_PATH, 'rb') as f:
            model_data = pickle.load(f)
        
        # Handle both old and new model formats
        if isinstance(model_data, dict):
            model = model_data.get('model')
            columns = model_data.get('columns', [])
            trained_at = model_data.get('trained_at')
        else:
            # Old format (just the model)
            model = model_data
            columns = []
            trained_at = datetime.fromtimestamp(os.path.getmtime(MODEL_PATH)).isoformat()
        
        # Get model parameters
        params = {
            "exists": True,
            "is_trained": True,
            "type": type(model).__name__,
            "n_estimators": getattr(model, 'n_estimators', None),
            "contamination": getattr(model, 'contamination', None),
            "last_trained": trained_at,
            "sample_count": data_info.get('total_rows', 0),
            "features": columns or data_info.get('original_columns', []),
            "feature_count": len(columns) or data_info.get('feature_count', 0),
            "uploaded_file": data_info.get('filename', None)
        }
        
        return params
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading model info: {str(e)}")


@app.post("/train")
async def train_model(request: TrainRequest):
    """Train or retrain the anomaly detection model with uploaded data"""
    try:
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        import pandas as pd
        import numpy as np
        
        # Check for uploaded training data
        data_path = "/app/data/training_data.csv"
        column_mapping_path = "/app/data/column_mapping.json"
        
        if not os.path.exists(data_path):
            raise HTTPException(
                status_code=400,
                detail="No training data found. Please upload a dataset first using the Dataset Upload feature."
            )
        
        # Load uploaded data
        df = pd.read_csv(data_path)
        
        if len(df) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient training data. Need at least 100 samples, got {len(df)}"
            )
        
        # Load column info
        column_info = {}
        if os.path.exists(column_mapping_path):
            with open(column_mapping_path, 'r') as f:
                column_info = json.load(f)
        
        # Prepare features (all numeric columns)
        X = df.values
        
        # Normalize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train model
        model = IsolationForest(
            n_estimators=request.n_estimators,
            contamination=request.contamination,
            random_state=request.random_state,
            n_jobs=-1
        )
        
        model.fit(X_scaled)
        
        # Save model and scaler
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        
        model_data = {
            'model': model,
            'scaler': scaler,
            'columns': df.columns.tolist(),
            'feature_count': len(df.columns),
            'trained_at': datetime.utcnow().isoformat()
        }
        
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(model_data, f)
        
        return {
            "message": "Model trained successfully",
            "samples_used": len(df),
            "features": df.columns.tolist(),
            "feature_count": len(df.columns),
            "n_estimators": request.n_estimators,
            "contamination": request.contamination,
            "model_path": MODEL_PATH,
            "source_file": column_info.get('filename', 'unknown')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@app.post("/reset-model")
async def reset_model():
    """Delete the trained model"""
    try:
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
            return {"message": "Model deleted successfully"}
        else:
            return {"message": "No model found to delete"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting model: {str(e)}")


@app.post("/upload-dataset")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload CSV/Excel dataset - auto-detects columns and file format"""
    try:
        import pandas as pd
        
        print(f"📥 Upload request received: {file.filename}, content_type: {file.content_type}")
        
        # Validate file type
        allowed_extensions = ['.csv', '.xls', '.xlsx']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        print(f"🔍 Detected file extension: {file_ext}")
        
        if file_ext not in allowed_extensions:
            error_msg = f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
            print(f"❌ {error_msg}")
            raise HTTPException(
                status_code=400, 
                detail=error_msg
            )
        
        # Read file content
        contents = await file.read()
        print(f"📦 File size: {len(contents)} bytes")
        
        # Load data based on file type
        try:
            if file_ext == '.csv':
                # Try to auto-detect delimiter (comma or semicolon)
                df = pd.read_csv(io.BytesIO(contents), sep=None, engine='python')
            elif file_ext in ['.xls', '.xlsx']:
                df = pd.read_excel(io.BytesIO(contents))
            print(f"✅ Parsed {len(df)} rows, {len(df.columns)} columns: {df.columns.tolist()}")
        except Exception as e:
            error_msg = f"Failed to parse file: {str(e)}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="File contains no data")
        
        # Auto-detect numeric columns (features)
        numeric_cols = df.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()
        
        if not numeric_cols:
            raise HTTPException(
                status_code=400, 
                detail="No numeric columns found. File must contain at least one numeric column."
            )
        
        # Handle missing values
        df_clean = df[numeric_cols].fillna(df[numeric_cols].mean())
        
        # Store column mapping for later use
        column_mapping_path = "/app/data/column_mapping.json"
        os.makedirs(os.path.dirname(column_mapping_path), exist_ok=True)
        
        column_info = {
            "original_columns": numeric_cols,
            "feature_count": len(numeric_cols),
            "uploaded_at": datetime.utcnow().isoformat(),
            "filename": file.filename,
            "total_rows": len(df_clean)
        }
        
        with open(column_mapping_path, 'w') as f:
            json.dump(column_info, f, indent=2)
        
        # Save processed data for training
        data_path = "/app/data/training_data.csv"
        df_clean.to_csv(data_path, index=False)
        
        # Also insert into InfluxDB for visualization
        points = []
        for idx, row in df_clean.iterrows():
            fields = {col: float(row[col]) for col in numeric_cols}
            
            point = {
                "measurement": MEASUREMENT,
                "tags": {
                    "source": "uploaded_dataset",
                    "filename": file.filename
                },
                "time": datetime.utcnow().isoformat(),
                "fields": fields
            }
            points.append(point)
        
        if influx_client and points:
            try:
                influx_client.write_points(points[:1000])  # Limit to first 1000 points for visualization
            except Exception as e:
                print(f"Warning: Could not write to InfluxDB: {e}")
        
        return {
            "message": "Dataset uploaded and processed successfully",
            "filename": file.filename,
            "total_rows": len(df_clean),
            "numeric_columns": numeric_cols,
            "feature_count": len(numeric_cols),
            "ready_for_training": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ============================================================================
# COMBINED PREDICTION ENDPOINT - Real-time Anomaly + Future Failure
# ============================================================================

class PredictionRequest(BaseModel):
    """Request model for combined prediction"""
    data: Dict[str, float]  # Current sensor readings
    equipmentId: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "Humidity": 65.0,
                    "Temperature": 45.0,
                    "Age": 12.0,
                    "Quantity": 42000.0
                }
            }
        }


@app.post("/predict")
async def predict_combined(request: PredictionRequest):
    """
    Combined prediction endpoint that provides:
    1. Real-time anomaly detection (Is it anomalous NOW?)
    2. Future failure prediction (WHEN will it fail?)
    
    Returns comprehensive analysis with risk assessment
    """
    try:
        input_data = request.data
        equipment_id = request.equipmentId
        
        # =====================================================================
        # Part 1: Real-time Anomaly Detection (Isolation Forest)
        # =====================================================================
        anomaly_result = {
            "is_anomaly": False,
            "anomaly_score": 0,
            "status": "UNKNOWN",
            "model_loaded": False
        }
        
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, 'rb') as f:
                    model_data = pickle.load(f)
                
                # Handle both old and new model formats
                if isinstance(model_data, dict):
                    model = model_data.get('model')
                    scaler = model_data.get('scaler')
                    expected_features = model_data.get('columns', [])
                else:
                    model = model_data
                    scaler = None
                    expected_features = list(input_data.keys())
                
                # Prepare input for anomaly detection
                input_df = np.array([[input_data.get(feat, 0) for feat in expected_features]])
                
                if scaler:
                    input_scaled = scaler.transform(input_df)
                else:
                    input_scaled = input_df
                
                # Predict anomaly (-1 = anomaly, 1 = normal)
                prediction = model.predict(input_scaled)[0]
                anomaly_score_raw = model.score_samples(input_scaled)[0]
                
                # Convert to 0-100 scale (lower = more anomalous)
                anomaly_score = max(0, min(100, int((anomaly_score_raw + 0.5) * 100)))
                
                # Calculate heuristic score for better interpretation
                heuristic_score = 0
                warnings = []
                
                # Temperature checks
                temp = input_data.get('Temperature', 0)
                if temp > 80:
                    heuristic_score += 30
                    warnings.append("🔴 Critical temperature detected")
                elif temp > 70:
                    heuristic_score += 15
                    warnings.append("🟡 High temperature warning")
                
                # Humidity checks
                humidity = input_data.get('Humidity', 0)
                if humidity > 85:
                    heuristic_score += 25
                    warnings.append("🔴 Extreme humidity levels")
                elif humidity > 75:
                    heuristic_score += 10
                    warnings.append("🟡 High humidity detected")
                
                # Age checks
                age = input_data.get('Age', 0)
                if age > 20:
                    heuristic_score += 20
                    warnings.append("⚠️ Equipment very old")
                elif age > 15:
                    heuristic_score += 10
                    warnings.append("⚠️ Equipment aging")
                
                # MTTF checks (if available)
                mttf = input_data.get('MTTF', input_data.get('MTTF ', 0))
                if mttf > 0:
                    if mttf < 100:
                        heuristic_score += 35
                        warnings.append("🔴 Critical MTTF - Failure imminent")
                    elif mttf < 300:
                        heuristic_score += 20
                        warnings.append("🟡 Low MTTF - Maintenance needed")
                    elif mttf < 500:
                        heuristic_score += 5
                        warnings.append("ℹ️ MTTF below average")
                
                # Determine status
                if heuristic_score >= 60 or prediction == -1:
                    status = "ANOMALY"
                    risk_level = "CRITICAL"
                    status_emoji = "🔴"
                elif heuristic_score >= 30:
                    status = "WARNING"
                    risk_level = "MEDIUM"
                    status_emoji = "🟡"
                else:
                    status = "NORMAL"
                    risk_level = "LOW"
                    status_emoji = "✅"
                
                anomaly_result = {
                    "is_anomaly": (status == "ANOMALY"),
                    "status": status,
                    "status_emoji": status_emoji,
                    "risk_level": risk_level,
                    "anomaly_score": heuristic_score,
                    "model_score": anomaly_score,
                    "warnings": warnings,
                    "model_loaded": True
                }
                
            except Exception as e:
                print(f"Anomaly detection error: {e}")
                anomaly_result["error"] = str(e)
        
        # =====================================================================
        # Part 2: Future Failure Prediction (Random Forest Regressor)
        # =====================================================================
        prediction_result = {
            "predicted_mttf": None,
            "estimated_days_until_failure": None,
            "future_risk_level": "UNKNOWN",
            "recommended_action": "Model not available",
            "model_loaded": False
        }
        
        if os.path.exists(PREDICTIVE_MODEL_PATH):
            try:
                with open(PREDICTIVE_MODEL_PATH, 'rb') as f:
                    pred_model_data = pickle.load(f)
                
                pred_model = pred_model_data['model']
                pred_scaler = pred_model_data['scaler']
                pred_features = pred_model_data['features']
                
                # Prepare input for prediction
                pred_input = np.array([[input_data.get(feat, 0) for feat in pred_features]])
                pred_input_scaled = pred_scaler.transform(pred_input)
                
                # Predict MTTF
                predicted_mttf = pred_model.predict(pred_input_scaled)[0]
                # Apply slight per-equipment adjustment to simulate scoping
                if equipment_id:
                    if str(equipment_id).endswith("001"):
                        predicted_mttf = predicted_mttf * 0.95
                    elif str(equipment_id).endswith("014"):
                        predicted_mttf = predicted_mttf * 1.05
                days_estimate = predicted_mttf / 24  # Convert hours to days
                
                # Risk assessment based on predicted MTTF
                if predicted_mttf < 100:
                    future_risk = "CRITICAL"
                    future_emoji = "🔴"
                    action = "IMMEDIATE MAINTENANCE REQUIRED - Equipment likely to fail within days"
                    confidence = "High"
                elif predicted_mttf < 300:
                    future_risk = "HIGH"
                    future_emoji = "🟠"
                    action = "Schedule maintenance within 1-2 weeks"
                    confidence = "High"
                elif predicted_mttf < 500:
                    future_risk = "MEDIUM"
                    future_emoji = "🟡"
                    action = "Monitor closely, plan maintenance within next month"
                    confidence = "Medium"
                else:
                    future_risk = "LOW"
                    future_emoji = "🟢"
                    action = "Continue normal operation, routine maintenance sufficient"
                    confidence = "Medium"
                
                # Get feature importance for explanation
                feature_importance = {
                    feat: float(imp) 
                    for feat, imp in zip(pred_features, pred_model.feature_importances_)
                }
                
                # Find most critical factor
                most_critical_factor = max(
                    [(feat, input_data.get(feat, 0), imp) for feat, imp in feature_importance.items()],
                    key=lambda x: x[2]
                )
                
                prediction_result = {
                    "predicted_mttf": round(predicted_mttf, 2),
                    "estimated_days_until_failure": round(days_estimate, 1),
                    "future_risk_level": future_risk,
                    "future_risk_emoji": future_emoji,
                    "recommended_action": action,
                    "confidence": confidence,
                    "feature_importance": feature_importance,
                    "most_critical_factor": {
                        "name": most_critical_factor[0],
                        "value": most_critical_factor[1],
                        "importance": round(most_critical_factor[2] * 100, 1)
                    },
                    "model_loaded": True
                }
                
            except Exception as e:
                print(f"Predictive model error: {e}")
                prediction_result["error"] = str(e)
        
        # =====================================================================
        # Part 3: Combined Risk Assessment
        # =====================================================================
        
        # Overall risk is highest of current + future
        risk_levels = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3, "UNKNOWN": -1}
        current_risk_val = risk_levels.get(anomaly_result.get("risk_level", "UNKNOWN"), -1)
        future_risk_val = risk_levels.get(prediction_result.get("future_risk_level", "UNKNOWN"), -1)
        
        overall_risk_val = max(current_risk_val, future_risk_val)
        overall_risk = [k for k, v in risk_levels.items() if v == overall_risk_val][0] if overall_risk_val >= 0 else "UNKNOWN"
        
        # Generate comprehensive recommendation
        if overall_risk == "CRITICAL":
            overall_action = "⚠️ URGENT: Both current conditions and future predictions indicate critical risk. Shut down equipment and perform immediate inspection."
        elif overall_risk == "HIGH":
            overall_action = "⚠️ HIGH PRIORITY: Schedule maintenance within 24-48 hours to prevent potential failure."
        elif overall_risk == "MEDIUM":
            overall_action = "⚠️ ATTENTION: Monitor closely and schedule maintenance within 1-2 weeks."
        else:
            overall_action = "✅ Equipment operating normally. Continue routine monitoring and maintenance schedule."
        
        # Return combined results
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_data": input_data,
            
            # Current state analysis
            "current_state": {
                **anomaly_result,
                "description": "Real-time anomaly detection using Isolation Forest"
            },
            
            # Future prediction
            "future_prediction": {
                **prediction_result,
                "description": "Time-to-failure prediction using Random Forest Regressor"
            },
            
            # Overall assessment
            "overall_assessment": {
                "risk_level": overall_risk,
                "recommendation": overall_action,
                "analysis": f"Current: {anomaly_result.get('status', 'UNKNOWN')}, Future: {prediction_result.get('future_risk_level', 'UNKNOWN')}"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/models/status")
async def get_models_status():
    """Check which models are available"""
    status = {
        "anomaly_detection_model": {
            "available": os.path.exists(MODEL_PATH),
            "path": MODEL_PATH,
            "type": "Isolation Forest",
            "purpose": "Real-time anomaly detection"
        },
        "predictive_model": {
            "available": os.path.exists(PREDICTIVE_MODEL_PATH),
            "path": PREDICTIVE_MODEL_PATH,
            "type": "Random Forest Regressor",
            "purpose": "Future failure prediction"
        },
        "enhanced_ml_available": ENHANCED_ML_AVAILABLE
    }
    
    # Add registry info if available
    if ENHANCED_ML_AVAILABLE:
        try:
            registry = get_registry()
            status["model_registry"] = registry.get_registry_summary()
        except Exception as e:
            status["model_registry"] = {"error": str(e)}
    
    return status


# =============================================================================
# MODEL REGISTRY API ENDPOINTS
# =============================================================================

@app.get("/api/models/registry")
async def get_model_registry():
    """Get summary of all registered models"""
    if not ENHANCED_ML_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced ML modules not available")
    
    try:
        registry = get_registry()
        return {
            "success": True,
            "registry": registry.get_registry_summary()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/{model_type}/versions")
async def list_model_versions(model_type: str):
    """List all versions for a model type"""
    if not ENHANCED_ML_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced ML modules not available")
    
    try:
        mt = ModelType(model_type)
        registry = get_registry()
        versions = registry.list_versions(mt)
        return {
            "success": True,
            "model_type": model_type,
            "versions": versions
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid model type: {model_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/{model_type}/promote/{version}")
async def promote_model_version(model_type: str, version: str):
    """Promote a model version to ACTIVE status"""
    if not ENHANCED_ML_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced ML modules not available")
    
    try:
        mt = ModelType(model_type)
        registry = get_registry()
        success = registry.promote_model(mt, version)
        
        if success:
            return {
                "success": True,
                "message": f"Model {model_type} v{version} promoted to ACTIVE"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Version {version} not found")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid model type: {model_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/{model_type}/rollback")
async def rollback_model(model_type: str, to_version: Optional[str] = None):
    """Rollback to a previous model version"""
    if not ENHANCED_ML_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced ML modules not available")
    
    try:
        mt = ModelType(model_type)
        registry = get_registry()
        success = registry.rollback(mt, to_version)
        
        if success:
            return {
                "success": True,
                "message": f"Rolled back {model_type} to {'previous version' if not to_version else f'v{to_version}'}"
            }
        else:
            raise HTTPException(status_code=404, detail="No version to rollback to")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid model type: {model_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ABTestConfig(BaseModel):
    allocations: Dict[str, float]  # version -> traffic percentage


@app.post("/api/models/{model_type}/ab-test")
async def configure_ab_test(model_type: str, config: ABTestConfig):
    """Configure A/B test traffic allocation"""
    if not ENHANCED_ML_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced ML modules not available")
    
    try:
        mt = ModelType(model_type)
        registry = get_registry()
        success = registry.set_ab_traffic(mt, config.allocations)
        
        return {
            "success": success,
            "message": f"A/B test configured for {model_type}",
            "allocations": config.allocations
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/train")
async def trigger_training(
    model_type: Optional[str] = "all",
    contamination: Optional[float] = 0.05
):
    """Trigger model training (runs in background)"""
    if not ENHANCED_ML_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced ML modules not available")
    
    try:
        import subprocess
        import threading
        
        def run_training():
            try:
                subprocess.run(
                    ["python", "-m", "src.train_enhanced"],
                    cwd="/app",
                    capture_output=True,
                    timeout=300  # 5 minute timeout
                )
            except Exception as e:
                print(f"Training failed: {e}")
        
        # Run in background thread
        thread = threading.Thread(target=run_training, daemon=True)
        thread.start()
        
        return {
            "success": True,
            "message": "Training started in background",
            "note": "Check /models/status for completion"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/{model_type}/metrics")
async def get_model_metrics(model_type: str, version: Optional[str] = None):
    """Get performance metrics for a model"""
    if not ENHANCED_ML_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced ML modules not available")
    
    try:
        mt = ModelType(model_type)
        registry = get_registry()
        
        if version:
            result = registry.get_model_by_version(mt, version)
        else:
            result = registry.get_active_model(mt)
        
        if not result:
            raise HTTPException(status_code=404, detail="Model not found")
        
        _, _, model_version = result
        
        return {
            "success": True,
            "model_type": model_type,
            "version": model_version.version,
            "status": model_version.status.value,
            "algorithm": model_version.algorithm,
            "features": model_version.features,
            "metrics": model_version.metrics.to_dict(),
            "created_at": model_version.created_at,
            "hyperparameters": model_version.hyperparameters
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid model type: {model_type}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENHANCED PREDICTION ENDPOINT
# =============================================================================

@app.post("/api/predict/enhanced")
async def predict_enhanced(request: PredictionRequest):
    """
    Enhanced prediction using ensemble anomaly detection.
    
    Returns detailed results from multiple algorithms with voting.
    """
    if not ENHANCED_ML_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced ML modules not available")
    
    try:
        input_data = request.data
        equipment_id = request.equipmentId
        
        # Try to load ensemble detector
        ensemble_path = "/app/models/ensemble_anomaly_detector.pkl"
        
        if not os.path.exists(ensemble_path):
            raise HTTPException(
                status_code=503, 
                detail="Ensemble model not trained. Run /api/models/train first."
            )
        
        detector = EnsembleAnomalyDetector.load(ensemble_path)
        
        # Prepare input
        features = detector.feature_names
        X = np.array([[input_data.get(f, 0) for f in features]])
        
        # Get prediction
        prediction = detector.predict(X)
        
        return {
            "success": True,
            "equipment_id": equipment_id,
            "input_data": input_data,
            "prediction": {
                "is_anomaly": prediction.is_anomaly,
                "anomaly_score": prediction.anomaly_score,
                "confidence": prediction.confidence,
                "risk_level": prediction.risk_level,
                "algorithm_votes": prediction.algorithm_votes,
                "contributing_factors": prediction.contributing_factors
            },
            "ensemble_info": {
                "algorithms": list(prediction.algorithm_votes.keys()),
                "voting_threshold": detector.voting_threshold,
                "weights": detector.weights
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced prediction failed: {str(e)}")


# =====================================================================
# ESP32 Motor Telemetry + Control (MVP)
# ESP posts a reading, we store it in InfluxDB and return a motor command.
# Dashboard polls /api/esp/status and can push a manual override.
# =====================================================================

ESP_MEASUREMENT = "esp_motor"
ESP_TEMP_WARN = float(os.getenv("ESP_TEMP_WARN", "70"))
ESP_TEMP_CRITICAL = float(os.getenv("ESP_TEMP_CRITICAL", "85"))
ESP_TEMP_FAILURE = float(os.getenv("ESP_TEMP_FAILURE", "110"))
ESP_VIB_WARN = float(os.getenv("ESP_VIB_WARN", "60"))

_esp_override: Optional[Dict[str, Any]] = None
_esp_last: Dict[str, Any] = {}


class ESPReading(BaseModel):
    temperature: Optional[float] = None       # DHT22 ambient
    humidity: Optional[float] = None
    thermocouple: Optional[float] = None      # MAX6675 motor surface
    vibration: Optional[float] = None         # optional accel magnitude
    device_id: Optional[str] = "esp32_motor_1"


class ESPCommand(BaseModel):
    action: str = "auto"                      # stop | slow | normal | auto
    speed_percent: Optional[int] = None


def _esp_decide(reading: Dict[str, Any]) -> Dict[str, Any]:
    """Manual override wins; otherwise threshold logic on thermocouple/vibration."""
    if _esp_override and _esp_override.get("action") != "auto":
        return {**_esp_override, "source": "override"}

    thermo = reading.get("thermocouple")
    vib = reading.get("vibration")

    if thermo is not None and thermo >= ESP_TEMP_CRITICAL:
        return {"action": "stop", "speed_percent": 0,
                "reason": f"thermocouple {thermo:.1f}C >= critical {ESP_TEMP_CRITICAL}C",
                "source": "auto"}
    if vib is not None and vib >= ESP_VIB_WARN * 1.5:
        return {"action": "stop", "speed_percent": 0,
                "reason": f"vibration {vib:.1f} too high",
                "source": "auto"}
    if thermo is not None and thermo >= ESP_TEMP_WARN:
        return {"action": "slow", "speed_percent": 40,
                "reason": f"thermocouple {thermo:.1f}C >= warn {ESP_TEMP_WARN}C",
                "source": "auto"}
    if vib is not None and vib >= ESP_VIB_WARN:
        return {"action": "slow", "speed_percent": 50,
                "reason": f"vibration {vib:.1f} elevated",
                "source": "auto"}
    return {"action": "normal", "speed_percent": 100,
            "reason": "all sensors within limits",
            "source": "auto"}


def _ema(values: np.ndarray, alpha: float = 0.3) -> np.ndarray:
    """Exponential moving average — smooths sensor noise (MAX6675 has ~0.5C jitter)."""
    out = np.empty_like(values, dtype=float)
    out[0] = float(values[0])
    for i in range(1, len(values)):
        out[i] = alpha * float(values[i]) + (1.0 - alpha) * out[i - 1]
    return out


def _r2(actual: np.ndarray, predicted: np.ndarray) -> float:
    ss_res = float(np.sum((actual - predicted) ** 2))
    ss_tot = float(np.sum((actual - float(np.mean(actual))) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


def _thermal_linear(times_sec: np.ndarray, temps: np.ndarray, t_failure: float) -> Dict[str, Any]:
    """Linear fallback when exponential fit fails or insufficient data."""
    if len(temps) < 3:
        return {"model": "linear", "minutes": None, "slope_c_per_min": 0.0, "r_squared": 0.0}
    slope, intercept = np.polyfit(times_sec, temps, 1)
    slope_per_min = float(slope) * 60.0
    r2 = _r2(temps, slope * times_sec + intercept)
    current = float(temps[-1])
    if slope_per_min <= 0.01:
        return {"model": "linear", "minutes": None,
                "slope_c_per_min": round(slope_per_min, 3),
                "r_squared": round(r2, 3)}
    minutes = max(0.0, (t_failure - current) / slope_per_min)
    return {"model": "linear", "minutes": round(minutes, 1),
            "slope_c_per_min": round(slope_per_min, 3),
            "r_squared": round(r2, 3)}


def _thermal_mttf(times_sec: np.ndarray, temps: np.ndarray, t_failure: float) -> Dict[str, Any]:
    """Fit T(t) = T_inf - (T_inf - T_0) * exp(-t/tau) — physics of motor heating.
    If T_inf < t_failure, the motor is asymptoting safely (will never overheat at this load).
    Falls back to linear if the fit is bad or convergence fails.
    """
    if len(temps) < 5:
        return _thermal_linear(times_sec, temps, t_failure)
    try:
        from scipy.optimize import curve_fit

        def model(t, T_inf, T_0, tau):
            return T_inf - (T_inf - T_0) * np.exp(-t / tau)

        popt, _ = curve_fit(
            model, times_sec, temps,
            p0=[float(np.max(temps)) + 10.0, float(temps[0]), 600.0],
            bounds=([float(temps[-1]) - 1.0, -50.0, 1.0], [500.0, 250.0, 1e5]),
            maxfev=2000,
        )
        T_inf, T_0, tau = float(popt[0]), float(popt[1]), float(popt[2])
        r2 = _r2(temps, model(times_sec, *popt))

        # Reject if the fit is poor or tau is degenerate — fall back to linear
        if r2 < 0.5 or tau < 10.0 or tau > 1e5:
            return _thermal_linear(times_sec, temps, t_failure)

        result: Dict[str, Any] = {
            "model": "exponential",
            "asymptote_c": round(T_inf, 2),
            "tau_min": round(tau / 60.0, 2),
            "r_squared": round(r2, 3),
        }
        if T_inf < t_failure:
            # Will stabilize below the failure threshold — no overheating risk at this load
            result["minutes"] = None
            result["status_hint"] = "stabilizing"
            return result

        ratio = (T_inf - t_failure) / (T_inf - T_0)
        if ratio <= 0:
            result["minutes"] = 0.0
            return result
        t_fail_sec = -tau * float(np.log(ratio))
        minutes_left = max(0.0, (t_fail_sec - float(times_sec[-1])) / 60.0)
        result["minutes"] = round(minutes_left, 1)
        return result
    except Exception:
        return _thermal_linear(times_sec, temps, t_failure)


def _vibration_mttf(times_sec: np.ndarray, vibs: np.ndarray, v_failure: float) -> Dict[str, Any]:
    """Linear trend on smoothed vibration. Vibration doesn't have a clear asymptote
    like temperature, so a linear extrapolation is fine for MVP."""
    if len(vibs) < 3:
        return {"minutes": None, "slope_per_min": 0.0, "r_squared": 0.0}
    slope, intercept = np.polyfit(times_sec, vibs, 1)
    slope_per_min = float(slope) * 60.0
    r2 = _r2(vibs, slope * times_sec + intercept)
    current = float(vibs[-1])
    if slope_per_min <= 0.01:
        return {"minutes": None, "slope_per_min": round(slope_per_min, 3),
                "r_squared": round(r2, 3)}
    minutes = max(0.0, (v_failure - current) / slope_per_min)
    return {"minutes": round(minutes, 1), "slope_per_min": round(slope_per_min, 3),
            "r_squared": round(r2, 3)}


def _esp_mttf() -> Dict[str, Any]:
    """Combined MTTF over a 30-min window:
      - EMA-smooth both signals to suppress sensor noise
      - Fit exponential thermal model (real motor physics) → fallback to linear
      - Linear vibration trend
      - Report the worst (lowest) MTTF as the headline; both available in detail
    """
    if not influx_client:
        return {"status": "unavailable", "minutes": None}
    try:
        query = (f'SELECT "thermocouple","vibration" FROM "{ESP_MEASUREMENT}" '
                 f'WHERE time > now() - 30m')
        all_pts = list(influx_client.query(query).get_points())
        thermo_pts = [p for p in all_pts if p.get("thermocouple") is not None]
        vib_pts = [p for p in all_pts if p.get("vibration") is not None]

        if len(thermo_pts) < 3:
            return {"status": "insufficient_data", "minutes": None,
                    "samples": len(thermo_pts), "window_minutes": 30}

        def _series(points, key):
            ts = np.array([datetime.fromisoformat(p["time"].replace("Z", "+00:00")).timestamp()
                           for p in points])
            ys = np.array([float(p[key]) for p in points])
            return ts - ts[0], ys

        t_thermal, raw_thermo = _series(thermo_pts, "thermocouple")
        thermal = _thermal_mttf(t_thermal, _ema(raw_thermo), ESP_TEMP_FAILURE)
        thermal["current_c"] = round(float(raw_thermo[-1]), 2)

        vibration: Optional[Dict[str, Any]] = None
        if len(vib_pts) >= 3:
            t_vib, raw_vib = _series(vib_pts, "vibration")
            v_failure = ESP_VIB_WARN * 1.5
            vibration = _vibration_mttf(t_vib, _ema(raw_vib), v_failure)
            vibration["current"] = round(float(raw_vib[-1]), 2)

        candidates = []
        if thermal.get("minutes") is not None:
            candidates.append(("thermal", float(thermal["minutes"])))
        if vibration and vibration.get("minutes") is not None:
            candidates.append(("vibration", float(vibration["minutes"])))

        if not candidates:
            status = "nominal"
            minutes: Optional[float] = None
            dominant: Optional[str] = None
        else:
            dominant, minutes = min(candidates, key=lambda x: x[1])
            if minutes <= 0:
                status = "failed"
            elif minutes < 10:
                status = "critical"
            elif minutes < 60:
                status = "warning"
            else:
                status = "nominal"

        return {
            "status": status,
            "minutes": minutes,
            "dominant_signal": dominant,
            "current_c": thermal.get("current_c"),
            "thermal": thermal,
            "vibration": vibration,
            "samples": len(thermo_pts),
            "vibration_samples": len(vib_pts),
            "window_minutes": 30,
        }
    except Exception as e:
        return {"status": "error", "minutes": None, "error": str(e)}


@app.post("/api/esp/ingest")
async def esp_ingest(reading: ESPReading):
    """ESP32 posts sensor reading → stored in InfluxDB → motor command returned."""
    global _esp_last
    payload = reading.model_dump()
    now = datetime.utcnow()

    if influx_client:
        try:
            fields = {k: float(payload[k]) for k in ("temperature", "humidity", "thermocouple", "vibration")
                      if payload.get(k) is not None}
            if fields:
                influx_client.write_points([{
                    "measurement": ESP_MEASUREMENT,
                    "tags": {"device_id": payload.get("device_id") or "esp32_motor_1"},
                    "time": now.isoformat() + "Z",
                    "fields": fields,
                }])
        except Exception as e:
            print(f"⚠️  ESP ingest InfluxDB write failed: {e}")

    command = _esp_decide(payload)
    _esp_last = {**payload, "timestamp": now.isoformat() + "Z", "command": command}
    return command


@app.get("/api/esp/status")
async def esp_status():
    """Dashboard poll: latest reading + current command + MTTF estimate."""
    return {
        "reading": _esp_last or None,
        "override": _esp_override,
        "mttf": _esp_mttf(),
        "thresholds": {
            "temp_warn": ESP_TEMP_WARN,
            "temp_critical": ESP_TEMP_CRITICAL,
            "temp_failure": ESP_TEMP_FAILURE,
            "vib_warn": ESP_VIB_WARN,
        },
    }


@app.post("/api/esp/command")
async def esp_set_command(cmd: ESPCommand):
    """Manual override from dashboard. action=auto clears the override."""
    global _esp_override
    action = (cmd.action or "auto").lower()
    if action == "auto":
        _esp_override = None
        return {"override": None}
    if action not in {"stop", "slow", "normal"}:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
    speed = cmd.speed_percent
    if speed is None:
        speed = {"stop": 0, "slow": 40, "normal": 100}[action]
    _esp_override = {
        "action": action,
        "speed_percent": int(max(0, min(100, speed))),
        "reason": "manual override from dashboard",
    }
    return {"override": _esp_override}


@app.get("/api/esp/history")
async def esp_history(minutes: int = 30):
    """Recent ESP readings for dashboard chart."""
    if not influx_client:
        raise HTTPException(status_code=503, detail="InfluxDB unavailable")
    minutes = max(1, min(1440, minutes))
    try:
        query = (f'SELECT "temperature","humidity","thermocouple","vibration" '
                 f'FROM "{ESP_MEASUREMENT}" WHERE time > now() - {minutes}m')
        pts = list(influx_client.query(query).get_points())
        return {"points": pts, "count": len(pts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Starting FastAPI Server")
    print("=" * 70)
    print(f"API Documentation: http://localhost:8000/docs")
    print(f"Alternative Docs: http://localhost:8000/redoc")
    print(f"CORS Enabled for: http://localhost:3000")
    print("=" * 70)
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
