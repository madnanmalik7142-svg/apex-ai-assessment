import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.appointment_service import appointment_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_appointment_db():
    """Reset appointment in-memory state before each integration test."""
    appointment_service.reset_state()


def test_integration_health_check():
    """Test GET /health health status endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_integration_emergency_workflow():
    """Test emergency symptom detection protocol returns 997 emergency guidance."""
    payload = {"message": "I am experiencing severe chest pain and difficulty breathing!"}
    response = client.post("/assistant/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "medical_emergency"
    assert data["status"] == "emergency_diverted"
    assert data["escalated"] is True
    assert "997" in data["reply"]


def test_integration_human_escalation_workflow():
    """Test human escalation request routing."""
    payload = {"message": "Please connect me to a human representative right now."}
    response = client.post("/assistant/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "human_escalation"
    assert data["status"] == "escalated"
    assert data["escalated"] is True
    assert "human" in data["reply"].lower()


def test_integration_out_of_scope_workflow():
    """Test out of scope query rejection."""
    payload = {"message": "What is the current bitcoin stock market price?"}
    response = client.post("/assistant/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "out_of_scope"
    assert data["status"] == "rejected"
    assert "AI Healthcare Assistant" in data["reply"]


def test_integration_check_availability_workflow():
    """Test checking appointment availability."""
    payload = {"message": "What available slots do you have for Dental tomorrow?"}
    response = client.post("/assistant/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "check_availability"
    assert data["status"] == "success"
    assert "SLOT-101" in data["reply"]


def test_integration_book_appointment_success():
    """Test booking an available slot."""
    payload = {
        "message": "I want to book appointment slot SLOT-103 for PAT-10023",
        "patient_id": "PAT-10023"
    }
    response = client.post("/assistant/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "book_appointment"
    assert data["status"] == "success"
    assert "successfully booked" in data["reply"].lower()


def test_integration_book_appointment_failure_already_booked():
    """Test booking a slot that is already booked returns failed status."""
    # First booking
    client.post("/assistant/message", json={"message": "Book slot SLOT-103 for PAT-10023", "patient_id": "PAT-10023"})

    # Second booking attempt on same slot
    payload = {"message": "Book slot SLOT-103 for PAT-20002", "patient_id": "PAT-20002"}
    response = client.post("/assistant/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "book_appointment"
    assert data["status"] == "failed"
    assert "already booked" in data["reply"].lower() or "unavailable" in data["reply"].lower()


def test_integration_reschedule_appointment_success():
    """Test rescheduling an existing appointment to a new slot."""
    payload = {
        "message": "Please reschedule appointment APT-8001 to slot SLOT-102 for patient PAT-10023",
        "patient_id": "PAT-10023"
    }
    response = client.post("/assistant/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "reschedule_appointment"
    assert data["status"] == "success"
    assert "rescheduled" in data["reply"].lower()


def test_integration_cancel_appointment_success():
    """Test cancelling an existing appointment."""
    payload = {
        "message": "Please cancel my appointment APT-8001 for patient PAT-10023",
        "patient_id": "PAT-10023"
    }
    response = client.post("/assistant/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "cancel_appointment"
    assert data["status"] == "success"
    assert "cancel" in data["reply"].lower() or "canceled" in data["reply"].lower()


def test_integration_rag_preparation_workflow():
    """Test RAG workflow for blood test preparation rules."""
    payload = {"message": "What are the fasting rules before blood test?"}
    response = client.post("/assistant/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "preparation_instructions"
    assert data["status"] == "success"
    assert "8 to 12 hours" in data["reply"]


def test_integration_rag_insurance_workflow():
    """Test RAG workflow for CCHI insurance policy."""
    payload = {"message": "What is the CCHI insurance copay cap in Saudi Arabia?"}
    response = client.post("/assistant/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "insurance_policy"
    assert data["status"] == "success"
    assert "SAR 100" in data["reply"]
