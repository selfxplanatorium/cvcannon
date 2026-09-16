# <img src="ASSETS/branding/cvcannon-logo.png" alt="cvcannon" width="760">

**Agent framework to turn a batch of job listings into organized, polished, ATS-friendly application packs.**

cvcannon accepts several job listings at once and produces a separate tailored CV and cover letter for every role. Paste the complete listing text for the most reliable result, or provide listing links when the text is unavailable. The system organizes each application, selects relevant evidence from the candidate profile, generates the documents, exports the PDFs, and checks their technical quality.

It is built for turning a long list of opportunities into consistent, review-ready application packs within minutes. Reusable HTML templates, bundled static fonts, headless Chromium, and Poppler checks keep the output polished and ATS readable. Serif headings use the system font stack defined in the templates.

The included design is a starting point. Templates are intentionally customizable: typography, fonts, colors, spacing, section structure, icons, and other visual choices can be changed. Multiple named CV and cover letter template pairs can be saved and reused.

## How it works

1. Provide multiple job listings in one request. Full pasted text is preferred because it preserves the exact requirements even if a listing changes or disappears.
2. On first use, cvcannon turns an existing CV, a document, a text file, or information pasted in chat into one authoritative HTML CV.
3. cvcannon creates one organized folder per role and tailors a copy of the authoritative CV with the most relevant experience, skills, and terminology.
4. Each application receives a matching cover letter, two verified PDFs, and visual previews.
5. Review the finished application packs and submit the ones you want.

## Quick start

### 1. Install the prerequisites

You need:

- Python 3.10 or newer
- GNU Make
- Git
- Chromium or Google Chrome
- Poppler tools: `pdfinfo`, `pdftotext`, `pdffonts`, `pdfimages`, and `pdftoppm`

See the [complete setup guide](docs/SETUP.md) for package names and platform notes.

### 2. Provide existing candidate information

Use whichever format is already available:

- drop an existing CV into `PROFILE/`;
- add a PDF, DOCX, HTML, Markdown, or text file containing career information; or
- paste career information directly into chat when working with an agent.

The agent creates `PROFILE/master-cv.html` from the supplied material. This becomes the authoritative CV used in every later session. A portrait is optional; save it as `PROFILE/portrait.png` when wanted.

For manual setup, create the master shell:

```bash
make profile
```

Fill it from the supplied source material, remove unused sections and placeholders, then continue.

To start the master CV with another saved template:

```bash
make profile TEMPLATE=editorial
```

### 3. Initialize and verify the environment

```bash
make setup
make privacy
```

`make setup` configures the project and checks the required software and authoritative CV.

### 4. Provide one or more listings

When working with an agent, paste all listings into the same request. Separate them with headings or blank lines. Complete listing text is preferred; URLs are supported when necessary.

For direct command-line use, create a folder for each listing:

```bash
make new SLUG=acme-platform-engineer
make new SLUG=example-data-analyst
```

To use another saved design for one application:

```bash
make new SLUG=acme-platform-engineer TEMPLATE=editorial
```

Without `TEMPLATE`, the completed master CV is copied. With `TEMPLATE`, the selected template shell is used and the agent populates it from the master CV before tailoring it.

Edit:

- `APPLICATIONS/acme-platform-engineer/cv.html`
- `APPLICATIONS/acme-platform-engineer/cover-letter.html`
- `APPLICATIONS/acme-platform-engineer/job-description.md`

Replace every visible placeholder and all sample prose with supported, role-specific content.

### 5. Build and review

```bash
make build SLUG=acme-platform-engineer
```

The build creates and verifies `cv.pdf` and `cover-letter.pdf`, then renders PNG previews. Open both files under `APPLICATIONS/acme-platform-engineer/previews/` and inspect them before sending the PDFs.

## What the build verifies

- exactly one A4 page per document;
- static embedded fonts with no Type 3 text;
- meaningful selectable text;
- no unresolved visible placeholders or Lorem Ipsum;
- an embedded portrait when the master CV uses one;
- preview images for visual review.

Automated checks cannot judge factual accuracy, writing quality, visual balance, or whether the contact row wrapped. Human review remains required.

## Project layout

| Path | Contents |
| --- | --- |
| `BASE/TEMPLATES/<name>/` | Saved CV and cover letter template pairs |
| `ASSETS/fonts/` | Lexend fonts and license |
| `PROFILE/master-cv.html` | Authoritative candidate CV |
| `PROFILE/` | Original source files and optional portrait |
| `APPLICATIONS/` | Role-specific sources, PDFs, and previews |
| `scripts/` | Setup, generation, rendering, and verification commands |
| `docs/` | Setup, workflow, privacy, and troubleshooting guides |

## Commands

Run `make help` for the short command list. The full command contract is in [the CLI reference](docs/REFERENCE.md).

## Customize and save templates

Each template is a named folder containing `cv.html` and `cover-letter.html`. Duplicate the included bundle to create another design:

```bash
cp -R BASE/TEMPLATES/default BASE/TEMPLATES/editorial
```

Edit either HTML file freely. Fonts, colors, spacing, layout, sections, decorative elements, and print styling are all customizable. Keep both documents printable as one A4 page with selectable text and use local or embedded assets so PDF generation remains reliable.

List saved templates with:

```bash
make templates
```

Template names use lowercase letters, digits, and hyphens. Add redistributable static font files and their licenses under `ASSETS/fonts/`, embed suitable font data, or use a system font stack.

## Documentation

- [First-time setup](docs/SETUP.md)
- [Application workflow](docs/WORKFLOW.md)
- [Privacy model and safe publishing](docs/PRIVACY.md)
- [Command reference](docs/REFERENCE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Agent operating rules](AGENTS.md)

## License

cvcannon is available under the [MIT License](LICENSE). Lexend is licensed separately under the SIL Open Font License 1.1; see [third-party notices](THIRD_PARTY_NOTICES.md).
