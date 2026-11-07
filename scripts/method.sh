#!/bin/bash
# Run the paper's proposed method.
#
# sharpASP-sR needs no training: "running" it means self-testing the counter and
# registering it under the counter interface so the evaluators can invoke it on
# benchmark programs:
#   checkpoints/sharpasp_sr/counter.json         direct subtractive-reduction counter (GANAK)
#   checkpoints/hybrid_sharpasp_sr/counter.json  clingo enumeration up to 10^4 answer sets, then sharpASP-sR
# Then scores every registered counter on the train programs (scripts/evaluate.sh).
# Set SKIP_EVAL=1 to only self-test and register.
#
# Usage:
#   bash scripts/method.sh

set -e

cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}

python method/selftest.py
python method/register_counters.py --registry checkpoints
if [ "${SKIP_EVAL:-0}" != "1" ]; then
  bash scripts/evaluate.sh
fi
