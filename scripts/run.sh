#!/bin/bash
# Hardening job (iteration 11). Builds the train and hidden-test benchmarks
# (ground truth + reference calibration, cached and resumable), then scores the
# reference counters, better/weaker variants and shortcuts through the evaluators.
# After this iteration run.sh is reset to: bash scripts/reproduce.sh && python validate.py

set -uo pipefail
cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}

echo "== environment"
nproc; python --version
python -c "import clingo; print('clingo', clingo.__version__)" || { echo "clingo missing: environment/setup.sh not applied" >&2; exit 3; }
test -x data/downloads/ganak || { echo "data/downloads/ganak missing: run scripts/download.sh" >&2; exit 3; }
data/downloads/ganak --version 2>&1 | head -1

set -e
H=redteam/hardening
D=checkpoints/_eval_details
mkdir -p $H/details

echo "== self-test and registration"
python method/selftest.py
python method/register_counters.py --registry checkpoints
python baseline/enumerate.py --register --registry checkpoints

echo "== build train benchmark"
python data/make_benchmarks.py --registry checkpoints --deadline-minutes 75
echo "== build hidden test benchmark"
python eval/test/build_hidden.py --registry checkpoints --deadline-minutes 75

echo "== reference: hidden test"
bash scripts/evaluate_test.sh
cp scoring/scores_test.json /tmp/scores_test_reference.json
echo "== reference: train"
bash scripts/evaluate_train.sh
cp scoring/scores_train.json scoring/scores.json

echo "== variants: hidden test"
python eval/test/evaluate.py --registry $H/registry_variants --output $H/scores_test_variants.json --details-dir $D/test_variants

echo "== shortcuts: hidden test (one shortcut forges scoring/scores_test.json; the evaluator overwrites it)"
python eval/test/evaluate.py --registry $H/registry_shortcuts --output scoring/scores_test.json --details-dir $D/test_shortcuts
cp scoring/scores_test.json $H/scores_test_shortcuts.json
cp /tmp/scores_test_reference.json scoring/scores_test.json

echo "== reference repeat: hidden test (run-to-run spread)"
python eval/test/evaluate.py --output $H/scores_test_reference_repeat.json --details-dir $D/test_repeat

echo "== variants: train"
python eval/train/evaluate.py --registry $H/registry_variants --output $H/scores_train_variants.json --details-dir $D/train_variants

for d in test train test_variants test_shortcuts test_repeat train_variants; do
  mkdir -p $H/details/$d && cp $D/$d/*.json $H/details/$d/ 2>/dev/null || true
done

set +e
python validate.py
echo "== done"
