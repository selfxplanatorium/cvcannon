# Docker workflow

Docker is an optional execution environment for cvcannon's deterministic tools. It supplies Python, GNU Make, Git, Chromium, Poppler, `cwebp` for portrait conversion, and compatible system fonts in one image. The native workflow remains available and produces the same repository layout.

## Bring your own harness

The container is not an agent harness and contains no AI provider SDK, account, or API credential. Run Codex, Claude Code, OpenCode, or another agent in the repository as usual. The agent reads `AGENTS.md`, edits the mounted files, and invokes the Docker-backed Make targets when it needs to scaffold, render, or validate documents.

This division keeps cvcannon provider agnostic:

1. your chosen harness performs role analysis, writing, and template edits;
2. the bind-mounted repository stores the profile and application files; and
3. the container performs repeatable rendering and technical checks.

## How the host agent uses Docker

Start your chosen agent in the repository root, the same way you would for the native workflow. The agent finds `AGENTS.md` in that working directory and reads and edits the checkout directly.

When the agent runs a Docker target, the call flows like this:

```text
agent in the host repository
  -> make docker-build SLUG=acme-platform-engineer
  -> scripts/docker.sh
  -> docker compose run --rm cvcannon ...
  -> repository mounted at /workspace
  -> generated files written into the host checkout
  -> container exits
```

The container is a disposable command runner. There is no persistent application inside it, no agent protocol, and no file synchronization step. The bind mount means that `PROFILE/master-cv.html` seen by the host agent is the same file available as `/workspace/PROFILE/master-cv.html` to the container. PDFs written by Chromium inside the container immediately appear under the host's `APPLICATIONS/` folder.

For a typical session:

1. change into the cvcannon repository on the host;
2. launch the preferred agent there;
3. give the agent the listings or links;
4. the agent reads `AGENTS.md`, edits the profile and application HTML, and runs `make docker-*` targets; and
5. review the resulting host files normally.

An agent harness that supports dev containers may itself be launched inside a configured container, but cvcannon does not require or manage that mode. The documented setup keeps the harness on the host and containerizes only the reproducible toolchain.

## Requirements

Install one of:

- Docker Desktop with Docker Compose; or
- Docker Engine with the Compose plugin.

Confirm that both commands work:

```bash
docker info
docker compose version
```

## One-command setup

On the first session, the agent asks whether to use Docker or native tools. When Docker is selected, the agent saves that preference and runs this command from the repository root:

```bash
./docker-setup.sh
```

The script:

1. verifies the Docker CLI, Compose plugin, and running daemon;
2. builds `cvcannon:local` from the included `Dockerfile`;
3. configures the repository's committed pre-commit hook;
4. maps container writes to the current host user and group;
5. lists the available templates and runs the privacy scan; and
6. runs the full doctor when an authoritative CV already exists.

This is an implementation command for the agent. The normal user flow is to open the harness in the repository and answer its setup question; the user does not need to launch the script.

No candidate data is copied into the image. `PROFILE/` and `APPLICATIONS/` are excluded from the build context by `.dockerignore` and mounted only at runtime.

## First use

Place an existing CV or career notes under `PROFILE/`, or provide the information to your agent in chat. Then create the master shell:

```bash
make docker-profile
```

To use another saved template:

```bash
make docker-profile TEMPLATE=editorial
```

Ask the agent to transfer supported facts into `PROFILE/master-cv.html`, remove unused sections and placeholders, and remove the portrait element when no portrait is wanted. A portrait may be `portrait.webp` (preferred), `portrait.png`, or `portrait.jpg`; convert a PNG or JPEG to WebP inside the container with `make docker-portrait-convert`. Then run:

```bash
make docker-doctor
```

## Applications

Create, tailor, and build each application with:

```bash
make docker-new SLUG=acme-platform-engineer
make docker-build SLUG=acme-platform-engineer
```

The repository is bind-mounted at `/workspace`, so generated PDFs and previews appear directly under `APPLICATIONS/<slug>/` on the host. The wrapper uses the host user and group IDs to prevent root-owned outputs on Linux.

## Command map

| Task | Docker command |
| --- | --- |
| Guided setup | `./docker-setup.sh` or `make docker-setup` |
| Rebuild the image | `make docker-image` |
| List templates | `make docker-templates` |
| Create master CV | `make docker-profile [TEMPLATE=name]` |
| Check the environment and master CV | `make docker-doctor` |
| Convert the portrait to WebP | `make docker-portrait-convert` |
| Create an application | `make docker-new SLUG=<slug> [TEMPLATE=name]` |
| Render and verify PDFs | `make docker-build SLUG=<slug>` |
| Recheck PDFs and previews | `make docker-check SLUG=<slug>` |
| Run the Git privacy scan | `make docker-privacy` |
| Remove generated files for one role | `make docker-clean SLUG=<slug>` |

The generic wrapper can run another command in the same container:

```bash
scripts/docker.sh make help
scripts/docker.sh python3 --version
```

## How it works

- `Dockerfile` pins the operating-system family and installs the complete rendering toolchain.
- `compose.yaml` mounts the current checkout, sets the working directory, maps the host user, and gives Chromium sufficient shared memory.
- The Compose environment marks Chromium as containerized so it uses Docker isolation instead of attempting to create a nested browser sandbox.
- `scripts/docker.sh` validates Docker and runs a single disposable container.
- `docker-setup.sh` builds the image and prepares a new clone.
- `.dockerignore` keeps Git metadata, candidate sources, applications, and generated documents out of the image build context.

Containers are disposable. The repository is the persistent state, so native and Docker commands can be mixed when their tool versions produce acceptable output.

## Updating the image

After changing `Dockerfile` or upgrading the repository, rebuild with:

```bash
make docker-image
```

To discard the local image manually:

```bash
docker image rm cvcannon:local
```

The next `./docker-setup.sh` or `make docker-image` recreates it.
