#!/usr/bin/env bash
# Publish a contact-info-redacted snapshot of the resume/CV to the public
# `resume-cv` remote, then restore real contact info locally. Every PDF in
# the repo (public and local-only) is recompiled fresh and copied to
# RESUME_DIR, even though only the public ones get redacted and pushed.
#
# Preconditions: all real content (including CLAUDE.md) already committed on
# `main`. Only *.tex/CLAUDE.md are checked for cleanliness — PDFs are expected
# to differ run-to-run because pdflatex embeds a compile timestamp.
#
# Usage: scripts/publish.sh

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

RESUME_DIR="/home/rc/Documents/Personal/Resume"
TEX_FILES=(Master___Resume.tex Master___CV.tex Research___Resume.tex)
PDF_FILES=(Master___Resume.pdf Master___CV.pdf Research___Resume.pdf)
# Targeted/draft resumes that stay local-only — never pushed to the public
# repo, but still compiled fresh and copied to RESUME_DIR like everything else.
LOCAL_ONLY_TEX=(TA___Resume.tex Leadership___Resume.tex)
LOCAL_ONLY_PDF=(TA___Resume.pdf Leadership___Resume.pdf)
# Any file NOT in this list must never reach the public repo — add new
# local-only resumes to LOCAL_ONLY_TEX/PDF above, not just here.
EXCLUDE_FROM_PUBLISH=(CLAUDE.md "${LOCAL_ONLY_TEX[@]}" "${LOCAL_ONLY_PDF[@]}")

REAL_EMAIL="ritabratabits@gmail.com"
REAL_TEL_HREF="tel:+12673253075"
REAL_TEL_TEXT="+1 267 325 3075"
FAKE_EMAIL="rc@gmail.com"
FAKE_TEL_HREF="tel:+910000000000"
FAKE_TEL_TEXT="+91 00000 00000"

if [[ -n "$(git status --porcelain -- "${TEX_FILES[@]}" "${LOCAL_ONLY_TEX[@]}" CLAUDE.md)" ]]; then
  echo "Uncommitted changes in .tex files or CLAUDE.md — commit real content first." >&2
  exit 1
fi

PUBLISHED=0
restore() {
  echo "Restoring real contact info..."
  if [[ "$PUBLISHED" == "1" ]]; then
    git reset --hard HEAD~1 >/dev/null
  else
    git checkout -- "${TEX_FILES[@]}" 2>/dev/null || true
  fi
  rm -f ./*.aux ./*.log ./*.out
  for f in "${TEX_FILES[@]}" "${LOCAL_ONLY_TEX[@]}"; do
    pdflatex -interaction=nonstopmode "$f" >/dev/null 2>&1
  done
  rm -f ./*.aux ./*.log ./*.out
  cp "${PDF_FILES[@]}" "${LOCAL_ONLY_PDF[@]}" "$RESUME_DIR/"
  echo "Restored real content and PDFs (repo + $RESUME_DIR, all PDFs including local-only)."
}
trap restore EXIT

echo "Redacting contact info..."
for f in "${TEX_FILES[@]}"; do
  sed -i "s/\\\\href{mailto:${REAL_EMAIL}}{${REAL_EMAIL}}/\\\\href{mailto:${FAKE_EMAIL}}{${FAKE_EMAIL}}/" "$f"
  sed -i "s/\\\\href{${REAL_TEL_HREF}}{${REAL_TEL_TEXT}}/\\\\href{${FAKE_TEL_HREF}}{${FAKE_TEL_TEXT}}/" "$f"
  if grep -qF "$REAL_EMAIL" "$f" || grep -qF "$REAL_TEL_TEXT" "$f"; then
    echo "FATAL: redaction did not apply to $f — aborting before commit/push." >&2
    exit 1
  fi
done

echo "Compiling redacted PDFs..."
for f in "${TEX_FILES[@]}"; do
  pdflatex -interaction=nonstopmode "$f" >/dev/null 2>&1
done
rm -f ./*.aux ./*.log ./*.out

git add -A
# Must run AFTER `git add -A`, not before: `git add -A` re-stages anything it
# finds on disk, so an earlier `git rm --cached` gets silently undone.
echo "Excluding non-public files from this snapshot..."
git rm -q --cached --ignore-unmatch "${EXCLUDE_FROM_PUBLISH[@]}"
git commit -q -m "Publish: redact contact info for public release"
PUBLISHED=1

echo "Verifying published tree contains only expected files..."
ALLOWED_PATTERN='^(Master___Resume\.(tex|pdf)|Master___CV\.(tex|pdf)|Research___Resume\.(tex|pdf)|README\.md|scripts/(publish\.sh|check_consistency\.py))$'
UNEXPECTED="$(git ls-tree -r --name-only HEAD | grep -Ev "$ALLOWED_PATTERN" || true)"
if [[ -n "$UNEXPECTED" ]]; then
  echo "FATAL: unexpected files in publish commit, aborting before push:" >&2
  echo "$UNEXPECTED" >&2
  exit 1
fi

echo "Force-pushing to resume-cv/main..."
git push resume-cv HEAD:main --force
