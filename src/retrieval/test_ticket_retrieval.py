import json
import sys
from pathlib import Path

# Allow importing retriever.py from this directory.
sys.path.append(str(Path(__file__).parent))

from retriever import KBRetriever


with open(
    "data/tickets.json",
    "r",
    encoding="utf-8",
) as f:
    tickets = json.load(f)


retriever = KBRetriever()

for ticket in tickets[:5]:
    query = (
    f"{ticket['product']} "
    f"{ticket['product']} "
    f"{ticket['product_area']} "
    f"{ticket['product_area']} "
    f"{ticket['subject']} "
    f"{ticket['subject']} "
    f"{ticket['body']}"
    )

    print("=" * 80)
    print("TICKET:", ticket["ticket_id"])
    print("SUBJECT:", ticket["subject"])
    print()

    results = retriever.search(query, top_k=3)

    for i, result in enumerate(results, start=1):
        print(
            f"{i}. "
            f"{result['source']} | "
            f"{result['section']} | "
            f"score={result['score']:.4f}"
        )

    print()