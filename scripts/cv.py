#!/usr/bin/env python3
"""Create, render, and verify tailored CV application packs."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from datetime import date
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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
PORTRAIT_SRC_RE = re.compile(
    r'src="(?:[^"]*?/)?' + PORTRAIT_STEM + r"\.(?:" + "|".join(PORTRAIT_EXTENSIONS) + r')"'
)
PORTRAIT_IMG_RE = re.compile(
    r"[ \t]*<img\b[^>]*class=[\"'][^\"']*profile-pic[^\"']*[\"'][^>]*>[ \t]*\n?", re.I
)
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


def tool(name: str) -> str | None:
    return shutil.which(name)


def browser() -> str | None:
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        found = tool(name)
        if found:
            return found
    mac = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    return str(mac) if mac.exists() else None


def require_master_cv() -> None:
    if not MASTER_CV.is_file() or not MASTER_CV.read_text(errors="ignore").strip():
        fail(
            "missing `PROFILE/master-cv.html`. Ask the user to provide an existing CV, "
            "a text or document file in `PROFILE/`, or their career information in chat; "
            "then create the authoritative HTML CV with `make profile`."
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
        value = PORTRAIT_PREFERENCE.read_text().strip()
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
            "or portrait.jpg, then run `bash scripts/portrait.sh wanted`. "
            "If no, run `bash scripts/portrait.sh none`."
        )


def validate_slug(value: str) -> str:
    if not value:
        fail("missing SLUG. Example: make new SLUG=acme-platform-engineer")
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
    source = MASTER_CV.read_text()
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
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
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
        fail("missing required software or project files: " + ", ".join(problems))
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
    source = (bundle / "cv.html").read_text()
    source = source.replace("../../../ASSETS/", "../ASSETS/")
    source = source.replace("../../../PROFILE/", "")
    source = apply_portrait_src(source, "")
    if portrait_file() is None:
        source = remove_portrait_img(source)
    source = source.replace(
        "<head>", f'<head>\n  <meta name="cvcannon-template" content="{name}">', 1
    )
    MASTER_CV.write_text(source)
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
        fail("cwebp is required to convert the portrait to WebP; install the `webp` package")
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
        source = (bundle / "cv.html").read_text()
        source = source.replace("../../../ASSETS/", "../../ASSETS/")
        source = source.replace("../../../PROFILE/", "../../PROFILE/")
    else:
        source = MASTER_CV.read_text()
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
    (target / "cv.html").write_text(scaffold_cv_source(template=template, bundle=bundle))
    cover_source = (bundle / "cover-letter.html").read_text()
    cover_source = cover_source.replace("../../../ASSETS/", "../../ASSETS/")
    (target / "cover-letter.html").write_text(cover_source)
    for filename, content in analysis_scaffolds(slug).items():
        (target / filename).write_text(content)
    print(f"Created {target.relative_to(ROOT)} with template `{name}`")
    if template:
        print("Populate the selected CV template from PROFILE/master-cv.html, then tailor it for the role.")
    print("Fill job-description.md, job-analysis.md, and evidence-map.md before writing.")
    print("Edit cv.html and cover-letter.html, then run: " + f"make build SLUG={slug}")


def visible_text(path: Path) -> str:
    parser = VisibleText()
    parser.feed(path.read_text())
    return " ".join(" ".join(parser.parts).split())


def validate_html(path: Path, *, cv: bool, portrait_prefix: str = "../../PROFILE/") -> None:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    source = path.read_text()
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
    parser.feed(path.read_text())
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
        if PENDING in path.read_text():
            fail(
                f"{path.relative_to(ROOT)} is still the scaffold; complete it before building "
                "(see docs/WRITING.md)"
            )
    writing_check(target)


def render(html: Path, pdf: Path) -> None:
    browser_path = browser()
    if not browser_path:
        fail("Chromium or Google Chrome is required")
    command = [
        browser_path,
        "--headless",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--no-pdf-header-footer",
        "--virtual-time-budget=8000",
        f"--print-to-pdf={pdf.resolve()}",
    ]
    if os.environ.get("CVCANNON_CONTAINER") == "1" or (
        hasattr(os, "geteuid") and os.geteuid() == 0
    ):
        command.append("--no-sandbox")
    command.append(html.resolve().as_uri())
    run(command)
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

    text = run(["pdftotext", str(pdf), "-"], capture=True)
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
        require_image = html_name == "cv.html" and portrait_img_src(html.read_text()) is not None
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
        fail(f"missing {target.relative_to(ROOT)}; run make new SLUG={slug} first")
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

  ./docker-setup.sh                  build and verify the optional Docker toolchain
  make docker-new SLUG=role          scaffold through Docker
  make docker-build SLUG=role        render and verify through Docker
"""
    )


def main(argv: list[str]) -> None:
    command = argv[1] if len(argv) > 1 else "help"
    slug = argv[2] if len(argv) > 2 else ""
    template = argv[3] if len(argv) > 3 else ""
    actions = {
        "help": lambda: help_text(),
        "templates": list_templates,
        "profile": lambda: create_master(slug),
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
