# Command reference

Run commands from the project root.

Every `make` target is also available as `python3 scripts/cv.py <target> [SLUG=...] [TEMPLATE=...]`. On Windows, `cvcannon.cmd` replaces `make` with the same arguments, for example `cvcannon.cmd new SLUG=acme-role TEMPLATE=editorial`. It installs Python first when none is available.

## `cvcannon.cmd install [docker]` (Windows)

Installs the native toolchain for the current user without administrator rights or prompts: Python from python.org, then Git (MinGit), Poppler, and `cwebp` into `%LOCALAPPDATA%\cvcannon\tools`, each added to the user `PATH`. Downloads a portable headless Chrome only when no Edge, Chrome, or Chromium is installed. Existing tools are kept, so rerunning it is fast. With `docker`, it installs only Python and Git and fails with instructions when Docker Desktop is missing. It ends by running `tools`.

## `make tools`

Lists the path of every required program (Python, Git, browser, and Poppler commands) and the optional `cwebp`. Exits nonzero when a required program is missing. Unlike `doctor`, it does not need the authoritative CV.

Every document command has a Docker equivalent. See [Docker commands](#docker-commands) or the [Docker guide](DOCKER.md).

## `python3 scripts/cv.py mode [docker|native]`

`bash scripts/mode.sh` is an equivalent shortcut on Linux and macOS. With no argument, prints the locally selected execution mode. With `docker` or `native`, saves that mode under the ignored `.cvcannon/` directory. The agent uses this during first-time setup; users do not need to invoke it themselves.

## `python3 scripts/cv.py portrait [wanted|none]`

`bash scripts/portrait.sh` is an equivalent shortcut on Linux and macOS. With no argument, prints the saved portrait preference. With `wanted` or `none`, records whether the user intends to include a photo, under the ignored `.cvcannon/` directory. The agent uses this so it asks about a missing portrait only once; users do not need to invoke it themselves.

## `make setup`

Configures Git hooks, sets executable bits on Linux and macOS, and runs `doctor`. It initializes a Git repository when needed.

## `make profile`

Creates `PROFILE/master-cv.html` from the `default` CV template and adjusts resource paths for its location. It points the portrait `src` at whichever `portrait.webp`, `portrait.png`, `portrait.jpg`, or `portrait.jpeg` exists, and removes the portrait element when none is present. It also removes the portrait element from a scaffolded application when no portrait file exists, so photo-free profiles stay photo-free with any template. It refuses to overwrite an existing master. Complete the file from an existing CV, supplied documents, or information provided in chat.

Use `make profile TEMPLATE=<name>` to select another saved template.

## `make templates`

Lists complete template bundles found under `BASE/TEMPLATES/`. Each bundle must contain `cv.html` and `cover-letter.html`.

## `make doctor`

Checks for a supported browser (Chromium, Google Chrome, or Microsoft Edge on Windows, or the executable in `CVCANNON_BROWSER`), all required Poppler commands, templates, static fonts, and a complete authoritative CV. It accepts `PROFILE/portrait.webp`, `PROFILE/portrait.png`, `PROFILE/portrait.jpg`, or `PROFILE/portrait.jpeg`, prefers WebP, and notes when the saved portrait preference should be confirmed. A nonzero exit identifies each missing requirement.

## `make portrait-convert`

Converts the portrait in `PROFILE/` to WebP, which renders the same and keeps the finished PDF smaller. It requires `cwebp` from the `webp` package, which `cvcannon.cmd install` provides on Windows. If the portrait is already WebP, the command reports that and does nothing. After conversion, point the CV portrait `src` at `portrait.webp` and remove the original if unused.

## `make new SLUG=<slug>`

Copies `PROFILE/master-cv.html` into `APPLICATIONS/<slug>/cv.html`, adjusts its relative asset paths, copies the cover letter from the selected template bundle (the master's template, or the `TEMPLATE` override), and scaffolds `job-description.md`, `job-analysis.md`, `evidence-map.md`, and `application-notes.md`. Each artifact carries a `cvcannon:pending` marker until the agent completes it. The command does not analyze or tailor content. The slug must match `[a-z0-9][a-z0-9-]*`. Existing folders are never overwritten.

Use `make new SLUG=<slug> TEMPLATE=<name>` to scaffold both documents from another saved bundle. The resulting CV is a blank template that the agent must populate from the authoritative CV.

The writing stages that fill these artifacts are documented in [WRITING.md](WRITING.md).

## `make build SLUG=<slug>`

Runs `doctor`, rejects incomplete analysis artifacts, applies the writing checks to both documents, checks source HTML, renders `cv.pdf` and `cover-letter.pdf`, runs all PDF checks, and creates preview PNGs. The command exits nonzero on the first failed gate.

## `make check SLUG=<slug>`

Verifies existing PDFs and refreshes previews without rendering the HTML again. It also re-runs the analysis-artifact and writing checks.

## `make clean SLUG=<slug>`

Deletes only the generated PDFs and `previews/` directory for one application. Source HTML and the saved job description remain.

## `make build-all`, `make check-all`, `make clean-all`

Apply `build`, `check`, or `clean` to every complete application under `APPLICATIONS/`. Each application is processed independently; a failure in one does not stop the others. The command exits nonzero and names every application that failed. They fail immediately when no applications exist.

## `make privacy`

Scans files eligible for commit. The pre-commit hook runs `scripts/privacy_check.py --staged` to inspect staged content instead. It uses the first working `python3`, `python`, or `py -3`, so it also runs under Git for Windows.

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
| `make docker-build-all` | `make build-all` |
| `make docker-check-all` | `make check-all` |
| `make docker-privacy` | `make privacy` |
| `make docker-clean SLUG=<slug>` | `make clean ...` |
| `make docker-clean-all` | `make clean-all` |

For an uncommon command, run it through the wrapper directly:

```bash
python3 scripts/cv.py docker make help
```

`scripts/docker.sh make help` is an equivalent shortcut on Linux and macOS. On Windows, use `cvcannon.cmd docker make help`.

## Outputs and exit status

Commands exit with status `0` on success and a nonzero status on failure. Errors begin with `ERROR:` and state the failed requirement. An exception: `mode` and `portrait` exit `1` when queried with no argument and no saved value, which is a normal "unset" result rather than an error.
