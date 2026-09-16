#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$repo_root"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Install Docker Desktop or Docker Engine with the Compose plugin, then run this script again." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: Docker Compose is unavailable. Install a current Docker Desktop or Docker Engine with the Compose plugin." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Start Docker, then run this script again." >&2
  exit 1
fi

export CVCANNON_UID="$(id -u)"
export CVCANNON_GID="$(id -g)"

echo "Building the cvcannon toolchain..."
docker compose build

if [[ ! -d .git ]]; then
  git init -b main
fi
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit scripts/*.sh scripts/*.py docker-setup.sh

echo "Checking the container and repository..."
scripts/docker.sh make templates
scripts/docker.sh make privacy

if [[ -s PROFILE/master-cv.html ]]; then
  scripts/docker.sh make doctor
  echo "cvcannon is ready. Add listings, then create an application with:"
  echo "  make docker-new SLUG=company-role"
else
  echo
  echo "The Docker toolchain is ready. Continue the agent workflow:"
  echo "  1. Ask the user to drop an existing CV or career notes into PROFILE/, or provide them in chat."
  echo "  2. Run make docker-profile."
  echo "  3. Complete PROFILE/master-cv.html from the supplied material."
  echo "  4. Run make docker-doctor."
fi
