#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from sharpasp_sr.asp import load_program
from sharpasp_sr.reduction import sharpasp_sr_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/benchmarks.json")
    parser.add_argument("--output", default="checkpoints/sharpasp_sr/results.json")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    results = {}
    for item in manifest["instances"]:
        program = load_program(item["path"])
        result = sharpasp_sr_count(program)
        result["log2_answer_sets"] = math.log2(result["answer_sets"]) if result["answer_sets"] > 0 else None
        results[item["name"]] = result

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"method": "sharpasp_sr", "instances": results}, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
