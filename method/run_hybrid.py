#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from baseline.enumerate import capped_enumeration_count
from data.asp import load_program
from sharpasp_sr.reduction import sharpasp_sr_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/benchmarks.json")
    parser.add_argument("--output", default="checkpoints/hybrid/results.json")
    parser.add_argument("--enumeration-limit", type=int, default=1000)
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    results = {}
    fallback_instances = 0
    for item in manifest["instances"]:
        program = load_program(item["path"])
        enum_count, enum_complete = capped_enumeration_count(program, args.enumeration_limit)
        if enum_complete:
            result = {
                "answer_sets": enum_count,
                "complete": True,
                "used_fallback": False,
                "enumeration_limit": args.enumeration_limit,
            }
        else:
            result = sharpasp_sr_count(program)
            result["complete"] = True
            result["used_fallback"] = True
            result["enumeration_limit"] = args.enumeration_limit
            fallback_instances += 1
        result["log2_answer_sets"] = math.log2(result["answer_sets"]) if result["answer_sets"] > 0 else None
        results[item["name"]] = result

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "method": "enumeration_then_sharpasp_sr",
                "enumeration_limit": args.enumeration_limit,
                "fallback_instances": fallback_instances,
                "instances": results,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
