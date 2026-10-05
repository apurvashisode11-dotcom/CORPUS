"""AI Manager: turns an owner goal into a task plan and saves it."""
import json

from sqlalchemy import select

from . import config
from .bus import Envelope, MessageBus, MsgType
from .i18n import t
from .llm import call_llm
from .models import Agent, Objective, Task


def template(lang: str) -> list[dict]:
    """Deterministic plan used offline and as the fallback if the LLM answer is unusable."""
    return [
        {"title": t(lang, "t_results"), "assignee": "analytics", "action": "read_data", "tool": "memory", "amount": 0, "deps": []},
        {"title": t(lang, "t_campaign"), "assignee": "marketing", "action": "spend", "tool": "ad_platform", "amount": 18000, "deps": [0]},
        {"title": t(lang, "t_replies"), "assignee": "support", "action": "send_message", "tool": "email", "amount": 0, "deps": []},
        {"title": t(lang, "t_offers"), "assignee": "sales", "action": "send_email", "tool": "email", "amount": 0, "deps": [1]},
    ]


def fit(plan: list[dict], roles: set[str]) -> list[dict]:
    """Drop tasks for roles that were not hired and repair dependency numbers."""
    keep = [i for i, p in enumerate(plan) if p["assignee"] in roles]
    remap = {old: new for new, old in enumerate(keep)}
    return [{**plan[i], "deps": [remap[d] for d in plan[i]["deps"] if d in remap]} for i in keep]


def valid(plan) -> bool:
    keys = {"title", "assignee", "action", "tool", "amount", "deps"}
    return (isinstance(plan, list) and bool(plan) and all(
        isinstance(p, dict) and keys <= p.keys() and all(isinstance(d, int) and 0 <= d < i for d in p["deps"])
        for i, p in enumerate(plan)))


async def make_plan(text: str, lang: str, roles: set[str]) -> list[dict]:
    if config.LLM_PROVIDER != "mock":
        try:
            system = (f"You are an AI manager. Split the goal into tasks. Reply with a JSON list. Each item: title, "
                      f"assignee (one of {sorted(roles)}), action (spend|send_message|send_email|read_data), "
                      f"tool (ad_platform|email|memory), amount (number, 0 if none), deps (earlier item indexes). "
                      f"Write titles in language code '{lang}'.")
            plan = json.loads(await call_llm(system, text, json_mode=True))
            if valid(plan):
                return fit(plan, roles)
        except Exception:
            pass
    return fit(template(lang), roles)


async def create_objective(sessions, bus: MessageBus, text: str, lang: str) -> int:
    async with sessions() as s:
        roles = {a.role for a in (await s.scalars(select(Agent))).all()}
    plan = await make_plan(text, lang, roles)
    async with sessions() as s:
        obj = Objective(text=text, status="running")
        s.add(obj)
        await s.flush()
        ids: list[int] = []
        for p in plan:
            row = Task(objective_id=obj.id, title=p["title"], assignee=p["assignee"], action=p["action"],
                       tool=p["tool"], amount=int(p["amount"]), depends_on=[ids[d] for d in p["deps"]])
            s.add(row)
            await s.flush()
            ids.append(row.id)
        await s.commit()
        oid = obj.id
    await bus.publish(Envelope(sender="owner", recipient="manager", type=MsgType.REQUEST, text=text))
    await bus.audit("system", "manager", t(lang, "plan", n=len(plan)), {"objective_id": oid})
    return oid
