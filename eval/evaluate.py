import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT / "src" / "retrieval"))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "triage"))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "summarizer"))

from retriever import KBRetriever
from triage import triage_ticket
from summarizer import build_account_health


# ============================================================
# TASK 0: RETRIEVAL EVALUATION
# ============================================================

def score_retrieval(case, retriever):
    results = retriever.search(
        case["query"],
        top_k=3,
    )

    sources = [
        result["source"]
        for result in results
    ]

    expected_source = case["expected_source"]

    if expected_source not in sources:
        return {
            "status": "FAIL",
            "score": 0.0,
            "details": (
                "Expected source was not found "
                "in the top 3 results."
            ),
        }

    rank = sources.index(expected_source)

    if rank == 0:
        score = 1.0
    elif rank == 1:
        score = 0.9
    else:
        score = 0.8

    return {
        "status": "PASS",
        "score": score,
        "details": (
            f"Expected source found at rank {rank + 1}."
        ),
    }


# ============================================================
# TASK 1: TICKET TRIAGE
# ============================================================

def score_triage(case, retriever):
    try:
        result = triage_ticket(
            case["ticket"],
            retriever,
        )

        checks = []

        # Category
        if "category" in case:
            checks.append(
                result.get("category")
                == case["category"]
            )

        # Urgency
        if "urgency" in case:
            checks.append(
                result.get("urgency")
                == case["urgency"]
            )

        # Expected KB source
        if "expected_source" in case:
            sources = result.get(
                "kb_sources",
                [],
            )

            checks.append(
                case["expected_source"]
                in sources
            )

        # Responder team
        if "responder_team" in case:
            checks.append(
                result.get("responder_team")
                == case["responder_team"]
            )

        if not checks:
            return {
                "status": "FAIL",
                "score": 0.0,
                "details": (
                    "No acceptance criteria defined."
                ),
            }

        passed_checks = sum(checks)
        total_checks = len(checks)

        score = passed_checks / total_checks

        return {
            "status": (
                "PASS"
                if score == 1.0
                else "FAIL"
            ),
            "score": round(score, 2),
            "details": (
                f"{passed_checks}/{total_checks} "
                "acceptance criteria passed."
            ),
        }

    except Exception as exc:
        return {
            "status": "FAIL",
            "score": 0.0,
            "details": f"Error: {exc}",
        }


# ============================================================
# TASK 2: ACCOUNT HEALTH
# ============================================================

def score_account_health(case):
    try:
        result = build_account_health(
            case["account_id"]
        )

        checks = []

        # Company
        if case.get("company"):
            checks.append(
                result["account_summary"].get(
                    "company"
                )
                == case["company"]
            )

        # Health status
        if case.get("health_status"):
            checks.append(
                result["account_summary"].get(
                    "health_status"
                )
                == case["health_status"]
            )

        # Usage trend
        if case.get("usage_trend"):
            checks.append(
                result["account_summary"].get(
                    "usage_trend"
                )
                == case["usage_trend"]
            )

        # Minimum ticket count
        if case.get("min_ticket_count") is not None:
            checks.append(
                result.get("ticket_count", 0)
                >= case["min_ticket_count"]
            )

        # Churn flag
        if case.get("requires_churn_flag"):
            checks.append(
                len(
                    result["open_risks"].get(
                        "churn_flags",
                        [],
                    )
                )
                > 0
            )

        # Escalation flag
        if case.get("requires_escalation_flag"):
            checks.append(
                len(
                    result["open_risks"].get(
                        "escalation_flags",
                        [],
                    )
                )
                > 0
            )

        if not checks:
            return {
                "status": "FAIL",
                "score": 0.0,
                "details": (
                    "No acceptance criteria defined."
                ),
            }

        passed_checks = sum(checks)
        total_checks = len(checks)

        score = passed_checks / total_checks

        return {
            "status": (
                "PASS"
                if score == 1.0
                else "FAIL"
            ),
            "score": round(score, 2),
            "details": (
                f"{passed_checks}/{total_checks} "
                "acceptance criteria passed."
            ),
        }

    except ValueError as exc:
        # ----------------------------------------------------
        # Adversarial / unknown account handling
        #
        # If the evaluation case deliberately uses a nonexistent
        # account, rejecting it is the correct behavior.
        # ----------------------------------------------------
        if case.get("account_id") == "ACC-DOES-NOT-EXIST":
            return {
                "status": "PASS",
                "score": 1.0,
                "details": (
                    "Unknown account was correctly rejected."
                ),
            }

        return {
            "status": "FAIL",
            "score": 0.0,
            "details": f"Error: {exc}",
        }

    except Exception as exc:
        return {
            "status": "FAIL",
            "score": 0.0,
            "details": f"Error: {exc}",
        }


# ============================================================
# MAIN EVALUATION
# ============================================================

def main():
    eval_dir = PROJECT_ROOT / "eval"

    # --------------------------------------------------------
    # Load retrieval test cases
    # --------------------------------------------------------

    retrieval_path = (
        eval_dir / "test_cases.json"
    )

    with open(
        retrieval_path,
        encoding="utf-8",
    ) as file:
        retrieval_cases = json.load(file)

    # --------------------------------------------------------
    # Load triage test cases
    # --------------------------------------------------------

    triage_path = (
        eval_dir / "triage_test_cases.json"
    )

    triage_cases = []

    if triage_path.exists():
        with open(
            triage_path,
            encoding="utf-8",
        ) as file:
            triage_cases = json.load(file)

    # --------------------------------------------------------
    # Load account health test cases
    # --------------------------------------------------------

    account_path = (
        eval_dir / "account_health_test_cases.json"
    )

    account_cases = []

    if account_path.exists():
        with open(
            account_path,
            encoding="utf-8",
        ) as file:
            account_cases = json.load(file)

    # --------------------------------------------------------
    # Initialize retriever
    # --------------------------------------------------------

    retriever = KBRetriever()

    report = {
        "retrieval": [],
        "task_1_triage": [],
        "task_2_account_health": [],
    }

    # ========================================================
    # RETRIEVAL
    # ========================================================

    print("=== Retrieval Evaluation ===")

    for case in retrieval_cases:
        result = score_retrieval(
            case,
            retriever,
        )

        report["retrieval"].append(
            {
                "query": case["query"],
                **result,
            }
        )

        print(
            f'{result["status"]}: '
            f'{case["query"]} '
            f'(score={result["score"]:.2f})'
        )

    # ========================================================
    # TASK 1: TRIAGE
    # ========================================================

    print()
    print("=== Task 1: Ticket Triage ===")

    for case in triage_cases:
        result = score_triage(
            case,
            retriever,
        )

        report["task_1_triage"].append(
            {
                "name": case["name"],
                **result,
            }
        )

        print(
            f'{result["status"]}: '
            f'{case["name"]} '
            f'(score={result["score"]:.2f})'
        )

    # ========================================================
    # TASK 2: ACCOUNT HEALTH
    # ========================================================

    print()
    print("=== Task 2: Account Health ===")

    for case in account_cases:
        result = score_account_health(
            case
        )

        report["task_2_account_health"].append(
            {
                "name": case["name"],
                **result,
            }
        )

        print(
            f'{result["status"]}: '
            f'{case["name"]} '
            f'(score={result["score"]:.2f})'
        )

    # ========================================================
    # OVERALL SCORE
    # ========================================================

    all_results = (
        report["retrieval"]
        + report["task_1_triage"]
        + report["task_2_account_health"]
    )

    passed = sum(
        result["status"] == "PASS"
        for result in all_results
    )

    total = len(all_results)

    failed = total - passed

    pass_rate = (
        passed / total
        if total
        else 0.0
    )

    quality_score = (
        sum(
            result["score"]
            for result in all_results
        ) / total
        if total
        else 0.0
    )

    report["summary"] = {
        "total_cases": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(
            pass_rate,
            2,
        ),
        "quality_score": round(
            quality_score,
            2,
        ),
    }

    # --------------------------------------------------------
    # Save evaluation report
    # --------------------------------------------------------

    report_path = (
        eval_dir / "eval_report.json"
    )

    with open(
        report_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
        )

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print()
    print("=== Overall ===")
    print(
        f"Passed: {passed}/{total}"
    )
    print(
        f"Failed: {failed}/{total}"
    )
    print(
        f"Pass rate: {pass_rate:.2f}"
    )
    print(
        f"Quality score: {quality_score:.2f}"
    )
    print(
        f"Report: {report_path}"
    )


if __name__ == "__main__":
    main()