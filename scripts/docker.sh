#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is not installed or is not on PATH." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: Docker Compose is unavailable. Install a current Docker Desktop or Docker Engine with the Compose plugin." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: The Docker daemon is not running or is not accessible." >&2
  exit 1
fi

export CVCANNON_UID="$(id -u)"
export CVCANNON_GID="$(id -g)"

if [[ $# -eq 0 ]]; then
  set -- make help
fi

exec docker compose run --rm cvcannon "$@"
