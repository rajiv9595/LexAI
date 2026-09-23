# LexAssist AI Architecture & Real Gemini Provider Foundation

> **STEP 17 ARCHITECTURE**:
> STEP 17 integrates the official Google GenAI Python SDK (`google-genai`) behind the existing `AIProvider` abstraction.
> LexAssist supports structured legal-information generation when `AI_ENABLED=true` and `AI_PROVIDER=gemini`, while gracefully falling back to deterministic offline simulation when `AI_ENABLED=false` or `AI_PROVIDER=mock`.

---

## 1. Architectural Overview

```
User Query
    │
    ▼
┌───────────────────────────────────────────────┐
│ Assistant API Endpoint                        │
│ (POST /api/v1/assistant/messages)             │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│ Pre-Generation Safety Assessment (Guardrails) │
│ - Checks for Emergencies / Harm               │
│ - Checks for Imminent Court Deadlines         │
│ - Checks for Criminal Incarceration           │
│ - Checks for Fraud / Law Evasion              │
│ - Checks for Formal Legal Notices             │
└───────────────────────┬───────────────────────┘
                        │
         ┌──────────────┴──────────────┐
         │ (Status: ESCALATE)          │ (Status: SAFE / CAUTION)
         ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────────────────────┐
│ Urgent Escalation       │   │ Assistant Orchestrator                  │
│ Direct Advisory Notice  │   │ - Applies Versioned Legal Prompt (v1)   │
│ (Immediate Counsel/911) │   │ - Formats Conversation & Case Context   │
│ [No Gemini API Call]    │   │ - Injects Grounding Context (RAG ready) │
└────────┬────────────────┘   └────────────────────┬────────────────────┘
         │                                         │
         │                                         ▼
         │                    ┌─────────────────────────────────────────┐
         │                    │ Provider Factory (get_ai_provider)      │
         │                    │ ├── AI_PROVIDER=gemini (GeminiAIProvider)│
         │                    │ └── AI_PROVIDER=mock   (MockAIProvider) │
         │                    └────────────────────┬────────────────────┘
         │                                         │
         │                                         ▼
         │                    ┌─────────────────────────────────────────┐
         │                    │ Post-Generation Safety Validation       │
         │                    │ - Verifies No Guaranteed Win Claims     │
         │                    │ - Verifies No Attorney Representation   │
         │                    │ - Enforces Zero Citation Hallucination  │
         │                    └────────────────────┬────────────────────┘
         │                                         │
         │                                         ▼
         │                    ┌─────────────────────────────────────────┐
         │                    │ Central Disclaimer Attachment           │
         │                    └────────────────────┬────────────────────┘
         │                                         │
         │                                         ▼
        ┌───────────────────────────────────────────┐
        │ Typed LegalAssistantResponse (JSON DTO)   │
        └───────────────────────────────────────────┘
```

---

## 2. Configuration & Environment Variables

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `AI_ENABLED` | `bool` | `false` | Global feature flag. When `false`, uses offline prototype/mock without external API calls. |
| `AI_PROVIDER` | `str` | `mock` | Selected provider: `gemini` or `mock`. |
| `GEMINI_API_KEY` | `str` | `None` | Google GenAI API key. Required only when `AI_ENABLED=true` and `AI_PROVIDER=gemini`. |
| `GEMINI_MODEL` | `str` | `gemini-2.5-flash` | Selected Gemini model with native structured output support. |

### Security & No-Key Development Mode
- The application starts and runs 100% of unit tests without a Gemini API key.
- `backend/.env` is strictly git-ignored and must never be committed.
- API keys are never printed, logged, or returned in API responses.

---

## 3. Core Modules & Separation of Concerns

### A. Provider Abstraction & Registry (`app/ai/providers/`)
- `AIProvider`: Abstract base class enforcing `generate(request: AIRequest) -> AIResponse`.
- `GeminiAIProvider`: Real Gemini implementation using the official `google-genai` SDK. Configures JSON structured outputs (`response_mime_type="application/json"`, `response_schema=LegalAssistantResponse`), parses token counts, and wraps SDK errors into controlled exceptions (`GeminiAuthenticationError`, `GeminiRateLimitError`, `GeminiTimeoutError`, `GeminiResponseError`).
- `MockDeterministicAIProvider`: Deterministic offline implementation for unit tests and local development.
- `get_ai_provider(provider_name)`: Central factory resolving providers based on system configuration.

### B. Models & Data Contracts (`app/ai/models/`)
- `AIRequest`: Container for `system_instruction`, `user_message`, `conversation_history`, `retrieved_context`, and `case_context`.
- `AIResponse`: Raw provider payload containing `content`, `provider`, `model`, `finish_reason`, and token metadata.
- `LegalAssistantResponse`: Canonical Pydantic schema for structured legal answers (`answer`, `issue_summary`, `assumptions`, `missing_information`, `potential_considerations`, `suggested_next_steps`, `references`, `disclaimer`, `safety_assessment`).

### C. Versioned Prompts (`app/ai/prompts/`)
- `LEGAL_ASSISTANT_PROMPT_VERSION = "v1"`: Centralized prompt version tag.
- `LEGAL_ASSISTANT_SYSTEM_PROMPT`: Rules requiring neutral legal information, strict issue identification, missing-fact queries, and zero fabricated citations.

### D. Safety & Guardrails (`app/ai/safety/`)
- `assess_request(user_message)`: Pre-generation screening categorizing inputs as `SAFE`, `CAUTION`, or `ESCALATE`. Emergency requests (`ESCALATE`) bypass LLM calls entirely.
- `validate_response(content, assessment)`: Detects and strips prohibited win guarantees or claims of representation.
- `CENTRAL_LEGAL_DISCLAIMER`: Standardized advisory statement attached to all generated legal outputs.

### E. Orchestration (`app/ai/services/`)
- `AssistantOrchestrator`: End-to-end pipeline manager that executes safety screening, prompt assembly, provider dispatch, post-validation, and response compilation.

---

## 4. Testing & Verification

### Running Automated Unit Tests (Offline / Mocked)
All automated tests run without network calls or external API keys:
```bash
cd backend
.\.venv\Scripts\python -m pytest
```

### Performing Local Live Gemini Smoke Test
To test live structured generation with a valid Gemini key:
1. Set `AI_ENABLED=true`, `AI_PROVIDER=gemini`, `GEMINI_API_KEY=<your_key>`, and `GEMINI_MODEL=gemini-2.5-flash` in `backend/.env`.
2. Run the isolated verification command:
```bash
cd backend
.\.venv\Scripts\python -c "from app.ai.models.responses import AIRequest; from app.ai.services.assistant_orchestrator import AssistantOrchestrator; resp = AssistantOrchestrator().process_request(AIRequest(user_message='What is a security deposit in a rental agreement, in general terms?')); print('Status:', resp.safety_assessment.status.value); print('Provider:', resp.provider_used); print('Answer preview:', resp.answer[:120])"
```

---

## 5. Capstone Project Requirement Traceability

| Project Requirement | Architectural Component | Implementation Status |
| :--- | :--- | :--- |
| **1. Natural-Language Understanding** | `GeminiAIProvider` + `AIRequest` + `AssistantOrchestrator` | Real Gemini structured NLU implemented in Step 17. |
| **2. Legal Issue Identification** | `LegalAssistantResponse.issue_summary` + Prompt rules | Real structured generation implemented in Step 17. |
| **3. Personalized Legal Assistance** | `AIRequest.case_context` + `conversation_history` | Supported in `AIRequest` model and Gemini prompting. |
| **4. Automated Document Drafting** | Future document generation service integration | Architecture compatible with `DocumentTemplate` schemas. |
| **5. Statutes & Precedents Retrieval** | `AIRequest.retrieved_context` + Zero Hallucination Rule | Prepared for future RAG / Knowledge Graph retrieval. |
| **6. Ethical AI & Guardrails** | `guardrails.py` + `SafetyAssessment` + `assess_request` | Pre-generation and post-generation safety checks active. |
| **7. Fairness & Bias Mitigation** | Central system prompt constraints + response validation | Enforced via versioned system prompt and Pydantic schema. |
| **8. Text/Voice Interaction** | RESTful endpoint architecture | Backend contracts established; UI voice adapter in later step. |

