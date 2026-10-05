import asyncio

import httpx

from app import config
from app.builder import rule_profile
from app.main import create_app
from app.roles import ROLES

CLOTHING = "I run a small clothing business selling through Instagram and a website."


def hired(profile):
    return {r for r, d in ROLES.items() if d["when"](profile)}


def test_clothing_business_gets_full_team():
    assert hired(rule_profile(CLOTHING)) == {"manager", "sales", "marketing", "support", "finance", "inventory", "analytics"}


def test_service_business_gets_no_inventory_agent():
    team = hired(rule_profile("I am a freelance graphic designer with clients"))
    assert "inventory" not in team and {"manager", "sales", "finance"} <= team


async def _client(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t")


async def _wait(fn, tries=200):
    for _ in range(tries):
        v = await fn()
        if v:
            return v
        await asyncio.sleep(0.05)
    raise AssertionError("timed out")


async def _start(c, lang="en"):
    r = await c.post("/api/workforce/build", json={"description": CLOTHING, "lang": lang})
    assert len(r.json()["agents"]) == 7
    await c.post("/api/objectives", json={"text": "Launch our new Rs 1,999 jacket next Monday", "lang": lang})


async def test_full_flow_approve_retry_reassign(tmp_path):
    app = create_app(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    async with app.router.lifespan_context(app):
        async with await _client(app) as c:
            assert (await c.get("/")).status_code == 200
            await _start(c)
            ap = await _wait(lambda: _json(c, "/api/approvals"))
            assert ap[0]["amount"] == 18000 and ap[0]["agent"] == "marketing"
            await c.post(f"/api/approvals/{ap[0]['id']}/decision", json={"approve": True})
            st = await _wait(lambda: _done(c))
            assert st["objective"]["status"] == "done"
            assert {x["status"] for x in st["tasks"]} == {"done"}
            log = (await c.get("/api/audit")).json()
            texts = " | ".join(e["text"] for e in log)
            assert {"guard", "failure", "approval", "good"} <= {e["kind"] for e in log}
            assert "handed over" in texts and "4.2% click rate" in texts


async def test_rejected_approval_escalates_and_skips_dependents(tmp_path):
    app = create_app(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    async with app.router.lifespan_context(app):
        async with await _client(app) as c:
            await _start(c)
            ap = await _wait(lambda: _json(c, "/api/approvals"))
            await c.post(f"/api/approvals/{ap[0]['id']}/decision", json={"approve": False})
            st = await _wait(lambda: _done(c))
            by = {x["assignee"]: x["status"] for x in st["tasks"]}
            assert st["objective"]["status"] == "needs_attention"
            assert by["marketing"] == "failed" and by["sales"] == "skipped" and by["support"] == "done"


async def test_marathi_log_and_reset(tmp_path):
    app = create_app(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    async with app.router.lifespan_context(app):
        async with await _client(app) as c:
            await _start(c, "mr")
            ap = await _wait(lambda: _json(c, "/api/approvals"))
            await c.post(f"/api/approvals/{ap[0]['id']}/decision", json={"approve": True})
            await _wait(lambda: _done(c))
            assert any("मंजूर" in e["text"] for e in (await c.get("/api/audit")).json())
            await c.post("/api/reset")
            assert (await c.get("/api/audit")).json() == []
            r = await c.post("/api/objectives", json={"text": "x"})
            assert r.status_code == 400


async def _json(c, path):
    return (await c.get(path)).json()


async def _done(c):
    st = (await c.get("/api/state")).json()
    return st if st["objective"] and st["objective"]["status"] != "running" else None


def test_hindi_and_marathi_descriptions_hire_full_team():
    full = {"manager", "sales", "marketing", "support", "finance", "inventory", "analytics"}
    assert hired(rule_profile("मैं इंस्टाग्राम और वेबसाइट से कपड़े बेचता हूँ।")) == full
    assert hired(rule_profile("मी इन्स्टाग्राम आणि वेबसाइटवरून कपडे विकतो.")) == full
