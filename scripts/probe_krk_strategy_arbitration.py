#!/usr/bin/env python3
"""Probe KRK strategy arbitration dataset v0 with non-causal baselines.

The probe compares raw global provider score, provider-local rank/normalization,
and simple visible heuristics against known outcome labels already present in
the dataset. It does not run gameplay, train, route, mutate topology, or use
DTM/tablebase at runtime.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _outcome_result(label: Any) -> str | None:
    if not isinstance(label, dict):
        return None
    result = label.get("result")
    if result is None:
        result = label.get("playout_result")
    return str(result) if result is not None else None


def _positive_providers(record: dict[str, Any]) -> set[str]:
    providers: set[str] = set()
    for frame in record.get("strategy_proposals") or []:
        if _outcome_result(frame.get("known_outcome_label")) == "mate":
            provider = frame.get("provider_id")
            if provider:
                providers.add(str(provider))
    return providers


def _score_value(value: Any, fallback: float = -999999.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _top_provider_by(records: list[dict[str, Any]], key: str) -> str | None:
    if not records:
        return None
    top = max(records, key=lambda frame: _score_value(frame.get(key)))
    provider = top.get("provider_id")
    return str(provider) if provider else None


def _raw_global_choice(record: dict[str, Any]) -> str | None:
    return _top_provider_by(record.get("strategy_proposals") or [], "raw_score")


def _normalized_choice(record: dict[str, Any]) -> str | None:
    return _top_provider_by(record.get("strategy_proposals") or [], "normalized_score")


def _provider_local_rank1_choices(record: dict[str, Any]) -> set[str]:
    return {
        str(frame.get("provider_id"))
        for frame in record.get("strategy_proposals") or []
        if frame.get("provider_id") and int(frame.get("provider_local_rank") or 999999) == 1
    }


def _visible_heuristic_choice(record: dict[str, Any]) -> str | None:
    context = record.get("terminal_space_context") or {}
    active = set(context.get("active_terminal_terms") or [])
    edge_bucket = context.get("black_king_edge_bucket")
    box_relevance = context.get("box_area_relevance")
    fence_exists = bool(context.get("fence_exists"))
    fence_stable = bool(context.get("fence_stable"))
    support_available = bool(context.get("white_king_support_available"))
    support_improve = bool(context.get("white_king_can_improve_support"))
    edge_pressure = bool(context.get("edge_net_pressure_proxy"))
    mate_in_one = bool(context.get("mate_in_one_available"))

    if mate_in_one:
        return "krk.stage0_basin"
    if edge_pressure or edge_bucket == "at_edge":
        if fence_exists or "edge_trap_shape_available" in active:
            return "krk.edge_trap_close"
        return "krk.fence_established"
    if fence_exists and not fence_stable:
        return "krk.fence_established"
    if support_available or support_improve:
        if box_relevance == "high":
            return "krk.drive_to_edge"
        return "krk.edge_trap_close"
    if box_relevance == "high":
        return "krk.box_shrink"
    return "krk.stage0_basin"


def _box_relevance_by_edge(records: list[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    for record in records:
        context = record.get("terminal_space_context") or {}
        key = f"{context.get('black_king_edge_bucket')}|{context.get('box_area_relevance')}"
        counts[key] += 1
    return dict(counts)


def _evaluate_choice(records: list[dict[str, Any]], choice_fn) -> dict[str, Any]:
    labeled = 0
    hit = 0
    miss_examples = []
    choice_counts: Counter[str] = Counter()
    for record in records:
        positives = _positive_providers(record)
        if not positives:
            continue
        labeled += 1
        choice = choice_fn(record)
        if choice:
            choice_counts[choice] += 1
        if choice in positives:
            hit += 1
        elif len(miss_examples) < 8:
            miss_examples.append(
                {
                    "state_id": record.get("state_id"),
                    "source_stage": record.get("source_stage"),
                    "choice": choice,
                    "positive_providers": sorted(positives),
                    "context": record.get("terminal_space_context"),
                }
            )
    denom = float(labeled or 1)
    return {
        "labeled_record_count": labeled,
        "hit_count": hit,
        "hit_rate": hit / denom,
        "choice_counts": dict(choice_counts),
        "miss_examples": miss_examples,
    }


def _evaluate_rank1(records: list[dict[str, Any]]) -> dict[str, Any]:
    labeled = 0
    covered = 0
    for record in records:
        positives = _positive_providers(record)
        if not positives:
            continue
        labeled += 1
        if _provider_local_rank1_choices(record) & positives:
            covered += 1
    denom = float(labeled or 1)
    return {
        "labeled_record_count": labeled,
        "coverage_count": covered,
        "coverage_rate": covered / denom,
    }


def _stage7_cluster_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [record for record in records if record.get("source_stage") == "stage7"]
    counts: Counter[str] = Counter()
    owner_counts: Counter[str] = Counter()
    for record in rows:
        result = (record.get("result_label") or {}).get("current_graph_h40")
        context = record.get("terminal_space_context") or {}
        raw = _raw_global_choice(record)
        key = (
            f"result={result}|edge={context.get('black_king_edge_bucket')}|"
            f"box={context.get('box_area_relevance')}"
        )
        counts[key] += 1
        if raw:
            owner_counts[f"{result}:{raw}"] += 1
    return {
        "stage7_record_count": len(rows),
        "phase_context_counts": dict(counts),
        "raw_owner_by_result_counts": dict(owner_counts),
    }


def build_probe(dataset_path: Path) -> dict[str, Any]:
    dataset = _load_json(dataset_path)
    records = [record for record in dataset.get("records") or [] if isinstance(record, dict)]

    raw_eval = _evaluate_choice(records, _raw_global_choice)
    normalized_eval = _evaluate_choice(records, _normalized_choice)
    visible_eval = _evaluate_choice(records, _visible_heuristic_choice)
    rank1_eval = _evaluate_rank1(records)
    stage7_summary = _stage7_cluster_summary(records)
    labeled = raw_eval["labeled_record_count"]

    if labeled < 8:
        status = "inconclusive_need_more_stratified_data"
        next_step = "Add one more small stratified dataset slice before any design note."
    elif max(normalized_eval["hit_rate"], visible_eval["hit_rate"], rank1_eval["coverage_rate"]) > raw_eval["hit_rate"] + 0.15:
        status = "strategy_arbitration_promising"
        next_step = "Create a non-causal sandbox design document only; do not implement runtime arbiter."
    elif visible_eval["hit_rate"] < 0.35 and rank1_eval["coverage_rate"] >= 0.6:
        status = "missing_feature_first"
        next_step = "Propose non-causal terminal/affordance candidates and a separability audit."
    else:
        status = "inconclusive_need_more_stratified_data"
        next_step = "Add one bounded stratified dataset/probe cycle, then stop if still inconclusive."

    probe = {
        "schema_version": "krk_strategy_arbitration_probe.v0",
        "causal_status": "non_causal_probe",
        "runtime_behavior_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "dataset_path": str(dataset_path),
        "dataset_summary": dataset.get("summary"),
        "metrics": {
            "raw_global_provider_score": raw_eval,
            "provider_local_rank1_coverage": rank1_eval,
            "normalized_provider_score": normalized_eval,
            "visible_heuristic_arbiter": visible_eval,
            "box_relevance_by_edge_bucket": _box_relevance_by_edge(records),
            "stage7_cluster_summary": stage7_summary,
        },
        "answers": {
            "raw_provider_score_incomparability_suspected": raw_eval["hit_rate"] < rank1_eval["coverage_rate"],
            "provider_local_rank_helps": rank1_eval["coverage_rate"] > raw_eval["hit_rate"] + 0.15,
            "box_area_relevance_correlates_with_edge_distance": bool(_box_relevance_by_edge(records)),
            "stage7_failures_cluster_by_phase_boundary": any(
                "result=max_plies" in key for key in stage7_summary["phase_context_counts"]
            ),
            "missing_terms_obvious": visible_eval["hit_rate"] < raw_eval["hit_rate"] and rank1_eval["coverage_rate"] > 0.5,
        },
        "decision": {
            "status": status,
            "next_step": next_step,
            "forbidden_runtime_work": [
                "train_stage8",
                "promote_stage7",
                "implement_runtime_arbiter",
                "add_stage7_repair",
                "use_runtime_dtm_or_tablebase",
                "mutate_topology_during_gameplay",
            ],
        },
    }
    validate_probe(probe)
    return probe


def validate_probe(probe: dict[str, Any]) -> None:
    if probe.get("schema_version") != "krk_strategy_arbitration_probe.v0":
        raise ValueError("unexpected probe schema")
    if probe.get("causal_status") != "non_causal_probe":
        raise ValueError("probe must be non-causal")
    if probe.get("runtime_behavior_changed") is not False:
        raise ValueError("probe must not change runtime behavior")
    if probe.get("runtime_dtm_or_tablebase_lookup") is not False:
        raise ValueError("probe must not use runtime DTM/tablebase")
    if probe.get("gameplay_topology_mutation") is not False:
        raise ValueError("probe must not mutate gameplay topology")
    if probe.get("stage7_promotion_allowed") is not False or probe.get("stage8_training_allowed") is not False:
        raise ValueError("Stage 7 promotion and Stage 8 training must remain blocked")


def render_markdown(probe: dict[str, Any]) -> str:
    decision = probe["decision"]
    metrics = probe["metrics"]
    lines = [
        "# KRK Strategy Arbitration Probe v0",
        "",
        "This probe is non-causal. It compares arbitration baselines using only labels already present in dataset v0.",
        "",
        "## Decision",
        "",
        f"- Status: `{decision['status']}`",
        f"- Next step: {decision['next_step']}",
        f"- Runtime behavior changed: `{probe['runtime_behavior_changed']}`",
        f"- Stage 7 promotion allowed: `{probe['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{probe['stage8_training_allowed']}`",
        "",
        "## Baseline Metrics",
        "",
        f"- Raw global score hit rate: `{metrics['raw_global_provider_score']['hit_rate']:.3f}` over `{metrics['raw_global_provider_score']['labeled_record_count']}` labeled records",
        f"- Provider-local rank1 coverage: `{metrics['provider_local_rank1_coverage']['coverage_rate']:.3f}`",
        f"- Normalized provider score hit rate: `{metrics['normalized_provider_score']['hit_rate']:.3f}`",
        f"- Visible heuristic hit rate: `{metrics['visible_heuristic_arbiter']['hit_rate']:.3f}`",
        "",
        "## Context Summaries",
        "",
        f"- Box relevance by edge bucket: `{metrics['box_relevance_by_edge_bucket']}`",
        f"- Stage 7 phase context counts: `{metrics['stage7_cluster_summary']['phase_context_counts']}`",
        f"- Stage 7 raw owner by result counts: `{metrics['stage7_cluster_summary']['raw_owner_by_result_counts']}`",
        "",
        "## Answers",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in probe["answers"].items())
    lines.extend(["", "## Forbidden Runtime Work", ""])
    lines.extend(f"- {item}" for item in decision["forbidden_runtime_work"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json"),
    )
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    probe = build_probe(args.dataset)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(probe), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(probe, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
