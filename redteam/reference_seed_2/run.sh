#!/bin/bash
set -euo pipefail
cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}
python redteam/audit.py reference_seed_2
