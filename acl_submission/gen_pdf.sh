#!/usr/bin/env bash
# Build the ACL (ACL Rolling Review) version of the ALERT paper.
#
# Requires a TeX Live installation (pdflatex + bibtex). On Overleaf, just set
# the main document to main.tex; the toolchain below is what Overleaf runs.
#
# Usage:  ./gen_pdf.sh
set -euo pipefail

MAIN=main

pdflatex -interaction=nonstopmode -halt-on-error "${MAIN}.tex"
bibtex   "${MAIN}"
pdflatex -interaction=nonstopmode -halt-on-error "${MAIN}.tex"
pdflatex -interaction=nonstopmode -halt-on-error "${MAIN}.tex"

echo "Built ${MAIN}.pdf"
