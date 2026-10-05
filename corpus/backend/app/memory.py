"""Company memory. MVP recall = word overlap. Upgrade path: embeddings + pgvector."""
import re

from sqlalchemy import select

from .models import Memory


def _words(s: str) -> set[str]:
    return set(re.findall(r"\w+", s.lower()))


async def save(sessions, text: str, kind: str = "lesson") -> None:
    async with sessions() as s:
        s.add(Memory(kind=kind, text=text))
        await s.commit()


async def recall(sessions, query: str, k: int = 3) -> list[str]:
    async with sessions() as s:
        rows = (await s.scalars(select(Memory))).all()
    q = _words(query)
    scored = sorted(((len(q & _words(r.text)), r.text) for r in rows), reverse=True)
    return [text for score, text in scored if score > 0][:k]
