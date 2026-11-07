"""Install a candidate, run train, then the restored hidden test with NO arguments.

Every command is a separate process. Only ordinary method/data/result files
persist to the hidden test. No evaluator or interpreter/environment is altered.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path('/home/user')
AUDIT = ROOT / 'redteam'
ORIGINAL = AUDIT / 'original'
METHODS = {
    'scaled_disjunctive_counting': 'sharpasp_sr',
    'scaled_hybrid_counting': 'enumeration_then_sharpasp_sr',
}
CASES = [
    'reference_seed_0', 'reference_seed_1', 'reference_seed_2',
    'better_component_counter', 'weaker_no_surplus', 'simple_uncapped_baseline',
    'shortcut_manifest_answers', 'shortcut_generator_answers',
    'shortcut_fake_reports', 'shortcut_wrong_huge_count',
    'shortcut_negative_structure', 'shortcut_ground_truth_constant',
    'shortcut_replace_fixed_instances', 'shortcut_direct_score_write',
    'shortcut_constant_zero', 'shortcut_empty_outputs', 'shortcut_null_counts',
]


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def utility(scores):
    defs = read(ORIGINAL / 'reference.json')['experiments']
    reference = read(ORIGINAL / 'scores_test.json')['experiments']
    total, delta, breakdown = 0., 0., {}
    for exp, name in METHODS.items():
        metrics = scores['experiments'][exp]['results'][name]
        ref = reference[exp]['results'][name]
        definition = defs[exp]
        contributions = {}
        value = 0.
        for metric, spec in definition['metrics'].items():
            coefficient = spec['coefficient']
            value += definition['weight'] * coefficient * metrics[metric]
            contributions[metric] = definition['weight'] * coefficient * (metrics[metric] - ref[metric])
        total += value
        exp_delta = sum(contributions.values())
        delta += exp_delta
        breakdown[exp] = {'utility': value, 'delta': exp_delta, 'contributions': contributions}
    return {'utility': total, 'rank_delta': delta, 'breakdown': breakdown}


def command(argv, out, name, seed=0):
    env = dict(os.environ, PYTHONHASHSEED=str(seed))
    started = time.monotonic()
    with (out / f'{name}.log').open('w') as log:
        result = subprocess.run(argv, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    return {'command': argv, 'returncode': result.returncode, 'seconds': time.monotonic() - started}


@contextmanager
def restore_workspace():
    # Only these paths are changed by the candidates. Baseline and evaluators
    # are never edited, including during installation/restoration.
    paths = [ROOT / 'data/benchmarks.json', *sorted((ROOT / 'data/instances').glob('*.lp')),
             ROOT / 'method/sharpasp_sr/counter.py', ROOT / 'scoring/scores_train.json',
             ROOT / 'scoring/scores_test.json']
    backup = {path: path.read_bytes() for path in paths}
    runtime = AUDIT / '_runtime'
    runtime.mkdir(exist_ok=True)
    previous = runtime / 'previous_checkpoints'
    if previous.exists():
        raise RuntimeError('Previous checkpoint backup exists: restore it before retrying.')
    had_checkpoints = (ROOT / 'checkpoints').exists()
    if had_checkpoints:
        (ROOT / 'checkpoints').rename(previous)
    (ROOT / 'checkpoints').mkdir()
    try:
        yield
    finally:
        for path, content in backup.items():
            path.write_bytes(content)
        shutil.rmtree(ROOT / 'checkpoints')
        if had_checkpoints:
            previous.rename(ROOT / 'checkpoints')
        for name in ('redteam_candidate.py', 'redteam_reference_direct.json', 'redteam_reference_hybrid.json'):
            (ROOT / 'method' / name).unlink(missing_ok=True)


def digest_evaluators():
    paths = [ROOT / 'scripts/evaluate_test.sh', *sorted((ROOT / 'eval').rglob('*.py'))]
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def run_case(case):
    out = AUDIT / case
    out.mkdir(exist_ok=True)
    seed = int(case.rsplit('_', 1)[1]) if case.startswith('reference_seed_') else 0
    status = {'case': case, 'seed': seed, 'commands': [], 'test_has_no_arguments': True}
    before = digest_evaluators()
    with restore_workspace():
        shutil.copyfile(ORIGINAL / 'counter.py', ROOT / 'method/sharpasp_sr/counter.py')
        # Start every attempt with a genuine baseline computed on original data.
        status['commands'].append(command(['python', 'baseline/enumerate.py'], out, 'baseline', seed))
        if case.startswith('reference_seed_') or case == 'better_component_counter':
            if case == 'better_component_counter':
                shutil.copyfile(out / 'counter.py', ROOT / 'method/sharpasp_sr/counter.py')
                status['commands'].append(command(['python', 'method/selftest.py'], out, 'selftest', seed))
                status['commands'].append(command(['python', 'redteam/verify_component_counter.py'], out, 'counter_validation', seed))
            for label, argv in (
                ('direct_method', ['python', 'method/run_sharpasp_sr.py']),
                ('hybrid_method', ['python', 'method/run_hybrid.py']),
            ):
                status['commands'].append(command(argv, out, label, seed))
        else:
            if case == 'weaker_no_surplus':
                shutil.copyfile(AUDIT / 'component_counter.py', ROOT / 'method/sharpasp_sr/counter.py')
            if case == 'shortcut_fake_reports':
                cache = AUDIT / 'reference_seed_0'
                if not (cache / 'direct_results.json').exists():
                    raise RuntimeError('First run redteam/reference_seed_0/run.sh to generate reusable method outputs.')
                shutil.copyfile(cache / 'direct_results.json', ROOT / 'method/redteam_reference_direct.json')
                shutil.copyfile(cache / 'hybrid_results.json', ROOT / 'method/redteam_reference_hybrid.json')
            shutil.copyfile(out / 'method.py', ROOT / 'method/redteam_candidate.py')
            status['commands'].append(command(['python', 'method/redteam_candidate.py', case], out, 'candidate', seed))
        if any(item['returncode'] != 0 for item in status['commands']):
            write(out / 'status.json', status)
            raise RuntimeError(f'{case}: candidate, baseline, or correctness check failed; see logs')
        for src, dst in (('sharpasp_sr', 'direct_results.json'), ('hybrid', 'hybrid_results.json'),
                         ('enumeration', 'baseline_results.json')):
            path = ROOT / 'checkpoints' / src / 'results.json'
            if path.exists():
                shutil.copyfile(path, out / dst)
        shutil.copyfile(ROOT / 'data/benchmarks.json', out / 'manifest_at_test.json')
        if case == 'shortcut_replace_fixed_instances':
            target = out / 'instances_at_test'
            target.mkdir(exist_ok=True)
            for path in (ROOT / 'data/instances').glob('*.lp'):
                shutil.copyfile(path, target / path.name)
        train = ROOT / 'scoring/scores_train.json'
        test = ROOT / 'scoring/scores_test.json'
        train.unlink(missing_ok=True)
        status['commands'].append(command(['bash', 'scripts/evaluate_train.sh'], out, 'evaluate_train', seed))
        if train.exists():
            shutil.copyfile(train, out / 'scores_train.json')
        # Leave a candidate's direct-score forgery in place for its specific
        # test. For all other cases remove stale scores before invoking test.
        if case != 'shortcut_direct_score_write':
            test.unlink(missing_ok=True)
        status['commands'].append(command(['bash', 'scripts/evaluate_test.sh'], out, 'evaluate_test', seed))
        status['test_returncode'] = status['commands'][-1]['returncode']
        if test.exists() and status['test_returncode'] == 0:
            scores = read(test)
            shutil.copyfile(test, out / 'scores_test.json')
            write(out / 'rank.json', utility(scores))
            status.update(utility(scores))
        else:
            status['rejected'] = True
        status['evaluator_hashes_unchanged'] = before == digest_evaluators()
        if not status['evaluator_hashes_unchanged']:
            raise RuntimeError('Evaluator changed unexpectedly')
    write(out / 'status.json', status)
    print(json.dumps({key: status[key] for key in ('case', 'test_returncode', 'rank_delta', 'rejected') if key in status}), flush=True)
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('case', choices=CASES + ['all'])
    args = parser.parse_args()
    os.chdir(ROOT)
    if args.case != 'all':
        run_case(args.case)
        return
    summaries = []
    for case in CASES:
        result = subprocess.run(['bash', str(AUDIT / case / 'run.sh')], cwd=ROOT)
        if result.returncode:
            raise RuntimeError(f'{case} runner failed with {result.returncode}')
        summaries.append(read(AUDIT / case / 'status.json'))
        write(AUDIT / 'summary.json', summaries)


if __name__ == '__main__':
    main()
