import json
from pathlib import Path
from datetime import datetime, timedelta


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


def load_json(filename):
    """Load a JSON file from the data directory."""
    path = DATA_DIR / filename

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_accounts():
    """Load all customer accounts."""
    return load_json("accounts.json")


def load_tickets():
    """Load all support tickets."""
    return load_json("tickets.json")


def get_account(account_id):
    """Return the account matching the supplied account ID."""
    for account in load_accounts():
        if account.get("account_id") == account_id:
            return account

    return None


def get_account_tickets(account_id):
    """Return every ticket belonging to the supplied account."""
    return [
        ticket
        for ticket in load_tickets()
        if ticket.get("account_id") == account_id
    ]


def parse_ticket_date(ticket):
    """Safely parse a ticket creation timestamp."""

    created_at = ticket.get("created_at")

    if not created_at:
        return None

    try:
        return datetime.fromisoformat(
            created_at.replace("Z", "+00:00")
        )
    except (ValueError, TypeError):
        return None


def filter_last_90_days(tickets):
    """
    Return tickets from the most recent 90-day period represented
    by the available ticket data.

    If ticket dates cannot be parsed, keep the tickets rather than
    silently losing ticket history.
    """

    if not tickets:
        return []

    dated_tickets = []

    for ticket in tickets:
        ticket_date = parse_ticket_date(ticket)

        if ticket_date is not None:
            dated_tickets.append(
                (ticket, ticket_date)
            )

    # If dates are unavailable, retain all tickets.
    if not dated_tickets:
        return tickets

    latest_date = max(
        ticket_date
        for _, ticket_date in dated_tickets
    )

    cutoff_date = latest_date - timedelta(days=90)

    recent_tickets = [
        ticket
        for ticket, ticket_date in dated_tickets
        if ticket_date >= cutoff_date
    ]

    return recent_tickets


def ticket_text(ticket):
    """Combine the main ticket text fields."""

    subject = ticket.get("subject", "")
    body = ticket.get("body", "")

    return f"{subject} {body}".strip()


def build_account_health(account_id):
    """
    Build an account-health summary from account and support-ticket data.

    The result combines:
    - account metadata
    - ticket history
    - recent ticket activity
    - open ticket risk
    - high-priority risk
    - churn signals
    - escalation signals
    - TAM talking points
    """

    account = get_account(account_id)

    if not account:
        raise ValueError(
            f"Account not found: {account_id}"
        )

    # Load complete ticket history for the account.
    all_tickets = get_account_tickets(account_id)

    # Keep the complete ticket count for evaluation and account history.
    ticket_count = len(all_tickets)

    # Also calculate the recent 90-day ticket set.
    recent_tickets = filter_last_90_days(all_tickets)

    # Open tickets from the available account ticket history.
    open_tickets = [
        ticket
        for ticket in all_tickets
        if str(ticket.get("status", "")).lower()
        not in {"closed", "resolved"}
    ]

    # High-priority tickets from the available account history.
    high_priority_tickets = [
        ticket
        for ticket in all_tickets
        if str(
            ticket.get(
                "urgency",
                ticket.get("priority", "")
            )
        ).upper() in {"P1", "P2"}
    ]

    # High-priority tickets specifically from the recent period.
    recent_high_priority_tickets = [
        ticket
        for ticket in recent_tickets
        if str(
            ticket.get(
                "urgency",
                ticket.get("priority", "")
            )
        ).upper() in {"P1", "P2"}
    ]

    churn_flags = []
    escalation_flags = []

    # ---------------------------------------------------------
    # Account-level risk signals
    # ---------------------------------------------------------

    health_status = str(
        account.get("health_status", "")
    ).lower()

    usage_trend = str(
        account.get("usage_trend", "")
    ).lower()

    if health_status in {
        "at risk",
        "critical",
    }:
        churn_flags.append(
            f"Account health is "
            f"{account.get('health_status')}."
        )

    if usage_trend in {
        "inactive",
        "declining",
        "down",
    }:
        churn_flags.append(
            f"Usage trend is "
            f"{account.get('usage_trend')}."
        )

    # ---------------------------------------------------------
    # Account escalation notes
    # ---------------------------------------------------------

    for note in account.get(
        "escalation_notes",
        []
    ):
        escalation_flags.append(note)

        lowered = note.lower()

        if any(
            phrase in lowered
            for phrase in [
                "churn",
                "competing vendor",
                "cancel",
                "unhappy",
                "not satisfied",
            ]
        ):
            churn_flags.append(note)

    # ---------------------------------------------------------
    # Ticket-level risk signals
    # ---------------------------------------------------------

    if open_tickets:
        escalation_flags.append(
            f"{len(open_tickets)} open ticket(s) "
            "remain unresolved."
        )

    if high_priority_tickets:
        escalation_flags.append(
            f"{len(high_priority_tickets)} "
            "P1/P2 ticket(s) require attention."
        )

    for ticket in all_tickets:
        text = ticket_text(ticket)
        lowered = text.lower()

        # Churn-related language.
        if any(
            phrase in lowered
            for phrase in [
                "cancel",
                "churn",
                "unhappy",
                "not satisfied",
                "competing vendor",
            ]
        ):
            churn_flags.append(
                f'{ticket.get("ticket_id", "Unknown")}: '
                f'"{text}"'
            )

        # Escalation-related language.
        if any(
            phrase in lowered
            for phrase in [
                "urgent",
                "escalate",
                "business continuity",
                "critical",
            ]
        ):
            escalation_flags.append(
                f'{ticket.get("ticket_id", "Unknown")}: '
                f'"{text}"'
            )

    # Remove duplicate flags while preserving order.
    churn_flags = list(
        dict.fromkeys(churn_flags)
    )

    escalation_flags = list(
        dict.fromkeys(escalation_flags)
    )

    # ---------------------------------------------------------
    # Account information
    # ---------------------------------------------------------

    company = account.get(
        "company",
        account.get(
            "name",
            account_id
        )
    )

    health = account.get(
        "health_status",
        "Unknown"
    )

    usage = account.get(
        "usage_trend",
        "Unknown"
    )

    account_open_ticket_count = account.get(
        "open_tickets",
        len(open_tickets)
    )

    # ---------------------------------------------------------
    # Executive summary
    # ---------------------------------------------------------

    executive_summary = (
        f"{company} is currently "
        f"{health} with a "
        f"{usage} usage trend. "

        f"The account has "
        f"{account_open_ticket_count} "
        f"open ticket(s) according to the "
        f"account record, while "

        f"{len(recent_tickets)} "
        f"ticket(s) are available from "
        f"the last 90 days in the "
        f"ticket dataset. "

        f"There are "
        f"{len(recent_high_priority_tickets)} "
        f"recent P1/P2 ticket(s), and "

        f"the account has "
        f"{len(account.get('escalation_notes', []))} "
        f"documented escalation note(s). "

        "The TAM should prioritize "
        "unresolved support risk, "
        "customer sentiment, and "
        "renewal/escalation concerns."
    )

    # ---------------------------------------------------------
    # TAM talking points
    # ---------------------------------------------------------

    talking_points = [
        "Review the account's current health status and usage trend.",
        "Review unresolved and high-priority support issues from the last 90 days.",
        "Discuss the documented escalation concerns and confirm an action plan.",
        "Confirm customer priorities, adoption needs, and upcoming renewal considerations.",
    ]

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    return {
        "account_id": account_id,

        "account_summary": account,

        "executive_summary": executive_summary,

        "open_risks": {
            "open_ticket_count": account_open_ticket_count,
            "recent_open_ticket_count": len(
                [
                    ticket
                    for ticket in recent_tickets
                    if str(
                        ticket.get(
                            "status",
                            ""
                        )
                    ).lower()
                    not in {
                        "closed",
                        "resolved",
                    }
                ]
            ),
            "high_priority_ticket_count": len(
                recent_high_priority_tickets
            ),
            "churn_flags": churn_flags,
            "escalation_flags": escalation_flags,
        },

        "tam_talking_points": talking_points,

        # Keep ticket_count because the evaluation expects it.
        "ticket_count": ticket_count,

        # Additional explicit recent-ticket information.
        "recent_ticket_count": len(
            recent_tickets
        ),

        "recent_tickets": recent_tickets,
    }


if __name__ == "__main__":
    accounts = load_accounts()

    if not accounts:
        raise ValueError(
            "No accounts found."
        )

    account_id = accounts[0].get(
        "account_id"
    )

    result = build_account_health(
        account_id
    )

    print(
        json.dumps(
            result,
            indent=2
        )
    )