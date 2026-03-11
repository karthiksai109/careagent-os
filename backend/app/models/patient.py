import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(String(10))
    gender = Column(String(20))
    phone = Column(String(20))
    email = Column(String(255))
    address = Column(Text)
    insurance_provider = Column(String(255))
    insurance_id = Column(String(100))
    medical_history = Column(JSON, default=list)
    allergies = Column(JSON, default=list)
    medications = Column(JSON, default=list)
    emergency_contact = Column(String(255))
    emergency_phone = Column(String(20))
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, nullable=False, index=True)
    encounter_type = Column(String(50))  # intake, visit, follow_up, emergency
    status = Column(String(50), default="in_progress")  # in_progress, completed, cancelled
    chief_complaint = Column(Text)
    symptoms = Column(JSON, default=list)
    vital_signs = Column(JSON, default=dict)
    triage_level = Column(String(20))  # critical, emergency, urgent, semi_urgent, non_urgent
    triage_score = Column(Float)
    assigned_department = Column(String(100))
    assigned_provider = Column(String(255))
    soap_notes = Column(JSON, default=dict)
    icd_codes = Column(JSON, default=list)
    prescriptions = Column(JSON, default=list)
    follow_up_plan = Column(JSON, default=dict)
    prior_auth_status = Column(String(50))  # pending, approved, denied, appealing
    prior_auth_details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


class VitalSign(Base):
    __tablename__ = "vital_signs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, nullable=False, index=True)
    encounter_id = Column(String, nullable=True, index=True)
    heart_rate = Column(Integer)
    systolic_bp = Column(Integer)
    diastolic_bp = Column(Integer)
    temperature = Column(Float)
    respiratory_rate = Column(Integer)
    oxygen_saturation = Column(Float)
    pain_level = Column(Integer)
    consciousness = Column(String(20), default="alert")
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AgentActivity(Base):
    __tablename__ = "agent_activities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_name = Column(String(50), nullable=False, index=True)
    agent_type = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    status = Column(String(30), default="running")  # running, completed, failed, escalated
    patient_id = Column(String, nullable=True, index=True)
    encounter_id = Column(String, nullable=True)
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    reasoning = Column(Text)
    model_used = Column(String(100))
    tokens_used = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)
    escalated_to = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, nullable=False, index=True)
    encounter_id = Column(String, nullable=True)
    provider_name = Column(String(255))
    department = Column(String(100))
    appointment_type = Column(String(50))  # initial, follow_up, specialist
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    status = Column(String(30), default="scheduled")  # scheduled, confirmed, completed, cancelled, no_show
    notes = Column(Text)
    reminder_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, nullable=True, index=True)
    agent_name = Column(String(50))
    severity = Column(String(20))  # critical, warning, info
    title = Column(String(255))
    message = Column(Text)
    action_required = Column(Boolean, default=False)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
