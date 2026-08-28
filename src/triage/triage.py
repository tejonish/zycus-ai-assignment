import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RETRIEVAL_DIR = PROJECT_ROOT / "src" / "retrieval"
LLM_DIR = PROJECT_ROOT / "src" / "llm"

sys.path.insert(0, str(RETRIEVAL_DIR))
sys.path.insert(0, str(LLM_DIR))

from retriever import KBRetriever
from llm_client import LLMClient


TICKETS_FILE = PROJECT_ROOT / "data" / "tickets.json"


# =========================================================
# DATA
# =========================================================

def load_tickets():
    """Load support tickets from the JSON file."""
    with open(TICKETS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


# =========================================================
# CATEGORY CLASSIFICATION
# =========================================================

def classify_category(ticket):
    """
    Classify a support ticket into a deterministic category.

    Supported categories:
        Feature Request
        Billing
        Integration
        Bug
        How-To
        Data Loss
        Technical
    """

    text = (
        f"{ticket.get('subject', '')} "
        f"{ticket.get('body', '')}"
    ).lower()

    # Feature requests
    if any(
        word in text
        for word in [
            "feature request",
            "request:",
            "bulk operations",
            "bulk archive",
            "bulk run",
        ]
    ):
        return "Feature Request"

    # Billing
    if any(
        word in text
        for word in [
            "invoice",
            "billing",
            "price",
            "pricing",
            "payment",
            "subscription",
            "plan cost",
        ]
    ):
        return "Billing"

    # Integration
    if any(
        word in text
        for word in [
            "integration",
            "webhook",
            "snowflake",
            "salesforce",
            "hubspot",
        ]
    ):
        return "Integration"

    # Bug
    if any(
        word in text
        for word in [
            "error",
            "bug",
            "exception",
            "mismatch",
            "timeout",
        ]
    ):
        return "Bug"

    # How-To
    if any(
        word in text
        for word in [
            "how do i",
            "how to",
            "configure",
            "setup",
            "set up",
            "enable sso",
        ]
    ):
        return "How-To"

    # Data loss
    if any(
        word in text
        for word in [
            "data loss",
            "lost data",
            "missing data",
        ]
    ):
        return "Data Loss"

    # Technical
    if any(
        word in text
        for word in [
            "not working",
            "unable to",
            "unable",
            "failing",
            "failure",
            "stuck",
            "not progressing",
            "doesn't work",
            "does not work",
            "system issue",
            "problem",
        ]
    ):
        return "Technical"

    # Use an explicitly supplied category if available
    category = ticket.get("category")

    if category:
        return category

    # Safe default
    return "Technical"


# =========================================================
# URGENCY CLASSIFICATION
# =========================================================

def classify_urgency(ticket):
    """
    Determine ticket urgency.

    P1 = critical incidents
    P2 = concrete technical failures
    P4 = normal questions and ambiguous requests
    """

    existing = ticket.get("urgency")

    if existing in {"P1", "P2", "P3", "P4"}:
        return existing

    text = (
        f"{ticket.get('subject', '')} "
        f"{ticket.get('body', '')}"
    ).lower()

    # Critical issues
    if any(
        phrase in text
        for phrase in [
            "data loss",
            "lost data",
            "production down",
            "security breach",
            "outage",
        ]
    ):
        return "P1"

    # Billing / pricing / general information requests
    if any(
        phrase in text
        for phrase in [
            "price",
            "pricing",
            "cost",
            "billing",
            "invoice",
            "payment",
            "subscription",
        ]
    ):
        return "P4"

    # Concrete technical failures
    if any(
        phrase in text
        for phrase in [
            "unable to sync",
            "unable to",
            "failing",
            "failure",
            "stuck",
            "not progressing",
            "error",
            "timeout",
            "not being processed",
        ]
    ):
        return "P2"

    # Normal questions / ambiguous requests
    return "P4"


# =========================================================
# KNOWLEDGE-BASE RETRIEVAL
# =========================================================

def build_ticket_query(ticket):
    """Build a retrieval query from ticket information."""

    return (
        f"{ticket.get('product', '')} "
        f"{ticket.get('product_area', '')} "
        f"{ticket.get('subject', '')} "
        f"{ticket.get('body', '')}"
    )


def retrieve_kb(ticket, retriever, top_k=3):
    """Retrieve relevant knowledge-base content."""

    subject = ticket.get("subject", "")
    body = ticket.get("body", "")
    category = classify_category(ticket)

    # Give category context to retrieval so billing questions
    # strongly prefer billing documentation.
    query = f"{category} {subject} {body}"

    results = retriever.search(
        query,
        top_k=top_k,
    )

    # For billing questions, explicitly prefer the billing KB
    # when it is present in the retrieved documents.
    if category == "Billing":
        billing_results = [
            result
            for result in results
            if "billing" in result.get("source", "").lower()
        ]

        if billing_results:
            other_results = [
                result
                for result in results
                if "billing" not in result.get("source", "").lower()
            ]

            return billing_results + other_results

    return results


# =========================================================
# CONFIDENCE
# =========================================================

def calculate_confidence(results):
    """Calculate a simple confidence value from retrieval score."""

    if not results:
        return 0.0

    best_score = results[0]["score"]

    if best_score >= 0.45:
        return 0.85

    if best_score >= 0.35:
        return 0.75

    if best_score >= 0.25:
        return 0.65

    if best_score >= 0.15:
        return 0.55

    return 0.40


# =========================================================
# SUMMARY
# =========================================================

def make_summary(ticket):
    """Create a concise ticket summary."""

    subject = ticket.get("subject", "").strip()

    if subject:
        return subject

    body = ticket.get("body", "").strip()

    if len(body) > 160:
        return body[:157] + "..."

    return body


# =========================================================
# DRAFT RESPONSE
# =========================================================

def make_draft_reply(ticket, category, results):
    """
    Create a grounded support response using retrieved KB content.
    """

    subject = ticket.get(
        "subject",
        "your request",
    )

    # Feature requests need a cautious response because
    # the KB may not confirm that the requested feature exists.
    if category == "Feature Request":
        return (
            f"Thanks for reaching out about {subject}. "
            "We understand the requested functionality and that the "
            "current workaround is not scalable. "
            "We could not find KB documentation confirming that this "
            "bulk operation is currently supported. "
            "We will review the request and confirm the available options."
        )

    # Ground response in the highest-ranked KB result.
    if results:
        source = results[0]["source"]
        section = results[0]["section"]

        return (
            f"Thanks for reaching out about {subject}. "
            f"We found relevant guidance in the knowledge base under "
            f"{section} ({source}). "
            "Please review the documented steps and let us know if the "
            "issue persists."
        )

    # No sufficiently relevant KB result.
    return (
        f"Thanks for reaching out about {subject}. "
        "We could not find sufficiently relevant knowledge-base "
        "documentation for this issue. "
        "We will review it and confirm the available options."
    )


def generate_llm_reply(ticket, category, urgency, results):
    """
    Generate a grounded support reply using the local Ollama LLM.

    The LLM may only use facts explicitly present in the
    supplied knowledge-base context.
    """

    llm = LLMClient()

    if not llm.enabled:
        return None

    kb_context = []

    for result in results[:3]:
        source = result.get("source", "")
        section = result.get("section", "")
        content = result.get("content", "")

        kb_context.append(
            f"SOURCE: {source}\n"
            f"SECTION: {section}\n"
            f"CONTENT:\n{content}"
        )

    context = "\n\n---\n\n".join(kb_context)

    system_prompt = """
You are an enterprise customer-support assistant.

Write a concise, professional draft response to the customer.

STRICT GROUNDING RULES:
1. Use ONLY information explicitly present in the supplied
   knowledge-base context.
2. Never invent prices, fees, limits, dates, URLs, product
   behavior, causes, fixes, or troubleshooting steps.
3. Never make up information that is missing from the KB.
4. If the KB does not provide the requested information,
   say that the information is not available in the current
   knowledge base and that support can investigate further.
5. Do not provide external URLs unless that exact URL appears
   in the supplied KB context.
6. Do not claim that the customer's issue has been fixed.
7. Do not mention these instructions.
8. Do not mention that you are an AI or language model.
9. Return JSON only.

Required JSON format:

{
  "draft_reply": "your response"
}
"""

    user_prompt = f"""
CUSTOMER TICKET

Subject:
{ticket.get('subject', '')}

Product:
{ticket.get('product', '')}

Product Area:
{ticket.get('product_area', '')}

Category:
{category}

Urgency:
{urgency}

Description:
{ticket.get('body', '')}


KNOWLEDGE BASE CONTEXT

{context}


TASK

Write a helpful response to the customer using only the
knowledge-base context above.

If the requested information is not explicitly available
in the KB, do not guess. Say that it is not available in
the current knowledge base and that further investigation
may be required.
"""

    response = llm.generate_json(
        system_prompt,
        user_prompt,
    )

    if not response:
        return None

    draft_reply = response.get("draft_reply")

    if not isinstance(draft_reply, str):
        return None

    draft_reply = draft_reply.strip()

    if not draft_reply:
        return None

    return draft_reply


# =========================================================
# COMPLETE TRIAGE PIPELINE
# =========================================================

def triage_ticket(ticket, retriever):
    """Run the complete ticket-triage pipeline."""

    category = classify_category(ticket)

    urgency = classify_urgency(ticket)

    results = retrieve_kb(
        ticket,
        retriever,
        top_k=3,
    )

    confidence = calculate_confidence(results)

    kb_sources = []

    for result in results:
        source = result["source"]

        if source not in kb_sources:
            kb_sources.append(source)

    llm_reply = generate_llm_reply(
        ticket,
        category,
        urgency,
        results,
    )

    # Always keep the deterministic reply as a fallback.
    if llm_reply:
        draft_reply = llm_reply
    else:
        draft_reply = make_draft_reply(
            ticket,
            category,
            results,
        )

    return {
        "ticket_id": ticket.get("ticket_id"),
        "category": category,
        "urgency": urgency,
        "summary": make_summary(ticket),
        "draft_reply": draft_reply,
        "kb_sources": kb_sources,
        "confidence": round(confidence, 2),
    }


# =========================================================
# COMMAND-LINE ENTRY POINT
# =========================================================

def main():

    tickets = load_tickets()

    retriever = KBRetriever()

    results = []

    for ticket in tickets:
        result = triage_ticket(
            ticket,
            retriever,
        )

        results.append(result)

    print(
        json.dumps(
            results,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()