#!/bin/bash
# Run the paper's proposed method.
#
# This script trains/runs the paper's method using code in method/.
#
# Usage:
#   bash scripts/method.sh

set -e

cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}

python method/run_sharpasp_sr.py --output checkpoints/sharpasp_sr/results.json
python method/run_hybrid.py --enumeration-limit 1000 --output checkpoints/hybrid/results.json
bash scripts/evaluate.sh
