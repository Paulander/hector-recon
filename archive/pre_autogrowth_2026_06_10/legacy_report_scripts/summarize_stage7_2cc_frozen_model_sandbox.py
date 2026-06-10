#!/usr/bin/env python3
"""Summarize the Stage 7 2cc frozen-model sandbox smoke.

This is a reporting-only candidate status update. It compares a default-off run
with an explicit sandbox-on run and classifies whether the frozen model hook is
working, underbroad, overbroad, or still insufficient.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def summarize_sandbox(*, default_off: dict[str, Any], enabled: dict[str, Any]) -> dict[str, Any]:
    off_count = int(
        default_off.get("stage7_post_box_frozen_model_candidate_supported_suggestion_count", 0)
        or 0
    )
    on_count = int(
        enabled.get("stage7_post_box_frozen_model_candidate_supported_suggestion_count", 0)
        or 0
    )
    on_selected = int(
        enabled.get("stage7_post_box_frozen_model_candidate_selected_supported_count", 0)
        or 0
    )
    off_playouts = dict(default_off.get("playouts", {}) or {})
    on_playouts = dict(enabled.get("playouts", {}) or {})
    on_draws = int(on_playouts.get("draw", 0) or 0)
    on_max = int(on_playouts.get("max_plies", 0) or 0)
    on_mates = int(on_playouts.get("mate", 0) or 0)
    off_mates = int(off_playouts.get("mate", 0) or 0)

    if off_count:
        diagnosis = "default_off_semantics_violation"
        next_action = "stop_and_diagnose_candidate_layer_default_off"
    elif not on_count:
        diagnosis = "frozen_model_candidate_hook_underbroad_or_not_reached"
        next_action = "inspect post-box context and CandidateMoveFrame availability"
    elif on_selected and (on_draws or on_max):
        diagnosis = "selected_candidate_move_still_insufficient_for_multistep_conversion"
        next_action = "run bounded candidate-local continuation warmup only if guardrails remain scoped"
    elif on_mates > off_mates and not (on_draws or on_max):
        diagnosis = "sandbox_candidate_improves_smoke"
        next_action = "scale to 10/25 sample target before guardrails"
    else:
        diagnosis = "candidate_visible_but_no_clear_target_improvement"
        next_action = "keep candidate sandboxed; do not promote"

    return {
        "schema_version": "stage7_2cc_frozen_model_sandbox_summary.v1",
        "causal_status": "non_causal",
        "runtime_behavior_changed": False,
        "default_off": {
            "playouts": off_playouts,
            "supported_suggestion_count": off_count,
            "selected_supported_count": int(
                default_off.get(
                    "stage7_post_box_frozen_model_candidate_selected_supported_count",
                    0,
                )
                or 0
            ),
        },
        "enabled": {
            "playouts": on_playouts,
            "supported_suggestion_count": on_count,
            "selected_supported_count": on_selected,
            "supported_move_by_outcome": dict(
                enabled.get(
                    "stage7_post_box_frozen_model_candidate_supported_move_by_outcome",
                    {},
                )
                or {}
            ),
            "selected_by_outcome": dict(
                enabled.get(
                    "stage7_post_box_frozen_model_candidate_selected_by_outcome",
                    {},
                )
                or {}
            ),
        },
        "candidate_status_update": {
            "candidate_id": "cand.krk.box_shrink.family_2cc.post_box_continuation_overlay.v1",
            "diagnosis": diagnosis,
            "next_action": next_action,
            "causal_status": "non_causal",
            "promotion_status": "sandbox_hook_smoke_complete",
            "credit": 0.0,
        },
        "guardrails": [
            "do_not_train_stage8",
            "do_not_promote_stage7",
            "do_not_enable_by_default",
            "do_not_make_structural_candidate_causal",
            "do_not_use_dtm_or_tablebase_at_runtime",
        ],
    }


def _write_md(payload: dict[str, Any], path: Path) -> None:
    update = payload["candidate_status_update"]
    lines = [
        "# Stage 7 2cc Frozen Model Sandbox Summary",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Runtime behavior changed: `{payload['runtime_behavior_changed']}`",
        "",
        "## Default Off",
        "",
        f"Playouts: `{payload['default_off']['playouts']}`",
        f"Supported suggestions: `{payload['default_off']['supported_suggestion_count']}`",
        "",
        "## Enabled",
        "",
        f"Playouts: `{payload['enabled']['playouts']}`",
        f"Supported suggestions: `{payload['enabled']['supported_suggestion_count']}`",
        f"Selected supported: `{payload['enabled']['selected_supported_count']}`",
        f"Supported moves by outcome: `{payload['enabled']['supported_move_by_outcome']}`",
        f"Selected by outcome: `{payload['enabled']['selected_by_outcome']}`",
        "",
        "## Candidate Update",
        "",
        f"Candidate: `{update['candidate_id']}`",
        f"Diagnosis: `{update['diagnosis']}`",
        f"Next action: `{update['next_action']}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--default-off", type=Path, required=True)
    parser.add_argument("--enabled", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = summarize_sandbox(
        default_off=_load_json(args.default_off),
        enabled=_load_json(args.enabled),
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        _write_md(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
