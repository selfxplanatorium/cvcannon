#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
preference_file="$repo_root/.cvcannon/portrait"
requested="${1:-}"

if [[ -z "$requested" ]]; then
  if [[ -f "$preference_file" ]]; then
    cat "$preference_file"
    exit 0
  fi
  echo "unset"
  exit 1
fi

case "$requested" in
  wanted|none)
    mkdir -p "$(dirname "$preference_file")"
    printf '%s\n' "$requested" > "$preference_file"
    echo "Saved cvcannon portrait preference: $requested"
    ;;
  *)
    echo "ERROR: portrait preference must be 'wanted' or 'none'." >&2
    exit 1
    ;;
esac
