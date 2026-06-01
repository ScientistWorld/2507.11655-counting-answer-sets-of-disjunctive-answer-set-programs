#!/bin/bash
# Reproduce the paper's results end-to-end.
#
# This script runs inside the compute container and should call
# scripts/baseline.sh and scripts/method.sh to run baselines and
# the paper's method, each of which calls scripts/evaluate.sh.
#
# Assumes:
#   - Container is built (environment/container.sif)
#   - Data and models are downloaded (via scripts/download.sh)
#   - Working directory is /home/user
#
# This is the "gold standard" reproduction — 
# You do not need to run this, but keep this in good shape
# so other agents can easily run a full loop of reproduction and get the paper's numbers.

set -e

cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}

python data/make_benchmarks.py
python baseline/enumerate.py --limit 1000 --output checkpoints/enumeration/results.json
python method/run_sharpasp_sr.py --output checkpoints/sharpasp_sr/results.json
python method/run_hybrid.py --enumeration-limit 1000 --output checkpoints/hybrid/results.json
bash scripts/evaluate.sh
