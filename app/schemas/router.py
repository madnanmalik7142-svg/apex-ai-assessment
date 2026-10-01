from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class IntentEnum(str, Enum):
    BOOK = "book_appointment"
    RESCHEDULE = "reschedule_appointment"
    CANCEL = "cancel_appointment"
    AVAILABILITY = "check_availability"
    PREPARATION = "preparation_instructions"
    INSURANCE = "insurance_policy"
    GENERAL = "general_query"
    EMERGENCY = "medical_emergency"
    ESCALATE = "human_escalation"
    OUT_OF_SCOPE = "out_of_scope"


class SafetyCheckResult(BaseModel):
    is_safe: bool = Field(..., description="False if emergency or prompt injection/violating input detected")
    trigger_reason: Optional[str] = Field(default=None, description="Reason for safety flag")
    is_emergency: bool = Field(default=False, description="True if red-flag symptoms detected")
    should_escalate: bool = Field(default=False, description="True if human agent transfer is required")


class RoutingResult(BaseModel):
    intent: IntentEnum
    confidence: float = Field(..., ge=0.0, le=1.0)
    safety: SafetyCheckResult
    extracted_entities: dict = Field(default_factory=dict, description="Extracted dates, IDs, specialty")
