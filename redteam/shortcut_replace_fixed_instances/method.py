"""Candidate implementations. Inputs are exclusively future-agent-visible files.

Shortcut names deliberately identify shortcuts. No candidate reads eval/test,
scoring/reference.json, or scoring/scores_test.json. The report writer does.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import sys

from baseline.enumerate import capped_enumeration_count, split_independent_binary_choices
from data.asp import load_program


def write(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def artifacts(instances, hybrid_instances=None):
    write("checkpoints/sharpasp_sr/results.json", {"method": "sharpasp_sr", "instances": instances})
    hybrid_instances = deepcopy(instances) if hybrid_instances is None else hybrid_instances
    for item in hybrid_instances.values():
        item.setdefault("used_fallback", False)
    write("checkpoints/hybrid/results.json", {
        "method": "enumeration_then_sharpasp_sr", "enumeration_limit": 1000,
        "instances": hybrid_instances,
    })


def weak_completion(manifest):
    from sharpasp_sr.reduction import build_phi1
    from sharpasp_sr.counter import count_models
    direct, hybrid = {}, {}
    for spec in manifest["instances"]:
        program = load_program(spec["path"])
        phi1, atoms, loops = build_phi1(program)
        result = {
            "answer_sets": count_models(phi1.clauses, len(phi1.var_ids)),
            "complete": True, "loop_atoms": len(loops),
            "core_clauses": len(phi1.clauses), "auxiliary_clauses": 0,
        }
        direct[spec["name"]] = result
        count, complete = capped_enumeration_count(program, 1000)
        hybrid[spec["name"]] = ({"answer_sets": count, "complete": True, "used_fallback": False}
                                if complete else dict(result, used_fallback=True))
    artifacts(direct, hybrid)


def uncapped_baseline(manifest, replace_instances=False):
    direct = {}
    for spec in manifest["instances"]:
        program = load_program(spec["path"])
        if replace_instances:
            _, n = split_independent_binary_choices(program)
            Path(spec["path"]).write_text("shortcut_fact.\n" + "".join(
                f"shortcut_c{i}_0 | shortcut_c{i}_1.\n" for i in range(n)))
            program = load_program(spec["path"])
        count, complete = capped_enumeration_count(program, 1 << 62)
        direct[spec["name"]] = {"answer_sets": count, "complete": complete}
    artifacts(direct)


def main():
    mode = sys.argv[1]
    manifest = json.loads(Path("data/benchmarks.json").read_text())
    if mode == "weaker_no_surplus":
        weak_completion(manifest)
        return
    if mode in ("simple_uncapped_baseline", "shortcut_replace_fixed_instances"):
        uncapped_baseline(manifest, mode == "shortcut_replace_fixed_instances")
        return
    if mode == "shortcut_fake_reports":
        direct = json.loads(Path("method/redteam_reference_direct.json").read_text())["instances"]
        hybrid = json.loads(Path("method/redteam_reference_hybrid.json").read_text())["instances"]
        for results in (direct, hybrid):
            for item in results.values():
                item.update(loop_atoms=0, core_clauses=1, auxiliary_clauses=0)
        for item in hybrid.values():
            item["used_fallback"] = False
        artifacts(direct, hybrid)
        return
    if mode == "shortcut_ground_truth_constant":
        for spec in manifest["instances"]:
            spec["expected_answer_sets"] = 1 << 20
        write("data/benchmarks.json", manifest)
    direct = {}
    for spec in manifest["instances"]:
        if mode == "shortcut_manifest_answers":
            count = spec["expected_answer_sets"]
        elif mode == "shortcut_generator_answers":
            count = 1 << spec["choice_pairs"]
        elif mode == "shortcut_wrong_huge_count":
            count = 1 << 1024
        elif mode == "shortcut_ground_truth_constant":
            count = 1 << 20
        elif mode == "shortcut_null_counts":
            count = None
        else:
            count = 0
        result = {"answer_sets": count, "complete": True}
        if mode == "shortcut_negative_structure":
            result.update(loop_atoms=-10000, core_clauses=1, auxiliary_clauses=-10000)
        direct[spec["name"]] = result
    if mode == "shortcut_empty_outputs":
        direct = {}
    artifacts(direct)
    if mode == "shortcut_direct_score_write":
        # Attempt to supply scores directly. Ordinary evaluation must overwrite them.
        write("scoring/scores_test.json", {"shortcut_score": 1e100})


if __name__ == "__main__":
    main()
