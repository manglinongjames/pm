# Part 5 Database Approach

## Scope

This document proposes the Part 5 data model and JSON contracts for MVP.

## Artifacts

- Relational schema proposal: docs/DB_SCHEMA.json
- Board/API/AI JSON contract: docs/BOARD_JSON_CONTRACT.json

## Why this schema

1. It keeps board structure normalized (`boards` -> `columns` -> `cards`) so move/reorder operations are explicit and simple.
2. It enforces one board per user in MVP with `UNIQUE(boards.user_id)` while still supporting multiple users.
3. It uses `position` fields for stable ordering without requiring complex diff logic.
4. It adds optional `chat_messages` so AI history can be persisted when implemented.

## Tradeoffs

1. Normalized rows are slightly more verbose than storing a full board JSON blob.
2. Reordering cards requires updating position values in one column.
3. The model intentionally avoids extra entities (labels, assignees, activity logs) to stay MVP-simple.

## Validation Against Part 5 Requirements

1. Schema supports one board per user now, and many users later via `users` + `boards.user_id`.
2. Contract includes operations for:
   - rename column
   - create card
   - move card
   - delete card
3. JSON contract is aligned for both backend CRUD APIs (Part 6/7) and AI structured updates (Part 9/10).

## Implementation Notes for Part 6

1. Enable SQLite foreign keys (`PRAGMA foreign_keys = ON`).
2. Seed default five columns when creating a new board.
3. Keep API surface close to `mutationContract.operations` in docs/BOARD_JSON_CONTRACT.json.

## Sign-off Request

Please review docs/DB_SCHEMA.json and docs/BOARD_JSON_CONTRACT.json. After approval, Part 6 can implement these structures as the runtime source of truth.
