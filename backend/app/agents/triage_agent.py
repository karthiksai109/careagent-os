"""
Agent 2: Triage & Routing Agent
AI triage assessment using Manchester Triage System + Emergency Severity Index.
Classifies urgency, routes to department, and escalates critical cases.
"""
import json
from typing import Dict, Any, List, Optional

from app.agents.base_agent import BaseAgent


class TriageAgent(BaseAgent):
    """Autonomous AI triage and patient routing agent."""

    CRITICAL_SYMPTOMS = [
        "chest pain", "difficulty breathing", "shortness of breath", "stroke",
        "unresponsive", "seizure", "severe bleeding", "anaphylaxis",
        "cardiac arrest", "unconscious", "not breathing", "choking",
        "severe head injury", "poisoning", "overdose"
    ]

    EMERGENCY_SYMPTOMS = [
        "high fever", "severe abdominal pain", "fracture", "deep laceration",
        "severe burn", "dehydration", "diabetic emergency", "asthma attack",
        "allergic reaction", "severe vomiting blood", "blood in stool"
    ]

    DEPARTMENT_ROUTING = {
        "cardiac": ["chest pain", "palpitations", "heart", "cardiac", "arrhythmia", "hypertension"],
        "respiratory": ["breathing", "cough", "asthma", "pneumonia", "respiratory", "lung", "wheezing"],
        "neurology": ["headache", "seizure", "stroke", "numbness", "dizziness", "confusion", "tingling"],
        "orthopedics": ["fracture", "bone", "joint", "sprain", "back pain", "musculoskeletal"],
        "gastroenterology": ["abdominal", "nausea", "vomiting", "diarrhea", "stomach", "bowel"],
        "pediatrics": ["child", "infant", "pediatric", "newborn"],
        "obstetrics": ["pregnancy", "pregnant", "contractions", "labor", "prenatal"],
        "psychiatry": ["depression", "anxiety", "suicidal", "mental health", "psychosis"],
        "dermatology": ["rash", "skin", "wound", "burn", "lesion"],
        "internal_medicine": [],  # default fallback
    }

    TRIAGE_SYSTEM_PROMPT = """You are an expert medical triage AI using the Manchester Triage System (MTS) 
and Emergency Severity Index (ESI). Analyze the patient presentation and provide:

1. Urgency Level: critical (ESI-1), emergency (ESI-2), urgent (ESI-3), semi_urgent (ESI-4), non_urgent (ESI-5)
2. Urgency Score: 0.0 to 1.0
3. Recommended Department
4. Preliminary Assessment
5. Suggested Tests/Workup
6. Clinical Reasoning chain

Consider:
- Vital signs abnormalities
- Age-based risk factors (pediatric <12, geriatric >70)
- Pain severity
- Symptom acuity and progression
- Red flags and critical presentations

Output as JSON:
{
    "urgency_level": "critical|emergency|urgent|semi_urgent|non_urgent",
    "urgency_score": 0.0,
    "esi_level": 1-5,
    "recommended_department": "",
    "preliminary_assessment": "",
    "differential_diagnoses": [{"condition": "", "probability": 0.0}],
    "suggested_tests": [],
    "red_flags": [],
    "clinical_reasoning": "",
    "estimated_wait_time_minutes": 0,
    "requires_immediate_intervention": false
}"""

    def __init__(self):
        super().__init__(
            name="Triage Agent",
            agent_type="triage",
            description="AI-powered triage assessment, urgency classification, and department routing"
        )

    async def can_handle(self, task_type: str) -> bool:
        return task_type in ["triage", "urgency_assessment", "department_routing", "triage_assessment"]

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action", "full_triage")

        if action == "full_triage":
            return await self._full_triage(input_data)
        elif action == "quick_triage":
            return await self._quick_triage(input_data)
        elif action == "route_department":
            return await self._route_department(input_data)
        else:
            return await self._full_triage(input_data)

    async def _full_triage(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        symptoms = input_data.get("symptoms", "")
        vital_signs = input_data.get("vital_signs", {})
        patient_age = input_data.get("patient_age", 35)
        patient_gender = input_data.get("patient_gender", "unknown")
        pain_level = input_data.get("pain_level", 0)
        medical_history = input_data.get("medical_history", [])

        # Rule-based pre-screening for critical symptoms
        is_critical = self._check_critical(symptoms)
        rule_based_score = self._calculate_rule_score(symptoms, vital_signs, patient_age, pain_level)

        messages = [
            {"role": "system", "content": self.TRIAGE_SYSTEM_PROMPT},
            {"role": "user", "content": f"""Triage this patient:

Symptoms: {symptoms}
Vital Signs: {json.dumps(vital_signs)}
Age: {patient_age}, Gender: {patient_gender}
Pain Level: {pain_level}/10
Medical History: {', '.join(medical_history) if medical_history else 'None reported'}
Rule-based pre-screen: {'CRITICAL FLAG' if is_critical else f'Score: {rule_based_score:.2f}'}

Provide complete triage assessment as JSON."""}
        ]

        response = await self.llm.complete(
            task_type="triage",
            messages=messages,
            temperature=0.1,
        )

        try:
            ai_triage = json.loads(response["content"])
        except json.JSONDecodeError:
            ai_triage = {
                "urgency_level": "critical" if is_critical else self._score_to_level(rule_based_score),
                "urgency_score": 1.0 if is_critical else rule_based_score,
                "preliminary_assessment": response["content"],
            }

        # Rules always override AI for safety (critical cases)
        if is_critical and ai_triage.get("urgency_level") != "critical":
            ai_triage["urgency_level"] = "critical"
            ai_triage["urgency_score"] = max(ai_triage.get("urgency_score", 0), 0.95)
            ai_triage["requires_immediate_intervention"] = True
            ai_triage["clinical_reasoning"] = (
                ai_triage.get("clinical_reasoning", "") +
                " [RULE OVERRIDE: Critical symptoms detected — safety rules supersede AI assessment]"
            )

        # Route to department
        department = ai_triage.get("recommended_department", self._route_by_symptoms(symptoms))
        ai_triage["recommended_department"] = department

        # Store in shared memory
        patient_id = input_data.get("patient_id", "unknown")
        self.memory.update_patient_context(patient_id, {
            "triage": ai_triage,
            "triage_agent": self.name,
        }, self.name)

        # Escalate critical cases
        if ai_triage.get("urgency_level") == "critical":
            self.escalate(
                reason=f"CRITICAL triage: {ai_triage.get('preliminary_assessment', 'Critical symptoms detected')}",
                patient_id=patient_id,
                data=ai_triage,
            )

        return {
            "status": "triage_completed",
            "patient_id": patient_id,
            "triage": ai_triage,
            "rule_based_score": rule_based_score,
            "is_critical_flag": is_critical,
            "handoff_to": "clinical_doc_agent" if ai_triage.get("urgency_level") != "non_urgent" else None,
            "model_used": response["model"],
            "tokens_used": response["tokens"],
        }

    async def _quick_triage(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        symptoms = input_data.get("symptoms", "")
        is_critical = self._check_critical(symptoms)
        score = self._calculate_rule_score(
            symptoms,
            input_data.get("vital_signs", {}),
            input_data.get("patient_age", 35),
            input_data.get("pain_level", 0)
        )

        return {
            "status": "quick_triage_completed",
            "urgency_level": "critical" if is_critical else self._score_to_level(score),
            "urgency_score": 1.0 if is_critical else score,
            "recommended_department": self._route_by_symptoms(symptoms),
            "is_critical": is_critical,
            "model_used": "rule-based",
            "tokens_used": 0,
        }

    async def _route_department(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        symptoms = input_data.get("symptoms", "")
        department = self._route_by_symptoms(symptoms)
        return {
            "status": "routed",
            "department": department,
            "model_used": "rule-based",
            "tokens_used": 0,
        }

    def _check_critical(self, symptoms: str) -> bool:
        symptoms_lower = symptoms.lower()
        return any(cs in symptoms_lower for cs in self.CRITICAL_SYMPTOMS)

    def _calculate_rule_score(self, symptoms: str, vitals: Dict, age: int, pain: int) -> float:
        score = 0.2  # base

        symptoms_lower = symptoms.lower()
        if any(cs in symptoms_lower for cs in self.CRITICAL_SYMPTOMS):
            score += 0.5
        elif any(es in symptoms_lower for es in self.EMERGENCY_SYMPTOMS):
            score += 0.3

        # Vital sign scoring
        hr = vitals.get("heart_rate", 80)
        if hr and (hr < 50 or hr > 120):
            score += 0.15
        sbp = vitals.get("systolic_bp", 120)
        if sbp and (sbp < 90 or sbp > 180):
            score += 0.15
        spo2 = vitals.get("oxygen_saturation", 98)
        if spo2 and spo2 < 92:
            score += 0.2
        temp = vitals.get("temperature", 98.6)
        if temp and (temp > 103 or temp < 95):
            score += 0.1

        # Age risk
        if age < 12 or age > 70:
            score += 0.1

        # Pain
        if pain >= 9:
            score += 0.15
        elif pain >= 7:
            score += 0.1

        return min(score, 1.0)

    def _score_to_level(self, score: float) -> str:
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "emergency"
        elif score >= 0.4:
            return "urgent"
        elif score >= 0.2:
            return "semi_urgent"
        return "non_urgent"

    def _route_by_symptoms(self, symptoms: str) -> str:
        symptoms_lower = symptoms.lower()
        for dept, keywords in self.DEPARTMENT_ROUTING.items():
            if any(kw in symptoms_lower for kw in keywords):
                return dept
        return "internal_medicine"
