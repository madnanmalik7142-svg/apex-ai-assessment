from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test GET /health returns 200 OK and expected structure."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "environment" in data


def test_assistant_message_valid():
    """Test POST /assistant/message with valid payload through orchestrator."""
    payload = {
        "message": "What free slots are available for Dental department?",
        "patient_id": "PAT-999",
        "session_id": "test_sess_001"
    }
    response = client.post("/assistant/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_sess_001"
    assert data["status"] == "success"
    assert "intent" in data
    assert len(data["reply"]) > 0


def test_assistant_message_validation_failure():
    """Test POST /assistant/message with invalid payload (empty message)."""
    payload = {
        "message": "",
        "patient_id": "PAT-999"
    }
    response = client.post("/assistant/message", json=payload)
    assert response.status_code == 422  # Validation error from Pydantic min_length=1
