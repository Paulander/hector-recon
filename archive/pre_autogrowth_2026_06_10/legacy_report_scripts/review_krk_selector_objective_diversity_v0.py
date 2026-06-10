#!/usr/bin/env python3
"""Review selector-objective diversity after the joined trace collection path."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COLLECTION = Path("reports/strategy_arbitration/krk_joined_trace_ownership_collection_v0.json")
SEED = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v1.json")
SEED_PROBE = Path("reports/strategy_arbitration/krk_selector_objective_seed_probe_v1.json")
FEATURE_REVIEW = Path("reports/strategy_arbitration/krk_selector_objective_feature_probe_review_v0.json")
OWNERSHIP_CONTEXT = Path("reports/krk_ownership_selection_context_dataset_v3.json")
BRIEF = Path("current_agent_brief.md")
OUT_JSON = Path("reports/strategy_arbitration/krk_selector_objective_diversity_review_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_selector_objective_diversity_review_v0.md")

PROTECTED_STAGES = {"stage5", "stage6"}
EXCLUDED_STAGES = {"stage4", "stage7", "stage8"}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _brief_present(path: Path = BRIEF) -> bool:
    return (ROOT / path).exists()


def _provider_family(row: dict[str, Any]) -> str:
    return str(
        row.get("selected_provider_family")
        or row.get("provider_family")
        or str(row.get("selected_provider") or row.get("provider_id") or "").replace("krk.", "")
        or "unknown"
    )


def _selected_provider(row: dict[str, Any]) -> str:
    return str(row.get("selected_provider") or row.get("provider_id") or "unknown")


def _owner_label(row: dict[str, Any]) -> str:
    return str(row.get("selected_owner_label") or row.get("target_label") or "unknown")


def _stage(row: dict[str, Any]) -> str:
    return str(row.get("source_stage") or row.get("stage") or "unknown")


def _objective_channel(label: str) -> str:
    if label == "selected_owner_failed":
        return "candidate_switch_contrast_seed"
    if label == "selected_owner_converted":
        return "safe_preservation_contrast_seed"
    return "excluded_non_ownership_label"


def _recovery_class(label: str) -> str:
    if label == "selected_owner_failed":
        return "selected_failure_requires_joined_trace_observation"
    if label == "selected_owner_converted":
        return "safe_preservation_requires_joined_trace_observation"
    return "excluded_non_ownership_label"


def _candidate_from_context(row: dict[str, Any], *, reason: str) -> dict[str, Any]:
    label = _owner_label(row)
    return {
        "schema_version": "krk_selector_objective_diverse_collection_candidate.v0",
        "causal_status": "non_causal_collection_candidate",
        "state_id": row.get("state_id"),
        "frame_id": row.get("frame_id"),
        "fen": row.get("fen"),
        "source_stage": _stage(row),
        "active_landmark_label": row.get("active_landmark_label"),
        "selected_provider": _selected_provider(row),
        "selected_provider_family": _provider_family(row),
        "selected_owner_label": label,
        "objective_channel": _objective_channel(label),
        "recovery_class": _recovery_class(label),
        "priority_reason": reason,
        "stage7_training_row": False,
        "usable_for_selector_training": False,
        "requires_explicit_collection_approval": True,
    }


def _stage5_6_ownership_rows(ownership_context: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in ownership_context.get("rows") or []:
        if not isinstance(row, dict):
            continue
        stage = _stage(row)
        label = _owner_label(row)
        if stage in PROTECTED_STAGES and label in {
            "selected_owner_failed",
            "selected_owner_converted",
        }:
            rows.append(row)
    return rows


def _select_future_candidates(
    ownership_context: dict[str, Any],
    seed: dict[str, Any],
    collection: dict[str, Any],
    *,
    max_rows: int = 8,
) -> list[dict[str, Any]]:
    rows_by_state = {
        str(row.get("state_id") or ""): row for row in _stage5_6_ownership_rows(ownership_context)
    }
    collected_states = {
        str(row.get("state_id") or "")
        for row in collection.get("rows") or []
        if isinstance(row, dict)
    }
    seed_rows = [
        row for row in seed.get("seed_rows") or [] if isinstance(row, dict)
    ]
    seed_states = {str(row.get("state_id") or "") for row in seed_rows}

    priority_states: list[tuple[str, str]] = []
    for row in seed_rows:
        state_id = str(row.get("state_id") or "")
        if state_id in collected_states or state_id not in rows_by_state:
            continue
        label = _owner_label(row)
        family = _provider_family(row)
        if label == "selected_owner_failed" and family != "stage0_basin":
            priority_states.append((state_id, "non_stage0_switch_seed_needs_joined_observation"))
        elif label == "selected_owner_failed":
            priority_states.append((state_id, "switch_seed_needs_joined_observation"))
        elif family != "stage0_basin":
            priority_states.append((state_id, "non_stage0_safe_seed_needs_joined_observation"))

    for row in _stage5_6_ownership_rows(ownership_context):
        state_id = str(row.get("state_id") or "")
        if state_id in collected_states or state_id in seed_states:
            continue
        family = _provider_family(row)
        if family != "stage0_basin":
            priority_states.append((state_id, "unseeded_non_stage0_safe_ownership_row"))

    for row in _stage5_6_ownership_rows(ownership_context):
        state_id = str(row.get("state_id") or "")
        if state_id in collected_states or state_id in {state for state, _ in priority_states}:
            continue
        priority_states.append((state_id, "stage5_6_safe_preservation_fill_row"))

    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for state_id, reason in priority_states:
        if state_id in seen:
            continue
        source = rows_by_state.get(state_id)
        if not source:
            continue
        candidate = _candidate_from_context(source, reason=reason)
        if candidate["source_stage"] in EXCLUDED_STAGES:
            continue
        candidates.append(candidate)
        seen.add(state_id)
        if len(candidates) >= max_rows:
            break
    return candidates


def build_payload(
    *,
    collection: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
    seed_probe: dict[str, Any] | None = None,
    feature_review: dict[str, Any] | None = None,
    ownership_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    collection = collection or _load(COLLECTION)
    seed = seed or _load(SEED)
    seed_probe = seed_probe or _load(SEED_PROBE)
    feature_review = feature_review or _load(FEATURE_REVIEW)
    ownership_context = ownership_context or _load(OWNERSHIP_CONTEXT)

    seed_rows = [row for row in seed.get("seed_rows") or [] if isinstance(row, dict)]
    seed_states = {str(row.get("state_id") or "") for row in seed_rows}
    context_rows = _stage5_6_ownership_rows(ownership_context)
    replay_free_extra = [
        row for row in context_rows if str(row.get("state_id") or "") not in seed_states
    ]
    replay_free_extra_label_counts = Counter(_owner_label(row) for row in replay_free_extra)
    replay_free_extra_family_counts = Counter(_provider_family(row) for row in replay_free_extra)
    replay_free_recovery_enough = (
        replay_free_extra_label_counts["selected_owner_failed"] >= 2
        and sum(
            count
            for family, count in replay_free_extra_family_counts.items()
            if family != "stage0_basin"
        )
        >= 2
    )
    seed_label_counts = Counter(_owner_label(row) for row in seed_rows)
    seed_family_counts = Counter(_provider_family(row) for row in seed_rows)
    seed_stage_counts = Counter(_stage(row) for row in seed_rows)
    collection_family_counts = Counter(
        str(row.get("selected_provider_label") or "unknown")
        for row in collection.get("rows") or []
        if isinstance(row, dict)
    )
    future_candidates = _select_future_candidates(
        ownership_context, seed, collection, max_rows=8
    )
    future_label_counts = Counter(row["selected_owner_label"] for row in future_candidates)
    future_family_counts = Counter(row["selected_provider_family"] for row in future_candidates)
    collection_stage_counts = Counter(row["source_stage"] for row in future_candidates)
    stage0_seed_count = seed_family_counts["stage0_basin"]
    seed_row_count = len(seed_rows)
    stage0_seed_ratio = stage0_seed_count / seed_row_count if seed_row_count else 0.0

    return {
        "schema_version": "krk_selector_objective_diversity_review.v0",
        "causal_status": "non_causal_diversity_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_provider_suppression": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(COLLECTION),
            str(SEED),
            str(SEED_PROBE),
            str(FEATURE_REVIEW),
            str(OWNERSHIP_CONTEXT),
            str(BRIEF),
        ],
        "questions": {
            "what_evidence_is_missing": [
                "more_selected_owner_failed_switch_rows",
                "more_non_stage0_selected_owner_rows",
                "joined_trace_observation_for_non_stage0_seed_rows",
                "provider_family_diversity_beyond_stage0_basin",
                "failure_type_diversity_beyond_current_stage0_basin_failures",
            ],
            "too_few_rows": False,
            "too_few_providers": True,
            "too_few_failure_types": True,
            "too_few_stages": False,
            "stage0_basin_dominance": True,
            "can_recover_more_replay_free_from_existing_artifacts": False,
            "why_replay_free_recovery_is_not_enough": (
                "Stage5/6 replay-free ownership rows not already in the seed set "
                "add safe-preservation rows but do not add enough switch or "
                "non-stage0 ownership evidence, and rows without joined trace "
                "observation should not be promoted into trace/ownership seeds."
            ),
        },
        "summary": {
            "collection_status": (collection.get("decision") or {}).get("status"),
            "seed_probe_status": (seed_probe.get("decision") or {}).get("status"),
            "feature_review_status": (feature_review.get("decision") or {}).get("status"),
            "seed_row_count": seed_row_count,
            "seed_stage_counts": dict(sorted(seed_stage_counts.items())),
            "seed_owner_label_counts": dict(sorted(seed_label_counts.items())),
            "seed_provider_family_counts": dict(sorted(seed_family_counts.items())),
            "seed_stage0_basin_ratio": stage0_seed_ratio,
            "joined_collection_provider_counts": dict(sorted(collection_family_counts.items())),
            "stage5_6_ownership_context_row_count": len(context_rows),
            "replay_free_extra_stage5_6_row_count": len(replay_free_extra),
            "replay_free_extra_owner_label_counts": dict(
                sorted(replay_free_extra_label_counts.items())
            ),
            "replay_free_extra_provider_family_counts": dict(
                sorted(replay_free_extra_family_counts.items())
            ),
            "replay_free_recovery_enough": replay_free_recovery_enough,
            "future_collection_candidate_count": len(future_candidates),
            "future_collection_stage_counts": dict(sorted(collection_stage_counts.items())),
            "future_collection_owner_label_counts": dict(sorted(future_label_counts.items())),
            "future_collection_provider_family_counts": dict(sorted(future_family_counts.items())),
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
            "brief_present": _brief_present(),
        },
        "future_collection_candidates": future_candidates,
        "decision": {
            "status": "selector_objective_diverse_collection_review_ready",
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "write_selector_objective_diverse_collection_review_packet_v0",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Objective Diversity Review v0",
        "",
        "This non-causal review evaluates the selector-objective evidence path after the joined trace/ownership collection and feature probe. It does not authorize selector runtime work.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- runtime_changes_allowed: `{payload['decision']['runtime_changes_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Questions",
        "",
    ]
    for key, value in payload["questions"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Summary", ""])
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Future Collection Candidates", ""])
    for row in payload["future_collection_candidates"]:
        lines.append(
            "- "
            f"`{row['state_id']}` "
            f"stage={row['source_stage']} "
            f"provider={row['selected_provider']} "
            f"label={row['selected_owner_label']} "
            f"reason={row['priority_reason']}"
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
