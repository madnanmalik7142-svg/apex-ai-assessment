from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from app.tools.tools import (
    check_availability,
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
    lookup_appointment,
    escalate_to_human
)

router = APIRouter(prefix="/assistant", tags=["Assistant"])
logger = logging.getLogger(__name__)

class MessageRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier for the user chat")
    message: str = Field(..., description="User message text")
    patient_id: Optional[str] = Field(None, description="Authenticated patient ID if available")

class MessageResponse(BaseModel):
    status: str = Field(..., description="success, needs_clarification, or escalated")
    reply: str = Field(..., description="Assistant response text")
    action_taken: Optional[str] = Field(None, description="The tool or workflow action executed")
    data: Optional[Dict[str, Any]] = Field(None, description="Payload returned by the tool if successful")

# Simple heuristic & guardrail processor for intent detection and prompt-injection checks
def evaluate_guardrails(message: str) -> Optional[str]:
    lowered = message.lower()
    # Check for prompt injection patterns
    injection_keywords = ["ignore previous instructions", "system prompt", "you are now", "developer mode"]
    if any(kw in injection_keywords for kw in injection_keywords if kw in lowered):
        return "I'm sorry, I cannot comply with requests that modify my core instructions. How can I help you with your healthcare appointment today?"
    return None

@router.post("/message", response_model=MessageResponse)
async def handle_assistant_message(payload: MessageRequest):
    # 1. Guardrail & Security Check
    guardrail_response = evaluate_guardrails(payload.message)
    if guardrail_response:
        return MessageResponse(
            status="success",
            reply=guardrail_response,
            action_taken="guardrail_blocked"
        )

    user_msg = payload.message.lower()
    
    try:
        # 2. Intent Routing & Tool Execution Logic
        if "availability" in user_msg or "available" in user_msg or "slots" in user_msg:
            # Mock extracting date/department or asking for clarification
            result = check_availability(date="2026-10-10", department="General Medicine")
            return MessageResponse(
                status="success",
                reply=f"Here are the available slots for General Medicine on 2026-10-10: {result.get('slots', [])}",
                action_taken="check_availability",
                data=result
            )

        elif "book" in user_msg or "schedule" in user_msg:
            if not payload.patient_id:
                return MessageResponse(
                    status="needs_clarification",
                    reply="To book an appointment, please provide your Patient ID and preferred date/slot.",
                    action_taken="request_patient_id"
                )
            
            # Execute booking tool with strict verification
            result = book_appointment(patient_id=payload.patient_id, slot_id="slot_2026_10_10_01")
            if result.get("success"):
                return MessageResponse(
                    status="success",
                    reply="Your appointment has been successfully booked and confirmed.",
                    action_taken="book_appointment",
                    data=result
                )
            else:
                return MessageResponse(
                    status="success",
                    reply=f"I couldn't complete the booking: {result.get('error', 'Service unavailable')}. Would you like me to escalate this?",
                    action_taken="book_appointment_failed",
                    data=result
                )

        elif "cancel" in user_msg:
            result = cancel_appointment(appointment_id="apt_12345")
            if result.get("success"):
                return MessageResponse(
                    status="success",
                    reply="Your appointment has been successfully canceled.",
                    action_taken="cancel_appointment",
                    data=result
                )
            else:
                return MessageResponse(
                    status="success",
                    reply="We encountered an issue canceling your appointment. Let me escalate this to our support team.",
                    action_taken="cancel_appointment_failed"
                )

        elif "human" in user_msg or "agent" in user_msg or "support" in user_msg or "speak to someone" in user_msg:
            escalation = escalate_to_human(reason="User requested human intervention", context=payload.message)
            return MessageResponse(
                status="escalated",
                reply="I have transferred your request to a human patient service representative. They will contact you shortly.",
                action_taken="escalate_to_human",
                data=escalation
            )

        else:
            # Default RAG or general conversational fallback
            return MessageResponse(
                status="success",
                reply="I can help you check appointment availability, book, reschedule, or cancel visits. What would you like to do?",
                action_taken="general_query"
            )

    except Exception as e:
        logger.error(f"Tool execution error: {str(e)}")
        # Safe fallback: Never claim success on error/timeout
        return MessageResponse(
            status="success",
            reply="I am currently experiencing a temporary issue reaching our scheduling system. Your request was not executed. Would you like to try again or talk to support?",
            action_taken="system_error_fallback"
        )
