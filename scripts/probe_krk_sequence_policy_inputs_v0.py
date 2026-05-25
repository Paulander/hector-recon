#!/usr/bin/env python3
"""Probe currently assembled KRK sequence-policy inputs non-causally."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json"
OUTPUT_JSON = ROOT / "reports/strategy_arbitration/krk_sequence_policy_input_probe_v0.json"
OUTPUT_MD = ROOT / "reports/strategy_arbitration/krk_sequence_policy_input_probe_v0.md"

SCHEMA_VERSION = "krk_sequence_policy_input_probe.v0"

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _binary_metrics(rows: list[dict[str, Any]], predictions: dict[str, bool]) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row in rows:
        predicted = bool(predictions.get(row["row_id"], False))
        positive = row.get("target_label") == "conversion_positive"
        if predicted and positive:
            tp += 1
        elif predicted and not positive:
            fp += 1
        elif not predicted and positive:
            fn += 1
        else:
            tn += 1
    total = tp + fp + tn + fn
    return {
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "accuracy": (tp + tn) / total if total else None,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "negative_suppression": tn / (tn + fp) if tn + fp else None,
    }


def _stage4_probe(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stage4 = [row for row in rows if row.get("input_group") == "stage4_first_move_contrast"]
    predictions = {
        row["row_id"]: bool((row.get("features") or {}).get("rook_mid_rank8_cut_candidate"))
        for row in stage4
    }
    by_state: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in stage4:
        by_state[str(row.get("state_id"))].append(row)
    top1_hits = 0
    top3_hits = 0
    state_count = 0
    for state_rows in by_state.values():
        if not state_rows:
            continue
        state_count += 1
        ranked = sorted(
            state_rows,
            key=lambda row: (
                1 if predictions.get(row["row_id"]) else 0,
                -int((row.get("features") or {}).get("target_distance_to_black_king") or 99),
                str(row.get("move_uci")),
            ),
            reverse=True,
        )
        top1_hits += int(ranked[0].get("target_label") == "conversion_positive")
        top3_hits += int(any(row.get("target_label") == "conversion_positive" for row in ranked[:3]))
    metrics = _binary_metrics(stage4, predictions)
    metrics.update(
        {
            "row_count": len(stage4),
            "state_count": state_count,
            "top1_conversion_positive_by_state": top1_hits / state_count if state_count else None,
            "top3_conversion_positive_by_state": top3_hits / state_count if state_count else None,
            "heuristic": "rook_mid_rank8_cut_candidate",
            "runtime_ready": False,
        }
    )
    return metrics


def _plan_window_probe(rows: list[dict[str, Any]]) -> dict[str, Any]:
    plan_rows = [row for row in rows if row.get("input_group") == "protected_plan_window"]
    term_stats: dict[str, Counter] = defaultdict(Counter)
    for row in plan_rows:
        label = str(row.get("target_label"))
        features = row.get("features") or {}
        for field in ("entry_terms_confirmed", "progress_terms_after_first_reply", "abort_terms", "handoff_targets"):
            for value in features.get(field) or []:
                term_stats[f"{field}:{value}"][label] += 1
        if features.get("selected_successor"):
            term_stats[f"selected_successor:{features['selected_successor']}"][label] += 1
        term_stats[f"semantic_alignment_status:{features.get('semantic_alignment_status')}"][label] += 1
    sorted_terms = []
    for term, counts in term_stats.items():
        total = sum(counts.values())
        sorted_terms.append(
            {
                "term": term,
                "support": total,
                "conversion_positive": counts.get("conversion_positive", 0),
                "conversion_failure": counts.get("conversion_failure", 0),
                "failure_precision": counts.get("conversion_failure", 0) / total if total else None,
                "success_precision": counts.get("conversion_positive", 0) / total if total else None,
            }
        )
    sorted_terms.sort(key=lambda item: (-item["support"], item["term"]))
    outcome_counts = Counter(row.get("target_label") for row in plan_rows)
    return {
        "row_count": len(plan_rows),
        "source_stage_counts": dict(Counter(row.get("source_stage") for row in plan_rows)),
        "target_label_counts": dict(outcome_counts),
        "failure_row_count": outcome_counts.get("conversion_failure", 0),
        "failure_evidence_sparse": outcome_counts.get("conversion_failure", 0) < 5,
        "top_terms": sorted_terms[:12],
        "runtime_ready": False,
    }


def _stage7_probe(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stage7 = [row for row in rows if row.get("input_group") == "stage7_clean_heldout_control"]
    outcome_counts = Counter(row.get("target_label") for row in stage7)
    provider_counts = Counter((row.get("features") or {}).get("selected_provider") for row in stage7)
    alignment_counts = Counter((row.get("features") or {}).get("semantic_alignment_status") for row in stage7)
    success = outcome_counts.get("conversion_positive", 0)
    failure = outcome_counts.get("conversion_failure", 0)
    return {
        "row_count": len(stage7),
        "target_label_counts": dict(outcome_counts),
        "selected_provider_counts": {str(key): value for key, value in provider_counts.items()},
        "semantic_alignment_counts": {str(key): value for key, value in alignment_counts.items()},
        "success_controls": success,
        "failure_controls": failure,
        "success_controls_required": 5,
        "failure_controls_required": 5,
        "success_controls_met": success >= 5,
        "failure_controls_met": failure >= 5,
        "underpowered": success < 5 or failure < 5,
        "runtime_ready": False,
    }


def build_payload(*, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    inputs = inputs or _load(INPUTS)
    rows = inputs.get("rows") or []
    stage4 = _stage4_probe(rows)
    plan_windows = _plan_window_probe(rows)
    stage7 = _stage7_probe(rows)
    full_ready = bool(inputs.get("summary", {}).get("benchmark_input_ready"))
    status = (
        "sequence_policy_input_probe_ready_for_full_non_causal_benchmark"
        if full_ready
        else "sequence_policy_input_probe_partial_stage7_success_controls_missing"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_sequence_policy_input_probe",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json"
        ],
        "summary": {
            "row_count": len(rows),
            "benchmark_input_ready": full_ready,
            "stage4_binary_heuristic_sufficient": (
                stage4.get("precision") is not None
                and stage4.get("recall") is not None
                and stage4["precision"] >= 0.7
                and stage4["recall"] >= 0.7
            ),
            "stage4_topk_signal": (
                stage4.get("precision") is not None
                and stage4.get("top3_conversion_positive_by_state") is not None
                and stage4["precision"] >= 0.7
                and stage4["top3_conversion_positive_by_state"] >= 0.8
            ),
            "protected_plan_window_failure_sparse": plan_windows["failure_evidence_sparse"],
            "stage7_underpowered": stage7["underpowered"],
            "selector_training_row_count": sum(
                1 for row in rows if row.get("usable_for_selector_training")
            ),
            "runtime_authorization_row_count": sum(
                1 for row in rows if row.get("usable_for_runtime_authorization")
            ),
        },
        "stage4_first_move_contrast_probe": stage4,
        "protected_plan_window_probe": plan_windows,
        "stage7_heldout_probe": stage7,
        "decision": {
            "status": status,
            "recommended_next_step": (
                "fill_stage7_clean_success_controls_before_full_sequence_policy_benchmark"
                if stage7["underpowered"]
                else "run_full_non_causal_sequence_policy_benchmark"
            ),
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    decision = payload["decision"]
    summary = payload["summary"]
    stage4 = payload["stage4_first_move_contrast_probe"]
    plan_windows = payload["protected_plan_window_probe"]
    stage7 = payload["stage7_heldout_probe"]
    lines = [
        "# KRK Sequence-Policy Input Probe v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is a partial non-causal probe over the currently assembled inputs. It does not train a model, authorize runtime behavior, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Stage 4 First-Move Contrast",
            "",
            f"- row_count: `{stage4['row_count']}`",
            f"- precision: `{stage4['precision']}`",
            f"- recall: `{stage4['recall']}`",
            f"- negative_suppression: `{stage4['negative_suppression']}`",
            f"- top1_conversion_positive_by_state: `{stage4['top1_conversion_positive_by_state']}`",
            f"- top3_conversion_positive_by_state: `{stage4['top3_conversion_positive_by_state']}`",
            "",
            "## Protected Plan-Window Evidence",
            "",
            f"- row_count: `{plan_windows['row_count']}`",
            f"- target_label_counts: `{plan_windows['target_label_counts']}`",
            f"- failure_evidence_sparse: `{plan_windows['failure_evidence_sparse']}`",
            "",
            "## Stage 7 Held-Out Controls",
            "",
            f"- success_controls: `{stage7['success_controls']}`",
            f"- failure_controls: `{stage7['failure_controls']}`",
            f"- underpowered: `{stage7['underpowered']}`",
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            "- runtime_changes_allowed: `false`",
            "- label_run_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- Stage 7 promotion and Stage 8 training remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": payload["decision"]["status"],
                "stage4_topk_signal": payload["summary"]["stage4_topk_signal"],
                "stage7_underpowered": payload["summary"]["stage7_underpowered"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
