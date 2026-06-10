#!/usr/bin/env python3
"""Run bounded selected-provider diversity observations.

This observes selected providers for reviewed protected jobs only. It does not
run playout labels, implement a selector, change runtime defaults, promote
Stage 7, or train Stage 8.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import chess


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import test_krk_landmark_progress as diag  # noqa: E402
from recon_lite.engine import ReConEngine  # noqa: E402


MANIFEST = Path("reports/krk_selected_provider_diversity_sampling_manifest_v0.json")
REVIEW = Path("reports/krk_selected_provider_diversity_sampling_manifest_review_v0.json")
OUT_JSON = Path("reports/krk_selected_provider_diversity_observation_scan_v0.json")
OUT_MD = Path("reports/krk_selected_provider_diversity_observation_scan_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _provider_family(provider_id: str | None) -> str:
    provider_id = provider_id or "unknown"
    if provider_id.startswith("krk.edge_trap"):
        return "edge_trap"
    if provider_id == "krk.stage0_basin":
        return "stage0_basin"
    return provider_id.removeprefix("krk.")


def _load_graph_engine(topology_path: str, cache: dict[str, tuple[Any, ReConEngine]]) -> tuple[Any, ReConEngine]:
    if topology_path not in cache:
        graph = diag.build_graph_from_topology(ROOT / topology_path)
        cache[topology_path] = (graph, ReConEngine(graph))
    return cache[topology_path]


def _selected_provider(move_details: dict[str, Any]) -> str | None:
    suggestion = diag._selected_engine_suggestion(move_details)
    if not suggestion:
        return None
    return diag._skill_id_for_suggestion(suggestion)


def _observe_job(job: dict[str, Any], cache: dict[str, tuple[Any, ReConEngine]]) -> dict[str, Any]:
    binding = job.get("execution_binding") or {}
    settings = binding.get("profile_settings") or {}
    graph, engine = _load_graph_engine(str(binding.get("topology_path") or ""), cache)
    board = chess.Board(str(job.get("fen") or ""))
    move_details = diag.choose_move_details(
        graph,
        engine,
        board,
        max_ticks=int(binding.get("max_ticks") or 200),
        stage_filter=None,
        suggestion_limit=int(binding.get("suggestion_limit") or 10),
        successor_affordance_layer_enabled=bool(settings.get("successor_affordance_layer_enabled")),
        successor_role_license_enabled=bool(settings.get("successor_role_license_enabled")),
        successor_role_scoped_move_shape_enabled=bool(
            settings.get("successor_role_scoped_move_shape_enabled")
        ),
        successor_role_scoped_move_shape_bonus=float(
            settings.get("successor_role_scoped_move_shape_bonus") or 0.0
        ),
        stagnation_breaker_enabled=bool(settings.get("stagnation_breaker_enabled")),
        stagnation_breaker_bonus=float(settings.get("stagnation_breaker_bonus") or 0.0),
        post_break_continuation_enabled=bool(settings.get("post_break_continuation_enabled")),
        post_break_continuation_bonus=float(settings.get("post_break_continuation_bonus") or 0.0),
        successor_stage0_drift_penalty=float(settings.get("successor_stage0_drift_penalty") or 0.0),
        early_stop_stable_suggestions=int(binding.get("early_stop_stable_suggestions") or 0),
        active_landmark_label=str(job.get("active_landmark_label") or ""),
        enable_diagnostic_caches=bool(binding.get("enable_diagnostic_caches")),
    )
    selected = diag._selected_engine_suggestion(move_details) or {}
    provider_id = _selected_provider(move_details)
    suggestions = []
    for index, suggestion in enumerate(move_details.get("suggestions") or [], start=1):
        skill_id = diag._skill_id_for_suggestion(suggestion)
        suggestions.append(
            {
                "rank": index,
                "provider_id": skill_id,
                "provider_family": _provider_family(skill_id),
                "move_uci": suggestion.get("move"),
                "score": suggestion.get("score"),
            }
        )
    return {
        "schema_version": "krk_selected_provider_observation.v0",
        "causal_status": "non_causal_selected_provider_observation",
        "job_id": job.get("job_id"),
        "state_id": job.get("state_id"),
        "frame_id": job.get("frame_id"),
        "source_stage": job.get("source_stage"),
        "active_landmark_label": job.get("active_landmark_label"),
        "fen": job.get("fen"),
        "selected_move": move_details.get("move"),
        "selected_provider_id": provider_id,
        "selected_provider_family": _provider_family(provider_id),
        "selected_score": selected.get("score"),
        "suggestion_count": len(move_details.get("suggestions") or []),
        "top_suggestions": suggestions[:10],
    }


def run_observations() -> dict[str, Any]:
    manifest = _load_json(MANIFEST)
    review = _load_json(REVIEW)
    if manifest.get("causal_status") != "non_causal_sampling_manifest":
        raise ValueError("manifest must remain non-causal")
    if review.get("causal_status") != "non_causal_manifest_review":
        raise ValueError("review must remain non-causal")
    if not (review.get("decision") or {}).get("observations_allowed"):
        raise ValueError("review must allow observations")
    cache: dict[str, tuple[Any, ReConEngine]] = {}
    start = time.monotonic()
    observations = [_observe_job(job, cache) for job in manifest.get("jobs") or []]
    wall_time = time.monotonic() - start
    family_counts = Counter(obs["selected_provider_family"] for obs in observations)
    stage_counts = Counter(obs["source_stage"] for obs in observations)
    total = len(observations)
    max_dominance = max(family_counts.values()) / total if total else 1.0
    payload = {
        "schema_version": "krk_selected_provider_diversity_observation_scan.v0",
        "causal_status": "non_causal_observation_scan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "labels_generated_in_this_slice": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST), str(REVIEW)],
        "summary": {
            "observation_count": total,
            "selected_provider_family_counts": dict(sorted(family_counts.items())),
            "selected_stage_counts": dict(sorted(stage_counts.items())),
            "distinct_selected_provider_families": len(family_counts),
            "max_selected_provider_family_dominance": round(max_dominance, 4),
            "stage7_observations": sum(1 for obs in observations if obs.get("source_stage") == "stage7"),
            "wall_time_seconds": round(wall_time, 3),
        },
        "observations": observations,
        "decision": {
            "status": (
                "selected_provider_diversity_observation_satisfied"
                if len(family_counts) >= 3 and max_dominance <= 0.7
                else "selected_provider_diversity_observation_insufficient"
            ),
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": (
                "architecture_review_selector_readiness_after_selected_provider_observations"
                if len(family_counts) >= 3 and max_dominance <= 0.7
                else "review_sampling_strategy_or_pause_selector_work"
            ),
        },
        "blocked_next_steps": [
            "runtime_arbiter",
            "selector_sandbox",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_payload(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("causal_status") != "non_causal_observation_scan":
        raise ValueError("observation scan must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_arbiter_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "labels_generated_in_this_slice",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_observations"] != 0:
        raise ValueError("Stage 7 observations must remain excluded")


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# KRK Selected Provider Diversity Observation Scan v0",
        "",
        "This is a bounded selection-only observation scan. It does not run playout labels, "
        "implement a selector, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
        f"- Observations: `{summary['observation_count']}`",
        f"- Provider family counts: `{summary['selected_provider_family_counts']}`",
        f"- Stage counts: `{summary['selected_stage_counts']}`",
        f"- Distinct selected provider families: `{summary['distinct_selected_provider_families']}`",
        f"- Max selected provider family dominance: `{summary['max_selected_provider_family_dominance']}`",
        f"- Stage 7 observations: `{summary['stage7_observations']}`",
        f"- Wall time seconds: `{summary['wall_time_seconds']}`",
        "",
        "## Decision",
        "",
        f"- Status: `{payload['decision']['status']}`",
        f"- Recommended next step: `{payload['decision']['recommended_next_step']}`",
        "- Runtime arbiter and selector sandbox remain blocked.",
        "",
        "## Observations",
        "",
    ]
    for obs in payload["observations"]:
        lines.append(
            f"- `{obs['job_id']}` stage=`{obs['source_stage']}` "
            f"provider=`{obs['selected_provider_id']}` family=`{obs['selected_provider_family']}` "
            f"move=`{obs['selected_move']}`"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run_observations()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
