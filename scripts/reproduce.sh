#!/bin/bash
# Reproduce the paper's results end-to-end (scaled; see briefing/evaluation.md).
#
# Runs inside the compute container. Assumes:
#   - environment/setup.sh has installed clingo
#   - scripts/download.sh has fetched data/downloads/ganak (compute nodes have no internet)
#   - Working directory is /home/user
#
# The benchmark programs are tracked in git. Regenerating them (expensive, about
# an hour per split) is NOT part of reproduction:
#   python data/make_benchmarks.py        # train split (data/train/)
#   python eval/test/build_hidden.py      # hidden test split (eval/test/)

set -e

cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}

test -x data/downloads/ganak || bash scripts/download.sh

SKIP_EVAL=1 bash scripts/baseline.sh      # registers clingo_enumeration
SKIP_EVAL=1 bash scripts/method.sh        # self-test, registers sharpasp_sr and hybrid_sharpasp_sr

bash scripts/evaluate_train.sh            # scoring/scores_train.json
cp scoring/scores_train.json scoring/scores.json   # same content as scripts/evaluate.sh would write
if [ -f eval/test/answers.json ]; then
  bash scripts/evaluate_test.sh           # scoring/scores_test.json
fi
