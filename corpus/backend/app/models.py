from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class Agent(Base):
    __tablename__ = "agents"
    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(40), unique=True)
    manager_role: Mapped[str | None] = mapped_column(String(40), nullable=True)
    goals: Mapped[str] = mapped_column(Text, default="")


class Objective(Base):
    __tablename__ = "objectives"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    objective_id: Mapped[int] = mapped_column(ForeignKey("objectives.id"))
    title: Mapped[str] = mapped_column(String(200))
    assignee: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="queued")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    action: Mapped[str] = mapped_column(String(40), default="")
    tool: Mapped[str] = mapped_column(String(40), default="")
    amount: Mapped[int] = mapped_column(Integer, default=0)
    depends_on: Mapped[list] = mapped_column(JSON, default=list)
    previous_assignee: Mapped[str | None] = mapped_column(String(40), nullable=True)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int | None] = mapped_column(nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    sender: Mapped[str] = mapped_column(String(40))
    recipient: Mapped[str] = mapped_column(String(40))
    type: Mapped[str] = mapped_column(String(20))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int | None] = mapped_column(nullable=True)
    agent: Mapped[str] = mapped_column(String(40))
    action: Mapped[str] = mapped_column(String(60))
    amount: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(12), default="pending")  # pending|approved|rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditEvent(Base):
    """The single timeline the dashboard reads. Every message and decision lands here."""
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))  # message | guard | failure | approval | system
    actor: Mapped[str] = mapped_column(String(40))
    text: Mapped[str] = mapped_column(Text)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Memory(Base):
    """Company memory: facts and lessons agents can recall later."""
    __tablename__ = "memories"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(12), default="lesson")  # fact | lesson | policy
    text: Mapped[str] = mapped_column(Text)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
