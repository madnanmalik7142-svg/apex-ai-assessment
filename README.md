# Saudi Healthcare Patient Service Assistant

A production-ready Python & FastAPI backend designed for the **Apex AI Arabia AI Engineer hiring assessment**. This assistant provides a practical patient-service API for Saudi healthcare inquiries, appointment lifecycle management (booking, rescheduling, cancellation, availability checks), test preparation instructions, CCHI insurance policies, emergency redirection (Red Crescent 997), human escalation, guardrails, and deterministic RAG knowledge retrieval.

---

## 📌 Key Highlights & Architectural Features

1. **Multi-Step Assistant Orchestration:** Executes a clean pipeline: `Guardrails` $\rightarrow$ `Intent Router & Entity Extractor` $\rightarrow$ `(Appointment Tools / RAG Engine / Escalation)` $\rightarrow$ `Structured Output`.
2. **Saudi Red Flag Emergency Protocol:** Detects life-threatening medical symptoms (in English and Arabic: chest pain, shortness of breath, `ألم في الصدر`, `ضيق في التنفس`) and instantly diverts patients to call **997 (Saudi Red Crescent)**.
3. **Strict Confirmation Rule:** Never reports an appointment action as successful unless the underlying tool explicitly returns `success=True`.
4. **Deterministic RAG Knowledge Engine:** High-precision Jaccard keyword retrieval for Saudi CCHI insurance regulations, prior authorization rules, ultrasound/blood test fasting preparation guidelines, and clinic branch working hours.
5. **Parametric Clarification Loops:** Automatically detects missing mandatory parameters (`slot_id`, `appointment_id`) and prompts the patient for clarification before tool execution.

---

## 📁 Project Structure

```text
apex-healthcare-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point & CORS configuration
│   ├── config.py            # Environment configuration via pydantic-settings
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # GET /health and POST /assistant/message routes
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── chat.py          # Request (ChatRequest) and Response (ChatResponse) schemas
│   │   ├── tools.py         # Appointment tools schemas (Availability, Booking, Reschedule, Cancel)
│   │   ├── rag.py           # RAG schemas (KnowledgeDocument, RAGSearchResult, RAGResponse)
│   │   └── router.py        # IntentEnum, SafetyCheckResult, and RoutingResult schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── assistant_service.py   # Multi-step Assistant Orchestrator
│   │   ├── appointment_service.py # Mocked appointment tools & in-memory state engine
│   │   ├── rag_service.py         # Deterministic RAG search engine
│   │   ├── guardrails.py          # Safety guardrails (Emergency, Escalation, Scope)
│   │   └── router.py              # Bilingual Intent Router & Regex Entity Extractor
│   └── data/
│       └── knowledge_base.json     # Official Saudi healthcare knowledge base dataset
├── docs/
│   └── ASSESSMENT_REPORT.md        # Comprehensive technical report, cost analysis, and evaluation
├── tests/
│   ├── __init__.py
│   ├── test_api.py                 # API health & message tests
│   ├── test_appointment_service.py # In-memory appointment service unit tests
│   ├── test_rag_service.py         # RAG search unit tests
│   ├── test_router_guardrails.py   # Guardrails & intent router unit tests
│   └── test_api_integration.py     # End-to-end integration tests for all workflows
├── .env.example                    # Environment variable template
├── .gitignore                      # Git ignore configuration
├── Dockerfile                      # Production Docker container definition
├── docker-compose.yml              # Container orchestration setup
├── requirements.txt                # Python dependencies
└── README.md                       # Main project documentation
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10+ installed.
- Docker & Docker Compose (optional for containerized deployment).

### 2. Local Environment Setup

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🏃 Running the API

### Option A: Running with Uvicorn (Local Development)
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option B: Running with Docker Compose (Production)
```bash
docker-compose up --build -d
```

Once running:
- **Interactive Swagger Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check Endpoint:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🧪 Testing the Application

Run the automated test suite with `pytest`:

```bash
python -m pytest -v
```

*(All 44 test cases covering unit logic, guardrails, RAG precision, appointment tools, and API integration pass cleanly).*

---

## 📖 Comprehensive Architectural Report
For detailed answers to all theoretical assessment questions (Model & Cost Comparison, Production HIS Architecture, Workflow vs. Agent justification, Debugging Case Analysis, and Non-Technical Customer Explanation), see:
👉 **[`docs/ASSESSMENT_REPORT.md`](file:///c:/Users/madna/apex-ai-assessment/docs/ASSESSMENT_REPORT.md)**
