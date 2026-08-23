# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## The five documents

`Master___Resume.tex` is the **single source of truth**. Everything else is derived from it.

| File | Role |
|---|---|
| `Master___Resume.tex` | Comprehensive resume. All content lands here **first**. |
| `Master___CV.tex` | Comprehensive CV — same content, descriptions shortened. |
| `Research___Resume.tex` | Short selective resume (research applications). |
| `TA___Resume.tex` | Targeted resume for ML/AI/DS teaching-assistant applications. |
| `Leadership___Resume.tex` | Targeted resume for non-academic part-time/admin roles (management, marketing, proctoring, advising). |

Each `.tex` has a matching `.pdf` — regenerate and commit together.

## Rule 1 — Derived resumes are strict subsets

`Research___Resume.tex`, `TA___Resume.tex`, `Leadership___Resume.tex` may only **omit**. They must never:

- add an entry, bullet, skill, or word that is not in Master;
- reword anything — not a metric, verb, title, supervisor name/position, institution, link, or date;
- restructure — a Master `\resumeSubSubheading` stays a sub-sub-heading, it cannot be promoted to a `\resumeSubheading` (keep the parent entry and drop the sibling sub-entries instead);
- use a section title that isn't in Master.

To add content to a derived resume, **copy the block verbatim from Master**. If the content doesn't exist in Master yet, add it to Master first.

## Rule 2 — The CV is Master with shorter descriptions

`Master___CV.tex` must carry the **same section titles and the same entry titles** as Master; only bullet bodies may be condensed. Specifically:

- Every entry title and every section title must appear in Master (or be a documented alias, below).
- One Master topic (a `\resumeSubheading` or a nested `\resumeSubSubheading`) → exactly **one** condensed bullet. Don't merge two Master sub-projects into one CV bullet.
- Drop metrics and multi-sentence detail; keep the topic.
- **Every link in Master must survive** — as the same `\faExternalLink*` icon or embedded on a keyword. Condensing must never drop a link.
- Master entries sharing an institution/supervisor merge into one CV entry with a date range spanning them, one bullet per original topic.
- Content in one file but not the other is a gap to fix, not a style choice.

## Documented exceptions

These are the *only* permitted deviations. Anything else is a bug.

| File | Exception |
|---|---|
| `Master___CV.tex` | Renames `Teaching` → `Teaching Experience`; splits Master's `Leadership \& Volunteering` into `Leadership Experience` + `Volunteering Experience`; groups Master's three themed `Experience -- …` sections into one `Research Experience`; promotes Master's Education scholarship bullet into its own `Honours \& Scholarships` section (text verbatim). Uses `{role}{institution}` in `\resumeSubheading` where Master uses `{title $\|$ org}{}`. |
| `TA___Resume.tex` | `Relevant Coursework` trimmed to the ML-relevant subset. |
| `Leadership___Resume.tex` | Section named `Skills` rather than `Technical Skills \& Coursework`. |

## Verifying

`scripts/check_consistency.py` enforces Rules 1–2 and the exception list. Run it after **every** content edit:

```bash
python3 scripts/check_consistency.py    # exits 1 on any violation
```

Also check action verbs:

```bash
grep -o '\\resumeItem{[A-Z][a-z]*' Master___Resume.tex | sed 's/\\resumeItem{//' | sort | uniq -c | awk '$1>1'
```

## Build

```bash
pdflatex <file>.tex
rm -f *.aux *.log *.out    # never commit these
```

## Macros

- `\resumeSubheading{title}{location/company}{role/description}{date}` — main entry.
- `\resumeSubSubheading{role}{date}` — nested sub-entry.
- `\resumeProjectHeading{title}{date}` — bold subsection label (e.g. inside Publications).
- `\resumeItemListStart` / `\resumeItem{…}` / `\resumeItemListEnd` — bullets.
- `\nbresumeItemListStart` / `\nbresumeItem{…}` / `\nbresumeItemListEnd` — no-bullet list (skills).

**Gotcha — bold dates:** `\resumeSubheading`'s 2nd argument is wrapped in `\textbf{}`. For single-line entries (Awards, Honours, Competitive Exams) that put the date there with args 3–4 empty, prefix `\mdseries` (`{\mdseries\textit{Mar '25}}`) to cancel the inherited bold.

**Gotcha — literal `&`:** arguments render inside a `tabular*`, so an unescaped `&` is read as a column separator and causes cascading fatal errors. Always write `\&`.

## Content conventions

- Dates: en dash with spaces — `Jan '24 – May '26` (never `--`).
- Own name bolded in author lists: `\textbf{R. Chakraborty}`.
- Link icons are bold in Publications, unbold elsewhere — intentional.
- Publications split by type: Journal / Conference / Poster / Peer Reviews.
- Every `\resumeItem` in a resume opens with a **distinct action verb** — no repeats within a file. (CV bullets are noun-phrase topics; rule doesn't apply there.)
- Dr. Mani Shankar Dasgupta is **Associate Professor**, BITS Pilani.

## Publishing

Remote `resume-cv` → `github.com/Ritabrata-Chakraborty/Resume-CV.git` (**public**). No `origin` remote.

Real contact info must never reach it. `scripts/publish.sh` handles this:

1. Requires all `.tex` and `CLAUDE.md` committed on `main`.
2. Redacts email/phone to `rc@gmail.com` / `+91 00000 00000`, aborting if the substitution fails.
3. Excludes `CLAUDE.md`, `TA___Resume.*`, `Leadership___Resume.*`; verifies the tree against an allowlist and aborts before pushing if anything unexpected is staged.
4. Force-pushes, then **always** restores real contact info, recompiles, and copies **all** PDFs to `/home/rc/Documents/Personal/Resume/` — even if the push fails.

New local-only resumes must be added to `LOCAL_ONLY_TEX`/`LOCAL_ONLY_PDF` **and** `ALLOWED_PATTERN` in that script.
