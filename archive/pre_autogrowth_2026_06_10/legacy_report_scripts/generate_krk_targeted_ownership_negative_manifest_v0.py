#!/usr/bin/env python3
"""Generate a bounded manifest for targeted ownership-negative labels.

This is not blind label farming: candidates are filtered by current-profile
selected owner and known false-positive risk cells from the refreshed ownership
probe. Labels remain non-causal and selector training remains blocked.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import test_krk_landmark_progress as diag  # noqa: E402
from generate_krk_strategy_arbiter_out_of_sample_execution_manifest import (  # noqa: E402
    STAGE_CONFIGS,
    _binding_for_stage,
)
from recon_lite_chess.routing import stable_record_id  # noqa: E402
from run_krk_strategy_arbiter_out_of_sample_control_labels import (  # noqa: E402
    _choose_initial,
    _load_graph_engine,
    _selected_provider,
)


OWNERSHIP_V4 = Path("reports/krk_ownership_selection_label_dataset_v4.json")
PROBE_V2 = Path("reports/krk_ownership_selection_context_feature_probe_v2.json")
OUT_JSON = Path("reports/krk_targeted_ownership_negative_manifest_v0.json")
OUT_MD = Path("reports/krk_targeted_ownership_negative_manifest_v0.md")


TARGET_CELLS = [
    {
        "target_cell_id": "stage4_stage0_wrong_tempo_like",
        "source_stage": "stage4",
        "active_landmark_label": "edge_trap_wrong_tempo",
        "selected_provider": "krk.stage0_basin",
        "target_count": 4,
        "reason": "stage4 stage0 owns most current negatives and false positives",
    },
    {
        "target_cell_id": "stage5_stage0_fence_like",
        "source_stage": "stage5",
        "active_landmark_label": "fence_established",
        "selected_provider": "krk.stage0_basin",
        "target_count": 2,
        "reason": "stage5 stage0 has sparse true ownership negatives",
    },
    {
        "target_cell_id": "stage6_stage0_drive_like",
        "source_stage": "stage6",
        "active_landmark_label": "drive_to_edge",
        "selected_provider": "krk.stage0_basin",
        "target_count": 2,
        "reason": "stage6 stage0 false-positive cell needs more direct labels",
    },
]


def _load_json(repo_root: Path, path: Path) -> dict[str, Any]:
    payload = json.loads((repo_root / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _state_id_from_board(board: Any) -> str:
    return stable_record_id("state", board.board_fen(), board.turn)


def _stable_seed(*parts: Any) -> int:
    text = "|".join(str(part) for part in parts)
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:8], 16)


def _job_for_candidate(candidate: dict[str, Any], *, horizon: int) -> dict[str, Any]:
    stage = str(candidate["source_stage"])
    return {
        "schema_version": "krk_targeted_ownership_negative_job.v0",
        "job_id": stable_record_id(
            "job.krk.targeted_ownership_negative",
            candidate["state_id"],
            stage,
            candidate["target_cell_id"],
        ),
        "causal_status": "non_causal_label_job",
        "labels_generated": False,
        "runtime_behavior_changed": False,
        "stage7_training_row": False,
        "source_kind": "targeted_false_positive_risk_cell",
        "target_cell_id": candidate["target_cell_id"],
        "target_cell_reason": candidate["target_cell_reason"],
        "frame_id": f"cp.krk.{candidate['state_id']}",
        "state_id": candidate["state_id"],
        "source_stage": stage,
        "stage_role": STAGE_CONFIGS[stage]["stage_role"],
        "active_landmark_label": candidate["active_landmark_label"],
        "fen": candidate["fen"],
        "current_profile_preselected_provider": candidate["selected_provider"],
        "current_profile_preselected_move": candidate["selected_move"],
        "horizon": horizon,
        "diagnostic_caches_required": True,
        "parallel_workers_allowed": True,
        "exhaustive_legal_first_sweeps": False,
        "target_label_semantics": [
            "current_profile_selected_owner_h40",
            "targeted_false_positive_risk_cell_outcome",
        ],
        "generation": candidate["generation"],
        "execution_binding": _binding_for_stage(stage),
    }


def build_manifest(
    repo_root: Path,
    *,
    horizon: int = 40,
    base_seed: int = 31,
    max_sample_index: int = 240,
    max_jobs: int = 8,
    position_mode: str = "hybrid",
) -> dict[str, Any]:
    ownership = _load_json(repo_root, OWNERSHIP_V4)
    probe = _load_json(repo_root, PROBE_V2)
    if ownership.get("causal_status") != "non_causal_ownership_label_dataset":
        raise ValueError("ownership dataset must remain non-causal")
    if probe.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("ownership probe must remain non-causal")
    used_state_ids = {str(row.get("state_id")) for row in ownership.get("rows") or []}

    graph_cache: dict[str, tuple[Any, Any]] = {}
    selected: list[dict[str, Any]] = []
    selected_state_ids: set[str] = set()
    target_counts: Counter[str] = Counter()
    scan_counts: Counter[str] = Counter()
    match_counts: Counter[str] = Counter()

    for cell in TARGET_CELLS:
        stage = cell["source_stage"]
        binding = _binding_for_stage(stage)
        topology_path = str(binding["topology_path"])
        if topology_path not in graph_cache:
            graph_cache[topology_path] = _load_graph_engine(repo_root, topology_path)
        graph, engine = graph_cache[topology_path]
        source_names = tuple(diag.source_stage_names_for_label(str(cell["active_landmark_label"])))
        for sample_index in range(max_sample_index):
            if len(selected) >= max_jobs or target_counts[cell["target_cell_id"]] >= int(cell["target_count"]):
                break
            sample_seed = _stable_seed(base_seed, cell["target_cell_id"], sample_index)
            rng = random.Random(sample_seed)
            random.seed(sample_seed)
            board = diag.select_eval_position(
                rng,
                str(cell["active_landmark_label"]),
                position_mode,
                source_names,
            )
            state_id = _state_id_from_board(board)
            scan_counts[cell["target_cell_id"]] += 1
            if state_id in used_state_ids or state_id in selected_state_ids:
                continue
            job_stub = {
                "execution_binding": binding,
                "active_landmark_label": cell["active_landmark_label"],
            }
            initial = _choose_initial(graph, engine, board, job_stub)
            selected_provider = _selected_provider(initial)
            if selected_provider != cell["selected_provider"]:
                continue
            match_counts[cell["target_cell_id"]] += 1
            selected_state_ids.add(state_id)
            target_counts[cell["target_cell_id"]] += 1
            selected.append(
                {
                    "target_cell_id": cell["target_cell_id"],
                    "target_cell_reason": cell["reason"],
                    "source_stage": stage,
                    "active_landmark_label": cell["active_landmark_label"],
                    "state_id": state_id,
                    "fen": board.fen(),
                    "selected_provider": selected_provider,
                    "selected_move": initial.get("move"),
                    "generation": {
                        "base_seed": base_seed,
                        "sample_index": sample_index,
                        "sample_seed": sample_seed,
                        "position_mode": position_mode,
                        "source_stage_names": list(source_names),
                    },
                }
            )
        if len(selected) >= max_jobs:
            break

    jobs = [_job_for_candidate(candidate, horizon=horizon) for candidate in selected]
    missing_paths: list[str] = []
    for job in jobs:
        binding = job["execution_binding"]
        for path_key in ("topology_path", "source_checkpoint"):
            path = repo_root / str(binding[path_key])
            if not path.exists():
                missing_paths.append(str(path))

    payload = {
        "schema_version": "krk_targeted_ownership_negative_manifest.v0",
        "causal_status": "non_causal_execution_manifest",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "labels_generated_in_this_slice": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(OWNERSHIP_V4), str(PROBE_V2)],
        "selection_policy": {
            "horizon": horizon,
            "base_seed": base_seed,
            "max_sample_index": max_sample_index,
            "max_jobs": max_jobs,
            "position_mode": position_mode,
            "target_cells": TARGET_CELLS,
            "stage7_training_rows": 0,
            "filter_by_current_profile_selected_owner": True,
        },
        "scan_summary": {
            "scanned_by_target_cell": dict(sorted(scan_counts.items())),
            "matched_by_target_cell": dict(sorted(match_counts.items())),
            "selected_by_target_cell": dict(sorted(target_counts.items())),
        },
        "binding_summary": {
            "job_count": len(jobs),
            "job_count_by_stage": dict(sorted(Counter(job["source_stage"] for job in jobs).items())),
            "job_count_by_target_cell": dict(
                sorted(Counter(job["target_cell_id"] for job in jobs).items())
            ),
            "missing_path_count": len(missing_paths),
            "missing_paths": sorted(missing_paths),
            "all_bindings_valid": not missing_paths,
            "stage7_job_count": sum(1 for job in jobs if job.get("source_stage") == "stage7"),
        },
        "jobs": jobs,
        "decision": {
            "status": (
                "targeted_ownership_negative_manifest_ready"
                if jobs and not missing_paths
                else "targeted_ownership_negative_manifest_blocked"
            ),
            "execute_labels_now": bool(jobs and not missing_paths),
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": (
                "run_bounded_targeted_ownership_negative_labels"
                if jobs and not missing_paths
                else "review_target_cell_coverage_before_more_scanning"
            ),
        },
        "blocked_next_steps": [
            "runtime_arbiter",
            "runtime_selector",
            "selector_training",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_manifest(payload)
    return payload


def validate_manifest(payload: dict[str, Any]) -> None:
    if payload.get("causal_status") != "non_causal_execution_manifest":
        raise ValueError("manifest must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_arbiter_implemented",
        "runtime_selector_implemented",
        "runtime_candidate_generator_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "labels_generated_in_this_slice",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    for job in payload.get("jobs") or []:
        if job.get("source_stage") == "stage7":
            raise ValueError("Stage 7 must remain excluded")
        if job.get("causal_status") != "non_causal_label_job":
            raise ValueError("jobs must remain non-causal")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Targeted Ownership Negative Manifest v0",
        "",
        "This manifest targets known false-positive ownership risk cells. It is "
        "non-causal and does not implement or train a selector.",
        "",
        "## Summary",
        "",
        f"- Job count: `{payload['binding_summary']['job_count']}`",
        f"- Jobs by stage: `{payload['binding_summary']['job_count_by_stage']}`",
        f"- Jobs by target cell: `{payload['binding_summary']['job_count_by_target_cell']}`",
        f"- Scan summary: `{payload['scan_summary']}`",
        f"- Decision: `{payload['decision']['status']}`",
        "",
        "## Jobs",
        "",
    ]
    for job in payload["jobs"]:
        lines.append(
            f"- `{job['state_id']}` stage=`{job['source_stage']}` "
            f"cell=`{job['target_cell_id']}` selected=`{job['current_profile_preselected_provider']}` "
            f"move=`{job['current_profile_preselected_move']}`"
        )
    lines.extend(["", "## Recommended Next Step", "", f"`{payload['decision']['recommended_next_step']}`", ""])
    return "\n".join(lines)


def write_outputs(repo_root: Path, payload: dict[str, Any]) -> None:
    (repo_root / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (repo_root / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--horizon", type=int, default=40)
    parser.add_argument("--base-seed", type=int, default=31)
    parser.add_argument("--max-sample-index", type=int, default=240)
    parser.add_argument("--max-jobs", type=int, default=8)
    parser.add_argument("--position-mode", choices=("curriculum", "hybrid", "random"), default="hybrid")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_manifest(
        repo_root,
        horizon=args.horizon,
        base_seed=args.base_seed,
        max_sample_index=args.max_sample_index,
        max_jobs=args.max_jobs,
        position_mode=args.position_mode,
    )
    write_outputs(repo_root, payload)
    print(json.dumps(payload["binding_summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
