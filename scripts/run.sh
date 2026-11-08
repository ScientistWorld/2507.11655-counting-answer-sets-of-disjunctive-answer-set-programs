#!/bin/bash
# Job script: reproduces the reference end to end inside the compute container
# (no internet; data/downloads/ganak must have been fetched by scripts/download.sh).
#   - self-tests sharpASP-sR, registers clingo_enumeration, sharpasp_sr, hybrid_sharpasp_sr
#   - scores every registered counter on the train programs and on the hidden test programs
# The hardening checks of iteration 11 (variants, shortcuts) are reproducible with
#   python eval/test/evaluate.py --registry redteam/hardening/registry_variants --output /tmp/v.json
#   python eval/test/evaluate.py --registry redteam/hardening/registry_shortcuts --output /tmp/s.json

set -e

cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}

bash scripts/reproduce.sh
python validate.py --compare
