# First-time setup

Run all commands from the project root.

## Prerequisites

The pipeline uses Python's standard library. PDF rendering and inspection require a Chromium-family browser and Poppler.

### Debian and Ubuntu

```bash
sudo apt update
sudo apt install git make python3 chromium poppler-utils
```

Some Ubuntu releases package Chromium as a Snap. That build may restrict access to files outside its allowed paths. Keep the repository under your home directory or install Google Chrome if local assets fail to load.

### Fedora

```bash
sudo dnf install git make python3 chromium poppler-utils
```

### Arch Linux

```bash
sudo pacman -S git make python chromium poppler
```

### macOS

Install Google Chrome from its official installer, then install the command-line dependencies with Homebrew:

```bash
brew install git make python poppler
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

Optional: save a portrait as `PROFILE/portrait.png`. Use a real PNG, ideally square or portrait-oriented and at least 400 pixels wide. Keep the portrait element in the master CV when using it; otherwise remove the element.

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

Source files, `PROFILE/master-cv.html`, `PROFILE/portrait.png`, and application content must not appear in `git status`. If they do, follow [the privacy guide](PRIVACY.md).

## Next step

Continue with the [application workflow](WORKFLOW.md).
