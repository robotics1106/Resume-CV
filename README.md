# Research Resume & CV LaTeX Templates

This repository contains three LaTeX documents for researchers and technical
students, all built on the same custom LaTeX macros so entries look
consistent across documents: a comprehensive resume, a comprehensive CV, and
a short selective resume.

## Master___Resume.tex

The comprehensive, achievement-driven resume — the content source of truth.
Work is grouped by theme, with two detailed, impact-driven bullets per entry.

1. Header — name, links (GitHub, Scholar, ResearchGate, Scopus, Portfolio,
   LinkedIn), email, and phone.
2. Education — degree, institute, location, dates, GPA.
3. Publications & Peer Reviews — Journal / Conference / Poster / Peer Review
   subsections, each with authors, title, venue, and links.
4. Experience — grouped by theme (Robotics & Computer Vision, Generative AI &
   Predictive Maintenance, Mechanical Simulation & Behavioral Research).
5. Industry Experience
6. Projects — selected project work with measurable outcomes.
7. Awards & Achievements
8. Leadership & Teaching
9. Volunteering
10. Technical Skills & Coursework

## Master___CV.tex

A comprehensive, academic-style CV: the same body of work as the Master
resume, condensed to one-line topics rather than full bullet descriptions.

1. Header — name and contact/profile links.
2. Education
3. Publications & Peer Reviews — same Journal / Conference / Poster / Peer
   Review breakdown as the resume.
4. Research Experience — position, institution, supervisor, one-line topic.
5. Industry Experience — same condensed format, for industry roles.
6. Projects
7. Teaching Experience
8. Honours & Scholarships
9. Awards & Achievements
10. Leadership Experience
11. Volunteering Experience
12. Professional Activities — society memberships, etc.
13. Competitive Examinations
14. Technical Skills & Coursework

## Research___Resume.tex

A short, selective resume for targeted applications — deliberately not
comprehensive; carries a subset of the entries in the other two documents.

## Building

Every file is self-contained; compile any of them with:

```bash
pdflatex Master___Resume.tex
pdflatex Master___CV.tex
pdflatex Research___Resume.tex
```

Requires a standard TeX Live installation (`fontawesome5`, `titlesec`,
`enumitem`, `tabularx`, `fancyhdr`, and `hyperref` are used by all three files).

## License

MIT License.
You can reuse and adapt these templates for your own resume or CV.

---

<p align="center">
  <strong>⭐ IF THIS HELPS, PLEASE STAR THE REPO! ⭐</strong>
</p>
