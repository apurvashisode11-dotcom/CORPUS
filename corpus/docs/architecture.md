# Architecture

Principle: the LLM thinks, deterministic code decides what is allowed ("controlled autonomy").

```
Owner
  |
AI Manager  (plans a task graph, assigns, verifies, escalates)
  |
Specialist agents (Marketing, Finance, Analytics, Support)
  |
Rules guard (policy engine, plain Python)
  |
Company memory | Audit log | Business tools
```

## Life of one task
1. Manager assigns a task.
2. The agent works and proposes an action.
3. Rules guard checks it: within limit runs, too large goes to owner approval, not allowed is blocked and logged.
4. Manager checks the result. Good: logged and saved to memory. Bad: retry, reassign or ask the owner.

## Design choices
- Agents never call each other directly. All messages go through one message bus, which gives the audit trail for free.
- No Kafka, Redis or microservices for the MVP. Module boundaries allow swapping them in later.
- Permissions live in code and the database, never in prompts, so injected text cannot change them.
