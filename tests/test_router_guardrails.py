import pytest
from app.services.guardrails import GuardrailService
from app.services.router import IntentRouter
from app.schemas.router import IntentEnum


@pytest.fixture
def router():
    return IntentRouter()


@pytest.fixture
def guardrail_svc():
    return GuardrailService()


# --- User Specific Router Tests ---
def test_emergency_detection(router):
    res = router.route("I have severe chest pain and difficulty breathing")
    assert res.intent == IntentEnum.EMERGENCY
    assert res.safety.is_emergency is True
    assert res.safety.should_escalate is True


def test_out_of_scope_detection(router):
    res = router.route("Can you give me a recipe for chocolate cake?")
    assert res.intent == IntentEnum.OUT_OF_SCOPE
    assert res.safety.is_safe is False


def test_intent_booking(router):
    res = router.route("I want to book an appointment with a cardiologist")
    assert res.intent == IntentEnum.BOOK
    assert res.safety.is_safe is True


def test_entity_extraction(router):
    res = router.route("Please cancel my appointment APP-101")
    assert res.intent == IntentEnum.CANCEL
    assert res.extracted_entities.get("appointment_id") == "APP-101"


# --- Additional Safety & Intent Tests ---
def test_guardrail_human_escalation_request(router):
    """Test explicit patient request for a human representative."""
    res = router.route("Please let me speak to a human representative right now.")
    assert res.intent == IntentEnum.ESCALATE
    assert res.safety.is_safe is True
    assert res.safety.should_escalate is True


def test_guardrail_arabic_emergency(router):
    """Test Arabic red flag emergency symptom detection."""
    res = router.route("أعاني من ألم في الصدر")
    assert res.intent == IntentEnum.EMERGENCY
    assert res.safety.is_emergency is True
    assert res.safety.should_escalate is True


def test_router_book_appointment_intent(router):
    """Test routing and entity extraction for booking appointment request."""
    msg = "I want to book an appointment with Dr. Sarah Al-Otaibi for Dental tomorrow."
    res = router.route(msg)
    assert res.intent == IntentEnum.BOOK
    assert res.extracted_entities.get("department") == "Dental"
    assert res.extracted_entities.get("doctor_name") == "Dr. Sarah Al-Otaibi"
    assert res.extracted_entities.get("date") == "tomorrow"


def test_router_reschedule_appointment_intent(router):
    """Test routing and entity extraction for reschedule request."""
    msg = "I need to reschedule my appointment APT-8001 to SLOT-102."
    res = router.route(msg)
    assert res.intent == IntentEnum.RESCHEDULE
    assert res.extracted_entities.get("appointment_id") == "APT-8001"
    assert res.extracted_entities.get("slot_id") == "SLOT-102"


def test_router_check_availability_intent(router):
    """Test routing for checking available slots."""
    msg = "What free slots are available for Dental department tomorrow?"
    res = router.route(msg)
    assert res.intent == IntentEnum.AVAILABILITY
    assert res.extracted_entities.get("department") == "Dental"


def test_router_preparation_instructions_intent(router):
    """Test routing for test preparation inquiry."""
    msg = "What is the fasting preparation needed before a blood glucose test?"
    res = router.route(msg)
    assert res.intent == IntentEnum.PREPARATION


def test_router_insurance_inquiry_intent(router):
    """Test routing for CCHI insurance query."""
    msg = "What is the CCHI copay limit for outpatient consultations?"
    res = router.route(msg)
    assert res.intent == IntentEnum.INSURANCE


def test_router_general_inquiry_intent(router):
    """Test routing for clinic working hours and locations."""
    msg = "What are the clinic opening hours in Riyadh on Saturday?"
    res = router.route(msg)
    assert res.intent == IntentEnum.GENERAL
