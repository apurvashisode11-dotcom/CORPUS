from sqlalchemy import func, select

from app.bus import Envelope, MsgType
from app.models import AuditEvent, Message


async def test_publish_saves_message_and_audit_event(bus):
    out = await bus.publish(Envelope(sender="marketing", recipient="finance",
                                     type=MsgType.REQUEST, text="Need Rs 18,000"))
    assert out["text"] == "Need Rs 18,000"
    async with bus.sessions() as s:
        assert await s.scalar(select(func.count()).select_from(Message)) == 1
        assert await s.scalar(select(func.count()).select_from(AuditEvent)) == 1


async def test_live_listener_receives_events(bus):
    q = bus.subscribe()
    await bus.audit("guard", "rules_guard", "Rs 18,000 sent to owner")
    assert (await q.get())["kind"] == "guard"
    bus.unsubscribe(q)
    await bus.audit("system", "system", "nobody listening")
    assert q.empty()
