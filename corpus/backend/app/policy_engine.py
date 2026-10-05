"""Rules guard: decides whether an agent action is allowed.

Plain deterministic code. The LLM never changes these limits.
"""
from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    ALLOW = "allow"
    NEEDS_APPROVAL = "needs_approval"
    BLOCK = "block"


@dataclass(frozen=True)
class Result:
    decision: Decision
    reason: str


# agent -> spend limit without approval, and actions that are never allowed
POLICIES = {
    "marketing": {"spend_limit": 10_000, "blocked": {"delete_data"}},
    "finance": {"spend_limit": 50_000, "blocked": {"delete_data"}},
    "support": {"spend_limit": 1_000, "blocked": {"delete_data", "change_contract"}},
    "sales": {"spend_limit": 5_000, "blocked": {"delete_data"}},
    "inventory": {"spend_limit": 20_000, "blocked": {"delete_data"}},
    "manager": {"spend_limit": 50_000, "blocked": {"delete_data"}},
    "analytics": {"spend_limit": 0, "blocked": {"delete_data", "spend"}},
}
HARD_CAP = 500_000  # nothing above this is ever auto-approved


def check(agent: str, action: str, amount: float = 0) -> Result:
    policy = POLICIES.get(agent)
    if policy is None:
        return Result(Decision.BLOCK, f"Unknown agent '{agent}'")
    if action in policy["blocked"]:
        return Result(Decision.BLOCK, f"{agent} is not allowed to {action}")
    if amount < 0:
        return Result(Decision.BLOCK, "Negative amount")
    if amount > HARD_CAP:
        return Result(Decision.BLOCK, f"Rs {amount:,.0f} is above the hard cap")
    if amount > policy["spend_limit"]:
        return Result(
            Decision.NEEDS_APPROVAL,
            f"Rs {amount:,.0f} is above the Rs {policy['spend_limit']:,} limit for {agent}",
        )
    return Result(Decision.ALLOW, "Within limit")
