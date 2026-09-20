# Command reference

Run commands from the project root.

Every document command has a Docker equivalent. See [Docker commands](#docker-commands) or the [Docker guide](DOCKER.md).

## `bash scripts/mode.sh [docker|native]`

With no argument, prints the locally selected execution mode. With `docker` or `native`, saves that mode under the ignored `.cvcannon/` directory. The agent uses this during first-time setup; users do not need to invoke it themselves.

## `bash scripts/portrait.sh [wanted|none]`

With no argument, prints the saved portrait preference. With `wanted` or `none`, records whether the user intends to include a photo, under the ignored `.cvcannon/` directory. The agent uses this so it asks about a missing portrait only once; users do not need to invoke it themselves.

## `make setup`

Configures Git hooks, sets executable bits, and runs `doctor`. It initializes a Git repository when needed.

## `make profile`

Creates `PROFILE/master-cv.html` from the `default` CV template and adjusts resource paths for its location. It points the portrait `src` at whichever `portrait.webp`, `portrait.png`, or `portrait.jpg` exists, and removes the portrait element when none is present. It refuses to overwrite an existing master. Complete the file from an existing CV, supplied documents, or information provided in chat.

Use `make profile TEMPLATE=<name>` to select another saved template.

## `make templates`

Lists complete template bundles found under `BASE/TEMPLATES/`. Each bundle must contain `cv.html` and `cover-letter.html`.

## `make doctor`

Checks for a supported browser, all required Poppler commands, templates, static fonts, and a complete authoritative CV. It accepts `PROFILE/portrait.webp`, `PROFILE/portrait.png`, or `PROFILE/portrait.jpg`, prefers WebP, and notes when the saved portrait preference should be confirmed. A nonzero exit identifies each missing requirement.

## `make portrait-convert`

Converts the portrait in `PROFILE/` to WebP, which renders the same and keeps the finished PDF smaller. It requires `cwebp` from the `webp` package. If the portrait is already WebP, the command reports that and does nothing. After conversion, point the CV portrait `src` at `portrait.webp` and remove the original if unused.

## `make new SLUG=<slug>`

Copies `PROFILE/master-cv.html` into `APPLICATIONS/<slug>/cv.html`, adjusts its relative asset paths, copies the generic cover letter template, and scaffolds `job-description.md`, `job-analysis.md`, `evidence-map.md`, and `application-notes.md`. Each artifact carries a `cvcannon:pending` marker until the agent completes it. The command does not analyze or tailor content. The slug must match `[a-z0-9][a-z0-9-]*`. Existing folders are never overwritten.

Use `make new SLUG=<slug> TEMPLATE=<name>` to scaffold both documents from another saved bundle. The resulting CV is a blank template that the agent must populate from the authoritative CV.

The writing stages that fill these artifacts are documented in [WRITING.md](WRITING.md).

## `make build SLUG=<slug>`

Runs `doctor`, rejects incomplete analysis artifacts, applies the writing checks to both documents, checks source HTML, renders `cv.pdf` and `cover-letter.pdf`, runs all PDF checks, and creates preview PNGs. The command exits nonzero on the first failed gate.

## `make check SLUG=<slug>`

Verifies existing PDFs and refreshes previews without rendering the HTML again. It also re-runs the analysis-artifact and writing checks.

## `make clean SLUG=<slug>`

Deletes only the generated PDFs and `previews/` directory for one application. Source HTML and the saved job description remain.

## `make privacy`

Scans files eligible for commit. The pre-commit hook uses `python3 scripts/privacy_check.py --staged` to inspect staged content instead.

## Docker commands

`make docker-setup` runs the guided first-time Docker setup. `make docker-image` rebuilds the image without running setup checks.

The remaining targets mirror the native commands:

| Docker target | Equivalent native target |
| --- | --- |
| `make docker-templates` | `make templates` |
| `make docker-profile [TEMPLATE=name]` | `make profile [TEMPLATE=name]` |
| `make docker-doctor` | `make doctor` |
| `make docker-portrait-convert` | `make portrait-convert` |
| `make docker-new SLUG=<slug> [TEMPLATE=name]` | `make new ...` |
| `make docker-build SLUG=<slug>` | `make build ...` |
| `make docker-check SLUG=<slug>` | `make check ...` |
| `make docker-privacy` | `make privacy` |
| `make docker-clean SLUG=<slug>` | `make clean ...` |

For an uncommon command, run it through the wrapper directly:

```bash
scripts/docker.sh make help
```

## Outputs and exit status

All commands exit with status `0` on success and a nonzero status on failure. Errors begin with `ERROR:` and state the failed requirement.
