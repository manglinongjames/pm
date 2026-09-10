# Project Plan

This plan is the execution checklist for the MVP. Work must stay inside stated requirements and avoid extra features.

## Part 1: Plan and Documentation (current phase)

### Checklist
- [x] Expand this plan with concrete implementation steps, tests, and success criteria for Parts 1-10.
- [x] Create a frontend-specific AGENTS file describing the existing frontend codebase and workflow.
- [x] Confirm assumptions that affect architecture (auth boundary, API contract shape, persistence format).
- [x] Get explicit user approval before starting Part 2.

### Tests
- [x] Manual review: ensure each part has checklist + tests + success criteria sections.
- [x] Manual review: verify Part 1 output references the current repository structure.

### Success Criteria
- [x] User approves this plan as the source of truth for execution order.
- [x] User approves frontend AGENTS guidance.

## Part 2: Scaffolding (Docker + FastAPI + scripts)

### Checklist
- [x] Add Docker assets for local single-container run (Dockerfile and supporting files as needed).
- [x] Initialize backend app in backend/ using FastAPI and uv-based dependency management.
- [x] Implement a basic health API route and one simple sample API route.
- [x] Serve a temporary static hello-world page from FastAPI to validate web serving pipeline.
- [x] Add cross-platform start/stop scripts in scripts/ for Windows, macOS, and Linux.
- [x] Document local run commands minimally in repo docs.

### Tests
- [x] Build container successfully.
- [x] Start container via scripts and confirm service boots.
- [x] Verify hello-world page loads in browser at /.
- [x] Verify sample API endpoint returns expected JSON.
- [x] Stop scripts terminate service cleanly.

### Success Criteria
- [x] One command path exists to build/start/stop locally on each OS family.
- [x] FastAPI is reachable and serving both HTML and JSON.

## Part 3: Add Frontend Build/Serve Integration

### Checklist
- [x] Configure frontend build output for static serving by backend.
- [x] Wire backend static file serving so / returns the Kanban UI.
- [x] Remove temporary hello-world route/content from primary path.
- [x] Keep routing behavior simple and compatible with single-board MVP.

### Tests
- [x] Frontend unit tests pass.
- [x] Frontend e2e tests pass against served app.
- [x] Containerized app displays Kanban at / with no manual frontend dev server.

### Success Criteria
- [x] Single deployed artifact serves working frontend and backend.
- [x] Existing Kanban interactions remain functional after integration.

## Part 4: Fake Sign-in Experience

### Checklist
- [x] Add login gate at / requiring username/password.
- [x] Accept only hardcoded credentials user/password for MVP.
- [x] Add logout flow that returns user to login screen.
- [x] Keep implementation minimal while preserving future multi-user path.

### Tests
- [x] Unit/integration test: invalid login is rejected.
- [x] Unit/integration test: valid login grants Kanban access.
- [x] Unit/integration test: logout clears logged-in state.
- [x] E2E flow: login -> view board -> logout.

### Success Criteria
- [x] Unauthenticated users cannot reach Kanban view.
- [x] Auth behavior is deterministic and easy to replace later.

## Part 5: Database Modeling

### Checklist
- [x] Propose SQLite schema for users, board, columns, cards, and optional chat history.
- [x] Define a JSON representation for board state exchange with AI/backend APIs.
- [x] Document schema decisions and tradeoffs in docs/.
- [x] Request user sign-off before schema implementation in runtime paths.

### Tests
- [x] Validate schema supports one board per user while allowing future multi-user expansion.
- [x] Validate JSON example can represent rename, create, delete, and move operations.

### Success Criteria
- [x] User approves schema and JSON contract.
- [x] Schema is minimal and sufficient for Parts 6-10.

## Part 6: Backend Kanban API

### Checklist
- [x] Implement SQLite initialization on startup if DB file does not exist.
- [x] Add API routes to fetch board state for authenticated user.
- [x] Add API routes to mutate board (rename column, create/edit/delete/move card).
- [x] Add input validation and consistent error responses.
- [x] Keep route design simple and stable for frontend usage.

### Tests
- [x] Backend unit tests for each route success path.
- [x] Backend unit tests for validation and not-found/error paths.
- [x] Persistence tests proving data survives app restart.

### Success Criteria
- [x] Backend fully supports board CRUD/move operations for MVP user flow.
- [x] DB auto-creation and migrations (if any) are reliable locally.

## Part 7: Frontend + Backend Persistence

### Checklist
- [x] Replace in-memory frontend board mutations with backend API calls.
- [x] Add loading and error handling states without adding extra features.
- [x] Ensure UI refreshes from persisted backend state after mutations.
- [x] Keep local UX responsive and consistent.

### Tests
- [x] Frontend unit tests for API client and state transitions.
- [x] Integration tests for create/edit/delete/move via API mocks or test backend.
- [x] E2E tests verifying data persists across page reload.

### Success Criteria
- [x] Board behavior is persistent, not demo-only.
- [x] Existing drag/drop and edit flows still behave correctly.

## Part 8: OpenRouter Connectivity

### Checklist
- [x] Add backend AI client using OPENROUTER_API_KEY from .env.
- [x] Configure model openai/gpt-oss-120b for requests.
- [x] Add a simple internal connectivity check path using prompt 2+2.
- [x] Implement clear handling for missing key and upstream errors.

### Tests
- [x] Unit tests for request formatting and error mapping.
- [x] Connectivity test against OpenRouter returns expected response format.
- [x] Negative test: missing/invalid key returns controlled error.

### Success Criteria
- [x] Backend can successfully complete a basic OpenRouter call.
- [x] Failures are explicit and debuggable.

## Part 9: Structured AI Board Operations

### Checklist
- [ ] Send board JSON + conversation history + user prompt to AI route.
- [ ] Enforce structured output schema: assistant message plus optional board update.
- [ ] Validate and sanitize AI-proposed board updates before persistence.
- [ ] Persist accepted AI updates and return updated board payload.

### Tests
- [ ] Unit tests for structured output parsing/validation.
- [ ] Unit tests for no-update and update-present response variants.
- [ ] Integration tests for persistence after AI-proposed changes.
- [ ] Robustness tests for malformed AI output fallback behavior.

### Success Criteria
- [ ] AI responses are machine-parseable and safe to apply.
- [ ] Optional AI board updates reliably modify persisted state.

## Part 10: AI Chat Sidebar in UI

### Checklist
- [ ] Build a sidebar chat UI integrated with backend AI endpoint.
- [ ] Render user/assistant messages and maintain conversation context.
- [ ] Apply AI-proposed board updates and refresh board immediately.
- [ ] Preserve existing Kanban usability on desktop and mobile.

### Tests
- [ ] Component tests for chat rendering, submit state, and error display.
- [ ] Integration tests verifying board updates after AI responses.
- [ ] E2E test: user asks AI to modify card; UI and persisted board reflect change.

### Success Criteria
- [ ] Chat experience is functional, clear, and stable.
- [ ] AI updates are visible in board UI without manual refresh.

## Global Quality Gates

### Checklist
- [ ] Keep implementation simple and avoid speculative abstractions.
- [ ] Use latest stable libraries where introduced.
- [ ] Keep docs concise and focused on operation and decisions.
- [ ] When issues arise, identify and verify root cause before fixing.
- [ ] Prioritize high-value tests. Target around 80% coverage only when sensible, and avoid adding low-value tests just to hit a metric.

### Delivery Criteria
- [ ] All relevant automated tests pass for each completed part.
- [ ] Each part is reviewed with the user before moving to the next part.