import json
from collections import Counter

with open("data/tickets.json", "r", encoding="utf-8") as f:
    tickets = json.load(f)

with open("data/accounts.json", "r", encoding="utf-8") as f:
    accounts = json.load(f)

ticket_counts = Counter(
    ticket["account_id"]
    for ticket in tickets
)

accounts_with_tickets = []
accounts_without_tickets = []

for account in accounts:
    account_id = account["account_id"]
    count = ticket_counts[account_id]

    if count > 0:
        accounts_with_tickets.append(account)
    else:
        accounts_without_tickets.append(account)

print("Total account summaries:", len(accounts))
print("Accounts with tickets:", len(accounts_with_tickets))
print("Accounts without tickets:", len(accounts_without_tickets))

print("\n--- Accounts WITH tickets ---")

for account in accounts_with_tickets:
    account_id = account["account_id"]
    print(
        f"{account_id} | "
        f"{account['company']} | "
        f"{ticket_counts[account_id]} tickets"
    )

print("\n--- Accounts WITHOUT tickets ---")

for account in accounts_without_tickets:
    print(
        f"{account['account_id']} | "
        f"{account['company']}"
    )