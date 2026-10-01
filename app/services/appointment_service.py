import re
import uuid
from typing import Dict, Optional, List
from app.schemas.tools import (
    AvailabilityQuery,
    AvailabilityResponse,
    SlotInfo,
    BookingRequest,
    BookingResponse,
    AppointmentDetails,
    RescheduleRequest,
    RescheduleResponse,
    CancelRequest,
    CancelResponse
)


class AppointmentService:
    """
    In-memory appointment management service implementing mocked appointment tools.
    Guarantees strict tool execution checks and explicit success status reporting.
    """

    def __init__(self):
        # In-memory mock database for slots
        self._slots: Dict[str, SlotInfo] = {
            "SLOT-101": SlotInfo(
                slot_id="SLOT-101",
                department="Dental",
                doctor_name="Dr. Sarah Al-Otaibi",
                datetime="2026-10-02 09:00",
                is_available=True
            ),
            "SLOT-102": SlotInfo(
                slot_id="SLOT-102",
                department="Dental",
                doctor_name="Dr. Sarah Al-Otaibi",
                datetime="2026-10-02 11:30",
                is_available=True
            ),
            "SLOT-103": SlotInfo(
                slot_id="SLOT-103",
                department="General Practice",
                doctor_name="Dr. Ahmed Al-Ghamdi",
                datetime="2026-10-02 10:00",
                is_available=True
            ),
            "SLOT-104": SlotInfo(
                slot_id="SLOT-104",
                department="Cardiology",
                doctor_name="Dr. Khalid Al-Shehri",
                datetime="2026-10-03 14:00",
                is_available=True
            ),
            "SLOT-105": SlotInfo(
                slot_id="SLOT-105",
                department="Dental",
                doctor_name="Dr. Sarah Al-Otaibi",
                datetime="2026-10-03 15:00",
                is_available=True
            ),
            "SLOT-106": SlotInfo(
                slot_id="SLOT-106",
                department="Pediatrics",
                doctor_name="Dr. Mona Al-Hassan",
                datetime="2026-10-04 10:00",
                is_available=True
            ),
        }

        # In-memory mock database for existing booked appointments
        self._appointments: Dict[str, AppointmentDetails] = {
            "APT-8001": AppointmentDetails(
                appointment_id="APT-8001",
                patient_id="PAT-10023",
                patient_name="Nasser Al-Subaie",
                doctor_name="Dr. Ahmed Al-Ghamdi",
                department="General Practice",
                datetime="2026-10-01 14:00",
                status="confirmed"
            )
        }

        # Track which slot belongs to which appointment
        self._appointment_slots: Dict[str, str] = {
            "APT-8001": "SLOT-100"
        }

    def reset_state(self):
        """Reset in-memory data for clean unit testing."""
        self.__init__()

    def check_availability(self, query: AvailabilityQuery) -> AvailabilityResponse:
        """
        Check for available appointment slots filtered by department, date, or doctor name.
        """
        results: List[SlotInfo] = []

        for slot in self._slots.values():
            if not slot.is_available:
                continue

            if query.department and query.department.lower() not in slot.department.lower():
                continue

            if query.doctor_name and query.doctor_name.lower() not in slot.doctor_name.lower():
                continue

            if query.date and re.match(r"^\d{4}-\d{2}-\d{2}", query.date):
                if not slot.datetime.startswith(query.date):
                    continue

            results.append(slot)

        msg = (
            f"Found {len(results)} available slot(s)."
            if results else "No available slots found matching criteria."
        )
        return AvailabilityResponse(
            success=True,
            slots=results,
            message=msg
        )

    def book_appointment(self, request: BookingRequest) -> BookingResponse:
        """
        Book an available appointment slot.
        Only reports success if slot exists and is currently available.
        """
        slot = self._slots.get(request.slot_id)

        if not slot:
            return BookingResponse(
                success=False,
                appointment=None,
                message=f"Booking failed: Slot ID '{request.slot_id}' was not found."
            )

        if not slot.is_available:
            return BookingResponse(
                success=False,
                appointment=None,
                message=f"Booking failed: Slot '{request.slot_id}' is already booked or unavailable."
            )

        # Generate unique appointment ID
        apt_id = f"APT-{uuid.uuid4().hex[:6].upper()}"

        # Mark slot as unavailable
        slot.is_available = False

        # Create appointment details
        appointment = AppointmentDetails(
            appointment_id=apt_id,
            patient_id=request.patient_id,
            patient_name=request.patient_name,
            doctor_name=slot.doctor_name,
            department=slot.department,
            datetime=slot.datetime,
            status="confirmed"
        )

        self._appointments[apt_id] = appointment
        self._appointment_slots[apt_id] = request.slot_id

        return BookingResponse(
            success=True,
            appointment=appointment,
            message=f"Appointment {apt_id} successfully booked with {slot.doctor_name} for {slot.datetime}."
        )

    def reschedule_appointment(self, request: RescheduleRequest) -> RescheduleResponse:
        """
        Reschedule an existing appointment to a new slot.
        Verifies appointment ownership and slot availability before confirming.
        """
        appointment = self._appointments.get(request.appointment_id)

        if not appointment:
            return RescheduleResponse(
                success=False,
                updated_appointment=None,
                message=f"Reschedule failed: Appointment '{request.appointment_id}' not found."
            )

        if appointment.patient_id != request.patient_id:
            return RescheduleResponse(
                success=False,
                updated_appointment=None,
                message=f"Reschedule failed: Patient ID mismatch for appointment '{request.appointment_id}'."
            )

        if appointment.status == "cancelled":
            return RescheduleResponse(
                success=False,
                updated_appointment=None,
                message=f"Reschedule failed: Appointment '{request.appointment_id}' is already cancelled."
            )

        new_slot = self._slots.get(request.new_slot_id)

        if not new_slot:
            return RescheduleResponse(
                success=False,
                updated_appointment=None,
                message=f"Reschedule failed: Requested new slot '{request.new_slot_id}' does not exist."
            )

        if not new_slot.is_available:
            return RescheduleResponse(
                success=False,
                updated_appointment=None,
                message=f"Reschedule failed: Requested slot '{request.new_slot_id}' is unavailable."
            )

        # Free the previous slot if tracked
        old_slot_id = self._appointment_slots.get(request.appointment_id)
        if old_slot_id and old_slot_id in self._slots:
            self._slots[old_slot_id].is_available = True

        # Reserve new slot
        new_slot.is_available = False
        self._appointment_slots[request.appointment_id] = request.new_slot_id

        # Update appointment details
        appointment.doctor_name = new_slot.doctor_name
        appointment.department = new_slot.department
        appointment.datetime = new_slot.datetime
        appointment.status = "confirmed"

        return RescheduleResponse(
            success=True,
            updated_appointment=appointment,
            message=f"Appointment '{request.appointment_id}' successfully rescheduled to {new_slot.datetime}."
        )

    def cancel_appointment(self, request: CancelRequest) -> CancelResponse:
        """
        Cancel an existing appointment and release its slot.
        """
        appointment = self._appointments.get(request.appointment_id)

        if not appointment:
            return CancelResponse(
                success=False,
                appointment_id=request.appointment_id,
                message=f"Cancellation failed: Appointment '{request.appointment_id}' not found."
            )

        if appointment.patient_id != request.patient_id:
            return CancelResponse(
                success=False,
                appointment_id=request.appointment_id,
                message=f"Cancellation failed: Patient ID mismatch for appointment '{request.appointment_id}'."
            )

        if appointment.status == "cancelled":
            return CancelResponse(
                success=False,
                appointment_id=request.appointment_id,
                message=f"Cancellation failed: Appointment '{request.appointment_id}' is already cancelled."
            )

        # Update status
        appointment.status = "cancelled"

        # Free slot if tracked
        slot_id = self._appointment_slots.get(request.appointment_id)
        if slot_id and slot_id in self._slots:
            self._slots[slot_id].is_available = True

        return CancelResponse(
            success=True,
            appointment_id=request.appointment_id,
            message=f"Appointment '{request.appointment_id}' has been successfully cancelled."
        )


# Singleton instance for service usage across modules
appointment_service = AppointmentService()
