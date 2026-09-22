# AGENTS.md — cvcannon rules

## What cvcannon is

cvcannon is an agent-operated batch production system for job applications. A user provides one or many job listings in a single request. For every listing, the agent produces a separate application pack containing:

- the saved job listing;
- a one-page A4 CV tailored to that role;
- a matching one-page cover letter;
- ATS-readable PDFs with selectable text; and
- PNG previews for visual review.

The user should be able to provide a batch, leave the organization and production work to the agent, and receive finished packs grouped by company and role.

cvcannon is provider agnostic and follows a bring-your-own-harness model. It does not assume Codex, Claude Code, OpenCode, or any other specific agent runtime. Any capable harness may operate the repository by reading this file, editing the HTML sources, and invoking the documented Make targets. Docker contains the deterministic document toolchain only; it does not contain or select the user's agent.

The harness is expected to run with the repository root as its working directory. In Docker mode, continue reading and editing files from that host checkout. `make docker-*` targets mount the checkout at `/workspace` in a disposable container, run one mechanical command, and write outputs back through the bind mount. Do not expect a resident service or agent inside the container.

The first session establishes one complete, authoritative HTML CV at `PROFILE/master-cv.html`. It can be created from an existing CV, arbitrary source documents, or information pasted in chat. Later sessions reuse this master without repeating profile setup. Each application starts as a copy of the master, then changes only inside its own `APPLICATIONS/<slug>/` folder.

## Agent and script responsibilities

The agent performs the judgment-heavy work:

- interpret source CVs and user-provided career information;
- retrieve listings when the user supplies links;
- separate and organize batches of listings;
- identify responsibilities, required skills, preferred skills, keywords, and employer priorities;
- record a structured job analysis and a requirement-to-evidence map before writing;
- select, reorder, and rewrite supported evidence for each role;
- write a role-specific profile and cover letter;
- record tailoring decisions and validation results in the application notes;
- keep claims factual and dates, titles, credentials, metrics, and proficiency levels exact;
- inspect the generated previews and correct layout problems; and
- present completed outputs grouped by role.

The repository scripts perform repeatable mechanical work:

- `make templates` lists saved template bundles;
- `make profile TEMPLATE=<name>` creates the initial master CV shell from a selected template;
- `make new SLUG=<company-role>` scaffolds an application from the master CV and creates the job analysis, evidence map, and application notes;
- `make new SLUG=<company-role> TEMPLATE=<name>` scaffolds an application with another saved design;
- `make build SLUG=<company-role>` renders and verifies both PDFs, rejects incomplete analysis artifacts, and applies the writing checks;
- `make check SLUG=<company-role>` rechecks PDFs and refreshes previews;
- `make build-all`, `make check-all`, and `make clean-all` apply those commands to every application, reporting failures per application; and
- `make privacy` checks files that could enter Git.

When the user chooses Docker, use the corresponding `docker-` target, such as `make docker-new SLUG=<company-role>` or `make docker-build SLUG=<company-role>`. These commands produce the same files and apply the same checks through the containerized toolchain.

The scripts do not interpret job listings, choose evidence, or write tailored content. The agent must complete those steps after scaffolding. The scripts scaffold the analysis artifacts, reject them while they are still empty, and enforce a short list of banned writing patterns; they never generate prose.

## First-time execution setup

At the beginning of work, check `.cvcannon/mode`.

If the file is missing, ask the user one short question before running setup: whether they want the Docker toolchain or tools installed natively. Explain that Docker standardizes Python, Chromium, Poppler, and fonts; native mode uses installations already available on their machine. Do not choose on the user's behalf.

After the user answers:

1. Run `bash scripts/mode.sh docker` or `bash scripts/mode.sh native` to save the choice locally.
2. For Docker, run `bash docker-setup.sh` yourself. Do not tell the user to launch it.
3. For native mode, inspect the prerequisites and guide any required system installation, then run the native commands yourself. Run `make setup` after the authoritative CV has been completed because its doctor validates that file.
4. Use the selected command family for later work: `make docker-*` for Docker or the ordinary `make` targets for native mode.

The saved mode is a local preference and is ignored by Git. If the user asks to switch modes, update it with `scripts/mode.sh` and run the selected setup. Never require the user to launch repository scripts manually; invoke them through the harness.

## Sources of truth

Use these sources in this order:

1. Direct corrections and facts supplied by the user.
2. `PROFILE/master-cv.html` for established candidate facts and the baseline document.
3. Source documents under `PROFILE/` when building or correcting the master CV.
4. The saved job listing for role requirements, vocabulary, company details, and recipient information.

When the user supplies a lasting factual correction, update the master CV before using it. Keep role-specific emphasis and wording in the application copy.

Tracked files must remain free of personally identifiable information (PII). Completed candidate profiles and generated applications belong in ignored paths.

## First-time profile setup

Before creating an application, check for `PROFILE/master-cv.html`.

If it is missing, ask the user for any one of the following:

- an existing CV uploaded or placed anywhere under `PROFILE/`;
- a PDF, DOCX, HTML, Markdown, or text file containing career information; or
- career and contact information pasted directly into chat.

After receiving source material:

1. Choose a saved template with the user when they express a design preference; otherwise use `default`.
2. Run `make profile TEMPLATE=<name>` to create the master shell.
3. Transfer only supported facts into `PROFILE/master-cv.html`, using the source material and user clarifications.
4. Remove unused sections and all placeholders.
5. Handle the portrait (see the portrait rule below).
6. Run `make doctor` and correct every reported issue.

## Portrait rule

A portrait is optional. Supported files are `PROFILE/portrait.webp`, `PROFILE/portrait.png`, and `PROFILE/portrait.jpg` (or `.jpeg`). Prefer WebP: it renders the same and keeps the finished PDF smaller. When the user supplies PNG or JPEG, tell them WebP shrinks the file and offer `make portrait-convert` to convert it in place.

- If a portrait file exists and the user wants a photo, keep the portrait `<img>` in the master CV with its `src` set to that filename. `make profile` and `make new` set the correct path automatically.
- If the user does not want a photo, the master CV is photo-free; remove the portrait `<img>`.
- If no portrait is present and no preference is saved, ask the user whether they intended one before continuing. If yes, ask them to add `PROFILE/portrait.webp` (preferred), `PROFILE/portrait.png`, `PROFILE/portrait.jpg`, or `PROFILE/portrait.jpeg`, then save the choice with `bash scripts/portrait.sh wanted`. If no, save it with `bash scripts/portrait.sh none` and take no further action.
- The saved preference lives in `.cvcannon/portrait` and is ignored by Git. Do not ask again once it is saved. If the user changes their mind, update the file and the master CV.

Do not force the user into a schema, require them to rewrite an existing CV, or invent missing details. Never force-add files under `PROFILE/` to Git.

## Repository structure

- `BASE/TEMPLATES/<name>/` — named template bundles containing `cv.html` and `cover-letter.html`.
- `ASSETS/` — Lexend and Liberation Serif font files and their licenses.
- `PROFILE/master-cv.html` — authoritative candidate CV used as the base for every application.
- `PROFILE/` — source files and an optional `portrait.webp`, `portrait.png`, `portrait.jpg`, or `portrait.jpeg` used to create the master CV.
- `APPLICATIONS/<slug>/` — ignored role-specific analysis, HTML, PDF, and preview outputs.
- `scripts/` — setup, scaffolding, rendering, verification, and privacy checks.
- `docs/` — workflow, privacy, and troubleshooting documentation.

## Application writing pipeline

Both documents are generated from one factual model. Do not treat CV tailoring and
cover-letter writing as independent creative prompts.

```text
job listing -> structured job analysis -> candidate evidence matching -> tailoring strategy
-> tailored CV -> CV validation -> cover-letter argument selection -> company/context research
-> cover letter -> final factual and style validation -> saved application pack
```

Read `docs/WRITING.md` for the complete rules. The non-negotiables:

- `PROFILE/master-cv.html` is the source of truth. Never modify the master for a single
  job; generate each application-specific version from it.
- Tailoring selects, reorders, emphasises, and accurately reframes real experience. It
  never manufactures a better candidate.
- Every meaningful claim in either document traces through the evidence map to the master
  CV, documented project history, or a fact the user confirmed.
- Acceptable: reordering true information, using accurate industry terminology, phrasing
  vague accomplishments more clearly, selecting different verified bullets, and
  translating genuinely equivalent concepts into the employer's vocabulary.
- Unacceptable: adding skills, altering metrics, inventing achievements or
  responsibilities, claiming titles or credentials never held, converting adjacent
  experience into direct experience, or implying unsupported proficiency. This rule has
  priority over ATS optimisation.
- Preserve the candidate's established positioning. Do not relabel automation,
  infrastructure, integration, troubleshooting, or systems-operations work as software
  engineering merely because a listing mentions programming.
- Write bullets as action + system or problem + context + result when the evidence
  supports it, without inventing metrics.
- Apply the shared anti-AI style pass to both documents. `make build` rejects banned
  buzzwords and cover-letter clichés and warns on softer judgment words.

## Application workflow

1. Accept one or more job listings in the same request. Prefer complete pasted text. Accept listing URLs when text is unavailable and retrieve the current listing before writing.
2. Identify each distinct role and create a lowercase, hyphenated `<company-role>` slug.
3. Run `make new SLUG=<company-role>` for every listing. Add `TEMPLATE=<name>` when the user requests a saved design other than the master CV's design. Multiple applications should be created concurrently when possible.
4. Save the supplied or retrieved listing text in that application's `job-description.md` and remove the pending marker.
5. Read `PROFILE/master-cv.html` as the authoritative candidate source, then fill `job-analysis.md`: primary responsibilities, employer priorities, required and preferred skills, employer terminology, and company context.
6. Fill `evidence-map.md` before writing: map each requirement to matching evidence, its source, an exact/adjacent/gap match, the terminology to use, and whether it belongs in the CV or the cover letter.
7. Record the tailoring strategy and cover-letter plan in `application-notes.md`.
8. Edit only `APPLICATIONS/<slug>/cv.html`, `cover-letter.html`, and the markdown artifacts for the assigned role. Tailor the CV from the evidence map, then select a small number of the strongest connections for the letter.
9. Keep every claim supported by the master CV or new facts directly confirmed by the user. Add lasting factual corrections to the master CV before using them in applications.
10. When the master includes a portrait, application copies must use `../../PROFILE/portrait.<ext>` matching the supplied file (`webp`, `png`, or `jpg`). Photo-free master CVs remain photo-free.
11. Follow the layout and writing rules in the template comments and `docs/WRITING.md`. Each document must fit on one A4 page and retain selectable text.
12. Run `make build SLUG=<company-role>` for every application. It rejects incomplete analysis artifacts, applies the writing checks, renders both PDFs, and verifies them. Correct any reported writing problem in the document itself, not only in the report.
13. Record the validation outcome and final status in `application-notes.md`, then present results grouped by role. Do not claim completion unless every requested pack contains both verified PDFs.

## Privacy and Git rules

- Never commit source documents, `master-cv.html`, or any `portrait.*` from `PROFILE/`; only its existing README may be tracked.
- Never commit anything under `APPLICATIONS/` except its tracked `README.md` and `.gitkeep`.
- Never put a real name, email, phone number, address, portrait, employment history, job description, application HTML, or generated PDF in tracked files.
- Run `make privacy` before every commit. The installed pre-commit hook runs the same check.
- Do not add a Git remote, publish, or push without the user's explicit confirmation.
- If private data is accidentally staged, unstage it and move it to an ignored path. If it was committed, stop and follow `docs/PRIVACY.md` before publishing.

## Template rules

Template customization is an intended agent capability. The included `default` bundle is an editable starting point rather than a locked design.

- A saved template is `BASE/TEMPLATES/<name>/cv.html` plus `cover-letter.html`.
- Create another template by copying an existing bundle to a lowercase, hyphenated name, then edit the copies.
- The agent may change fonts, type scale, colors, spacing, borders, icons, section order, section selection, page composition, and other visual details when requested or when creating a reusable design.
- Keep the CV and cover letter visually related within a bundle.
- Fonts may be changed freely. Store redistributable static font files and their licenses under `ASSETS/fonts/`, embed suitable font data, or use a system font stack.
- Keep templates free of candidate and company data. Use placeholders and example domains.
- Use local or embedded resources. Do not add CDN fonts, scripts, analytics, or remote images.
- Preserve the output contract: one A4 page per document, selectable ATS-readable text, working links, and successful `make build` verification.
- Keep relative asset paths correct for the template bundle, master CV, and application copy. The scaffolding command adjusts paths for the bundled structure.
- Prefer editing content and spacing before reducing type. Never reduce body text below 7pt.
- `PROFILE/master-cv.html` governs candidate facts. Keep job-specific wording in `APPLICATIONS/<slug>/` unless it is a lasting factual correction.

## Parallel work

Use subagents when it speeds up a task. When producing several applications, assign one application to each subagent. Each subagent must follow this file and write only inside its assigned `APPLICATIONS/<slug>/` folder.
