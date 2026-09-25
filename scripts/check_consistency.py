#!/usr/bin/env python3
"""Enforce the subset/brief rules between Master___Resume.tex and every derived file.

Rules checked (see CLAUDE.md for the authoritative statement):

1. SUBSET RULE — Research___Resume.tex, Leadership___Resume.tex
   may only *omit* content. Every content argument they contain must appear
   byte-identical in Master___Resume.tex: no added items, no reworded text, no
   changed dates/supervisors/links/titles.

2. CV BRIEF RULE — Master___CV.tex must use the same entry titles and the same
   section titles as Master, but is allowed (expected) to shorten descriptions.
   So: titles must match Master exactly; bullet bodies need not.

3. Section titles used by any derived file must exist in Master.

Documented exceptions live in EXCEPTIONS below and are mirrored in CLAUDE.md.

Usage: scripts/check_consistency.py   (exit 1 if any violation)
"""
import re
import sys
import os

MASTER = "Master___Resume.tex"
SUBSETS = ["Research___Resume.tex", "Leadership___Resume.tex"]  # TA___Resume.tex removed for now (in git history)
CV = "Master___CV.tex"
# Targeted industry resumes: bullets/projects/awards/skills are verbatim Master
# content, but entry headers are the CV's "Institution - Role" form, and the two
# experience sections are merged into one "Experience".
INDUSTRY = ["Robotics___Resume.tex", "ML___Resume.tex", "Mechanical___Resume.tex"]
INDUSTRY_SECTIONS = {"Experience", "Publications", "Leadership \\& Teaching Experience"}

# --- Documented exceptions (keep in sync with CLAUDE.md) -------------------
EXCEPTIONS = {
    # Leadership___Resume.tex targets non-academic part-time roles: it uses a
    # plain "Skills" heading instead of "Technical Skills & Coursework".
    ("Leadership___Resume.tex", "section", "Skills"),
}

# Master section titles the CV is allowed to rename, and what it renames them to.
CV_SECTION_ALIASES = {
    "Teaching": "Teaching Experience",
    # CV splits Master's combined Leadership & Volunteering into two sections.
    "Leadership \\& Volunteering": ("Leadership Experience", "Volunteering Experience"),
    # CV promotes the scholarship (inline in Master's Education) to its own section.
    "Education": ("Education", "Honours \\& Scholarships"),
    # CV groups Master's three themed Experience sections into one.
    "Experience -- Robotics \\& Computer Vision": "Research Experience",
    "Experience -- Generative AI \\& Predictive Maintenance": "Research Experience",
    "Experience -- Mechanical Simulation \\& Behavioral Research": "Research Experience",
}


def strip_comments(text):
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("%"))


def macro_args(text, macro):
    """Return the raw first-brace-group of every occurrence of `macro`."""
    out = []
    for m in re.finditer(r"\\" + macro + r"(?![A-Za-z])", text):
        i = text.find("{", m.end())
        if i == -1:
            continue
        depth, j = 0, i
        while j < len(text):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out.append(re.sub(r"\s+", " ", text[i + 1 : j]).strip())
    return out


def skill_items(row):
    """Split a skills row into its label and comma-separated items (parens kept)."""
    m = re.match(r"(\\textbf\{[^}]*\})\s*(.*)", row)
    if not m:
        return None, []
    label, rest = m.groups()
    items, depth, cur = [], 0, ""
    for ch in rest:
        depth += (ch == "(") - (ch == ")")
        if ch == "," and depth == 0:
            items.append(cur.strip())
            cur = ""
        else:
            cur += ch
    items.append(cur.strip())
    return label, [i for i in items if i]


def is_skill_subset(row, master_rows):
    """True if `row` is a Master skills row with only items removed."""
    label, items = skill_items(row)
    if not label or not items:
        return False
    for mrow in master_rows:
        mlabel, mitems = skill_items(mrow)
        if mlabel == label and set(items) <= set(mitems):
            return True
    return False


def pub_words(text):
    """A publication entry reduced to its content words.

    Drops links, LaTeX markup, quotes and punctuation, so that formatting choices
    (bold vs bold-italic, quoted vs unquoted, `2025;` vs `2025.`) do not matter but
    every surviving *word* still has to come from Master.
    """
    text = re.sub(r"\\href\{[^{}]*\}\{(?:[^{}]|\{[^{}]*\})*\}", " ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?", " ", text)
    text = re.sub(r"[{}`'\".,;:()\[\]$~*-]", " ", text)
    return text.lower().split()


def is_omission_of_master(arg, master_items):
    """True if `arg` is some Master entry with words only removed (order kept).

    The industry resumes shorten publication entries to title/venue/year/status by
    dropping the author list; nothing may be added or reworded.
    """
    words = pub_words(arg)
    for m in master_items:
        it = iter(pub_words(m))
        if all(w in it for w in words):
            return True
    return False


def section_text(text, title):
    """The body of one \\section{...}, up to the next section."""
    start = text.find("\\section{%s}" % title)
    if start == -1:
        return ""
    nxt = text.find("\\section{", start + 1)
    return text[start:nxt if nxt != -1 else len(text)]


def sections(text):
    return re.findall(r"^\\section\{(.+?)\}", text, re.M)


def load(path):
    """Document body only — the preamble's \newcommand definitions are not content,
    and the industry resumes compress their spacing there."""
    text = strip_comments(open(path).read())
    return text[text.index("\\begin{document}"):]


def main():
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    master = load(MASTER)
    master_sections = set(sections(master))
    # Pool of every content string Master contains, per macro type.
    master_pool = {
        m: set(macro_args(master, m))
        for m in ("resumeItem", "nbresumeItem", "resumeSubheading",
                  "resumeSubSubheading", "resumeProjectHeading")
    }
    # resumeSubheading/SubSubheading/ProjectHeading take multiple brace groups;
    # compare the full raw run of groups instead for those.
    def full_entries(text, macro, n):
        out = []
        for m in re.finditer(r"\\" + macro + r"(?![A-Za-z])", text):
            pos, groups = m.end(), []
            for _ in range(n):
                i = text.find("{", pos)
                if i == -1:
                    break
                depth, j = 0, i
                while j < len(text):
                    if text[j] == "{":
                        depth += 1
                    elif text[j] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                groups.append(re.sub(r"\s+", " ", text[i + 1 : j]).strip())
                pos = j + 1
            out.append(" || ".join(groups))
        return out

    master_full = {
        "resumeSubheading": set(full_entries(master, "resumeSubheading", 4)),
        "resumeSubSubheading": set(full_entries(master, "resumeSubSubheading", 2)),
        "resumeProjectHeading": set(full_entries(master, "resumeProjectHeading", 2)),
    }

    violations = []

    # ---- Rule 1: strict subsets ----
    for f in SUBSETS:
        text = load(f)
        for sec in sections(text):
            if sec not in master_sections and (f, "section", sec) not in EXCEPTIONS:
                violations.append(f"{f}: section '{sec}' not in Master")
        for macro in ("resumeItem", "nbresumeItem"):
            for arg in macro_args(text, macro):
                if arg in master_pool[macro]:
                    continue
                if macro == "nbresumeItem" and arg.startswith("\\textbf{Relevant Coursework:}") \
                        and (f, "nbresumeItem", "RELEVANT_COURSEWORK_TRIMMED") in EXCEPTIONS:
                    continue
                violations.append(f"{f}: \\{macro} not verbatim in Master:\n      {arg[:150]}")
        for macro, n in (("resumeSubheading", 4), ("resumeSubSubheading", 2),
                         ("resumeProjectHeading", 2)):
            for e in full_entries(text, macro, n):
                if e not in master_full[macro]:
                    violations.append(f"{f}: \\{macro} not verbatim in Master:\n      {e[:150]}")

    # ---- Rule 2 + 3: CV titles ----
    cv = load(CV)
    allowed_cv_sections = set(master_sections)
    for v in CV_SECTION_ALIASES.values():
        allowed_cv_sections.update(v if isinstance(v, tuple) else (v,))
    for sec in sections(cv):
        if sec not in allowed_cv_sections:
            violations.append(f"{CV}: section '{sec}' is neither in Master nor a documented alias")

    # CV entry titles (1st brace group of each subheading) must exist in Master.
    master_titles = {e.split(" || ")[0] for e in master_full["resumeSubheading"]}
    master_titles |= {e.split(" || ")[0] for e in master_full["resumeProjectHeading"]}
    master_titles |= {e.split(" || ")[0] for e in master_full["resumeSubSubheading"]}
    # Master also expresses some topics only as sub-sub headings or bullets; the
    # CV condenses those into bullets, so bullets are exempt from title matching.
    cv_titles = {e.split(" || ")[0] for e in full_entries(cv, "resumeSubheading", 4)}
    cv_titles |= {e.split(" || ")[0] for e in full_entries(cv, "resumeProjectHeading", 2)}
    # CV titles research/industry entries "Institution - Role" (e.g.
    # "Uber - ML Intern"); the roles ("Research Intern" etc.) are role labels rather than Master's project titles.
    CV_ROLE_TITLES = {"Research Intern", "Research Assistant", "ML Intern",
                      "Subject Matter Expert", "Teaching Assistant", "Volunteer"}
    # The CV may promote a Master bullet into its own section entry (e.g. the
    # scholarship, inline under Education in Master, becomes the sole entry of
    # the CV's Honours & Scholarships section) — but the text must be verbatim.
    master_text_pool = master_titles | master_pool["resumeItem"] | master_pool["nbresumeItem"]
    for t in sorted(cv_titles):
        if t in master_text_pool or t.split(" - ")[-1] in CV_ROLE_TITLES:
            continue
        violations.append(f"{CV}: entry title not present in Master: {t[:120]}")

    # ---- Industry trio: Master content under CV headers ----
    cv_subheads = set(full_entries(cv, "resumeSubheading", 4))
    for f in INDUSTRY:
        text = load(f)
        for sec in sections(text):
            if sec not in allowed_cv_sections and sec not in INDUSTRY_SECTIONS:
                violations.append(f"{f}: section '{sec}' is neither in Master nor a documented alias")
        pubs = set(macro_args(section_text(text, "Publications"), "resumeItem"))
        for macro in ("resumeItem", "nbresumeItem"):
            for arg in macro_args(text, macro):
                if arg in master_pool[macro]:
                    continue
                # Skills rows may drop items from a Master row, never add or reword.
                if macro == "nbresumeItem" and is_skill_subset(arg, master_pool["nbresumeItem"]):
                    continue
                # Publication entries may drop the author list (and nothing else).
                if macro == "resumeItem" and arg in pubs \
                        and is_omission_of_master(arg, master_pool["resumeItem"]):
                    continue
                violations.append(f"{f}: \\{macro} not verbatim in Master:\n      {arg[:150]}")
        for e in full_entries(text, "resumeSubSubheading", 2):
            if e not in master_full["resumeSubSubheading"]:
                violations.append(f"{f}: \\resumeSubSubheading not verbatim in Master:\n      {e[:150]}")
        for e in full_entries(text, "resumeSubheading", 4):
            # Industry resumes may add a 4-point conversion after the CGPA
            # ("CGPA: 8.57/10 (3.52/4)"); nothing else in the entry may differ.
            e = re.sub(r"(CGPA: [\d.]+/10) \([\d.]+/4\)", r"\1", e)
            if e not in master_full["resumeSubheading"] and e not in cv_subheads:
                violations.append(f"{f}: \\resumeSubheading verbatim in neither Master nor the CV:\n      {e[:150]}")
        for e in full_entries(text, "resumeProjectHeading", 2):
            # An empty {}{} is a structural spacer (supplies the \item a flat
            # Publications list needs), not content - see CLAUDE.md Rule 3.
            if e == " || " or e in master_full["resumeProjectHeading"]:
                continue
            violations.append(f"{f}: \\resumeProjectHeading not verbatim in Master:\n      {e[:150]}")

    if violations:
        print(f"FAIL — {len(violations)} violation(s):\n")
        for v in violations:
            print("  - " + v)
        return 1
    print("PASS — all derived files are clean subsets/briefs of " + MASTER)
    return 0


if __name__ == "__main__":
    sys.exit(main())
