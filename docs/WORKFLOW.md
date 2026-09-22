# Application workflow

Provide one listing or a batch of listings. cvcannon creates one folder and one complete application pack per role. Each slug may contain lowercase letters, digits, and hyphens, for example `acme-platform-engineer`.

Every application follows the writing pipeline documented in [WRITING.md](WRITING.md). The scripts scaffold the intermediate artifacts, but the agent completes the analysis, the evidence map, and the writing. Do the stages in order: the analysis grounds both documents.

The examples below use native commands. With the optional Docker toolchain, add `docker-` to the target: `make docker-new`, `make docker-build`, and `make docker-check`. See [the Docker guide](DOCKER.md).

## 1. Provide the listings

Paste the full text of every listing whenever possible. Full text is preferred because it preserves the employer's exact wording, remains available after a listing expires, and avoids errors caused by dynamic or restricted pages.

Links are supported when listing text is unavailable. Retrieve the current listing, record its URL and retrieval date, and save the useful listing text in the generated `job-description.md`. Do not retrieve or reconstruct a listing when the user has already supplied its complete text.

Clearly separate listings in a batch. Each listing becomes an independent application and must be evaluated against the candidate profile on its own.

## 2. Create the application folders

```bash
make new SLUG=acme-platform-engineer
make new SLUG=example-data-analyst
```

Run the command once per listing. The command refuses to overwrite an existing folder and refuses to run until `PROFILE/master-cv.html` is complete.

This command scaffolds the application: it copies the authoritative CV, adds the cover letter template, and creates four Markdown artifacts:

```text
APPLICATIONS/acme-platform-engineer/
├── job-description.md      saved vacancy
├── job-analysis.md         structured role and company analysis
├── evidence-map.md         requirement-to-evidence grounding
├── application-notes.md    tailoring decisions, cover-letter plan, validation
├── cv.html
└── cover-letter.html
```

Each artifact starts with a `cvcannon:pending` marker. Fill it and remove the marker. `make build` refuses to run while a marker remains.

Optional: select another saved design for a role:

```bash
make new SLUG=acme-platform-engineer TEMPLATE=editorial
```

With `TEMPLATE`, the command copies that template's blank CV and cover letter shells. The agent then transfers relevant candidate facts from the master CV and tailors them for the listing.

## 3. Analyze the role and map evidence

Save the listing in `job-description.md`, then fill `job-analysis.md` with conclusions rather than a copy of the posting: primary responsibilities, employer priorities, required and preferred skills, the employer's terminology, company context, and the recipient.

Fill `evidence-map.md` before writing either document. Map each requirement to real evidence and mark the match honestly as `exact`, `adjacent`, or `gap`. The map is the grounding layer: every meaningful claim in the CV and cover letter traces to a row here.

## 4. Plan the tailoring

Record the strategy in `application-notes.md`: the target, how the summary and skills will change, which experience bullets are promoted, demoted, or reworded, and which requirements are covered or still gaps. Record the cover-letter plan at the same time: opening strategy, the strongest direct match, additional value or gap handling, the specific company detail to use, and the tone.

## 5. Tailor the CV

Edit `APPLICATIONS/<slug>/cv.html`.

- Start from the copied master CV and preserve its document shell, A4 print rules, and local font paths.
- Replace every visible placeholder.
- Support every claim with `PROFILE/master-cv.html` or a direct clarification from the user.
- Select evidence relevant to the role and remove weak material before reducing font size.
- Keep dates, titles, credentials, metrics, and proficiency levels exact.
- Keep the professional profile distinct from the cover letter.
- Preserve the master CV's choice to include or omit a portrait unless the user requests a different version for that role. When the master uses one, the `src` must match the supplied file (`portrait.webp`, `portrait.png`, `portrait.jpg`, or `portrait.jpeg`); `make new` sets it automatically.

Before moving on, run the CV validation checklist in [WRITING.md](WRITING.md#cv-validation).

## 6. Write the cover letter

Edit `APPLICATIONS/<slug>/cover-letter.html`.

- Replace the recipient, role, date, greeting, and contact placeholders.
- Replace every Lorem Ipsum paragraph.
- Connect selected evidence to the role's stated needs. Do not restate the CV.
- Use a supported opening strategy, not a generic "I am writing to apply".
- Keep the letter to roughly 250–400 words and one A4 page.
- Record the validation outcome in `application-notes.md`.

## 7. Build and validate

```bash
make build SLUG=acme-platform-engineer
```

The command rejects incomplete analysis artifacts, applies the writing checks, validates source HTML, prints both documents with headless Chromium, verifies the PDFs, and generates previews. Any failed gate stops the command with a specific error. Fix the reported problem in the document, then rebuild.

The application folder should then contain:

```text
APPLICATIONS/acme-platform-engineer/
├── application-notes.md
├── cover-letter.html
├── cover-letter.pdf
├── cv.html
├── cv.pdf
├── evidence-map.md
├── job-analysis.md
├── job-description.md
└── previews/
    ├── cover-letter.png
    └── cv.png
```

## 8. Review manually

Open both preview PNGs and both PDFs. Check:

- no clipping, overlap, unexpected blank area, or second page;
- when present, the portrait is correctly cropped and not distorted;
- contact details remain on one line;
- dates align and do not collide with titles;
- links point to their intended destinations;
- spelling and organization names match the source facts;
- PDF text can be selected and copied;
- the CV and letter address the target role without unsupported claims; and
- the cover letter adds reasoning the CV does not contain.

Run `make build` again after every content or CSS change.

## 9. Share only the final PDFs

Send `cv.pdf` and `cover-letter.pdf` through the intended application channel. Do not publish the application folder in this repository. If you want to publish the reusable pipeline, follow [the safe publishing checklist](PRIVACY.md#before-the-first-push).
