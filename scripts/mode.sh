#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mode_file="$repo_root/.cvcannon/mode"
requested="${1:-}"

if [[ -z "$requested" ]]; then
  if [[ -f "$mode_file" ]]; then
    cat "$mode_file"
    exit 0
  fi
  echo "unset"
  exit 1
fi

case "$requested" in
  docker|native)
    mkdir -p "$(dirname "$mode_file")"
    printf '%s\n' "$requested" > "$mode_file"
    echo "Saved cvcannon execution mode: $requested"
    ;;
  *)
    echo "ERROR: mode must be 'docker' or 'native'." >&2
    exit 1
    ;;
esac
