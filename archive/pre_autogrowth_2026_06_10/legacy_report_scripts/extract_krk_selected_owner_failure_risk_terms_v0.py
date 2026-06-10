#!/usr/bin/env python3
"""Extract visible selected-owner failure-risk proxy terms non-causally."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROXY_DATASET = Path("reports/krk_state_local_paired_runtime_proxy_dataset_v0.json")
CONTEXT_DATASET = Path("reports/krk_ownership_selection_context_dataset_v3.json")

OUT_TERMS_JSON = Path("reports/krk_selected_owner_failure_risk_visible_terms_v0.json")
OUT_TERMS_MD = Path("reports/krk_selected_owner_failure_risk_visible_terms_v0.md")
OUT_PROBE_JSON = Path("reports/krk_selected_owner_failure_risk_visible_proxy_probe_v0.json")
OUT_PROBE_MD = Path("reports/krk_selected_owner_failure_risk_visible_proxy_probe_v0.md")
OUT_REVIEW_JSON = Path("reports/krk_selected_owner_failure_risk_visible_proxy_review_v0.json")
OUT_REVIEW_MD = Path("reports/krk_selected_owner_failure_risk_visible_proxy_review_v0.md")


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


def _nested(row: dict[str, Any], path: str) -> Any:
    value: Any = row
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _context_index() -> dict[tuple[str, str], dict[str, Any]]:
    payload = _load(CONTEXT_DATASET)
    if payload.get("causal_status") != "non_causal_context_feature_dataset":
        raise ValueError("context dataset must remain non-causal")
    return {
        (str(row.get("state_id")), str(row.get("provider_id"))): row
        for row in payload.get("rows") or []
        if row.get("source_stage") != "stage7"
    }


def _source_terms(context: dict[str, Any]) -> set[str]:
    return {str(term) for term in context.get("source_terms") or []}


def _stagnation_terms(context: dict[str, Any]) -> dict[str, Any]:
    playout = context.get("selected_playout_success") or {}
    summary = playout.get("stagnation_summary") or {}
    return {
        "selected_owner_trace_available": bool(summary),
        "selected_owner_rook_oscillation_visible": summary.get("rook_oscillation_detected") is True
        or summary.get("rook_oscillation_loop") is True,
        "selected_owner_no_edge_progress_visible": summary.get("no_edge_progress_recently") is True,
        "selected_owner_no_mate_progress_visible": summary.get("no_mate_progress_recently") is True,
        "selected_owner_repeated_state_visible": int(summary.get("repeated_state_count") or 0) > 0,
        "selected_owner_no_progress_plies": summary.get("no_progress_plies"),
    }


def _candidate_terms(row: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    runtime = row.get("runtime_visible_candidate_features") or {}
    source_terms = _source_terms(context)
    selected_king_no_box_progress = (
        runtime.get("selected_piece") == "king"
        and runtime.get("box_area_delta") == "same"
    )
    selected_king_worsens_rook_support = (
        runtime.get("selected_piece") == "king"
        and runtime.get("rook_distance_delta") == "worsens"
    )
    stage0_vs_edge_trap_selected_king_stalls_box = (
        runtime.get("family_pair") == "stage0_basin->edge_trap"
        and selected_king_no_box_progress
        and selected_king_worsens_rook_support
    )
    edge_trap_drive_context_rook_expands_box = (
        runtime.get("family_pair") == "edge_trap->stage0_basin"
        and runtime.get("active_landmark_label") == "drive_to_edge"
        and runtime.get("selected_piece") == "rook"
        and runtime.get("box_area_delta") == "worsens"
    )
    source_contention = {
        "wrong_tempo_detected": "wrong_tempo_detected" in source_terms,
        "fence_needs_repair": "fence_needs_repair" in source_terms,
        "post_fence_conversion_needed": "post_fence_conversion_needed" in source_terms,
        "edge_trap_geometry_visible": "edge_trap_close_geometry" in source_terms
        or "edge_trap_shape_available" in source_terms,
        "king_support_improvement_available": "king_support_improvement_move_exists" in source_terms
        or "white_king_can_improve_support" in source_terms,
    }
    stagnation = _stagnation_terms(context)
    visible_proxy_v0 = stage0_vs_edge_trap_selected_king_stalls_box or edge_trap_drive_context_rook_expands_box
    return {
        "selected_king_no_box_progress": selected_king_no_box_progress,
        "selected_king_worsens_rook_support": selected_king_worsens_rook_support,
        "stage0_vs_edge_trap_selected_king_stalls_box": stage0_vs_edge_trap_selected_king_stalls_box,
        "edge_trap_drive_context_rook_expands_box": edge_trap_drive_context_rook_expands_box,
        "selected_owner_context_contention_visible": any(source_contention.values()),
        "selected_owner_trace_stagnation_visible": any(
            value is True for key, value in stagnation.items() if key != "selected_owner_trace_available"
        ),
        "selected_owner_failure_risk_proxy_v0": visible_proxy_v0,
        "source_contention_terms": source_contention,
        "trace_progress_terms": stagnation,
        "requires_visible_competing_provider_proposal": True,
        "causal_status": "non_causal_visible_proxy_term",
    }


def _classification_metrics(rows: list[dict[str, Any]], term_name: str) -> dict[str, Any]:
    tp = sum(1 for row in rows if row["extracted_terms"].get(term_name) and row["selected_owner_failure_risk_target"])
    fp = sum(1 for row in rows if row["extracted_terms"].get(term_name) and not row["selected_owner_failure_risk_target"])
    tn = sum(1 for row in rows if not row["extracted_terms"].get(term_name) and not row["selected_owner_failure_risk_target"])
    fn = sum(1 for row in rows if not row["extracted_terms"].get(term_name) and row["selected_owner_failure_risk_target"])
    return {
        "term_name": term_name,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "safe_preservation_recall": tn / (tn + fp) if tn + fp else None,
    }


def build_terms() -> dict[str, Any]:
    proxy = _load(PROXY_DATASET)
    if proxy.get("causal_status") != "non_causal_proxy_validation_dataset":
        raise ValueError("proxy dataset must remain non-causal")
    contexts = _context_index()
    rows: list[dict[str, Any]] = []
    for row in proxy.get("rows") or []:
        if row.get("source_stage") == "stage7":
            continue
        owner_a = str(row.get("owner_a") or "")
        context = contexts.get((str(row.get("state_id")), owner_a), {})
        extracted_terms = _candidate_terms(row, context)
        rows.append(
            {
                "schema_version": "krk_selected_owner_failure_risk_visible_term_row.v0",
                "causal_status": "non_causal_visible_proxy_term_row",
                "state_id": row.get("state_id"),
                "source_stage": row.get("source_stage"),
                "owner_a": row.get("owner_a"),
                "owner_b": row.get("owner_b"),
                "comparison_label": row.get("comparison_label"),
                "selected_owner_failure_risk_target": row.get("selected_owner_failure_risk_target") is True,
                "safe_preservation_confidence_target": row.get("safe_preservation_confidence_target") is True,
                "runtime_visible_candidate_features": row.get("runtime_visible_candidate_features"),
                "context_join_found": bool(context),
                "extracted_terms": extracted_terms,
                "usable_for_selector_training": False,
                "runtime_behavior_allowed": False,
            }
        )
    term_names = [
        "selected_king_no_box_progress",
        "selected_king_worsens_rook_support",
        "stage0_vs_edge_trap_selected_king_stalls_box",
        "edge_trap_drive_context_rook_expands_box",
        "selected_owner_context_contention_visible",
        "selected_owner_trace_stagnation_visible",
        "selected_owner_failure_risk_proxy_v0",
    ]
    summary = {
        "row_count": len(rows),
        "state_count": len({row.get("state_id") for row in rows}),
        "failure_risk_target_count": sum(1 for row in rows if row["selected_owner_failure_risk_target"]),
        "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
        "selector_training_row_count": sum(1 for row in rows if row.get("usable_for_selector_training")),
        "context_join_count": sum(1 for row in rows if row.get("context_join_found")),
        "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
        "term_metrics": {name: _classification_metrics(rows, name) for name in term_names},
    }
    payload = {
        "schema_version": "krk_selected_owner_failure_risk_visible_terms.v0",
        "causal_status": "non_causal_visible_proxy_terms",
        **_runtime_false_block(),
        "implementation_allowed_by_this_artifact": False,
        "source_artifacts": [str(PROXY_DATASET), str(CONTEXT_DATASET)],
        "candidate_terms": [
            {
                "term_id": "selected_king_no_box_progress",
                "meaning": "Selected owner proposes a king move that does not reduce the box proxy.",
                "runtime_visibility": "candidate_move_frame_or_selected_suggestion_metadata",
                "causal_status": "non_causal_candidate",
            },
            {
                "term_id": "stage0_vs_edge_trap_selected_king_stalls_box",
                "meaning": "Stage0 owns while an edge-trap alternative is under comparison and the selected king move stalls box progress.",
                "runtime_visibility": "requires visible competing provider proposal plus move-shape terms",
                "causal_status": "non_causal_candidate",
            },
            {
                "term_id": "edge_trap_drive_context_rook_expands_box",
                "meaning": "Edge-trap owns in drive context while selected rook move expands the box proxy.",
                "runtime_visibility": "requires visible competing provider proposal plus move-shape terms",
                "causal_status": "non_causal_candidate",
            },
            {
                "term_id": "selected_owner_trace_stagnation_visible",
                "meaning": "A recent owner window exposes oscillation or no-progress terms.",
                "runtime_visibility": "only after a visible owner/plan window, not initial move selection",
                "causal_status": "non_causal_candidate",
            },
        ],
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": "visible_failure_risk_terms_extracted_for_probe",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": "probe_visible_failure_risk_proxy_terms",
        },
    }
    _validate_non_causal(payload)
    return payload


def build_probe(terms: dict[str, Any]) -> dict[str, Any]:
    metrics = terms["summary"]["term_metrics"]
    composite = metrics["selected_owner_failure_risk_proxy_v0"]
    review_threshold_met = (
        (composite.get("precision") or 0.0) >= 0.70
        and (composite.get("recall") or 0.0) >= 0.70
        and (composite.get("safe_preservation_recall") or 0.0) >= 0.80
        and terms["summary"]["stage7_row_count"] == 0
    )
    payload = {
        "schema_version": "krk_selected_owner_failure_risk_visible_proxy_probe.v0",
        "causal_status": "non_causal_visible_proxy_probe",
        **_runtime_false_block(),
        "implementation_allowed_by_this_probe": False,
        "source_artifacts": [str(OUT_TERMS_JSON)],
        "summary": {
            "row_count": terms["summary"]["row_count"],
            "failure_risk_target_count": terms["summary"]["failure_risk_target_count"],
            "stage7_row_count": terms["summary"]["stage7_row_count"],
            "selected_owner_failure_risk_proxy_precision": composite.get("precision"),
            "selected_owner_failure_risk_proxy_recall": composite.get("recall"),
            "safe_preservation_recall": composite.get("safe_preservation_recall"),
            "review_threshold_met": review_threshold_met,
        },
        "term_metrics": metrics,
        "candidate_proxy": {
            "term_id": "selected_owner_failure_risk_proxy_v0",
            "definition": (
                "stage0_vs_edge_trap_selected_king_stalls_box OR "
                "edge_trap_drive_context_rook_expands_box"
            ),
            "requires_visible_competing_provider_proposal": True,
            "requires_out_of_sample_validation": True,
            "causal_status": "non_causal_candidate",
            **composite,
        },
        "decision": {
            "status": (
                "visible_failure_risk_proxy_candidate_needs_out_of_sample_validation"
                if review_threshold_met
                else "visible_failure_risk_proxy_terms_insufficient"
            ),
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": (
                "validate_proxy_candidate_on_independent_protected_pairs"
                if review_threshold_met
                else "design_better_visible_failure_risk_terms"
            ),
        },
    }
    _validate_non_causal(payload)
    return payload


def build_review(terms: dict[str, Any], probe: dict[str, Any]) -> dict[str, Any]:
    threshold_met = probe["summary"]["review_threshold_met"]
    payload = {
        "schema_version": "krk_selected_owner_failure_risk_visible_proxy_review.v0",
        "causal_status": "non_causal_architecture_review",
        **_runtime_false_block(),
        "implementation_allowed_by_this_review": False,
        "source_artifacts": [str(OUT_TERMS_JSON), str(OUT_PROBE_JSON)],
        "summary": {
            "row_count": terms["summary"]["row_count"],
            "stage7_row_count": terms["summary"]["stage7_row_count"],
            "proxy_precision": probe["summary"]["selected_owner_failure_risk_proxy_precision"],
            "proxy_recall": probe["summary"]["selected_owner_failure_risk_proxy_recall"],
            "safe_preservation_recall": probe["summary"]["safe_preservation_recall"],
            "review_threshold_met_on_current_dataset": threshold_met,
        },
        "interpretation": [
            "The selected-owner failure-risk blocker can be expressed as visible proxy candidates on the current protected paired dataset.",
            "The strongest candidate is not an outcome label: it uses provider-family comparison, active context, and selected move-shape/post-move terms.",
            "It still requires a visible competing-provider proposal source and out-of-sample validation before any runtime-review packet.",
            "This artifact does not authorize runtime selector behavior, causal terminals, topology mutation, Stage 7 promotion, or Stage 8 training.",
        ],
        "remaining_blockers": [
            "The candidate was discovered on the same paired dataset that it fits; independent protected-pair validation is required.",
            "A future runtime design must expose same-state competing provider proposals visibly, not as forced-capacity labels.",
            "Trace-window stagnation is currently sparse and only available after ownership has already run.",
        ],
        "decision": {
            "status": (
                "visible_failure_risk_proxy_candidate_identified_not_runtime_ready"
                if threshold_met
                else "visible_failure_risk_proxy_still_blocked"
            ),
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": (
                "independent_protected_proxy_validation_or_runtime_review_question"
                if threshold_met
                else "collect_or_design_more_visible_failure_risk_terms"
            ),
        },
    }
    _validate_non_causal(payload)
    return payload


def _validate_non_causal(payload: dict[str, Any]) -> None:
    if not str(payload.get("causal_status") or "").startswith("non_causal"):
        raise ValueError("payload must remain non-causal")
    for key in RUNTIME_FALSE_KEYS:
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    for key, value in payload.items():
        if key.startswith("implementation_allowed") and value is not False:
            raise ValueError(f"{key} must be false")
    summary = payload.get("summary") or {}
    if summary.get("stage7_row_count", 0) != 0:
        raise ValueError("Stage 7 rows must remain excluded")
    if summary.get("selector_training_row_count", 0) not in {0, None}:
        raise ValueError("selector training rows must remain zero")


def _write_json(repo_root: Path, path: Path, payload: dict[str, Any]) -> None:
    (repo_root / path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render_terms_md(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Selected-Owner Failure-Risk Visible Terms v0",
        "",
        "Non-causal extraction of candidate visible terms for selected-owner failure risk.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        if key == "term_metrics":
            continue
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Term Metrics", ""])
    for name, metrics in payload["summary"]["term_metrics"].items():
        lines.append(
            f"- `{name}`: precision=`{metrics.get('precision')}`, recall=`{metrics.get('recall')}`, "
            f"safe_preservation_recall=`{metrics.get('safe_preservation_recall')}`"
        )
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def _render_probe_md(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Selected-Owner Failure-Risk Visible Proxy Probe v0",
        "",
        "Non-causal probe of visible failure-risk proxy candidates.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Candidate Proxy", ""])
    for key, value in payload["candidate_proxy"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def _render_review_md(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Selected-Owner Failure-Risk Visible Proxy Review v0",
        "",
        "Architecture review of visible selected-owner failure-risk proxy candidates.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    for item in payload["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Remaining Blockers", ""])
    for item in payload["remaining_blockers"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def write_outputs(repo_root: Path, terms: dict[str, Any], probe: dict[str, Any], review: dict[str, Any]) -> None:
    _write_json(repo_root, OUT_TERMS_JSON, terms)
    (repo_root / OUT_TERMS_MD).write_text(_render_terms_md(terms), encoding="utf-8")
    _write_json(repo_root, OUT_PROBE_JSON, probe)
    (repo_root / OUT_PROBE_MD).write_text(_render_probe_md(probe), encoding="utf-8")
    _write_json(repo_root, OUT_REVIEW_JSON, review)
    (repo_root / OUT_REVIEW_MD).write_text(_render_review_md(review), encoding="utf-8")


def build_all() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    terms = build_terms()
    probe = build_probe(terms)
    review = build_review(terms, probe)
    return terms, probe, review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    terms, probe, review = build_all()
    write_outputs(repo_root, terms, probe, review)
    print(json.dumps(review["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
