"""
Agent 5: Patient Advocate Agent
Post-visit follow-ups, medication reminders, health education, and patient communication.
Acts as the patient's personal health assistant via SMS/voice.
"""
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from app.agents.base_agent import BaseAgent


class PatientAdvocateAgent(BaseAgent):
    """Autonomous patient advocacy and follow-up agent."""

    ADVOCATE_SYSTEM_PROMPT = """You are a compassionate patient health advocate. Your role is to:
1. Follow up with patients after visits
2. Send medication reminders and check adherence
3. Explain medical instructions in simple language (6th grade reading level)
4. Answer patient health questions
5. Detect warning signs that need escalation
6. Coordinate care transitions

Always be empathetic, clear, and actionable. Use the patient's first name.
If the patient reports worsening symptoms, escalate immediately.

For follow-up messages, output as JSON:
{
    "message_type": "follow_up|reminder|education|alert|check_in",
    "channel": "sms|voice|email",
    "message": "",
    "urgency": "routine|elevated|urgent",
    "action_items": [],
    "escalate": false,
    "escalation_reason": ""
}"""

    def __init__(self):
        super().__init__(
            name="Patient Advocate Agent",
            agent_type="patient_advocate",
            description="Post-visit follow-ups, medication reminders, and patient communication"
        )
        self._scheduled_followups: List[Dict] = []
        self._message_history: List[Dict] = []

    async def can_handle(self, task_type: str) -> bool:
        return task_type in [
            "patient_followup", "medication_reminder", "patient_education",
            "care_transition", "patient_communication", "patient_advocate"
        ]

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action", "follow_up")

        if action == "follow_up":
            return await self._generate_followup(input_data)
        elif action == "medication_reminder":
            return await self._medication_reminder(input_data)
        elif action == "explain_diagnosis":
            return await self._explain_diagnosis(input_data)
        elif action == "check_in":
            return await self._check_in(input_data)
        elif action == "process_response":
            return await self._process_patient_response(input_data)
        elif action == "schedule_followups":
            return await self._schedule_followups(input_data)
        else:
            return await self._generate_followup(input_data)

    async def _generate_followup(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        patient_id = input_data.get("patient_id", "unknown")
        patient_name = input_data.get("patient_name", "there")
        context = self.memory.get_patient_context(patient_id)
        documentation = context.get("documentation", {})
        triage = context.get("triage", {})

        diagnosis = input_data.get("diagnosis", triage.get("preliminary_assessment", "your recent visit"))
        medications = input_data.get("medications", documentation.get("prescriptions", []))
        follow_up_plan = input_data.get("follow_up_plan", documentation.get("soap", {}).get("plan", ""))

        messages = [
            {"role": "system", "content": self.ADVOCATE_SYSTEM_PROMPT},
            {"role": "user", "content": f"""Generate a post-visit follow-up message:

Patient Name: {patient_name}
Diagnosis/Visit Reason: {diagnosis}
Medications Prescribed: {json.dumps(medications)}
Follow-up Plan: {follow_up_plan}
Days since visit: {input_data.get('days_since_visit', 1)}

Create a warm, personalized follow-up message checking on the patient.
Ask about medication adherence and any new/worsening symptoms.
Output as JSON."""}
        ]

        response = await self.llm.complete(
            task_type="patient_communication",
            messages=messages,
            temperature=0.5,
        )

        try:
            followup = json.loads(response["content"])
        except json.JSONDecodeError:
            followup = {
                "message_type": "follow_up",
                "channel": "sms",
                "message": response["content"],
                "urgency": "routine",
                "action_items": [],
                "escalate": False,
            }

        message_record = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "type": "follow_up",
            "content": followup,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }
        self._message_history.append(message_record)

        return {
            "status": "followup_generated",
            "patient_id": patient_id,
            "followup": followup,
            "message_id": message_record["id"],
            "model_used": response["model"],
            "tokens_used": response["tokens"],
        }

    async def _medication_reminder(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        patient_name = input_data.get("patient_name", "there")
        medications = input_data.get("medications", [])
        pharmacy_status = input_data.get("pharmacy_status", "ready")

        messages = [
            {"role": "system", "content": self.ADVOCATE_SYSTEM_PROMPT},
            {"role": "user", "content": f"""Generate a medication reminder:

Patient: {patient_name}
Medications: {json.dumps(medications)}
Pharmacy pickup status: {pharmacy_status}
Adherence history: {input_data.get('adherence', 'First reminder')}

Be friendly but clear about importance. Include timing and food instructions.
If pharmacy shows not picked up, gently remind about pickup.
Output as JSON."""}
        ]

        response = await self.llm.complete(
            task_type="patient_communication",
            messages=messages,
            temperature=0.5,
        )

        try:
            reminder = json.loads(response["content"])
        except json.JSONDecodeError:
            reminder = {
                "message_type": "reminder",
                "channel": "sms",
                "message": response["content"],
                "urgency": "routine",
            }

        return {
            "status": "reminder_generated",
            "reminder": reminder,
            "model_used": response["model"],
            "tokens_used": response["tokens"],
        }

    async def _explain_diagnosis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "Explain medical conditions in simple, everyday language. Use analogies. 6th grade reading level. Be reassuring but honest."},
            {"role": "user", "content": f"""Explain this to a patient:

Diagnosis: {input_data.get('diagnosis', '')}
Treatment plan: {input_data.get('treatment', '')}
What they need to know: {input_data.get('key_points', '')}

Make it clear, simple, and actionable. What should they do? What warning signs to watch for?"""}
        ]

        response = await self.llm.complete(
            task_type="patient_communication",
            messages=messages,
            temperature=0.5,
        )

        return {
            "status": "explanation_generated",
            "explanation": response["content"],
            "model_used": response["model"],
            "tokens_used": response["tokens"],
        }

    async def _check_in(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        patient_name = input_data.get("patient_name", "there")
        condition = input_data.get("condition", "")
        days_post = input_data.get("days_post_visit", 3)

        check_in_message = {
            "message_type": "check_in",
            "channel": "sms",
            "message": f"Hi {patient_name}! This is your care team checking in. It's been {days_post} days since your visit. How are you feeling? Are your symptoms improving? Reply YES if better, NO if same/worse, or HELP if you need to talk to someone.",
            "urgency": "routine",
            "action_items": ["Monitor response", "Escalate if worsening"],
            "escalate": False,
        }

        return {
            "status": "check_in_sent",
            "check_in": check_in_message,
            "model_used": "template",
            "tokens_used": 0,
        }

    async def _process_patient_response(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        patient_response = input_data.get("response", "").lower().strip()
        patient_id = input_data.get("patient_id", "unknown")

        # Quick classification
        if patient_response in ["no", "worse", "not better", "bad", "terrible", "help"]:
            self.escalate(
                reason=f"Patient reports worsening symptoms: '{input_data.get('response', '')}'",
                patient_id=patient_id,
                data=input_data,
            )
            return {
                "status": "escalated",
                "urgency": "elevated",
                "message": "I'm sorry to hear that. Let me connect you with your care team right away. Someone will reach out within the hour.",
                "model_used": "rule-based",
                "tokens_used": 0,
            }
        elif patient_response in ["yes", "better", "good", "great", "improving"]:
            return {
                "status": "positive_response",
                "urgency": "routine",
                "message": "That's great to hear! Keep following your care plan. We'll check in again in a few days. Don't hesitate to reach out if anything changes.",
                "model_used": "rule-based",
                "tokens_used": 0,
            }
        else:
            # Use LLM for ambiguous responses
            messages = [
                {"role": "system", "content": "Classify patient response as: improving, stable, worsening, or unclear. If worsening, set escalate=true."},
                {"role": "user", "content": f"Patient said: '{input_data.get('response', '')}'. Classify and respond appropriately as JSON."}
            ]
            response = await self.llm.complete(task_type="patient_communication", messages=messages, temperature=0.3)
            return {
                "status": "response_processed",
                "analysis": response["content"],
                "model_used": response["model"],
                "tokens_used": response["tokens"],
            }

    async def _schedule_followups(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        patient_id = input_data.get("patient_id", "unknown")
        patient_name = input_data.get("patient_name", "Patient")
        diagnosis = input_data.get("diagnosis", "")

        followups = [
            {"type": "check_in", "days_after": 1, "channel": "sms"},
            {"type": "medication_reminder", "days_after": 1, "channel": "sms"},
            {"type": "follow_up", "days_after": 3, "channel": "sms"},
            {"type": "check_in", "days_after": 7, "channel": "voice"},
            {"type": "follow_up", "days_after": 14, "channel": "sms"},
        ]

        for f in followups:
            self._scheduled_followups.append({
                "id": str(uuid.uuid4()),
                "patient_id": patient_id,
                "patient_name": patient_name,
                **f,
                "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=f["days_after"])).isoformat(),
                "status": "scheduled",
            })

        return {
            "status": "followups_scheduled",
            "patient_id": patient_id,
            "scheduled": followups,
            "total_scheduled": len(followups),
            "model_used": "scheduler",
            "tokens_used": 0,
        }

    @property
    def followup_stats(self) -> Dict:
        return {
            "scheduled": len(self._scheduled_followups),
            "messages_sent": len(self._message_history),
        }
