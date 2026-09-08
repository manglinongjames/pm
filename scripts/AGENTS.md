# Scripts Agent Guide

## Purpose

This folder contains OS-specific scripts for starting and stopping the local Dockerized MVP service.

## Scripts

- Windows:
	- `start-windows.ps1`
	- `stop-windows.ps1`
- macOS:
	- `start-macos.sh`
	- `stop-macos.sh`
- Linux:
	- `start-linux.sh`
	- `stop-linux.sh`

## Runtime Contract

- Image name: `pm-mvp:part2`
- Container name: `pm-mvp`
- Exposed URL: `http://127.0.0.1:8000`

## Script Behavior

- Start scripts:
	- Build Docker image from repository root.
	- Remove existing container with the same name if present.
	- Start container in detached mode and print URL.
- Stop scripts:
	- Remove container if present.
	- Print a clear status message if container is absent.

## Constraints

- Keep scripts idempotent and simple.
- Do not add extra deployment environments here.