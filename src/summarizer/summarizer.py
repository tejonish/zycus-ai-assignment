import json
from pathlib import Path
from datetime import datetime, timedelta


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


def load_json(filename):
    path = DATA_DIR / filename

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_accounts():
    return load_json("accounts.json")


def load_tickets():
    return load_json("tickets.json")


def get_account(account_id):
    for account in load_accounts():
        if account.get("account_id") == account_id:
            return account

    return None


def get_account_tickets(account_id):
    tickets = load_tickets()

    return [
        ticket
        for ticket in tickets
        if ticket.get("account_id") == account_id
    ]


def filter_last_90_days(tickets):
    if not tickets:
        return []

    dates = []

    for ticket in tickets:
        created_at = ticket.get("created_at")

        if created_at:
            try:
                dates.append(
                    datetime.fromisoformat(
                        created_at.replace("Z", "+00:00")
                    )
                )
            except ValueError:
                pass

    if not dates:
        return tickets

    latest_date = max(dates)
    cutoff_date = latest_date - timedelta(days=90)

    recent_tickets = []

    for ticket in tickets:
        created_at = ticket.get("created_at")

        if not created_at:
            continue

        try:
            ticket_date = datetime.fromisoformat(
                created_at.replace("Z", "+00:00")
            )
        except ValueError:
            continue

        if ticket_date >= cutoff_date:
            recent_tickets.append(ticket)

    return recent_tickets


def ticket_text(ticket):
    subject = ticket.get("subject", "")
    body = ticket.get("body", "")

    return f"{subject} {body}".strip()


def build_account_health(account_id):
    account = get_account(account_id)

    if not account:
        raise ValueError(f"Account not found: {account_id}")

    all_tickets = get_account_tickets(account_id)

    # Assignment requires the last 90 days of tickets.
    tickets = filter_last_90_days(all_tickets)

    open_tickets = [
        ticket
        for ticket in tickets
        if str(ticket.get("status", "")).lower()
        not in {"closed", "resolved"}
    ]

    high_priority = [
        ticket
        for ticket in tickets
        if str(ticket.get("urgency", "")).upper() in {"P1", "P2"}
    ]

    churn_flags = []
    escalation_flags = []

    # Account-level risk signals
    health_status = str(
        account.get("health_status", "")
    ).lower()

    usage_trend = str(
        account.get("usage_trend", "")
    ).lower()

    if health_status in {"at risk", "critical"}:
        churn_flags.append(
            f"Account health is {account.get('health_status')}."
        )

    if usage_trend in {"inactive", "declining", "down"}:
        churn_flags.append(
            f"Usage trend is {account.get('usage_trend')}."
        )

    # Use the provided escalation notes as explicit account risks.
    for note in account.get("escalation_notes", []):
        escalation_flags.append(note)

        lowered = note.lower()

        if any(
            phrase in lowered
            for phrase in [
                "churn",
                "competing vendor",
                "cancel",
                "unhappy",
            ]
        ):
            churn_flags.append(note)

    # Ticket-level risk signals
    if open_tickets:
        escalation_flags.append(
            f"{len(open_tickets)} open ticket(s) remain unresolved."
        )

    if high_priority:
        escalation_flags.append(
            f"{len(high_priority)} P1/P2 ticket(s) require attention."
        )

    for ticket in tickets:
        text = ticket_text(ticket)
        lowered = text.lower()

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
                f'{ticket.get("ticket_id", "Unknown")}: "{text}"'
            )

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
                f'{ticket.get("ticket_id", "Unknown")}: "{text}"'
            )

    # Remove duplicates while preserving order.
    churn_flags = list(dict.fromkeys(churn_flags))
    escalation_flags = list(dict.fromkeys(escalation_flags))

    company = account.get(
        "company",
        account.get("name", account_id)
    )

    health = account.get("health_status", "Unknown")
    usage = account.get("usage_trend", "Unknown")

    executive_summary = (
        f"{company} is currently {health} with a "
        f"{usage} usage trend. "
        f"The account has {account.get('open_tickets', 0)} "
        f"open ticket(s) according to the account record, while "
        f"{len(tickets)} ticket(s) are available from the last 90 days "
        f"in the ticket dataset. "
        f"There are {len(high_priority)} recent P1/P2 ticket(s), "
        f"and the account has {len(account.get('escalation_notes', []))} "
        f"documented escalation note(s). "
        f"The TAM should prioritize unresolved support risk, "
        f"customer sentiment, and renewal/escalation concerns."
    )

    talking_points = [
        "Review the account's current health status and usage trend.",
        "Review unresolved and high-priority support issues from the last 90 days.",
        "Discuss the documented escalation concerns and confirm an action plan.",
        "Confirm customer priorities, adoption needs, and upcoming renewal considerations.",
    ]

    return {
        "account_id": account_id,
        "account_summary": account,
        "executive_summary": executive_summary,
        "open_risks": {
            "open_ticket_count": account.get("open_tickets", len(open_tickets)),
            "recent_open_ticket_count": len(open_tickets),
            "high_priority_ticket_count": len(high_priority),
            "churn_flags": churn_flags,
            "escalation_flags": escalation_flags,
        },
        "tam_talking_points": talking_points,
        "recent_ticket_count": len(tickets),
        "recent_tickets": tickets,
    }


if __name__ == "__main__":
    accounts = load_accounts()

    if not accounts:
        raise ValueError("No accounts found.")

    account_id = accounts[0].get("account_id")

    result = build_account_health(account_id)

    print(json.dumps(result, indent=2))