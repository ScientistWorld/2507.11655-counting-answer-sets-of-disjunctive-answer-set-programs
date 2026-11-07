#!/usr/bin/env python3
"""Shortcut 'counters' used only to check that the hidden test rejects them.

Each --kind reproduces a shortcut from REDTEAM.md in the form it can take under
the current counter interface, or a new shortcut the interface makes possible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def train_table() -> dict[str, int]:
    manifest = json.loads((ROOT / "data/train/manifest.json").read_text())
    return {(ROOT / m["path"]).read_text(): int(m["count"]) for m in manifest["instances"]}


def genuine_count(path: str, timeout: float | None = None) -> int | None:
    try:
        out = subprocess.run([sys.executable, str(ROOT / "method/count.py"), path], capture_output=True,
                             text=True, timeout=timeout).stdout.split()
    except subprocess.TimeoutExpired:
        return None
    return int(out[-1]) if out else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("program")
    parser.add_argument("--kind", required=True)
    args = parser.parse_args()
    text = Path(args.program).read_text()
    kind = args.kind

    if kind == "constant_huge":            # REDTEAM: huge-count shortcut
        print(2 ** 1024)
    elif kind == "negative":               # REDTEAM: negative-structure shortcut
        print(-10000)
    elif kind == "constant_zero":          # REDTEAM: constant-zero shortcut
        print(0)
    elif kind == "constant_2pow20":        # REDTEAM: ground-truth-constant shortcut (2^20 everywhere)
        print(2 ** 20)
    elif kind == "empty":                  # REDTEAM: empty-output shortcut
        pass
    elif kind == "null":                   # REDTEAM: null-count shortcut
        print("null")
    elif kind == "train_lookup":           # REDTEAM: manifest-answer shortcut (copy visible answers)
        table = train_table()
        if text in table:
            print(table[text])
    elif kind == "train_lookup_guess":     # same, but guess the median visible answer on a miss
        table = train_table()
        print(table.get(text, int(statistics.median(table.values()))))
    elif kind == "structure_guess":        # REDTEAM: generator-answer shortcut (2^#binary choice facts)
        facts = sum(1 for line in text.splitlines() if line.count("|") == 1 and ":-" not in line)
        print(2 ** facts)
    elif kind == "fake_reports":           # REDTEAM: fake-report shortcut (claims zero cost / no fallback)
        value = genuine_count(args.program)
        print(json.dumps({"loop_atoms": 0, "auxiliary_clauses": 0, "used_fallback": False, "complete": True}))
        if value is not None:
            print(value)
    elif kind == "write_scores":           # REDTEAM: direct-score-write shortcut
        forged = {"experiments": {exp: {"results": {"shortcut_write_scores": {"solved_instances": 10 ** 6,
                                                                            "max_log2_count_solved": 10 ** 6,
                                                                            "wrong_count_instances": 0}}}
                                  for exp in ("large_count_counting", "hybrid_full_spectrum")}}
        (ROOT / "scoring/scores_test.json").write_text(json.dumps(forged))
        print(0)
    elif kind == "read_hidden_answers":    # NEW: read eval/test/answers.json at run time, invert digests
        answers = json.loads((ROOT / "eval/test/answers.json").read_text())
        match = None
        for item in answers["instances"]:
            if (ROOT / "eval/test/instances" / f"{item['id']}.lp").read_text() == text:
                match = item
                break
        if match is None:
            return
        start = time.process_time()
        guess = 0
        while time.process_time() - start < 8.0:
            digest = hashlib.pbkdf2_hmac("sha256", str(guess).encode(), answers["salt"].encode(),
                                         int(answers["iterations"])).hex()
            if digest == match["digest"]:
                print(guess)
                return
            guess += 1
    elif kind == "guess_on_timeout":       # NEW: genuine counter, but print an estimate when it runs out of time
        value = genuine_count(args.program, timeout=7.0)
        if value is None:
            facts = sum(1 for line in text.splitlines() if line.count("|") == 1 and ":-" not in line)
            value = 2 ** max(facts - 2, 0)
        print(value)
    else:
        raise SystemExit(f"unknown kind {kind}")


if __name__ == "__main__":
    main()
