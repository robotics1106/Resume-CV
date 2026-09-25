#!/usr/bin/env bash
# Publish a public snapshot of the resume/CV to the `resume-cv` remote, then
# compile every resume with real contact info into RESUME_DIR.
#
# What goes public: ONE parentless commit holding only the public files
# (PUBLIC_TEX, their PDFs, PUBLIC_EXTRA) - never main's history. CLAUDE.md
# and the local-only resumes therefore never leave this machine, and the force-push replaces whatever history the remote had.
#
# Contact info: committed .tex files hold placeholders (git `contact` filter,
# scripts/contact_filter.sh); the real values live only in the untracked
# .contact.local. The snapshot is built from the committed blobs and checked
# for the real values - text, PDFs and the final tree - before anything is pushed.
# The working tree and main are never modified.
#
# Preconditions: .contact.local exists; all .tex and CLAUDE.md committed.
# Usage: scripts/publish.sh

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

RESUME_DIR="/home/rc/Documents/Personal/Resume"
PUBLIC_TEX=(Master___Resume.tex Master___CV.tex Research___Resume.tex)
PUBLIC_EXTRA=(resume_style.tex README.md scripts/publish.sh scripts/check_consistency.py)  # every .tex \inputs resume_style.tex
# Local-only resumes: never published, but compiled and copied to RESUME_DIR.
LOCAL_ONLY_TEX=(Leadership___Resume.tex Robotics___Resume.tex ML___Resume.tex Mechanical___Resume.tex)
ALLOWED_PATTERN='^(Master___Resume\.(tex|pdf)|Master___CV\.(tex|pdf)|Research___Resume\.(tex|pdf)|resume_style\.tex|README\.md|scripts/(publish\.sh|check_consistency\.py))$'

[[ -f .contact.local ]] || { echo "FATAL: .contact.local missing (see scripts/contact_filter.sh)." >&2; exit 1; }
source .contact.local
REAL=(-e "$REAL_EMAIL" -e "$REAL_TEL_TEXT" -e "${REAL_TEL_HREF#tel:}")

if [[ -n "$(git status --porcelain -- '*.tex' CLAUDE.md)" ]]; then
  echo "Uncommitted changes in .tex files or CLAUDE.md - commit first." >&2
  exit 1
fi

TMP="$(mktemp -d)"
IDX="$(mktemp -u)"
trap 'rm -rf "$TMP" "$IDX"' EXIT

echo "Building public snapshot from HEAD's committed blobs..."
for f in "${PUBLIC_TEX[@]}" "${PUBLIC_EXTRA[@]}"; do
  mkdir -p "$TMP/$(dirname "$f")"
  git cat-file blob "HEAD:$f" > "$TMP/$f"      # raw blob: placeholders, no smudge
done
if grep -rlF "${REAL[@]}" "$TMP"; then
  echo "FATAL: real contact info in the snapshot sources above - aborting before push." >&2
  exit 1
fi

echo "Compiling public PDFs..."
( cd "$TMP"
  for f in "${PUBLIC_TEX[@]}"; do
    pdflatex -interaction=nonstopmode "$f" >/dev/null 2>&1 || true
    [[ -s "${f%.tex}.pdf" ]] || { echo "FATAL: $f did not compile." >&2; exit 1; }
    if grep -aqF "${REAL[@]}" "${f%.tex}.pdf" || pdftotext "${f%.tex}.pdf" - | grep -qF "${REAL[@]}"; then
      echo "FATAL: real contact info in ${f%.tex}.pdf - aborting before push." >&2; exit 1
    fi
  done
  rm -f ./*.aux ./*.log ./*.out )

echo "Creating parentless snapshot commit..."
PUBLIC_FILES=("${PUBLIC_TEX[@]}" "${PUBLIC_TEX[@]/%.tex/.pdf}" "${PUBLIC_EXTRA[@]}")
GIT_INDEX_FILE="$IDX" git -c filter.contact.clean=cat -c filter.contact.smudge=cat -c filter.contact.required=false \
  --work-tree="$TMP" add -f -- "${PUBLIC_FILES[@]}"
TREE="$(GIT_INDEX_FILE="$IDX" git write-tree)"
SNAP="$(git commit-tree "$TREE" -m "Public snapshot ($(date +%F)) - contact info redacted")"

UNEXPECTED="$(git ls-tree -r --name-only "$SNAP" | grep -Ev "$ALLOWED_PATTERN" || true)"
if [[ -n "$UNEXPECTED" ]]; then
  echo "FATAL: unexpected files in snapshot, aborting before push:" >&2; echo "$UNEXPECTED" >&2; exit 1
fi
if git grep -qF "${REAL[@]}" "$SNAP" --; then
  echo "FATAL: real contact info in snapshot tree - aborting before push." >&2; exit 1
fi

echo "Force-pushing snapshot $SNAP to resume-cv/main (replaces remote history)..."
git push resume-cv "$SNAP:refs/heads/main" --force

echo "Compiling all resumes with real contact info -> $RESUME_DIR ..."
for f in "${PUBLIC_TEX[@]}" "${LOCAL_ONLY_TEX[@]}"; do
  pdflatex -interaction=nonstopmode "$f" >/dev/null 2>&1 || true
  [[ -s "${f%.tex}.pdf" ]] || { echo "WARNING: $f did not compile." >&2; continue; }
  cp "${f%.tex}.pdf" "$RESUME_DIR/"
done
rm -f ./*.aux ./*.log ./*.out
echo "Done."
