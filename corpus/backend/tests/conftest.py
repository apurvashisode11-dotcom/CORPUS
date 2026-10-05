import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app import config
from app.bus import MessageBus
from app.db import init_db, make_session_factory


@pytest.fixture
async def bus():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    await init_db(engine)
    yield MessageBus(make_session_factory(engine))
    await engine.dispose()


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    monkeypatch.setattr(config, "DEMO_DELAY", 0)  # tests run instantly
