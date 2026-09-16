#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if [[ ! -d .git ]]; then
  git init -b main
fi

git config core.hooksPath .githooks
chmod +x .githooks/pre-commit scripts/setup.sh scripts/cv.py scripts/privacy_check.py

echo "Configured local Git hooks."
python3 scripts/cv.py doctor
