# Application writing pipeline

This is the operating guide for the judgment-heavy part of cvcannon: turning one saved
job listing into one tailored CV and one matching cover letter. The agent follows it;
the scripts only scaffold, render, and verify.

The goal is applications that make the strongest defensible case from the candidate's
real experience, use the employer's own terminology where it is accurate, stay
ATS-readable, and read as credible human writing.

## The pipeline

```text
job listing
  -> structured job analysis          job-analysis.md
  -> candidate evidence matching      evidence-map.md
  -> tailoring strategy               application-notes.md
  -> tailored CV                      cv.html
  -> CV validation                    application-notes.md + make build
  -> cover-letter argument selection  application-notes.md
  -> company / context research       application-notes.md
  -> cover letter                     cover-letter.html
  -> final factual + style validation make build + application-notes.md
  -> save application outputs         APPLICATIONS/<slug>/
```

Both documents are generated from the same factual model. The CV decides which
evidence receives prominence; the cover letter explains a small number of the
strongest connections. Neither invents facts, and neither interprets the raw vacancy
independently once the analysis exists.

Do the stages in order. The analysis artifacts are grounding, not paperwork: writing
from them is what makes tailoring reproducible and hallucination difficult.

## Sources of truth

Use these in order:

1. direct corrections and facts supplied by the user;
2. `PROFILE/master-cv.html` for established candidate facts and bullet variants;
3. source documents under `PROFILE/`;
4. the saved listing in `job-description.md` for requirements, vocabulary, company
   details, and the recipient.

A claim may appear in an application only when it traces to one of these. If the user
supplies a lasting correction, update the master CV first, then use it.

## Stage 1 — Structured job analysis

Read the saved listing and fill `job-analysis.md`. Extract conclusions, not a copy of
the posting:

- primary responsibilities of the role;
- the employer's apparent priorities;
- required and preferred skills, separated;
- the terminology and keywords the employer actually uses;
- company context: product, operating model, and tone (startup, enterprise, technical);
- any concrete, verifiable company detail worth referencing later.

If a strong analysis already exists for this listing, reuse and correct it rather than
re-deriving it. Every later stage reads these conclusions instead of re-interpreting
the vacancy.

## Stage 2 — Candidate evidence map

Fill `evidence-map.md` before writing a single line of either document. Map each
requirement to real evidence:

| Requirement / priority | Importance | Matching evidence | Evidence source | Match | Terminology | CV? | Letter? |
| --- | --- | --- | --- | --- | --- | --- | --- |

Match is one of three honest values:

- **exact** — the candidate has done this specific thing;
- **adjacent** — related experience that transfers, stated honestly;
- **gap** — no supporting evidence exists.

Never collapse adjacent experience or a gap into exact to raise keyword similarity.
Use exact employer terminology only when it accurately names something the candidate
genuinely knows or has done.

Close the map with a coverage summary: major requirements covered, gaps remaining, the
single strongest connection (this will lead the cover letter), the second argument,
additional value, and any material gap that genuinely needs addressing.

The evidence map is the grounding layer. Every meaningful claim in the CV and cover
letter must trace to a row here, and every row must trace to the master CV, documented
project history, or a user-confirmed fact.

## Stage 3 — Tailoring strategy

Record the plan in `application-notes.md` before editing the documents. For each
section decide what deserves more emphasis, less emphasis, rewording, or removal.

Ask of every section:

- Does this materially support candidacy for **this** job?
- Is there a more accurate and relevant way to phrase it for **this** job?
- Should it have greater or lower prominence?
- Is there stronger evidence elsewhere in the candidate's background?

### Master CV as source of truth

Keep one complete master profile containing all verified experience, skills, projects,
metrics, and useful bullet variants. Never modify the master because a particular job
wants something different. Generate application-specific versions from it. Prefer
selecting different verified bullets over rewriting facts.

### Candidate positioning

Establish the candidate's positioning from the master CV and preserve it. A vacancy
does not get to redefine the candidate. For an operations/automation profile, the
positioning centers on systems operations, automation, infrastructure, integrations,
production support, Linux/server administration, internal tooling, workflow and
process automation, technical troubleshooting, self-hosted systems, APIs and system
integration, and operational ownership.

Do not relabel such a candidate as a software engineer merely because a listing
mentions Python or programming. Do not imply conventional software-development
expertise when the actual evidence is automation, infrastructure, integration,
scripting, troubleshooting, or systems ownership. When a requirement is adjacent
rather than exact, communicate the transfer honestly.

### Professional summary

Rewrite the summary for the target role so it reflects the actual function and the
strongest matching capabilities. Do not replace the candidate's real professional
identity with the vacancy's job title.

Remove empty phrases such as:

- results-driven professional
- dynamic professional
- proven track record (when no evidence follows)
- highly motivated
- passionate technology professional

Demonstrate qualities through evidence instead.

### Skills

Reorder skills by relevance to the role. Use exact vacancy terminology when it
truthfully describes existing experience. Adding a keyword is allowed only when it
describes real experience, never to raise ATS similarity. Where useful, distinguish
direct experience, closely adjacent experience, familiarity or exposure, and genuine
gaps. Never collapse those categories.

### Experience

- Put the strongest relevant bullets first within each role.
- De-emphasise or remove weaker, irrelevant bullets when space is tight.
- Incorporate vacancy terminology naturally where accurate.
- Add context to vague existing statements.
- Preserve important concrete numbers and outcomes.
- Emphasise business impact alongside technical implementation.
- Surface highly relevant projects where they strengthen the application.

Ordering experience by relevance is allowed, but do it only when it does not make
chronology confusing or produce an unconventional CV without a clear benefit. Prefer
normal reverse chronology and change emphasis within positions.

### Truth versus tailoring

Acceptable:

- reordering true information;
- emphasising relevant experience;
- using accurate industry terminology;
- explaining vague accomplishments more clearly;
- matching terminology to the vacancy;
- selecting different verified bullets from the master profile;
- translating genuinely equivalent concepts into the employer's vocabulary.

Unacceptable:

- adding skills the candidate does not have;
- altering metrics;
- inventing achievements or responsibilities;
- claiming titles never held;
- adding certifications or education not possessed;
- converting adjacent experience into direct experience;
- implying proficiency unsupported by evidence.

This rule has priority over ATS optimisation.

### Bullet writing

Prioritise this shape when the evidence supports the elements:

```text
action + system or problem + meaningful context + result or impact
```

Prefer:

> Refactored a 53-node n8n workflow into an orchestrator and six sub-workflows, adding
> validation and eliminating silent failure paths.

over:

> Improved automation workflows and increased reliability.

Do not manufacture metrics because quantified bullets are generally stronger.
Preserve existing verified quantitative evidence whenever it is useful. Specific
technical scale is valuable evidence even when there is no financial or percentage
outcome.

## Stage 4 — Tailored CV

Edit `cv.html` from the scaffolded copy of the master. Preserve the document shell, A4
print rules, and local font paths. Keep dates, titles, credentials, metrics, and
proficiency levels exact.

### CV validation

Before accepting the CV, check each item. When a problem is found, correct the document
rather than only reporting it.

- Is every claim true and traceable to the evidence map?
- Has any adjacent experience been overstated?
- Were unsupported technologies added?
- Were metrics altered or invented?
- Are the employer's most important requirements represented when genuine evidence exists?
- Are the strongest relevant bullets placed prominently?
- Are important keywords present naturally?
- Is terminology accurate?
- Is anything obviously keyword-stuffed?
- Has irrelevant material consumed valuable space?
- Is the formatting still ATS-safe and one A4 page?
- Is it easy for a human recruiter to scan?
- Does the candidate still sound like the same real person as the master CV?

Record the outcome in the validation section of `application-notes.md`.

## Stage 5 — Cover letter

Generate the letter only after the job analysis and CV tailoring are complete. It is not
a restatement of the CV. It provides context, reasoning, personality, and connections
the CV cannot express as effectively, and it answers:

- Why me?
- Why this role?
- Why this company or environment?

Do not force artificial answers where the evidence is weak.

### Argument selection and research

Before writing, decide and record:

- strongest qualification match;
- second-best supporting argument;
- relevant additional value;
- an important gap, only if one genuinely needs addressing;
- concrete company information worth mentioning;
- appropriate tone for the organisation.

Research the company when reliable information is available, and use it only if it
materially improves the letter. Do not produce fake admiration based on generic website
copy. Never write "I have always admired your innovative company." Prefer something
specific about the role's actual problem, product, technical environment, operating
model, a recent initiative, or a relevant company characteristic.

If there is nothing meaningful to say, omit company enthusiasm instead of fabricating
it.

### Opening strategy

Choose the hook that is actually supported:

- specific company knowledge;
- genuine mutual connection;
- problem-solver / job-problem opening;
- relevant achievement;
- credible industry insight.

For operations and infrastructure roles, a problem/role alignment or a concrete
relevant achievement is usually more credible than enthusiasm.

Avoid generic openings:

- "I am writing to apply for..."
- "I saw your posting on LinkedIn..."
- "I believe I am the perfect candidate..."

Establish relevance quickly. Do not force a theatrical hook when a concise
professional opening is stronger.

### Body paragraph 1 — direct match

Use:

```text
their important need + directly relevant experience + specific evidence or result
```

Choose one strong connection from the evidence map. Do not cram unrelated skills into
one paragraph.

### Body paragraph 2 — broader value or gap handling

Use this for either another meaningful dimension of value, or a material qualification
gap that genuinely requires explanation. Do not proactively advertise every minor
mismatch.

When addressing a real gap:

- do not apologise;
- do not pretend it does not exist;
- identify transferable or adjacent evidence;
- show relevant learning ability through evidence where possible;
- distinguish clearly between what is already known and what would need to be learned.

For example, no direct experience with a specific enterprise platform may be supported
by experience administering comparable systems and learning unfamiliar production
tooling. That is acceptable. Claiming experience with the requested platform is not.

### Tone and company context

Adapt tone to the organisation:

- **Startup:** somewhat less formal; emphasise autonomy, ambiguity, broad ownership, and
  practical problem-solving where supported.
- **Enterprise:** somewhat more formal; emphasise process, reliability, scale,
  documentation, collaboration, and operational ownership where supported.
- **Technical roles:** mention relevant technologies and systems, demonstrate technical
  understanding, emphasise meaningful projects, and include technical and business
  impact.

Do not imitate the employer's marketing language. The voice must still sound like the
candidate.

### Length and structure

- approximately 250–400 words;
- usually 3–4 paragraphs;
- professional, concise, confident without arrogance.

```text
1. Opening hook + role and company relevance
2. Strongest direct qualification match
3. Additional value, and gap handling only where useful
4. Concise close with a specific contribution and an invitation to discuss
```

Do not pad a strong 260-word letter to approach the upper limit. Do not compress a
technically substantive application until important reasoning disappears.

### Closing

Reference a plausible contribution and invite further discussion. Avoid desperation,
exaggerated enthusiasm, passive boilerplate, generic promises, and unnecessary
statements that the CV is attached:

- "I look forward to hearing from you"
- "Please find my resume attached"
- "I am available for an interview at your convenience"

## Stage 6 — Shared anti-AI style pass

Apply the same style pass to both documents. Remove:

- generic AI prose;
- inflated adjectives and excessive buzzwords;
- fake enthusiasm, superlatives, and unsupported claims of being innovative, strategic,
  or exceptional;
- repetitive sentence structures and formulaic transitions;
- corporate filler;
- "leveraged" and "spearheaded";
- suspiciously polished but information-poor sentences.

Prefer plain, specific technical language. Evidence should create the impression, not
adjectives. The tone is calm, technically literate, concise, credible, understated,
confident, and human.

The build fails on a short list of banned buzzwords and cover-letter clichés and warns
on softer judgment words. See `scripts/cv.py` for the exact lists.

### Cover-letter validation

Check that:

- the opening is not generic;
- meaningful company or role context is present;
- experience is connected directly to requirements;
- at least one concrete achievement or metric is included when the evidence supports it;
- any material gap is handled appropriately;
- the tone is confident but not arrogant;
- the closing has a sensible call to action;
- the letter is normally 250–400 words;
- grammar and spelling are clean;
- it provides information or reasoning beyond the CV;
- every substantive claim is supported;
- it does not sound mass-generated.

Do not score the letter subjectively. Translate "would this make me want to interview
the candidate?" into concrete checks for relevance, credibility, specificity, and
clarity.

Record the outcome in `application-notes.md`.

## Application artifacts

Each `APPLICATIONS/<slug>/` folder retains:

| File | Purpose |
| --- | --- |
| `job-description.md` | Saved source vacancy and retrieval details |
| `job-analysis.md` | Structured role, requirement, and company analysis |
| `evidence-map.md` | Requirement-to-evidence grounding table |
| `application-notes.md` | Tailoring decisions, cover-letter plan, validation record, date, state |
| `cv.html` / `cv.pdf` | Tailored CV source and PDF |
| `cover-letter.html` / `cover-letter.pdf` | Cover letter source and PDF |
| `previews/` | PNG previews for visual review |

Filenames are deterministic and readable. The master CV is never overwritten. The
notes are retained so an interview-preparation agent can later reconstruct exactly
which arguments were made to that employer. Keep the notes out of the documents
themselves.

`make new` scaffolds these artifacts, each beginning with a `cvcannon:pending` marker
that must be removed once the file is complete. To add a missing artifact to an
existing application, create it with the same sections:

- `job-analysis.md`: Target; Primary responsibilities; Employer priorities;
  Requirements (Requirement, Required or preferred, Importance, Employer terminology);
  ATS keywords; Company context; Recipient.
- `evidence-map.md`: the requirement table (Requirement / priority, Importance,
  Matching candidate evidence, Evidence source, Match, Terminology to use, CV?,
  Letter?); Coverage summary.
- `application-notes.md`: Generated date and Status; Tailoring decisions (Target,
  Summary, Skills, Experience, Overall); Cover-letter plan; Validation record.

`make build` refuses to run until the analysis artifacts are complete and applies the
writing checks described above.
