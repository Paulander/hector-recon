#!/usr/bin/env python3
"""Audit state-local contrast between optimal and hard-negative Stage 7 moves.

This is an offline, non-causal diagnostic. It asks whether existing visible
terms separate DTM-positive moves from winning-nonoptimal hard negatives within
the same board state. It does not train, route, mutate topology, or use
DTM/tablebase at runtime.
"""

from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any

import benchmark_stage7_training_objectives as bench


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _term_set(label: dict[str, Any]) -> set[str]:
    return bench._all_terms(label)


def _pair_terms(terms: set[str]) -> set[tuple[str, str]]:
    selected = sorted(term for term in terms if not term.startswith("coordinate_terms."))
    return set(itertools.combinations(selected, 2))


def _step_contrast(step: dict[str, Any]) -> dict[str, Any]:
    positives = [label for label in step["labels"] if bench._is_positive(label)]
    hard_negatives = [
        label for label in step["labels"] if str(label.get("target_class") or "") == "winning_nonoptimal_move"
    ]
    non_winning = [label for label in step["labels"] if str(label.get("target_class") or "") == "non_winning_move"]

    pos_terms = [_term_set(label) for label in positives]
    hard_terms = [_term_set(label) for label in hard_negatives]
    hard_union = set().union(*hard_terms) if hard_terms else set()
    pos_union = set().union(*pos_terms) if pos_terms else set()
    positive_unique = sorted(pos_union - hard_union)
    hard_negative_unique = sorted(hard_union - pos_union)

    pos_pairs = set().union(*(_pair_terms(terms) for terms in pos_terms)) if pos_terms else set()
    hard_pairs = set().union(*(_pair_terms(terms) for terms in hard_terms)) if hard_terms else set()
    positive_pair_unique = sorted(pos_pairs - hard_pairs)

    best_positive = min((label.get("child_dtm", 9999) for label in positives), default=None)
    best_hard = min((label.get("child_dtm", 9999) for label in hard_negatives), default=None)
    if positive_unique:
        diagnosis = "single_terms_separate_positive_from_hard_negative"
    elif positive_pair_unique:
        diagnosis = "term_interactions_separate_positive_from_hard_negative"
    elif positives and hard_negatives:
        diagnosis = "visible_terms_collide_with_hard_negatives"
    else:
        diagnosis = "insufficient_state_local_comparison"

    return {
        "trajectory_index": step["trajectory_index"],
        "step_index": step["step_index"],
        "fen": step["fen"],
        "positive_move_count": len(positives),
        "hard_negative_move_count": len(hard_negatives),
        "non_winning_move_count": len(non_winning),
        "best_positive_child_dtm": best_positive,
        "best_hard_negative_child_dtm": best_hard,
        "positive_unique_terms": positive_unique[:25],
        "hard_negative_unique_terms": hard_negative_unique[:25],
        "positive_unique_pair_terms": [
            {"term_a": a, "term_b": b} for a, b in positive_pair_unique[:25]
        ],
        "diagnosis": diagnosis,
    }


def build_audit(artifact_root: Path) -> dict[str, Any]:
    seed_path = artifact_root / "stage7_post_box_dtm_trajectory_seed_expanded_h40.json"
    calibration_path = artifact_root / "stage7_ranking_calibration_audit.json"
    seed = _load_json(seed_path)
    calibration = _load_json(calibration_path) if calibration_path.exists() else {}
    steps = bench._trajectory_steps(seed)
    rows = [_step_contrast(step) for step in steps]
    diagnosis_counts = Counter(row["diagnosis"] for row in rows)

    positive_unique_terms = Counter(
        term for row in rows for term in row["positive_unique_terms"]
    )
    hard_negative_unique_terms = Counter(
        term for row in rows for term in row["hard_negative_unique_terms"]
    )
    positive_pair_terms = Counter(
        (pair["term_a"], pair["term_b"])
        for row in rows
        for pair in row["positive_unique_pair_terms"]
    )

    separable_single = diagnosis_counts["single_terms_separate_positive_from_hard_negative"]
    separable_pair = diagnosis_counts["term_interactions_separate_positive_from_hard_negative"]
    colliding = diagnosis_counts["visible_terms_collide_with_hard_negatives"]
    total = len(rows) or 1
    if separable_single / total >= 0.5:
        candidate_status = "state_local_single_terms_available"
        next_action = "non-causal visible term refinement audit before any runtime patch"
    elif (separable_single + separable_pair) / total >= 0.5:
        candidate_status = "state_local_interaction_terms_needed"
        next_action = "offline interaction-feature benchmark; no runtime repair"
    elif colliding / total >= 0.5:
        candidate_status = "visible_terminal_space_underexpressive_for_state_local_ranking"
        next_action = "pause Stage 7 repair work and request architecture review before adding representation"
    else:
        candidate_status = "state_local_contrast_inconclusive"
        next_action = "do not patch; collect a broader but still offline contrast sample only if justified"

    audit = {
        "schema_version": "stage7_state_local_contrast_audit.v1",
        "causal_status": "non_causal_offline_audit",
        "runtime_behavior_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "stage7_status": "local_valid_composition_quarantined",
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": {
            "expanded_trajectory_seed": str(seed_path),
            "ranking_calibration_audit": str(calibration_path),
        },
        "dataset": {
            "step_count": len(rows),
            "calibration_candidate_status": calibration.get("candidate_status"),
        },
        "diagnosis_counts": dict(diagnosis_counts),
        "separability_rates": {
            "single_term_rate": separable_single / float(total),
            "single_or_pair_term_rate": (separable_single + separable_pair) / float(total),
            "collision_rate": colliding / float(total),
        },
        "top_positive_unique_terms": [
            {"term": term, "count": count} for term, count in positive_unique_terms.most_common(25)
        ],
        "top_hard_negative_unique_terms": [
            {"term": term, "count": count} for term, count in hard_negative_unique_terms.most_common(25)
        ],
        "top_positive_unique_pair_terms": [
            {"term_a": a, "term_b": b, "count": count}
            for (a, b), count in positive_pair_terms.most_common(25)
        ],
        "sample_rows": rows[:20],
        "candidate_status": candidate_status,
        "recommended_next_step": next_action,
        "blocked_next_steps": [
            "runtime_repair",
            "stage7_promotion",
            "stage8_training",
            "support_adapter",
            "score_bonus_or_provider_penalty",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_audit(audit)
    return audit


def validate_audit(audit: dict[str, Any]) -> None:
    if audit.get("schema_version") != "stage7_state_local_contrast_audit.v1":
        raise ValueError("unexpected audit schema")
    if audit.get("causal_status") != "non_causal_offline_audit":
        raise ValueError("audit must be non-causal")
    if audit.get("runtime_behavior_changed") is not False:
        raise ValueError("audit must not change runtime behavior")
    if audit.get("runtime_dtm_or_tablebase_lookup") is not False:
        raise ValueError("audit must not use runtime DTM/tablebase")
    if audit.get("stage7_promotion_allowed") is not False or audit.get("stage8_training_allowed") is not False:
        raise ValueError("Stage 7 promotion and Stage 8 training must remain blocked")


def render_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 State-Local Contrast Audit",
        "",
        "This audit is offline-only and non-causal. It checks whether existing visible terms separate positives from hard negatives inside each state.",
        "",
        "## Status",
        "",
        f"- Candidate status: `{audit['candidate_status']}`",
        f"- Recommended next step: {audit['recommended_next_step']}",
        f"- Stage 7 promotion allowed: `{audit['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{audit['stage8_training_allowed']}`",
        "",
        "## Summary",
        "",
        f"- Step count: `{audit['dataset']['step_count']}`",
        f"- Diagnosis counts: `{audit['diagnosis_counts']}`",
        f"- Separability rates: `{audit['separability_rates']}`",
        "",
        "## Top Positive-Unique Terms",
        "",
    ]
    lines.extend(
        f"- `{item['term']}`: {item['count']}" for item in audit["top_positive_unique_terms"][:12]
    )
    lines.extend(["", "## Top Hard-Negative-Unique Terms", ""])
    lines.extend(
        f"- `{item['term']}`: {item['count']}" for item in audit["top_hard_negative_unique_terms"][:12]
    )
    lines.extend(["", "## Top Positive-Unique Term Pairs", ""])
    lines.extend(
        f"- `{item['term_a']}` + `{item['term_b']}`: {item['count']}"
        for item in audit["top_positive_unique_pair_terms"][:12]
    )
    lines.extend(["", "## Sample Rows", ""])
    for row in audit["sample_rows"][:8]:
        lines.append(
            f"- traj {row['trajectory_index']} step {row['step_index']}: `{row['diagnosis']}`, "
            f"positive_unique={row['positive_unique_terms'][:5]}"
        )
    lines.extend(["", "## Blocked Next Steps", ""])
    lines.extend(f"- {item}" for item in audit["blocked_next_steps"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path("reports/structural_candidates"))
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    audit = build_audit(args.artifact_root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(audit), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
