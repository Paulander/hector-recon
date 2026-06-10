#!/usr/bin/env python3
"""Build non-causal selected-owner failure-risk evidence v1.

The v1 evidence separates two visible tracks:

* competing-proposal evidence available before ownership changes;
* progress-window evidence available only after the selected owner has run.

It intentionally keeps outcome labels and forced-provider labels as offline
validation targets, not runtime inputs.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PROXY_DATASET = Path("reports/krk_state_local_paired_runtime_proxy_dataset_v0.json")
INVENTORY = Path("reports/krk_state_local_paired_ownership_inventory_v1.json")
INDEPENDENT_LABELS = Path("reports/krk_selected_owner_failure_risk_proxy_independent_labels_v0.json")
CONTEXT_DATASET = Path("reports/krk_ownership_selection_context_dataset_v3.json")
RANKED_FRAMES = Path("reports/krk_ranked_strategy_proposal_frames_v1.json")

OUT_JSON = Path("reports/krk_selected_owner_failure_risk_evidence_v1.json")
OUT_MD = Path("reports/krk_selected_owner_failure_risk_evidence_v1.md")

RUNTIME_FALSE_KEYS = (
    "runtime_behavior_changed",
    "runtime_defaults_changed",
    "runtime_selector_implemented",
    "runtime_candidate_generator_implemented",
    "runtime_terminals_added",
    "runtime_dtm_or_tablebase_lookup",
    "gameplay_topology_mutation",
    "stage7_promotion_allowed",
    "stage8_training_allowed",
    "selector_training_allowed",
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _runtime_false_block() -> dict[str, bool]:
    return {key: False for key in RUNTIME_FALSE_KEYS}


def _provider_family(provider_id: str | None) -> str:
    text = str(provider_id or "")
    if text == "krk.stage0_basin":
        return "stage0_basin"
    if text == "krk.drive_to_edge":
        return "drive_to_edge"
    if text == "krk.fence_established":
        return "fence_established"
    if text.startswith("krk.edge_trap"):
        return "edge_trap"
    if text == "stage0_basin" or text == "drive_to_edge" or text == "fence_established" or text == "edge_trap":
        return text
    return "other"


def _proposal_index() -> dict[str, list[dict[str, Any]]]:
    payload = _load(RANKED_FRAMES)
    if payload.get("causal_status") != "non_causal_ranked_frame_dataset":
        raise ValueError("ranked proposal frames must remain non-causal")
    index: dict[str, list[dict[str, Any]]] = {}
    for row in payload.get("rows") or []:
        if row.get("stage7_challenge_row") is True:
            continue
        index.setdefault(str(row.get("state_id")), []).append(row)
    return index


def _context_index() -> dict[tuple[str, str], dict[str, Any]]:
    payload = _load(CONTEXT_DATASET)
    if payload.get("causal_status") != "non_causal_context_feature_dataset":
        raise ValueError("context dataset must remain non-causal")
    return {
        (str(row.get("state_id")), str(row.get("provider_id"))): row
        for row in payload.get("rows") or []
        if row.get("stage7_training_row") is not True
    }


def _inventory_index() -> dict[tuple[str, str, str], dict[str, Any]]:
    payload = _load(INVENTORY)
    if payload.get("causal_status") != "non_causal_pair_inventory":
        raise ValueError("paired ownership inventory must remain non-causal")
    return {
        (str(row.get("state_id")), str(row.get("owner_a")), str(row.get("owner_b"))): row
        for row in payload.get("rows") or []
        if row.get("stage7_training_row") is not True
    }


def _best_proposal(frames: list[dict[str, Any]], provider_id: str | None) -> dict[str, Any] | None:
    provider_id = str(provider_id or "")
    candidates = [row for row in frames if row.get("provider_id") == provider_id]
    if not candidates:
        return None
    return sorted(candidates, key=lambda row: row.get("provider_local_rank") or 9999)[0]


def _competing_proposal_evidence(
    *,
    frames: list[dict[str, Any]],
    owner_a: str | None,
    owner_b: str | None,
) -> dict[str, Any]:
    selected = _best_proposal(frames, owner_a)
    alternative = _best_proposal(frames, owner_b)
    selected_score = selected.get("raw_score") if selected else None
    alternative_score = alternative.get("raw_score") if alternative else None
    score_gap = None
    if isinstance(selected_score, (int, float)) and isinstance(alternative_score, (int, float)):
        score_gap = float(selected_score) - float(alternative_score)
    selected_move = selected.get("move_uci") if selected else None
    alternative_move = alternative.get("move_uci") if alternative else None
    if selected_move is None or alternative_move is None:
        move_relation = "missing"
    elif selected_move == alternative_move:
        move_relation = "same_move"
    else:
        move_relation = "distinct_move"
    families = sorted({_provider_family(row.get("provider_id")) for row in frames})
    return {
        "state_strategy_proposal_count": len(frames),
        "state_strategy_proposal_families": families,
        "selected_owner_live_proposal": selected is not None,
        "alternative_provider_live_proposal": alternative is not None,
        "alternative_provider_role_licensed": bool((alternative or {}).get("role_licenses")),
        "alternative_provider_score_visible": alternative_score is not None,
        "selected_owner_score_visible": selected_score is not None,
        "selected_owner_score_gap_visible": score_gap is not None,
        "selected_minus_alternative_raw_score": score_gap,
        "same_state_provider_conflict_visible": selected is not None and alternative is not None,
        "alternative_provider_same_move_or_distinct_move": move_relation,
    }


def _progress_window_from_summary(summary: dict[str, Any] | None) -> dict[str, Any]:
    summary = summary or {}
    no_progress_plies = summary.get("no_progress_plies")
    trace_available = bool(summary)
    no_edge = summary.get("no_edge_progress_recently") is True
    no_mate = summary.get("no_mate_progress_recently") is True
    repeated = int(summary.get("repeated_state_count") or summary.get("repeated_abstract_state_count") or 0) > 0
    oscillation = summary.get("rook_oscillation_detected") is True or summary.get("rook_oscillation_loop") is True
    return {
        "selected_owner_trace_available": trace_available,
        "selected_owner_no_edge_progress": no_edge,
        "selected_owner_no_mate_progress": no_mate,
        "selected_owner_rook_oscillation": oscillation,
        "selected_owner_repeated_abstract_state": repeated,
        "selected_owner_no_progress_plies": no_progress_plies,
        "selected_owner_handoff_gap": summary.get("handoff_gap") is True,
        "safe_loop_breaking_move_available": summary.get("safe_loop_breaking_move_available"),
        "progress_window_failure_visible": trace_available and (no_edge or no_mate or repeated or oscillation),
    }


def _progress_window_from_context(context: dict[str, Any] | None) -> dict[str, Any]:
    playout = (context or {}).get("selected_playout_success") or {}
    return _progress_window_from_summary(playout.get("stagnation_summary"))


def _label_row_from_proxy(
    row: dict[str, Any],
    *,
    proposals: dict[str, list[dict[str, Any]]],
    contexts: dict[tuple[str, str], dict[str, Any]],
    inventory: dict[tuple[str, str, str], dict[str, Any]],
) -> dict[str, Any]:
    state_id = str(row.get("state_id"))
    owner_a = str(row.get("owner_a"))
    owner_b = str(row.get("owner_b"))
    runtime_features = row.get("runtime_visible_candidate_features") or {}
    inv = inventory.get((state_id, owner_a, owner_b), {})
    context = contexts.get((state_id, owner_a), {})
    return {
        "schema_version": "krk_selected_owner_failure_risk_evidence_row.v1",
        "causal_status": "non_causal_failure_risk_evidence",
        "evidence_split": "discovery_proxy_dataset",
        "state_id": state_id,
        "frame_id": row.get("frame_id"),
        "source_stage": row.get("source_stage"),
        "active_landmark_label": row.get("active_landmark_label"),
        "owner_a": owner_a,
        "owner_b": owner_b,
        "owner_a_family": _provider_family(owner_a),
        "owner_b_family": _provider_family(owner_b),
        "comparison_label": row.get("comparison_label"),
        "selected_owner_failure_risk_target": row.get("selected_owner_failure_risk_target") is True,
        "safe_preservation_confidence_target": row.get("safe_preservation_confidence_target") is True,
        "selected_owner_result": (row.get("offline_outcome_forbidden_features") or {}).get("owner_a_outcome"),
        "alternative_result": (row.get("offline_outcome_forbidden_features") or {}).get("owner_b_outcome"),
        "runtime_visible_candidate_features": runtime_features,
        "competing_proposal_evidence": _competing_proposal_evidence(
            frames=proposals.get(state_id, []),
            owner_a=owner_a,
            owner_b=owner_b,
        ),
        "progress_window_evidence": _progress_window_from_context(context),
        "inventory_evidence_channel": inv.get("evidence_channel"),
        "stage7_training_row": False,
        "usable_for_selector_training": False,
        "runtime_behavior_allowed": False,
    }


def _label_row_from_independent(row: dict[str, Any]) -> dict[str, Any]:
    runtime_features = row.get("runtime_visible_candidate_features") or {}
    selected = row.get("selected_playout_success") or {}
    forced = row.get("forced_alternative_result") or {}
    owner_a_family = str(runtime_features.get("selected_owner_family") or "unknown")
    owner_b = str(row.get("forced_alternative_provider") or "")
    return {
        "schema_version": "krk_selected_owner_failure_risk_evidence_row.v1",
        "causal_status": "non_causal_failure_risk_evidence",
        "evidence_split": "independent_validation_label",
        "state_id": row.get("frame_id"),
        "frame_id": row.get("frame_id"),
        "fen": row.get("fen"),
        "source_stage": runtime_features.get("source_stage"),
        "active_landmark_label": row.get("active_landmark_label"),
        "owner_a": owner_a_family,
        "owner_b": owner_b,
        "owner_a_family": owner_a_family,
        "owner_b_family": _provider_family(owner_b),
        "comparison_label": "independent_validation_label",
        "selected_owner_failure_risk_target": row.get("selected_owner_failure_risk_target") is True,
        "safe_preservation_confidence_target": row.get("safe_preservation_confidence_target") is True,
        "selected_owner_result": selected.get("result"),
        "alternative_result": forced.get("result"),
        "runtime_visible_candidate_features": runtime_features,
        "competing_proposal_evidence": _competing_proposal_evidence(frames=[], owner_a=None, owner_b=None),
        "progress_window_evidence": _progress_window_from_summary(selected.get("stagnation_summary")),
        "inventory_evidence_channel": None,
        "stage7_training_row": False,
        "usable_for_selector_training": False,
        "runtime_behavior_allowed": False,
    }


def build_evidence() -> dict[str, Any]:
    proxy = _load(PROXY_DATASET)
    if proxy.get("causal_status") != "non_causal_proxy_validation_dataset":
        raise ValueError("runtime proxy dataset must remain non-causal")
    independent = _load(INDEPENDENT_LABELS)
    proposals = _proposal_index()
    contexts = _context_index()
    inventory = _inventory_index()
    rows = [
        _label_row_from_proxy(row, proposals=proposals, contexts=contexts, inventory=inventory)
        for row in proxy.get("rows") or []
        if row.get("stage7_training_row") is not True
    ]
    rows.extend(_label_row_from_independent(row) for row in independent.get("labels") or [])

    split_counts = Counter(str(row.get("evidence_split")) for row in rows)
    target_counts = Counter(
        "failure_risk" if row.get("selected_owner_failure_risk_target") else "safe_preservation"
        for row in rows
    )
    proposal_rows = [row for row in rows if row["competing_proposal_evidence"]["alternative_provider_live_proposal"]]
    progress_rows = [row for row in rows if row["progress_window_evidence"]["selected_owner_trace_available"]]
    payload = {
        "schema_version": "krk_selected_owner_failure_risk_evidence.v1",
        "causal_status": "non_causal_failure_risk_evidence",
        **_runtime_false_block(),
        "implementation_allowed_by_this_evidence": False,
        "source_artifacts": [
            str(PROXY_DATASET),
            str(INVENTORY),
            str(INDEPENDENT_LABELS),
            str(CONTEXT_DATASET),
            str(RANKED_FRAMES),
        ],
        "summary": {
            "row_count": len(rows),
            "stage7_row_count": sum(1 for row in rows if row.get("stage7_training_row")),
            "selector_training_row_count": sum(1 for row in rows if row.get("usable_for_selector_training")),
            "split_counts": dict(split_counts),
            "target_counts": dict(target_counts),
            "alternative_live_proposal_count": len(proposal_rows),
            "progress_window_trace_count": len(progress_rows),
            "progress_window_failure_count": sum(
                1 for row in rows if row["progress_window_evidence"]["progress_window_failure_visible"]
            ),
        },
        "evidence_tracks": {
            "visible_competing_proposal": {
                "status": "sparse_or_missing_for_alternatives",
                "alternative_live_proposal_count": len(proposal_rows),
                "note": "Ranked proposal frames mostly expose the selected owner; forced alternatives are usually offline labels, not live proposals.",
            },
            "progress_window": {
                "status": "available_when_selected_owner_trace_exists",
                "trace_count": len(progress_rows),
                "note": "Progress-window evidence is visible only after the selected owner has already run; it is monitor evidence, not an initial pre-decision selector input.",
            },
        },
        "rows": rows,
        "decision": {
            "status": "failure_risk_evidence_v1_built",
            "recommended_next_step": "probe_selected_owner_failure_risk_proxy_v1",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
        },
    }
    for key in RUNTIME_FALSE_KEYS:
        if payload[key] is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_row_count"] != 0:
        raise ValueError("Stage 7 rows must not enter readiness evidence")
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# KRK Selected-Owner Failure-Risk Evidence v1",
        "",
        "## Summary",
        "",
        f"- rows: `{summary['row_count']}`",
        f"- Stage 7 readiness rows: `{summary['stage7_row_count']}`",
        f"- selector-training rows: `{summary['selector_training_row_count']}`",
        f"- split counts: `{summary['split_counts']}`",
        f"- target counts: `{summary['target_counts']}`",
        f"- alternative live proposal rows: `{summary['alternative_live_proposal_count']}`",
        f"- progress-window trace rows: `{summary['progress_window_trace_count']}`",
        f"- progress-window failure rows: `{summary['progress_window_failure_count']}`",
        "",
        "## Evidence Tracks",
        "",
    ]
    for track, data in payload["evidence_tracks"].items():
        lines.append(f"- `{track}`: `{data['status']}`. {data['note']}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This evidence is non-causal. Forced-provider outcomes and selected-owner outcomes are labels only; they are not runtime inputs.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_evidence()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
