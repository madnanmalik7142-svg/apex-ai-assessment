import pytest
from app.services.appointment_service import AppointmentService
from app.schemas.tools import (
    AvailabilityQuery,
    BookingRequest,
    RescheduleRequest,
    CancelRequest
)


@pytest.fixture
def service():
    """Fixture providing a fresh instance of AppointmentService for each test."""
    svc = AppointmentService()
    svc.reset_state()
    return svc


def test_check_availability_all(service: AppointmentService):
    """Test retrieving all initial available slots."""
    query = AvailabilityQuery()
    response = service.check_availability(query)
    assert response.success is True
    assert len(response.slots) == 6
    assert any(s.slot_id == "SLOT-101" for s in response.slots)


def test_check_availability_filtered_by_department(service: AppointmentService):
    """Test filtering available slots by department."""
    query = AvailabilityQuery(department="Dental")
    response = service.check_availability(query)
    assert response.success is True
    assert len(response.slots) == 3
    assert all(s.department == "Dental" for s in response.slots)


def test_check_availability_no_match(service: AppointmentService):
    """Test checking availability for non-existent doctor."""
    query = AvailabilityQuery(doctor_name="Dr. NonExistent")
    response = service.check_availability(query)
    assert response.success is True
    assert len(response.slots) == 0
    assert "No available slots" in response.message


def test_book_appointment_success(service: AppointmentService):
    """Test successful booking of an available slot."""
    booking_req = BookingRequest(
        patient_id="PAT-2001",
        patient_name="Tariq Al-Mansoor",
        patient_phone="+966551234567",
        slot_id="SLOT-101",
        notes="First time visitor"
    )
    response = service.book_appointment(booking_req)
    assert response.success is True
    assert response.appointment is not None
    assert response.appointment.patient_id == "PAT-2001"
    assert response.appointment.doctor_name == "Dr. Sarah Al-Otaibi"
    assert response.appointment.status == "confirmed"

    # Verify slot is no longer available in availability check
    avail = service.check_availability(AvailabilityQuery(department="Dental"))
    assert not any(s.slot_id == "SLOT-101" for s in avail.slots)


def test_book_appointment_already_booked(service: AppointmentService):
    """Test booking a slot that has already been taken."""
    booking_req = BookingRequest(
        patient_id="PAT-2001",
        patient_name="Tariq Al-Mansoor",
        patient_phone="+966551234567",
        slot_id="SLOT-101"
    )
    # First booking succeeds
    res1 = service.book_appointment(booking_req)
    assert res1.success is True

    # Second booking fails
    booking_req2 = BookingRequest(
        patient_id="PAT-2002",
        patient_name="Reem Al-Dossary",
        patient_phone="+966557654321",
        slot_id="SLOT-101"
    )
    res2 = service.book_appointment(booking_req2)
    assert res2.success is False
    assert res2.appointment is None
    assert "already booked" in res2.message.lower() or "unavailable" in res2.message.lower()


def test_book_appointment_invalid_slot(service: AppointmentService):
    """Test booking an invalid/non-existent slot ID."""
    booking_req = BookingRequest(
        patient_id="PAT-2001",
        patient_name="Tariq Al-Mansoor",
        patient_phone="+966551234567",
        slot_id="SLOT-99999"
    )
    response = service.book_appointment(booking_req)
    assert response.success is False
    assert response.appointment is None
    assert "not found" in response.message.lower()


def test_reschedule_appointment_success(service: AppointmentService):
    """Test successful rescheduling of an appointment to a new available slot."""
    reschedule_req = RescheduleRequest(
        appointment_id="APT-8001",
        patient_id="PAT-10023",
        new_slot_id="SLOT-102"
    )
    response = service.reschedule_appointment(reschedule_req)
    assert response.success is True
    assert response.updated_appointment is not None
    assert response.updated_appointment.datetime == "2026-10-02 11:30"
    assert response.updated_appointment.doctor_name == "Dr. Sarah Al-Otaibi"

    # Verify SLOT-102 is now unavailable
    avail = service.check_availability(AvailabilityQuery())
    assert not any(s.slot_id == "SLOT-102" for s in avail.slots)


def test_reschedule_appointment_patient_mismatch(service: AppointmentService):
    """Test rescheduling with wrong patient ID."""
    reschedule_req = RescheduleRequest(
        appointment_id="APT-8001",
        patient_id="WRONG-PATIENT-ID",
        new_slot_id="SLOT-102"
    )
    response = service.reschedule_appointment(reschedule_req)
    assert response.success is False
    assert response.updated_appointment is None
    assert "mismatch" in response.message.lower()


def test_cancel_appointment_success(service: AppointmentService):
    """Test successful cancellation of an appointment."""
    cancel_req = CancelRequest(
        appointment_id="APT-8001",
        patient_id="PAT-10023",
        reason="Personal conflict"
    )
    response = service.cancel_appointment(cancel_req)
    assert response.success is True
    assert response.appointment_id == "APT-8001"
    assert "cancelled" in response.message.lower()


def test_cancel_appointment_already_cancelled(service: AppointmentService):
    """Test attempting to cancel an already cancelled appointment."""
    cancel_req = CancelRequest(
        appointment_id="APT-8001",
        patient_id="PAT-10023"
    )
    # First cancellation succeeds
    res1 = service.cancel_appointment(cancel_req)
    assert res1.success is True

    # Second cancellation fails
    res2 = service.cancel_appointment(cancel_req)
    assert res2.success is False
    assert "already cancelled" in res2.message.lower()


def test_cancel_appointment_patient_mismatch(service: AppointmentService):
    """Test attempting to cancel another patient's appointment."""
    cancel_req = CancelRequest(
        appointment_id="APT-8001",
        patient_id="PAT-UNAUTHORIZED"
    )
    response = service.cancel_appointment(cancel_req)
    assert response.success is False
    assert "mismatch" in response.message.lower()
