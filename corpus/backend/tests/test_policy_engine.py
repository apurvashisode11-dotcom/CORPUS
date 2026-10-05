

from app.policy_engine import check, Decision


def test_within_limit_is_allowed():
    assert check("marketing", "spend", 5_000).decision == Decision.ALLOW


def test_above_limit_needs_approval():
    r = check("marketing", "spend", 18_000)
    assert r.decision == Decision.NEEDS_APPROVAL
    assert "10,000" in r.reason


def test_blocked_action():
    assert check("support", "change_contract").decision == Decision.BLOCK


def test_hard_cap_blocks():
    assert check("finance", "spend", 600_000).decision == Decision.BLOCK


def test_unknown_agent_blocked():
    assert check("intern", "spend", 1).decision == Decision.BLOCK
