# Applications

Each role gets a folder containing its source listing, tailored HTML documents, PDFs, and previews.

The agent scaffolds that folder by running `make new SLUG=<company-role>`. This copies `PROFILE/master-cv.html`, adds the cover letter template, and creates an empty job-listing file. The agent then reads the supplied listing and tailors the copied documents.

See [`docs/WORKFLOW.md`](../docs/WORKFLOW.md) for the application lifecycle.
