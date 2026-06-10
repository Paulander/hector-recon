#!/usr/bin/env python3
"""Summarize the ownership-selection objective evidence and next architecture step."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP_V5 = Path("reports/krk_ownership_selection_label_dataset_v5.json")
PROBE_V3 = Path("reports/krk_ownership_selection_context_feature_probe_v3.json")
REVIEW_V3 = Path("reports/krk_ownership_context_feature_review_v3.json")
SOURCE_DIVERSITY = Path("reports/krk_ownership_source_diversity_review_v0.json")
OUT_JSON = Path("reports/krk_ownership_objective_architecture_review_v0.json")
OUT_MD = Path("reports/krk_ownership_objective_architecture_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    ownership = _load(OWNERSHIP_V5)
    probe = _load(PROBE_V3)
    review = _load(REVIEW_V3)
    diversity = _load(SOURCE_DIVERSITY)
    if ownership.get("causal_status") != "non_causal_ownership_label_dataset":
        raise ValueError("ownership evidence must remain non-causal")
    if probe.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("probe must remain non-causal")
    if review.get("causal_status") != "non_causal_review":
        raise ValueError("review must remain non-causal")

    best = probe.get("best_result") or {}
    balanced = probe.get("best_balanced_result") or {}
    threshold_pass = (
        (balanced.get("negative_suppression") or 0.0) >= 0.6
        and (balanced.get("positive_recall") or 0.0) >= 0.7
    )
    status = (
        "ownership_objective_requires_state_local_pairing_review"
        if not threshold_pass
        else "ownership_objective_review_ready_but_runtime_still_requires_explicit_approval"
    )
    payload = {
        "schema_version": "krk_ownership_objective_architecture_review.v0",
        "causal_status": "non_causal_architecture_review",
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
        "source_artifacts": [str(OWNERSHIP_V5), str(PROBE_V3), str(REVIEW_V3), str(SOURCE_DIVERSITY)],
        "summary": {
            "ownership_rows": (ownership.get("summary") or {}).get("merged_row_count"),
            "converted_rows": (ownership.get("summary") or {}).get("target_label_counts", {}).get(
                "selected_owner_converted"
            ),
            "failed_rows": (ownership.get("summary") or {}).get("target_label_counts", {}).get(
                "selected_owner_failed"
            ),
            "stage7_rows": (ownership.get("summary") or {}).get("stage7_row_count"),
            "non_stage0_rows": sum(
                1
                for row in ownership.get("rows") or []
                if row.get("provider_family") != "stage0_basin"
            ),
            "best_objective": best.get("objective"),
            "best_negative_suppression": best.get("negative_suppression"),
            "best_positive_recall": best.get("positive_recall"),
            "best_balanced_objective": balanced.get("objective"),
            "best_balanced_negative_suppression": balanced.get("negative_suppression"),
            "best_balanced_positive_recall": balanced.get("positive_recall"),
            "runtime_threshold_passed": threshold_pass,
            "source_diversity_status": (diversity.get("decision") or {}).get("status"),
        },
        "interpretation": [
            "Labeling here means offline observation of what the current graph selected and whether that selected path converted; it is not hand-authoring a policy.",
            "Targeted source-diversity work recovered non-stage0 selected-owner evidence and proved current profile can preserve those owners.",
            "Targeted false-positive risk-cell labels added true ownership negatives, but the probe still cannot preserve safe owners and suppress unsafe owners simultaneously.",
            "The remaining blocker is objective structure: global row classification over sparse labels is too crude for ownership selection.",
            "The next principled objective should be state-local or paired: compare candidate owners within the same state/control context, preserve validated safe owners, and suppress only owners with direct same-context failure evidence.",
        ],
        "recommended_next_design": {
            "status": "state_local_paired_ownership_objective_design",
            "goal": "separate safe-owner preservation from unsafe-owner suppression using same-state comparisons",
            "required_inputs": [
                "normal_selected_owner_outcome",
                "same_state_alternative_provider_capacity_when_available",
                "provider_family_and_terminal_context",
                "source_stage_and_active_landmark_scope",
                "explicit abstain/no_selector_when_no_safe_pair evidence",
            ],
            "forbidden_shortcuts": [
                "global provider penalty",
                "forced-capacity labels as direct ownership labels",
                "Stage7 training rows",
                "runtime selector before paired-objective review",
            ],
        },
        "decision": {
            "status": status,
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": "design_non_causal_state_local_paired_ownership_objective",
        },
        "blocked_next_steps": [
            "runtime_selector",
            "selector_training",
            "runtime_arbiter",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_review(payload)
    return payload


def validate_review(payload: dict[str, Any]) -> None:
    if payload.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("review must remain non-causal")
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
        "# KRK Ownership Objective Architecture Review v0",
        "",
        "This review closes the latest ownership-evidence branch. It does not "
        "authorize runtime behavior, selector training, Stage 7 promotion, or Stage 8 training.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    for item in payload["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Recommended Next Design", ""])
    for key, value in payload["recommended_next_design"].items():
        lines.append(f"- `{key}`: `{value}`")
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
    payload = build_review()
    write_outputs(repo_root, payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
