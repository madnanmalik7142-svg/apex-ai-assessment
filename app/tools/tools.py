from typing import Optional, Dict, Any
from app.services.appointment_service import appointment_service
from app.schemas.tools import AvailabilityQuery, BookingRequest, RescheduleRequest, CancelRequest


def check_availability(date: Optional[str] = None, department: Optional[str] = None) -> Dict[str, Any]:
    res = appointment_service.check_availability(AvailabilityQuery(date=date, department=department))
    return {
        "success": res.success,
        "message": res.message,
        "slots": [s.model_dump() for s in res.slots]
    }


def book_appointment(patient_id: str, slot_id: str, patient_name: str = "Patient", patient_phone: str = "+966500000000") -> Dict[str, Any]:
    res = appointment_service.book_appointment(BookingRequest(
        patient_id=patient_id,
        patient_name=patient_name,
        patient_phone=patient_phone,
        slot_id=slot_id
    ))
    return {
        "success": res.success,
        "message": res.message,
        "appointment": res.appointment.model_dump() if res.appointment else None,
        "error": None if res.success else res.message
    }


def reschedule_appointment(appointment_id: str, new_slot_id: str, patient_id: str = "PAT-10023") -> Dict[str, Any]:
    res = appointment_service.reschedule_appointment(RescheduleRequest(
        appointment_id=appointment_id,
        patient_id=patient_id,
        new_slot_id=new_slot_id
    ))
    return {
        "success": res.success,
        "message": res.message,
        "updated_appointment": res.updated_appointment.model_dump() if res.updated_appointment else None,
        "error": None if res.success else res.message
    }


def cancel_appointment(appointment_id: str, patient_id: str = "PAT-10023") -> Dict[str, Any]:
    res = appointment_service.cancel_appointment(CancelRequest(
        appointment_id=appointment_id,
        patient_id=patient_id
    ))
    return {
        "success": res.success,
        "message": res.message,
        "appointment_id": res.appointment_id,
        "error": None if res.success else res.message
    }


def lookup_appointment(appointment_id: str) -> Dict[str, Any]:
    apt = appointment_service._appointments.get(appointment_id)
    if apt:
        return {"success": True, "appointment": apt.model_dump()}
    return {"success": False, "message": f"Appointment '{appointment_id}' not found."}


def escalate_to_human(reason: str, context: str) -> Dict[str, Any]:
    return {
        "escalated": True,
        "reason": reason,
        "context": context
    }
