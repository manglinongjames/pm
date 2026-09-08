#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="pm-mvp"

if docker ps -a --format '{{.Names}}' | grep -Fxq "${CONTAINER_NAME}"; then
  docker rm -f "${CONTAINER_NAME}" >/dev/null
  echo "Container '${CONTAINER_NAME}' stopped and removed."
else
  echo "Container '${CONTAINER_NAME}' was not found."
fi
