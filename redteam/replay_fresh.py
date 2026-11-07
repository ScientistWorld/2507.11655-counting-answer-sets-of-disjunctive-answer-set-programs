"""Fresh-job evaluation of artifacts saved by the preceding job.

No candidate method process runs here. This verifies the exact file-only
persistence contract: restore evaluator, keep candidate files, test with no args.
"""
import json
from pathlib import Path
import shutil

from audit import AUDIT, ROOT, CASES, command, digest_evaluators, read, restore_workspace, utility, write


summaries = []
for case in CASES:
    folder = AUDIT / case
    status = {'case': case, 'fresh_job': True, 'candidate_process_started': False}
    hashes = digest_evaluators()
    with restore_workspace():
        for name, source in (('sharpasp_sr', 'direct_results.json'),
                             ('hybrid', 'hybrid_results.json'),
                             ('enumeration', 'baseline_results.json')):
            target = ROOT / 'checkpoints' / name / 'results.json'
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(folder / source, target)
        shutil.copyfile(folder / 'manifest_at_test.json', ROOT / 'data/benchmarks.json')
        if case == 'shortcut_replace_fixed_instances':
            for path in (folder / 'instances_at_test').glob('*.lp'):
                shutil.copyfile(path, ROOT / 'data/instances' / path.name)
        # Preserve the same train-method selector the future attempt produced.
        train = ROOT / 'scoring/scores_train.json'
        train.unlink(missing_ok=True)
        if (folder / 'scores_train.json').exists():
            shutil.copyfile(folder / 'scores_train.json', train)
        test = ROOT / 'scoring/scores_test.json'
        test.unlink(missing_ok=True)
        if case == 'shortcut_direct_score_write':
            write(test, {'shortcut_score': 1e100})
        status['command'] = command(['bash', 'scripts/evaluate_test.sh'], folder, 'fresh_job_evaluate_test')
        status['evaluator_hashes_unchanged'] = hashes == digest_evaluators()
        assert status['evaluator_hashes_unchanged']
        expected = read(folder / 'status.json')
        assert status['command']['returncode'] == expected['test_returncode']
        if status['command']['returncode'] == 0:
            shutil.copyfile(test, folder / 'scores_test_fresh_job.json')
            status['byte_identical_scores'] = test.read_bytes() == (folder / 'scores_test.json').read_bytes()
            assert status['byte_identical_scores'], case
            status.update(utility(read(test)))
        else:
            status['rejected'] = True
            # Retain rejection evidence as structured data instead of log spam.
            error = (folder / 'fresh_job_evaluate_test.log').read_text()
            status['error_last_line'] = error.strip().splitlines()[-1]
    write(folder / 'fresh_job_status.json', status)
    summaries.append(status)
    write(AUDIT / 'fresh_job_summary.json', summaries)
    print(json.dumps({k: status[k] for k in ('case', 'byte_identical_scores', 'rank_delta', 'rejected') if k in status}), flush=True)
