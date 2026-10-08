#!/usr/bin/env python3
"""Create, render, and verify tailored CV application packs."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from collections.abc import Callable
from datetime import date
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WINDOWS = os.name == "nt"
PROFILE = ROOT / "PROFILE"
MASTER_CV = PROFILE / "master-cv.html"
APPLICATIONS = ROOT / "APPLICATIONS"
TEMPLATES = ROOT / "BASE" / "TEMPLATES"
DEFAULT_TEMPLATE = "default"
SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
PORTRAIT_STEM = "portrait"
# Preference order: WebP first because it renders at the same quality in a smaller
# file, which keeps the finished PDF smaller.
PORTRAIT_EXTENSIONS = ("webp", "png", "jpg", "jpeg")
PORTRAIT_PREFERENCE = ROOT / ".cvcannon" / "portrait"
MODE_PREFERENCE = ROOT / ".cvcannon" / "mode"
# Windows runs every target through cvcannon.cmd, which takes the same arguments as make.
MAKE = "cvcannon.cmd" if WINDOWS else "make"
CLI = "cvcannon.cmd" if WINDOWS else "python3 scripts/cv.py"
EXECUTABLES = (
    ".githooks/pre-commit", "docker-setup.sh", "scripts/cv.py", "scripts/privacy_check.py",
    "scripts/setup.sh", "scripts/docker.sh", "scripts/mode.sh", "scripts/portrait.sh",
)
DOCKER_COMMANDS = (
    "templates", "profile", "doctor", "portrait-convert", "new", "build", "check",
    "build-all", "check-all", "clean", "clean-all", "privacy",
)
PORTRAIT_SRC_RE = re.compile(
    r'src="(?:[^"]*?/)?' + PORTRAIT_STEM + r"\.(?:" + "|".join(PORTRAIT_EXTENSIONS) + r')"'
)
PORTRAIT_IMG_RE = re.compile(
    r"[ \t]*<img\b[^>]*class=[\"'][^\"']*profile-pic[^\"']*[\"'][^>]*>[ \t]*\n?", re.I
)
HEADLESS_SHELL = "chrome-headless-shell/chrome-headless-shell-win64/chrome-headless-shell.exe"
LIBWEBP_URL = "https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.6.0-windows-x64.zip"
CHROME_FOR_TESTING = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
DOCKER_DESKTOP = "https://docs.docker.com/desktop/setup/install/windows-install/"
REQUIRED_TOOLS = ("pdfinfo", "pdftotext", "pdffonts", "pdfimages", "pdftoppm")
DOCUMENTS = (("cv.html", "cv.pdf", 800), ("cover-letter.html", "cover-letter.pdf", 300))
PENDING = "<!-- cvcannon:pending -->"
ANALYSIS_FILES = ("job-description.md", "job-analysis.md", "evidence-map.md", "application-notes.md")

# Phrases and cliches removed by the shared writing style pass. The build fails on these.
BANNED_EVERYWHERE = (
    "results-driven", "results-oriented", "dynamic professional", "highly motivated",
    "detail-oriented", "team player", "self-starter", "proven track record",
    "leveraged", "spearheaded", "synergy", "cutting-edge", "world-class",
    "best-in-class", "game changer", "game-changer", "thought leader", "rockstar",
    "ninja", "guru", "passionate",
)
BANNED_IN_COVER_LETTER = (
    "i am writing to apply", "i saw your posting", "i saw your job posting",
    "saw your posting on linkedin", "perfect candidate", "to whom it may concern",
    "please find my resume attached", "please find attached my resume",
    "please find my cv attached", "i am available for an interview at your convenience",
    "i look forward to hearing from you", "i have always admired", "your innovative company",
)
SOFT_FLAGS = (
    "innovative", "strategic", "exceptional", "dynamic", "visionary", "seamless",
    "state-of-the-art", "world-leading", "unparalleled",
)


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hidden = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"style", "script"}:
            self.hidden += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"style", "script"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


class ParagraphText(HTMLParser):
    """Collect the text of every element carrying one CSS class."""

    def __init__(self, class_name: str) -> None:
        super().__init__()
        self.class_name = class_name
        self.stack: list[str] = []
        self.capture_at: int | None = None
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = ""
        if tag == "p":
            classes = next((value or "" for key, value in attrs if key == "class"), "")
        if self.capture_at is None and self.class_name in classes.split():
            self.capture_at = len(self.stack)
        self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if self.stack:
            self.stack.pop()
        if self.capture_at is not None and len(self.stack) <= self.capture_at:
            self.capture_at = None

    def handle_data(self, data: str) -> None:
        if self.capture_at is not None:
            self.parts.append(data)


def fail(message: str) -> "NoReturn":
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def windows_dirs(*variables: str) -> list[Path]:
    return [Path(os.environ[name]) for name in variables if os.environ.get(name)]


def tools_home() -> Path:
    """Folder for the tools `install` downloads on Windows; needs no administrator rights."""
    return Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "cvcannon" / "tools"


def windows_registry_path() -> list[str]:
    import winreg

    entries: list[str] = []
    keys = (
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
        (winreg.HKEY_CURRENT_USER, "Environment"),
    )
    for root, name in keys:
        try:
            with winreg.OpenKey(root, name) as key:
                value, _ = winreg.QueryValueEx(key, "Path")
        except OSError:
            continue
        entries += [os.path.expandvars(entry) for entry in str(value).split(";") if entry]
    return entries


def refresh_windows_path() -> None:
    """Add PATH entries saved after this shell started, such as freshly installed tools."""
    current = [entry for entry in os.environ.get("PATH", "").split(os.pathsep) if entry]
    known = {os.path.normcase(entry) for entry in current}
    added = [entry for entry in windows_registry_path() if os.path.normcase(entry) not in known]
    if added:
        os.environ["PATH"] = os.pathsep.join(current + added)


def tool(name: str) -> str | None:
    # Take every Poppler command from the installation that provides pdfinfo. Git for
    # Windows ships its own pdftotext, which can come earlier on PATH.
    if name in REQUIRED_TOOLS and name != "pdfinfo":
        pdfinfo = shutil.which("pdfinfo")
        sibling = pdfinfo and shutil.which(name, path=str(Path(pdfinfo).parent))
        if sibling:
            return sibling
    return shutil.which(name)


def browser() -> str | None:
    override = os.environ.get("CVCANNON_BROWSER")
    if override:
        return override if Path(override).is_file() else tool(override)
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        found = shutil.which(name)
        if found:
            return found
    candidates = [Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")]
    if WINDOWS:
        # Edge ships with Windows 10 and 11 and uses the same headless PDF printer.
        roots = windows_dirs("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")
        candidates = [root / "Google/Chrome/Application/chrome.exe" for root in roots]
        candidates += [root / "Chromium/Application/chrome.exe" for root in roots]
        candidates += [root / "Microsoft/Edge/Application/msedge.exe" for root in roots]
        candidates.append(tools_home() / HEADLESS_SHELL)
    return next((str(path) for path in candidates if path.is_file()), None)


def require_master_cv() -> None:
    if not MASTER_CV.is_file() or not MASTER_CV.read_text(encoding="utf-8", errors="ignore").strip():
        fail(
            "missing `PROFILE/master-cv.html`. Ask the user to provide an existing CV, "
            "a text or document file in `PROFILE/`, or their career information in chat; "
            f"then create the authoritative HTML CV with `{MAKE} profile`."
        )


def supported_portrait_name(name: str) -> bool:
    path = Path(name)
    return path.stem == PORTRAIT_STEM and path.suffix.lower().lstrip(".") in PORTRAIT_EXTENSIONS


def validate_portrait(path: Path) -> None:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    extension = path.suffix.lower().lstrip(".")
    header = path.read_bytes()[:16]
    if extension == "png" and not header.startswith(b"\x89PNG\r\n\x1a\n"):
        fail(f"{path.relative_to(ROOT)} exists but is not a PNG file; renaming does not convert it")
    if extension in {"jpg", "jpeg"} and not header.startswith(b"\xff\xd8\xff"):
        fail(f"{path.relative_to(ROOT)} exists but is not a JPEG file; renaming does not convert it")
    if extension == "webp" and not (
        len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    ):
        fail(f"{path.relative_to(ROOT)} exists but is not a WebP file; renaming does not convert it")


def portrait_file() -> Path | None:
    found = [PROFILE / f"{PORTRAIT_STEM}.{ext}" for ext in PORTRAIT_EXTENSIONS]
    found = [path for path in found if path.is_file()]
    if not found:
        return None
    if len(found) > 1:
        ignored = ", ".join(path.name for path in found[1:])
        print(
            f"WARN: multiple portraits in PROFILE/; using {found[0].name} and ignoring {ignored}. "
            "Remove the unused portrait or reference the preferred one.",
            file=sys.stderr,
        )
    return found[0]


def portrait_name() -> str | None:
    path = portrait_file()
    return path.name if path else None


def portrait_preference() -> str:
    if PORTRAIT_PREFERENCE.is_file():
        value = PORTRAIT_PREFERENCE.read_text(encoding="utf-8").strip()
        if value in {"wanted", "none"}:
            return value
    return "unset"


def portrait_img_src(source: str) -> str | None:
    """Return the src of the profile-pic image, None when no such element exists."""
    for tag in re.findall(r"<img\b[^>]*>", source, re.I):
        classes = re.search(r'class=["\']([^"\']*)["\']', tag, re.I)
        if classes and "profile-pic" in classes.group(1).split():
            src = re.search(r'src=["\']([^"\']*)["\']', tag, re.I)
            return src.group(1) if src else ""
    return None


def apply_portrait_src(html: str, prefix: str) -> str:
    name = portrait_name()
    if not name:
        return html
    return PORTRAIT_SRC_RE.sub(f'src="{prefix}{name}"', html)


def remove_portrait_img(html: str) -> str:
    return PORTRAIT_IMG_RE.sub("", html, count=1)


def portrait_note() -> None:
    chosen = portrait_file()
    preference = portrait_preference()
    if chosen:
        if chosen.suffix.lower() != ".webp":
            print(
                f"NOTE: using PROFILE/{chosen.name}. WebP is smaller and preferred; "
                "converting to portrait.webp shrinks the finished PDF."
            )
        if preference == "none":
            print("NOTE: a portrait exists but the saved preference is 'none'; confirm with the user.")
        return
    if preference == "wanted":
        print(
            "NOTE: a portrait is wanted but none is in PROFILE/. Ask the user to add "
            f"{PORTRAIT_STEM}.webp (preferred), {PORTRAIT_STEM}.png, or {PORTRAIT_STEM}.jpg."
        )
    elif preference == "unset":
        print(
            "NOTE: no portrait found. Ask the user whether they intended one. "
            "If yes, have them add it to PROFILE/ as portrait.webp (preferred), portrait.png, "
            f"or portrait.jpg, then run `{CLI} portrait wanted`. "
            f"If no, run `{CLI} portrait none`."
        )


def validate_slug(value: str) -> str:
    if not value:
        fail(f"missing SLUG. Example: {MAKE} new SLUG=acme-platform-engineer")
    if not SLUG_RE.fullmatch(value):
        fail("SLUG must contain lowercase letters, digits, and single hyphen separators")
    return value


def app_dir(slug: str) -> Path:
    return APPLICATIONS / validate_slug(slug)


def template_bundle(value: str = "") -> tuple[str, Path]:
    name = value or DEFAULT_TEMPLATE
    if not SLUG_RE.fullmatch(name):
        fail("TEMPLATE must contain lowercase letters, digits, and hyphens")
    bundle = TEMPLATES / name
    missing = [filename for filename in ("cv.html", "cover-letter.html") if not (bundle / filename).is_file()]
    if missing:
        fail(f"template `{name}` is missing: " + ", ".join(missing))
    return name, bundle


def master_template_name() -> str:
    source = MASTER_CV.read_text(encoding="utf-8")
    match = re.search(r'<meta name="cvcannon-template" content="([a-z0-9-]+)">', source)
    return match.group(1) if match else DEFAULT_TEMPLATE


def list_templates() -> None:
    found = []
    for path in sorted(TEMPLATES.iterdir()):
        if path.is_dir() and (path / "cv.html").is_file() and (path / "cover-letter.html").is_file():
            found.append(path.name)
    if not found:
        fail("no complete template bundles found under BASE/TEMPLATES")
    print("Available templates:")
    for name in found:
        print(f"  {name}")


def run(command: list[str], *, capture: bool = False) -> str:
    command = [tool(command[0]) or command[0], *command[1:]]
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout or "").strip()
        fail(f"command failed ({' '.join(command)}): {detail}")
    return result.stdout if capture else ""


def doctor() -> None:
    problems: list[str] = []
    browser_path = browser()
    if not browser_path:
        problems.append("Chromium or Google Chrome")
    for name in REQUIRED_TOOLS:
        if not tool(name):
            problems.append(name)
    for path in (
        TEMPLATES / DEFAULT_TEMPLATE / "cv.html",
        TEMPLATES / DEFAULT_TEMPLATE / "cover-letter.html",
        ROOT / "ASSETS" / "fonts" / "Lexend-Regular.ttf",
        ROOT / "ASSETS" / "fonts" / "LiberationSerif-Regular.ttf",
        ROOT / "ASSETS" / "fonts" / "LiberationSerif-Bold.ttf",
    ):
        if not path.is_file():
            problems.append(str(path.relative_to(ROOT)))
    if problems:
        hint = f". Run `{MAKE} install` to install the software." if WINDOWS else ""
        fail("missing required software or project files: " + ", ".join(problems) + hint)
    require_master_cv()
    validate_html(MASTER_CV, cv=True, portrait_prefix="")
    portrait_note()
    print(f"Browser: {browser_path}")
    print("Poppler tools: ready")
    print("Authoritative CV: PROFILE/master-cv.html")


def create_master(template: str = "") -> None:
    if MASTER_CV.exists():
        fail("PROFILE/master-cv.html already exists; refusing to overwrite it")
    name, bundle = template_bundle(template)
    source = (bundle / "cv.html").read_text(encoding="utf-8")
    source = source.replace("../../../ASSETS/", "../ASSETS/")
    source = source.replace("../../../PROFILE/", "")
    source = apply_portrait_src(source, "")
    if portrait_file() is None:
        source = remove_portrait_img(source)
    source = source.replace(
        "<head>", f'<head>\n  <meta name="cvcannon-template" content="{name}">', 1
    )
    MASTER_CV.write_text(source, encoding="utf-8")
    print(f"Created PROFILE/master-cv.html from template `{name}`")
    if portrait_name():
        print(f"Using PROFILE/{portrait_name()} as the portrait.")
    else:
        print("No portrait found; the master CV is photo-free.")
    print("Fill it from the supplied CV, files, or chat.")


def convert_portrait() -> None:
    chosen = portrait_file()
    if chosen is None:
        formats = ", ".join(f"{PORTRAIT_STEM}.{ext}" for ext in PORTRAIT_EXTENSIONS)
        fail(f"no portrait found in PROFILE/; add one of {formats} first")
    if chosen.suffix.lower() == ".webp":
        print(f"PROFILE/{chosen.name} is already WebP; nothing to convert.")
        return
    converter = tool("cwebp")
    if not converter:
        fail("cwebp is required to convert the portrait to WebP; " + (f"run `{MAKE} install`" if WINDOWS else "install the `webp` package"))
    target = PROFILE / f"{PORTRAIT_STEM}.webp"
    run([converter, "-quiet", "-q", "90", str(chosen), "-o", str(target)])
    validate_portrait(target)
    print(f"Converted PROFILE/{chosen.name} to PROFILE/{target.name}")
    print(
        "Update the CV portrait src to \"portrait.webp\" in the master and "
        "\"../../PROFILE/portrait.webp\" in applications, then remove the original if unused."
    )


def analysis_scaffolds(slug: str) -> dict[str, str]:
    return {
        "job-description.md": (
            f"{PENDING}\n# Job listing\n\n"
            "Paste the complete listing text here (preferred). If only a link was supplied, "
            "record the URL, retrieval date, and retrieved listing text.\n"
        ),
        "job-analysis.md": (
            f"{PENDING}\n# Job analysis — {slug}\n\n"
            "<!-- Fill this from job-description.md before writing any document. "
            "Remove the pending marker on the first line when complete. -->\n\n"
            "## Target\n"
            "- Company:\n- Role title:\n- Location / work model:\n"
            "- Source (apply URL or channel):\n- Listing saved in: job-description.md\n\n"
            "## Primary responsibilities\n1.\n2.\n3.\n\n"
            "## Employer priorities\n1.\n2.\n\n"
            "## Requirements\n\n"
            "| Requirement | Required or preferred | Importance | Employer terminology |\n"
            "| --- | --- | --- | --- |\n|  |  |  |  |\n\n"
            "## ATS keywords\n- \n\n"
            "## Company context\n"
            "- Product or service:\n- Operating model:\n- Tone (startup / enterprise / technical):\n"
            "- Concrete, verifiable details worth referencing:\n\n"
            "## Recipient\n- Name or greeting target:\n- Known contact or referral:\n"
        ),
        "evidence-map.md": (
            f"{PENDING}\n# Evidence map — {slug}\n\n"
            "<!-- One row per requirement. Ground every claim here before it enters the CV or "
            "cover letter. Match is exact, adjacent, or gap. Evidence source is "
            "PROFILE/master-cv.html or a user-confirmed fact. Remove the pending marker when "
            "complete. -->\n\n"
            "| # | Requirement / priority | Importance | Matching candidate evidence | "
            "Evidence source | Match | Terminology to use | CV? | Letter? |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| 1 |  |  |  |  |  |  |  |  |\n\n"
            "## Coverage summary\n"
            "- Major requirements covered:\n- Gaps remaining:\n"
            "- Strongest connection (lead the cover letter with this):\n"
            "- Second argument:\n- Additional value:\n"
            "- Material gap to address (only if it genuinely needs explaining):\n"
        ),
        "application-notes.md": (
            f"{PENDING}\n# Application notes — {slug}\n\n"
            f"Generated: {date.today().isoformat()}\nStatus: draft\n\n"
            "<!-- Record tailoring decisions and the cover-letter plan, then remove the pending "
            "marker on the first line. -->\n\n"
            "## Tailoring decisions\n\n"
            "### Target\n- Role:\n- Company:\n\n"
            "### Summary\n- Was:\n- Now:\n- Reason:\n\n"
            "### Skills\n- New priority order:\n- Exact terminology introduced:\n"
            "- Removed or de-emphasised:\n\n"
            "### Experience\nFor each role changed:\n"
            "- Role:\n"
            "  - Bullets promoted:\n  - Bullets demoted or removed:\n  - Wording changes:\n"
            "  - Vacancy terminology integrated:\n  - Evidence source:\n\n"
            "### Overall\n- Major requirements covered:\n- Gaps remaining:\n- Sections modified:\n\n"
            "## Cover-letter plan\n"
            "- Opening strategy (company knowledge | mutual connection | problem/role | "
            "achievement | industry insight):\n"
            "- Body 1 direct match (their need + my evidence + result):\n"
            "- Body 2 (additional value or gap handling):\n"
            "- Specific company detail used:\n- Tone:\n- Target length (250–400 words):\n\n"
            "## Validation record\n"
            "- [ ] Every claim is true and traceable to evidence-map.md\n"
            "- [ ] No skills added, metrics altered, achievements invented, or seniority overstated\n"
            "- [ ] Adjacent experience stated honestly; gaps distinguished from direct experience\n"
            "- [ ] Strongest relevant bullets placed prominently\n"
            "- [ ] Keywords present naturally, no stuffing\n"
            "- [ ] Cover letter adds reasoning beyond the CV\n"
            "- [ ] Tone: calm, technically literate, concise, credible\n"
            "- [ ] Both documents pass make build\n"
            "- Notes:\n"
        ),
    }


def scaffold_cv_source(*, template: str, bundle: Path) -> str:
    """Build an application CV source, matching the profile's portrait state."""
    if template:
        source = (bundle / "cv.html").read_text(encoding="utf-8")
        source = source.replace("../../../ASSETS/", "../../ASSETS/")
        source = source.replace("../../../PROFILE/", "../../PROFILE/")
    else:
        source = MASTER_CV.read_text(encoding="utf-8")
        source = source.replace("../ASSETS/", "../../ASSETS/")
    source = apply_portrait_src(source, "../../PROFILE/")
    if portrait_file() is None:
        source = remove_portrait_img(source)
    return source


def new(slug: str, template: str = "") -> None:
    require_master_cv()
    validate_html(MASTER_CV, cv=True, portrait_prefix="")
    name, bundle = template_bundle(template or master_template_name())
    target = app_dir(slug)
    if target.exists():
        fail(f"{target.relative_to(ROOT)} already exists; refusing to overwrite it")
    target.mkdir(parents=True)
    (target / "cv.html").write_text(scaffold_cv_source(template=template, bundle=bundle), encoding="utf-8")
    cover_source = (bundle / "cover-letter.html").read_text(encoding="utf-8")
    cover_source = cover_source.replace("../../../ASSETS/", "../../ASSETS/")
    (target / "cover-letter.html").write_text(cover_source, encoding="utf-8")
    for filename, content in analysis_scaffolds(slug).items():
        (target / filename).write_text(content, encoding="utf-8")
    print(f"Created {target.relative_to(ROOT)} with template `{name}`")
    if template:
        print("Populate the selected CV template from PROFILE/master-cv.html, then tailor it for the role.")
    print("Fill job-description.md, job-analysis.md, and evidence-map.md before writing.")
    print(f"Edit cv.html and cover-letter.html, then run: {MAKE} build SLUG={slug}")


def visible_text(path: Path) -> str:
    parser = VisibleText()
    parser.feed(path.read_text(encoding="utf-8"))
    return " ".join(" ".join(parser.parts).split())


def validate_html(path: Path, *, cv: bool, portrait_prefix: str = "../../PROFILE/") -> None:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    source = path.read_text(encoding="utf-8")
    text = visible_text(path)
    runtime_source = re.sub(r"<!--.*?-->", "", source, flags=re.S)
    runtime_source = re.sub(r"<(style|script)\b.*?</\1>", "", runtime_source, flags=re.S | re.I)
    unresolved = re.findall(r"\{\{[^{}]+\}\}|\[[^\[\]]{2,5000}\]", runtime_source)
    if unresolved:
        sample = ", ".join(unresolved[:3])
        fail(f"unresolved placeholders in {path.relative_to(ROOT)}: {sample}")
    if "lorem ipsum" in text.lower():
        fail(f"placeholder prose remains in {path.relative_to(ROOT)}")
    dependency_source = re.sub(r"<!--.*?-->", "", source, flags=re.S)
    remote_resource = re.search(
        r"<(?:script|img|link)\b[^>]+(?:src|href)=[\"']https?://|"
        r"(?:@import|url\()[^;)]*https?://",
        dependency_source,
        re.I,
    )
    if remote_resource:
        fail(f"remote runtime dependency found in {path.relative_to(ROOT)}")
    if cv:
        src = portrait_img_src(source)
        if src is not None and not src.lower().startswith("data:image/"):
            name = Path(src).name
            expected = f"{portrait_prefix}{name}"
            if not supported_portrait_name(name) or src != expected:
                formats = ", ".join(f"{PORTRAIT_STEM}.{ext}" for ext in PORTRAIT_EXTENSIONS)
                fail(f'CV portrait must use src="{portrait_prefix}{PORTRAIT_STEM}.<ext>" ({formats}) or an embedded image')
            path = PROFILE / name
            if not path.is_file():
                chosen = portrait_file()
                if chosen:
                    fail(
                        f"CV references {name}, but PROFILE/ contains {chosen.name}; "
                        f'use src="{portrait_prefix}{chosen.name}"'
                    )
                formats = ", ".join(f"{PORTRAIT_STEM}.{ext}" for ext in PORTRAIT_EXTENSIONS)
                fail(
                    f"CV shows a portrait but PROFILE/{name} is missing. Add one of {formats} "
                    "(WebP preferred) or remove the profile-pic <img>."
                )
            validate_portrait(path)
            preferred = portrait_file()
            if preferred and preferred.name != name:
                print(
                    f"WARN: PROFILE/{preferred.name} is available and preferred; "
                    "WebP is smaller and shrinks the finished PDF.",
                    file=sys.stderr,
                )


def phrase_hits(text: str, phrases: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    return [
        phrase
        for phrase in phrases
        if re.search(r"\b" + re.escape(phrase) + r"\b", lowered)
    ]


def cover_letter_body_words(path: Path) -> int | None:
    parser = ParagraphText("body-text")
    parser.feed(path.read_text(encoding="utf-8"))
    text = " ".join(" ".join(parser.parts).split())
    if not text:
        return None
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’–-]*", text))


def writing_check(target: Path) -> None:
    problems: list[str] = []
    warnings: list[str] = []
    cv_text = visible_text(target / "cv.html")
    letter_text = visible_text(target / "cover-letter.html")

    for phrase in phrase_hits(cv_text, BANNED_EVERYWHERE):
        problems.append(f"cv.html: remove the phrase '{phrase}'")
    for phrase in phrase_hits(letter_text, BANNED_EVERYWHERE + BANNED_IN_COVER_LETTER):
        problems.append(f"cover-letter.html: remove the phrase '{phrase}'")
    for phrase in phrase_hits(cv_text, SOFT_FLAGS):
        warnings.append(f"cv.html: review '{phrase}' for unsupported self-praise")
    for phrase in phrase_hits(letter_text, SOFT_FLAGS):
        warnings.append(f"cover-letter.html: review '{phrase}' for unsupported self-praise")

    if "—" in cv_text:
        problems.append("cv.html: remove em dashes; use an en dash only for ranges")
    if "—" in letter_text:
        warnings.append("cover-letter.html: em dashes are discouraged; prefer commas or parentheses")

    words = cover_letter_body_words(target / "cover-letter.html")
    if words is None:
        warnings.append("cover-letter.html: could not measure body length; keep it to about 250–400 words")
    else:
        if not 220 <= words <= 440:
            problems.append(f"cover-letter.html: {words} body words; keep it to roughly 250–400")
        elif not 250 <= words <= 400:
            warnings.append(f"cover-letter.html: {words} body words; the target range is 250–400")
        if not re.search(r"\d", letter_text):
            warnings.append("cover-letter.html: include a concrete result or metric when the evidence supports one")

    for message in warnings:
        print(f"WARN: {message}", file=sys.stderr)
    if problems:
        for message in problems:
            print(f"ERROR: {message}", file=sys.stderr)
        print("Fix the writing problems above, then rebuild. See docs/WRITING.md.", file=sys.stderr)
        raise SystemExit(1)


def content_check(target: Path) -> None:
    for name in ANALYSIS_FILES:
        path = target / name
        if not path.is_file():
            fail(
                f"missing {path.relative_to(ROOT)}; create it from the artifact shapes in "
                "docs/WRITING.md before building"
            )
        if PENDING in path.read_text(encoding="utf-8"):
            fail(
                f"{path.relative_to(ROOT)} is still the scaffold; complete it before building "
                "(see docs/WRITING.md)"
            )
    writing_check(target)


def render(html: Path, pdf: Path) -> None:
    browser_path = browser()
    if not browser_path:
        fail("Chromium or Google Chrome is required")
    # A throwaway profile keeps headless runs independent of an open browser window.
    # Without it, Chrome and Edge on Windows hand the request to the running instance.
    profile = tempfile.mkdtemp(prefix="cvcannon-browser-")
    command = [
        browser_path,
        "--headless",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--no-pdf-header-footer",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={profile}",
        "--virtual-time-budget=8000",
        f"--print-to-pdf={pdf.resolve()}",
    ]
    if os.environ.get("CVCANNON_CONTAINER") == "1" or (
        hasattr(os, "geteuid") and os.geteuid() == 0
    ):
        command.append("--no-sandbox")
    command.append(html.resolve().as_uri())
    try:
        run(command)
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    if not pdf.is_file() or pdf.stat().st_size < 1_000:
        fail(f"browser did not produce a valid {pdf.relative_to(ROOT)}")


def pdfinfo(pdf: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in run(["pdfinfo", str(pdf)], capture=True).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def verify_pdf(pdf: Path, *, min_chars: int, require_image: bool) -> None:
    if not pdf.is_file():
        fail(f"missing {pdf.relative_to(ROOT)}")
    info = pdfinfo(pdf)
    if info.get("Pages") != "1":
        fail(f"{pdf.name} must have exactly one page; found {info.get('Pages', 'unknown')}")
    if "A4" not in info.get("Page size", ""):
        fail(f"{pdf.name} is not A4: {info.get('Page size', 'unknown')}")

    fonts = run(["pdffonts", str(pdf)], capture=True)
    if "Type 3" in fonts:
        fail(f"{pdf.name} contains Type 3 fonts; its text may not be selectable")
    font_rows = [line for line in fonts.splitlines()[2:] if line.strip()]
    if not font_rows:
        fail(f"{pdf.name} contains no detectable fonts")
    for row in font_rows:
        columns = row.split()
        if len(columns) >= 6 and columns[-5].lower() != "yes":
            fail(f"{pdf.name} contains a non-embedded font: {columns[0]}")

    text = run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"], capture=True)
    compact = re.sub(r"\s+", "", text)
    if len(compact) < min_chars:
        fail(f"{pdf.name} has only {len(compact)} extracted characters; expected at least {min_chars}")
    if "{{" in text or "lorem ipsum" in text.lower():
        fail(f"{pdf.name} contains unresolved template content")

    if require_image:
        images = run(["pdfimages", "-list", str(pdf)], capture=True)
        rows = [line for line in images.splitlines() if re.match(r"\s*\d+\s+\d+\s+", line)]
        if not rows:
            fail(f"{pdf.name} does not contain the portrait image")


def check(slug: str) -> None:
    target = app_dir(slug)
    if not target.is_dir():
        fail(f"missing {target.relative_to(ROOT)}")
    content_check(target)
    preview_dir = target / "previews"
    preview_dir.mkdir(exist_ok=True)
    for html_name, pdf_name, min_chars in DOCUMENTS:
        pdf = target / pdf_name
        html = target / html_name
        require_image = html_name == "cv.html" and portrait_img_src(html.read_text(encoding="utf-8")) is not None
        verify_pdf(pdf, min_chars=min_chars, require_image=require_image)
        run([
            "pdftoppm", "-png", "-singlefile", "-r", "144", str(pdf),
            str(preview_dir / Path(pdf_name).stem),
        ])
        print(f"PASS {pdf.relative_to(ROOT)}: one A4 page, embedded fonts, extractable text")
    print(f"Previews: {preview_dir.relative_to(ROOT)}")
    print("Open both preview PNGs and visually inspect layout before sending the PDFs.")


def build(slug: str) -> None:
    doctor()
    target = app_dir(slug)
    if not target.is_dir():
        fail(f"missing {target.relative_to(ROOT)}; run {MAKE} new SLUG={slug} first")
    for html_name, pdf_name, _ in DOCUMENTS:
        html = target / html_name
        validate_html(html, cv=(html_name == "cv.html"))
        render(html, target / pdf_name)
    check(slug)


def clean(slug: str) -> None:
    target = app_dir(slug)
    if not target.is_dir():
        fail(f"missing {target.relative_to(ROOT)}")
    for _, pdf_name, _ in DOCUMENTS:
        (target / pdf_name).unlink(missing_ok=True)
    shutil.rmtree(target / "previews", ignore_errors=True)
    print(f"Removed generated PDFs and previews from {target.relative_to(ROOT)}")


def application_slugs() -> list[str]:
    if not APPLICATIONS.is_dir():
        return []
    return sorted(
        path.name
        for path in APPLICATIONS.iterdir()
        if path.is_dir() and SLUG_RE.fullmatch(path.name) and (path / "cv.html").is_file()
    )


def for_every_application(action: Callable[[str], None], verb: str) -> None:
    slugs = application_slugs()
    if not slugs:
        fail(f"no applications found under {APPLICATIONS.relative_to(ROOT)}")
    failed: list[str] = []
    for slug in slugs:
        print(f"==> {verb} {slug}")
        try:
            action(slug)
        except SystemExit as error:
            if error.code:
                failed.append(slug)
    if failed:
        fail(f"{verb} failed for: " + ", ".join(failed))
    print(f"{verb} finished for {len(slugs)} application(s).")


def build_all() -> None:
    for_every_application(build, "build")


def check_all() -> None:
    for_every_application(check, "check")


def clean_all() -> None:
    for_every_application(clean, "clean")


def saved_choice(path: Path, value: str, allowed: tuple[str, ...], label: str) -> None:
    """Print or save a local preference under the ignored .cvcannon/ directory."""
    if not value:
        if path.is_file():
            print(path.read_text(encoding="utf-8").strip())
            return
        print("unset")
        raise SystemExit(1)
    if value not in allowed:
        fail(f"{label} must be " + " or ".join(f"'{option}'" for option in allowed))
    path.parent.mkdir(exist_ok=True)
    path.write_text(f"{value}\n", encoding="utf-8")
    print(f"Saved cvcannon {label}: {value}")


def configure_git() -> None:
    if not (ROOT / ".git").exists():
        run(["git", "init", "-b", "main"])
    run(["git", "config", "core.hooksPath", ".githooks"])
    if not WINDOWS:
        for name in EXECUTABLES:
            path = ROOT / name
            if path.is_file():
                path.chmod(path.stat().st_mode | 0o111)
    print("Configured local Git hooks.")


def setup() -> None:
    configure_git()
    doctor()


def docker_ready() -> None:
    if not tool("docker"):
        fail("Docker is not installed or is not on PATH. Install Docker Desktop or Docker Engine with the Compose plugin.")
    checks = (
        (["docker", "compose", "version"], "Docker Compose is unavailable. Install a current Docker Desktop or Docker Engine with the Compose plugin."),
        (["docker", "info"], "the Docker daemon is not running or is not accessible. Start Docker, then retry."),
    )
    for command, message in checks:
        if subprocess.run(command, cwd=ROOT, capture_output=True, check=False).returncode:
            fail(message)


def docker_env() -> dict[str, str]:
    env = dict(os.environ)
    # Linux bind mounts keep host ownership, so run as the host user. Docker Desktop on
    # Windows and macOS maps ownership itself and keeps the Compose default.
    if hasattr(os, "getuid"):
        env["CVCANNON_UID"] = str(os.getuid())
        env["CVCANNON_GID"] = str(os.getgid())
    return env


def docker_run(args: list[str]) -> None:
    docker_ready()
    command = ["docker", "compose", "run", "--rm", "cvcannon", *(args or ["make", "help"])]
    code = subprocess.run(command, cwd=ROOT, env=docker_env(), check=False).returncode
    if code:
        raise SystemExit(code)


def docker_cv(command: str, *args: str) -> None:
    docker_run(["python3", "scripts/cv.py", command, *args])


def docker_image() -> None:
    docker_ready()
    code = subprocess.run(["docker", "compose", "build"], cwd=ROOT, env=docker_env(), check=False).returncode
    if code:
        raise SystemExit(code)


def docker_setup() -> None:
    docker_ready()
    print("Building the cvcannon toolchain...")
    docker_image()
    configure_git()
    print("Checking the container and repository...")
    docker_cv("templates")
    docker_cv("privacy")
    if MASTER_CV.is_file() and MASTER_CV.stat().st_size:
        docker_cv("doctor")
        print("cvcannon is ready. Add listings, then create an application with:")
        print(f"  {MAKE} docker-new SLUG=company-role")
        return
    print()
    print("The Docker toolchain is ready. Continue the agent workflow:")
    print("  1. Ask the user to drop an existing CV or career notes into PROFILE/, or provide them in chat.")
    print(f"  2. Run {MAKE} docker-profile.")
    print("  3. Complete PROFILE/master-cv.html from the supplied material.")
    print(f"  4. Run {MAKE} docker-doctor.")


def privacy() -> None:
    code = subprocess.run([sys.executable, str(ROOT / "scripts" / "privacy_check.py")], check=False).returncode
    if code:
        raise SystemExit(code)


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "cvcannon"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def github_asset(repository: str, pattern: str) -> str:
    release = json.loads(fetch(f"https://api.github.com/repos/{repository}/releases/latest"))
    for asset in release.get("assets", []):
        if re.fullmatch(pattern, asset["name"]):
            return asset["browser_download_url"]
    fail(f"no download matching {pattern} in the latest {repository} release")


def install_zip(name: str, url: str) -> Path:
    """Download a zip into the per-user tools folder, replacing an older copy."""
    print(f"Downloading {name} from {url}")
    target = tools_home() / name
    archive = tools_home() / f"{name}.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_bytes(fetch(url))
    shutil.rmtree(target, ignore_errors=True)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(target)
    archive.unlink()
    return target


def add_user_path(directory: Path) -> None:
    """Append a folder to the user PATH so new terminals and this process find it."""
    import ctypes
    import winreg

    entry = str(directory)
    access = winreg.KEY_READ | winreg.KEY_WRITE
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, "Environment", 0, access) as key:
        try:
            value, kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            value, kind = "", winreg.REG_EXPAND_SZ
        entries = [item for item in str(value).split(";") if item]
        if os.path.normcase(entry) not in {os.path.normcase(item) for item in entries}:
            if kind not in (winreg.REG_SZ, winreg.REG_EXPAND_SZ):
                kind = winreg.REG_EXPAND_SZ
            winreg.SetValueEx(key, "Path", 0, kind, ";".join(entries + [entry]))
    # Tell Explorer and terminals opened later that the environment changed.
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, None)
    refresh_windows_path()
    if os.path.normcase(entry) not in {os.path.normcase(item) for item in os.environ["PATH"].split(os.pathsep)}:
        os.environ["PATH"] += os.pathsep + entry


def tools(*, docker: bool = False) -> None:
    """Report the software cvcannon needs and fail when a required tool is missing."""
    rows = [("python", sys.executable, True), ("git", tool("git"), True)]
    if docker:
        rows.append(("docker", tool("docker"), True))
    else:
        rows.append(("browser", browser(), True))
        rows += [(name, tool(name), True) for name in REQUIRED_TOOLS]
        rows.append(("cwebp (portrait-convert only)", tool("cwebp"), False))
    for name, found, _ in rows:
        print(f"{name}: {found or 'missing'}")
    missing = [name for name, found, required in rows if required and not found]
    if missing:
        hint = f" Run `{MAKE} install` to install them." if WINDOWS else " See docs/SETUP.md."
        fail("missing " + ", ".join(missing) + "." + hint)
    print("All required tools are available.")


def install(mode: str = "") -> None:
    """Install the Windows toolchain per user, without administrator rights or prompts."""
    mode = mode or "native"
    if not WINDOWS:
        fail("`install` sets up Windows. On Linux and macOS, install the packages listed in docs/SETUP.md.")
    if mode not in ("native", "docker"):
        fail("install mode must be 'native' or 'docker'")
    if not tool("git"):
        home = install_zip("git", github_asset("git-for-windows/git", r"MinGit-[\d.]+-64-bit\.zip"))
        add_user_path(home / "cmd")
    if mode == "docker":
        if not tool("docker"):
            fail(
                "Docker Desktop is not installed. It needs administrator rights and usually a "
                "restart, so ask the user to install it from " + DOCKER_DESKTOP + " or with "
                "`winget install --id Docker.DockerDesktop -e`, start it, and then continue with "
                f"`{MAKE} docker-setup`. Alternatively, choose native mode, which needs no installation by the user."
            )
        tools(docker=True)
        return
    if not all(tool(name) for name in REQUIRED_TOOLS):
        home = install_zip("poppler", github_asset("oschwartz10612/poppler-windows", r"Release-[\d.-]+\.zip"))
        add_user_path(next(home.glob("*/Library/bin")))
    if not tool("cwebp"):
        home = install_zip("libwebp", LIBWEBP_URL)
        add_user_path(next(home.glob("*/bin")))
    if not browser():
        # Windows normally includes Edge. Without any Chromium-family browser, download
        # Chrome's portable headless build, which needs no installer.
        downloads = json.loads(fetch(CHROME_FOR_TESTING))["channels"]["Stable"]["downloads"]
        url = next(item["url"] for item in downloads["chrome-headless-shell"] if item["platform"] == "win64")
        install_zip("chrome-headless-shell", url)
    tools()


def help_text() -> None:
    print(
        """cvcannon — turn batches of job listings into polished application packs

  make setup                         initialize local Git and hooks, then run doctor
  make templates                     list saved template bundles
  make profile [TEMPLATE=name]       create the authoritative CV with a template
  make doctor                        check tools and the authoritative CV
  make portrait-convert              convert the portrait to WebP to shrink the PDF
  make new SLUG=role [TEMPLATE=name] scaffold an application, optionally with another template
  make build SLUG=company-role       render, verify, and create preview PNGs
  make check SLUG=company-role       verify existing PDFs and refresh previews
  make clean SLUG=company-role       remove generated PDFs and previews
  make build-all                     build every application under APPLICATIONS/
  make check-all                     verify and refresh every application
  make clean-all                     remove generated files from every application
  make privacy                       scan Git candidates for personal data

  make docker-setup                  build and verify the optional Docker toolchain
  make docker-new SLUG=role          scaffold through Docker
  make docker-build SLUG=role        render and verify through Docker

On Windows, use cvcannon.cmd in place of make, with the same arguments:

  cvcannon.cmd install [docker]      install Python and the toolchain for the current user
  cvcannon.cmd build SLUG=company-role

Additional commands (cvcannon.cmd <command>, or python3 scripts/cv.py <command>):

  tools                              report the required software
  mode [docker|native]               print or save the execution mode
  portrait [wanted|none]             print or save the portrait preference
  docker <command...>                run any command in the toolchain container
"""
    )


def main(argv: list[str]) -> None:
    for stream in (sys.stdout, sys.stderr):
        # Windows consoles and pipes may use a legacy code page that cannot print every
        # character in these messages.
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    if WINDOWS:
        refresh_windows_path()
    command = argv[1] if len(argv) > 1 else "help"
    # Accept make-style SLUG=... and TEMPLATE=... as well as positional values.
    named = dict(arg.split("=", 1) for arg in argv[2:] if re.match(r"(SLUG|TEMPLATE)=", arg))
    positional = [arg for arg in argv[2:] if not re.match(r"(SLUG|TEMPLATE)=", arg)]
    slug = named.get("SLUG", positional[0] if positional else "")
    template = named.get("TEMPLATE", positional[1] if len(positional) > 1 else "")
    if command == "docker":
        docker_run(argv[2:])
        return
    if command.startswith("docker-") and command[len("docker-"):] in DOCKER_COMMANDS:
        docker_cv(command[len("docker-"):], *argv[2:])
        return
    actions = {
        "help": lambda: help_text(),
        "setup": setup,
        "mode": lambda: saved_choice(MODE_PREFERENCE, slug, ("docker", "native"), "execution mode"),
        "portrait": lambda: saved_choice(PORTRAIT_PREFERENCE, slug, ("wanted", "none"), "portrait preference"),
        "privacy": privacy,
        "install": lambda: install(slug),
        "tools": tools,
        "docker-setup": docker_setup,
        "docker-image": docker_image,
        "templates": list_templates,
        "profile": lambda: create_master(named.get("TEMPLATE") or slug),
        "doctor": doctor,
        "portrait-convert": convert_portrait,
        "new": lambda: new(slug, template),
        "build": lambda: build(slug),
        "check": lambda: check(slug),
        "clean": lambda: clean(slug),
        "build-all": build_all,
        "check-all": check_all,
        "clean-all": clean_all,
    }
    action = actions.get(command)
    if not action:
        fail(f"unknown command: {command}")
    action()


if __name__ == "__main__":
    main(sys.argv)
