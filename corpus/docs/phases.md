# Build phases (all done for the MVP)

- [x] Phase 0 - Setup: repo, Docker Compose, call_llm() wrapper, tests
- [x] Phase 1 - Foundation: tables, message bus, audit log, live stream
- [x] Phase 1b - Dashboard (plain HTML served by the backend; Next.js is an optional later swap)
- [x] Phase 2 - Self-building workforce (roles.py, builder.py)
- [x] Phase 3 - Manager + task execution (manager.py, executor.py, tools.py)
- [x] Phase 4 - Safety layer (policy engine on every action, approval inbox)
- [x] Phase 5 - Evaluation, recovery (retry, reassign, escalate) and memory
- [x] Phase 6 - Language and voice (English/Hindi/Marathi log + UI, mic, spoken approval check)
- [x] Phase 7 - Demo hardening (scripted failure, DEMO_DELAY pacing, reset button)

## Honest limits
- Default mode uses a mock AI (rules + templates). The real-AI path (`LLM_PROVIDER=anthropic`) is written but untested.
- Tools are mocked (ads, email). Gmail/Sheets are not connected.
- Memory recall is word-overlap, not embeddings/pgvector yet.
- Hinglish: typing works via the rule-based profile; voice needs a browser with speech recognition (Chrome).
- Role names and "why hired" reasons in the UI are partly English only.
- What-if simulation and KPI scoring are not built.
