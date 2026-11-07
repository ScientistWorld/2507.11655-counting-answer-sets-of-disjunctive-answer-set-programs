#!/bin/bash
set -euo pipefail
cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}
python redteam/audit.py shortcut_wrong_huge_count
