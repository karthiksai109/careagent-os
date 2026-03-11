"""Unit tests for CareAgent OS agents."""
import pytest
import asyncio
from app.agents.base_agent import BaseAgent, SharedMemory
from app.agents.voice_intake_agent import VoiceIntakeAgent
from app.agents.triage_agent import TriageAgent
from app.agents.prior_auth_agent import PriorAuthAgent
from app.agents.clinical_doc_agent import ClinicalDocAgent
from app.agents.patient_advocate_agent import PatientAdvocateAgent
from app.agents.operations_agent import OperationsAgent


class TestSharedMemory:
    def test_set_and_get(self):
        mem = SharedMemory()
        mem.set("test_key", {"value": 42})
        assert mem.get("test_key") == {"value": 42}

    def test_get_default(self):
        mem = SharedMemory()
        assert mem.get("missing") is None
        assert mem.get("missing", "default") == "default"

    def test_patient_context(self):
        mem = SharedMemory()
        mem.set("patient:p1:triage", {"urgency": "critical"})
        ctx = mem.get_patient_context("p1")
        assert "triage" in ctx
        assert ctx["triage"]["urgency"] == "critical"

    def test_event_log(self):
        mem = SharedMemory()
        mem.log_event("test_agent", "test_action", {"detail": "ok"})
        assert len(mem.event_log) == 1
        assert mem.event_log[0]["agent"] == "test_agent"


class TestVoiceIntakeAgent:
    def test_init(self):
        agent = VoiceIntakeAgent()
        assert agent.name == "Voice Intake Agent"
        assert agent.agent_type == "voice_intake"

    @pytest.mark.asyncio
    async def test_can_handle(self):
        agent = VoiceIntakeAgent()
        assert await agent.can_handle("voice_intake") is True
        assert await agent.can_handle("triage") is False


class TestTriageAgent:
    def test_init(self):
        agent = TriageAgent()
        assert agent.name == "Triage Agent"

    @pytest.mark.asyncio
    async def test_can_handle(self):
        agent = TriageAgent()
        assert await agent.can_handle("triage") is True
        assert await agent.can_handle("documentation") is False

    @pytest.mark.asyncio
    async def test_critical_symptoms_rule(self):
        agent = TriageAgent()
        result = await agent.execute({
            "action": "full_triage",
            "symptoms": "chest pain radiating to left arm, shortness of breath",
            "vital_signs": {"heart_rate": 110, "systolic_bp": 85, "oxygen_saturation": 90},
            "patient_age": 60,
            "pain_level": 9,
        })
        assert result["is_critical_flag"] is True
        assert result["triage"]["urgency_level"] == "critical"


class TestPriorAuthAgent:
    def test_init(self):
        agent = PriorAuthAgent()
        assert agent.agent_type == "prior_auth"

    @pytest.mark.asyncio
    async def test_can_handle(self):
        agent = PriorAuthAgent()
        assert await agent.can_handle("prior_auth") is True
        assert await agent.can_handle("voice_intake") is False


class TestClinicalDocAgent:
    def test_init(self):
        agent = ClinicalDocAgent()
        assert agent.agent_type == "clinical_documentation"

    @pytest.mark.asyncio
    async def test_can_handle(self):
        agent = ClinicalDocAgent()
        assert await agent.can_handle("documentation") is True


class TestPatientAdvocateAgent:
    def test_init(self):
        agent = PatientAdvocateAgent()
        assert agent.agent_type == "patient_advocate"

    @pytest.mark.asyncio
    async def test_check_in(self):
        agent = PatientAdvocateAgent()
        result = await agent.execute({
            "action": "check_in",
            "patient_name": "Test Patient",
            "days_post_visit": 3,
        })
        assert result["status"] == "check_in_sent"


class TestOperationsAgent:
    def test_init(self):
        agent = OperationsAgent()
        assert agent.agent_type == "operations_intelligence"

    @pytest.mark.asyncio
    async def test_dashboard_metrics(self):
        agent = OperationsAgent()
        result = await agent.execute({"action": "dashboard_metrics"})
        assert result["status"] == "metrics_generated"
        assert "overview" in result["metrics"]
        assert "agent_performance" in result["metrics"]

    @pytest.mark.asyncio
    async def test_capacity_analysis(self):
        agent = OperationsAgent()
        result = await agent.execute({"action": "capacity_analysis"})
        assert result["status"] == "analysis_complete"
        assert "departments" in result
