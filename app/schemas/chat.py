from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="The patient's message or query to the assistant",
        examples=["Hello, I would like to book a dental appointment for tomorrow."]
    )
    patient_id: Optional[str] = Field(
        default=None,
        description="Optional unique identifier for the patient",
        examples=["PAT-10023"]
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session identifier to track multi-turn conversation state",
        examples=["sess_abc123"]
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional context metadata (e.g., specialty, slot_id, appointment_id)"
    )


class ChatResponse(BaseModel):
    session_id: Optional[str] = Field(
        default="sess_default",
        description="Session identifier tracking this conversation session",
        examples=["sess_abc123"]
    )
    reply: str = Field(
        ...,
        description="The assistant's response to the patient",
        examples=["Hello! How can I assist you with your healthcare needs today?"]
    )
    intent: str = Field(
        default="general_query",
        description="Identified user intent or workflow stage",
        examples=["general_query"]
    )
    status: str = Field(
        default="success",
        description="Execution status (success, failed, escalated, emergency_diverted, needs_clarification, rejected)",
        examples=["success"]
    )
    escalated: bool = Field(
        default=False,
        description="True if human escalation or emergency transfer was triggered",
        examples=[False]
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional execution metadata (e.g. tools invoked, RAG matches, entities)"
    )


# Aliases for API & testing backward compatibility
MessageRequest = ChatRequest
MessageResponse = ChatResponse


class HealthCheckResponse(BaseModel):
    status: str = Field(default="healthy", examples=["healthy"])
    app_name: str = Field(..., examples=["Saudi Healthcare Patient Service Assistant"])
    environment: str = Field(..., examples=["development"])
