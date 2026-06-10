#!/usr/bin/env python3
"""Review KRK state-local paired ownership probe v1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROBE = Path("reports/krk_state_local_paired_ownership_probe_v1.json")
ERROR_AUDIT = Path("reports/krk_state_local_paired_ownership_error_audit_v0.json")
OUT_JSON = Path("reports/krk_state_local_paired_ownership_review_v1.json")
OUT_MD = Path("reports/krk_state_local_paired_ownership_review_v1.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    probe = _load(PROBE)
    audit = _load(ERROR_AUDIT)
    if probe.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("probe must remain non-causal")
    if audit.get("causal_status") != "non_causal_error_audit":
        raise ValueError("audit must remain non-causal")
    passing = probe.get("threshold_passing_models") or {}
    runtime_passing = probe.get("runtime_feature_passing_models") or {}
    best = probe.get("best_result") or {}
    if runtime_passing:
        status = "runtime_feature_model_review_ready"
        next_step = "prepare_runtime_review_packet_for_explicit_approval"
    elif passing:
        status = "semantic_gate_review_ready_runtime_feature_translation_needed"
        next_step = "prepare_runtime_review_packet_with_translation_blocker"
    else:
        status = "paired_objective_feature_model_insufficient"
        next_step = "write_paired_ownership_blocker_review"
    payload = {
        "schema_version": "krk_state_local_paired_ownership_review.v1",
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
        "source_artifacts": [str(PROBE), str(ERROR_AUDIT)],
        "summary": {
            "threshold_passing_model_count": (probe.get("summary") or {}).get("threshold_passing_model_count"),
            "runtime_feature_passing_model_count": (probe.get("summary") or {}).get("runtime_feature_passing_model_count"),
            "best_objective": best.get("objective"),
            "prefer_capacity_recall": best.get("prefer_capacity_recall"),
            "selected_preservation_recall": best.get("selected_preservation_recall"),
            "safe_preservation_recall": best.get("safe_preservation_recall"),
            "strong_conflict_accuracy": best.get("strong_conflict_accuracy"),
            "safe_preservation_false_positive_count": best.get("safe_preservation_false_positive_count"),
            "stage7_row_count": (probe.get("summary") or {}).get("stage7_row_count"),
        },
        "interpretation": [
            "The safe-preservation semantics are now clean: selected-failed plus forced-mate prefers the alternative; selected-mate plus forced-mate preserves selected ownership.",
            "This validates the paired objective semantics and fixes the v0 safe-preservation false positives.",
            "The threshold-passing models rely on offline outcome/evidence-channel labels, so they are not directly runtime-feature eligible.",
            "A runtime sandbox design would need visible proxies for selected-owner failure risk and safe-preservation confidence before implementation.",
        ],
        "decision": {
            "status": status,
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": next_step,
        },
        "blocked_next_steps": [
            "runtime_selector_implementation",
            "selector_training",
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
        "# KRK State-Local Paired Ownership Review v1",
        "",
        "Non-causal review of safer paired-ownership semantics.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    for item in payload["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def write_outputs(repo_root: Path, payload: dict[str, Any]) -> None:
    (repo_root / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
