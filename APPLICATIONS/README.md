# Applications

Each role gets a folder containing its source listing, analysis artifacts, tailored HTML documents, PDFs, and previews.

The agent scaffolds that folder by running `make new SLUG=<company-role>`. This copies `PROFILE/master-cv.html`, adds the cover letter template, and creates `job-description.md`, `job-analysis.md`, `evidence-map.md`, and `application-notes.md`. The agent then fills the analysis and evidence map, records the tailoring plan, and writes the documents.

See [`docs/WRITING.md`](../docs/WRITING.md) for the writing pipeline and [`docs/WORKFLOW.md`](../docs/WORKFLOW.md) for the application lifecycle.
