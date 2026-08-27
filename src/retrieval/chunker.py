from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
KB_DIR = PROJECT_ROOT / "data" / "knowledge-base"


def clean_chunk(text):
    """Clean obvious Markdown table artifacts."""
    lines = []

    for line in text.splitlines():
        stripped = line.strip()

        # Skip Markdown table separator lines such as |---|---|.
        if stripped and all(char in "|-: " for char in stripped):
            continue

        lines.append(line)

    return "\n".join(lines).strip()


def update_heading(current_heading, text):
    """Find the latest Markdown heading in this section."""
    heading = current_heading

    for line in text.splitlines():
        line = line.strip()

        if line.startswith("#"):
            value = line.lstrip("#").strip()

            if value:
                heading = value

    return heading


def load_kb_documents():
    documents = []

    for path in sorted(KB_DIR.rglob("*.md")):
        text = path.read_text(encoding="utf-8")

        sections = text.split("---")
        current_heading = "General"

        for section in sections:
            section = section.strip()

            if not section:
                continue

            # Capture headings before cleaning.
            current_heading = update_heading(
                current_heading,
                section,
            )

            section = clean_chunk(section)

            if not section:
                continue

            documents.append(
                {
                    "source": str(path.relative_to(KB_DIR)),
                    "section": current_heading,
                    "text": section,
                }
            )

    return documents


if __name__ == "__main__":
    documents = load_kb_documents()

    print("Total KB chunks:", len(documents))

    print("\nFirst 5 chunks:\n")

    for i, document in enumerate(documents[:5], start=1):
        print(f"--- Chunk {i} ---")
        print("Source:", document["source"])
        print("Section:", document["section"])
        print("Text:")
        print(document["text"][:500])
        print()