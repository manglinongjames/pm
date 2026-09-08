# Part 3 Run Guide

## Prerequisites

- Docker installed and running.

## Start

Run from repository root on your OS:

- Windows PowerShell:
  - `powershell -ExecutionPolicy Bypass -File scripts/start-windows.ps1`
- macOS:
  - `bash scripts/start-macos.sh`
- Linux:
  - `bash scripts/start-linux.sh`

## Verify

- Open `http://127.0.0.1:8000`.
- Confirm the Kanban UI appears with heading `Kanban Studio`.
- Confirm API health endpoint:
  - `http://127.0.0.1:8000/api/health`
- Confirm sample API endpoint:
  - `http://127.0.0.1:8000/api/hello`

## Stop

Run from repository root on your OS:

- Windows PowerShell:
  - `powershell -ExecutionPolicy Bypass -File scripts/stop-windows.ps1`
- macOS:
  - `bash scripts/stop-macos.sh`
- Linux:
  - `bash scripts/stop-linux.sh`
