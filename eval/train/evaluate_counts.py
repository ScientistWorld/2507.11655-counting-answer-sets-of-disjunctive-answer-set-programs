#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path


SLICE = "train"
SPLIT_INSTANCE_NAMES = {"paper_example", "choices_14", "choices_20"}


@dataclass(frozen=True)
class Artifact:
    name: str
    path: Path
    results: dict


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def load_manifest(path: Path) -> dict:
    manifest = load_json(path)
    instances = [item for item in manifest["instances"] if item["name"] in SPLIT_INSTANCE_NAMES]
    found = {item["name"] for item in instances}
    missing = sorted(SPLIT_INSTANCE_NAMES - found)
    if missing:
        raise ValueError(f"{SLICE} split instances missing from {path}: {missing}")
    return {"instances": instances}


def unique_result_paths(results_root: Path, explicit_paths: list[str]) -> list[Path]:
    paths: list[Path] = []
    if results_root.exists():
        paths.extend(sorted(results_root.glob("*/results.json")))
    paths.extend(Path(item) for item in explicit_paths)

    unique: dict[Path, Path] = {}
    for path in paths:
        if path.exists():
            unique[path.resolve()] = path
    return list(unique.values())


def artifact_name(path: Path, results: dict) -> str:
    raw_name = str(results.get("method") or path.parent.name)
    if raw_name == "enumeration":
        limit = results.get("limit")
        for item in results.get("instances", {}).values():
            limit = item.get("limit", limit)
            if limit is not None:
                break
        if limit is not None:
            return f"enumeration_cap_{limit}"
    return raw_name


def load_artifacts(results_root: Path, explicit_paths: list[str]) -> dict[str, Artifact]:
    artifacts: dict[str, Artifact] = {}
    for path in unique_result_paths(results_root, explicit_paths):
        results = load_json(path)
        name = artifact_name(path, results)
        artifacts[name] = Artifact(name=name, path=path, results=results)
    if not artifacts:
        raise FileNotFoundError(
            f"No result artifacts found under {results_root} and no explicit result paths existed."
        )
    return artifacts


def has_hybrid_fields(results: dict) -> bool:
    if "enumeration_limit" in results or "fallback_instances" in results:
        return True
    return any("used_fallback" in item for item in results.get("instances", {}).values())


def is_enumeration_baseline(name: str) -> bool:
    return name.startswith("enumeration_cap_")


def summarize_counts(results: dict, manifest: dict) -> dict[str, float]:
    expected = {item["name"]: item for item in manifest["instances"]}
    solved = 0
    exact = 0
    max_log = 0.0
    total_loop_atoms = 0.0
    total_phi2_ratio = 0.0

    for name, item in expected.items():
        got = results.get("instances", {}).get(name)
        if not got:
            continue
        complete = got.get("complete", True)
        if complete:
            solved += 1
        if complete and got.get("answer_sets") == item["expected_answer_sets"]:
            exact += 1
        if complete and got.get("answer_sets", 0) > 0:
            max_log = max(max_log, math.log2(got["answer_sets"]))
        if "loop_atoms" in got:
            total_loop_atoms += got["loop_atoms"]
        if got.get("phi1_clauses"):
            total_phi2_ratio += got["phi2_clauses"] / got["phi1_clauses"]

    n = len(expected)
    return {
        "solved_instances": solved,
        "exact_count_accuracy": exact / n if n else 0.0,
        "max_log2_count_solved": max_log,
        "avg_loop_atoms": total_loop_atoms / n if n else 0.0,
        "avg_phi2_to_phi1_clause_ratio": total_phi2_ratio / n if n else 0.0,
    }


def summarize_hybrid(results: dict, manifest: dict) -> dict[str, float]:
    summary = summarize_counts(results, manifest)
    instances = {
        name: item
        for name, item in results.get("instances", {}).items()
        if name in SPLIT_INSTANCE_NAMES
    }
    summary["fallback_instances"] = sum(1 for item in instances.values() if item.get("used_fallback"))
    summary["enumeration_completed_instances"] = sum(
        1
        for item in instances.values()
        if item.get("complete", True) and not item.get("used_fallback", False)
    )
    return summary


def build_scores(artifacts: dict[str, Artifact], manifest: dict) -> dict:
    counting_results = {}
    hybrid_results = {}

    for name, artifact in sorted(artifacts.items()):
        hybrid_like = has_hybrid_fields(artifact.results)
        if not hybrid_like or is_enumeration_baseline(name):
            counting_results[name] = summarize_counts(artifact.results, manifest)
        if hybrid_like or is_enumeration_baseline(name):
            hybrid_results[name] = summarize_hybrid(artifact.results, manifest)

    return {
        "experiments": {
            "scaled_disjunctive_counting": {"results": counting_results},
            "scaled_hybrid_counting": {"results": hybrid_results},
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/benchmarks.json")
    parser.add_argument("--results-root", default="checkpoints")
    parser.add_argument("--method-results", action="append", default=[])
    parser.add_argument("--baseline-results", action="append", default=[])
    parser.add_argument("--hybrid-results", action="append", default=[])
    parser.add_argument("--output", default="scoring/scores_train.json")
    args = parser.parse_args()

    explicit_paths = args.method_results + args.baseline_results + args.hybrid_results
    manifest = load_manifest(Path(args.manifest))
    artifacts = load_artifacts(Path(args.results_root), explicit_paths)
    scores = build_scores(artifacts, manifest)
    Path(args.output).write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
