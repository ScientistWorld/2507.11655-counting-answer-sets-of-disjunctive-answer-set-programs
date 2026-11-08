#!/bin/bash
# Hardening job (iteration 11), resumable: each finished phase leaves a marker in
# checkpoints/_job_markers/ and is skipped on resubmission. Builds are skipped when
# their outputs exist, so the frozen benchmark cannot change between phases.
# After this iteration run.sh is reset to: bash scripts/reproduce.sh && python validate.py

set -uo pipefail
cd /home/user
export PYTHONPATH=/home/user:${PYTHONPATH:-}

echo "== environment"
nproc; python --version
python -c "import clingo; print('clingo', clingo.__version__)" || { echo "clingo missing: environment/setup.sh not applied" >&2; exit 3; }
test -x data/downloads/ganak || { echo "data/downloads/ganak missing: run scripts/download.sh" >&2; exit 3; }

set -e
H=redteam/hardening
D=checkpoints/_eval_details
M=checkpoints/_job_markers
mkdir -p $H/details $M
phase() { test -f "$M/$1.done" && { echo "== skip $1 (done)"; return 1; }; echo "== $1"; return 0; }
done_() { touch "$M/$1.done"; }

python method/selftest.py
python method/register_counters.py --registry checkpoints
python baseline/enumerate.py --register --registry checkpoints

test -f data/train/manifest.json || python data/make_benchmarks.py --registry checkpoints --deadline-minutes 75
test -f eval/test/answers.json || python eval/test/build_hidden.py --registry checkpoints --deadline-minutes 75

if phase reference_test; then
  bash scripts/evaluate_test.sh && cp scoring/scores_test.json $H/scores_test_reference.json && done_ reference_test
fi
if phase reference_train; then
  bash scripts/evaluate_train.sh && cp scoring/scores_train.json scoring/scores.json && done_ reference_train
fi
if phase variants_test; then
  python eval/test/evaluate.py --registry $H/registry_variants --output $H/scores_test_variants.json --details-dir $D/test_variants
  done_ variants_test
fi
if phase shortcuts_test; then
  # one shortcut forges scoring/scores_test.json mid-run; the evaluator overwrites it at the end
  python eval/test/evaluate.py --registry $H/registry_shortcuts --output scoring/scores_test.json --details-dir $D/test_shortcuts
  cp scoring/scores_test.json $H/scores_test_shortcuts.json
  cp $H/scores_test_reference.json scoring/scores_test.json
  done_ shortcuts_test
fi
if phase reference_repeat; then
  python eval/test/evaluate.py --output $H/scores_test_reference_repeat.json --details-dir $D/test_repeat
  done_ reference_repeat
fi
if phase variants_train; then
  python eval/train/evaluate.py --registry $H/registry_variants --output $H/scores_train_variants.json --details-dir $D/train_variants
  done_ variants_train
fi

for d in test train test_variants test_shortcuts test_repeat train_variants; do
  mkdir -p $H/details/$d && cp $D/$d/*.json $H/details/$d/ 2>/dev/null || true
done

set +e
python validate.py
echo "== done"
