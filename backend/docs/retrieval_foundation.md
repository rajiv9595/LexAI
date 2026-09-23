# STEP 19 — Legal Research Retrieval & Grounded-Context Foundation

## What the retriever does

- Searches the **existing curated research records** already used by
  `POST /api/v1/research/search` (same canonical `research_records` table).
- Converts matches into strongly typed `RetrievedLegalSource` items bundled
  as a `GroundedContext` (sources + deterministic `context_text`).
- Feeds the AI layer through the **existing** `AIRequest.retrieved_context`
  field (`GroundedContext` → single text chunk; empty retrieval → `[]`).
- Produces **evidence only** — no legal conclusions, no citations invented.

> The current retrieval layer operates over the curated research records
> already present in LexAssist. It is not a substitute for verified
> legal-source databases and does not by itself establish legal authority.

## Algorithm (`lexical-weighted-v1`)

1. Build retrieval terms from: raw query + `primary_issue` +
   `secondary_issues` + `legal_domain` (underscores → spaces). Facts, dates,
   amounts, party names, and inferred jurisdictions are **excluded**.
2. Normalize (lowercase, non-alphanumeric → space), tokenize, drop stop
   words and 1-character tokens, deduplicate preserving order.
3. Per unique term, substring-match lowercased fields:
   - title → **+3.0** (high weight)
   - topics → **+2.5** (high weight)
   - summary → **+1.0** (medium weight)
   - citation_label → **+0.8** (lower weight)
   - term equals record `source_type` → **+1.0**
   - explicit `LegalQueryUnderstanding.jurisdiction` exact match → **+1.0**
4. Rank by score descending, tie-break by `source_id` ascending. Top N
   (default 5, clamped 1–20; `limit <= 0` → empty). Zero-score records
   are never returned.

## Relevance score meaning

The score means **only** "lexical relevance to the user's query." It does
**not** represent legal authority, correctness, or precedential weight.

## Prototype-source limitation

- Every source preserves the canonical `prototype` flag and provenance
  (`source_record_id`, `source_kind`, `citation_label`, `prototype`).
- `source_url` is **always null** today because canonical records carry no
  URL field — it is never fabricated.
- The Gemini prompt labels grounded material as
  "curated prototype research records; not verified legal authority".
- Future STEP 20 grounded-answer work can distinguish prototype material
  from verified external sources via `prototype` / `provenance`.

## Why no external web scraping

STEP 19 is the **retrieval foundation**: deterministic, inspectable,
testable, provider-independent, and offline. No embeddings, vector DB,
external APIs, or scraping — so tests stay hermetic and no unverified
"authority" is smuggled in. The `RetrievalResolver` boundary
(`(query, understanding) -> GroundedContext`) lets future vector/semantic
retrieval replace or complement `lexical-weighted-v1` without touching the
orchestrator or provider architecture.

## Data flow

```
Research records (research_repository.list_all)
       ↓
research_retriever.retrieve(query, understanding, limit)
       ↓
RetrievedLegalSource[] + GroundedContext
       ↓
grounded_context_to_chunks() → AIRequest.retrieved_context
       ↓
Gemini final-answer prompt (STEP 20 owns citation-aware answers)
```

`assistant_service` injects a DB-backed resolver into
`AssistantOrchestrator.process_query(..., retrieval_resolver=...)`.
Explicit caller-supplied `retrieved_context` wins; ESCALATE short-circuits
before any retrieval call; empty retrieval yields `references == []`.

---

# STEP 20 — Grounded Answer Generation & Citation Validation

## Grounded context is supplied to Gemini

The final-answer call receives the retrieved material through the existing
`AIRequest.retrieved_context` field. The system prompt (section 6, "SOURCE
GROUNDING & CITATIONS") instructs Gemini that retrieved material is the
ONLY permitted basis for source-based claims, that `source_id` values must
be copied verbatim, and that nothing (cases, statutes, citations, URLs,
dates, jurisdictions) may be invented. No separate AI call was added; the
existing two-call (understanding + final answer) architecture is unchanged.

## Gemini is not trusted as the authority for source metadata

Every model-generated reference is rebound by the backend deterministic
validator (`app/ai/services/citation_validator.py`):

- The allowlist (`source_id` → source, plus citation labels) is built
  dynamically from the actual `GroundedContext` — never hard-coded.
- Valid references are REBUILT from backend metadata: `title`, `kind`
  (from `source_type`), `citation` (from `citation_label`), `jurisdiction`,
  and `prototype` all come from the retrieved record. Only the model's
  `relevance_note` is preserved, with URL-like tokens sanitized out.

## References are validated against retrieved source IDs

Binding order per candidate: `source_id` first, then `citation` label.
A candidate matching neither is rejected. A known `source_id` paired with
a foreign `citation` is also rejected (no fabricated citation may ride on
a real id). String-only caller context (no `GroundedContext`) admits no
references.

## Unknown references are removed, never replaced

Invalid entries are dropped while the answer prose is preserved; mixed
input keeps the valid entries in stable order; duplicates collapse by
`source_id` (first-seen wins). The validator never invents a replacement
and never remaps an invalid id onto an unrelated source.

## Prototype records remain prototype

The backend `prototype` flag overwrites any model claim, so a prototype
record can never be promoted to verified authority. When cited sources are
all prototype material, a single prototype-limitation notice is appended
to the answer (once).

## No-source responses have no references

Invariant: `GroundedContext.source_count == 0` → `references == []`, no
exceptions. The model may still give general legal information under the
standard disclaimer and guardrails; it must not claim source support it
does not have.

## Validation scope limit

> LexAssist's citation validation verifies reference provenance against
> retrieved records; it does not independently verify the legal correctness
> of the generated answer.

## External verified legal sources are still a future enhancement

The allowlist contains only the curated prototype records present in
LexAssist today. No embeddings, vector search, external APIs, scraping, or
new datasets were added in STEP 20.

---

# STEP 21 — Validated References in the Assistant UI

- The Assistant API (`AssistantMessageResponse`) now exposes an optional
  `references` list of `ValidatedAssistantReference` DTOs
  (`source_id`, `title`, `citation_label`, `source_type`, `jurisdiction`,
  `prototype`). It serializes exactly the STEP 20 citation-validated
  references, in backend order; empty when there are none.
- References are backend-bound: the frontend never generates citation
  metadata, prototype status, or URLs, and never calls the research API to
  reconstruct them. The DTO carries no URL field, so references render as
  information only — no links are invented.
- The Assistant UI renders a "Relevant references" section inside an
  assistant message only when references exist, with a "Prototype research"
  badge whenever `prototype === true`. No-source answers omit the section
  entirely. Prototype material is never labeled official, verified, or
  authoritative.
- References are transient per-response data: conversation persistence
  stores message content only, so no database migration was required. Past
  messages reloaded from history display without references.

This does not establish verified legal authority: displayed references are
curated prototype research records unless the backend explicitly defines
otherwise in a future step.
