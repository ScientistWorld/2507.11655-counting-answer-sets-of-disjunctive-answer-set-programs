#!/bin/bash
# Evaluation script — the standard way to evaluate work in this environment.
#
# This script must be SELF-CONTAINED using only code in eval/.
# Do NOT import from method/ — evaluate.sh must work even when the
# paper's method code is hidden from a scientist agent.
#
# Design it so that anyone following the same output format can run
# this script to evaluate their results.
#
# OUTPUT CONTRACT: this script writes scoring/scores.json with:
#   experiments -> experiment name -> results -> method name -> metrics.
# It scores existing result artifacts and omits methods whose artifacts are
# absent, so future agents can evaluate any compatible method output.
#
# Example usage:
#   bash scripts/evaluate.sh
#   bash scripts/evaluate.sh --method-results checkpoints/new_method/results.json
#
# Called from run.sh after training, or independently.

set -e

cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}

mkdir -p scoring

python eval/evaluate_counts.py "$@"
