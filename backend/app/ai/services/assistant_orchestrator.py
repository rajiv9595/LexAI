"""Assistant orchestrator coordinating safety, context assembly, provider generation, and post-validation."""

import json
import logging
from app.ai.models.responses import (
    AIRequest,
    AIRequestMessage,
    LegalAssistantResponse,
    LegalReferenceItem,
    SafetyStatus,
)
from app.ai.models.query_understanding import LegalQueryUnderstanding
from app.ai.models.retrieval import GroundedContext
from app.ai.services.citation_validator import validate_response_citations
from app.ai.services.research_retriever import (
    RetrievalResolver,
    grounded_context_to_chunks,
)
from app.ai.prompts.legal_assistant import (
    LEGAL_ASSISTANT_PROMPT_VERSION,
    LEGAL_ASSISTANT_SYSTEM_PROMPT,
)
from app.ai.providers.base import AIProvider
from app.ai.providers.factory import get_ai_provider
from app.ai.safety.guardrails import (
    CENTRAL_LEGAL_DISCLAIMER,
    assess_request,
    validate_response,
)
from app.ai.services.query_understanding import QueryUnderstandingService

logger = logging.getLogger(__name__)


def _format_understanding(understanding: LegalQueryUnderstanding) -> str:
    """Render structured understanding as final-answer prompt context."""
    parties = (
        ", ".join(
            f"{party.role}" + (f" ({party.name})" if party.name else "")
            for party in understanding.parties
        )
        or "none identified"
    )

    def _bullets(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items) or "- none"

    return (
        f"intent: {understanding.intent}\n"
        f"legal_domain: {understanding.legal_domain}\n"
        f"primary_issue: {understanding.primary_issue or 'unknown'}\n"
        f"secondary_issues: {', '.join(understanding.secondary_issues) or 'none'}\n"
        f"jurisdiction: {understanding.jurisdiction or 'unknown'}\n"
        f"parties: {parties}\n"
        f"facts:\n{_bullets(understanding.facts)}\n"
        f"dates: {', '.join(understanding.dates) or 'none explicitly provided'}\n"
        f"amounts: {', '.join(understanding.amounts) or 'none explicitly provided'}\n"
        f"missing_information:\n{_bullets(understanding.missing_information)}\n"
        f"clarification_questions:\n{_bullets(understanding.clarification_questions)}\n"
        f"urgency: {understanding.urgency}\n"
        f"extraction_confidence: {understanding.confidence}"
    )


class AssistantOrchestrator:
    """Coordinates the end-to-end AI assistant pipeline.

    Pipeline sequence:
    1. Normalize request
    2. Assess pre-generation safety (Short-circuit on ESCALATE)
    3. Derive structured LegalQueryUnderstanding (extraction only, same provider)
    4. Assemble system prompt, history, case context, understanding, and grounding context
    5. Dispatch to AIProvider interface (configured via factory or explicitly passed)
    6. Parse and validate structured output
    6b. Deterministic citation validation against GroundedContext (STEP 20)
    7. Run post-generation safety validation
    8. Attach centralized legal disclaimer
    9. Return typed LegalAssistantResponse
    """

    def __init__(
        self,
        provider: AIProvider | None = None,
        provider_name: str | None = None,
    ):
        self.provider = provider or get_ai_provider(provider_name)

    def process_request(self, request: AIRequest) -> LegalAssistantResponse:
        """Process an AIRequest container through the orchestrator pipeline."""
        return self.process_query(
            user_message=request.user_message,
            conversation_history=request.conversation_history,
            case_context=request.case_context,
            retrieved_context=request.retrieved_context,
        )

    def process_query(
        self,
        user_message: str,
        conversation_history: list[AIRequestMessage] | None = None,
        case_context: dict[str, str] | None = None,
        retrieved_context: list[str] | None = None,
        retrieval_resolver: RetrievalResolver | None = None,
    ) -> LegalAssistantResponse:
        """Process a legal query through the complete orchestration and safety pipeline.

        STEP 19 data flow: Safety -> Query Understanding -> Research
        Retrieval (via optional ``retrieval_resolver``) -> GroundedContext
        -> ``AIRequest.retrieved_context``. An explicitly supplied
        non-empty ``retrieved_context`` always wins (backwards compatible);
        otherwise the resolver output is used. ESCALATE short-circuits
        before any retrieval call.
        """
        normalized_message = user_message.strip()

        # Step 1: Pre-generation Safety Assessment
        safety = assess_request(normalized_message)

        # Step 2: Urgent Escalation Short-Circuit (Zero-cost safe fast exit)
        if safety.status == SafetyStatus.ESCALATE:
            return LegalAssistantResponse(
                answer=safety.advisory_message,
                issue_summary="Urgent safety or judicial escalation detected.",
                assumptions=["User requires immediate human legal counsel or emergency intervention."],
                missing_information=[],
                potential_considerations=[
                    "Statutory rights may be severely prejudiced without immediate qualified counsel.",
                    "Emergency safety concerns take absolute priority over general legal information.",
                ],
                suggested_next_steps=[
                    "Contact emergency services (911 or local emergency) if in immediate physical danger.",
                    "Retain qualified criminal defense or litigation counsel immediately.",
                ],
                references=[],
                disclaimer=CENTRAL_LEGAL_DISCLAIMER,
                safety_assessment=safety,
                prompt_version=LEGAL_ASSISTANT_PROMPT_VERSION,
                provider_used=self.provider.provider_name,
            )

        # Step 3: Derive Structured Query Understanding (extraction only)
        # Uses the same provider instance, so mock mode stays fully offline.
        # The understanding is AI-derived interpretation, not verified fact:
        # the final prompt still relies primarily on the original user message.
        understanding = QueryUnderstandingService(provider=self.provider).understand(
            normalized_message,
            conversation_history or [],
        )

        # Step 3b (STEP 19): Research Retrieval -> GroundedContext.
        # Resolver is DB-backed and injected by the caller (assistant_service);
        # the orchestrator itself stays provider- and DB-independent.
        # Explicit caller-supplied retrieved_context takes precedence.
        # The GroundedContext object itself is retained for STEP 20 citation
        # validation; string-only caller context carries no allowlist.
        effective_retrieved: list[str] = list(retrieved_context or [])
        grounded: GroundedContext | None = None
        if not effective_retrieved and retrieval_resolver is not None:
            try:
                grounded = retrieval_resolver(
                    normalized_message, understanding
                )
            except Exception:
                logger.warning("Research retrieval failed; continuing without grounding.")
                grounded = None
            if grounded is not None:
                effective_retrieved = grounded_context_to_chunks(grounded)

        # Step 4: Build AI Request (final answer generation)
        ai_request = AIRequest(
            system_instruction=LEGAL_ASSISTANT_SYSTEM_PROMPT,
            user_message=normalized_message,
            conversation_history=conversation_history or [],
            retrieved_context=effective_retrieved,
            case_context=case_context or {},
            query_understanding=_format_understanding(understanding),
        )

        # Step 5: Dispatch to Provider Interface
        raw_response = self.provider.generate(ai_request)

        # Step 6: Parse Structured Output
        answer_text = raw_response.content
        issue_summary = f"Inquiry regarding: {normalized_message[:80]}..."
        assumptions: list[str] = []
        missing_information = [
            "Applicable jurisdiction (State / Region)",
            "Relevant contract terms or executed documentation",
        ]
        potential_considerations = [
            "General legal principles apply; specific statutory requirements vary by jurisdiction.",
        ]
        suggested_next_steps = [
            "Review relevant documents and agreements.",
            "Consult a licensed attorney in your jurisdiction for tailored guidance.",
        ]
        references: list[LegalReferenceItem] = []

        # Attempt JSON decoding if provider returned structured JSON
        try:
            parsed = json.loads(raw_response.content)
            if isinstance(parsed, dict):
                answer_text = str(parsed.get("answer") or parsed.get("content") or raw_response.content)
                if parsed.get("issue_summary"):
                    issue_summary = str(parsed["issue_summary"])
                if isinstance(parsed.get("assumptions"), list):
                    assumptions = [str(x) for x in parsed["assumptions"]]
                if isinstance(parsed.get("missing_information"), list) and parsed["missing_information"]:
                    missing_information = [str(x) for x in parsed["missing_information"]]
                if isinstance(parsed.get("potential_considerations"), list) and parsed["potential_considerations"]:
                    potential_considerations = [str(x) for x in parsed["potential_considerations"]]
                if isinstance(parsed.get("suggested_next_steps"), list) and parsed["suggested_next_steps"]:
                    suggested_next_steps = [str(x) for x in parsed["suggested_next_steps"]]

                # Strict grounding rule: only permit references if retrieved_context was non-empty
                if effective_retrieved and isinstance(parsed.get("references"), list):
                    for ref in parsed["references"]:
                        if isinstance(ref, dict):
                            references.append(
                                LegalReferenceItem(
                                    title=str(ref.get("title", "")),
                                    kind=str(ref.get("kind", "Reference")),
                                    citation=str(ref.get("citation", "")),
                                    relevance_note=str(ref.get("relevance_note", "")),
                                    source_id=str(ref.get("source_id", "") or ""),
                                )
                            )
                else:
                    references = []
        except (json.JSONDecodeError, ValueError):
            # Non-JSON content (e.g., deterministic mock string) is handled as plain text answer
            pass

        # Step 6b (STEP 20): Deterministic Citation Validation.
        # Model-supplied references are bound against the GroundedContext
        # allowlist and rebuilt from backend metadata; unknown, fabricated,
        # or duplicate references are removed. Empty retrieval always yields
        # references == []. Runs before post-generation safety validation so
        # both safety and citation checks are always applied, in that order.
        provisional = LegalAssistantResponse(
            answer=answer_text,
            issue_summary=issue_summary,
            assumptions=assumptions,
            missing_information=missing_information,
            potential_considerations=potential_considerations,
            suggested_next_steps=suggested_next_steps,
            references=references,
            disclaimer=CENTRAL_LEGAL_DISCLAIMER,
            safety_assessment=safety,
            prompt_version=LEGAL_ASSISTANT_PROMPT_VERSION,
            provider_used=self.provider.provider_name,
        )
        citation_result = validate_response_citations(provisional, grounded)
        if citation_result.removed_count:
            logger.info(
                "Citation validation removed %d ungrounded reference(s).",
                citation_result.removed_count,
            )
        answer_text = citation_result.response.answer
        references = citation_result.response.references

        # Step 7: Post-generation Response Validation
        is_valid, violations = validate_response(answer_text, safety)
        if not is_valid:
            answer_text = (
                f"{answer_text}\n\n"
                "[Notice: This response provides general legal information and does not constitute guaranteed legal outcomes or formal representation.]"
            )

        # Step 8: Assemble Domain-Level LegalAssistantResponse
        return LegalAssistantResponse(
            answer=answer_text,
            issue_summary=issue_summary,
            assumptions=assumptions,
            missing_information=missing_information,
            potential_considerations=potential_considerations,
            suggested_next_steps=suggested_next_steps,
            references=references,
            disclaimer=CENTRAL_LEGAL_DISCLAIMER,
            safety_assessment=safety,
            prompt_version=LEGAL_ASSISTANT_PROMPT_VERSION,
            provider_used=self.provider.provider_name,
        )
