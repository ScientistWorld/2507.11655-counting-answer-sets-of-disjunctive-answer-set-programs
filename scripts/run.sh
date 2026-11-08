#!/bin/bash
# Final hardening job (iteration 11): reproduce the reference end to end from the
# final code (train + hidden test), then score the better/weaker variants on the
# enlarged train split (train/test consistency check).
# After this job run.sh is reset to: bash scripts/reproduce.sh && python validate.py

set -uo pipefail
cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}
python -c "import clingo; print('clingo', clingo.__version__)" || { echo "clingo missing" >&2; exit 3; }

set -e
H=redteam/hardening
bash scripts/reproduce.sh
cp scoring/scores_test.json $H/scores_test_reference_final_run.json
python eval/train/evaluate.py --registry $H/registry_variants --output $H/scores_train_variants.json --details-dir checkpoints/_eval_details/train_variants
rm -rf $H/details/train $H/details/train_variants $H/details/test_final_run
mkdir -p $H/details/train $H/details/train_variants $H/details/test_final_run
cp checkpoints/_eval_details/train/*.json $H/details/train/
cp checkpoints/_eval_details/train_variants/*.json $H/details/train_variants/
cp checkpoints/_eval_details/test/*.json $H/details/test_final_run/

set +e
python validate.py
echo "== done"
