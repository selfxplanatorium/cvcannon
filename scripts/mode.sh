#!/usr/bin/env sh
# POSIX shortcut for `python scripts/cv.py mode`, which also works on Windows.
set -eu
cd "$(dirname "$0")/.."
exec python3 scripts/cv.py mode "$@"
