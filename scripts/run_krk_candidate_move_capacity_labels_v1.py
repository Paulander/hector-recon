#!/usr/bin/env python3
"""Run bounded offline CandidateMoveFrame capacity labels."""

from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import chess

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from recon_lite.engine import ReConEngine  # noqa: E402
from recon_lite_chess.graph.builder import build_graph_from_topology  # noqa: E402
from scripts.run_krk_candidate_generation_observation_sandbox_v0 import (  # noqa: E402
    TOPOLOGY,
    _profile_kwargs,
)
from scripts.test_krk_landmark_progress import (  # noqa: E402
    COMPOSITION_PROFILE_HANDOFF_V1,
    play_to_mate,
)


MANIFEST = Path(
    "reports/strategy_arbitration/krk_candidate_move_capacity_label_manifest_v1.json"
)
OUT_JSON = Path("reports/strategy_arbitration/krk_candidate_move_capacity_labels_v1.json")
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_move_capacity_labels_v1.md")
EXECUTION_LANDMARK_LABELS = {
    "wrong_tempo_control": "edge_trap_wrong_tempo",
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _stable_seed(value: str) -> int:
    return int(hashlib.sha1(value.encode("utf-8")).hexdigest()[:8], 16)


def _new_graph_engine() -> tuple[Any, ReConEngine]:
    graph = build_graph_from_topology(ROOT / TOPOLOGY)
    return graph, ReConEngine(graph)


def _run_job(job: dict[str, Any]) -> dict[str, Any]:
    if job.get("source_stage") == "stage7" or job.get("stage7_training_row"):
        raise ValueError("Stage 7 jobs are not allowed in candidate-move capacity labels")
    fen = str(job.get("fen") or "")
    move_uci = str(job.get("candidate_move_uci") or "")
    board = chess.Board(fen)
    move = chess.Move.from_uci(move_uci)
    if move not in board.legal_moves:
        return {
            "schema_version": "krk_candidate_move_capacity_label.v1",
            "causal_status": "non_causal_outcome_label",
            "job_id": job.get("job_id"),
            "source_stage": job.get("source_stage"),
            "active_landmark_label": job.get("active_landmark_label"),
            "fen": fen,
            "forced_first_move": move_uci,
            "forced_first_move_legal": False,
            "result": "illegal_move",
            "plies_after_forced_move": 0,
            "total_plies_including_forced_move": 0,
            "horizon": int(job.get("horizon") or 40),
            "label_semantics": job.get("label_semantics"),
            "stage7_training_row": False,
        }

    board.push(move)
    graph, engine = _new_graph_engine()
    horizon = int(job.get("horizon") or 40)
    execution_label = EXECUTION_LANDMARK_LABELS.get(
        str(job.get("active_landmark_label") or ""),
        str(job.get("active_landmark_label") or "candidate_move_capacity"),
    )
    result = play_to_mate(
        graph,
        engine,
        board,
        random.Random(_stable_seed(str(job.get("job_id") or move_uci))),
        label=execution_label,
        stage_filter=None,
        max_plies=max(horizon - 1, 0),
        black_policy="adversarial",
        trace=False,
        max_ticks=200,
        suggestion_limit=10,
        early_stop_stable_suggestions=2,
        enable_diagnostic_caches=True,
        **_profile_kwargs(),
    )
    return {
        "schema_version": "krk_candidate_move_capacity_label.v1",
        "causal_status": "non_causal_outcome_label",
        "job_id": job.get("job_id"),
        "source_stage": job.get("source_stage"),
        "state_id": job.get("state_id"),
        "active_landmark_label": job.get("active_landmark_label"),
        "execution_landmark_label": execution_label,
        "fen": fen,
        "forced_first_move": move_uci,
        "forced_first_move_legal": True,
        "selected_move_before_observation": job.get("selected_move_before_observation"),
        "selected_provider_before_observation": job.get("selected_provider_before_observation"),
        "result": result.get("result"),
        "plies_after_forced_move": result.get("plies"),
        "total_plies_including_forced_move": int(result.get("plies", 0) or 0) + 1,
        "horizon": horizon,
        "black_policy": "adversarial",
        "composition_profile": COMPOSITION_PROFILE_HANDOFF_V1,
        "topology": str(TOPOLOGY),
        "label_semantics": job.get("label_semantics"),
        "capacity_label": "positive_capacity" if result.get("result") == "mate" else "negative_capacity",
        "stage7_training_row": False,
        "engine_decision_count": result.get("engine_decision_count"),
        "engine_ticks_total": result.get("engine_ticks_total"),
    }


def build_payload() -> dict[str, Any]:
    manifest = _load(MANIFEST)
    if manifest.get("causal_status") != "offline_label_manifest_only":
        raise ValueError("manifest must be offline-label only")
    jobs = list(manifest.get("jobs") or [])
    if any(job.get("source_stage") == "stage7" for job in jobs):
        raise ValueError("Stage 7 jobs are not allowed")
    start = time.monotonic()
    labels = []
    for index, job in enumerate(jobs, start=1):
        print(
            f"[{index}/{len(jobs)}] {job.get('source_stage')} {job.get('candidate_move_uci')}",
            file=sys.stderr,
            flush=True,
        )
        labels.append(_run_job(job))
    wall = time.monotonic() - start
    result_counts = Counter(str(label.get("result") or "unknown") for label in labels)
    capacity_counts = Counter(str(label.get("capacity_label") or "unknown") for label in labels)
    by_stage = Counter(f"{label.get('source_stage')}:{label.get('result')}" for label in labels)
    payload = {
        "schema_version": "krk_candidate_move_capacity_labels.v1",
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifact": str(MANIFEST),
        "labels": labels,
        "summary": {
            "label_count": len(labels),
            "result_counts": dict(sorted(result_counts.items())),
            "capacity_label_counts": dict(sorted(capacity_counts.items())),
            "result_counts_by_stage": dict(sorted(by_stage.items())),
            "stage7_label_count": sum(1 for label in labels if label.get("source_stage") == "stage7"),
            "stage7_training_label_count": sum(
                1 for label in labels if label.get("stage7_training_row")
            ),
            "wall_time_seconds": round(wall, 3),
        },
        "decision": {
            "status": "bounded_candidate_move_capacity_labels_completed",
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "merge_candidate_move_capacity_labels_and_refresh_annotation",
        },
    }
    validate_payload(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("causal_status") != "non_causal_label_run":
        raise ValueError("labels must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_score_changes",
        "runtime_direct_routing",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_label_count"] != 0:
        raise ValueError("Stage 7 labels must remain excluded")
    if payload["summary"]["stage7_training_label_count"] != 0:
        raise ValueError("Stage 7 training labels must remain excluded")
    for label in payload.get("labels") or []:
        if label.get("causal_status") != "non_causal_outcome_label":
            raise ValueError("each label must remain non-causal")
        if label.get("label_semantics") != "forced_first_move_capacity_not_runtime_ownership_label":
            raise ValueError("candidate-move labels must not become ownership labels")


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK CandidateMoveFrame Capacity Labels v1",
        "",
        "Bounded protected-only offline labels for observed candidate moves. These labels are capacity evidence, not runtime ownership labels.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- guardrails_allowed: `{payload['decision']['guardrails_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- label_count: {summary['label_count']}",
        f"- result_counts: `{summary['result_counts']}`",
        f"- capacity_label_counts: `{summary['capacity_label_counts']}`",
        f"- result_counts_by_stage: `{summary['result_counts_by_stage']}`",
        f"- stage7_label_count: {summary['stage7_label_count']}",
        f"- wall_time_seconds: `{summary['wall_time_seconds']}`",
        "",
        "## Labels",
        "",
    ]
    for label in payload["labels"]:
        lines.append(
            f"- `{label['job_id']}` stage=`{label['source_stage']}` "
            f"move=`{label['forced_first_move']}` result=`{label['result']}` "
            f"capacity=`{label.get('capacity_label')}` total_plies=`{label['total_plies_including_forced_move']}`"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "These labels do not authorize selector training, routing, guardrails, Stage 7 promotion, or Stage 8 training.",
        ]
    )
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
