"""
Agent 1: Voice Intake Agent
Answers patient calls, collects symptoms via natural conversation, books appointments.
Uses Whisper for STT and GPT-4o for conversational intake.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from app.agents.base_agent import BaseAgent


class VoiceIntakeAgent(BaseAgent):
    """Autonomous voice-based patient intake agent."""

    INTAKE_SYSTEM_PROMPT = """You are a compassionate, professional medical intake specialist for CareAgent OS. 
Your job is to conduct patient intake via voice/text conversation.

During intake, you must collect:
1. Patient name and date of birth
2. Chief complaint (why are they calling/visiting)
3. Symptom details (onset, duration, severity, progression)
4. Pain level (0-10 scale)
5. Relevant medical history
6. Current medications
7. Allergies
8. Insurance information

Be empathetic, clear, and efficient. Ask one question at a time.
If symptoms suggest an emergency (chest pain, difficulty breathing, stroke symptoms, severe bleeding),
immediately flag as CRITICAL and recommend calling 911.

Output your assessment as JSON with these fields:
{
    "patient_info": {"name": "", "dob": "", "phone": "", "insurance": ""},
    "chief_complaint": "",
    "symptoms": [{"name": "", "onset": "", "duration": "", "severity": ""}],
    "pain_level": 0,
    "medical_history": [],
    "medications": [],
    "allergies": [],
    "urgency_flag": "normal|elevated|critical",
    "intake_summary": "",
    "recommended_action": ""
}"""

    def __init__(self):
        super().__init__(
            name="Voice Intake Agent",
            agent_type="voice_intake",
            description="Handles patient calls, collects symptoms, and initiates intake process"
        )
        self._active_conversations: Dict[str, list] = {}

    async def can_handle(self, task_type: str) -> bool:
        return task_type in ["voice_intake", "patient_call", "symptom_collection", "intake"]

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action", "start_intake")

        if action == "start_intake":
            return await self._start_intake(input_data)
        elif action == "continue_conversation":
            return await self._continue_conversation(input_data)
        elif action == "complete_intake":
            return await self._complete_intake(input_data)
        elif action == "transcribe_voice":
            return await self._transcribe_voice(input_data)
        else:
            return await self._start_intake(input_data)

    async def _start_intake(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        conversation_id = str(uuid.uuid4())
        patient_message = input_data.get("message", "")

        messages = [
            {"role": "system", "content": self.INTAKE_SYSTEM_PROMPT},
            {"role": "user", "content": f"A new patient is reaching out. Their initial message: '{patient_message}'. Begin the intake process by greeting them and asking your first question."}
        ]

        response = await self.llm.complete(
            task_type="patient_communication",
            messages=messages,
            temperature=0.4,
        )

        self._active_conversations[conversation_id] = messages + [
            {"role": "assistant", "content": response["content"]}
        ]

        return {
            "status": "conversation_started",
            "conversation_id": conversation_id,
            "agent_response": response["content"],
            "model_used": response["model"],
            "tokens_used": response["tokens"],
        }

    async def _continue_conversation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        conversation_id = input_data.get("conversation_id", "")
        patient_message = input_data.get("message", "")

        if conversation_id not in self._active_conversations:
            return await self._start_intake(input_data)

        conversation = self._active_conversations[conversation_id]
        conversation.append({"role": "user", "content": patient_message})

        response = await self.llm.complete(
            task_type="patient_communication",
            messages=conversation,
            temperature=0.4,
        )

        conversation.append({"role": "assistant", "content": response["content"]})

        return {
            "status": "conversation_continued",
            "conversation_id": conversation_id,
            "agent_response": response["content"],
            "model_used": response["model"],
            "tokens_used": response["tokens"],
        }

    async def _complete_intake(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        conversation_id = input_data.get("conversation_id", "")
        conversation = self._active_conversations.get(conversation_id, [])

        if not conversation:
            symptoms = input_data.get("symptoms", "general complaint")
            patient_name = input_data.get("patient_name", "Unknown")
            conversation = [
                {"role": "system", "content": self.INTAKE_SYSTEM_PROMPT},
                {"role": "user", "content": f"Patient {patient_name} reports: {symptoms}. Generate a complete intake assessment."}
            ]

        conversation.append({
            "role": "user",
            "content": "Based on our conversation, generate the complete intake assessment as JSON."
        })

        response = await self.llm.complete(
            task_type="triage",
            messages=conversation,
            temperature=0.2,
        )

        try:
            assessment = json.loads(response["content"])
        except json.JSONDecodeError:
            assessment = {
                "chief_complaint": input_data.get("symptoms", "See conversation"),
                "intake_summary": response["content"],
                "urgency_flag": "normal",
                "recommended_action": "Schedule standard appointment"
            }

        patient_id = input_data.get("patient_id", str(uuid.uuid4()))
        self.memory.update_patient_context(patient_id, {
            "intake": assessment,
            "intake_timestamp": datetime.now(timezone.utc).isoformat(),
            "intake_agent": self.name,
        }, self.name)

        if conversation_id in self._active_conversations:
            del self._active_conversations[conversation_id]

        return {
            "status": "intake_completed",
            "patient_id": patient_id,
            "assessment": assessment,
            "handoff_to": "triage_agent",
            "model_used": response["model"],
            "tokens_used": response["tokens"],
        }

    async def _transcribe_voice(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe voice input (simulated in demo mode)."""
        audio_text = input_data.get("transcription", input_data.get("message", ""))
        return {
            "status": "transcribed",
            "text": audio_text,
            "model_used": "whisper-1",
            "tokens_used": 0,
        }
