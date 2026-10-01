import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.config import settings
from app.schemas.chat import HealthCheckResponse
from app.services.assistant_service import assistant_orchestrator
from app.tools.tools import (
    check_availability,
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
    lookup_appointment,
    escalate_to_human
)

router = APIRouter(tags=["Assistant"])
logger = logging.getLogger(__name__)


class MessageRequest(BaseModel):
    session_id: Optional[str] = Field(default="sess_default", description="Unique session identifier for the user chat")
    message: str = Field(..., min_length=1, description="User message text")
    patient_id: Optional[str] = Field(None, description="Authenticated patient ID if available")


class MessageResponse(BaseModel):
    status: str = Field(..., description="success, needs_clarification, failed, or escalated")
    reply: str = Field(..., description="Assistant response text")
    action_taken: Optional[str] = Field(None, description="The tool or workflow action executed")
    data: Optional[Dict[str, Any]] = Field(None, description="Payload returned by the tool if successful")
    session_id: Optional[str] = Field(default="sess_default", description="Session ID tracking")
    intent: Optional[str] = Field(default="general_query", description="Classified intent")
    escalated: Optional[bool] = Field(default=False, description="Whether escalation was triggered")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata trace")


def evaluate_guardrails(message: str) -> Optional[str]:
    lowered = message.lower()
    injection_keywords = ["ignore previous instructions", "system prompt", "you are now", "developer mode"]
    if any(kw in lowered for kw in injection_keywords):
        return "I'm sorry, I cannot comply with requests that modify my core instructions. How can I help you with your healthcare appointment today?"
    return None


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Service Health Check",
    tags=["Health"]
)
async def health_check() -> HealthCheckResponse:
    """Return health status of the API service."""
    return HealthCheckResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT
    )


@router.post(
    "/assistant/message",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Process Patient Message",
    description="Main entry point for assistant message processing."
)
async def handle_assistant_message(payload: MessageRequest):
    """
    Process patient message through guardrail evaluation and multi-step workflow orchestrator.
    """
    # 1. Guardrail & Security Check for Injection Patterns
    guardrail_response = evaluate_guardrails(payload.message)
    if guardrail_response:
        return MessageResponse(
            status="success",
            reply=guardrail_response,
            action_taken="guardrail_blocked",
            session_id=payload.session_id,
            intent="out_of_scope",
            escalated=False,
            data={"blocked": True}
        )

    try:
        # Delegate to multi-step AssistantOrchestrator
        orchestration_request = payload
        from app.schemas.chat import ChatRequest
        chat_req = ChatRequest(
            message=payload.message,
            patient_id=payload.patient_id,
            session_id=payload.session_id
        )
        res = await assistant_orchestrator.process_message(chat_req)

        return MessageResponse(
            status=res.status,
            reply=res.reply,
            action_taken=res.intent,
            data=res.metadata,
            session_id=res.session_id,
            intent=res.intent,
            escalated=res.escalated,
            metadata=res.metadata
        )

    except Exception as e:
        logger.error(f"Tool execution error: {str(e)}")
        # Safe fallback: Never claim success on error/timeout
        return MessageResponse(
            status="failed",
            reply="I am currently experiencing a temporary issue reaching our scheduling system. Your request was not executed. Would you like to try again or talk to support?",
            action_taken="system_error_fallback",
            session_id=payload.session_id,
            intent="system_error",
            escalated=False,
            data={"error": str(e)}
        )
