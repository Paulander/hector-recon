#!/usr/bin/env python3
"""Train a narrow Stage 7 post-box continuation overlay learner.

This converts the offline DTM trajectory seed into ordinary baseline learner
actuators. DTM labels are used only offline to create transitions; the resulting
learner contains only sensor/actuator terminal deltas and can be compiled as an
opt-in overlay provider.
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Any

import chess
import numpy as np

from recon_lite_chess.training.krk_landmarks import RICH_FEATURE_NAMES, rich_feature_vector
from recon_lite_hector.learning.baseline import (
    ActuatorSpec,
    BaselineLearner,
    SensorSpec,
    Terminal,
    TerminalRole,
    TransitionData,
)
from train_baseline_krk_chain import update_learner_from_transitions


LABEL = "post_box_shrink_continuation"
SKILL_ID = "krk.post_box_shrink_continuation"
PROVIDER_VERSION = "stage7_post_box_continuation_overlay_v1"
PLAN_CAPSULE_ID = "krk.post_box_shrink_continuation"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _identity_sensors(*, stage: int, first_sensor_id: int) -> list[Terminal]:
    sensors: list[Terminal] = []
    feature_dim = len(RICH_FEATURE_NAMES)
    for idx, name in enumerate(RICH_FEATURE_NAMES):
        mask = np.zeros(feature_dim, dtype=bool)
        mask[idx] = True
        sensor = Terminal(
            id=first_sensor_id + idx,
            stage=stage,
            role=TerminalRole.SENSOR,
            sensor_spec=SensorSpec(
                feature_mask=mask,
                readout_type="identity",
                readout_params={"feature_name": name},
            ),
            xp=1.0,
            activations=100,
            cycles_alive=10,
            is_mature=True,
        )
        sensors.append(sensor)
    return sensors


def _transition_for_move(fen: str, move_uci: str, label: int, reward: float) -> TransitionData | None:
    board = chess.Board(fen)
    move = chess.Move.from_uci(move_uci)
    if move not in board.legal_moves:
        return None
    before = np.array(rich_feature_vector(board), dtype=np.float32)
    board.push(move)
    after = np.array(rich_feature_vector(board), dtype=np.float32)
    return TransitionData(v0=before, v1=after, label=int(label), action=move_uci, reward=float(reward))


def _transitions(seed: dict[str, Any], *, include_nonoptimal_winning_negatives: bool) -> list[TransitionData]:
    transitions: list[TransitionData] = []
    for trajectory in seed.get("trajectories") or []:
        if not isinstance(trajectory, dict):
            continue
        for step in trajectory.get("white_training_steps") or []:
            if not isinstance(step, dict):
                continue
            fen = str(step.get("fen") or "")
            for item in step.get("legal_move_labels") or []:
                if not isinstance(item, dict) or not item.get("move"):
                    continue
                label = int(item.get("label", 0) or 0)
                target_class = str(item.get("target_class") or "")
                if label == 0 and target_class == "winning_nonoptimal_move" and not include_nonoptimal_winning_negatives:
                    continue
                reward = 1.0 if label == 1 else -0.35
                if target_class == "non_winning_move":
                    reward = -1.0
                transition = _transition_for_move(fen, str(item["move"]), label, reward)
                if transition is not None:
                    transitions.append(transition)
    return transitions


def train_overlay_learner(
    *,
    trajectory_seed_path: Path,
    output_learner_path: Path,
    summary_path: Path,
    stage: int = 7,
    first_sensor_id: int = 7000,
    first_actuator_id: int = 9000,
    cycles: int = 3,
    top_k: int = 6,
    delta_eps: float = 0.03,
    max_actuators: int = 24,
    include_nonoptimal_winning_negatives: bool = True,
) -> dict[str, Any]:
    seed = _load_json(trajectory_seed_path)
    learner = BaselineLearner(
        feature_dim=len(RICH_FEATURE_NAMES),
        stage=stage,
        device="numpy",
    )
    learner.sensors = _identity_sensors(stage=stage, first_sensor_id=first_sensor_id)
    learner._next_sensor_id = first_sensor_id + len(learner.sensors)
    learner._next_actuator_id = first_actuator_id

    transitions = _transitions(
        seed,
        include_nonoptimal_winning_negatives=include_nonoptimal_winning_negatives,
    )
    if not transitions:
        raise ValueError("trajectory seed produced no transitions")

    cycle_stats = []
    protected_ids = {sensor.id for sensor in learner.sensors}
    for _ in range(max(1, cycles)):
        stats = update_learner_from_transitions(
            learner,
            transitions,
            max_actuators_per_stage=max_actuators,
            max_actuators_total=0,
            delta_eps=delta_eps,
            top_k=top_k,
            goal_sensor_ids=[sensor.id for sensor in learner.sensors],
            curriculum_label=LABEL,
            pruning_profile="frozen",
            protected_sensor_ids=protected_ids,
            prevent_cross_label_actuator_merge=True,
        )
        cycle_stats.append(stats)

    for actuator in learner.actuators:
        if getattr(actuator, "curriculum_label", None) == LABEL:
            actuator.stage = stage

    output_learner_path.parent.mkdir(parents=True, exist_ok=True)
    with output_learner_path.open("wb") as fh:
        pickle.dump(learner, fh)

    overlay_actuators = [
        actuator for actuator in learner.actuators if getattr(actuator, "curriculum_label", None) == LABEL
    ]
    summary = {
        "schema_version": "stage7_post_box_overlay_learner_training.v1",
        "causal_status": "offline_training_non_promoted",
        "trajectory_seed_source": str(trajectory_seed_path),
        "learner_output": str(output_learner_path),
        "target_label": LABEL,
        "target_skill": SKILL_ID,
        "provider_skill_id": SKILL_ID,
        "provider_version": PROVIDER_VERSION,
        "plan_capsule_id": PLAN_CAPSULE_ID,
        "provider_maturity": "candidate_high_plasticity",
        "plasticity_scope": "candidate_local",
        "can_m3_update": True,
        "can_m4_consolidate": False,
        "default_enabled": False,
        "promotion_status": "sandbox_candidate",
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
                "white_king_support_improves",
                "enemy_king_mobility_decreases",
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
        "trainable_internal_components": [
            "sensor_context_terms",
            "candidate_move_shape_terms",
            "post_move_terms",
            "trajectory_target_memory",
            "actuator_legs",
            "learned_scoring_head",
            "bounded_plan_ownership_trace",
            "exit_abort_monitoring",
        ],
        "stage": stage,
        "feature_set": "krk_rich_v1",
        "transition_count": len(transitions),
        "positive_transition_count": sum(1 for item in transitions if item.label == 1),
        "negative_transition_count": sum(1 for item in transitions if item.label == 0),
        "sensor_count": len(learner.sensors),
        "overlay_actuator_count": len(overlay_actuators),
        "actuator_ids": [int(actuator.id) for actuator in overlay_actuators],
        "cycle_stats": cycle_stats,
        "constraints": [
            "offline_training_only",
            "do_not_use_dtm_or_tablebase_at_runtime",
            "do_not_enable_by_default",
            "do_not_promote_without_guardrails",
            "prevent_cross_label_actuator_merge",
            "freeze_validated_base_providers",
            "disable_m4_consolidation_initially",
        ],
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Train Stage 7 post-box overlay learner")
    parser.add_argument("--trajectory-seed", type=Path, required=True)
    parser.add_argument("--output-learner", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--delta-eps", type=float, default=0.03)
    parser.add_argument("--max-actuators", type=int, default=24)
    parser.add_argument("--first-sensor-id", type=int, default=7000)
    parser.add_argument("--first-actuator-id", type=int, default=9000)
    parser.add_argument("--exclude-nonoptimal-winning-negatives", action="store_true")
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    summary = train_overlay_learner(
        trajectory_seed_path=args.trajectory_seed,
        output_learner_path=args.output_learner,
        summary_path=args.summary_output,
        first_sensor_id=args.first_sensor_id,
        first_actuator_id=args.first_actuator_id,
        cycles=args.cycles,
        top_k=args.top_k,
        delta_eps=args.delta_eps,
        max_actuators=args.max_actuators,
        include_nonoptimal_winning_negatives=not args.exclude_nonoptimal_winning_negatives,
    )
    if not args.no_json_stdout:
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
