"""Paired timings for the real exact optimization, independent of score writing."""
import importlib.util
from pathlib import Path
import random
import statistics
import time

from audit import AUDIT, ROOT, read, write
from data.asp import load_program
from method.sharpasp_sr import reduction


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reference = load('method.sharpasp_sr.audit_original_counter', AUDIT / 'original/counter.py')
better = load('method.sharpasp_sr.audit_better_counter', AUDIT / 'component_counter.py')
manifest = read(ROOT / 'data/benchmarks.json')
programs = [(item['name'], load_program(ROOT / item['path'])) for item in manifest['instances']]
expected = read(AUDIT / 'reference_seed_0/direct_results.json')['instances']
results = {'repeats': 7, 'cache_policy': 'clear optimization caches before each instance; original caches are local to each call',
           'timings_include': 'program reduction plus ordinary and projected counting on all six unchanged programs',
           'runs': []}
for seed in range(7):
    order = [('reference', reference), ('better', better)]
    random.Random(seed).shuffle(order)
    for name, module in order:
        reduction.count_models = module.count_models
        reduction.projected_count = module.projected_count
        total = 0.
        for instance_name, program in programs:
            if module is better:
                module.rec.cache_clear()
                module.sat.cache_clear()
            started = time.perf_counter()
            got = reduction.sharpasp_sr_count(program)
            total += time.perf_counter() - started
            assert got['answer_sets'] == expected[instance_name]['answer_sets']
            for field in ('loop_atoms', 'phi1_clauses', 'phi2_clauses'):
                assert got[field] == expected[instance_name][field]
        results['runs'].append({'seed': seed, 'method': name, 'seconds_all_six': total})
for name in ('reference', 'better'):
    values = [item['seconds_all_six'] for item in results['runs'] if item['method'] == name]
    results[name] = {'median_seconds': statistics.median(values), 'min_seconds': min(values), 'max_seconds': max(values)}
results['median_speedup'] = results['reference']['median_seconds'] / results['better']['median_seconds']
write(AUDIT / 'better_component_counter/paired_timing.json', results)
print(results)
