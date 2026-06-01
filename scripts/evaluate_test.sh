#!/bin/bash
# Evaluate the held-out test slice of the gym scoring harness.
#
# Mirrors scripts/evaluate.sh: scores existing result artifacts, does not run
# method code, and writes a scores JSON file for downstream comparison.

set -e

cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}

mkdir -p scoring

python eval/test/evaluate_counts.py --output scoring/scores_test.json "$@"
