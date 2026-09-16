# Command reference

Run commands from the project root.

## `make setup`

Configures Git hooks, sets executable bits, and runs `doctor`. It initializes a Git repository when needed.

## `make profile`

Creates `PROFILE/master-cv.html` from the `default` CV template and adjusts resource paths for its location. It refuses to overwrite an existing master. Complete the file from an existing CV, supplied documents, or information provided in chat.

Use `make profile TEMPLATE=<name>` to select another saved template.

## `make templates`

Lists complete template bundles found under `BASE/TEMPLATES/`. Each bundle must contain `cv.html` and `cover-letter.html`.

## `make doctor`

Checks for a supported browser, all required Poppler commands, templates, static fonts, and a complete authoritative CV. A nonzero exit identifies each missing requirement.

## `make new SLUG=<slug>`

Copies `PROFILE/master-cv.html` into `APPLICATIONS/<slug>/cv.html`, adjusts its relative asset paths, copies the generic cover letter template, and creates an empty `job-description.md`. It does not analyze or tailor content. The slug must match `[a-z0-9][a-z0-9-]*`. Existing folders are never overwritten.

Use `make new SLUG=<slug> TEMPLATE=<name>` to scaffold both documents from another saved bundle. The resulting CV is a blank template that the agent must populate from the authoritative CV.

## `make build SLUG=<slug>`

Runs `doctor`, checks source HTML, renders `cv.pdf` and `cover-letter.pdf`, runs all PDF checks, and creates preview PNGs. The command exits nonzero on the first failed gate.

## `make check SLUG=<slug>`

Verifies existing PDFs and refreshes previews without rendering the HTML again.

## `make clean SLUG=<slug>`

Deletes only the generated PDFs and `previews/` directory for one application. Source HTML and the saved job description remain.

## `make privacy`

Scans files eligible for commit. The pre-commit hook uses `python3 scripts/privacy_check.py --staged` to inspect staged content instead.

## Outputs and exit status

All commands exit with status `0` on success and a nonzero status on failure. Errors begin with `ERROR:` and state the failed requirement.
