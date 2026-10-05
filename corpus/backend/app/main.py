import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import delete, select

from . import config
from .bus import Envelope, MessageBus, event_dict
from .db import init_db, make_engine, make_session_factory
from .builder import agent_view, build_workforce
from .executor import Executor
from .manager import create_objective
from .models import Agent, Approval, AuditEvent, Memory, Message, Objective, Task


class BuildReq(BaseModel):
    description: str
    lang: str = "en"


class ObjReq(BaseModel):
    text: str
    lang: str = "en"


class DecisionReq(BaseModel):
    approve: bool


def create_app(database_url: str = config.DATABASE_URL) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = make_engine(database_url)
        await init_db(engine)
        app.state.sessions = make_session_factory(engine)
        app.state.bus = MessageBus(app.state.sessions)
        app.state.executor = Executor(app.state.sessions, app.state.bus)
        app.state.bg = set()
        yield
        await engine.dispose()

    app = FastAPI(title="corpus - AI Workforce OS", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=[config.FRONTEND_ORIGIN],
                       allow_methods=["*"], allow_headers=["*"])

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/api/demo/message")
    async def demo_message(env: Envelope):
        """Phase 1 test hook: push a message through the bus."""
        return await app.state.bus.publish(env)

    @app.get("/api/audit")
    async def audit(limit: int = 100):
        async with app.state.sessions() as s:
            rows = (await s.scalars(
                select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit))).all()
        return [event_dict(e) for e in reversed(rows)]

    @app.get("/api/stream")
    async def stream():
        q = app.state.bus.subscribe()

        async def gen():
            try:
                while True:
                    try:
                        item = await asyncio.wait_for(q.get(), timeout=15)
                        yield f"data: {json.dumps(item)}\n\n"
                    except asyncio.TimeoutError:
                        yield ": keep-alive\n\n"
            finally:
                app.state.bus.unsubscribe(q)

        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return Response(status_code=204)

    @app.get("/")
    async def home():
        return FileResponse(config.FRONTEND_DIR / "index.html")

    @app.post("/api/workforce/build")
    async def build(req: BuildReq):
        return await build_workforce(app.state.sessions, app.state.bus, req.description, req.lang)

    @app.post("/api/objectives")
    async def objective(req: ObjReq):
        async with app.state.sessions() as s:
            if not (await s.scalars(select(Agent))).first():
                raise HTTPException(400, "Build the workforce first")
        oid = await create_objective(app.state.sessions, app.state.bus, req.text, req.lang)
        job = asyncio.create_task(app.state.executor.run_objective(oid, req.lang))
        app.state.bg.add(job)
        job.add_done_callback(app.state.bg.discard)
        return {"objective_id": oid}

    @app.get("/api/approvals")
    async def approvals():
        async with app.state.sessions() as s:
            rows = (await s.scalars(select(Approval).where(Approval.status == "pending").order_by(Approval.id))).all()
        return [{"id": a.id, "agent": a.agent, "action": a.action, "amount": a.amount, "task_id": a.task_id} for a in rows]

    @app.post("/api/approvals/{aid}/decision")
    async def decision(aid: int, req: DecisionReq):
        status = await app.state.executor.decide(aid, req.approve)
        if status is None:
            raise HTTPException(404, "No pending approval with that id")
        return {"status": status}

    @app.get("/api/state")
    async def state():
        async with app.state.sessions() as s:
            agents = (await s.scalars(select(Agent).order_by(Agent.id))).all()
            obj = await s.scalar(select(Objective).order_by(Objective.id.desc()).limit(1))
            tasks = []
            if obj:
                tasks = (await s.scalars(select(Task).where(Task.objective_id == obj.id).order_by(Task.id))).all()
        return {"agents": [agent_view(a.role) for a in agents],
                "objective": {"id": obj.id, "text": obj.text, "status": obj.status} if obj else None,
                "tasks": [{"id": x.id, "title": x.title, "assignee": x.assignee, "status": x.status,
                           "action": x.action, "amount": x.amount, "previous_assignee": x.previous_assignee} for x in tasks],
                "approvals": await approvals()}

    @app.post("/api/reset")
    async def reset():
        async with app.state.sessions() as s:
            for model in (Task, Approval, Message, AuditEvent, Objective, Agent, Memory):
                await s.execute(delete(model))
            await s.commit()
        app.state.executor.waiters.clear()
        return {"status": "reset"}

    return app


app = create_app()
