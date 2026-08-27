import json
import sys
from pathlib import Path

# Allow imports from src/retrieval
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RETRIEVAL_DIR = PROJECT_ROOT / "src" / "retrieval"

sys.path.insert(0, str(RETRIEVAL_DIR))

from retriever import KBRetriever


TICKETS_FILE = PROJECT_ROOT / "data" / "tickets.json"


def load_tickets():
    """Load support tickets from the JSON file."""
    with open(TICKETS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def classify_category(ticket):
    """
    Lightweight rule-based category classification.

    Since we do not have an OpenAI API key, this keeps the
    classification deterministic and local.
    """
    text = (
        f"{ticket.get('subject', '')} "
        f"{ticket.get('body', '')}"
    ).lower()

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

    if any(
        word in text
        for word in [
            "invoice",
            "billing",
            "price",
            "pricing",
            "payment",
            "subscription",
        ]
    ):
        return "Billing"

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

    if any(
        word in text
        for word in [
            "how do i",
            "how to",
            "configure",
            "setup",
            "set up",
        ]
    ):
        return "How-To"

    if any(
        word in text
        for word in [
            "data loss",
            "lost data",
            "missing data",
        ]
    ):
        return "Data Loss"

    return ticket.get("category", "General")


def classify_urgency(ticket):
    """Use the ticket's existing urgency when available."""
    urgency = ticket.get("urgency")

    if urgency in {"P1", "P2", "P3", "P4"}:
        return urgency

    return "P3"


def build_ticket_query(ticket):
    """
    Build a retrieval query using the important ticket fields.
    """
    return (
        f"{ticket.get('product', '')} "
        f"{ticket.get('product_area', '')} "
        f"{ticket.get('subject', '')} "
        f"{ticket.get('body', '')}"
    )


def retrieve_kb(ticket, retriever, top_k=3):
    """Retrieve relevant KB chunks for the ticket."""
    query = build_ticket_query(ticket)

    return retriever.search(
        query,
        top_k=top_k,
    )


def calculate_confidence(results):
    """
    Estimate confidence from the best retrieval score.

    This is not an LLM confidence score.
    It is a simple retrieval-based heuristic.
    """
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


def make_summary(ticket):
    """Create a concise ticket summary."""
    subject = ticket.get("subject", "").strip()

    if subject:
        return subject

    body = ticket.get("body", "").strip()

    if len(body) > 160:
        return body[:157] + "..."

    return body


def make_draft_reply(ticket, category, results):
    """
    Generate a grounded local draft reply.

    Important:
    We do not claim that a feature exists unless the KB supports it.
    """
    subject = ticket.get("subject", "your request")

    if category == "Feature Request":
        return (
            f"Thanks for reaching out about {subject}. "
            "We understand the requested functionality and that the "
            "current workaround is not scalable. "
            "We could not find KB documentation confirming that this "
            "bulk operation is currently supported. "
            "We will review the request and confirm the available options."
        )

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

    return (
        f"Thanks for reaching out about {subject}. "
        "We could not find sufficiently relevant knowledge-base "
        "documentation for this issue. "
        "We will review it and confirm the available options."
    )


def triage_ticket(ticket, retriever):
    """Run the complete local triage pipeline."""
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

    return {
        "ticket_id": ticket.get("ticket_id"),
        "category": category,
        "urgency": urgency,
        "summary": make_summary(ticket),
        "draft_reply": make_draft_reply(
            ticket,
            category,
            results,
        ),
        "kb_sources": kb_sources,
        "confidence": round(confidence, 2),
    }


def main():
    tickets = load_tickets()

    retriever = KBRetriever()

    # Process the first ticket for now.
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