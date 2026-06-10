#!/usr/bin/env python3
"""Analyze selector-objective observability recommendations and write next gate."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OBSERVABILITY = Path(
    "reports/strategy_arbitration/krk_selector_objective_observability_sandbox_v0.json"
)
BENCHMARK = Path("reports/strategy_arbitration/krk_selector_objective_benchmark_v0.json")
BENCHMARK_DECISION = Path(
    "reports/strategy_arbitration/krk_selector_objective_benchmark_decision_v0.json"
)
SEED_MANIFEST = Path(
    "reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json"
)
SEED_PROBE = Path("reports/strategy_arbitration/krk_selector_objective_seed_probe_v2.json")
AGENT_BRIEF = Path("reports/current_agent_brief.md")
OUT_ANALYSIS_JSON = Path(
    "reports/strategy_arbitration/krk_selector_objective_recommendation_analysis_v0.json"
)
OUT_ANALYSIS_MD = Path(
    "reports/strategy_arbitration/krk_selector_objective_recommendation_analysis_v0.md"
)
OUT_GATE_JSON = Path(
    "reports/strategy_arbitration/krk_selector_objective_next_gate_v0.json"
)
OUT_GATE_MD = Path("reports/strategy_arbitration/krk_selector_objective_next_gate_v0.md")

RECOMMENDATION_CLASSES = [
    "preserve_selected_owner",
    "prefer_visible_alternative",
    "abstain_context_only",
]

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_provider_suppression": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "hidden_python_controller": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _target_from_offline_label(row: dict[str, Any], rec: dict[str, Any]) -> str:
    if int(rec.get("positive_trace_provider_candidate_count", 0) or 0) <= 0:
        return "abstain_context_only"
    if row.get("selected_owner_label") == "selected_owner_failed":
        return "prefer_visible_alternative"
    if row.get("selected_owner_label") == "selected_owner_converted":
        return "preserve_selected_owner"
    return "abstain_context_only"


def _seed_index(seed_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in seed_manifest.get("seed_rows") or []:
        if isinstance(row, dict) and row.get("state_id"):
            out[str(row["state_id"])] = row
    return out


def _probe_index(seed_probe: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in seed_probe.get("predictions") or []:
        if isinstance(row, dict) and row.get("state_id"):
            out[str(row["state_id"])] = row
    return out


def _recommendation_label_alignment(
    row: dict[str, Any],
    *,
    seed_by_state: dict[str, dict[str, Any]],
    probe_by_state: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    rec = row.get("enabled_decision", {}).get("selector_recommendation", {}) or {}
    recommendation = str(rec.get("recommendation") or "")
    target = _target_from_offline_label(row, rec)
    state_id = str(row.get("state_id") or "")
    seed = seed_by_state.get(state_id, {})
    probe = probe_by_state.get(state_id, {})
    selected_owner_label = row.get("selected_owner_label")
    preserve_safe_owner = (
        recommendation == "preserve_selected_owner"
        and selected_owner_label == "selected_owner_converted"
    )
    switch_selected_failure = (
        recommendation == "prefer_visible_alternative"
        and selected_owner_label == "selected_owner_failed"
    )
    abstain_weak_evidence = (
        recommendation == "abstain_context_only"
        and int(rec.get("positive_trace_provider_candidate_count", 0) or 0) <= 0
    )
    unsafe_if_causal = (
        recommendation == "preserve_selected_owner"
        and selected_owner_label == "selected_owner_failed"
    )
    return {
        "row_id": row.get("row_id"),
        "state_id": state_id,
        "source_stage": row.get("source_stage"),
        "objective_channel": row.get("objective_channel"),
        "selected_owner_label": selected_owner_label,
        "selected_provider": row.get("selected_provider_label"),
        "recommendation": recommendation,
        "decision_reason": rec.get("decision_reason"),
        "offline_target_action": target,
        "aligns_with_offline_label": recommendation == target,
        "preserve_protects_safe_owner": preserve_safe_owner,
        "switch_corresponds_to_selected_owner_failure": switch_selected_failure,
        "abstain_occurs_when_evidence_weak": abstain_weak_evidence,
        "unsafe_if_made_causal": unsafe_if_causal,
        "visible_alternative_count": int(rec.get("visible_alternative_count", 0) or 0),
        "has_visible_alternatives": int(rec.get("visible_alternative_count", 0) or 0) > 0,
        "positive_trace_provider_candidate_count": int(
            rec.get("positive_trace_provider_candidate_count", 0) or 0
        ),
        "positive_trace_count_bucket": rec.get("positive_trace_count_bucket"),
        "source_terms": list(rec.get("source_terms") or []),
        "explanation_terms": list(rec.get("explanation_terms") or []),
        "capacity_label_used_as_ownership_label": bool(
            row.get("capacity_label_used_as_ownership_label", False)
        ),
        "visible_alternative_label_semantics": sorted(
            {
                str(alt.get("label_semantics") or "")
                for alt in rec.get("visible_alternatives_considered") or []
                if isinstance(alt, dict)
            }
        ),
        "seed_manifest_label": seed.get("selected_owner_label"),
        "seed_manifest_objective_channel": seed.get("objective_channel"),
        "seed_manifest_runtime_usable": bool(seed.get("usable_for_runtime", False)),
        "seed_manifest_training_usable": bool(seed.get("usable_for_selector_training", False)),
        "seed_manifest_capacity_label_used_as_ownership_label": bool(
            seed.get("capacity_label_used_as_ownership_label", False)
        ),
        "seed_probe_predicted_action": probe.get("predicted_action"),
        "seed_probe_target_action": probe.get("target_action"),
        "seed_probe_runtime_feature_eligible": bool(
            probe.get("runtime_feature_eligible", False)
        ),
    }


def build_analysis() -> dict[str, Any]:
    observability = _load_json(OBSERVABILITY)
    benchmark = _load_json(BENCHMARK)
    benchmark_decision = _load_json(BENCHMARK_DECISION)
    seed_manifest = _load_json(SEED_MANIFEST)
    seed_probe = _load_json(SEED_PROBE)
    brief_exists = (ROOT / AGENT_BRIEF).exists()
    seed_by_state = _seed_index(seed_manifest)
    probe_by_state = _probe_index(seed_probe)
    rows = [
        _recommendation_label_alignment(
            row,
            seed_by_state=seed_by_state,
            probe_by_state=probe_by_state,
        )
        for row in observability.get("rows") or []
        if isinstance(row, dict)
    ]
    counts = Counter(row["recommendation"] for row in rows)
    recommendation_counts = {
        klass: int(counts.get(klass, 0)) for klass in RECOMMENDATION_CLASSES
    }
    source_terms = sorted({term for row in rows for term in row["source_terms"]})
    explanation_terms = sorted({term for row in rows for term in row["explanation_terms"]})
    rows_with_visible_alternatives = sum(1 for row in rows if row["has_visible_alternatives"])
    aligned_count = sum(1 for row in rows if row["aligns_with_offline_label"])
    preserve_rows = [row for row in rows if row["recommendation"] == "preserve_selected_owner"]
    switch_rows = [row for row in rows if row["recommendation"] == "prefer_visible_alternative"]
    abstain_rows = [row for row in rows if row["recommendation"] == "abstain_context_only"]
    preserve_safe_count = sum(1 for row in preserve_rows if row["preserve_protects_safe_owner"])
    switch_failure_count = sum(
        1 for row in switch_rows if row["switch_corresponds_to_selected_owner_failure"]
    )
    abstain_weak_count = sum(
        1 for row in abstain_rows if row["abstain_occurs_when_evidence_weak"]
    )
    unsafe_rows = [row for row in rows if row["unsafe_if_made_causal"]]
    capacity_as_ownership_rows = [
        row
        for row in rows
        if row["capacity_label_used_as_ownership_label"]
        or row["seed_manifest_capacity_label_used_as_ownership_label"]
    ]
    stage7_training_row_count = (
        int(observability.get("summary", {}).get("stage7_training_row_count", 0) or 0)
        + sum(
            1
            for row in seed_manifest.get("seed_rows") or []
            if isinstance(row, dict) and row.get("stage7_training_row")
        )
    )
    selector_training_row_count = (
        int(observability.get("summary", {}).get("selector_training_row_count", 0) or 0)
        + sum(
            1
            for row in seed_manifest.get("seed_rows") or []
            if isinstance(row, dict) and row.get("usable_for_selector_training")
        )
    )
    no_runtime_behavior_changes = all(
        observability.get(key) is False for key in COMMON_FALSE_FLAGS
    ) and all(
        int(observability.get("summary", {}).get(key, 0) or 0) == 0
        for key in (
            "selected_move_delta_count",
            "selected_provider_delta_count",
            "selected_score_delta_count",
            "score_delta_count",
            "routing_delta_count",
        )
    )
    stage7_held_out = (
        bool(observability.get("summary", {}).get("stage7_rows_remain_held_out"))
        and stage7_training_row_count == 0
    )
    candidate_generation_blocked = rows_with_visible_alternatives < len(rows)
    semantics_fail = bool(capacity_as_ownership_rows) or not stage7_held_out
    ready = (
        bool(rows)
        and aligned_count == len(rows)
        and preserve_safe_count == len(preserve_rows)
        and switch_failure_count == len(switch_rows)
        and recommendation_counts["abstain_context_only"] > 0
        and abstain_weak_count == len(abstain_rows)
        and not unsafe_rows
        and not candidate_generation_blocked
        and not semantics_fail
        and no_runtime_behavior_changes
        and selector_training_row_count == 0
    )
    if semantics_fail:
        decision_status = "selector_recommendations_fail_semantics"
    elif candidate_generation_blocked:
        decision_status = "selector_recommendations_blocked_by_candidate_generation"
    elif ready:
        decision_status = "selector_recommendations_ready_for_runtime_review_packet"
    else:
        decision_status = "selector_recommendations_need_more_observation_data"
    summary = {
        "observed_row_count": len(rows),
        "recommendation_count_by_class": recommendation_counts,
        "rows_with_visible_alternatives": rows_with_visible_alternatives,
        "rows_without_visible_alternatives": len(rows) - rows_with_visible_alternatives,
        "offline_label_alignment_count": aligned_count,
        "offline_label_mismatch_count": len(rows) - aligned_count,
        "preserve_recommendation_count": len(preserve_rows),
        "preserve_safe_owner_count": preserve_safe_count,
        "preserve_on_selected_owner_failure_count": sum(
            1
            for row in preserve_rows
            if row["selected_owner_label"] == "selected_owner_failed"
        ),
        "switch_recommendation_count": len(switch_rows),
        "switch_on_selected_owner_failure_count": switch_failure_count,
        "abstain_recommendation_count": len(abstain_rows),
        "abstain_weak_evidence_count": abstain_weak_count,
        "unsafe_if_made_causal_count": len(unsafe_rows),
        "capacity_label_used_as_ownership_label_count": len(capacity_as_ownership_rows),
        "stage7_training_row_count": stage7_training_row_count,
        "selector_training_row_count": selector_training_row_count,
        "stage7_remains_held_out": stage7_held_out,
        "runtime_behavior_changed": False,
        "no_runtime_behavior_changes": no_runtime_behavior_changes,
        "runtime_dtm_or_tablebase_use": False,
        "gameplay_topology_mutation": False,
        "unique_source_term_count": len(source_terms),
        "unique_explanation_term_count": len(explanation_terms),
        "source_terms": source_terms,
        "explanation_terms": explanation_terms,
        "benchmark_best_model": benchmark.get("summary", {}).get("best_model"),
        "benchmark_best_accuracy": benchmark.get("summary", {}).get("best_accuracy"),
        "benchmark_switch_contrast_recall": benchmark_decision.get("summary", {}).get(
            "best_switch_contrast_recall"
        ),
        "benchmark_abstain_recall": benchmark_decision.get("summary", {}).get(
            "best_abstain_recall"
        ),
        "agent_brief_present": brief_exists,
    }
    return {
        "schema_version": "krk_selector_objective_recommendation_analysis.v0",
        "causal_status": "non_causal_recommendation_analysis",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            str(OBSERVABILITY),
            str(BENCHMARK),
            str(BENCHMARK_DECISION),
            str(SEED_MANIFEST),
            str(SEED_PROBE),
            str(AGENT_BRIEF),
        ],
        "summary": summary,
        "rows": rows,
        "unsafe_if_made_causal_rows": unsafe_rows,
        "capacity_label_used_as_ownership_label_rows": capacity_as_ownership_rows,
        "decision": {
            "status": decision_status,
            "future_behavior_changing_selector_review_packet_allowed": ready,
            "runtime_changes_allowed": False,
            "selector_runtime_ready": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "recommended_next_step": (
                "write_future_default_off_behavior_changing_selector_review_packet"
                if ready
                else "collect_bounded_recommendation_observations_covering_abstain_and_preserve_false_negative_cases"
            ),
        },
    }


def build_next_gate(analysis: dict[str, Any]) -> dict[str, Any]:
    summary = analysis["summary"]
    status = analysis["decision"]["status"]
    return {
        "schema_version": "krk_selector_objective_next_gate.v0",
        "causal_status": "non_causal_next_gate",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [str(OUT_ANALYSIS_JSON), *analysis["source_artifacts"]],
        "decision": {
            "status": status,
            "future_behavior_changing_selector_review_packet_allowed": (
                status == "selector_recommendations_ready_for_runtime_review_packet"
            ),
            "runtime_changes_allowed": False,
            "selector_runtime_ready": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "gate_findings": {
            "recommendation_count_by_class": summary["recommendation_count_by_class"],
            "offline_label_mismatch_count": summary["offline_label_mismatch_count"],
            "preserve_on_selected_owner_failure_count": summary[
                "preserve_on_selected_owner_failure_count"
            ],
            "abstain_recommendation_count": summary["abstain_recommendation_count"],
            "unsafe_if_made_causal_count": summary["unsafe_if_made_causal_count"],
            "rows_without_visible_alternatives": summary["rows_without_visible_alternatives"],
            "capacity_label_used_as_ownership_label_count": summary[
                "capacity_label_used_as_ownership_label_count"
            ],
            "stage7_remains_held_out": summary["stage7_remains_held_out"],
            "no_runtime_behavior_changes": summary["no_runtime_behavior_changes"],
        },
        "next_bounded_evidence_recommendation": {
            "name": "selector_objective_recommendation_observation_expansion_v0",
            "execute_without_separate_approval": False,
            "purpose": (
                "Collect more recommendation-only observations before any behavior-changing "
                "review packet, especially abstain/weak-evidence cases and the preserve "
                "false-negative pattern."
            ),
            "required_coverage_before_runtime_review_packet": {
                "abstain_context_only_rows": "at_least_one_runtime_observation_with_zero_visible_positive_alternatives",
                "preserve_false_negative_recheck": "no_preserve_selected_owner_on_selected_owner_failed_rows",
                "switch_failure_alignment": "all_switch_recommendations_on_selected_owner_failed_rows",
                "safe_preservation_alignment": "all_preserve_recommendations_on_selected_owner_converted_rows",
                "visible_alternative_metadata": "present_for_all_non_abstain_recommendations",
            },
            "forbidden_actions": [
                "behavior_changing_selector_implementation",
                "routing_changes",
                "score_changes",
                "provider_selection_changes",
                "provider_suppression",
                "stage7_promotion",
                "stage8_training",
                "runtime_dtm_or_tablebase",
                "gameplay_topology_mutation",
                "treating_capacity_labels_as_ownership_labels",
            ],
        },
    }


def write_analysis_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# KRK Selector Objective Recommendation Analysis v0",
        "",
        "This analysis reviews recommendation-only observability records. It does not authorize or implement behavior-changing selection.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- future_behavior_changing_selector_review_packet_allowed: `{payload['decision']['future_behavior_changing_selector_review_packet_allowed']}`",
        f"- selector_runtime_ready: `{payload['decision']['selector_runtime_ready']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Row Alignment", ""])
    for row in payload["rows"]:
        lines.append(
            "- "
            f"`{row['row_id']}` "
            f"owner={row['selected_owner_label']} "
            f"recommendation=`{row['recommendation']}` "
            f"target=`{row['offline_target_action']}` "
            f"aligned={row['aligns_with_offline_label']} "
            f"unsafe_if_causal={row['unsafe_if_made_causal']}"
        )
    return "\n".join(lines) + "\n"


def write_gate_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Selector Objective Next Gate v0",
        "",
        "This gate blocks behavior-changing selector work until more non-causal recommendation observations are reviewed.",
        "",
        "## Decision",
        "",
    ]
    for key, value in payload["decision"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Findings", ""])
    for key, value in payload["gate_findings"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Next Bounded Evidence", ""])
    next_step = payload["next_bounded_evidence_recommendation"]
    lines.append(f"- name: `{next_step['name']}`")
    lines.append(
        f"- execute_without_separate_approval: `{next_step['execute_without_separate_approval']}`"
    )
    lines.append(f"- purpose: {next_step['purpose']}")
    lines.append(f"- forbidden_actions: `{next_step['forbidden_actions']}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    analysis = build_analysis()
    gate = build_next_gate(analysis)
    (ROOT / OUT_ANALYSIS_JSON).write_text(
        json.dumps(analysis, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / OUT_ANALYSIS_MD).write_text(
        write_analysis_markdown(analysis),
        encoding="utf-8",
    )
    (ROOT / OUT_GATE_JSON).write_text(
        json.dumps(gate, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / OUT_GATE_MD).write_text(write_gate_markdown(gate), encoding="utf-8")
    print(json.dumps({"analysis": analysis["decision"], "gate": gate["decision"]}, indent=2))


if __name__ == "__main__":
    main()
