import uuid
import logging
from typing import Optional, Dict, Any
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.router import IntentEnum, RoutingResult
from app.schemas.tools import (
    AvailabilityQuery,
    BookingRequest,
    RescheduleRequest,
    CancelRequest
)
from app.services.guardrails import GuardrailService
from app.services.router import IntentRouter
from app.services.appointment_service import AppointmentService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class AssistantOrchestrator:
    """
    End-to-End Multi-Step Assistant Orchestrator.
    Executes Guardrails -> Router -> (Appointment Tools / RAG Knowledge Service / Escalation) -> Structured Output.
    Enforces strict safety protocols, parameter clarification loops, and tool success confirmations.
    """

    def __init__(
        self,
        guardrail_service: Optional[GuardrailService] = None,
        router_service: Optional[IntentRouter] = None,
        rag_service: Optional[RAGService] = None,
        appointment_service: Optional[AppointmentService] = None,
    ):
        self.guardrails = guardrail_service or GuardrailService()
        self.router = router_service or IntentRouter()
        self.rag = rag_service or RAGService()
        self.appointment_service = appointment_service or AppointmentService()

    async def process_message(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or f"sess_{uuid.uuid4().hex[:8]}"
        message = request.message.strip()
        patient_id = request.patient_id or "P_GUEST"
        metadata = request.metadata or {}

        try:
            # Step 1: Safety & Guardrails + Intent Routing with Entity Extraction
            routing: RoutingResult = self.router.route(message)
            safety = routing.safety
            extracted = routing.extracted_entities

            # Handle Medical Emergency Protocol (Red Crescent 997)
            if safety.is_emergency:
                return ChatResponse(
                    session_id=session_id,
                    reply=(
                        "⚠️ CRITICAL MEDICAL NOTICE: Based on your symptoms, please seek immediate emergency care. "
                        "Call Saudi Red Crescent at 997 or go to the nearest hospital emergency room immediately."
                    ),
                    intent=IntentEnum.EMERGENCY.value,
                    status="emergency_diverted",
                    escalated=True,
                    metadata={"emergency": True, "call_emergency": "997", "trigger_reason": safety.trigger_reason}
                )

            # Handle Out of Scope / Misuse / Injection Attempts
            if not safety.is_safe:
                return ChatResponse(
                    session_id=session_id,
                    reply=(
                        "I am an AI Healthcare Assistant for Apex AI Arabia. I can only assist with appointment "
                        "booking, rescheduling, cancellations, clinic guidance, and test preparation instructions."
                    ),
                    intent=IntentEnum.OUT_OF_SCOPE.value,
                    status="rejected",
                    escalated=False,
                    metadata={"out_of_scope": True, "trigger_reason": safety.trigger_reason}
                )

            # Handle Explicit Human Escalation Request
            if safety.should_escalate or routing.intent == IntentEnum.ESCALATE:
                return ChatResponse(
                    session_id=session_id,
                    reply="Connecting you with a human patient service representative. Please stay on the line.",
                    intent=IntentEnum.ESCALATE.value,
                    status="escalated",
                    escalated=True,
                    metadata={"escalated_human": True, "trigger_reason": safety.trigger_reason}
                )

            # Step 2: Multi-Step Appointment Workflows with Clarification Loops
            intent = routing.intent

            # --- A. Check Availability Workflow ---
            if intent == IntentEnum.AVAILABILITY:
                dept = metadata.get("specialty") or metadata.get("department") or extracted.get("department")
                date = metadata.get("date") or extracted.get("date")
                doc = metadata.get("doctor_name") or extracted.get("doctor_name")

                query = AvailabilityQuery(department=dept, date=date, doctor_name=doc)
                avail_res = self.appointment_service.check_availability(query)

                if not avail_res.slots:
                    reply_text = f"No available slots currently found for {dept or 'your request'}."
                else:
                    formatted_slots = ", ".join([f"{s.slot_id} ({s.department}, {s.doctor_name} at {s.datetime})" for s in avail_res.slots[:3]])
                    reply_text = f"Available slots: {formatted_slots}."

                return ChatResponse(
                    session_id=session_id,
                    reply=reply_text,
                    intent=intent.value,
                    status="success",
                    escalated=False,
                    metadata={"slots_count": len(avail_res.slots), "entities": extracted}
                )

            # --- B. Booking Workflow ---
            elif intent == IntentEnum.BOOK:
                slot_id = metadata.get("slot_id") or extracted.get("slot_id")
                pid = extracted.get("patient_id") or patient_id

                # Clarification step if mandatory slot_id parameter is missing
                if not slot_id:
                    avail_res = self.appointment_service.check_availability(
                        AvailabilityQuery(department=extracted.get("department"))
                    )
                    slots_hint = ", ".join([s.slot_id for s in avail_res.slots[:3]]) if avail_res.slots else "SLOT-101"
                    return ChatResponse(
                        session_id=session_id,
                        reply=f"To book an appointment, please specify your desired slot ID (e.g., {slots_hint}).",
                        intent=intent.value,
                        status="needs_clarification",
                        escalated=False,
                        metadata={"missing_parameter": "slot_id", "entities": extracted}
                    )

                # Execute Booking Tool
                book_req = BookingRequest(
                    patient_id=pid,
                    patient_name="Patient",
                    patient_phone="+966500000000",
                    slot_id=slot_id
                )
                res = self.appointment_service.book_appointment(book_req)

                # STRICT CONFIRMATION RULE: Success only if tool confirms
                if res.success and res.appointment:
                    return ChatResponse(
                        session_id=session_id,
                        reply=f"Successfully booked appointment! Confirmation ID: {res.appointment.appointment_id}. Details: {res.message}",
                        intent=intent.value,
                        status="success",
                        escalated=False,
                        metadata={"tool_success": True, "appointment_id": res.appointment.appointment_id}
                    )
                else:
                    return ChatResponse(
                        session_id=session_id,
                        reply=f"Booking failed: {res.message}",
                        intent=intent.value,
                        status="failed",
                        escalated=False,
                        metadata={"tool_success": False, "error": res.message}
                    )

            # --- C. Cancellation Workflow ---
            elif intent == IntentEnum.CANCEL:
                app_id = metadata.get("appointment_id") or extracted.get("appointment_id")
                pid = extracted.get("patient_id") or patient_id

                # Clarification step if appointment_id is missing
                if not app_id:
                    return ChatResponse(
                        session_id=session_id,
                        reply="Please provide your Appointment ID (e.g., APP-101 or APT-8001) to process the cancellation.",
                        intent=intent.value,
                        status="needs_clarification",
                        escalated=False,
                        metadata={"missing_parameter": "appointment_id", "entities": extracted}
                    )

                cancel_req = CancelRequest(appointment_id=app_id, patient_id=pid)
                res = self.appointment_service.cancel_appointment(cancel_req)

                if res.success:
                    return ChatResponse(
                        session_id=session_id,
                        reply=f"Appointment {app_id} has been canceled successfully.",
                        intent=intent.value,
                        status="success",
                        escalated=False,
                        metadata={"tool_success": True, "appointment_id": app_id}
                    )
                else:
                    return ChatResponse(
                        session_id=session_id,
                        reply=f"Cancellation failed: {res.message}",
                        intent=intent.value,
                        status="failed",
                        escalated=False,
                        metadata={"tool_success": False, "error": res.message}
                    )

            # --- D. Rescheduling Workflow ---
            elif intent == IntentEnum.RESCHEDULE:
                app_id = metadata.get("appointment_id") or extracted.get("appointment_id")
                new_slot = metadata.get("new_slot_id") or metadata.get("slot_id") or extracted.get("slot_id")
                pid = extracted.get("patient_id") or patient_id

                if not app_id or not new_slot:
                    return ChatResponse(
                        session_id=session_id,
                        reply="To reschedule, please specify both your current Appointment ID (e.g., APT-8001) and your new desired Slot ID (e.g., SLOT-102).",
                        intent=intent.value,
                        status="needs_clarification",
                        escalated=False,
                        metadata={"missing_parameters": ["appointment_id", "new_slot_id"], "entities": extracted}
                    )

                reschedule_req = RescheduleRequest(appointment_id=app_id, patient_id=pid, new_slot_id=new_slot)
                res = self.appointment_service.reschedule_appointment(reschedule_req)

                if res.success:
                    return ChatResponse(
                        session_id=session_id,
                        reply=f"Appointment {app_id} successfully rescheduled to slot {new_slot}.",
                        intent=intent.value,
                        status="success",
                        escalated=False,
                        metadata={"tool_success": True, "appointment_id": app_id, "new_slot_id": new_slot}
                    )
                else:
                    return ChatResponse(
                        session_id=session_id,
                        reply=f"Rescheduling failed: {res.message}",
                        intent=intent.value,
                        status="failed",
                        escalated=False,
                        metadata={"tool_success": False, "error": res.message}
                    )

            # --- E. Knowledge Base RAG Search (Preparation, Insurance, General) ---
            elif intent in [IntentEnum.PREPARATION, IntentEnum.INSURANCE, IntentEnum.GENERAL]:
                rag_res = self.rag.search(query=message)
                if rag_res.has_match and rag_res.results:
                    top_doc = rag_res.results[0].document
                    reply_text = f"[{top_doc.topic}]: {top_doc.content}"
                    return ChatResponse(
                        session_id=session_id,
                        reply=reply_text,
                        intent=intent.value,
                        status="success",
                        escalated=False,
                        metadata={"rag_match": True, "document_id": top_doc.id}
                    )
                else:
                    reply_text = "I couldn't find specific information regarding your request in our knowledge base. Transferring to patient assistance."
                    return ChatResponse(
                        session_id=session_id,
                        reply=reply_text,
                        intent=intent.value,
                        status="escalated",
                        escalated=True,
                        metadata={"rag_match": False}
                    )

            # Default Fallback
            return ChatResponse(
                session_id=session_id,
                reply="I am here to assist with your healthcare needs. How can I help you today?",
                intent=IntentEnum.GENERAL.value,
                status="success",
                escalated=False
            )

        except Exception as e:
            logger.exception("Unexpected error in AssistantOrchestrator")
            return ChatResponse(
                session_id=session_id,
                reply=f"An error occurred while processing your request: {str(e)}. Please try again or contact support.",
                intent="system_error",
                status="failed",
                escalated=False,
                metadata={"error": str(e)}
            )


# Singleton instance
assistant_orchestrator = AssistantOrchestrator()
