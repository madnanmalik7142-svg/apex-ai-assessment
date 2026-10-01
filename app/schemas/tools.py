from typing import Optional, List
from pydantic import BaseModel, Field


# --- Availability Schemas ---
class AvailabilityQuery(BaseModel):
    department: Optional[str] = Field(
        default=None,
        description="Medical department (e.g. Dental, General Practice, Cardiology)",
        examples=["Dental"]
    )
    date: Optional[str] = Field(
        default=None,
        description="Target date for appointment in YYYY-MM-DD format",
        examples=["2026-10-02"]
    )
    doctor_name: Optional[str] = Field(
        default=None,
        description="Preferred doctor name",
        examples=["Dr. Sarah Al-Otaibi"]
    )


class SlotInfo(BaseModel):
    slot_id: str = Field(..., examples=["SLOT-101"])
    department: str = Field(..., examples=["Dental"])
    doctor_name: str = Field(..., examples=["Dr. Sarah Al-Otaibi"])
    datetime: str = Field(..., examples=["2026-10-02 09:00"])
    is_available: bool = Field(default=True, examples=[True])


class AvailabilityResponse(BaseModel):
    success: bool = Field(..., description="Whether query was processed successfully")
    slots: List[SlotInfo] = Field(default_factory=list, description="List of matching available slots")
    message: str = Field(..., description="Human-readable status summary")


# --- Shared Appointment Details Schema ---
class AppointmentDetails(BaseModel):
    appointment_id: str = Field(..., examples=["APT-8001"])
    patient_id: str = Field(..., examples=["PAT-10023"])
    patient_name: str = Field(..., examples=["Nasser Al-Subaie"])
    doctor_name: str = Field(..., examples=["Dr. Sarah Al-Otaibi"])
    department: str = Field(..., examples=["Dental"])
    datetime: str = Field(..., examples=["2026-10-02 09:00"])
    status: str = Field(..., description="Status of appointment (confirmed, cancelled)", examples=["confirmed"])


# --- Booking Schemas ---
class BookingRequest(BaseModel):
    patient_id: str = Field(..., min_length=1, description="Patient unique ID", examples=["PAT-10023"])
    patient_name: str = Field(..., min_length=1, description="Patient full name", examples=["Nasser Al-Subaie"])
    patient_phone: str = Field(..., min_length=8, description="Patient phone number", examples="+966500000000")
    slot_id: str = Field(..., min_length=1, description="Slot ID to book", examples=["SLOT-101"])
    notes: Optional[str] = Field(default=None, description="Optional clinical or administrative notes")


class BookingResponse(BaseModel):
    success: bool = Field(..., description="Explicit booking confirmation status")
    appointment: Optional[AppointmentDetails] = Field(default=None, description="Confirmed appointment details if success is True")
    message: str = Field(..., description="Status message detailing outcome")


# --- Rescheduling Schemas ---
class RescheduleRequest(BaseModel):
    appointment_id: str = Field(..., min_length=1, description="Existing appointment ID", examples=["APT-8001"])
    patient_id: str = Field(..., min_length=1, description="Patient ID for ownership verification", examples=["PAT-10023"])
    new_slot_id: str = Field(..., min_length=1, description="New slot ID requested", examples=["SLOT-102"])


class RescheduleResponse(BaseModel):
    success: bool = Field(..., description="Explicit rescheduling confirmation status")
    updated_appointment: Optional[AppointmentDetails] = Field(default=None, description="Updated appointment details if success is True")
    message: str = Field(..., description="Status message detailing outcome")


# --- Cancellation Schemas ---
class CancelRequest(BaseModel):
    appointment_id: str = Field(..., min_length=1, description="Appointment ID to cancel", examples=["APT-8001"])
    patient_id: str = Field(..., min_length=1, description="Patient ID for ownership verification", examples=["PAT-10023"])
    reason: Optional[str] = Field(default=None, description="Optional reason for cancellation")


class CancelResponse(BaseModel):
    success: bool = Field(..., description="Explicit cancellation confirmation status")
    appointment_id: str = Field(..., description="Target appointment ID")
    message: str = Field(..., description="Status message detailing outcome")
