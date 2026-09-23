"""Minimal deterministic prototype datasets for the LexAssist API.

Everything here is clearly labeled prototype/demo data. Nothing is an
authoritative legal source. Repositories read from these structures only.
"""

PROTOTYPE_JURISDICTION = "Prototype / General"

ASSISTANT_PROTOTYPE_REPLY = (
    "LexAssist prototype response: your message was received. "
    "Real AI-assisted legal analysis will be connected in a later "
    "integration step."
)

ASSISTANT_CONVERSATIONS = {
    "conversation-demo": {
        "conversation_id": "conversation-demo",
        "messages": [
            {
                "message_id": "message-demo-1",
                "role": "user",
                "content": "I rented a house and my landlord is refusing to return my security deposit after I moved out. What should I do?",
            },
            {
                "message_id": "message-demo-2",
                "role": "assistant",
                "content": "LexAssist prototype response: this demonstration conversation shows how a rental-deposit concern could be structured. Real AI-assisted legal analysis will be connected in a later integration step.",
            },
        ],
    }
}

DOCUMENT_TEMPLATES = [
    {
        "type": "rental",
        "title": "Rental Agreement",
        "description": "Create a structured rental agreement draft from property and tenancy details.",
        "category": "Tenancy",
    },
    {
        "type": "employment",
        "title": "Employment Agreement",
        "description": "Prepare a structured employment agreement draft from role and employment details.",
        "category": "Employment",
    },
    {
        "type": "nda",
        "title": "Non-Disclosure Agreement",
        "description": "Create a structured NDA draft from the parties and confidentiality requirements.",
        "category": "Confidentiality",
    },
    {
        "type": "will",
        "title": "Will / Testament",
        "description": "Organize basic information for a will or testament draft.",
        "category": "Estate",
    },
]

DOCUMENTS = {
    "rental-agreement-demo": {
        "document_id": "rental-agreement-demo",
        "type": "rental",
        "title": "Rental Agreement Draft",
        "status": "Prototype Draft",
        "created_date": "Sep 20, 2026",
        "details": {
            "landlordName": "Rajiv Reddy",
            "tenantName": "Example Tenant",
            "propertyAddress": "Example Address",
        },
    }
}

RESEARCH_RECORDS = [
    {
        "result_id": "rental-deposit-dispute",
        "title": "Rental Deposit Dispute — Prototype Research Record",
        "source_type": "case",
        "jurisdiction": PROTOTYPE_JURISDICTION,
        "date": "Sep 20, 2026",
        "citation_label": "Demo case record",
        "summary": "A demonstration record showing how rental-deposit issues could be organized for legal research.",
        "topics": ["Rental housing", "Security deposit", "Tenant rights"],
    },
    {
        "result_id": "employment-termination",
        "title": "Employment Termination — Prototype Research Record",
        "source_type": "precedent",
        "jurisdiction": PROTOTYPE_JURISDICTION,
        "date": "Sep 12, 2026",
        "citation_label": "Prototype reference",
        "summary": "A demonstration record showing how employment-ending scenarios could be organized for legal research.",
        "topics": ["Employment", "Termination procedures", "Workplace rights"],
    },
    {
        "result_id": "confidentiality-obligations",
        "title": "Confidentiality Obligations — Prototype Research Record",
        "source_type": "regulation",
        "jurisdiction": PROTOTYPE_JURISDICTION,
        "date": "Aug 28, 2026",
        "citation_label": "Prototype reference",
        "summary": "A demonstration record showing how confidentiality duties could be organized for legal research.",
        "topics": ["Confidentiality", "Business agreements", "Disclosure duties"],
    },
    {
        "result_id": "property-ownership-dispute",
        "title": "Property Ownership Dispute — Prototype Research Record",
        "source_type": "statute",
        "jurisdiction": PROTOTYPE_JURISDICTION,
        "date": "Aug 15, 2026",
        "citation_label": "General reference",
        "summary": "A demonstration record showing how property-ownership questions could be organized for legal research.",
        "topics": ["Property ownership", "Title records", "Boundary questions"],
    },
    {
        "result_id": "contract-review-basics",
        "title": "Contract Review Basics — Prototype Research Record",
        "source_type": "general-reference",
        "jurisdiction": PROTOTYPE_JURISDICTION,
        "date": "Jul 30, 2026",
        "citation_label": "General reference",
        "summary": "A demonstration record showing how contract-review topics could be organized for legal research.",
        "topics": ["Contracts", "Review checklist", "Signatures"],
    },
]

HISTORY_ITEMS = [
    {
        "item_id": "history-rental-deposit-session",
        "type": "assistant",
        "title": "Rental Deposit Question",
        "description": "Prototype assistant session demonstrating structured legal issue analysis.",
        "category": "Rental / Housing",
        "status": "completed",
        "updated_at": "Sep 21, 2026",
        "related_route": "/app/assistant",
    },
    {
        "item_id": "history-rental-agreement-draft",
        "type": "document",
        "title": "Rental Agreement Draft",
        "description": "Prototype document draft demonstrating the guided document workflow.",
        "category": "Tenancy",
        "status": "draft",
        "updated_at": "Sep 20, 2026",
        "related_route": "/app/documents/rental-agreement-demo",
    },
    {
        "item_id": "history-security-deposit-research",
        "type": "research",
        "title": "Security Deposit Dispute Research",
        "description": "Prototype research activity demonstrating organized legal references.",
        "category": "Rental / Housing",
        "status": "prototype",
        "updated_at": "Sep 20, 2026",
        "related_route": "/app/research",
    },
]
