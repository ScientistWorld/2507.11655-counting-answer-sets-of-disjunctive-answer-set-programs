#!/usr/bin/env python3
"""Build the visible TRAIN benchmark in data/train/ (programs + exact counts).

Program families (scaled analogs of families in the paper's benchmark suite):
  qbf     exists-forall 2QBF problems in the standard disjunctive saturation
          encoding. Answer sets correspond to assignments of X for which the
          DNF matrix is valid for every Y assignment, so the exact count is
          2^|X| - #exists Y. CNF(not matrix). That projected count is computed
          with GANAK in exact mode on a formula that involves no ASP reduction,
          i.e. independently of any answer-set counter under evaluation.
  random  random non-tight disjunctive programs (with default negation, or
          positive programs with integrity constraints). Exact count by
          exhaustive clingo enumeration; programs whose answer sets cannot be
          enumerated within GT_ENUM_CAP CPU seconds are discarded.
Atom names are randomized and rule / literal order shuffled.

Calibration and selection (deterministic given SEED):
  Each candidate is run through the reference counters registered under
  --registry with a budget of MARGIN * CPU_BUDGET. Candidates on which a
  reference counter finishes between CPU_BUDGET / MARGIN and MARGIN * CPU_BUDGET
  CPU seconds are dropped, so the reference outcome under the evaluation budget
  does not hinge on small timing differences. Counts from different sources
  (ground truth, every reference counter) must agree or the candidate is
  dropped and reported.
  Slices: large_count_counting holds programs with >= 2^23 answer sets;
  hybrid_full_spectrum holds programs across small / mid / large counts. Each
  count band mixes programs the direct reference counter solves within the
  budget with programs it does not (quotas below).

Usage: python data/make_benchmarks.py [--registry checkpoints]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------- configuration
SPLIT = "train"
SEED = "train-split-2507.11655-v2"
OUT_DIR = ROOT / "data" / "train"
CACHE_PATH = OUT_DIR / ".build_cache" / "cache.json"
ID_PREFIX = "tr"

CPU_BUDGET = 10.0          # must equal the evaluators' CPU_BUDGET_SECONDS
MARGIN = 2.5               # calibration margin factor
GT_ENUM_CAP = 120.0        # CPU seconds for exhaustive clingo ground truth
GT_QBF_CAP = 60.0          # CPU seconds for the independent 2QBF ground truth
MAX_LONG_ENUM_GT = 12      # at most this many long clingo ground-truth runs per split
SMALL_MAX = 10_000         # count bands: small <= 10^4 < mid < 2^23 <= large
LARGE_MIN = 2 ** 23
ENUM_HOPELESS = 2 ** 26    # enumeration cannot finish this many answer sets in MARGIN*CPU_BUDGET

DIRECT = "sharpasp_sr"
HYBRID = "hybrid_sharpasp_sr"
ENUM = "clingo_enumeration"
HYBRID_SWITCH = 10_000     # the hybrid enumerates at most this many answer sets before switching

# (nx, ny, terms, width, max X-literals per term), seeds per entry
QBF_GRID = [
    (16, 4, 28, 4, 2), (18, 5, 33, 4, 2), (20, 5, 36, 4, 2), (22, 5, 39, 4, 2),
    (25, 5, 42, 4, 2), (26, 6, 50, 4, 2), (28, 6, 50, 4, 2), (29, 6, 56, 4, 2),
    (31, 6, 54, 4, 2), (33, 7, 64, 4, 2), (36, 7, 66, 4, 2),
    (28, 6, 42, 3, 2), (32, 6, 48, 3, 2), (36, 7, 56, 3, 2),
]
QBF_SEEDS = 3
# (atoms, rules/atom, p_disjunctive, max_pos, max_neg, p_constraint), seeds per entry
RANDOM_GRID = [
    (40, 1.8, 0.5, 2, 1, 0.0), (60, 2.2, 0.5, 2, 1, 0.0), (90, 1.8, 0.5, 2, 1, 0.0),
    (90, 2.2, 0.5, 2, 1, 0.0), (120, 2.0, 0.5, 2, 1, 0.0), (120, 2.4, 0.5, 2, 1, 0.0),
    (150, 2.2, 0.5, 2, 1, 0.0), (180, 2.4, 0.5, 2, 1, 0.0),
    (60, 1.6, 0.6, 2, 0, 0.05), (100, 1.7, 0.6, 2, 0, 0.03), (140, 1.6, 0.6, 2, 0, 0.02),
]
RANDOM_SEEDS = 3
# per-slice quotas: (band, direct reference solves?) -> number of programs
QUOTAS = {
    "hybrid_full_spectrum": {("small", True): 2, ("small", False): 3, ("mid", True): 3, ("mid", False): 3,
                             ("large", True): 5, ("large", False): 2},
    "large_count_counting": {("large", True): 7, ("large", False): 7},
}
PREFERRED_FAMILY = {"hybrid_full_spectrum": "random", "large_count_counting": "qbf"}

# ---------------------------------------------------------------- generators


def derived_seed(*parts: object) -> int:
    return int(hashlib.sha256(":".join(map(str, (SEED,) + parts)).encode()).hexdigest()[:16], 16)


def gen_qbf(rng: random.Random, nx: int, ny: int, nt: int, width: int, kxmax: int):
    terms = []
    for _ in range(nt):
        kx = rng.randint(1, kxmax)
        ky = width - kx
        xs = rng.sample(range(nx), kx)
        ys = rng.sample(range(ny), ky)
        terms.append(([(i, rng.random() < 0.5) for i in xs], [(j, rng.random() < 0.5) for j in ys]))
    rules = [([f"x{i}", f"nx{i}"], [], []) for i in range(nx)]
    for j in range(ny):
        rules += [([f"y{j}", f"ny{j}"], [], []), ([f"y{j}"], ["sat"], []), ([f"ny{j}"], ["sat"], [])]
    for xl, yl in terms:
        body = [f"x{i}" if p else f"nx{i}" for i, p in xl] + [f"y{j}" if p else f"ny{j}" for j, p in yl]
        rules.append((["sat"], body, []))
    rules.append(([], [], ["sat"]))
    return rules, {"nx": nx, "ny": ny, "terms": terms}


def gen_random(rng: random.Random, n: int, ratio: float, p_disj: float, max_pos: int, max_neg: int, p_con: float):
    atoms = [f"a{i}" for i in range(n)]
    rules = []
    for _ in range(int(round(ratio * n))):
        if rng.random() < p_con:
            head = []
        else:
            head = rng.sample(atoms, 2 if rng.random() < p_disj else 1)
        rest = [a for a in atoms if a not in head]
        pos = rng.sample(rest, rng.randint(0, max_pos) if head else 2)
        rest = [a for a in rest if a not in pos]
        neg = rng.sample(rest, rng.randint(0, max_neg))
        rules.append((head, pos, neg))
    return rules


def loop_atom_count(rules) -> int:
    graph: dict[str, set[str]] = {}
    for head, pos, _ in rules:
        for h in head:
            graph.setdefault(h, set()).update(pos)
            for b in pos:
                graph.setdefault(b, set())
    index, low, on, stack, loops, counter = {}, {}, set(), [], set(), 0
    for root in sorted(graph):
        if root in index:
            continue
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on.add(root)
        work = [(root, sorted(graph[root]))]
        while work:
            v, succ = work[-1]
            if succ:
                w = succ.pop()
                if w not in index:
                    index[w] = low[w] = counter
                    counter += 1
                    stack.append(w)
                    on.add(w)
                    work.append((w, sorted(graph[w])))
                elif w in on:
                    low[v] = min(low[v], index[w])
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                if len(comp) > 1 or comp[0] in graph[comp[0]]:
                    loops.update(comp)
    return len(loops)


def render(rules, rng: random.Random) -> str:
    atoms = sorted({a for head, pos, neg in rules for a in head + pos + neg})
    perm = list(range(1, len(atoms) + 1))
    rng.shuffle(perm)
    name = {a: f"v{perm[k]}" for k, a in enumerate(atoms)}
    order = list(range(len(rules)))
    rng.shuffle(order)
    lines = []
    for idx in order:
        head, pos, neg = rules[idx]
        h = [name[a] for a in head]
        rng.shuffle(h)
        body = [name[a] for a in pos] + [f"not {name[a]}" for a in neg]
        rng.shuffle(body)
        text = " | ".join(h)
        if body:
            text += (" :- " if h else ":- ") + ", ".join(body)
        lines.append(text + ".")
    return "\n".join(lines) + "\n"


def candidates() -> list[dict]:
    out = []
    for g, (nx, ny, nt, width, kxmax) in enumerate(QBF_GRID):
        for s in range(QBF_SEEDS):
            rng = random.Random(derived_seed("qbf", g, s))
            rules, meta = gen_qbf(rng, nx, ny, nt, width, kxmax)
            out.append({"key": f"qbf-{g}-{s}", "family": "qbf", "params": [nx, ny, nt, width, kxmax],
                        "text": render(rules, rng), "meta": meta, "loop_atoms": loop_atom_count(rules),
                        "rules": len(rules)})
    for g, (n, ratio, p_disj, max_pos, max_neg, p_con) in enumerate(RANDOM_GRID):
        for s in range(RANDOM_SEEDS):
            rng = random.Random(derived_seed("random", g, s))
            rules = gen_random(rng, n, ratio, p_disj, max_pos, max_neg, p_con)
            out.append({"key": f"random-{g}-{s}", "family": "random", "params": [n, ratio, p_disj, max_pos, max_neg, p_con],
                        "text": render(rules, rng), "meta": None, "loop_atoms": loop_atom_count(rules),
                        "rules": len(rules)})
    # interleave: all seed-0 programs first, then seed 1, ... (a build deadline cuts uniformly)
    out.sort(key=lambda c: (int(c["key"].rsplit("-", 1)[1]), c["family"], int(c["key"].split("-")[1])))
    return out

# ---------------------------------------------------------------- running tools


def run_command(command: list[str], cpu_budget: float, wall_limit: float) -> dict:
    soft = int(math.ceil(cpu_budget)) + 1

    def _limit() -> None:
        resource.setrlimit(resource.RLIMIT_CPU, (soft, soft + 1))

    cmd = [sys.executable if (i == 0 and part == "python") else part for i, part in enumerate(command)]
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = time.monotonic()
    timed_out = False
    proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, preexec_fn=_limit, start_new_session=True)
    try:
        out, _ = proc.communicate(timeout=wall_limit)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
        out, _ = proc.communicate()
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except OSError:
        pass
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime)
    text = out.decode("utf-8", errors="replace") if out else ""
    value = None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not timed_out and proc.returncode == 0 and lines and re.fullmatch(r"\d+", lines[-1]):
        value = int(lines[-1])
    return {"value": value, "cpu": round(cpu, 3), "wall": round(time.monotonic() - start, 3),
            "returncode": proc.returncode, "timed_out": timed_out}


CLINGO_ENUM = (
    "import sys, clingo\n"
    "ctl = clingo.Control(['0', '--warn=none'])\n"
    "ctl.add('base', [], open(sys.argv[1]).read())\n"
    "ctl.ground([('base', [])])\n"
    "r = ctl.solve()\n"
    "sys.exit(1) if not r.exhausted else print(int(ctl.statistics['summary']['models']['enumerated']))\n"
)


def ganak_binary() -> str:
    for cand in (os.environ.get("GANAK_BIN"), str(ROOT / "data" / "downloads" / "ganak"), shutil.which("ganak")):
        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    raise FileNotFoundError("GANAK binary not found (run scripts/download.sh)")


def qbf_ground_truth(meta: dict, workdir: Path) -> tuple[int | None, float]:
    nx, ny = meta["nx"], meta["ny"]
    clauses = []
    for xl, yl in meta["terms"]:
        clause = [-(i + 1) if p else (i + 1) for i, p in xl] + [-(nx + j + 1) if p else (nx + j + 1) for j, p in yl]
        clauses.append(clause)
    cnf = workdir / "qbf_gt.cnf"
    with open(cnf, "w") as handle:
        handle.write(f"p cnf {nx + ny} {len(clauses)}\n")
        handle.write("c p show " + " ".join(str(i + 1) for i in range(nx)) + " 0\n")
        for clause in clauses:
            handle.write(" ".join(map(str, clause)) + " 0\n")
    proc_cmd = [ganak_binary(), "--prob", "0", "--verb", "0", "--seed", "0", str(cnf)]
    run = run_ganak(proc_cmd, GT_QBF_CAP)
    if run[0] is None:
        return None, run[1]
    return 2 ** nx - run[0], run[1]


def run_ganak(cmd: list[str], cap: float) -> tuple[int | None, float]:
    soft = int(math.ceil(cap)) + 1
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=cap * 1.5 + 10,
                              preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_CPU, (soft, soft + 1)))
        out = proc.stdout
    except subprocess.TimeoutExpired:
        out = ""
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime)
    m = re.search(r"^c s exact arb int (\d+)\s*$", out, re.MULTILINE)
    return (int(m.group(1)) if m else None), round(cpu, 3)

# ---------------------------------------------------------------- calibration


def load_registry(registry: Path) -> dict[str, list[str]]:
    counters = {}
    for name in (ENUM, DIRECT, HYBRID):
        spec = registry / name / "counter.json"
        if not spec.exists():
            raise SystemExit(f"reference counter {name} not registered under {registry}")
        counters[name] = json.loads(spec.read_text())["command"]
    return counters


def band_of(count: int) -> str:
    if count <= SMALL_MAX:
        return "small"
    return "large" if count >= LARGE_MIN else "mid"


LONG_ENUM_RUNS = [0]


def calibrate(cand: dict, counters: dict, entry: dict, workdir: Path) -> None:
    """Fill entry with ground truth and reference timings (idempotent per field)."""
    prog = workdir / "program.lp"
    prog.write_text(cand["text"])
    cap = CPU_BUDGET * MARGIN
    runs = entry.setdefault("runs", {})
    known = []
    if cand["family"] == "qbf" and "gt" not in entry:
        entry["gt"], entry["gt_cpu"] = qbf_ground_truth(cand["meta"], workdir)
        entry["gt_source"] = "qbf_independent_projected_count"
    if entry.get("gt") is not None:
        known.append(entry["gt"])
    if DIRECT not in runs:
        runs[DIRECT] = run_command(counters[DIRECT] + [str(prog)], cap, cap * 2 + 10)
    if runs[DIRECT]["value"] is not None:
        known.append(runs[DIRECT]["value"])
    if ENUM not in runs:
        if known and min(known) >= ENUM_HOPELESS:
            runs[ENUM] = {"value": None, "cpu": None, "skipped": "count >= 2^26"}
        else:
            runs[ENUM] = run_command(counters[ENUM] + [str(prog)], cap, cap * 2 + 10)
    if runs[ENUM].get("value") is not None:
        known.append(runs[ENUM]["value"])
    if HYBRID not in runs:
        direct_slow = runs[DIRECT]["value"] is None
        if direct_slow and (runs[ENUM].get("value") is None or runs[ENUM]["value"] > HYBRID_SWITCH):
            runs[HYBRID] = {"value": None, "cpu": None, "skipped": "count > switch and direct counter slow"}
        else:
            runs[HYBRID] = run_command(counters[HYBRID] + [str(prog)], cap, cap * 2 + 10)
    if cand["family"] == "random" and "gt" not in entry:
        if runs[ENUM].get("value") is not None:
            entry["gt"], entry["gt_cpu"], entry["gt_source"] = runs[ENUM]["value"], runs[ENUM]["cpu"], "clingo_enumeration"
        elif runs[DIRECT]["value"] is not None and runs[DIRECT]["value"] > 15_000_000:
            entry["gt"], entry["gt_source"] = None, "too_many_answer_sets_for_independent_enumeration"
        elif LONG_ENUM_RUNS[0] >= MAX_LONG_ENUM_GT:
            entry["gt"], entry["gt_source"] = None, "long_enumeration_quota_exhausted"
        else:
            LONG_ENUM_RUNS[0] += 1
            r = run_command([sys.executable, "-c", CLINGO_ENUM, str(prog)], GT_ENUM_CAP, GT_ENUM_CAP * 2 + 10)
            entry["gt"], entry["gt_cpu"], entry["gt_source"] = r["value"], r["cpu"], "clingo_enumeration_long"


def classify(entry: dict) -> tuple[bool, str, bool]:
    """Return (eligible, reason, direct_solved)."""
    gt = entry.get("gt")
    if gt is None:
        return False, "no independent ground truth", False
    runs = entry["runs"]
    for name in (ENUM, DIRECT, HYBRID):
        run = runs[name]
        if run.get("value") is not None and run["value"] != gt:
            return False, f"COUNT MISMATCH {name}: {run['value']} vs ground truth {gt}", False
    fast_limit = CPU_BUDGET / MARGIN
    outcome = {}
    for name in (ENUM, DIRECT, HYBRID):
        run = runs[name]
        if run.get("value") is None:
            outcome[name] = False
        elif run["cpu"] <= fast_limit:
            outcome[name] = True
        else:
            return False, f"borderline {name} cpu={run['cpu']}", False
    return True, "ok", outcome[DIRECT]


def select(eligible: list[dict]) -> dict[str, list[dict]]:
    rng = random.Random(derived_seed("select"))
    pool = sorted(eligible, key=lambda e: e["key"])
    rng.shuffle(pool)
    used: set[str] = set()
    picks: dict[str, list[dict]] = {exp: [] for exp in QUOTAS}
    for exp in ("hybrid_full_spectrum", "large_count_counting"):
        for (band, solved), n in QUOTAS[exp].items():
            group = [e for e in pool if e["key"] not in used and e["band"] == band and e["direct_solved"] == solved]
            group.sort(key=lambda e: e["family"] != PREFERRED_FAMILY[exp])  # stable: preferred family first
            chosen = group[:n]
            if len(chosen) < n:  # top up from the same band with the other outcome
                extra = [e for e in pool if e["key"] not in used and e["band"] == band and e not in chosen]
                chosen += extra[: n - len(chosen)]
            for e in chosen:
                used.add(e["key"])
                picks[exp].append(e)
    return picks

# ---------------------------------------------------------------- output


def write_outputs(picks: dict[str, list[dict]], cands: dict[str, dict], report: dict) -> None:
    inst_dir = OUT_DIR / "instances"
    if inst_dir.exists():
        shutil.rmtree(inst_dir)
    inst_dir.mkdir(parents=True)
    rng = random.Random(derived_seed("ids"))
    chosen = [(exp, e) for exp in sorted(picks) for e in picks[exp]]
    rng.shuffle(chosen)
    manifest = []
    for k, (exp, e) in enumerate(chosen):
        iid = f"{ID_PREFIX}{k:03d}"
        cand = cands[e["key"]]
        (inst_dir / f"{iid}.lp").write_text(cand["text"])
        manifest.append({"id": iid, "path": f"data/train/instances/{iid}.lp", "slice": exp,
                         "family": cand["family"], "count": str(e["gt"]), "loop_atoms": cand["loop_atoms"],
                         "rules": cand["rules"]})
    manifest.sort(key=lambda m: m["id"])
    (OUT_DIR / "manifest.json").write_text(json.dumps(
        {"split": SPLIT, "cpu_budget_seconds": CPU_BUDGET, "instances": manifest}, indent=2) + "\n")
    (OUT_DIR / "build_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default=str(ROOT / "checkpoints"))
    parser.add_argument("--deadline-minutes", type=float, default=80.0,
                        help="stop calibrating new candidates after this long (cached ones are reused)")
    args = parser.parse_args()
    counters = load_registry(Path(args.registry))
    cands = {c["key"]: c for c in candidates()}
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    cache = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}
    digest = {k: hashlib.sha256(c["text"].encode()).hexdigest() for k, c in cands.items()}
    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix=f"build_{SPLIT}_") as tmp:
        for n, (key, cand) in enumerate(cands.items()):
            entry = cache.get(key)
            if entry is None or entry.get("digest") != digest[key]:
                entry = {"digest": digest[key]}
            if entry.get("gt_source") == "clingo_enumeration_long":
                LONG_ENUM_RUNS[0] += 1
            complete = "runs" in entry and all(n in entry["runs"] for n in (ENUM, DIRECT, HYBRID)) and "gt" in entry
            if not complete and time.time() - t0 > args.deadline_minutes * 60:
                print(f"[{SPLIT} build] deadline reached; skipping {key}", flush=True)
                continue
            calibrate(cand, counters, entry, Path(tmp))
            cache[key] = entry
            CACHE_PATH.write_text(json.dumps(cache, indent=1, sort_keys=True))
            runs = entry["runs"]
            for rname, run in runs.items():
                if run.get("value") is None and not run.get("skipped") and not run.get("timed_out") \
                        and (run.get("cpu") or 0) < CPU_BUDGET * MARGIN - 1:
                    print(f"!!! {key}: {rname} exited rc={run.get('returncode')} without a count "
                          f"after {run.get('cpu')}s CPU (crash?)", flush=True)
            print(f"[{SPLIT} build {n + 1}/{len(cands)} {time.time() - t0:.0f}s] {key} LA={cand['loop_atoms']} "
                  f"gt={entry.get('gt')} ({entry.get('gt_source')}, {entry.get('gt_cpu')}s) "
                  + " ".join(f"{k}={v.get('value') is not None}/{v.get('cpu')}" for k, v in runs.items()), flush=True)

    eligible, reasons = [], {}
    for key, entry in cache.items():
        if key not in cands or "runs" not in entry or "gt" not in entry:
            continue
        ok, why, solved = classify(entry)
        reasons[key] = why
        if why.startswith("COUNT MISMATCH"):
            print(f"!!! {key}: {why}", flush=True)
        if ok:
            eligible.append({"key": key, "family": cands[key]["family"], "gt": entry["gt"],
                             "band": band_of(entry["gt"]), "direct_solved": solved})
    picks = select(eligible)
    report = {
        "split": SPLIT,
        "cpu_budget_seconds": CPU_BUDGET,
        "margin": MARGIN,
        "candidates": len(cands),
        "eligible": len(eligible),
        "reasons": reasons,
        "mismatches": {k: v for k, v in reasons.items() if v.startswith("COUNT MISMATCH")},
        "selected": {exp: [{"key": e["key"], "family": e["family"], "band": e["band"],
                            "direct_solved": e["direct_solved"]} for e in picks[exp]] for exp in picks},
        "calibration": {k: {"gt_source": v.get("gt_source"), "gt_cpu": v.get("gt_cpu"),
                            "runs": {n: {"solved": r.get("value") is not None, "cpu": r.get("cpu")}
                                     for n, r in v.get("runs", {}).items()}} for k, v in cache.items() if k in cands},
    }
    write_outputs(picks, cands, report)
    for exp, items in picks.items():
        print(f"[{SPLIT}] {exp}: {len(items)} programs "
              f"(direct-solved {sum(e['direct_solved'] for e in items)}, "
              f"bands {sorted({e['band'] for e in items})})")


if __name__ == "__main__":
    main()
