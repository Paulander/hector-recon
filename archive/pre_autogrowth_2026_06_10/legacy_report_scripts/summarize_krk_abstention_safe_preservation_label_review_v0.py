#!/usr/bin/env python3
"""Review abstention label semantics after context features over-reject safe owners."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_abstention_context_feature_dataset_v0.json")
PROBE = Path("reports/krk_abstention_context_feature_probe_v0.json")
ERROR_AUDIT = Path("reports/krk_abstention_context_error_audit_v0.json")
OUT_JSON = Path("reports/krk_abstention_safe_preservation_label_review_v0.json")
OUT_MD = Path("reports/krk_abstention_safe_preservation_label_review_v0.md")


def _load_json(root: Path, path: Path) -> dict[str, Any]:
    payload = json.loads((root / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _by_label_source(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    buckets: dict[str, Counter[str]] = {}
    for row in rows:
        kind = str(row.get("label_source_kind"))
        buckets.setdefault(kind, Counter())[str(row.get("label"))] += 1
    return {key: dict(counter) for key, counter in sorted(buckets.items())}


def _forced_provider_safe_false_positive_examples(audit: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in ((audit.get("examples") or {}).get("false_positives") or [])
        if item.get("label_source_kind") == "forced_provider_conversion"
    ]


def validate_review(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["decision"]["runtime_test_allowed_next"] is not False:
        raise ValueError("label review must not authorize runtime testing")


def build_review(root: Path = ROOT) -> dict[str, Any]:
    dataset = _load_json(root, DATASET)
    probe = _load_json(root, PROBE)
    audit = _load_json(root, ERROR_AUDIT)
    for name, payload in (("dataset", dataset), ("probe", probe), ("audit", audit)):
        if not str(payload.get("causal_status") or "").startswith("non_causal"):
            raise ValueError(f"{name} must remain non-causal")

    rows = [row for row in dataset.get("rows") or [] if row.get("usable_for_training") is True]
    false_positive_patterns = (audit.get("error_patterns") or {})
    forced_fp_examples = _forced_provider_safe_false_positive_examples(audit)
    summary = {
        "row_count": len(rows),
        "label_source_distribution": _by_label_source(rows),
        "best_context_objective": (probe.get("best_result") or {}).get("objective"),
        "best_negative_suppression": (probe.get("best_result") or {}).get("negative_suppression"),
        "best_safe_preservation": (probe.get("best_result") or {}).get("safe_preservation"),
        "false_positive_count": (audit.get("summary") or {}).get("false_positive_count"),
        "false_positive_forced_provider_conversion_examples": len(forced_fp_examples),
        "false_positive_by_provider_family": false_positive_patterns.get("false_positive_by_provider_family"),
        "false_positive_by_label_source_kind": false_positive_patterns.get("false_positive_by_label_source_kind"),
    }
    label_semantics_findings = [
        {
            "finding": "forced_provider_conversion and selected_playout_success labels should not be treated as identical abstention targets",
            "reason": "False positives include known-safe forced-provider conversions, especially Stage 5 edge-trap owners.",
            "implication": "An abstention gate needs to preserve validated provider conversions even when context looks risky.",
        },
        {
            "finding": "king-support context is useful for unsafe-owner recall but too aggressive as a one-stage rejection rule",
            "reason": "It reaches high negative suppression but misses safe-preservation threshold.",
            "implication": "Use it as a risk feature inside a two-stage objective, not as a runtime decision rule.",
        },
        {
            "finding": "repair/phase monitor signatures are ambiguous",
            "reason": "They occur in both failed and successful protected contexts.",
            "implication": "Future labels need companion semantics: repair needed, repair possible, and repair-preserves-conversion should be separated.",
        },
    ]
    proposed_objective = {
        "name": "two_stage_abstention_preservation_objective_v0",
        "causal_status": "non_causal_design_only",
        "stage_1": {
            "goal": "preserve validated safe owners",
            "positive_examples": "forced_provider_conversion safe_owner rows and selected_playout_success positive rows",
            "failure_to_avoid": "false_positive_safe_owner_rejected",
            "minimum_safe_preservation_before_runtime_review": 0.75,
        },
        "stage_2": {
            "goal": "suppress unsafe owners after preservation filter",
            "positive_examples_for_rejection": "unsafe_owner rows separated by label_source_kind",
            "minimum_negative_suppression_before_runtime_review": 0.7,
        },
        "required_separations": [
            "forced_provider_conversion vs selected_playout_success",
            "provider_can_convert_if_forced vs normal_selected_provider_failed",
            "repair_needed_monitor vs repair_preserves_conversion",
            "white_king_support_bucket risk vs validated edge_trap safe ownership",
        ],
    }
    payload = {
        "schema_version": "krk_abstention_safe_preservation_label_review.v0",
        "causal_status": "non_causal_architecture_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET), str(PROBE), str(ERROR_AUDIT)],
        "summary": summary,
        "label_semantics_findings": label_semantics_findings,
        "proposed_non_causal_objective": proposed_objective,
        "blocked_runtime_interpretation": [
            "Do not turn king-support bucket into a causal abstention terminal.",
            "Do not suppress edge-trap ownership from this evidence.",
            "Do not use monitor signatures as direct runtime rejections.",
        ],
        "decision": {
            "status": "safe_preservation_requires_two_stage_label_semantics",
            "recommended_next_step": "design_or_probe_two_stage_abstention_objective_non_causal",
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_review(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Abstention Safe-Preservation Label Review v0",
        "",
        "This review explains the context-feature abstention blocker as a label-semantics issue. It is design/evidence only and does not authorize runtime selector behavior.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Findings", ""])
    for item in payload["label_semantics_findings"]:
        lines.append(f"- `{item['finding']}`: {item['reason']} Implication: {item['implication']}")
    lines.extend(["", "## Proposed Non-Causal Objective", ""])
    objective = payload["proposed_non_causal_objective"]
    lines.append(f"- Name: `{objective['name']}`")
    lines.append(f"- Stage 1 goal: {objective['stage_1']['goal']}")
    lines.append(f"- Stage 2 goal: {objective['stage_2']['goal']}")
    lines.append(f"- Required separations: `{objective['required_separations']}`")
    lines.extend(["", "## Runtime Blocks", ""])
    for item in payload["blocked_runtime_interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Decision", ""])
    lines.append(f"- Status: `{payload['decision']['status']}`")
    lines.append(f"- Recommended next step: `{payload['decision']['recommended_next_step']}`")
    lines.append(f"- Runtime test allowed next: `{payload['decision']['runtime_test_allowed_next']}`")
    lines.append(f"- Stage 7 promotion allowed: `{payload['decision']['stage7_promotion_allowed']}`")
    lines.append(f"- Stage 8 training allowed: `{payload['decision']['stage8_training_allowed']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
