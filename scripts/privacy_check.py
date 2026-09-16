#!/usr/bin/env python3
"""Reject common personal data and application artifacts before they enter Git."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALLOW_PROFILE = {"PROFILE/.gitkeep", "PROFILE/README.md"}
ALLOW_APPLICATIONS = {"APPLICATIONS/.gitkeep", "APPLICATIONS/README.md"}
BINARY_SUFFIXES = {".ttf", ".woff", ".woff2"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".heic"}
PUBLIC_IMAGES = {"ASSETS/branding/cvcannon-logo.png"}
PATTERNS = (
    ("absolute home path", re.compile(r"(?:/home/|/Users/)[A-Za-z0-9._-]+/")),
    ("email address", re.compile(r"\b[A-Z0-9._%+-]+@(?!example\.(?:com|org|net)\b)[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("international phone number", re.compile(r"(?<![\w.-])\+[1-9][0-9 ()-]{7,}[0-9]")),
    ("file URL with absolute path", re.compile(r"file:///(?:home|Users)/")),
)


def git_paths(staged: bool) -> list[str]:
    if staged:
        command = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"]
    else:
        command = ["git", "ls-files", "--cached", "--others", "--exclude-standard"]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        print("ERROR: initialize Git with `make setup` before running the privacy scan.", file=sys.stderr)
        raise SystemExit(1)
    return [line for line in result.stdout.splitlines() if line]


def staged_bytes(path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f":{path}"], cwd=ROOT, capture_output=True, check=False
    )
    return result.stdout if result.returncode == 0 else None


def main() -> None:
    staged = "--staged" in sys.argv[1:]
    findings: list[str] = []
    for relative in git_paths(staged):
        path = Path(relative)
        normalized = path.as_posix()
        if normalized.startswith("PROFILE/") and normalized not in ALLOW_PROFILE:
            findings.append(f"{normalized}: completed candidate profile data must not be tracked")
            continue
        if normalized.startswith("APPLICATIONS/") and normalized not in ALLOW_APPLICATIONS:
            findings.append(f"{normalized}: application material must not be tracked")
            continue
        if path.suffix.lower() in IMAGE_SUFFIXES and normalized not in PUBLIC_IMAGES:
            findings.append(f"{normalized}: image files require explicit privacy review and are blocked")
            continue
        if path.suffix.lower() in BINARY_SUFFIXES:
            continue
        data = staged_bytes(normalized) if staged else None
        if data is None:
            disk_path = ROOT / path
            if not disk_path.is_file():
                continue
            data = disk_path.read_bytes()
        if b"\x00" in data:
            continue
        text = data.decode("utf-8", errors="replace")
        for label, pattern in PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{normalized}:{line}: possible {label}")
        if path.suffix.lower() in {".html", ".htm"}:
            for line_no, line in enumerate(text.splitlines(), 1):
                if 'href="mailto:' in line and "{{Email}}" not in line and "@example." not in line:
                    findings.append(f"{normalized}:{line_no}: non-placeholder mailto link")
                if 'href="tel:' in line and "{{Phone}}" not in line:
                    findings.append(f"{normalized}:{line_no}: non-placeholder telephone link")

    if findings:
        print("Privacy check failed:", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        print("Move personal files to PROFILE/ or APPLICATIONS/ and remove identifiers from project files.", file=sys.stderr)
        raise SystemExit(1)
    mode = "staged files" if staged else "Git candidate files"
    print(f"Privacy check passed for {mode} ({len(git_paths(staged))} files).")


if __name__ == "__main__":
    main()
