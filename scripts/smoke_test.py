#!/usr/bin/env python3
"""Exercise the full scaffold -> analyze -> render -> verify pipeline on synthetic data.

The test runs against a throwaway copy of the repository, so it never touches the
real PROFILE/ or APPLICATIONS/ folders. It is intended for CI, where the Docker
toolchain supplies Chromium and Poppler.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SLUG = "smoke-test"
IGNORE = shutil.ignore_patterns(
    ".git", "PROFILE", "APPLICATIONS", ".cvcannon", "__pycache__", ".venv", "*.pyc"
)

MASTER_CV = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Smoke Test Candidate - Curriculum Vitae</title>
  <style>
    @font-face{font-family:'Lexend';font-style:normal;font-weight:300;src:url('../ASSETS/fonts/Lexend-Light.ttf') format('truetype');}
    @font-face{font-family:'Lexend';font-style:normal;font-weight:400;src:url('../ASSETS/fonts/Lexend-Regular.ttf') format('truetype');}
    @font-face{font-family:'Lexend';font-style:normal;font-weight:600;src:url('../ASSETS/fonts/Lexend-SemiBold.ttf') format('truetype');}
    @page{size:A4;margin:0;}
    *{margin:0;padding:0;box-sizing:border-box;}
    body{font-family:'Lexend',Arial,sans-serif;font-weight:300;color:#1e293b;line-height:1.4;}
    .cv{width:210mm;padding:9mm 14mm;font-size:8.5pt;}
    h1{font-size:18pt;font-weight:600;color:#0b2b40;}
    h2{font-size:9pt;font-weight:600;text-transform:uppercase;border-bottom:1px solid #dce3ed;margin:0.5rem 0 0.2rem;}
    li{font-size:7.5pt;margin-left:1rem;}
  </style>
</head>
<body>
  <main class="cv">
    <h1>Smoke Test Candidate</h1>
    <p>Systems operator focused on automation, Linux administration, integrations, and production support.</p>
    <h2>Profile</h2>
    <p>Maintains self-hosted infrastructure and internal tooling for small teams. Builds and debugs workflow automations, integrates external APIs, and keeps production systems running without downtime. Comfortable owning an unfamiliar system end to end, documenting how it works, and improving the parts that fail most often.</p>
    <h2>Work experience</h2>
    <ul>
      <li>Operated a fleet of 12 Linux servers, handling patching, backups, monitoring, and incident response for a distributed team.</li>
      <li>Designed and maintained automation workflows that moved data between internal services and external APIs without manual steps.</li>
      <li>Wrote internal documentation and runbooks so recurring maintenance could be performed by any team member.</li>
      <li>Investigated production incidents, traced failures across logs and services, and shipped fixes that removed the root cause.</li>
      <li>Built small Python and shell tools to replace repetitive operational tasks and reduce manual error rates.</li>
    </ul>
    <h2>Skills</h2>
    <p>Linux administration, automation, API integration, production support, troubleshooting, infrastructure, internal tooling, documentation.</p>
  </main>
</body>
</html>
"""

COVER_LETTER = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Smoke Test Candidate - Cover Letter</title>
  <style>
    @font-face{font-family:'Lexend';font-style:normal;font-weight:300;src:url('../../ASSETS/fonts/Lexend-Light.ttf') format('truetype');}
    @page{size:A4;margin:0;}
    *{margin:0;padding:0;box-sizing:border-box;}
    body{font-family:'Lexend',Arial,sans-serif;font-weight:300;color:#1e293b;line-height:1.5;}
    .letter{width:210mm;padding:9mm 14mm;font-size:9.5pt;}
    p.body-text{margin-bottom:0.55rem;text-align:justify;}
  </style>
</head>
<body>
  <main class="letter">
    <p class="body-text">Dear Hiring Team,</p>
    <p class="body-text">Your listing asks for someone who can keep production systems stable while automating the manual work around them. That mix is the core of my recent work. I operated a fleet of Linux servers for a distributed team, handling patching, backups, monitoring, and incident response, and I owned the automation that connected those systems to the rest of the business.</p>
    <p class="body-text">The automation work was not side work. I built and maintained workflows that moved data between internal services and external APIs without manual steps, which removed a recurring source of errors and freed the team from repetitive data entry. When a workflow failed, I traced the failure across logs and services, fixed the root cause, and added validation so the same silent failure could not return. That is the kind of ownership I would bring to this role.</p>
    <p class="body-text">I also work well in the unclear parts of a role. I have taken over systems I did not build, read the code and configuration until I understood them, documented how they ran, and then improved the parts that failed most often. I do not need a complete specification to make progress, and I do not leave a system harder to operate than I found it.</p>
    <p class="body-text">I would welcome the chance to discuss how I can help your team reduce operational load and keep its production environment reliable. I am happy to walk through the systems I have run and the failures I have fixed. Thank you for your time and consideration.</p>
    <p class="body-text">Sincerely,</p>
    <p class="body-text">Smoke Test Candidate</p>
  </main>
</body>
</html>
"""

ANALYSIS = {
    "job-description.md": "# Job listing\n\nSynthetic listing used by the cvcannon smoke test.\n",
    "job-analysis.md": "# Job analysis\n\nSynthetic analysis used by the cvcannon smoke test.\n",
    "evidence-map.md": "# Evidence map\n\nSynthetic evidence map used by the cvcannon smoke test.\n",
    "application-notes.md": "# Application notes\n\nSynthetic notes used by the cvcannon smoke test.\n",
}


def run(*args: str, cwd: Path) -> None:
    print(f"$ {' '.join(args)}")
    result = subprocess.run(args, cwd=cwd, text=True)
    if result.returncode:
        raise SystemExit(f"smoke test command failed: {' '.join(args)}")


def main() -> None:
    workdir = Path(tempfile.mkdtemp(prefix="cvcannon-smoke-"))
    try:
        shutil.copytree(ROOT, workdir / "repo", ignore=IGNORE)
        repo = workdir / "repo"
        (repo / "PROFILE").mkdir()
        (repo / "APPLICATIONS").mkdir()
        (repo / "PROFILE" / "master-cv.html").write_text(MASTER_CV)

        run(sys.executable, "scripts/cv.py", "doctor", cwd=repo)
        run(sys.executable, "scripts/cv.py", "new", SLUG, cwd=repo)

        target = repo / "APPLICATIONS" / SLUG
        (target / "cover-letter.html").write_text(COVER_LETTER)
        for name, content in ANALYSIS.items():
            (target / name).write_text(content)

        run(sys.executable, "scripts/cv.py", "build", SLUG, cwd=repo)
        run(sys.executable, "scripts/cv.py", "check", SLUG, cwd=repo)

        for name in ("cv.pdf", "cover-letter.pdf"):
            pdf = target / name
            if not pdf.is_file():
                raise SystemExit(f"smoke test did not produce {name}")
        if not (target / "previews" / "cv.png").is_file():
            raise SystemExit("smoke test did not produce preview images")

        print("SMOKE TEST PASSED: scaffold, analyze, render, and verify all succeeded.")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
