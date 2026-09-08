# Frontend Agent Guide

## Purpose

This frontend is a Next.js Kanban UI with a Part 4 sign-in gate and in-memory board state. It is exported as static files and served by the FastAPI backend at `/`.

## Stack

- Next.js 16 (App Router)
- React 19
- TypeScript 5
- Tailwind CSS 4
- dnd-kit for drag-and-drop
- Vitest + Testing Library for unit/component tests
- Playwright for e2e tests

## Current Behavior

- Route `/` first renders a sign-in gate.
- Valid credentials are fixed to `user` / `password` for MVP.
- After valid sign-in, the single-board Kanban UI is shown.
- Log out returns the user to the sign-in gate.
- The board has five predefined columns.
- Column titles are editable inline.
- Cards can be:
  - Dragged within the same column
  - Dragged across columns
  - Added to a column
  - Removed from a column
- All board changes are in memory and reset on refresh.

## Deployment Behavior (Part 3)

- Next.js is configured with `output: "export"`.
- Build output is generated in `frontend/out`.
- Docker build copies the exported files into `backend/app/static/frontend`.
- FastAPI serves those files at `/`.

## Authentication Behavior (Part 4)

- Auth is intentionally minimal for MVP and currently handled in the frontend shell component.
- There is no backend session yet; this will evolve in later parts.

## Data Model and State

- Board data lives in `src/lib/kanban.ts` as:
  - `Card`
  - `Column`
  - `BoardData`
- `initialData` seeds the board state.
- `moveCard` handles reorder and cross-column moves.
- `createId` generates IDs for new cards.
- `src/components/AuthKanbanApp.tsx` owns auth state and conditionally renders sign-in vs board.
- `src/components/KanbanBoard.tsx` owns board state via `useState` and passes handlers to child components.

## Key Files

- `src/app/page.tsx`: app entry for `/`, renders `AuthKanbanApp`.
- `src/components/AuthKanbanApp.tsx`: login form, credential check, and logout action.
- `src/app/layout.tsx`: metadata and font setup.
- `src/app/globals.css`: design tokens and global styles.
- `src/components/KanbanBoard.tsx`: main orchestrator for drag-drop and board mutation handlers.
- `src/components/KanbanColumn.tsx`: droppable column with title input and new-card form.
- `src/components/KanbanCard.tsx`: sortable card UI and remove action.
- `src/components/NewCardForm.tsx`: add-card form toggle and submit handling.
- `src/components/KanbanCardPreview.tsx`: drag overlay card preview.
- `src/lib/kanban.ts`: board types, seed data, and card move utility.

## Testing

- Unit/component tests:
  - `src/components/AuthKanbanApp.test.tsx`
  - `src/components/KanbanBoard.test.tsx`
  - `src/lib/kanban.test.ts`
- E2E tests:
  - `tests/kanban.spec.ts`
- Test setup:
  - `src/test/setup.ts`
  - `vitest.config.ts`
  - `playwright.config.ts`

## Commands

From `frontend/`:

- `npm install`
- `npm run dev`
- `npm run build`
- `npm run start`
- `npm run test:unit`
- `npm run test:e2e`
- `npm run test:all`

## Implementation Constraints for Next Parts

- Keep scope MVP-only; avoid adding non-requested features.
- Preserve current visual identity unless requirements say otherwise.
- Prefer small, direct state updates over abstractions.
- When integrating backend later, replace in-memory mutations with API calls while preserving existing UI interactions.
