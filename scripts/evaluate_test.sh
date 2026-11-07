#!/bin/bash
# Evaluate the hidden test slice: runs every counter registered under
# checkpoints/*/counter.json on the hidden programs in eval/test/ and writes
# scoring/scores_test.json. Uses only eval/test/. No arguments needed.

set -e

cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}

mkdir -p scoring

python eval/test/evaluate.py --output scoring/scores_test.json "$@"
