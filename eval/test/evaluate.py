#!/usr/bin/env python3
"""Hidden-test evaluator for exact answer-set counting.

Runs every counter registered under ``checkpoints/<name>/counter.json`` on the
hidden programs in ``eval/test/instances/`` under a fixed per-instance budget
and scores the integers the counters print. Nothing a counter writes besides
its printed count is read; every scored number is recomputed here.

Counter contract (identical to the train evaluator):
  checkpoints/<name>/counter.json = {"command": ["python", "path/to/counter.py", ...]}
  The evaluator appends the path of one ground ASP program and runs the command
  from the workspace root. The counter prints the exact number of answer sets as
  the last non-empty stdout line and exits 0. Printing nothing (or exiting
  non-zero) means "no answer".

Budget (fixed here, identical for every counter, including baselines):
  CPU_BUDGET_SECONDS of CPU time per program (counter process plus all of its
  waited-for child processes), with a hard wall-clock kill at WALL_LIMIT_SECONDS.

Scoring per experiment slice:
  solved_instances       programs whose exact count was printed within budget
  max_log2_count_solved  log2 of the largest count among solved programs
  wrong_count_instances  programs answered within budget with a wrong count, or
                         with an impossible value (negative / non-integer)
Exactness is the task constraint: if a counter returns any wrong or impossible
count on any test program, the run is failed and its solved_instances and
max_log2_count_solved are set to 0 in every slice.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import resource
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SLICE = "test"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INSTANCE_DIR = HERE / "instances"
ANSWERS_PATH = HERE / "answers.json"
CPU_BUDGET_SECONDS = 10.0
WALL_LIMIT_SECONDS = 20.0
EXPERIMENTS = ("large_count_counting", "hybrid_full_spectrum")

_INT_RE = re.compile(r"^\d+$")


def answer_digest(salt: str, iterations: int, count: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", str(count).encode(), salt.encode(), iterations).hex()


def discover_counters(registry: Path) -> dict[str, list[str]]:
    counters: dict[str, list[str]] = {}
    if not registry.is_dir():
        return counters
    for spec_path in sorted(registry.glob("*/counter.json")):
        try:
            spec = json.loads(spec_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[{SLICE}] skipping unreadable {spec_path}: {exc}", file=sys.stderr)
            continue
        command = spec.get("command") if isinstance(spec, dict) else None
        if not (isinstance(command, list) and command and all(isinstance(c, str) for c in command)):
            print(f"[{SLICE}] skipping {spec_path}: 'command' must be a non-empty list of strings", file=sys.stderr)
            continue
        counters[spec_path.parent.name] = command
    return counters


def run_command(command: list[str], cpu_budget: float, wall_limit: float) -> dict:
    """Run one counter invocation; measure CPU of the process tree it waited for."""
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
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            preexec_fn=_limit,
            start_new_session=True,
        )
    except OSError as exc:
        return {"returncode": None, "stdout": "", "cpu": 0.0, "wall": 0.0, "timed_out": False, "error": str(exc)}
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
    return {
        "returncode": proc.returncode,
        "stdout": out.decode("utf-8", errors="replace") if out else "",
        "cpu": cpu,
        "wall": time.monotonic() - start,
        "timed_out": timed_out,
    }


def parse_answer(stdout: str) -> tuple[str, int | None]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        return "none", None
    last = lines[-1]
    if _INT_RE.match(last):
        return "answer", int(last)
    try:
        float(last)
    except ValueError:
        return "none", None
    return "invalid", None  # negative, fractional, inf, nan: impossible counts


def judge(run: dict, cpu_budget: float) -> tuple[str, int | None]:
    if run.get("timed_out") or run.get("returncode") != 0:
        return "no_answer", None
    kind, value = parse_answer(run["stdout"])
    if kind == "none":
        return "no_answer", None
    if run["cpu"] > cpu_budget:
        return "over_budget", None
    if kind == "invalid":
        return "invalid", None
    return "answer", value


def load_answers() -> dict:
    data = json.loads(ANSWERS_PATH.read_text())
    for item in data["instances"]:
        if item["slice"] not in EXPERIMENTS:
            raise ValueError(f"unknown slice {item['slice']} for {item['id']}")
    return data


def evaluate_counter(name: str, command: list[str], answers: dict) -> tuple[dict, list[dict]]:
    salt = answers["salt"]
    iterations = int(answers["iterations"])
    details = []
    for item in answers["instances"]:
        program_text = (INSTANCE_DIR / f"{item['id']}.lp").read_text()
        with tempfile.TemporaryDirectory(prefix="asp_eval_") as tmp:
            program_path = Path(tmp) / "program.lp"
            program_path.write_text(program_text)
            run = run_command(command + [str(program_path)], CPU_BUDGET_SECONDS, WALL_LIMIT_SECONDS)
        status, value = judge(run, CPU_BUDGET_SECONDS)
        if status == "answer":
            status = "solved" if answer_digest(salt, iterations, value) == item["digest"] else "wrong"
        details.append(
            {
                "id": item["id"],
                "slice": item["slice"],
                "status": status,
                "log2_count": math.log2(max(value, 1)) if status == "solved" else None,
                "cpu": round(run["cpu"], 3),
                "wall": round(run["wall"], 3),
                "loop_atoms": item.get("loop_atoms"),
            }
        )
        print(f"[{SLICE}] {name:32s} {item['id']} {item['slice']:22s} {status:11s} cpu={run['cpu']:.2f}s", flush=True)

    failed = any(d["status"] in ("wrong", "invalid") for d in details)
    metrics: dict = {}
    for exp in EXPERIMENTS:
        rows = [d for d in details if d["slice"] == exp]
        solved = [d for d in rows if d["status"] == "solved"]
        wrong = sum(1 for d in rows if d["status"] in ("wrong", "invalid"))
        metrics[exp] = {
            "solved_instances": 0 if failed else len(solved),
            "max_log2_count_solved": 0.0 if (failed or not solved) else round(max(d["log2_count"] for d in solved), 6),
            "wrong_count_instances": wrong,
        }
    return metrics, details


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default=str(ROOT / "checkpoints"), help="directory holding <name>/counter.json")
    parser.add_argument("--output", default=str(ROOT / "scoring" / "scores_test.json"))
    parser.add_argument("--details-dir", default=str(ROOT / "checkpoints" / "_eval_details" / SLICE))
    args = parser.parse_args()

    answers = load_answers()
    counters = discover_counters(Path(args.registry))
    if not counters:
        raise SystemExit(f"No counters registered under {args.registry} (expected <name>/counter.json)")

    experiments = {exp: {"results": {}} for exp in EXPERIMENTS}
    details_dir = Path(args.details_dir)
    details_dir.mkdir(parents=True, exist_ok=True)
    for name, command in counters.items():
        metrics, details = evaluate_counter(name, command, answers)
        for exp in EXPERIMENTS:
            experiments[exp]["results"][name] = metrics[exp]
        (details_dir / f"{name}.json").write_text(json.dumps(details, indent=2) + "\n")

    scores = {
        "slice": SLICE,
        "budget": {"cpu_seconds_per_program": CPU_BUDGET_SECONDS, "wall_seconds_per_program": WALL_LIMIT_SECONDS},
        "instances_per_experiment": {exp: sum(1 for i in answers["instances"] if i["slice"] == exp) for exp in EXPERIMENTS},
        "experiments": experiments,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n")
    print(f"[{SLICE}] wrote {out}")


if __name__ == "__main__":
    main()
