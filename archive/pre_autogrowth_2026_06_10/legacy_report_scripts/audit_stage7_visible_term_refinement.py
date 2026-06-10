#!/usr/bin/env python3
"""Derive non-causal visible-term refinement candidates for Stage 7.

This replay-free audit combines the ranking calibration and state-local
contrast artifacts. It does not add terminals, train, route, mutate topology, or
use DTM/tablebase at runtime. Its job is to identify which existing visible
terms look useful only when scoped by companion terms, and which terms are too
broad to use as standalone causal evidence.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import benchmark_stage7_training_objectives as bench


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _term_kind(term: str) -> str:
    name = term.split(".", 1)[-1]
    if "box_area" in name:
        return "box_progress"
    if "king" in name or "support" in name or "opposition" in name:
        return "king_support"
    if "fence" in name or "cut" in name or "checking_line" in name:
        return "cut_fence_line"
    if "rook" in name:
        return "rook_geometry"
    if "edge" in name or "corner" in name or "escape" in name:
        return "edge_net_pressure"
    if "draw" in name or "stalemate" in name or "unsafe" in name:
        return "safety_veto"
    return "other"


def _term_stats(steps: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for step in steps:
        for label in step["labels"]:
            target = str(label.get("target_class") or "")
            bucket = (
                "positive"
                if bench._is_positive(label)
                else "hard_negative"
                if target == "winning_nonoptimal_move"
                else "non_winning"
            )
            for term in bench._all_terms(label):
                counts[term][bucket] += 1

    rows: dict[str, dict[str, Any]] = {}
    for term, counter in counts.items():
        positive = counter["positive"]
        hard_negative = counter["hard_negative"]
        non_winning = counter["non_winning"]
        total = positive + hard_negative + non_winning
        if not total:
            continue
        rows[term] = {
            "term": term,
            "kind": _term_kind(term),
            "positive_count": positive,
            "hard_negative_count": hard_negative,
            "non_winning_count": non_winning,
            "total_count": total,
            "positive_rate": positive / float(total),
            "hard_negative_rate": hard_negative / float(total),
            "non_winning_rate": non_winning / float(total),
            "collision_score": min(positive, hard_negative) / float(max(positive, hard_negative, 1)),
        }
    return rows


def _counter_from_items(items: list[dict[str, Any]], key: str = "term") -> Counter[str]:
    counter: Counter[str] = Counter()
    for item in items:
        term = str(item.get(key) or "")
        if not term:
            continue
        counter[term] += int(item.get("count", 0) or 0)
    return counter


def _positive_term_candidates(
    contrast: dict[str, Any], stats: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    unique_counts = _counter_from_items(contrast.get("top_positive_unique_terms") or [])
    rows: list[dict[str, Any]] = []
    for term, state_local_count in unique_counts.most_common():
        row = dict(stats.get(term) or {"term": term, "kind": _term_kind(term)})
        row["state_local_positive_unique_count"] = state_local_count
        hard = int(row.get("hard_negative_count", 0) or 0)
        pos = int(row.get("positive_count", 0) or 0)
        collision = float(row.get("collision_score", 0.0) or 0.0)
        if hard and collision >= 0.25:
            status = "candidate_positive_term_requires_companion_scope"
        elif pos > hard:
            status = "candidate_positive_term_standalone_hypothesis"
        else:
            status = "candidate_positive_term_weak_global_support"
        row["refinement_status"] = status
        row["suggested_use"] = (
            "Do not add as causal standalone term; evaluate only as scoped evidence in a future sandbox."
        )
        rows.append(row)
    return rows[:30]


def _interaction_candidates(
    contrast: dict[str, Any], stats: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in contrast.get("top_positive_unique_pair_terms") or []:
        term_a = str(item.get("term_a") or "")
        term_b = str(item.get("term_b") or "")
        if not term_a or not term_b:
            continue
        kinds = sorted({_term_kind(term_a), _term_kind(term_b)})
        stat_a = stats.get(term_a) or {}
        stat_b = stats.get(term_b) or {}
        max_collision = max(
            float(stat_a.get("collision_score", 0.0) or 0.0),
            float(stat_b.get("collision_score", 0.0) or 0.0),
        )
        if max_collision >= 0.25:
            status = "candidate_interaction_scopes_ambiguous_terms"
        else:
            status = "candidate_interaction_positive_context"
        rows.append(
            {
                "term_a": term_a,
                "term_b": term_b,
                "kinds": kinds,
                "state_local_positive_pair_count": int(item.get("count", 0) or 0),
                "max_component_collision_score": max_collision,
                "refinement_status": status,
                "suggested_use": (
                    "Keep non-causal; if later sandboxed, require both terms rather than either term alone."
                ),
            }
        )
    return rows[:30]


def _ambiguous_term_candidates(
    calibration: dict[str, Any], contrast: dict[str, Any], stats: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    positive_unique = _counter_from_items(contrast.get("top_positive_unique_terms") or [])
    rows: list[dict[str, Any]] = []
    collision_terms = (
        (calibration.get("term_collision_summary") or {}).get("high_collision_terms") or []
    )
    hard_unique = _counter_from_items(contrast.get("top_hard_negative_unique_terms") or [])
    seen: set[str] = set()
    for item in collision_terms:
        term = str(item.get("term") or "")
        if not term or term in seen:
            continue
        seen.add(term)
        row = dict(stats.get(term) or item)
        row["state_local_positive_unique_count"] = positive_unique.get(term, 0)
        row["state_local_hard_negative_unique_count"] = hard_unique.get(term, 0)
        row["refinement_status"] = (
            "ambiguous_but_state_local_positive"
            if positive_unique.get(term, 0)
            else "ambiguous_global_term_needs_companion_or_veto"
        )
        row["suggested_use"] = (
            "Block standalone causal use; require role/phase scope plus a separator companion term."
        )
        rows.append(row)
    return rows[:30]


def _blocked_or_veto_candidates(
    calibration: dict[str, Any], contrast: dict[str, Any], stats: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    hard_unique = _counter_from_items(contrast.get("top_hard_negative_unique_terms") or [])
    veto_terms = (
        (calibration.get("term_collision_summary") or {}).get("safety_veto_candidates") or []
    )
    terms = Counter(hard_unique)
    for item in veto_terms:
        term = str(item.get("term") or "")
        if term:
            terms[term] += int(item.get("non_winning_count", 0) or 0)
    rows: list[dict[str, Any]] = []
    for term, count in terms.most_common(30):
        row = dict(stats.get(term) or {"term": term, "kind": _term_kind(term)})
        row["state_local_hard_negative_or_veto_count"] = count
        row["refinement_status"] = (
            "candidate_hard_negative_suppression_context"
            if row.get("hard_negative_count", 0)
            else "candidate_safety_veto_context"
        )
        row["suggested_use"] = (
            "Non-causal only; use to explain hard negatives before considering explicit visible veto terms."
        )
        rows.append(row)
    return rows


def build_audit(artifact_root: Path) -> dict[str, Any]:
    seed_path = artifact_root / "stage7_post_box_dtm_trajectory_seed_expanded_h40.json"
    calibration_path = artifact_root / "stage7_ranking_calibration_audit.json"
    contrast_path = artifact_root / "stage7_state_local_contrast_audit.json"
    seed = _load_json(seed_path)
    calibration = _load_json(calibration_path)
    contrast = _load_json(contrast_path)
    steps = bench._trajectory_steps(seed)
    stats = _term_stats(steps)

    positive_terms = _positive_term_candidates(contrast, stats)
    interactions = _interaction_candidates(contrast, stats)
    ambiguous_terms = _ambiguous_term_candidates(calibration, contrast, stats)
    blocked_terms = _blocked_or_veto_candidates(calibration, contrast, stats)

    kind_counts = Counter(item["kind"] for item in positive_terms if item.get("kind"))
    interaction_kind_counts = Counter("+".join(item["kinds"]) for item in interactions)
    companion_required = sum(
        1
        for item in positive_terms
        if item["refinement_status"] == "candidate_positive_term_requires_companion_scope"
    )
    if positive_terms and companion_required / float(len(positive_terms)) >= 0.25:
        candidate_status = "visible_term_refinement_candidates_require_scoped_interactions"
        next_step = "non-causal scoped interaction benchmark; no runtime patch"
    else:
        candidate_status = "visible_term_refinement_candidates_non_causal"
        next_step = "architecture review or offline benchmark before any visible-term sandbox"

    audit = {
        "schema_version": "stage7_visible_term_refinement_audit.v1",
        "causal_status": "non_causal_offline_audit",
        "runtime_behavior_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "stage7_status": "local_valid_composition_quarantined",
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": {
            "expanded_trajectory_seed": str(seed_path),
            "ranking_calibration_audit": str(calibration_path),
            "state_local_contrast_audit": str(contrast_path),
        },
        "dataset": {
            "step_count": len(steps),
            "term_count": len(stats),
            "ranking_candidate_status": calibration.get("candidate_status"),
            "state_local_candidate_status": contrast.get("candidate_status"),
        },
        "summary": {
            "positive_term_kind_counts": dict(kind_counts),
            "interaction_kind_counts": dict(interaction_kind_counts),
            "positive_terms_requiring_companion_scope": companion_required,
            "positive_term_candidate_count": len(positive_terms),
            "interaction_candidate_count": len(interactions),
            "ambiguous_term_candidate_count": len(ambiguous_terms),
            "hard_negative_or_veto_candidate_count": len(blocked_terms),
        },
        "positive_term_refinement_candidates": positive_terms,
        "interaction_refinement_candidates": interactions,
        "ambiguous_terms_requiring_scope": ambiguous_terms,
        "hard_negative_or_veto_context_candidates": blocked_terms,
        "candidate_status": candidate_status,
        "recommended_next_step": next_step,
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
    if audit.get("schema_version") != "stage7_visible_term_refinement_audit.v1":
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
        "# Stage 7 Visible-Term Refinement Audit",
        "",
        "This audit is replay-free and non-causal. It derives visible-term refinement hypotheses from the ranking calibration and state-local contrast artifacts.",
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
        f"- Dataset: `{audit['dataset']}`",
        f"- Positive term kind counts: `{audit['summary']['positive_term_kind_counts']}`",
        f"- Interaction kind counts: `{audit['summary']['interaction_kind_counts']}`",
        f"- Positive terms requiring companion scope: `{audit['summary']['positive_terms_requiring_companion_scope']}`",
        "",
        "## Positive-Term Refinement Candidates",
        "",
    ]
    for item in audit["positive_term_refinement_candidates"][:12]:
        lines.append(
            f"- `{item['term']}` ({item.get('kind')}): state_local={item.get('state_local_positive_unique_count')}, "
            f"pos={item.get('positive_count', 0)}, hard_neg={item.get('hard_negative_count', 0)}, "
            f"status=`{item['refinement_status']}`"
        )
    lines.extend(["", "## Interaction Candidates", ""])
    for item in audit["interaction_refinement_candidates"][:12]:
        lines.append(
            f"- `{item['term_a']}` + `{item['term_b']}`: count={item['state_local_positive_pair_count']}, "
            f"status=`{item['refinement_status']}`"
        )
    lines.extend(["", "## Ambiguous Terms Requiring Scope", ""])
    for item in audit["ambiguous_terms_requiring_scope"][:12]:
        lines.append(
            f"- `{item['term']}` ({item.get('kind')}): pos={item.get('positive_count', 0)}, "
            f"hard_neg={item.get('hard_negative_count', 0)}, status=`{item['refinement_status']}`"
        )
    lines.extend(["", "## Hard-Negative Or Veto Context Candidates", ""])
    for item in audit["hard_negative_or_veto_context_candidates"][:12]:
        lines.append(
            f"- `{item['term']}` ({item.get('kind')}): count={item.get('state_local_hard_negative_or_veto_count')}, "
            f"status=`{item['refinement_status']}`"
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
