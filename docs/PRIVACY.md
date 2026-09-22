# Privacy and safe publishing

## Public and private boundaries

The public repository contains generic templates, scripts, documentation, and licensed fonts. These local paths contain personal or sensitive material and are ignored:

- source files under `PROFILE/`
- `PROFILE/master-cv.html`
- `PROFILE/portrait.webp`, `PROFILE/portrait.png`, `PROFILE/portrait.jpg`, or `PROFILE/portrait.jpeg`, when used
- everything generated under `APPLICATIONS/<slug>/`

Application folders may reveal identity, contact details, work history, job-search activity, company names, and tailored claims. Treat their HTML, Markdown, PDFs, and preview images as private.

`.gitignore` prevents ordinary additions. It does not remove a file that is already tracked, protect files copied elsewhere, clean Git history, or stop a forced `git add -f`.

## Privacy check

Run:

```bash
make privacy
```

The scanner examines tracked and unignored files. It blocks:

- unexpected files under `PROFILE/` and `APPLICATIONS/`;
- raster images that could contain a portrait or metadata;
- common email and international phone patterns;
- non-placeholder `mailto:` and `tel:` links; and
- machine-specific home and file paths.

The scanner cannot reliably identify names, employers, locations, uncommon identifiers, or sensitive prose. Review the staged diff yourself.

The setup command installs a pre-commit hook that scans the exact staged content. CI repeats the public-tree scan after publication.

## Before every commit

```bash
make privacy
git status --short
git diff --cached --stat
git diff --cached
```

Confirm that no completed candidate profile, application output, real identity, contact detail, company-specific role data, or machine-specific path appears.

## Before the first push

1. Confirm that no remote action is already configured:

   ```bash
   git remote -v
   ```

2. List every file in the proposed public history:

   ```bash
   git ls-tree -r --name-only HEAD
   ```

3. Search the complete history for files that should never have been committed:

   ```bash
   git log --all --name-only --format= | sort -u
   ```

4. Run `make privacy` and inspect the current tree and staged diff.

5. Obtain the user's explicit confirmation before creating a GitHub repository, adding a GitHub remote, or pushing. Repository agents are prohibited from taking those actions without confirmation.

## If a private file is staged

Unstage it without deleting the local file:

```bash
git restore --staged PROFILE/master-cv.html
```

Use the actual path if a different file was staged. Verify the ignore rule with `git check-ignore -v <path>`.

## If a private file is committed locally

Do not push. Remove it from the commit or rewrite the unpublished local history, then verify every commit again. The appropriate Git command depends on where the commit sits; preserve a separate local backup of the private source outside the repository before rewriting.

## If a private file was pushed

Removing it in a new commit does not remove it from history. Treat exposed contact details or credentials as compromised, rotate anything revocable, rewrite repository history with an appropriate tool such as `git filter-repo`, and follow the hosting provider's cache and sensitive-data removal procedure. Coordinate history rewriting with every collaborator before force-pushing.

Portraits may carry EXIF, XMP, C2PA, or other provenance metadata. This pipeline keeps the portrait out of Git entirely instead of relying on metadata stripping.
