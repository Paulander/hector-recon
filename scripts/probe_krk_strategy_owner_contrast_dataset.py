#!/usr/bin/env python3
"""Probe KRK strategy-owner contrast evidence non-causally."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_strategy_owner_contrast_dataset_v0.json")
OUT_JSON = Path("reports/krk_strategy_owner_contrast_probe_v0.json")
OUT_MD = Path("reports/krk_strategy_owner_contrast_probe_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _provider_family_rates(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        for label in row.get("provider_labels") or []:
            family = str(label.get("provider_family") or "unknown")
            counts[family]["total"] += 1
            counts[family]["positive" if label.get("positive") else "negative"] += 1
    return {
        family: {
            "total": counter["total"],
            "positive": counter["positive"],
            "negative": counter["negative"],
            "positive_rate": round(counter["positive"] / counter["total"], 4)
            if counter["total"]
            else 0.0,
        }
        for family, counter in sorted(counts.items())
    }


def _row_labels(row: dict[str, Any]) -> dict[str, Any]:
    positives = [label for label in row.get("provider_labels") or [] if label.get("positive")]
    negatives = [label for label in row.get("provider_labels") or [] if not label.get("positive")]
    return {
        "state_id": row.get("state_id"),
        "source_stage": row.get("source_stage"),
        "training_eligible": row.get("training_eligible"),
        "held_out_challenge": row.get("held_out_challenge"),
        "provider_count": (row.get("contrast_summary") or {}).get("provider_count"),
        "positive_provider_families": sorted({label.get("provider_family") for label in positives}),
        "negative_provider_families": sorted({label.get("provider_family") for label in negatives}),
        "positive_count": len(positives),
        "negative_count": len(negatives),
        "all_negative": bool(negatives) and not positives,
        "has_non_stage0_positive": (row.get("contrast_summary") or {}).get("has_non_stage0_positive"),
    }


def build_probe() -> dict[str, Any]:
    dataset = _load_json(DATASET)
    if dataset.get("causal_status") != "non_causal_dataset":
        raise ValueError("dataset must remain non-causal")
    rows = dataset.get("rows") or []
    training_rows = [row for row in rows if row.get("training_eligible")]
    heldout_rows = [row for row in rows if row.get("held_out_challenge")]
    training_labels = [label for row in training_rows for label in row.get("provider_labels") or []]
    training_positive = [label for label in training_labels if label.get("positive")]
    training_negative = [label for label in training_labels if not label.get("positive")]
    selected_training_families = sorted(
        {
            str(label.get("provider_family") or "unknown")
            for label in training_labels
            if label.get("selected") is True
        }
    )
    readiness_blockers = list((dataset.get("readiness_v2_assessment") or {}).get("blockers") or [])
    probe_findings = []
    if len({label.get("provider_family") for label in training_positive}) >= 3:
        probe_findings.append("protected_conversion_positive_provider_diversity_present")
    if len(training_positive) >= 6 and len(training_negative) >= 6:
        probe_findings.append("protected_label_balance_present")
    if len(selected_training_families) < 3:
        probe_findings.append("selected_provider_family_diversity_still_missing")
    if any(_row_labels(row)["all_negative"] for row in heldout_rows):
        probe_findings.append("heldout_stage7_contains_unresolved_all_negative_rows")

    status = (
        "strategy_owner_contrast_signal_present_selector_sandbox_blocked"
        if "protected_conversion_positive_provider_diversity_present" in probe_findings
        and "protected_label_balance_present" in probe_findings
        else "strategy_owner_contrast_signal_still_underpowered"
    )
    probe = {
        "schema_version": "krk_strategy_owner_contrast_probe.v0",
        "causal_status": "non_causal_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET)],
        "metrics": {
            "row_count": len(rows),
            "training_row_count": len(training_rows),
            "heldout_row_count": len(heldout_rows),
            "training_positive_label_count": len(training_positive),
            "training_negative_label_count": len(training_negative),
            "training_provider_family_rates": _provider_family_rates(training_rows),
            "heldout_provider_family_rates": _provider_family_rates(heldout_rows),
            "selected_training_provider_families": selected_training_families,
            "readiness_blockers": readiness_blockers,
        },
        "row_summaries": [_row_labels(row) for row in rows],
        "findings": probe_findings,
        "decision": {
            "status": status,
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": (
                "architecture_review_selector_readiness_after_contrast_probe"
                if status == "strategy_owner_contrast_signal_present_selector_sandbox_blocked"
                else "collect_more_protected_contrast_rows"
            ),
        },
        "blocked_next_steps": [
            "runtime_arbiter",
            "selector_sandbox",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_probe(probe)
    return probe


def validate_probe(probe: dict[str, Any]) -> None:
    if probe.get("causal_status") != "non_causal_probe":
        raise ValueError("probe must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_arbiter_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if probe.get(key) is not False:
            raise ValueError(f"{key} must be false")


def render_markdown(probe: dict[str, Any]) -> str:
    metrics = probe["metrics"]
    lines = [
        "# KRK Strategy Owner Contrast Probe v0",
        "",
        "This is a non-causal probe over protected and held-out strategy-owner contrast labels. "
        "It does not train or run a selector.",
        "",
        "## Metrics",
        "",
        f"- Rows: `{metrics['row_count']}`",
        f"- Training rows: `{metrics['training_row_count']}`",
        f"- Held-out rows: `{metrics['heldout_row_count']}`",
        f"- Training positives: `{metrics['training_positive_label_count']}`",
        f"- Training negatives: `{metrics['training_negative_label_count']}`",
        f"- Training provider family rates: `{metrics['training_provider_family_rates']}`",
        f"- Held-out provider family rates: `{metrics['heldout_provider_family_rates']}`",
        f"- Selected training provider families: `{metrics['selected_training_provider_families']}`",
        f"- Readiness blockers: `{metrics['readiness_blockers']}`",
        "",
        "## Findings",
        "",
    ]
    for finding in probe["findings"]:
        lines.append(f"- `{finding}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{probe['decision']['status']}`",
            f"- Recommended next step: `{probe['decision']['recommended_next_step']}`",
            "- Runtime arbiter and selector sandbox remain blocked.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    probe = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(probe), encoding="utf-8")
    print(json.dumps(probe["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
