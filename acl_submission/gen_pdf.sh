#!/usr/bin/env bash
# Build the ALERT paper.
#
#   ./gen_pdf.sh            anonymous review version  -> main.pdf
#   ./gen_pdf.sh preprint   non-anonymous preprint    -> main-preprint.pdf
#   ./gen_pdf.sh final      camera-ready              -> main-final.pdf
#
# preprint/final require camera_ready.tex (copy camera_ready.tex.example).
# Requires TeX Live (pdflatex + bibtex). On Overleaf, set main.tex as the
# main document; it builds the review version by default.
set -euo pipefail

MODE="${1:-review}"
case "$MODE" in
  review|preprint|final) ;;
  *) echo "usage: $0 [review|preprint|final]" >&2; exit 2 ;;
esac
if [[ "$MODE" != review && ! -f camera_ready.tex ]]; then
  echo "camera_ready.tex not found: copy camera_ready.tex.example and fill in authors." >&2
  exit 1
fi

JOB=main
[[ "$MODE" != review ]] && JOB="main-$MODE"
TEX="\\def\\aclmode{$MODE}\\input{main.tex}"

pdflatex -interaction=nonstopmode -halt-on-error -jobname="$JOB" "$TEX"
bibtex   "$JOB"
pdflatex -interaction=nonstopmode -halt-on-error -jobname="$JOB" "$TEX"
pdflatex -interaction=nonstopmode -halt-on-error -jobname="$JOB" "$TEX"

echo "Built ${JOB}.pdf ($MODE)"
