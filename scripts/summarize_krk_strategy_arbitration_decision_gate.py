#!/usr/bin/env python3
"""Summarize KRK strategy arbitration decision gate v0.

This is non-causal. It chooses the next diagnostic/design class from the
strategy arbitration dataset/probe/manifest artifacts and explicitly blocks
runtime arbiter implementation, Stage 7 promotion, and Stage 8 training.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_STATUSES = {
    "strategy_arbitration_promising",
    "missing_feature_first",
    "curriculum_boundary_likely",
    "continuation_capacity_dominant",
    "training_objective_dominant",
    "inconclusive_need_more_stratified_data",
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _recommendation(status: str) -> dict[str, Any]:
    if status == "missing_feature_first":
        return {
            "next_class": "non_causal_terminal_affordance_candidate_audit",
            "next_step": "Propose non-causal terminal/affordance candidates and a separability audit; do not implement them causally.",
            "stop_after_next_class": True,
        }
    if status == "strategy_arbitration_promising":
        return {
            "next_class": "non_causal_sandbox_design_document",
            "next_step": "Create a default-off sandbox design document only; do not implement runtime arbiter.",
            "stop_after_next_class": True,
        }
    if status == "curriculum_boundary_likely":
        return {
            "next_class": "non_causal_curriculum_boundary_redesign_note",
            "next_step": "Document box_shrink as local evidence / handoff trigger; do not train or implement.",
            "stop_after_next_class": True,
        }
    if status == "continuation_capacity_dominant":
        return {
            "next_class": "non_causal_continuation_capacity_design_note",
            "next_step": "Document capacity hypothesis; do not train or implement full-KRK overlay.",
            "stop_after_next_class": True,
        }
    if status == "training_objective_dominant":
        return {
            "next_class": "non_causal_training_objective_redesign_note",
            "next_step": "Document training objective redesign; do not train.",
            "stop_after_next_class": True,
        }
    return {
        "next_class": "one_more_small_stratified_dataset_slice",
        "next_step": "Add one bounded stratified dataset/probe cycle; stop for review if still inconclusive.",
        "stop_after_next_class": False,
    }


def build_gate(report_root: Path) -> dict[str, Any]:
    dataset_path = report_root / "krk_strategy_arbitration_dataset_v0.json"
    probe_path = report_root / "krk_strategy_arbitration_probe_v0.json"
    manifest_path = report_root / "stage7_challenge_set_manifest.json"
    dataset = _load_json(dataset_path)
    probe = _load_json(probe_path)
    manifest = _load_json(manifest_path)
    status = ((probe.get("decision") or {}).get("status") or "inconclusive_need_more_stratified_data")
    if status not in ALLOWED_STATUSES:
        status = "inconclusive_need_more_stratified_data"

    recommendation = _recommendation(status)
    metrics = probe.get("metrics") or {}
    evidence = [
        f"Dataset v0 has {dataset.get('summary', {}).get('record_count')} records and {dataset.get('summary', {}).get('proposal_count')} proposal frames.",
        f"Probe v0 selected {status}.",
        f"Raw global hit rate: {(metrics.get('raw_global_provider_score') or {}).get('hit_rate')}.",
        f"Provider-local rank1 coverage: {(metrics.get('provider_local_rank1_coverage') or {}).get('coverage_rate')}.",
        f"Visible heuristic hit rate: {(metrics.get('visible_heuristic_arbiter') or {}).get('hit_rate')}.",
        f"Challenge manifest has {manifest.get('summary', {}).get('challenge_family_count')} held-out Stage 7 families.",
    ]

    gate = {
        "schema_version": "krk_strategy_arbitration_decision_gate.v0",
        "causal_status": "non_causal_decision_gate",
        "runtime_behavior_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selected_status": status,
        "recommendation": recommendation,
        "evidence": evidence,
        "missing_evidence": [
            "More successful Stage 5/6/7 provider-labeled records with terminal-space context.",
            "A separability audit for candidate terminal/affordance terms before any sandbox.",
            "Better visible heuristic features for edge-net, king-support, phase-boundary, and box-shrink exit conditions.",
        ],
        "forbidden_next_steps": [
            "train_stage8",
            "promote_stage7",
            "implement_runtime_arbiter",
            "add_stage7_runtime_repair",
            "add_support_adapter",
            "add_score_bonus_or_provider_penalty",
            "use_runtime_dtm_or_tablebase",
            "mutate_topology_during_gameplay",
        ],
        "source_artifacts": {
            "dataset": str(dataset_path),
            "probe": str(probe_path),
            "challenge_manifest": str(manifest_path),
        },
    }
    validate_gate(gate)
    return gate


def validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("schema_version") != "krk_strategy_arbitration_decision_gate.v0":
        raise ValueError("unexpected decision gate schema")
    if gate.get("causal_status") != "non_causal_decision_gate":
        raise ValueError("decision gate must be non-causal")
    if gate.get("runtime_behavior_changed") is not False:
        raise ValueError("decision gate must not change runtime behavior")
    if gate.get("runtime_dtm_or_tablebase_lookup") is not False:
        raise ValueError("decision gate must not use runtime DTM/tablebase")
    if gate.get("stage7_promotion_allowed") is not False or gate.get("stage8_training_allowed") is not False:
        raise ValueError("Stage 7 promotion and Stage 8 training must remain blocked")
    if gate.get("selected_status") not in ALLOWED_STATUSES:
        raise ValueError("invalid selected status")


def render_markdown(gate: dict[str, Any]) -> str:
    lines = [
        "# KRK Strategy Arbitration Decision Gate v0",
        "",
        "This decision gate is non-causal. It recommends the next diagnostic/design class only.",
        "",
        "## Decision",
        "",
        f"- Selected status: `{gate['selected_status']}`",
        f"- Next class: `{gate['recommendation']['next_class']}`",
        f"- Next step: {gate['recommendation']['next_step']}",
        f"- Stop after next class: `{gate['recommendation']['stop_after_next_class']}`",
        f"- Stage 7 promotion allowed: `{gate['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{gate['stage8_training_allowed']}`",
        "",
        "## Evidence",
        "",
    ]
    lines.extend(f"- {item}" for item in gate["evidence"])
    lines.extend(["", "## Missing Evidence", ""])
    lines.extend(f"- {item}" for item in gate["missing_evidence"])
    lines.extend(["", "## Forbidden Next Steps", ""])
    lines.extend(f"- {item}" for item in gate["forbidden_next_steps"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-root", type=Path, default=Path("reports/strategy_arbitration"))
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    gate = build_gate(args.report_root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(gate), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(gate, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
