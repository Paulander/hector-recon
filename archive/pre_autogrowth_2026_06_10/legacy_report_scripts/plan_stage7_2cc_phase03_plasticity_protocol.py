#!/usr/bin/env python3
"""Plan bounded candidate-local plasticity for the Stage 7 2cc family.

This does not train, promote, or alter runtime defaults. It converts the
Phase 2 replay diagnosis into an explicit bounded protocol so any later
plasticity/sandbox step is local, inspectable, and guardrailed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPECTED_DIAGNOSIS = "visible_first_step_winning_but_current_graph_downstream_continuation_fails"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_phase03_protocol(phase02: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(
        phase02.get("candidate_status_update", {}).get("candidate_id")
        or "cand.krk.box_shrink.family_2cc.post_box_continuation_overlay.v1"
    )
    diagnosis = str(phase02.get("diagnosis") or "")
    selected_move = str(phase02.get("selected_move") or "")
    selected_dtm = dict(phase02.get("selected_move_dtm", {}) or {})
    current_replay = dict(phase02.get("selected_move_current_graph_replay", {}) or {})
    protocol_enabled = diagnosis == EXPECTED_DIAGNOSIS
    status = (
        "candidate_local_plasticity_protocol_ready"
        if protocol_enabled
        else "blocked_until_phase02_downstream_gap_confirmed"
    )
    return {
        "schema_version": "stage7_2cc_phase03_plasticity_protocol.v1",
        "causal_status": "non_causal",
        "runtime_behavior_changed": False,
        "source_phase02_schema": phase02.get("schema_version"),
        "source_diagnosis": diagnosis,
        "structural_candidate_update": {
            "candidate_id": candidate_id,
            "promotion_status": status,
            "causal_status": "non_causal",
            "credit": 0.0,
            "diagnostic_label": (
                "expressive_but_untrained_multistep_continuation"
                if protocol_enabled
                else "phase02_not_ready_for_plasticity"
            ),
        },
        "bounded_scope": {
            "target_family": "state.2cc0b3e1033a",
            "target_skill": "krk.box_shrink",
            "parent_skill": "krk.post_box_shrink_continuation",
            "selected_visible_first_move": selected_move,
            "selected_move_tablebase_winning": bool(selected_dtm.get("forces_mate", False)),
            "selected_move_current_graph_result": current_replay.get("result"),
            "stage7_status": "local_valid_composition_quarantined",
        },
        "plasticity_budget": {
            "phase": "candidate_local_m3_warmup",
            "max_warmup_episodes": 32,
            "max_weight_delta_l2": 0.25,
            "max_weight_saturation_rate": 0.15,
            "allowed_update_scope": [
                "krk.post_box_shrink_continuation",
                "krk.stage7_post_box_learned_continuation",
                "candidate-local support/selection weights",
            ],
            "frozen_provider_versions": [
                "stage5_validated_v1",
                "stage6_overlay_v1",
            ],
            "disallowed_update_scope": [
                "stage0_basin validated provider weights",
                "fence_established validated provider weights",
                "edge_trap validated provider weights",
                "drive_to_edge validated overlay weights unless explicitly testing handoff",
                "global successor hub weights",
            ],
        },
        "training_evidence_allowed": [
            "CandidateMoveFrame visible current/move/post terms",
            "DTM-derived trajectory seed as offline supervision only",
            "legal-first replay outcomes as offline labels only",
            "current graph failure traces",
        ],
        "runtime_forbidden_terms": [
            "tablebase_lookup",
            "dtm_oracle_move_selection",
            "state_hash_exception",
            "legal_move_id_persistent_topology_node",
            "hidden_python_router",
        ],
        "evaluation_sequence": [
            {
                "phase": "default_off_equivalence",
                "acceptance": [
                    "same selected first move",
                    "same selected successor",
                    "same local result",
                    "same conversion result",
                    "same shadow candidate count",
                ],
            },
            {
                "phase": "frozen_candidate_model_probe",
                "acceptance": [
                    "candidate suggestion visible",
                    "source CandidateMoveFrame terms cited",
                    "direct_request false",
                    "no runtime DTM/tablebase/state-hash use",
                ],
            },
            {
                "phase": "bounded_candidate_local_m3_warmup",
                "acceptance": [
                    "target family conversion improves or failure remains classified",
                    "weight_delta_magnitude within budget",
                    "no protected provider mutation",
                    "no topology mutation during gameplay",
                ],
            },
            {
                "phase": "target_smoke",
                "acceptance": [
                    "2cc targeted replay improves or exposes post-first-move failure class",
                    "10-sample Stage 7 h40 does not regress",
                ],
            },
            {
                "phase": "guardrails_if_target_improves",
                "acceptance": [
                    "Stage 6 guardrail holds",
                    "Stage 5 guardrail holds",
                    "Stage 4 guardrail holds",
                    "M1-M4 preservation suite remains green",
                ],
            },
        ],
        "stop_conditions": [
            "default-off behavior differs",
            "candidate path needs hidden routing to win",
            "candidate updates protected providers",
            "guardrails regress",
            "candidate improves only through DTM/tablebase runtime terms",
            "candidate requires persistent topology nodes for legal moves",
        ],
        "next_action": (
            "run default-off frozen candidate model sandbox and bounded candidate-local warmup"
            if protocol_enabled
            else "rerun or repair Phase 2 before plasticity"
        ),
    }


def _write_md(payload: dict[str, Any], path: Path) -> None:
    update = payload["structural_candidate_update"]
    scope = payload["bounded_scope"]
    budget = payload["plasticity_budget"]
    lines = [
        "# Stage 7 2cc Phase 3 Plasticity Protocol",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Runtime behavior changed: `{payload['runtime_behavior_changed']}`",
        "",
        "## Candidate",
        "",
        f"Candidate: `{update['candidate_id']}`",
        f"Promotion status: `{update['promotion_status']}`",
        f"Diagnostic label: `{update['diagnostic_label']}`",
        "",
        "## Scope",
        "",
        f"Target family: `{scope['target_family']}`",
        f"Selected visible first move: `{scope['selected_visible_first_move']}`",
        f"Current graph result: `{scope['selected_move_current_graph_result']}`",
        "",
        "## Budget",
        "",
        f"Max warmup episodes: `{budget['max_warmup_episodes']}`",
        f"Max weight delta L2: `{budget['max_weight_delta_l2']}`",
        f"Max saturation rate: `{budget['max_weight_saturation_rate']}`",
        "",
        "## Next Action",
        "",
        payload["next_action"],
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase02", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = build_phase03_protocol(_load_json(args.phase02))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        _write_md(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
