"""Deterministic legal safety, risk evaluation, and guardrails."""

import re
from app.ai.models.responses import (
    SafetyAssessment,
    SafetyFlag,
    SafetyStatus,
)

CENTRAL_LEGAL_DISCLAIMER = (
    "LexAssist provides AI-assisted legal information and document drafting assistance "
    "for informational purposes only. It is not a law firm and does not provide legal "
    "advice or formal representation. Using this service does not establish an "
    "attorney-client relationship. Legal outcomes depend on specific jurisdictions "
    "and factual circumstances; always consult a qualified legal professional for "
    "advice on specific legal matters."
)

# High-Risk Escalation Patterns: Immediate danger, criminal detention, urgent court deadlines, or fraud
_ESCALATION_RULES: list[dict[str, str]] = [
    {
        "pattern": r"\b(kill|suicide|physically harm|domestic abuse|domestic violence|immediate danger)\b",
        "flag_name": "emergency_physical_safety",
        "category": "Immediate Emergency",
        "description": "Situation involves immediate physical danger, domestic harm, or emergency safety concerns.",
    },
    {
        "pattern": r"\b(court tomorrow|hearing tomorrow|hearing today|trial tomorrow|warrant for my arrest)\b",
        "flag_name": "imminent_court_deadline",
        "category": "Imminent Judicial Deadline",
        "description": "User faces an urgent court appearance or deadline within 24-48 hours.",
    },
    {
        "pattern": r"\b(arrested|in jail|custody of police|police interrogation|charged with felony)\b",
        "flag_name": "criminal_custody_interrogation",
        "category": "Criminal Incarceration / Custody",
        "description": "User is undergoing active arrest, detention, or criminal interrogation requiring defense counsel.",
    },
    {
        "pattern": r"\b(hide assets from (the )?court|forge (a )?signature|fake evidence|commit perjury|evade (the )?police)\b",
        "flag_name": "fraud_and_law_evasion",
        "category": "Illegal Conduct / Fraud",
        "description": "Request seeks assistance in committing fraud, perverting justice, or evading law enforcement.",
    },
]

# Caution Patterns: Formal notices, impending litigation, debt garnishment, eviction
_CAUTION_RULES: list[dict[str, str]] = [
    {
        "pattern": r"\b(legal notice|eviction notice|received a summons|served with papers|lawsuit against me|foreclosure notice)\b",
        "flag_name": "active_legal_notice",
        "category": "Formal Legal Process",
        "description": "User received formal process or notice with statutory response windows.",
    },
    {
        "pattern": r"\b(wage garnishment|bank levy|sued for debt|debt collection lawsuit)\b",
        "flag_name": "debt_enforcement",
        "category": "Financial Enforcement",
        "description": "User faces active collection or asset garnishment proceedings.",
    },
]

# Forbidden terms in generated content
_PROHIBITED_OUTPUT_PATTERNS: list[str] = [
    r"i guarantee (you will|you'll|a favorable) win",
    r"you are (100%|guaranteed) immune from liability",
    r"as your (lawyer|attorney), i advise",
    r"this is (formal|official) legal advice",
]


def assess_request(user_message: str) -> SafetyAssessment:
    """Evaluate an incoming user message deterministically for legal and safety risks."""
    text = user_message.lower().strip()
    flags: list[SafetyFlag] = []

    # 1. Check Escalation Triggers
    for rule in _ESCALATION_RULES:
        if re.search(rule["pattern"], text, re.IGNORECASE):
            flags.append(
                SafetyFlag(
                    flag_name=rule["flag_name"],
                    category=rule["category"],
                    description=rule["description"],
                )
            )

    if flags:
        return SafetyAssessment(
            status=SafetyStatus.ESCALATE,
            flags=flags,
            requires_professional_review=True,
            advisory_message=(
                "URGENT: Your inquiry involves an urgent, critical, or emergency matter. "
                "LexAssist cannot provide emergency response or legal representation. "
                "Please contact emergency services (if in danger) or an attorney immediately."
            ),
        )

    # 2. Check Caution Triggers
    for rule in _CAUTION_RULES:
        if re.search(rule["pattern"], text, re.IGNORECASE):
            flags.append(
                SafetyFlag(
                    flag_name=rule["flag_name"],
                    category=rule["category"],
                    description=rule["description"],
                )
            )

    if flags:
        return SafetyAssessment(
            status=SafetyStatus.CAUTION,
            flags=flags,
            requires_professional_review=True,
            advisory_message=(
                "NOTICE: This situation involves formal legal notices or active proceedings. "
                "Statutory response deadlines may apply. We strongly recommend having an attorney "
                "review your documents."
            ),
        )

    # 3. Default Safe Assessment
    return SafetyAssessment(
        status=SafetyStatus.SAFE,
        flags=[],
        requires_professional_review=False,
        advisory_message="",
    )


def validate_response(
    content: str, assessment: SafetyAssessment
) -> tuple[bool, list[str]]:
    """Verify that a generated response adheres to legal guardrails and does not make forbidden claims."""
    violations: list[str] = []
    text = content.lower()

    for pattern in _PROHIBITED_OUTPUT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            violations.append(f"Response contains prohibited representation claim matching: {pattern}")

    is_valid = len(violations) == 0
    return is_valid, violations
