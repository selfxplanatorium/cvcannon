# Troubleshooting

## Doctor says the authoritative CV is missing

Provide an existing CV, a readable document or text file under `PROFILE/`, or career information in chat. Run `make profile`, complete `PROFILE/master-cv.html` from that material, and remove every placeholder.

## Portrait exists but is not a PNG

The script checks the PNG file signature. Export or convert the original image to PNG. Changing the filename extension alone does not convert an image.

## Portrait is missing from the PDF

When using a portrait, the application CV must contain:

```html
<img src="../../PROFILE/portrait.png" alt="..." class="profile-pic">
```

Run `make doctor`, then rebuild. If Chromium is installed as a confined Snap, move the repository under your home directory or use a browser build that can read the repository path.

If the master CV is intentionally photo-free, remove the portrait `<img>` element. The build supports CVs without a photo.

## The document has two pages

Remove weak or repeated content first. Then follow the fitting order in the CV template comments. Keep body text at 7pt or larger. Rebuild after each change; browser preview alone does not prove the PDF page count.

## The build reports unresolved placeholders

Search visible document content for `{{...}}` and `[bracketed prompts]`. Replace every prompt in headings, links, `alt` text, addresses, dates, and body copy. Template comments may retain instructional examples because they are not visible content.

## The build reports Type 3 or non-embedded fonts

Use static local or embedded font files. Do not load fonts from a CDN or use a variable font for PDF export. Confirm that every `@font-face` path resolves from the generated application folder.

The default template bundles Lexend. Its serif headings use the first available system font from `Georgia`, `Liberation Serif`, `Times New Roman`, and the generic `serif` fallback. Custom templates may replace either font stack.

## A template is missing from `make templates`

Confirm that its folder name contains lowercase letters, digits, and hyphens and that the folder contains both `cv.html` and `cover-letter.html`.

## Extracted text is too short

Open the PDF and try selecting a paragraph. Restore the local static fonts if selection fails. If selection works, the document may simply contain too little finished content; replace remaining sample text and add only relevant supported evidence.

## Chromium is not found

Install Chromium or Google Chrome and ensure its executable is on `PATH`. Supported Linux executable names are `chromium`, `chromium-browser`, `google-chrome`, and `google-chrome-stable`.

## The contact row wraps

Shorten visible link labels while preserving complete `href` values, remove optional contact channels, or tighten the documented gap. Keep the photo at 80px and use font-size changes last. Inspect the generated preview and PDF after rebuilding.

## Privacy check flags an example

Use reserved example domains such as `example.com` and template placeholders such as `{{Email}}`. Do not add a personal allowlist to the scanner. Private content belongs under `PROFILE/` or `APPLICATIONS/`.

## Candidate or application data appears in Git status

Check its path and ignore rule:

```bash
git check-ignore -v path/to/file
git ls-files --error-unmatch path/to/file
```

If the second command succeeds, the file is already tracked. Follow [the privacy cleanup procedure](PRIVACY.md#if-a-private-file-is-staged).
