# API

| Method | Path | Purpose |
|---|---|---|
| GET | / | Dashboard |
| POST | /api/workforce/build | {description, lang} -> profile + hired agents |
| POST | /api/objectives | {text, lang} -> starts the Manager and agents |
| GET | /api/state | agents, latest objective, tasks, pending approvals |
| GET | /api/approvals | pending approvals |
| POST | /api/approvals/{id}/decision | {approve: true/false} |
| GET | /api/audit | full activity history |
| GET | /api/stream | live events (Server-Sent Events) |
| POST | /api/reset | clear everything for a fresh demo |
