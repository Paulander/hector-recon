#!/usr/bin/env python3
"""Join selector target labels with trace-only observation features."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TARGETS = Path("reports/krk_selector_target_dataset_v0.json")
OBSERVATIONS = Path("reports/krk_strategy_arbiter_labeled_observation_controls_v0.json")
OUT_JSON = Path("reports/krk_selector_feature_dataset_v0.json")
OUT_MD = Path("reports/krk_selector_feature_dataset_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _observation_by_state(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in payload.get("records", []) or []:
        state_id = str(record.get("state_id") or "")
        if state_id:
            result[state_id] = record
    return result


def _provider_candidate_features(observation: dict[str, Any], provider_id: str | None) -> dict[str, Any]:
    candidates = [
        item for item in observation.get("provider_candidates", []) or []
        if isinstance(item, dict)
    ]
    matching = [
        item for item in candidates
        if provider_id and str(item.get("provider_id") or "") == provider_id
    ]
    provider_summary = dict(observation.get("provider_summary", {}) or {})
    return {
        "target_provider_in_top_candidates": bool(matching),
        "target_provider_in_provider_summary": bool(provider_id and provider_id in provider_summary),
        "target_provider_summary_count": int(provider_summary.get(provider_id, 0) or 0) if provider_id else 0,
        "target_provider_best_rank": min(
            (int(item.get("provider_local_rank", 9999) or 9999) for item in matching),
            default=None,
        ),
        "target_provider_best_raw_score": max(
            (float(item.get("raw_score", 0.0) or 0.0) for item in matching),
            default=None,
        ),
    }


def build_dataset(root: Path = ROOT) -> dict[str, Any]:
    targets = _load_json(TARGETS)
    observations = _observation_by_state(_load_json(OBSERVATIONS))
    rows: list[dict[str, Any]] = []
    for row in targets.get("rows", []) or []:
        state_id = str(row.get("state_id") or "")
        obs_record = observations.get(state_id, {})
        observation = dict(obs_record.get("observation", {}) or {})
        source_terms = list(observation.get("source_terms", []) or [])
        provider_id = row.get("provider_id")
        joined = {
            "schema_version": "krk_selector_feature_example.v0",
            "causal_status": "non_causal_feature_example",
            "state_id": state_id,
            "frame_id": row.get("frame_id"),
            "source_stage": row.get("source_stage"),
            "active_landmark_label": row.get("active_landmark_label"),
            "target_kind": row.get("target_kind"),
            "split": row.get("split"),
            "provider_id": provider_id,
            "move_uci": row.get("move_uci"),
            "label": row.get("label"),
            "usable_for_training": bool(row.get("usable_for_training")),
            "held_out_challenge": row.get("target_kind") == "held_out_challenge",
            "observation_present": bool(observation),
            "selected_provider_before_observation": observation.get(
                "selected_provider_before_observation"
            ),
            "selected_provider_matches_target": bool(
                provider_id
                and observation.get("selected_provider_before_observation") == provider_id
            ),
            "source_terms": source_terms,
            "source_term_count": len(source_terms),
            "unique_provider_count": int(observation.get("unique_provider_count", 0) or 0),
            "all_suggestion_count": int(observation.get("all_suggestion_count", 0) or 0),
            "provider_summary": dict(observation.get("provider_summary", {}) or {}),
        }
        joined.update(_provider_candidate_features(observation, provider_id))
        rows.append(joined)
    stage_counts = Counter(str(row.get("source_stage") or "unknown") for row in rows)
    label_counts = Counter(str(row.get("label") or "none") for row in rows)
    target_counts = Counter(str(row.get("target_kind") or "unknown") for row in rows)
    training_rows = [row for row in rows if row.get("usable_for_training")]
    return {
        "schema_version": "krk_selector_feature_dataset.v0",
        "causal_status": "non_causal_feature_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifacts": [str(TARGETS), str(OBSERVATIONS)],
        "row_count": len(rows),
        "training_row_count": len(training_rows),
        "stage_counts": dict(sorted(stage_counts.items())),
        "target_kind_counts": dict(sorted(target_counts.items())),
        "label_counts": dict(sorted(label_counts.items())),
        "rows_with_observation": sum(1 for row in rows if row["observation_present"]),
        "stage7_training_rows": sum(
            1 for row in training_rows if row.get("source_stage") == "stage7"
        ),
        "rows": rows,
        "decision": {
            "status": "selector_feature_dataset_built",
            "runtime_arbiter_allowed": False,
            "sandbox_ready": False,
            "recommended_next_step": "probe_selector_feature_baselines_non_causal",
        },
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# KRK Selector Feature Dataset v0",
        "",
        "This replay-free dataset joins explicit selector targets with trace-only observation features.",
        "",
        "## Summary",
        "",
        f"- Rows: `{payload['row_count']}`",
        f"- Training rows: `{payload['training_row_count']}`",
        f"- Rows with observation: `{payload['rows_with_observation']}`",
        f"- Stage counts: `{payload['stage_counts']}`",
        f"- Target kind counts: `{payload['target_kind_counts']}`",
        f"- Label counts: `{payload['label_counts']}`",
        f"- Stage7 training rows: `{payload['stage7_training_rows']}`",
        "",
        "## Decision",
        "",
        f"Status: `{payload['decision']['status']}`",
        f"Runtime arbiter allowed: `{payload['decision']['runtime_arbiter_allowed']}`",
        f"Sandbox ready: `{payload['decision']['sandbox_ready']}`",
        f"Recommended next step: `{payload['decision']['recommended_next_step']}`",
    ]
    (ROOT / path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_dataset()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload, OUT_MD)


if __name__ == "__main__":
    main()
