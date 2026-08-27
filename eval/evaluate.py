import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "retrieval"))

from retriever import KBRetriever


def main():
    with open(PROJECT_ROOT / "eval" / "test_cases.json", encoding="utf-8") as file:
        test_cases = json.load(file)

    retriever = KBRetriever()

    passed = 0

    for case in test_cases:
        results = retriever.search(case["query"], top_k=3)

        sources = [result["source"] for result in results]

        if case["expected_source"] in sources:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"

        print(f"{status}: {case['query']}")

    print()
    print(f"Passed: {passed}/{len(test_cases)}")


if __name__ == "__main__":
    main()