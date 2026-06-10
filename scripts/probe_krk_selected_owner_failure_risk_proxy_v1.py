#!/usr/bin/env python3
"""Probe selected-owner failure-risk visible proxies v1 non-causally."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path("reports/krk_selected_owner_failure_risk_evidence_v1.json")

OUT_PROBE_JSON = Path("reports/krk_selected_owner_failure_risk_proxy_probe_v1.json")
OUT_PROBE_MD = Path("reports/krk_selected_owner_failure_risk_proxy_probe_v1.md")
OUT_VALIDATION_JSON = Path("reports/krk_selected_owner_failure_risk_proxy_independent_validation_v1.json")
OUT_VALIDATION_MD = Path("reports/krk_selected_owner_failure_risk_proxy_independent_validation_v1.md")
OUT_PACKET_JSON = Path("reports/krk_state_local_paired_selector_runtime_proxy_review_packet_v1.json")
OUT_PACKET_MD = Path("reports/krk_state_local_paired_selector_runtime_proxy_review_packet_v1.md")
OUT_BLOCKER_JSON = Path("reports/krk_selected_owner_failure_risk_proxy_v1_blocker_review.json")
OUT_BLOCKER_MD = Path("reports/krk_selected_owner_failure_risk_proxy_v1_blocker_review.md")

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

THRESHOLDS = {
    "precision": 0.70,
    "recall": 0.70,
    "safe_preservation_recall": 0.80,
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _runtime_false_block() -> dict[str, bool]:
    return {key: False for key in RUNTIME_FALSE_KEYS}


def _metrics(rows: list[dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    false_positives: list[str] = []
    false_negatives: list[str] = []
    for row in rows:
        pred = predicate(row)
        target = row.get("selected_owner_failure_risk_target") is True
        if pred and target:
            tp += 1
        elif pred and not target:
            fp += 1
            false_positives.append(str(row.get("state_id")))
        elif not pred and not target:
            tn += 1
        else:
            fn += 1
            false_negatives.append(str(row.get("state_id")))
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    safe = tn / (tn + fp) if tn + fp else None
    return {
        "row_count": len(rows),
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "precision": precision,
        "recall": recall,
        "safe_preservation_recall": safe,
        "false_positive_state_ids": false_positives[:10],
        "false_negative_state_ids": false_negatives[:10],
    }


def _competing_proposal_proxy(row: dict[str, Any]) -> bool:
    evidence = row.get("competing_proposal_evidence") or {}
    gap = evidence.get("selected_minus_alternative_raw_score")
    return (
        evidence.get("same_state_provider_conflict_visible") is True
        and evidence.get("alternative_provider_live_proposal") is True
        and isinstance(gap, (int, float))
        and gap < 0
    )


def _progress_window_stagnation_proxy(row: dict[str, Any]) -> bool:
    evidence = row.get("progress_window_evidence") or {}
    return (
        evidence.get("selected_owner_trace_available") is True
        and evidence.get("selected_owner_no_edge_progress") is True
        and evidence.get("selected_owner_no_mate_progress") is True
        and (
            evidence.get("selected_owner_repeated_abstract_state") is True
            or evidence.get("selected_owner_rook_oscillation") is True
            or int(evidence.get("selected_owner_no_progress_plies") or 0) >= 4
        )
    )


def _combined_proxy(row: dict[str, Any]) -> bool:
    return _competing_proposal_proxy(row) or _progress_window_stagnation_proxy(row)


def _conservative_safe_preservation_gated_proxy(row: dict[str, Any]) -> bool:
    runtime = row.get("runtime_visible_candidate_features") or {}
    # Only fire on progress-window failure or a live-proposal conflict where the
    # selected owner is not a validated/protected family. This keeps the proxy
    # from converting forced-capacity evidence into a pre-decision override.
    if _progress_window_stagnation_proxy(row):
        return True
    return _competing_proposal_proxy(row) and runtime.get("selected_provider_validated_family") is False


PROXIES: dict[str, Callable[[dict[str, Any]], bool]] = {
    "competing_proposal_proxy": _competing_proposal_proxy,
    "progress_window_stagnation_proxy": _progress_window_stagnation_proxy,
    "combined_competing_or_progress_proxy": _combined_proxy,
    "conservative_safe_preservation_gated_proxy": _conservative_safe_preservation_gated_proxy,
}


def _passes(metrics: dict[str, Any]) -> bool:
    return all(metrics.get(name) is not None and metrics[name] >= value for name, value in THRESHOLDS.items())


def build_probe(evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    evidence = evidence if evidence is not None else _load(EVIDENCE)
    if evidence.get("causal_status") != "non_causal_failure_risk_evidence":
        raise ValueError("evidence must remain non-causal")
    rows = [row for row in evidence.get("rows") or [] if row.get("stage7_training_row") is not True]
    split_counts = Counter(str(row.get("evidence_split")) for row in rows)
    proxy_results: dict[str, Any] = {}
    for name, predicate in PROXIES.items():
        by_split = {
            split: _metrics([row for row in rows if row.get("evidence_split") == split], predicate)
            for split in sorted(split_counts)
        }
        proxy_results[name] = {
            "all_rows": _metrics(rows, predicate),
            "by_split": by_split,
            "independent_validation_passes": _passes(by_split.get("independent_validation_label", {})),
        }
    independent_passing = [
        name for name, result in proxy_results.items() if result["independent_validation_passes"]
    ]
    # Prefer the conservative proxy if it passes; otherwise preserve the first
    # passing proxy for transparent validation review.
    selected_proxy = None
    for name in ("conservative_safe_preservation_gated_proxy", "progress_window_stagnation_proxy", "combined_competing_or_progress_proxy"):
        if name in independent_passing:
            selected_proxy = name
            break
    payload = {
        "schema_version": "krk_selected_owner_failure_risk_proxy_probe.v1",
        "causal_status": "non_causal_proxy_probe",
        **_runtime_false_block(),
        "implementation_allowed_by_this_probe": False,
        "source_artifacts": [str(EVIDENCE)],
        "thresholds": THRESHOLDS,
        "summary": {
            "row_count": len(rows),
            "stage7_row_count": sum(1 for row in rows if row.get("stage7_training_row")),
            "split_counts": dict(split_counts),
            "independent_passing_proxy_count": len(independent_passing),
            "selected_proxy_for_independent_validation": selected_proxy,
        },
        "proxy_results": proxy_results,
        "decision": {
            "status": "proxy_v1_independent_candidate_found" if selected_proxy else "proxy_v1_no_independent_candidate",
            "recommended_next_step": "assemble_independent_validation_v1" if selected_proxy else "write_proxy_v1_blocker_review",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
        },
    }
    if payload["summary"]["stage7_row_count"] != 0:
        raise ValueError("Stage 7 rows must not enter readiness evidence")
    return payload


def build_validation(probe: dict[str, Any], evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    evidence = evidence if evidence is not None else _load(EVIDENCE)
    selected = (probe.get("summary") or {}).get("selected_proxy_for_independent_validation")
    rows = [
        row
        for row in evidence.get("rows") or []
        if row.get("evidence_split") == "independent_validation_label"
        and row.get("stage7_training_row") is not True
    ]
    metrics = _metrics(rows, PROXIES[selected]) if selected else _metrics(rows, lambda _row: False)
    threshold_met = selected is not None and _passes(metrics)
    payload = {
        "schema_version": "krk_selected_owner_failure_risk_proxy_independent_validation.v1",
        "causal_status": "non_causal_proxy_validation",
        **_runtime_false_block(),
        "implementation_allowed_by_this_validation": False,
        "source_artifacts": [str(EVIDENCE), str(OUT_PROBE_JSON)],
        "selected_proxy": selected,
        "metrics": metrics,
        "summary": {
            "label_count": len(rows),
            "stage7_row_count": sum(1 for row in rows if row.get("stage7_training_row")),
            "threshold_met": threshold_met,
            "runtime_scope": "progress_window_monitor_or_reconsideration_only" if selected else "none",
        },
        "decision": {
            "status": "independent_proxy_validation_passed" if threshold_met else "independent_proxy_validation_failed_or_underpowered",
            "recommended_next_step": "create_runtime_review_packet_only" if threshold_met else "write_proxy_v1_blocker_review",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
        },
    }
    return payload


def build_packet(validation: dict[str, Any]) -> dict[str, Any] | None:
    if validation["decision"]["status"] != "independent_proxy_validation_passed":
        return None
    payload = {
        "schema_version": "krk_state_local_paired_selector_runtime_proxy_review_packet.v1",
        "causal_status": "non_causal_runtime_review_packet",
        **_runtime_false_block(),
        "implementation_allowed_by_this_packet": False,
        "source_artifacts": [str(OUT_VALIDATION_JSON), str(OUT_PROBE_JSON), str(EVIDENCE)],
        "selected_proxy": validation.get("selected_proxy"),
        "review_scope": "default_off_progress_window_selected_owner_failure_risk_monitor",
        "summary": {
            "precision": validation["metrics"].get("precision"),
            "recall": validation["metrics"].get("recall"),
            "safe_preservation_recall": validation["metrics"].get("safe_preservation_recall"),
            "label_count": validation["summary"].get("label_count"),
            "stage7_row_count": validation["summary"].get("stage7_row_count"),
        },
        "runtime_sandbox_requirements": [
            "default_off_explicit_flag_required",
            "default_off_equivalence_required",
            "trace_every_proxy_firing",
            "proxy_metadata_must_not_directly_request_provider",
            "protected_stage4_stage5_stage6_guardrails_required",
            "stage7_heldout_challenge_required",
            "m1_m4_preservation_required",
            "rollback_tag_required_before_any_runtime_test",
        ],
        "translation_blocker": (
            "The passing v1 evidence is progress-window based. It supports a future "
            "monitor/reconsideration sandbox review, not an initial pre-decision "
            "selector based only on one-ply move shape."
        ),
        "decision": {
            "status": "runtime_review_ready_progress_window_scope_only",
            "runtime_implementation_allowed": False,
            "recommended_next_step": "explicit_human_review_before_default_off_runtime_sandbox",
        },
    }
    return payload


def build_blocker(probe: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    reason = "missing_competing_proposal_visibility"
    if validation["metrics"].get("recall"):
        reason = "data_underpowered_or_scope_limited"
    payload = {
        "schema_version": "krk_selected_owner_failure_risk_proxy_v1_blocker_review.v1",
        "causal_status": "non_causal_architecture_review",
        **_runtime_false_block(),
        "implementation_allowed_by_this_review": False,
        "source_artifacts": [str(OUT_PROBE_JSON), str(OUT_VALIDATION_JSON), str(EVIDENCE)],
        "summary": {
            "selected_proxy": validation.get("selected_proxy"),
            "validation_metrics": validation.get("metrics"),
            "stage7_row_count": validation.get("summary", {}).get("stage7_row_count"),
        },
        "blocker_reason": reason,
        "decision": {
            "status": "selected_owner_failure_risk_proxy_v1_blocked",
            "recommended_next_step": "visible_candidate_proposal_layer_or_progress_window_monitor_design_review",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
        },
    }
    return payload


def render_probe_md(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Selected-Owner Failure-Risk Proxy Probe v1",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selected proxy: `{payload['summary']['selected_proxy_for_independent_validation']}`",
        f"- Stage 7 rows: `{payload['summary']['stage7_row_count']}`",
        "",
        "## Proxy Metrics",
        "",
    ]
    for name, result in payload["proxy_results"].items():
        metrics = result["all_rows"]
        lines.append(
            f"- `{name}` all rows: precision `{metrics['precision']}`, recall `{metrics['recall']}`, safe `{metrics['safe_preservation_recall']}`; independent pass `{result['independent_validation_passes']}`"
        )
    return "\n".join(lines) + "\n"


def render_validation_md(payload: dict[str, Any]) -> str:
    metrics = payload["metrics"]
    return "\n".join(
        [
            "# KRK Selected-Owner Failure-Risk Proxy Independent Validation v1",
            "",
            f"- selected proxy: `{payload['selected_proxy']}`",
            f"- status: `{payload['decision']['status']}`",
            f"- precision: `{metrics['precision']}`",
            f"- recall: `{metrics['recall']}`",
            f"- safe-preservation recall: `{metrics['safe_preservation_recall']}`",
            f"- label count: `{payload['summary']['label_count']}`",
            f"- Stage 7 rows: `{payload['summary']['stage7_row_count']}`",
            f"- runtime scope: `{payload['summary']['runtime_scope']}`",
            "",
        ]
    )


def render_packet_md(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK State-Local Paired Selector Runtime Proxy Review Packet v1",
        "",
        "This packet is review-only and does not authorize implementation.",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selected proxy: `{payload['selected_proxy']}`",
        f"- review scope: `{payload['review_scope']}`",
        f"- implementation allowed by this packet: `{payload['implementation_allowed_by_this_packet']}`",
        "",
        "## Translation Blocker",
        "",
        payload["translation_blocker"],
        "",
        "## Requirements",
        "",
    ]
    lines.extend(f"- `{item}`" for item in payload["runtime_sandbox_requirements"])
    return "\n".join(lines) + "\n"


def render_blocker_md(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# KRK Selected-Owner Failure-Risk Proxy v1 Blocker Review",
            "",
            f"- status: `{payload['decision']['status']}`",
            f"- blocker reason: `{payload['blocker_reason']}`",
            "- runtime work allowed: `false`",
            "- selector training allowed: `false`",
            "",
        ]
    )


def main() -> None:
    evidence = _load(EVIDENCE)
    probe = build_probe(evidence)
    validation = build_validation(probe, evidence)
    packet = build_packet(validation)
    (ROOT / OUT_PROBE_JSON).write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_PROBE_MD).write_text(render_probe_md(probe), encoding="utf-8")
    (ROOT / OUT_VALIDATION_JSON).write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_VALIDATION_MD).write_text(render_validation_md(validation), encoding="utf-8")
    if packet is not None:
        (ROOT / OUT_PACKET_JSON).write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (ROOT / OUT_PACKET_MD).write_text(render_packet_md(packet), encoding="utf-8")
        if (ROOT / OUT_BLOCKER_JSON).exists():
            (ROOT / OUT_BLOCKER_JSON).unlink()
        if (ROOT / OUT_BLOCKER_MD).exists():
            (ROOT / OUT_BLOCKER_MD).unlink()
    else:
        blocker = build_blocker(probe, validation)
        (ROOT / OUT_BLOCKER_JSON).write_text(json.dumps(blocker, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (ROOT / OUT_BLOCKER_MD).write_text(render_blocker_md(blocker), encoding="utf-8")


if __name__ == "__main__":
    main()
