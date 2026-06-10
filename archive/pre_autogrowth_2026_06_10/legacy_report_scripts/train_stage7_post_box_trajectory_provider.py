#!/usr/bin/env python3
"""Train a tiny visible-term scorer for Stage 7 post-box continuation.

This consumes the non-causal DTM trajectory seed and produces a sandbox model
that scores legal moves from graph-visible move-shape/post-move terms. The
model artifact is not promoted, does not contain tablebase state lookup, and
must only be used through an explicit opt-in sandbox topology.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _features(item: dict[str, Any]) -> set[str]:
    feats = set()
    if item.get("piece"):
        feats.add(f"piece:{item['piece']}")
    if item.get("is_king_move"):
        feats.add("piece_type:king")
    if item.get("is_rook_move"):
        feats.add("piece_type:rook")
    for term in item.get("coordinate_terms") or []:
        feats.add(f"coord:{term}")
    for term in item.get("move_shape_terms") or []:
        feats.add(f"move_shape:{term}")
    for term in item.get("post_move_terms") or []:
        feats.add(f"post_move:{term}")
    return feats


def _examples(seed: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for trajectory in seed.get("trajectories") or []:
        if not isinstance(trajectory, dict):
            continue
        for step in trajectory.get("white_training_steps") or []:
            if not isinstance(step, dict):
                continue
            fen = str(step.get("fen") or "")
            for item in step.get("legal_move_labels") or []:
                if not isinstance(item, dict):
                    continue
                rows.append({
                    "fen": fen,
                    "move": item.get("move"),
                    "label": int(item.get("label", 0) or 0),
                    "target_class": item.get("target_class"),
                    "child_dtm": item.get("child_dtm"),
                    "features": sorted(_features(item)),
                })
    return rows


def train_model(*, seed_path: Path, l2: float = 1.0, max_abs_weight: float = 3.0) -> dict[str, Any]:
    seed = _load_json(seed_path)
    rows = _examples(seed)
    pos = [row for row in rows if row["label"] == 1]
    neg = [row for row in rows if row["label"] == 0]
    if not pos or not neg:
        raise ValueError("trajectory seed must contain positive and negative legal-move labels")

    pos_counts: Counter[str] = Counter()
    neg_counts: Counter[str] = Counter()
    for row in pos:
        pos_counts.update(row["features"])
    for row in neg:
        neg_counts.update(row["features"])

    terms = sorted(set(pos_counts) | set(neg_counts))
    weights: dict[str, float] = {}
    for term in terms:
        p_rate = (pos_counts[term] + l2) / (len(pos) + 2.0 * l2)
        n_rate = (neg_counts[term] + l2) / (len(neg) + 2.0 * l2)
        weight = math.log(p_rate / n_rate)
        weights[term] = max(-max_abs_weight, min(max_abs_weight, weight))
    bias = math.log((len(pos) + l2) / (len(neg) + l2))

    def score(row: dict[str, Any]) -> float:
        return bias + sum(weights.get(term, 0.0) for term in row["features"])

    per_fen: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        row = dict(row)
        row["score"] = score(row)
        per_fen[row["fen"]].append(row)

    selected_rows = []
    correct_top1 = 0
    for fen, fen_rows in sorted(per_fen.items()):
        best = max(fen_rows, key=lambda row: (row["score"], row["move"] or ""))
        positives = [row for row in fen_rows if row["label"] == 1]
        if best["label"] == 1:
            correct_top1 += 1
        selected_rows.append({
            "fen": fen,
            "selected_move": best["move"],
            "selected_label": best["label"],
            "selected_score": best["score"],
            "positive_moves": [row["move"] for row in positives],
            "positive_count": len(positives),
        })

    top_terms = sorted(weights.items(), key=lambda item: abs(item[1]), reverse=True)[:40]
    return {
        "schema_version": "stage7_post_box_trajectory_provider_model.v1",
        "causal_status": "sandbox_model_non_promoted",
        "training_seed_source": str(seed_path),
        "target_skill": "krk.post_box_shrink_continuation",
        "provider_skill_id": "krk.stage7_post_box_learned_continuation",
        "provider_version": "stage7_post_box_continuation_overlay_v1",
        "role_id": "krk.post_box_shrink_continuation",
        "plan_capsule_id": "krk.post_box_shrink_continuation",
        "default_enabled": False,
        "promotion_status": "sandbox_candidate",
        "provider_maturity": "candidate_high_plasticity",
        "plasticity_scope": "candidate_local",
        "can_m3_update": True,
        "can_m4_consolidate": False,
        "bounded_plan_ownership": {
            "ttl_white_moves": 4,
            "entry_terms": [
                "active_landmark_label.box_shrink",
                "post_box_shrink_continuation_needed",
                "stage7_post_box_post_reply_context",
                "rook_safe",
                "mate_in_one_available.false",
            ],
            "progress_terms": [
                "cut_or_fence_preserved_or_restored",
                "box_area_not_expanded",
                "king_support_improves",
                "mate_basin_proximity_improves",
                "stagnation_avoided",
            ],
            "exit_terms": [
                "mate_in_one_available",
                "stage0_finish_licensed",
                "edge_trap_role_confirmed",
                "drive_to_edge_role_confirmed",
                "fence_or_cut_restored",
            ],
            "abort_terms": [
                "rook_unsafe",
                "draw_or_stalemate_risk",
                "box_expansion",
                "stagnation_loop",
                "no_progress_after_ttl",
            ],
        },
        "model_kind": "visible_term_log_odds_linear_scorer",
        "bias": bias,
        "weights": weights,
        "positive_count": len(pos),
        "negative_count": len(neg),
        "feature_count": len(weights),
        "train_top1_accuracy": correct_top1 / max(1, len(per_fen)),
        "train_position_count": len(per_fen),
        "selected_rows": selected_rows,
        "top_weighted_terms": [{"term": term, "weight": value} for term, value in top_terms],
        "runtime_forbidden_terms": [
            "tablebase_lookup",
            "dtm_oracle_move_selection",
            "state_hash_exception",
        ],
        "constraints": [
            "sandbox_opt_in_only",
            "do_not_enable_by_default",
            "do_not_promote_without_guardrails",
            "do_not_use_dtm_or_tablebase_at_runtime",
            "visible_terms_only_at_runtime",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Train Stage 7 post-box visible-term provider model")
    parser.add_argument("--trajectory-seed", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--l2", type=float, default=1.0)
    parser.add_argument("--max-abs-weight", type=float, default=3.0)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = train_model(
        seed_path=args.trajectory_seed,
        l2=args.l2,
        max_abs_weight=args.max_abs_weight,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
