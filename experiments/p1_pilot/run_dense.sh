#!/usr/bin/env bash
# Dense hosts on CPU; chunk budgets fixed before any results were seen
# (bge: first 2 x 512 tokens, legalbert: first 512 tokens). See RESULTS.md.
set -e
cd "$(dirname "$0")"
python retrieve.py --host bge --chunks 2 --batch 32
python retrieve.py --host legalbert --chunks 1 --batch 16
