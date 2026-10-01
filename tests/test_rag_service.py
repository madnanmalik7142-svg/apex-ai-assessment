import pytest
from app.services.rag_service import RAGService


@pytest.fixture
def rag_service():
    return RAGService()


def test_rag_search_preparation(rag_service):
    res = rag_service.search("What are the fasting rules for blood test?")
    assert res.has_match is True
    assert len(res.results) > 0
    assert "blood" in res.results[0].document.content.lower()


def test_rag_search_insurance(rag_service):
    res = rag_service.search("Does insurance cover CCHI copayment?")
    assert res.has_match is True
    assert res.results[0].document.category == "insurance"


def test_rag_search_no_match(rag_service):
    res = rag_service.search("xyz unknown nonmedical query")
    assert res.has_match is False
    assert len(res.results) == 0


def test_load_knowledge_base(rag_service):
    """Test knowledge base dataset loads all 5 initial documents."""
    assert len(rag_service.documents) == 5
    ids = [d.id for d in rag_service.documents]
    assert "prep_fasting_blood" in ids
    assert "prep_ultrasound_abdomen" in ids
    assert "ins_cchi_coverage" in ids
    assert "ins_approval_process" in ids
    assert "gen_working_hours" in ids


def test_search_ultrasound_instructions(rag_service):
    """Test retrieving preparation instructions for abdominal ultrasound."""
    res = rag_service.search("Can I drink water before abdominal ultrasound?")
    assert res.has_match is True
    assert len(res.results) > 0
    assert res.results[0].document.id == "prep_ultrasound_abdomen"


def test_search_prior_authorization(rag_service):
    """Test retrieving pre-approval / prior authorization guidelines."""
    res = rag_service.search("How long does MRI imaging pre-approval take?")
    assert res.has_match is True
    assert len(res.results) > 0
    assert res.results[0].document.id == "ins_approval_process"


def test_search_clinic_working_hours(rag_service):
    """Test retrieving clinic opening hours and branch locations."""
    res = rag_service.search("What are the clinic opening hours in Riyadh on Saturday?")
    assert res.has_match is True
    assert len(res.results) > 0
    assert res.results[0].document.id == "gen_working_hours"
