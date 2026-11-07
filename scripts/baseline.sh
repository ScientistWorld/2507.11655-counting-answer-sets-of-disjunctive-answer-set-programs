#!/bin/bash
# Run the paper's baseline: answer-set enumeration with clingo (the paper's
# strongest enumeration baseline). Registers checkpoints/clingo_enumeration/counter.json
# and scores every registered counter on the train programs (scripts/evaluate.sh).
# Set SKIP_EVAL=1 to only register.
#
# Usage:
#   bash scripts/baseline.sh [clingo_enumeration]

set -e

cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}

name="${1:-clingo_enumeration}"
if [ "$name" != "clingo_enumeration" ]; then
  echo "Unknown baseline: $name" >&2
  exit 2
fi

python baseline/enumerate.py --register --registry checkpoints
if [ "${SKIP_EVAL:-0}" != "1" ]; then
  bash scripts/evaluate.sh
fi
