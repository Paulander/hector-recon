#!/usr/bin/env python3
"""Summarize replay-free evidence for the selected Stage 7 failure path.

This audit does not run gameplay, train, mutate topology, or authorize runtime
behavior. It asks whether the actual selected max-plies paths are covered by
existing abstention, monitor, strategy-arbiter, or continuation evidence.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_MERGE = Path("reports/structural_candidates/stage7_evidence_merge_table.json")
INTERNAL_TERMINAL_VALIDATION = Path("reports/strategy_arbitration/krk_internal_terminal_validation_v0.json")
STRATEGY_MONITOR_RECORDS = Path("reports/strategy_arbitration/krk_strategy_monitor_records_v0.json")
ABSTENTION_STAGE7_SMOKE = Path("reports/krk_two_stage_abstention_stage7_challenge_smoke_v0.json")
ABSTENTION_GO_NO_GO = Path("reports/krk_two_stage_abstention_runtime_go_no_go_v0.json")
OUT_JSON = Path("reports/structural_candidates/stage7_selected_failure_path_audit_v0.json")
OUT_MD = Path("reports/structural_candidates/stage7_selected_failure_path_audit_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _records_by_state(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_state: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        state_id = record.get("state_id")
        if state_id:
            by_state[str(state_id)].append(record)
    return dict(by_state)


def _forced_mating_provider(forced: dict[str, Any]) -> str | None:
    for provider_id, result in forced.items():
        if isinstance(result, dict) and result.get("result") == "mate":
            return provider_id
    return None


def _legal_first_has_mate(label: Any) -> bool | None:
    if not isinstance(label, dict):
        return None
    if label.get("any_mate") is not None:
        return bool(label.get("any_mate"))
    moves = label.get("mating_moves")
    if isinstance(moves, list):
        return bool(moves)
    return None


def _classify_path(row: dict[str, Any]) -> str:
    strategy = row.get("strategy_provider_evidence") or {}
    continuation = row.get("continuation_evidence") or {}
    forced = strategy.get("forced_provider_results") or {}
    selected_provider = strategy.get("raw_selected_provider")
    forced_mate = _forced_mating_provider(forced)
    best_forced = strategy.get("best_forced_provider") or forced_mate
    legal_has_mate = _legal_first_has_mate(strategy.get("legal_first_or_dtm_label"))
    if best_forced and best_forced != selected_provider:
        return "strategy_ownership_gap_existing_provider_can_convert"
    if continuation.get("forced_provider_result_h40", {}).get("result") == "no_forced_provider_mate":
        return "continuation_capacity_or_sequence_policy_gap"
    if legal_has_mate is False:
        return "continuation_capacity_or_sequence_policy_gap"
    return "mixed_or_missing_evidence"


def _selected_failure_rows(evidence_merge: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in evidence_merge.get("rows") or []:
        if not isinstance(row, dict):
            continue
        strategy = row.get("strategy_provider_evidence") or {}
        continuation = row.get("continuation_evidence") or {}
        if strategy.get("raw_selected_provider") and continuation.get("current_graph_result_h40") == "max_plies":
            rows.append(row)
    return rows


def build_audit() -> dict[str, Any]:
    evidence_merge = _load(EVIDENCE_MERGE)
    terminal_validation = _load(INTERNAL_TERMINAL_VALIDATION)
    monitor_records = _load(STRATEGY_MONITOR_RECORDS)
    abstention_smoke = _load(ABSTENTION_STAGE7_SMOKE)
    abstention_go_no_go = _load(ABSTENTION_GO_NO_GO)

    internal_by_state = _records_by_state(terminal_validation.get("validation_records") or [])
    monitor_by_state = _records_by_state(monitor_records.get("records") or [])
    rows = []
    family_counts: Counter[str] = Counter()
    selected_provider_counts: Counter[str] = Counter()
    internal_terminal_counts: Counter[str] = Counter()
    monitor_type_counts: Counter[str] = Counter()

    for row in _selected_failure_rows(evidence_merge):
        identity = row.get("state_identity") or {}
        strategy = row.get("strategy_provider_evidence") or {}
        continuation = row.get("continuation_evidence") or {}
        state_id = str(identity.get("state_signature") or "")
        forced = strategy.get("forced_provider_results") or {}
        forced_mating = _forced_mating_provider(forced)
        path_class = _classify_path(row)
        family_counts[path_class] += 1
        selected_provider_counts[str(strategy.get("raw_selected_provider"))] += 1

        terminal_hits = []
        for record in internal_by_state.get(state_id, []):
            terminal_id = record.get("terminal_id")
            if terminal_id:
                internal_terminal_counts[str(terminal_id)] += 1
            terminal_hits.append({
                "terminal_id": terminal_id,
                "source_terms_met": record.get("source_terms_met") or [],
                "associated_outcome": record.get("associated_outcome"),
                "confidence": record.get("confidence"),
            })

        monitor_hits = []
        for record in monitor_by_state.get(state_id, []):
            monitor_type = record.get("monitor_type")
            if monitor_type:
                monitor_type_counts[str(monitor_type)] += 1
            monitor_hits.append({
                "monitor_id": record.get("monitor_id"),
                "monitor_type": monitor_type,
                "suggested_action_class": record.get("suggested_action_class"),
                "source_terms": record.get("source_terms") or [],
                "missing_terms": record.get("missing_terms") or [],
                "confidence": record.get("confidence"),
            })

        rows.append({
            "state_id": state_id,
            "family_id": identity.get("family_id"),
            "post_reply_fen": identity.get("post_reply_fen"),
            "raw_selected_provider": strategy.get("raw_selected_provider"),
            "raw_selected_move": strategy.get("raw_selected_move"),
            "current_graph_result_h40": continuation.get("current_graph_result_h40"),
            "best_forced_provider": strategy.get("best_forced_provider") or forced_mating,
            "forced_mating_provider": forced_mating,
            "forced_provider_result_h40": continuation.get("forced_provider_result_h40"),
            "legal_first_or_dtm_label": strategy.get("legal_first_or_dtm_label"),
            "hypothesis_labels": row.get("hypothesis_labels") or [],
            "selected_failure_path_class": path_class,
            "internal_terminal_hits": terminal_hits,
            "strategy_monitor_hits": monitor_hits,
            "coverage": {
                "abstention_selector_selected_penalized": False,
                "abstention_selector_state_level_only": True,
                "internal_terminal_hit_count": len(terminal_hits),
                "strategy_monitor_hit_count": len(monitor_hits),
                "existing_provider_can_convert": bool(strategy.get("best_forced_provider") or forced_mating),
                "all_tested_existing_providers_fail": path_class == "continuation_capacity_or_sequence_policy_gap",
            },
            "recommended_next_evidence_class": (
                "strategy_ownership_training_target"
                if path_class == "strategy_ownership_gap_existing_provider_can_convert"
                else "sequence_policy_or_continuation_capacity_target"
                if path_class == "continuation_capacity_or_sequence_policy_gap"
                else "fill_selected_path_evidence"
            ),
        })

    selected_penalized = int((abstention_smoke.get("enabled") or {}).get("selected_penalized_count") or 0)
    penalized = int((abstention_smoke.get("enabled") or {}).get("penalized_count") or 0)
    decision = (
        "mixed_selected_path_gap_no_runtime_patch"
        if len(family_counts) > 1
        else "selected_path_evidence_inconclusive"
    )
    payload = {
        "schema_version": "stage7_selected_failure_path_audit.v0",
        "causal_status": "non_causal_replay_free_audit",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "runtime_selector_implemented_by_this_slice": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(EVIDENCE_MERGE),
            str(INTERNAL_TERMINAL_VALIDATION),
            str(STRATEGY_MONITOR_RECORDS),
            str(ABSTENTION_STAGE7_SMOKE),
            str(ABSTENTION_GO_NO_GO),
        ],
        "summary": {
            "selected_failure_state_count": len(rows),
            "selected_provider_counts": dict(selected_provider_counts),
            "selected_failure_path_class_counts": dict(family_counts),
            "internal_terminal_hit_counts": dict(internal_terminal_counts),
            "strategy_monitor_type_counts": dict(monitor_type_counts),
            "abstention_stage7_penalized_count": penalized,
            "abstention_stage7_selected_penalized_count": selected_penalized,
            "abstention_target_conversion_delta_mates": (abstention_smoke.get("summary") or {}).get("conversion_delta_mates"),
        },
        "rows": rows,
        "decision": {
            "status": decision,
            "primary_interpretation": (
                "The actual selected Stage 7 max-plies path is mostly stage0_basin ownership, but it splits into two different problem classes: "
                "some states have an existing forced provider that converts, while others remain unresolved even under forced providers/legal-first h40 evidence."
            ),
            "why_abstention_selector_did_not_help": (
                "The runtime selector penalized suggestions in the Stage 7 smoke, but selected_penalized_count stayed 0. "
                "It therefore did not target the move/provider that actually won selection in the sampled failure path."
            ),
            "recommended_next_step": "do_not_tune_abstention; build a non-causal selected-path target spec that separately models strategy ownership gaps and sequence/continuation gaps",
            "forbidden_next_steps": [
                "increase abstention penalty",
                "scale runtime selector validation",
                "promote Stage 7",
                "train Stage 8",
                "add support adapter or provider penalty",
                "make internal terminals causal",
            ],
        },
    }
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Selected Failure Path Audit v0",
        "",
        f"Decision: `{payload['decision']['status']}`",
        "",
        "This is a replay-free audit. It does not change runtime behavior, train Stage 8, promote Stage 7, use DTM/tablebase at runtime, or mutate topology.",
        "",
        "## Summary",
        "",
    ]
    summary = payload["summary"]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend([
        "",
        "## Selected Failure Rows",
        "",
        "| State | Selected provider | Selected move | Path class | Forced mating provider | Internal terminals | Strategy monitors |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ])
    for row in payload["rows"]:
        terminals = ", ".join(hit["terminal_id"] for hit in row["internal_terminal_hits"] if hit.get("terminal_id")) or "none"
        monitors = ", ".join(hit["monitor_type"] for hit in row["strategy_monitor_hits"] if hit.get("monitor_type")) or "none"
        lines.append(
            "| "
            f"`{row['state_id']}` | "
            f"`{row['raw_selected_provider']}` | "
            f"`{row['raw_selected_move']}` | "
            f"`{row['selected_failure_path_class']}` | "
            f"`{row['forced_mating_provider']}` | "
            f"{terminals} | "
            f"{monitors} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        payload["decision"]["primary_interpretation"],
        "",
        payload["decision"]["why_abstention_selector_did_not_help"],
        "",
        "## Recommended Next Step",
        "",
        f"`{payload['decision']['recommended_next_step']}`",
        "",
        "## Forbidden Next Steps",
        "",
    ])
    for item in payload["decision"]["forbidden_next_steps"]:
        lines.append(f"- `{item}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_audit()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
