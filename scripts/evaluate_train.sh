#!/bin/bash
# Evaluate the visible train slice: runs every counter registered under
# checkpoints/*/counter.json on data/train/ programs and writes
# scoring/scores_train.json. Uses only eval/train/.

set -e

cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}

mkdir -p scoring

python eval/train/evaluate.py --output scoring/scores_train.json "$@"
