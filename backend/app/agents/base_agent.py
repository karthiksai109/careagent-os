"""
Base Agent — Abstract base class for all CareAgent OS agents.
Every agent has: name, type, shared memory access, LLM routing, activity logging.
"""
import uuid
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from app.services.llm_router import llm_router


class SharedMemory:
    """Blackboard-style shared memory for inter-agent communication."""

    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._history: List[Dict] = []

    def write(self, key: str, value: Any, agent_name: str):
        self._store[key] = value
        self._history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent_name,
            "action": "write",
            "key": key,
        })

    def read(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def get_patient_context(self, patient_id: str) -> Dict:
        return self._store.get(f"patient:{patient_id}", {})

    def update_patient_context(self, patient_id: str, data: Dict, agent_name: str):
        existing = self.get_patient_context(patient_id)
        existing.update(data)
        self.write(f"patient:{patient_id}", existing, agent_name)

    def get_history(self, limit: int = 50) -> List[Dict]:
        return self._history[-limit:]

    @property
    def all_keys(self) -> List[str]:
        return list(self._store.keys())


# Global shared memory instance
shared_memory = SharedMemory()


class BaseAgent(ABC):
    """Abstract base class for all CareAgent OS agents."""

    def __init__(self, name: str, agent_type: str, description: str):
        self.name = name
        self.agent_type = agent_type
        self.description = description
        self.memory = shared_memory
        self.llm = llm_router
        self._activity_log: List[Dict] = []
        self._status = "idle"
        self._tasks_completed = 0
        self._tasks_failed = 0

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task. Must be implemented by each agent."""
        pass

    @abstractmethod
    async def can_handle(self, task_type: str) -> bool:
        """Check if this agent can handle a given task type."""
        pass

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with logging, timing, and error handling."""
        activity_id = str(uuid.uuid4())
        start_time = time.time()
        self._status = "running"

        activity = {
            "id": activity_id,
            "agent_name": self.name,
            "agent_type": self.agent_type,
            "action": input_data.get("action", "process"),
            "status": "running",
            "patient_id": input_data.get("patient_id"),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "input_summary": self._summarize_input(input_data),
        }

        try:
            result = await self.process(input_data)
            duration_ms = int((time.time() - start_time) * 1000)

            activity.update({
                "status": "completed",
                "duration_ms": duration_ms,
                "output_summary": self._summarize_output(result),
                "model_used": result.get("model_used", ""),
                "tokens_used": result.get("tokens_used", 0),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })

            self._tasks_completed += 1
            self._status = "idle"

            result["activity_id"] = activity_id
            result["agent_name"] = self.name
            result["duration_ms"] = duration_ms

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            activity.update({
                "status": "failed",
                "duration_ms": duration_ms,
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })

            self._tasks_failed += 1
            self._status = "error"

            result = {
                "activity_id": activity_id,
                "agent_name": self.name,
                "status": "failed",
                "error": str(e),
                "duration_ms": duration_ms,
            }

        self._activity_log.append(activity)
        return result

    def escalate(self, reason: str, patient_id: Optional[str] = None, data: Optional[Dict] = None):
        """Escalate to human with full reasoning chain."""
        escalation = {
            "id": str(uuid.uuid4()),
            "agent_name": self.name,
            "reason": reason,
            "patient_id": patient_id,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.memory.write(f"escalation:{escalation['id']}", escalation, self.name)
        return escalation

    def _summarize_input(self, data: Dict) -> str:
        keys = list(data.keys())[:5]
        return f"Keys: {', '.join(keys)}"

    def _summarize_output(self, data: Dict) -> str:
        status = data.get("status", "unknown")
        return f"Status: {status}"

    @property
    def stats(self) -> Dict:
        return {
            "name": self.name,
            "type": self.agent_type,
            "status": self._status,
            "tasks_completed": self._tasks_completed,
            "tasks_failed": self._tasks_failed,
            "recent_activities": self._activity_log[-10:],
        }

    @property
    def recent_activities(self) -> List[Dict]:
        return self._activity_log[-20:]
