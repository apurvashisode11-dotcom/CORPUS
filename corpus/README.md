# corpus

**Build your AI workforce. Give it a goal. Let it operate your business.**

corpus lets a small business owner describe their business and get a team of specialised AI employees (Manager, Marketing, Finance, Analytics, Support) that work like an organisation, not like separate chatbots. The AI does the thinking. Plain code enforces the rules, so the AI cannot talk its way past a spend limit.

Built for CURIOUSPARC 2026 (State Innovation Challenge) by team StrangerStrings, VIT Pune.

## Status

All MVP phases are built (see `docs/phases.md`, including its honest limits). Sample data and mocked tools are used for the demo.

## How it works

```
Owner -> AI Manager -> specialist agents -> Rules guard -> Memory / Audit log / Business tools
```

1. The owner gives a goal by text or voice.
2. The Manager breaks it into tasks and assigns them.
3. Every action passes the Rules guard: allowed, needs owner approval, or blocked with a logged reason.
4. The Manager checks each result and retries, reassigns or asks the owner.
5. Every message and decision is saved to the audit log.

See `docs/architecture.md` and `docs/message-protocol.md`.

## Tech stack (planned)

Next.js, React, Tailwind | Python, FastAPI, asyncio | LLM API with structured JSON output | PostgreSQL + pgvector | Web Speech API for voice

## Run it

```
cd backend
python -m venv .venv && .venv\Scripts\activate     (Windows)
pip install -r requirements.txt
pytest                                  # 14 tests
uvicorn app.main:app --reload           # open http://localhost:8000
```

If you ran an older version, delete `backend/corpus.db` first (the tables changed).
With Postgres: `cp .env.example .env && docker compose up --build`.

## Demo script

0. Fastest: click **Play demo** (builds the team and starts the goal for you in the chosen language), then go to step 3.
1. Or type/speak your business, click **Build my AI workforce**.
2. Give the goal (try Hindi or Marathi with the language switch), click **Run goal**.
3. Watch the log: agents talk, the Rules guard stops Rs 18,000, you approve (spoken read-back), the ad tool fails twice, the Manager reassigns to Finance, everything finishes.
4. **Reset demo** and run it again.

## Roadmap

MVP (Manager + 3 agents, rules guard, audit trail) -> testing with 2-3 real small businesses -> pilot with more agents and real integrations -> industry templates and more languages.

## Team

Sairaj Thorat, Apurva Shisode, Moksh - VIT Pune
