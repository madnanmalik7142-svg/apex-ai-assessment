import re
from typing import Optional, Dict, Any
from app.schemas.router import IntentEnum, RoutingResult, SafetyCheckResult
from app.services.guardrails import GuardrailService


class IntentRouter:
    """
    Intent Router & Workflow Classifier.
    Evaluates guardrails, classifies patient intent with English & Arabic keyword support,
    and extracts appointment entities.
    """

    DEPARTMENT_NAMES = ["dental", "cardiology", "pediatrics", "general practice", "dermatology", "orthopedics"]

    def __init__(self):
        self.guardrails = GuardrailService()

    def route(self, message: str, safety_result: Optional[SafetyCheckResult] = None) -> RoutingResult:
        # Step 1: Run Guardrail Checks if not provided
        if safety_result is None:
            safety = self.guardrails.evaluate(message)
        else:
            safety = safety_result

        if safety.is_emergency:
            return RoutingResult(
                intent=IntentEnum.EMERGENCY,
                confidence=1.0,
                safety=safety
            )

        if not safety.is_safe:
            return RoutingResult(
                intent=IntentEnum.OUT_OF_SCOPE,
                confidence=1.0,
                safety=safety
            )

        if safety.should_escalate:
            return RoutingResult(
                intent=IntentEnum.ESCALATE,
                confidence=1.0,
                safety=safety
            )

        # Step 2: Intent Classification via Pattern Matching
        msg_lower = message.lower()

        # Cancellation
        if any(w in msg_lower for w in ["cancel", "إلغاء", "void appointment"]):
            intent = IntentEnum.CANCEL
            confidence = 0.9

        # Rescheduling
        elif any(w in msg_lower for w in ["reschedule", "change time", "move appointment", "تغيير الموعد"]):
            intent = IntentEnum.RESCHEDULE
            confidence = 0.9

        # Booking
        elif any(w in msg_lower for w in ["book", "schedule an appointment", "reserve", "حجز"]):
            intent = IntentEnum.BOOK
            confidence = 0.95

        # Availability
        elif any(w in msg_lower for w in ["available", "slots", "openings", "free times", "المواعيد المتاحة"]):
            intent = IntentEnum.AVAILABILITY
            confidence = 0.9

        # Preparation instructions
        elif any(w in msg_lower for w in ["fasting", "prepare", "prep", "ultrasound prep", "blood test instructions"]):
            intent = IntentEnum.PREPARATION
            confidence = 0.85

        # Insurance
        elif any(w in msg_lower for w in ["insurance", "cchi", "copay", "coverage", "approval", "تأمين"]):
            intent = IntentEnum.INSURANCE
            confidence = 0.85

        else:
            intent = IntentEnum.GENERAL
            confidence = 0.60

        # Step 3: Entity Extraction (Appointment IDs, Slot IDs, Patient IDs, Departments, Doctor names, Dates)
        entities: Dict[str, Any] = {}

        # Match Appointment ID (APT-XXXX or APP-XXXX)
        app_id_match = re.search(r"\b(apt|app)-[a-zA-Z0-9]+\b", msg_lower)
        if app_id_match:
            entities["appointment_id"] = app_id_match.group(0).upper()

        # Match Slot ID (SLOT-XXXX)
        slot_match = re.search(r"\bslot-[a-zA-Z0-9]+\b", msg_lower)
        if slot_match:
            entities["slot_id"] = slot_match.group(0).upper()

        # Match Patient ID (PAT-XXXX)
        pat_match = re.search(r"\bpat-[a-zA-Z0-9]+\b", msg_lower)
        if pat_match:
            entities["patient_id"] = pat_match.group(0).upper()

        # Match Department
        for dept in self.DEPARTMENT_NAMES:
            if dept in msg_lower:
                entities["department"] = dept.title()
                break

        # Match Doctor Name from original case message to preserve exact capitalization (e.g. Dr. Sarah Al-Otaibi)
        doc_match = re.search(r"\b(Dr\.|Doctor)\s+([A-Z][a-zA-Z\-]+(?:\s+[A-Z][a-zA-Z\-]+)*)", message)
        if doc_match:
            entities["doctor_name"] = doc_match.group(0)

        # Match Date
        date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", msg_lower)
        if date_match:
            entities["date"] = date_match.group(0)
        elif "tomorrow" in msg_lower:
            entities["date"] = "tomorrow"
        elif "today" in msg_lower:
            entities["date"] = "today"

        return RoutingResult(
            intent=intent,
            confidence=confidence,
            safety=safety,
            extracted_entities=entities
        )


# Alias for backward compatibility
WorkflowRouter = IntentRouter
intent_router = IntentRouter()
workflow_router = intent_router
