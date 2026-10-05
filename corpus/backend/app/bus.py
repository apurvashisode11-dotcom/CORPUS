"""Message bus. Agents never call each other directly; everything goes through publish().

Every message is saved to the messages table and mirrored as an audit event, so the
audit trail comes for free. Live listeners (the dashboard stream) get it from a queue.
"""
import asyncio
from enum import Enum

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .models import AuditEvent, Message


class MsgType(str, Enum):
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    APPROVAL_REQUEST = "APPROVAL_REQUEST"
    ESCALATION = "ESCALATION"
    REPORT = "REPORT"


class Envelope(BaseModel):
    sender: str
    recipient: str
    type: MsgType
    text: str
    payload: dict = {}
    task_id: int | None = None
    correlation_id: str | None = None


def event_dict(e: AuditEvent) -> dict:
    return {"id": e.id, "kind": e.kind, "actor": e.actor, "text": e.text,
            "data": e.data, "ts": e.ts.isoformat()}


class MessageBus:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]):
        self.sessions = sessions
        self.listeners: set[asyncio.Queue] = set()

    async def audit(self, kind: str, actor: str, text: str, data: dict | None = None) -> dict:
        async with self.sessions() as s:
            e = AuditEvent(kind=kind, actor=actor, text=text, data=data or {})
            s.add(e)
            await s.commit()
            out = event_dict(e)
        for q in list(self.listeners):
            q.put_nowait(out)
        return out

    async def publish(self, env: Envelope) -> dict:
        async with self.sessions() as s:
            s.add(Message(task_id=env.task_id, correlation_id=env.correlation_id,
                          sender=env.sender, recipient=env.recipient,
                          type=env.type.value, payload={**env.payload, "text": env.text}))
            await s.commit()
        return await self.audit(
            "message", env.sender, env.text,
            {"type": env.type.value, "to": env.recipient, "task_id": env.task_id})

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self.listeners.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self.listeners.discard(q)
