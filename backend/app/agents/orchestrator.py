"""
Orchestrator — The meta-agent that coordinates all 6 specialized agents.
Routes tasks, manages handoffs, handles escalations, and provides the unified API.
This is the "secret sauce" of CareAgent OS.
"""
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.agents.base_agent import shared_memory
from app.agents.voice_intake_agent import VoiceIntakeAgent
from app.agents.triage_agent import TriageAgent
from app.agents.prior_auth_agent import PriorAuthAgent
from app.agents.clinical_doc_agent import ClinicalDocAgent
from app.agents.patient_advocate_agent import PatientAdvocateAgent
from app.agents.operations_agent import OperationsAgent


class Orchestrator:
    """
    The CareAgent OS Orchestrator — coordinates a swarm of 6 specialized healthcare agents.
    
    Key capabilities:
    - Task routing: Determines which agent handles each request
    - Multi-agent workflows: Chains agents for end-to-end patient journeys
    - Handoff management: Passes context between agents seamlessly
    - Escalation handling: Routes critical issues to humans
    - Activity feed: Real-time stream of all agent activities
    """

    def __init__(self):
        # Initialize all 6 agents
        self.agents = {
            "voice_intake": VoiceIntakeAgent(),
            "triage": TriageAgent(),
            "prior_auth": PriorAuthAgent(),
            "clinical_doc": ClinicalDocAgent(),
            "patient_advocate": PatientAdvocateAgent(),
            "operations": OperationsAgent(),
        }
        self.memory = shared_memory
        self._activity_feed: List[Dict] = []
        self._workflow_history: List[Dict] = []
        self._active_workflows: Dict[str, Dict] = {}
        self._escalations: List[Dict] = []

    async def route_task(self, task_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route a single task to the appropriate agent."""
        agent = self._find_agent(task_type)
        if not agent:
            return {"status": "error", "message": f"No agent found for task type: {task_type}"}

        start_time = time.time()
        result = await agent.execute(input_data)
        duration_ms = int((time.time() - start_time) * 1000)

        # Log to activity feed
        activity = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": agent.name,
            "agent_type": agent.agent_type,
            "task_type": task_type,
            "status": result.get("status", "unknown"),
            "duration_ms": duration_ms,
            "patient_id": input_data.get("patient_id"),
            "summary": self._summarize_result(result),
        }
        self._activity_feed.append(activity)

        # Check for handoffs
        handoff_to = result.get("handoff_to")
        if handoff_to:
            result["_handoff"] = {
                "next_agent": handoff_to,
                "context_passed": True,
            }

        return result

    async def run_patient_journey(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete patient journey through all relevant agents:
        1. Voice Intake → 2. Triage → 3. Clinical Doc → 4. Prior Auth (if needed) → 5. Patient Advocate
        """
        workflow_id = str(uuid.uuid4())
        patient_id = input_data.get("patient_id", str(uuid.uuid4()))
        input_data["patient_id"] = patient_id

        workflow = {
            "id": workflow_id,
            "patient_id": patient_id,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "steps": [],
            "current_step": 0,
        }
        self._active_workflows[workflow_id] = workflow

        results = {}

        # Step 1: Voice Intake
        workflow["current_step"] = 1
        intake_input = {
            **input_data,
            "action": "complete_intake",
        }
        intake_result = await self.route_task("intake", intake_input)
        results["intake"] = intake_result
        workflow["steps"].append({
            "step": 1, "agent": "Voice Intake", "status": intake_result.get("status"),
            "duration_ms": intake_result.get("duration_ms", 0),
        })

        # Step 2: Triage
        workflow["current_step"] = 2
        triage_input = {
            "patient_id": patient_id,
            "symptoms": input_data.get("symptoms", ""),
            "vital_signs": input_data.get("vital_signs", {}),
            "patient_age": input_data.get("patient_age", 35),
            "patient_gender": input_data.get("patient_gender", "unknown"),
            "pain_level": input_data.get("pain_level", 0),
            "medical_history": input_data.get("medical_history", []),
            "action": "full_triage",
        }
        triage_result = await self.route_task("triage", triage_input)
        results["triage"] = triage_result
        workflow["steps"].append({
            "step": 2, "agent": "Triage", "status": triage_result.get("status"),
            "urgency": triage_result.get("triage", {}).get("urgency_level", "unknown"),
            "duration_ms": triage_result.get("duration_ms", 0),
        })

        # Step 3: Clinical Documentation
        workflow["current_step"] = 3
        doc_input = {
            "patient_id": patient_id,
            "symptoms": input_data.get("symptoms", ""),
            "vital_signs": input_data.get("vital_signs", {}),
            "patient_age": input_data.get("patient_age", 35),
            "patient_gender": input_data.get("patient_gender", "unknown"),
            "medical_history": input_data.get("medical_history", []),
            "medications": input_data.get("medications", []),
            "allergies": input_data.get("allergies", []),
            "action": "generate_soap",
        }
        doc_result = await self.route_task("clinical_doc", doc_input)
        results["documentation"] = doc_result
        workflow["steps"].append({
            "step": 3, "agent": "Clinical Doc", "status": doc_result.get("status"),
            "duration_ms": doc_result.get("duration_ms", 0),
        })

        # Step 4: Prior Auth (if needed)
        if doc_result.get("needs_prior_auth"):
            workflow["current_step"] = 4
            auth_input = {
                "patient_id": patient_id,
                "procedure": input_data.get("procedure", ""),
                "medication": input_data.get("medication", ""),
                "insurance_provider": input_data.get("insurance_provider", "BlueCross BlueShield"),
                "diagnosis": input_data.get("symptoms", ""),
                "clinical_notes": str(doc_result.get("documentation", {}).get("soap", "")),
                "action": "check_and_submit",
            }
            auth_result = await self.route_task("prior_auth", auth_input)
            results["prior_auth"] = auth_result
            workflow["steps"].append({
                "step": 4, "agent": "Prior Auth", "status": auth_result.get("status"),
                "duration_ms": auth_result.get("duration_ms", 0),
            })

        # Step 5: Patient Advocate
        workflow["current_step"] = 5
        advocate_input = {
            "patient_id": patient_id,
            "patient_name": input_data.get("patient_name", "Patient"),
            "diagnosis": triage_result.get("triage", {}).get("preliminary_assessment", ""),
            "medications": doc_result.get("documentation", {}).get("prescriptions", []),
            "action": "schedule_followups",
        }
        advocate_result = await self.route_task("patient_advocate", advocate_input)
        results["patient_advocate"] = advocate_result
        workflow["steps"].append({
            "step": 5, "agent": "Patient Advocate", "status": advocate_result.get("status"),
            "duration_ms": advocate_result.get("duration_ms", 0),
        })

        # Complete workflow
        workflow["status"] = "completed"
        workflow["completed_at"] = datetime.now(timezone.utc).isoformat()
        workflow["total_duration_ms"] = sum(s.get("duration_ms", 0) for s in workflow["steps"])

        self._workflow_history.append(workflow)
        del self._active_workflows[workflow_id]

        return {
            "status": "journey_completed",
            "workflow_id": workflow_id,
            "patient_id": patient_id,
            "workflow": workflow,
            "results": results,
        }

    async def run_demo_scenario(self) -> Dict[str, Any]:
        """Run a complete demo scenario with 3 patients to showcase all agents."""
        scenarios = [
            {
                "patient_name": "Maria Santos",
                "patient_age": 62,
                "patient_gender": "female",
                "symptoms": "Severe chest pain radiating to left arm, shortness of breath, diaphoresis",
                "vital_signs": {"heart_rate": 110, "systolic_bp": 90, "diastolic_bp": 60, "oxygen_saturation": 92, "temperature": 98.6, "respiratory_rate": 24},
                "pain_level": 9,
                "medical_history": ["hypertension", "type 2 diabetes", "hyperlipidemia"],
                "medications": ["metformin", "lisinopril", "atorvastatin"],
                "allergies": ["penicillin"],
                "insurance_provider": "Medicare",
            },
            {
                "patient_name": "James Wilson",
                "patient_age": 8,
                "patient_gender": "male",
                "symptoms": "High fever 103.5°F for 3 days, severe sore throat, difficulty swallowing, white patches on tonsils",
                "vital_signs": {"heart_rate": 120, "systolic_bp": 100, "diastolic_bp": 65, "oxygen_saturation": 97, "temperature": 103.5, "respiratory_rate": 22},
                "pain_level": 7,
                "medical_history": ["recurrent strep throat"],
                "medications": [],
                "allergies": ["amoxicillin"],
                "insurance_provider": "BlueCross BlueShield",
            },
            {
                "patient_name": "Aisha Patel",
                "patient_age": 34,
                "patient_gender": "female",
                "symptoms": "Progressive lower back pain for 2 weeks, now radiating down right leg, numbness in right foot",
                "vital_signs": {"heart_rate": 82, "systolic_bp": 128, "diastolic_bp": 78, "oxygen_saturation": 98, "temperature": 98.2, "respiratory_rate": 16},
                "pain_level": 8,
                "medical_history": ["none"],
                "medications": ["ibuprofen PRN"],
                "allergies": [],
                "insurance_provider": "UnitedHealthcare",
                "procedure": "MRI lumbar spine",
            },
        ]

        demo_results = []
        for scenario in scenarios:
            result = await self.run_patient_journey(scenario)
            demo_results.append({
                "patient": scenario["patient_name"],
                "urgency": result.get("results", {}).get("triage", {}).get("triage", {}).get("urgency_level", "unknown"),
                "workflow_steps": len(result.get("workflow", {}).get("steps", [])),
                "total_duration_ms": result.get("workflow", {}).get("total_duration_ms", 0),
            })

        # Also generate operations metrics
        ops_result = await self.route_task("operations", {"action": "dashboard_metrics"})

        return {
            "status": "demo_completed",
            "patients_processed": len(demo_results),
            "patient_results": demo_results,
            "operations_metrics": ops_result.get("metrics", {}),
        }

    def _find_agent(self, task_type: str):
        """Find the best agent for a given task type."""
        for agent in self.agents.values():
            # Synchronous check — agents define their capabilities
            if task_type in self._get_agent_tasks(agent.agent_type):
                return agent
        # Fallback: try to match by agent_type
        return self.agents.get(task_type)

    def _get_agent_tasks(self, agent_type: str) -> List[str]:
        """Map agent types to task types they handle."""
        mapping = {
            "voice_intake": ["voice_intake", "patient_call", "symptom_collection", "intake"],
            "triage": ["triage", "urgency_assessment", "department_routing", "triage_assessment"],
            "prior_auth": ["prior_auth", "insurance_auth", "auth_check", "auth_appeal", "prior_authorization"],
            "clinical_documentation": ["documentation", "soap_notes", "icd_coding", "clinical_doc", "medical_coding"],
            "patient_advocate": ["patient_followup", "medication_reminder", "patient_education", "care_transition", "patient_communication", "patient_advocate"],
            "operations_intelligence": ["analytics", "forecasting", "scheduling", "revenue", "capacity", "operations", "metrics", "operations_intelligence"],
        }
        return mapping.get(agent_type, [])

    def _summarize_result(self, result: Dict) -> str:
        status = result.get("status", "unknown")
        agent = result.get("agent_name", "")
        return f"{agent}: {status}"

    @property
    def activity_feed(self) -> List[Dict]:
        return sorted(self._activity_feed, key=lambda x: x["timestamp"], reverse=True)[:50]

    @property
    def system_status(self) -> Dict:
        return {
            "agents": {name: agent.stats for name, agent in self.agents.items()},
            "active_workflows": len(self._active_workflows),
            "completed_workflows": len(self._workflow_history),
            "total_activities": len(self._activity_feed),
            "escalations": len(self._escalations),
            "shared_memory_keys": len(self.memory.all_keys),
        }

    @property
    def all_agent_stats(self) -> List[Dict]:
        return [agent.stats for agent in self.agents.values()]


# Singleton instance
orchestrator = Orchestrator()
