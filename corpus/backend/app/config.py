import os
from pathlib import Path

# Local default is SQLite so the app runs with zero setup.
# docker-compose sets DATABASE_URL to Postgres.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./corpus.db")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")  # mock | (real provider added in Phase 2)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-5-5")
DEMO_DELAY = float(os.getenv("DEMO_DELAY", "1.0"))            # seconds between steps; use 1.0 for a live demo
DEMO_AD_FAILURES = int(os.getenv("DEMO_AD_FAILURES", "2"))  # scripted ad-platform failures (shows retry + reassign)
APPROVAL_TIMEOUT = float(os.getenv("APPROVAL_TIMEOUT", "600"))
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", Path(__file__).resolve().parents[2] / "frontend"))
