"""
Agent 4: Clinical Documentation Agent
Generates SOAP notes, ICD-10 codes, and clinical documentation from encounters.
Listens to visits and produces structured medical records.
"""
import json
from typing import Dict, Any

from app.agents.base_agent import BaseAgent


class ClinicalDocAgent(BaseAgent):
    """Autonomous clinical documentation and medical coding agent."""

    SOAP_SYSTEM_PROMPT = """You are an expert medical documentation specialist. Generate comprehensive 
SOAP notes from clinical encounter data. Follow these standards:

SUBJECTIVE: Patient's own words, chief complaint, HPI (onset, location, duration, character, 
aggravating/alleviating factors, radiation, timing, severity), ROS, PMH, medications, allergies, 
social history, family history.

OBJECTIVE: Vital signs, physical exam findings, diagnostic results, lab values.

ASSESSMENT: Clinical impression, differential diagnoses ranked by probability, severity assessment.

PLAN: Diagnostic workup, medications (with dose, route, frequency, duration), procedures, referrals,
follow-up timeline, patient education, disposition.

Also provide:
- ICD-10 codes for all diagnoses
- CPT codes for procedures performed
- E/M level recommendation

Output as JSON:
{
    "soap": {
        "subjective": "",
        "objective": "",
        "assessment": "",
        "plan": ""
    },
    "icd10_codes": [{"code": "", "description": "", "type": "primary|secondary"}],
    "cpt_codes": [{"code": "", "description": ""}],
    "em_level": "",
    "critical_findings": [],
    "follow_up": {"timeframe": "", "instructions": ""},
    "prescriptions": [{"medication": "", "dose": "", "route": "", "frequency": "", "duration": ""}]
}"""

    def __init__(self):
        super().__init__(
            name="Clinical Doc Agent",
            agent_type="clinical_documentation",
            description="Generates SOAP notes, ICD-10 codes, and clinical documentation"
        )

    async def can_handle(self, task_type: str) -> bool:
        return task_type in ["documentation", "soap_notes", "icd_coding", "clinical_doc", "medical_coding"]

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action", "generate_soap")

        if action == "generate_soap":
            return await self._generate_soap(input_data)
        elif action == "code_encounter":
            return await self._code_encounter(input_data)
        elif action == "generate_referral":
            return await self._generate_referral(input_data)
        elif action == "generate_discharge":
            return await self._generate_discharge(input_data)
        else:
            return await self._generate_soap(input_data)

    async def _generate_soap(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        patient_id = input_data.get("patient_id", "unknown")
        context = self.memory.get_patient_context(patient_id)

        # Gather all available data
        symptoms = input_data.get("symptoms", context.get("intake", {}).get("chief_complaint", ""))
        vital_signs = input_data.get("vital_signs", {})
        triage = context.get("triage", {})
        exam_findings = input_data.get("exam_findings", "")
        visit_transcript = input_data.get("visit_transcript", "")

        messages = [
            {"role": "system", "content": self.SOAP_SYSTEM_PROMPT},
            {"role": "user", "content": f"""Generate SOAP notes for this encounter:

Patient ID: {patient_id}
Chief Complaint: {symptoms}
Vital Signs: {json.dumps(vital_signs)}
Triage Assessment: {json.dumps(triage) if triage else 'Not available'}
Physical Exam: {exam_findings or 'Standard exam performed, findings within normal limits unless noted'}
Visit Notes/Transcript: {visit_transcript or 'Standard visit conducted'}
Patient Age: {input_data.get('patient_age', 'Adult')}
Gender: {input_data.get('patient_gender', 'Not specified')}
Medical History: {json.dumps(input_data.get('medical_history', []))}
Medications: {json.dumps(input_data.get('medications', []))}
Allergies: {json.dumps(input_data.get('allergies', []))}

Generate complete SOAP notes with ICD-10 codes and plan as JSON."""}
        ]

        response = await self.llm.complete(
            task_type="documentation",
            messages=messages,
            temperature=0.2,
        )

        try:
            documentation = json.loads(response["content"])
        except json.JSONDecodeError:
            documentation = {
                "soap": {
                    "subjective": f"Patient presents with: {symptoms}",
                    "objective": f"Vitals: {json.dumps(vital_signs)}. {exam_findings}",
                    "assessment": response["content"],
                    "plan": "See clinical notes"
                },
                "icd10_codes": [],
                "cpt_codes": [],
            }

        # Store in shared memory
        self.memory.update_patient_context(patient_id, {
            "documentation": documentation,
            "doc_agent": self.name,
        }, self.name)

        # Check if any prescriptions need prior auth
        prescriptions = documentation.get("prescriptions", [])
        needs_auth = any(
            self._might_need_auth(p.get("medication", ""))
            for p in prescriptions
        )

        return {
            "status": "documentation_complete",
            "patient_id": patient_id,
            "documentation": documentation,
            "needs_prior_auth": needs_auth,
            "handoff_to": "prior_auth_agent" if needs_auth else "patient_advocate_agent",
            "model_used": response["model"],
            "tokens_used": response["tokens"],
        }

    async def _code_encounter(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "You are a certified medical coder (CPC). Assign ICD-10-CM and CPT codes."},
            {"role": "user", "content": f"""Code this encounter:
Diagnosis: {input_data.get('diagnosis', '')}
Procedures: {input_data.get('procedures', '')}
Visit type: {input_data.get('visit_type', 'office visit')}
Complexity: {input_data.get('complexity', 'moderate')}

Return JSON with icd10_codes and cpt_codes arrays."""}
        ]

        response = await self.llm.complete(
            task_type="coding",
            messages=messages,
            temperature=0.1,
        )

        try:
            coding = json.loads(response["content"])
        except json.JSONDecodeError:
            coding = {"icd10_codes": [], "cpt_codes": [], "raw": response["content"]}

        return {
            "status": "coding_complete",
            "coding": coding,
            "model_used": response["model"],
            "tokens_used": response["tokens"],
        }

    async def _generate_referral(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "Generate a specialist referral letter. Be professional, include clinical justification."},
            {"role": "user", "content": f"""Generate referral:
From: {input_data.get('referring_provider', 'Primary Care')}
To: {input_data.get('specialist', 'Specialist')}
Patient: {input_data.get('patient_name', 'Patient')}
Reason: {input_data.get('reason', '')}
Clinical summary: {input_data.get('clinical_summary', '')}
Urgency: {input_data.get('urgency', 'routine')}"""}
        ]

        response = await self.llm.complete(
            task_type="documentation",
            messages=messages,
            temperature=0.3,
        )

        return {
            "status": "referral_generated",
            "referral": response["content"],
            "model_used": response["model"],
            "tokens_used": response["tokens"],
        }

    async def _generate_discharge(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "Generate patient-friendly discharge instructions. Use simple language at 6th grade reading level. Include medication list, warning signs, follow-up plan."},
            {"role": "user", "content": f"""Generate discharge instructions:
Diagnosis: {input_data.get('diagnosis', '')}
Medications: {json.dumps(input_data.get('medications', []))}
Follow-up: {input_data.get('follow_up', '')}
Restrictions: {input_data.get('restrictions', 'None')}
Warning signs: {input_data.get('warning_signs', '')}"""}
        ]

        response = await self.llm.complete(
            task_type="patient_communication",
            messages=messages,
            temperature=0.4,
        )

        return {
            "status": "discharge_instructions_generated",
            "instructions": response["content"],
            "model_used": response["model"],
            "tokens_used": response["tokens"],
        }

    def _might_need_auth(self, medication: str) -> bool:
        auth_meds = ["biologic", "specialty", "infusion", "injectable", "chemotherapy"]
        return any(kw in medication.lower() for kw in auth_meds)
