"""
CareAgent OS — API Routes
Provides REST endpoints for all agent operations + WebSocket for real-time activity feed.
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from pydantic import BaseModel, Field

from app.agents.orchestrator import orchestrator
from app.services.llm_router import llm_router


router = APIRouter()


# ──────────────────────────────── Schemas ────────────────────────────────

class PatientIntakeRequest(BaseModel):
    message: str = ""
    patient_name: str = "Patient"
    symptoms: str = ""
    patient_age: int = 35
    patient_gender: str = "unknown"
    phone: str = ""

class ConversationContinue(BaseModel):
    conversation_id: str
    message: str

class TriageRequest(BaseModel):
    patient_id: str = ""
    symptoms: str
    vital_signs: Dict[str, Any] = {}
    patient_age: int = 35
    patient_gender: str = "unknown"
    pain_level: int = 0
    medical_history: List[str] = []

class PriorAuthRequest(BaseModel):
    patient_id: str = ""
    procedure: str = ""
    medication: str = ""
    insurance_provider: str = "BlueCross BlueShield"
    diagnosis: str = ""
    clinical_notes: str = ""
    medical_history: List[str] = []

class ClinicalDocRequest(BaseModel):
    patient_id: str = ""
    symptoms: str = ""
    vital_signs: Dict[str, Any] = {}
    patient_age: int = 35
    patient_gender: str = "unknown"
    exam_findings: str = ""
    visit_transcript: str = ""
    medical_history: List[str] = []
    medications: List[str] = []
    allergies: List[str] = []

class PatientFollowupRequest(BaseModel):
    patient_id: str = ""
    patient_name: str = "Patient"
    diagnosis: str = ""
    medications: List[Dict] = []
    follow_up_plan: str = ""
    days_since_visit: int = 1

class PatientResponseRequest(BaseModel):
    patient_id: str = ""
    response: str = ""

class PatientJourneyRequest(BaseModel):
    patient_name: str = "Patient"
    patient_age: int = 35
    patient_gender: str = "unknown"
    symptoms: str = ""
    vital_signs: Dict[str, Any] = {}
    pain_level: int = 0
    medical_history: List[str] = []
    medications: List[str] = []
    allergies: List[str] = []
    insurance_provider: str = "BlueCross BlueShield"
    procedure: str = ""
    medication: str = ""

class InsuranceCallRequest(BaseModel):
    insurance_provider: str = "BlueCross BlueShield"
    call_reason: str = "prior authorization status check"
    auth_id: str = ""


# ──────────────────────────────── System ────────────────────────────────

@router.get("/status")
async def system_status():
    """Get overall system status and all agent stats."""
    return {
        "app": "CareAgent OS",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": orchestrator.system_status,
        "llm_usage": llm_router.usage_stats,
    }


@router.get("/agents")
async def list_agents():
    """List all agents and their current status."""
    return {
        "agents": orchestrator.all_agent_stats,
        "total": len(orchestrator.agents),
    }


@router.get("/activity-feed")
async def activity_feed(limit: int = Query(default=50, le=200)):
    """Get the real-time agent activity feed."""
    feed = orchestrator.activity_feed[:limit]
    return {
        "activities": feed,
        "total": len(feed),
    }


# ──────────────────────────────── Voice Intake ────────────────────────────────

@router.post("/intake/start")
async def start_intake(request: PatientIntakeRequest):
    """Start a new patient intake conversation."""
    result = await orchestrator.route_task("intake", {
        "action": "start_intake",
        "message": request.message or request.symptoms,
        "patient_name": request.patient_name,
    })
    return result


@router.post("/intake/continue")
async def continue_intake(request: ConversationContinue):
    """Continue an intake conversation."""
    result = await orchestrator.route_task("intake", {
        "action": "continue_conversation",
        "conversation_id": request.conversation_id,
        "message": request.message,
    })
    return result


@router.post("/intake/complete")
async def complete_intake(request: PatientIntakeRequest):
    """Complete intake and generate assessment."""
    result = await orchestrator.route_task("intake", {
        "action": "complete_intake",
        "patient_name": request.patient_name,
        "symptoms": request.symptoms,
    })
    return result


# ──────────────────────────────── Triage ────────────────────────────────

@router.post("/triage")
async def triage_patient(request: TriageRequest):
    """Run full AI triage assessment."""
    result = await orchestrator.route_task("triage", {
        "action": "full_triage",
        "patient_id": request.patient_id,
        "symptoms": request.symptoms,
        "vital_signs": request.vital_signs,
        "patient_age": request.patient_age,
        "patient_gender": request.patient_gender,
        "pain_level": request.pain_level,
        "medical_history": request.medical_history,
    })
    return result


@router.post("/triage/quick")
async def quick_triage(request: TriageRequest):
    """Quick rule-based triage (no LLM call)."""
    result = await orchestrator.route_task("triage", {
        "action": "quick_triage",
        "symptoms": request.symptoms,
        "vital_signs": request.vital_signs,
        "patient_age": request.patient_age,
        "pain_level": request.pain_level,
    })
    return result


# ──────────────────────────────── Prior Authorization ────────────────────────────────

@router.post("/prior-auth")
async def submit_prior_auth(request: PriorAuthRequest):
    """Check and submit prior authorization."""
    result = await orchestrator.route_task("prior_auth", {
        "action": "check_and_submit",
        "patient_id": request.patient_id,
        "procedure": request.procedure,
        "medication": request.medication,
        "insurance_provider": request.insurance_provider,
        "diagnosis": request.diagnosis,
        "clinical_notes": request.clinical_notes,
        "medical_history": request.medical_history,
    })
    return result


@router.post("/prior-auth/check")
async def check_auth_required(request: PriorAuthRequest):
    """Check if prior authorization is required."""
    result = await orchestrator.route_task("prior_auth", {
        "action": "check_required",
        "procedure": request.procedure,
        "medication": request.medication,
    })
    return result


@router.post("/prior-auth/appeal")
async def appeal_denial(request: Dict[str, Any]):
    """Handle prior auth denial and generate appeal."""
    result = await orchestrator.route_task("prior_auth", {
        "action": "handle_denial",
        **request,
    })
    return result


@router.post("/prior-auth/call-insurance")
async def call_insurance(request: InsuranceCallRequest):
    """Simulate autonomous phone call to insurance company."""
    result = await orchestrator.route_task("prior_auth", {
        "action": "call_insurance",
        "insurance_provider": request.insurance_provider,
        "call_reason": request.call_reason,
        "auth_id": request.auth_id,
    })
    return result


# ──────────────────────────────── Clinical Documentation ────────────────────────────────

@router.post("/documentation/soap")
async def generate_soap(request: ClinicalDocRequest):
    """Generate SOAP notes for an encounter."""
    result = await orchestrator.route_task("clinical_doc", {
        "action": "generate_soap",
        "patient_id": request.patient_id,
        "symptoms": request.symptoms,
        "vital_signs": request.vital_signs,
        "patient_age": request.patient_age,
        "patient_gender": request.patient_gender,
        "exam_findings": request.exam_findings,
        "visit_transcript": request.visit_transcript,
        "medical_history": request.medical_history,
        "medications": request.medications,
        "allergies": request.allergies,
    })
    return result


@router.post("/documentation/code")
async def code_encounter(request: Dict[str, Any]):
    """Generate ICD-10 and CPT codes."""
    result = await orchestrator.route_task("clinical_doc", {
        "action": "code_encounter",
        **request,
    })
    return result


@router.post("/documentation/discharge")
async def generate_discharge(request: Dict[str, Any]):
    """Generate patient discharge instructions."""
    result = await orchestrator.route_task("clinical_doc", {
        "action": "generate_discharge",
        **request,
    })
    return result


# ──────────────────────────────── Patient Advocate ────────────────────────────────

@router.post("/patient/followup")
async def patient_followup(request: PatientFollowupRequest):
    """Generate patient follow-up message."""
    result = await orchestrator.route_task("patient_advocate", {
        "action": "follow_up",
        "patient_id": request.patient_id,
        "patient_name": request.patient_name,
        "diagnosis": request.diagnosis,
        "medications": request.medications,
        "follow_up_plan": request.follow_up_plan,
        "days_since_visit": request.days_since_visit,
    })
    return result


@router.post("/patient/response")
async def process_patient_response(request: PatientResponseRequest):
    """Process patient's response to follow-up."""
    result = await orchestrator.route_task("patient_advocate", {
        "action": "process_response",
        "patient_id": request.patient_id,
        "response": request.response,
    })
    return result


@router.post("/patient/explain")
async def explain_diagnosis(request: Dict[str, Any]):
    """Explain diagnosis in simple language."""
    result = await orchestrator.route_task("patient_advocate", {
        "action": "explain_diagnosis",
        **request,
    })
    return result


# ──────────────────────────────── Operations Intelligence ────────────────────────────────

@router.get("/operations/dashboard")
async def operations_dashboard():
    """Get real-time operations dashboard metrics."""
    result = await orchestrator.route_task("operations", {"action": "dashboard_metrics"})
    return result


@router.get("/operations/predictions")
async def volume_predictions(days: int = Query(default=7, le=30)):
    """Get patient volume predictions."""
    result = await orchestrator.route_task("operations", {"action": "predict_volume", "days_ahead": days})
    return result


@router.get("/operations/schedule")
async def optimize_schedule():
    """Get optimized schedule."""
    result = await orchestrator.route_task("operations", {"action": "optimize_schedule"})
    return result


@router.get("/operations/revenue")
async def revenue_forecast(months: int = Query(default=3, le=12)):
    """Get revenue forecast."""
    result = await orchestrator.route_task("operations", {"action": "revenue_forecast", "months_ahead": months})
    return result


@router.get("/operations/capacity")
async def capacity_analysis():
    """Get department capacity analysis."""
    result = await orchestrator.route_task("operations", {"action": "capacity_analysis"})
    return result


# ──────────────────────────────── Full Journey ────────────────────────────────

@router.post("/journey")
async def run_patient_journey(request: PatientJourneyRequest):
    """Run complete patient journey through all agents."""
    result = await orchestrator.run_patient_journey(request.model_dump())
    return result


@router.post("/demo")
async def run_demo():
    """Run demo scenario with 3 patients through the full system."""
    result = await orchestrator.run_demo_scenario()
    return result


# ──────────────────────────────── WebSocket ────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


ws_manager = ConnectionManager()


@router.websocket("/ws/activity")
async def websocket_activity_feed(websocket: WebSocket):
    """WebSocket for real-time agent activity feed."""
    await ws_manager.connect(websocket)
    try:
        # Send initial state
        await websocket.send_json({
            "type": "initial_state",
            "data": {
                "agents": orchestrator.all_agent_stats,
                "recent_activities": orchestrator.activity_feed[:20],
            }
        })

        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg.get("type") == "get_activities":
                await websocket.send_json({
                    "type": "activities",
                    "data": orchestrator.activity_feed[:20],
                })
            elif msg.get("type") == "get_metrics":
                result = await orchestrator.route_task("operations", {"action": "dashboard_metrics"})
                await websocket.send_json({
                    "type": "metrics",
                    "data": result.get("metrics", {}),
                })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
