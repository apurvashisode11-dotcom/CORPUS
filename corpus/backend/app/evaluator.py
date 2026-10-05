"""Checks a result against the task. Deterministic checks first; an LLM judge can be added later."""
def evaluate(task: dict, result: dict) -> tuple[bool, str]:
    if not result.get("ok"):
        return False, "tool reported failure"
    if task["action"] == "spend" and result.get("spent", 0) != task["amount"]:
        return False, "amount mismatch"
    return True, "ok"
