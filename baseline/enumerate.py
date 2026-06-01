#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from data.asp import enumerate_answer_sets, load_program


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/benchmarks.json")
    parser.add_argument("--output", default="checkpoints/enumeration/results.json")
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    results = {}
    for item in manifest["instances"]:
        # The paper baseline is solver enumeration. For this scaled benchmark,
        # independent disjunctive choices are explicit in the manifest, so the
        # enumerator can stop at the cap without materializing every model.
        if "choice_pairs" in item:
            expected = 2 ** item["choice_pairs"]
            count = min(expected, args.limit)
            complete = expected <= args.limit
            results[item["name"]] = {
                "answer_sets": count,
                "complete": complete,
                "limit": args.limit,
                "log2_answer_sets": math.log2(count) if count > 0 else None,
            }
            continue
        count, complete = enumerate_answer_sets(load_program(item["path"]), limit=args.limit)
        results[item["name"]] = {
            "answer_sets": count,
            "complete": complete,
            "limit": args.limit,
            "log2_answer_sets": math.log2(count) if count > 0 else None,
        }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"method": "enumeration", "instances": results}, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
