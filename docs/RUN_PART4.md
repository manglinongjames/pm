# Part 4 Run Guide

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

## Verify Login Flow

- Open `http://127.0.0.1:8000`.
- Confirm sign-in screen appears.
- Sign in with:
  - Username: `user`
  - Password: `password`
- Confirm Kanban board appears after sign-in.
- Click `Log out` and confirm sign-in screen appears again.

## Verify API Endpoints

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/api/hello`

## Stop

Run from repository root on your OS:

- Windows PowerShell:
  - `powershell -ExecutionPolicy Bypass -File scripts/stop-windows.ps1`
- macOS:
  - `bash scripts/stop-macos.sh`
- Linux:
  - `bash scripts/stop-linux.sh`
