#!/usr/bin/env python3
"""Write a non-causal KRK candidate-generation training-refresh design."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MERGED_DATASET = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_dataset_v2_capacity_merged.json"
)
REFRESH_PROBE = Path(
    "reports/strategy_arbitration/krk_candidate_generation_refresh_probe_v2_after_labels.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_generation_training_refresh_design_v2.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_candidate_generation_training_refresh_design_v2.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _best_metrics(probe: dict[str, Any]) -> dict[str, Any]:
    summary = probe.get("summary") or {}
    metrics = summary.get("best_non_oracle_metrics") or {}
    if not isinstance(metrics, dict):
        return {}
    return metrics


def _leave_stage_metrics(probe: dict[str, Any]) -> dict[str, Any]:
    summary = probe.get("summary") or {}
    metrics = summary.get("leave_stage_out_aggregate") or {}
    if not isinstance(metrics, dict):
        return {}
    return metrics


def build_payload(
    merged_dataset: dict[str, Any] | None = None,
    refresh_probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    merged_dataset = merged_dataset or _load(MERGED_DATASET)
    refresh_probe = refresh_probe or _load(REFRESH_PROBE)
    dataset_summary = merged_dataset.get("summary") or {}
    probe_summary = refresh_probe.get("summary") or {}
    best = _best_metrics(refresh_probe)
    leave_stage = _leave_stage_metrics(refresh_probe)
    selector_training_rows = dataset_summary.get("selector_training_row_count")
    stage7_training_rows = dataset_summary.get("stage7_readiness_training_row_count")
    candidate_refresh_supported = bool(
        best.get("positive_recall", 0.0) >= 0.7
        and best.get("negative_suppression", 0.0) >= 0.8
        and selector_training_rows == 0
        and stage7_training_rows == 0
    )
    cross_stage_robust = bool(
        leave_stage.get("positive_recall", 0.0) >= 0.7
        and leave_stage.get("negative_suppression", 0.0) >= 0.7
    )
    status = (
        "candidate_generation_training_refresh_design_ready"
        if candidate_refresh_supported
        else "candidate_generation_training_refresh_design_blocked"
    )
    return {
        "schema_version": "krk_candidate_generation_training_refresh_design.v2",
        "causal_status": "non_causal_design",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MERGED_DATASET), str(REFRESH_PROBE)],
        "design_goal": (
            "Define a non-causal candidate-generation training refresh that can "
            "improve proposal recall from protected capacity evidence while "
            "preserving the capacity-vs-ownership label boundary."
        ),
        "input_evidence": {
            "dataset_status": (merged_dataset.get("decision") or {}).get("status"),
            "probe_status": (refresh_probe.get("decision") or {}).get("status"),
            "capacity_row_count": probe_summary.get("capacity_row_count"),
            "capacity_label_counts": probe_summary.get("capacity_label_counts"),
            "candidate_generation_training_row_count": dataset_summary.get(
                "candidate_generation_training_row_count"
            ),
            "selector_training_row_count": selector_training_rows,
            "stage7_readiness_training_row_count": stage7_training_rows,
            "best_non_oracle_policy": probe_summary.get("best_non_oracle_policy"),
            "best_non_oracle_metrics": best,
            "leave_stage_out_aggregate": leave_stage,
        },
        "training_refresh_scope": {
            "allowed_target": "candidate_generation_recall_and_risk_filtering",
            "allowed_rows": "protected_non_stage7_positive_capacity_rows",
            "negative_rows_use": "risk_filtering_and_ablation_only",
            "stage7_rows_use": "held_out_challenge_only",
            "selector_rows_allowed": False,
            "ownership_labels_created": False,
            "runtime_use_allowed": False,
            "default_behavior_change_allowed": False,
        },
        "candidate_policy_seed": {
            "policy_name": probe_summary.get("best_non_oracle_policy"),
            "policy_role": "analysis_seed_for_candidate_generation_only",
            "positive_recall": best.get("positive_recall"),
            "positive_precision": best.get("positive_precision"),
            "negative_suppression": best.get("negative_suppression"),
            "false_negative": best.get("false_negative"),
            "false_positive": best.get("false_positive"),
            "known_limitations": [
                "capacity_labels_are_not_ownership_labels",
                "leave_stage_out_generalization_is_weak",
                "dataset_is_small",
                "negative_capacity_candidates_remain_present",
                "candidate_generation_does_not_select_or_score_candidates",
            ],
        },
        "minimum_training_refresh_requirements": [
            "preserve label_semantics on every row",
            "train or fit only candidate-generation emission/risk features",
            "produce no selector weights",
            "produce no provider score deltas",
            "emit no runtime routes or direct provider requests",
            "keep Stage 7 challenge rows out of training/readiness metrics",
            "evaluate leave-stage-out and report weak generalization explicitly",
            "require a separate review before any runtime candidate-generator refresh",
        ],
        "acceptance_thresholds_for_future_review": {
            "protected_positive_recall_min": 0.7,
            "protected_negative_suppression_min": 0.8,
            "leave_stage_out_positive_recall_min": 0.7,
            "leave_stage_out_negative_suppression_min": 0.7,
            "selector_training_row_count_required": 0,
            "stage7_training_row_count_required": 0,
            "runtime_mutation_flags_required": False,
        },
        "readiness_assessment": {
            "candidate_refresh_supported": candidate_refresh_supported,
            "cross_stage_generalization_supported": cross_stage_robust,
            "selector_supported": False,
            "runtime_candidate_generator_refresh_supported_now": False,
            "reason_runtime_blocked": (
                "The protected in-sample candidate-generation signal improved, "
                "but leave-stage-out negative suppression remains too weak for "
                "runtime refresh or selector use."
            ),
        },
        "forbidden_next_steps": [
            "runtime_selector",
            "provider_score_tuning",
            "provider_suppression",
            "direct_provider_routing",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
            "using_capacity_labels_as_ownership_labels",
        ],
        "decision": {
            "status": status,
            "selector_allowed": False,
            "runtime_candidate_generator_refresh_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": "candidate_generation_training_refresh_benchmark_or_cross_stage_capacity_review",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    evidence = payload["input_evidence"]
    readiness = payload["readiness_assessment"]
    policy = payload["candidate_policy_seed"]
    lines = [
        "# KRK Candidate-Generation Training Refresh Design v2",
        "",
        payload["design_goal"],
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- runtime_candidate_generator_refresh_allowed: `{payload['decision']['runtime_candidate_generator_refresh_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Evidence",
        "",
        f"- dataset_status: `{evidence['dataset_status']}`",
        f"- probe_status: `{evidence['probe_status']}`",
        f"- capacity_row_count: {evidence['capacity_row_count']}",
        f"- capacity_label_counts: `{evidence['capacity_label_counts']}`",
        f"- candidate_generation_training_row_count: {evidence['candidate_generation_training_row_count']}",
        f"- selector_training_row_count: {evidence['selector_training_row_count']}",
        f"- stage7_readiness_training_row_count: {evidence['stage7_readiness_training_row_count']}",
        "",
        "## Candidate Policy Seed",
        "",
        f"- policy_name: `{policy['policy_name']}`",
        f"- policy_role: `{policy['policy_role']}`",
        f"- positive_recall: {policy['positive_recall']}",
        f"- positive_precision: {policy['positive_precision']}",
        f"- negative_suppression: {policy['negative_suppression']}",
        "",
        "Known limitations:",
        "",
    ]
    lines.extend(f"- `{item}`" for item in policy["known_limitations"])
    lines.extend(
        [
            "",
            "## Readiness Assessment",
            "",
            f"- candidate_refresh_supported: `{readiness['candidate_refresh_supported']}`",
            f"- cross_stage_generalization_supported: `{readiness['cross_stage_generalization_supported']}`",
            f"- selector_supported: `{readiness['selector_supported']}`",
            f"- runtime_candidate_generator_refresh_supported_now: `{readiness['runtime_candidate_generator_refresh_supported_now']}`",
            f"- reason_runtime_blocked: {readiness['reason_runtime_blocked']}",
            "",
            "## Minimum Requirements For Any Future Refresh",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in payload["minimum_training_refresh_requirements"])
    lines.extend(
        [
            "",
            "## Forbidden Next Steps",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in payload["forbidden_next_steps"])
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
