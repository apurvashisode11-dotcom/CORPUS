import httpx
import pytest

from app.main import create_app


async def test_health_and_audit_roundtrip(tmp_path):
    app = create_app(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
            assert (await c.get("/health")).json() == {"status": "ok"}
            r = await c.post("/api/demo/message", json={
                "sender": "manager", "recipient": "marketing", "type": "REQUEST",
                "text": "Plan the jacket campaign"})
            assert r.status_code == 200
            log = (await c.get("/api/audit")).json()
            assert [e["text"] for e in log] == ["Plan the jacket campaign"]


async def test_bad_message_type_rejected(tmp_path):
    app = create_app(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
            r = await c.post("/api/demo/message", json={
                "sender": "a", "recipient": "b", "type": "NOPE", "text": "x"})
            assert r.status_code == 422
