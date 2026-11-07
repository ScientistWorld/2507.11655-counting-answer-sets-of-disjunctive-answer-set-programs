#!/bin/bash
# Evaluation script -- the standard way to evaluate work in this environment.
#
# SELF-CONTAINED: uses only code in eval/ (never imports method/).
#
# Runs every counter registered as checkpoints/<name>/counter.json on the visible
# train programs (data/train/) under the fixed per-program budget and writes
# scoring/scores.json:  experiments -> experiment -> results -> counter -> metrics.
#
# Counter contract: counter.json = {"command": [...]}; the evaluator appends the
# path of one ground ASP program, runs the command from /home/user, and reads the
# exact answer-set count from the last stdout line. See briefing/evaluation.md.
#
# Usage:
#   bash scripts/evaluate.sh                         # all registered counters
#   bash scripts/evaluate.sh --registry other_dir    # counters registered elsewhere

set -e

cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}

mkdir -p scoring

python eval/train/evaluate.py --output scoring/scores.json "$@"
