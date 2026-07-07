"""Scoring engine tests."""

from services.scoring.engine import score_posting


def test_score_posting_title_match():
    p = {
        "title": "Data Analyst",
        "location": "Auckland, New Zealand",
        "description": "Python SQL reporting defence aerospace",
    }
    result = score_posting(p)
    assert result["title_match"] is True
    assert result["score"] > 0
    assert any("role match" in r for r in result["reasons"])


def test_score_posting_seniority_gate():
    p = {
        "title": "Senior Data Engineer",
        "location": "Remote",
        "description": "python sql",
    }
    result = score_posting(p)
    assert result["too_senior"] is True
    from services.scoring.engine import rank_postings
    assert rank_postings([p]) == []
