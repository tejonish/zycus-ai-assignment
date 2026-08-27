import json


with open("data/tickets.json", "r", encoding="utf-8") as f:
    tickets = json.load(f)


for ticket in tickets[:10]:
    print("=" * 80)
    print("Ticket:", ticket["ticket_id"])
    print("Product:", ticket["product"])
    print("Product area:", ticket["product_area"])
    print("Category:", ticket["category"])
    print("Urgency:", ticket["urgency"])
    print("Status:", ticket["status"])
    print("Subject:", ticket["subject"])
    print("Body:")
    print(ticket["body"])
    print()