"""Executor: runs the task plan. Every action passes the rules guard; failures are retried,
reassigned or escalated; approvals pause only the task that needs them."""
import asyncio
import re

from sqlalchemy import select

from . import config, memory
from .bus import Envelope, MessageBus, MsgType
from .evaluator import evaluate
from .i18n import t, tn
from .models import Agent, Approval, Objective, Task
from .policy_engine import POLICIES, Decision, check
from .tools import ToolError, Tools

FALLBACK = {"marketing": "finance"}  # who takes over if the first agent's tool keeps failing


class Executor:
    def __init__(self, sessions, bus: MessageBus):
        self.sessions, self.bus = sessions, bus
        self.waiters: dict[int, tuple[asyncio.Event, str]] = {}
        self.tools = Tools(0)
        self.roles: set[str] = set()

    async def _pause(self):
        if config.DEMO_DELAY > 0:
            await asyncio.sleep(config.DEMO_DELAY)

    async def _set(self, task_id: int, **fields):
        async with self.sessions() as s:
            row = await s.get(Task, task_id)
            for k, v in fields.items():
                setattr(row, k, v)
            await s.commit()

    async def run_objective(self, oid: int, lang: str):
        try:
            await self._run(oid, lang)
        except Exception as e:  # never leave the dashboard hanging
            await self.bus.audit("failure", "system", f"Internal error: {e}")
            await self._finish(oid, "error")

    async def _finish(self, oid: int, status: str):
        async with self.sessions() as s:
            (await s.get(Objective, oid)).status = status
            await s.commit()

    async def _run(self, oid: int, lang: str):
        self.tools = Tools(config.DEMO_AD_FAILURES)
        async with self.sessions() as s:
            self.roles = {a.role for a in (await s.scalars(select(Agent))).all()}
            rows = (await s.scalars(select(Task).where(Task.objective_id == oid).order_by(Task.id))).all()
            pending = {r.id: dict(id=r.id, title=r.title, assignee=r.assignee, action=r.action,
                                  tool=r.tool, amount=r.amount, deps=list(r.depends_on)) for r in rows}
        done: set[int] = set()
        failed: set[int] = set()
        ok = True
        while pending:
            for tid in [i for i, tk in pending.items() if any(d in failed for d in tk["deps"])]:
                failed.add(tid)
                del pending[tid]
                await self._set(tid, status="skipped")
                ok = False
            ready = [tk for tk in pending.values() if all(d in done for d in tk["deps"])]
            if not ready:
                break
            for tk in ready:
                del pending[tk["id"]]
            results = await asyncio.gather(*(self.run_task(tk, lang) for tk in ready))
            for tk, good in zip(ready, results):
                (done if good else failed).add(tk["id"])
                ok = ok and good
        await self.bus.audit("good" if ok else "failure", "manager", t(lang, "complete" if ok else "partial"))
        await self._finish(oid, "done" if ok else "needs_attention")

    async def run_task(self, task: dict, lang: str) -> bool:
        agent = task["assignee"]
        fb = FALLBACK.get(agent, "manager")
        cands = [agent] + ([fb] if fb != agent and fb in self.roles else [])
        await self.bus.publish(Envelope(sender="manager", recipient=agent, type=MsgType.REQUEST,
                                        text=task["title"], task_id=task["id"]))
        await self._set(task["id"], status="in_progress")
        if task["action"] == "spend" and "finance" in self.roles:
            await self._pause()
            await self.bus.publish(Envelope(sender=agent, recipient="finance", type=MsgType.REQUEST,
                                            text=t(lang, "spend_req", amount=task["amount"]), task_id=task["id"]))
        last_tool = task["tool"]
        for i, owner in enumerate(cands):
            if i:
                await self._set(task["id"], assignee=owner, previous_assignee=agent)
            if not await self._gate(task, owner, lang):
                break
            for attempt in (1, 2):
                try:
                    res = await self._perform(task, owner, lang)
                    if not evaluate(task, res)[0]:
                        raise ToolError(task["tool"])
                except ToolError as e:
                    last_tool = e.tool
                    if attempt == 1:
                        await self.bus.audit("failure", e.tool, t(lang, "tool_fail", tool=e.tool), {"task_id": task["id"]})
                        await self._pause()
                        await self.bus.audit("system", "manager", t(lang, "retry"), {"task_id": task["id"]})
                    continue
                await self._set(task["id"], status="done")
                await self.bus.audit("good", owner, t(lang, "done", title=task["title"]), {"task_id": task["id"]})
                await memory.save(self.sessions, f"{owner} completed: {task['title']}")
                return True
            if i + 1 < len(cands):
                await self._pause()
                await self.bus.audit("failure", "manager", t(lang, "reassign", tool=tn(lang, last_tool)),
                                     {"task_id": task["id"], "to": cands[i + 1]})
        await self._set(task["id"], status="failed")
        await self.bus.audit("failure", "manager", t(lang, "escalate", title=task["title"]), {"task_id": task["id"]})
        return False

    async def _gate(self, task: dict, agent: str, lang: str) -> bool:
        """The rules guard. Plain code decides; the AI cannot change this."""
        r = check(agent, task["action"], task["amount"])
        if r.decision == Decision.ALLOW:
            return True
        if r.decision == Decision.BLOCK:
            await self.bus.audit("guard", "rules_guard", t(lang, "guard_block", agent=agent.title(), action=task["action"]),
                                 {"task_id": task["id"]})
            return False
        async with self.sessions() as s:
            ap = Approval(task_id=task["id"], agent=agent, action=task["action"], amount=int(task["amount"]))
            s.add(ap)
            await s.commit()
            aid = ap.id
        ev = asyncio.Event()
        self.waiters[aid] = (ev, lang)
        await self._set(task["id"], status="needs_approval")
        await self.bus.audit("guard", "rules_guard",
                             t(lang, "guard_escalate", amount=task["amount"], agent=agent.title(), limit=POLICIES[agent]["spend_limit"]),
                             {"task_id": task["id"], "approval_id": aid})
        try:
            await asyncio.wait_for(ev.wait(), config.APPROVAL_TIMEOUT)
        except asyncio.TimeoutError:
            await self.decide(aid, False)
        async with self.sessions() as s:
            status = (await s.get(Approval, aid)).status
        if status == "approved":
            await self._set(task["id"], status="in_progress")
            return True
        return False

    async def decide(self, aid: int, approve: bool) -> str | None:
        async with self.sessions() as s:
            ap = await s.get(Approval, aid)
            if ap is None or ap.status != "pending":
                return None
            ap.status = "approved" if approve else "rejected"
            amount, status = ap.amount, ap.status
            await s.commit()
        ev, lang = self.waiters.pop(aid, (None, "en"))
        await self.bus.audit("approval", "owner", t(lang, status, amount=amount), {"approval_id": aid})
        if ev:
            ev.set()
        return status

    async def _perform(self, task: dict, agent: str, lang: str) -> dict:
        await self._pause()
        if task["tool"] == "memory":
            hits = await memory.recall(self.sessions, "campaign click rate")
            m = re.search(r"(\d+(?:\.\d+)?)%", hits[0]) if hits else None
            await self.bus.publish(Envelope(sender=agent, recipient="marketing", type=MsgType.RESPONSE,
                                            text=t(lang, "ctr_reply", ctr=m.group(1) if m else "n/a"), task_id=task["id"]))
            return {"ok": True}
        return await self.tools.call(task["tool"], amount=task["amount"])
