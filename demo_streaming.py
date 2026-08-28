import sys

sys.path.insert(0, "src/triage")
sys.path.insert(0, "src/retrieval")
sys.path.insert(0, "src/llm")

from triage import retrieve_kb
from retriever import KBRetriever
from llm_client import LLMClient


def main():
    ticket = {
        "subject": "How much does the Business plan cost?",
        "body": "Please provide pricing information for the Business plan.",
    }

    retriever = KBRetriever()

    # Retrieve relevant KB context
    results = retrieve_kb(
        ticket,
        retriever,
        top_k=3,
    )

    context = []

    for result in results:
        context.append(
            f"Source: {result.get('source', '')}\n"
            f"Section: {result.get('section', '')}\n"
            f"Content:\n{result.get('content', '')}"
        )

    kb_context = "\n\n---\n\n".join(context)

    system_prompt = """
You are a customer support assistant.

Generate a concise, professional customer-facing reply.

Use ONLY the supplied knowledge-base context.

Do not invent:
- pricing
- product capabilities
- troubleshooting steps
- URLs

If the knowledge base does not contain enough information,
say that further review is required.
"""

    user_prompt = f"""
Ticket subject:
{ticket["subject"]}

Ticket body:
{ticket["body"]}

Knowledge-base context:

{kb_context}

Write the customer-facing reply.
"""

    client = LLMClient()

    if not client.enabled:
        print("Ollama model is unavailable.")
        return

    print("\n=== Streaming LLM Response ===\n")

    for chunk in client.generate_stream(
        system_prompt,
        user_prompt,
    ):
        print(chunk, end="", flush=True)

    print("\n")


if __name__ == "__main__":
    main()