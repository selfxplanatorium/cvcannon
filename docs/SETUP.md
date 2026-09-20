# First-time setup

Run all commands from the project root.

cvcannon supports two setup paths. Docker provides the shortest reproducible setup. Native setup uses tools installed directly on the host. Both paths produce the same files and use the same checks.

## Agent-led first run

Launch the preferred agent harness from the repository root. The agent checks `.cvcannon/mode`. On a new clone it asks whether to use Docker or native tools, saves the answer locally, and performs the setup commands itself. The user supplies the preference and any required candidate material; the agent operates the scripts.

The choice is stored only in `.cvcannon/mode`, which Git ignores. Tell the agent if you want to switch later.

## Docker setup

Install a current Docker Desktop, or Docker Engine with the Docker Compose plugin. The agent then runs:

```bash
./docker-setup.sh
```

The user is not expected to launch this script manually. The script verifies Docker, builds the image, configures the committed Git hook, lists the available templates, and runs the privacy check. If `PROFILE/master-cv.html` already exists, it also runs the full environment doctor. Otherwise it reports the profile creation steps to the agent.

Continue with Docker-prefixed targets such as `make docker-profile`, `make docker-new`, and `make docker-build`. The full workflow and command mapping are in [DOCKER.md](DOCKER.md).

## Native setup

The pipeline uses Python's standard library. PDF rendering and inspection require a Chromium-family browser and Poppler. Converting a portrait to WebP with `make portrait-convert` additionally requires `cwebp` from the `webp` package; it is optional and only needed for that command. The Docker image already includes it.

### Debian and Ubuntu

```bash
sudo apt update
sudo apt install git make python3 chromium poppler-utils webp
```

Some Ubuntu releases package Chromium as a Snap. That build may restrict access to files outside its allowed paths. Keep the repository under your home directory or install Google Chrome if local assets fail to load.

### Fedora

```bash
sudo dnf install git make python3 chromium poppler-utils libwebp-tools
```

### Arch Linux

```bash
sudo pacman -S git make python chromium poppler libwebp
```

### macOS

Install Google Chrome from its official installer, then install the command-line dependencies with Homebrew:

```bash
brew install git make python poppler webp
```

The pipeline recognizes Google Chrome in its standard `/Applications` location.

### Windows

Use WSL 2 with a Linux browser available inside WSL. Native Windows command paths are not currently supported by `scripts/cv.py`.

## Provide candidate information

Use one or more sources that already exist:

- an existing CV in PDF, DOCX, HTML, or another readable document format;
- a Markdown or plain-text file containing career information; or
- information pasted directly into the conversation with the agent.

Place source files anywhere under `PROFILE/`. Their filenames do not matter.

## Create the authoritative CV

List the available designs:

```bash
make templates
```

Run:

```bash
make profile
```

The command uses the `default` template. Select another saved template with `make profile TEMPLATE=<name>`.

Use the supplied information to complete `PROFILE/master-cv.html`. Remove sections that do not apply and resolve every placeholder. This file becomes the baseline for all future applications.

Optional: save a portrait as `PROFILE/portrait.webp` (preferred), `PROFILE/portrait.png`, or `PROFILE/portrait.jpg`. Use a real image file, ideally square or portrait-oriented and at least 400 pixels wide. WebP is preferred because it keeps the finished PDF smaller; if you supply PNG or JPEG, run `make portrait-convert` (it needs `cwebp` from the `webp` package, or the Docker toolchain) and then point the master CV's portrait `src` at `portrait.webp`. Keep the portrait element in the master CV when using it; otherwise remove the element.

If no portrait is present, the agent asks whether you intended one and records the answer in `.cvcannon/portrait`, so it does not ask again. Supply the file when you want a photo; no action is required when you do not.

## Configure the clone

Run:

```bash
make setup
```

This command:

1. creates a local Git repository on branch `main` if one does not exist;
2. sets `core.hooksPath` to `.githooks`;
3. marks the scripts executable; and
4. runs the environment doctor.

It does not add a remote, create a commit, upload files, or contact GitHub.

Successful output names the detected browser and reports the authoritative CV path.

## Check Git exclusions

Run:

```bash
make privacy
git status --short
```

Source files, `PROFILE/master-cv.html`, any `PROFILE/portrait.*`, and application content must not appear in `git status`. If they do, follow [the privacy guide](PRIVACY.md).

## Next step

Continue with the [application workflow](WORKFLOW.md).
