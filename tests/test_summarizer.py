from src.summarizer.summarizer import build_account_health


def test_account_health():
    result = build_account_health("ACC-3336")

    assert result["account_id"] == "ACC-3336"
    assert result["account_summary"]["company"] == "Omni Consumer Products"
    assert result["account_summary"]["health_status"] == "At Risk"
    assert result["account_summary"]["usage_trend"] == "Inactive"
    assert result["recent_ticket_count"] >= 1
    assert "executive_summary" in result
    assert "open_risks" in result
    assert "tam_talking_points" in result


def test_invalid_account():
    try:
        build_account_health("ACC-DOES-NOT-EXIST")
        assert False
    except ValueError:
        assert True