#!/usr/bin/env python3
"""Write the non-causal state-local paired ownership objective plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARCH_REVIEW = Path("reports/krk_ownership_objective_architecture_review_v0.json")
OUT_JSON = Path("reports/krk_state_local_paired_ownership_objective_plan_v0.json")
OUT_MD = Path("reports/krk_state_local_paired_ownership_objective_plan_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_plan() -> dict[str, Any]:
    review = _load(ARCH_REVIEW)
    if review.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("architecture review must remain non-causal")
    return {
        "schema_version": "krk_state_local_paired_ownership_objective_plan.v0",
        "causal_status": "non_causal_design_plan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selector_training_allowed": False,
        "source_artifacts": [str(ARCH_REVIEW)],
        "motivation": [
            "Global row classification over provider labels cannot preserve safe owners and suppress unsafe owners simultaneously.",
            "Ownership is state-relative: a provider is good or bad in a concrete state/control context, not globally.",
            "Forced-capacity, selected-playout, safe-preservation, and ownership-selection evidence must stay separated.",
        ],
        "objective": {
            "objective_id": "krk.selector.state_local_paired_ownership.v0",
            "status": "design_only",
            "goal": "learn non-causally whether one candidate owner should be preferred, rejected, or abstained relative to other owners in the same state",
            "unit": "state_local_owner_pair",
            "not_a_runtime_policy": True,
        },
        "row_schema": {
            "schema_version": "state_local_owner_pair.v0",
            "state_id": "stable state key",
            "fen": "board position when available",
            "source_stage": "protected source stage only for initial benchmark",
            "active_landmark_label": "active visible landmark/profile label",
            "owner_a": "candidate provider/strategy id",
            "owner_b": "candidate provider/strategy id or abstain",
            "owner_a_outcome": "selected/forced/capacity/handoff outcome evidence",
            "owner_b_outcome": "selected/forced/capacity/handoff outcome evidence",
            "comparison_label": "prefer_a / prefer_b / equivalent / abstain / insufficient_evidence",
            "evidence_channel": "normal_selected / forced_capacity / same_move / proposal_only / mixed",
            "terminal_context": "shared state features",
            "owner_a_features": "provider-local and move/post-move features",
            "owner_b_features": "provider-local and move/post-move features",
            "causal_status": "non_causal_pair_label",
        },
        "label_rules": [
            {
                "rule": "selected_owner_converted_vs_selected_owner_failed",
                "meaning": "within comparable state/local context, converting selected owners outrank failing selected owners",
                "requires_same_state": False,
                "risk": "cross-state fallback only; weaker than same-state evidence",
            },
            {
                "rule": "forced_alternative_converts_when_selected_owner_fails",
                "meaning": "same-state alternative capacity can mark an ownership gap, but not direct runtime ownership until selection evidence exists",
                "requires_same_state": True,
                "risk": "forced capacity may overstate normal-routing suitability",
            },
            {
                "rule": "safe_preservation_before_suppression",
                "meaning": "validated safe selected owners should be preserved unless same-context failure evidence overrides",
                "requires_same_state": False,
                "risk": "over-preservation can miss rare failures",
            },
            {
                "rule": "abstain_when_only_capacity_or_proposal_evidence",
                "meaning": "do not train a preference pair when only proposal/capacity evidence exists and no selected/handoff outcome is known",
                "requires_same_state": False,
                "risk": "slower learning but avoids handcrafted policy leakage",
            },
        ],
        "minimum_benchmark_requirements": {
            "protected_pair_count": 30,
            "same_state_conflict_pair_count": 8,
            "selected_failure_with_alternative_success_count": 4,
            "safe_preservation_pair_count": 12,
            "stage7_training_rows": 0,
            "leave_state_out_required": True,
            "family_holdout_required_if_possible": True,
        },
        "future_pipeline": [
            "build replay-free pair inventory from existing selected/forced/proposal artifacts",
            "classify pairs by evidence strength",
            "benchmark state-local pair scoring non-causally",
            "review whether same-state evidence improves negative suppression without sacrificing safe preservation",
            "only after explicit review, consider a default-off runtime sandbox design",
        ],
        "blocked_paths": [
            "runtime_selector",
            "selector_training",
            "global_provider_penalty",
            "forced_capacity_as_direct_ownership_label",
            "Stage7_training_rows",
            "Stage8_training",
            "runtime_DTM_or_tablebase",
        ],
        "decision": {
            "status": "state_local_paired_ownership_objective_plan_ready",
            "recommended_next_step": "build_replay_free_state_local_pair_inventory",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
        },
    }


def validate_plan(payload: dict[str, Any]) -> None:
    if payload.get("causal_status") != "non_causal_design_plan":
        raise ValueError("plan must remain non-causal")
    for key in (
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
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK State-Local Paired Ownership Objective Plan v0",
        "",
        "This is a non-causal design plan. It does not train or implement a runtime selector.",
        "",
        "## Motivation",
        "",
    ]
    for item in payload["motivation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Objective", ""])
    for key, value in payload["objective"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Label Rules", ""])
    for rule in payload["label_rules"]:
        lines.append(f"- `{rule['rule']}`: {rule['meaning']} Risk: {rule['risk']}")
    lines.extend(["", "## Minimum Benchmark Requirements", ""])
    for key, value in payload["minimum_benchmark_requirements"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Future Pipeline", ""])
    for step in payload["future_pipeline"]:
        lines.append(f"- {step}")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def write_outputs(repo_root: Path, payload: dict[str, Any]) -> None:
    (repo_root / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (repo_root / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_plan()
    validate_plan(payload)
    write_outputs(repo_root, payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
