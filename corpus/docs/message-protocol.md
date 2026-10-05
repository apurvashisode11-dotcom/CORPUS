# Message protocol

Fields: id, task_id, correlation_id, from, to, type, payload (JSON), timestamp

Types: REQUEST, RESPONSE, APPROVAL_REQUEST, ESCALATION, REPORT

Storage: a Postgres table plus an in-memory asyncio queue for the MVP.
