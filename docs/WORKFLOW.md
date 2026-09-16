# Application workflow

Provide one listing or a batch of listings. cvcannon creates one folder and one complete application pack per role. Each slug may contain lowercase letters, digits, and hyphens, for example `acme-platform-engineer`.

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

This command only scaffolds the application: it copies the authoritative CV, adds the cover letter template, and creates `job-description.md`. The agent performs the role analysis and document tailoring after scaffolding.

Optional: select another saved design for a role:

```bash
make new SLUG=acme-platform-engineer TEMPLATE=editorial
```

With `TEMPLATE`, the command copies that template's blank CV and cover letter shells. The agent then transfers relevant candidate facts from the master CV and tailors them for the listing.

## 3. Tailor the CV

Edit `APPLICATIONS/<slug>/cv.html`.

- Start from the copied master CV and preserve its document shell, A4 print rules, and local font paths.
- Replace every visible placeholder.
- Support every claim with `PROFILE/master-cv.html` or a direct clarification from the user.
- Select evidence relevant to the role and remove weak material before reducing font size.
- Keep dates, titles, credentials, metrics, and proficiency levels exact.
- Keep the professional profile distinct from the cover letter.
- Preserve the master CV's choice to include or omit a portrait unless the user requests a different version for that role.

## 4. Write the cover letter

Edit `APPLICATIONS/<slug>/cover-letter.html`.

- Replace the recipient, role, date, greeting, and contact placeholders.
- Replace every Lorem Ipsum paragraph.
- Connect selected evidence to the role's stated needs.
- Avoid repeating the CV profile sentence for sentence.
- Keep the letter to one A4 page.

## 5. Build and validate

```bash
make build SLUG=acme-platform-engineer
```

The command validates source HTML, prints both documents with headless Chromium, verifies the PDFs, and generates previews. Any failed gate stops the command with a specific error.

The application folder should then contain:

```text
APPLICATIONS/acme-platform-engineer/
├── cover-letter.html
├── cover-letter.pdf
├── cv.html
├── cv.pdf
├── job-description.md
└── previews/
    ├── cover-letter.png
    └── cv.png
```

## 6. Review manually

Open both preview PNGs and both PDFs. Check:

- no clipping, overlap, unexpected blank area, or second page;
- when present, the portrait is correctly cropped and not distorted;
- contact details remain on one line;
- dates align and do not collide with titles;
- links point to their intended destinations;
- spelling and organization names match the source facts;
- PDF text can be selected and copied; and
- the CV and letter address the target role without unsupported claims.

Run `make build` again after every content or CSS change.

## 7. Share only the final PDFs

Send `cv.pdf` and `cover-letter.pdf` through the intended application channel. Do not publish the application folder in this repository. If you want to publish the reusable pipeline, follow [the safe publishing checklist](PRIVACY.md#before-the-first-push).
