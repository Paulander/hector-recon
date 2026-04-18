"""
Stage-0/1 chained baseline training for KRK.

Stage 0: Learn sensors/actuators from mate-in-1 transitions.
Stage 1: Backchain using goal memories from Stage 0 (move closer to mate-in-1 goals).
"""

import argparse
import json
import pickle
import random
from pathlib import Path
from typing import Dict, List, Any

import chess
import numpy as np
try:
    import torch
except ImportError:
    torch = None

from recon_lite_hector.learning.baseline import (
    BaselineLearner, Terminal, TerminalRole,
    compute_sensor_xp, should_promote_sensor,
    extract_actuator_patterns, find_similar_actuator, enforce_actuator_cap,
    enforce_actuator_cap_total,
    TransitionData, apply_sensor,
    SensorSpec,
)
from recon_lite_chess.baseline_teacher import KRKTeacher, generate_krk_mate_in_1_position, can_deliver_mate
from recon_lite_chess.training.krk_landmarks import (
    select_stage_position,
    specs_through,
    worst_reply_reward,
)


PRUNING_PROFILES = {"explore", "consolidate", "frozen"}


def export_learner_cycle_snapshot(
    learner: BaselineLearner,
    output_dir: Path,
    *,
    stage_name: str,
    cycle: int,
    transitions: List[TransitionData],
    stats: Dict[str, Any],
) -> Path:
    """Write a lightweight learner topology snapshot for growth animation."""
    nodes: Dict[str, Any] = {}
    edges: Dict[str, Any] = {}

    mature = learner.get_mature_sensors()
    mature_by_id = {s.id: s for s in mature}
    mature_by_index = {i: s for i, s in enumerate(mature)}

    for sensor in learner.sensors:
        nodes[f"sensor_{sensor.id}"] = {
            "id": f"sensor_{sensor.id}",
            "type": "TERMINAL",
            "group": "sensor" if sensor.is_mature else "candidate_sensor",
            "meta": {
                "stage": int(sensor.stage),
                "xp": float(sensor.xp),
                "is_mature": bool(sensor.is_mature),
                "activations": int(sensor.activations),
                "cycles_alive": int(sensor.cycles_alive),
                "readout_type": sensor.sensor_spec.readout_type,
                "feature_count": int(np.sum(sensor.sensor_spec.feature_mask)),
            },
        }

    for actuator in learner.actuators:
        act_id = f"actuator_{actuator.id}"
        nodes[act_id] = {
            "id": act_id,
            "type": "TERMINAL",
            "group": "actuator",
            "meta": {
                "stage": int(actuator.stage),
                "curriculum_label": getattr(actuator, "curriculum_label", None),
                "xp": float(actuator.xp),
                "sensor_count": int(len(actuator.actuator_spec.sensor_indices)),
                "goal_delta_norm": float(np.linalg.norm(actuator.actuator_spec.goal_delta)),
                "activations": int(actuator.activations),
                "cycles_alive": int(actuator.cycles_alive),
            },
        }
        for raw_idx in actuator.actuator_spec.sensor_indices:
            sensor = mature_by_id.get(int(raw_idx)) or mature_by_index.get(int(raw_idx))
            if sensor is None:
                continue
            edge_key = f"sensor_{sensor.id}->{act_id}:DELTA"
            edges[edge_key] = {
                "src": f"sensor_{sensor.id}",
                "dst": act_id,
                "type": "DELTA",
                "weight": 1.0 + max(0.0, float(actuator.xp)),
            }

    total_transitions = len(transitions)
    positive_transitions = sum(1 for t in transitions if t.label == 1)
    avg_reward = float(np.mean([t.reward for t in transitions])) if transitions else 0.0
    snapshot = {
        "stage_name": stage_name,
        "cycle": cycle,
        "nodes": nodes,
        "edges": edges,
        "metrics": {
            "sensors": len(learner.sensors),
            "mature_sensors": len(mature),
            "actuators": len(learner.actuators),
            "goal_memories": len(learner.goal_memories),
            "positive_transitions": positive_transitions,
            "total_transitions": total_transitions,
            "positive_rate": positive_transitions / total_transitions if total_transitions else 0.0,
            "avg_transition_reward": avg_reward,
            **stats,
        },
    }

    stage_dir = output_dir / "topology_snapshots" / stage_name
    stage_dir.mkdir(parents=True, exist_ok=True)
    path = stage_dir / f"cycle_{cycle:04d}.json"
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return path


def generate_random_krk_position() -> chess.Board:
    """Generate a random legal KRK position (white to move, no check)."""
    squares = list(chess.SQUARES)
    while True:
        wk, bk, wr = random.sample(squares, 3)
        board = chess.Board(None)
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        board.set_piece_at(wr, chess.Piece(chess.ROOK, chess.WHITE))
        board.turn = chess.WHITE
        if chess.square_distance(wk, bk) <= 1:
            continue
        if not board.is_valid():
            continue
        if board.is_check():
            continue
        return board


def is_forced_mate_in_2(board: chess.Board) -> bool:
    """Return True if side-to-move (white) has a move that forces mate-in-1 next ply."""
    if board.turn != chess.WHITE:
        return False
    if can_deliver_mate(board):
        # Exclude mate-in-1 from Stage-1 generation.
        return False

    for move in board.legal_moves:
        b1 = board.copy()
        b1.push(move)
        if b1.is_checkmate():
            # Still mate-in-1 line, not Stage-1 target.
            continue
        replies = list(b1.legal_moves)
        if not replies:
            continue

        # Forced: after every black reply, white can mate in 1.
        forced = True
        for reply in replies:
            b2 = b1.copy()
            b2.push(reply)
            if not can_deliver_mate(b2):
                forced = False
                break
        if forced:
            return True
    return False


def generate_stage1_mate_in_2_position(max_tries: int = 5000) -> chess.Board:
    """Generate a legal KRK position that is forced mate-in-2 for white."""
    for _ in range(max_tries):
        b = generate_random_krk_position()
        if is_forced_mate_in_2(b):
            return b
    raise RuntimeError(f"Could not generate forced mate-in-2 after {max_tries} attempts")


def enemy_corner_bucket(board: chess.Board) -> int | None:
    """Return enemy king square if in a corner, else None."""
    bk = board.king(chess.BLACK)
    if bk is None:
        return None
    if bk in (chess.A1, chess.A8, chess.H1, chess.H8):
        return bk
    return None


def collect_goal_memories(learner: BaselineLearner, v0: np.ndarray) -> Dict[int, float] | None:
    """Build a sparse goal memory keyed by sensor id."""
    mature = learner.get_mature_sensors()
    if not mature:
        return None
    goal = {}
    for s in mature:
        goal[s.id] = apply_sensor(s, v0)
    return goal


def get_goal_feature_index(teacher: KRKTeacher) -> int:
    """Return the goal feature index (is_checkmate) from the teacher if available."""
    return int(getattr(teacher, "goal_feature_index", 13))


def seed_goal_sensor(learner: BaselineLearner, goal_feature_idx: int) -> None:
    """Seed a sensor that reads only the goal bit (generic goal template)."""
    mask = np.zeros(learner.feature_dim, dtype=bool)
    if 0 <= goal_feature_idx < learner.feature_dim:
        mask[goal_feature_idx] = True
    spec = SensorSpec(feature_mask=mask, readout_type="identity")
    sensor = Terminal(
        id=learner._next_sensor_id,
        stage=learner.stage,
        role=TerminalRole.SENSOR,
        sensor_spec=spec,
    )
    learner._next_sensor_id += 1
    learner.sensors.append(sensor)


def goal_signal_sensor_ids(learner: BaselineLearner, goal_feature_idx: int) -> List[int]:
    """Return sensor IDs that include the goal feature in their mask."""
    ids: List[int] = []
    for s in learner.sensors:
        spec = s.sensor_spec
        if spec is None:
            continue
        mask = spec.feature_mask
        if mask is not None and len(mask) > goal_feature_idx and bool(mask[goal_feature_idx]):
            ids.append(s.id)
    return ids


def compute_sensor_vectors_batch(learner: BaselineLearner, v_batch: Any, sensor_ids: List[int]) -> Any:
    """Compute sensor vectors for a batch of feature vectors in a fixed id order."""
    if not sensor_ids:
        batch_len = len(v_batch)
        if learner.backend.use_torch:
            return torch.zeros((batch_len, 0), device=learner.backend.device)
        return np.zeros((batch_len, 0), dtype=np.float32)

    outputs = learner.batch_apply_sensors(v_batch)
    
    # results[i] = [s_id_0_output, s_id_1_output, ...]
    matrices = []
    for sid in sensor_ids:
        if sid in outputs:
            matrices.append(outputs[sid])
        else:
            # Fallback for unknown IDs (shouldn't happen)
            if learner.backend.use_torch:
                matrices.append(torch.zeros(outputs[next(iter(outputs))].shape[0]).to(learner.backend.device))
            else:
                matrices.append(np.zeros(len(next(iter(outputs.values())))))
    
    if learner.backend.use_torch:
        return torch.stack(matrices, dim=1)
    return np.stack(matrices, axis=1)


def label_transitions_by_goal(
    learner: BaselineLearner,
    board: chess.Board,
    goal_vectors: List[np.ndarray],
    sensor_ids: List[int],
    teacher: KRKTeacher | None = None,
    eps: float = 1e-3,
    lookahead_black: bool = True,
    opponent_mode: str = "max",
) -> List[TransitionData]:
    """Label transitions as positive if they move closer to any goal memory.
    
    Optimized: Batches all boards (v1 and v2) for a single GPU pass.
    """
    if not sensor_ids or not goal_vectors:
        return []

    teacher = teacher or KRKTeacher()
    v0 = teacher.features(board)
    
    # 1. Collect all board feature vectors for current move alternatives
    moves = list(board.legal_moves)
    v1_list = []
    v2_map = {} # move_idx -> list of v2s
    
    all_v_to_compute = [v0]
    
    for i, move in enumerate(moves):
        b1 = board.copy()
        b1.push(move)
        v1 = teacher.features(b1)
        v1_list.append(v1)
        all_v_to_compute.append(v1)
        
        if lookahead_black:
            v2_list = []
            for reply in b1.legal_moves:
                b2 = b1.copy()
                b2.push(reply)
                v2 = teacher.features(b2)
                v2_list.append(v2)
                all_v_to_compute.append(v2)
            v2_map[i] = v2_list

    # 2. GPU Batch Compute for all vectors
    all_v_batch = np.stack(all_v_to_compute)
    s_vectors = compute_sensor_vectors_batch(learner, all_v_batch, sensor_ids)
    
    # Bring to CPU for distance logic (which is branching)
    if learner.backend.use_torch:
        s_vectors = s_vectors.detach().cpu().numpy()
        goal_vectors_np = [g if isinstance(g, np.ndarray) else g.detach().cpu().numpy() for g in goal_vectors]
    else:
        goal_vectors_np = goal_vectors

    # 3. Distance scoring (align with runtime: weighted + normalized terminal distance)
    sensor_by_id = {s.id: s for s in learner.sensors}
    weights = np.array(
        [
            1.0 + max(0.0, float(getattr(sensor_by_id.get(sid), "xp", 0.0)))
            for sid in sensor_ids
        ],
        dtype=np.float32,
    )

    def weighted_goal_dist(cur: np.ndarray, goal: np.ndarray) -> float:
        """Runtime-aligned weighted normalized L2 over full sensor vectors.

        No min-overlap gate is required here because training vectors are dense
        and always computed on the same fixed `sensor_ids` basis.
        """
        if cur.shape != goal.shape:
            return float("inf")
        cur = cur.astype(np.float32, copy=False)
        goal = goal.astype(np.float32, copy=False)
        cur = cur / (np.sqrt(np.sum(weights * (cur ** 2))) + 1e-6)
        goal = goal / (np.sqrt(np.sum(weights * (goal ** 2))) + 1e-6)
        diff = cur - goal
        return float(np.sqrt(np.sum(weights * (diff ** 2))))

    def get_min_dist(s_vec):
        if not goal_vectors_np:
            return float("inf")
        dists = [weighted_goal_dist(s_vec, g) for g in goal_vectors_np]
        return min(dists) if dists else float("inf")

    cursor = 0
    s0 = s_vectors[cursor]
    d0 = get_min_dist(s0)
    cursor += 1
    
    transitions = []
    for i, move in enumerate(moves):
        s1 = s_vectors[cursor]
        v1 = all_v_to_compute[cursor]
        cursor += 1
        
        if lookahead_black:
            replies = v2_map.get(i, [])
            if replies:
                d1_candidates = []
                for _ in range(len(replies)):
                    s2 = s_vectors[cursor]
                    d1_candidates.append(get_min_dist(s2))
                    cursor += 1
                d1 = max(d1_candidates) if opponent_mode == "max" else min(d1_candidates)
            else:
                d1 = get_min_dist(s1)
        else:
            d1 = get_min_dist(s1)
            
        reward = d0 - d1
        label = 1 if reward > eps else 0
        transitions.append(TransitionData(v0=v0, v1=v1, label=label, action=move, reward=reward))
        
    return transitions


def label_transitions_by_landmark(
    teacher: KRKTeacher,
    board: chess.Board,
    label: str,
    eps: float = 1e-3,
    lookahead_black: bool = True,
) -> List[TransitionData]:
    """Label legal moves by explicit KRK landmark progress."""
    transitions: List[TransitionData] = []
    v0 = teacher.features(board)
    for move in board.legal_moves:
        b1 = board.copy()
        b1.push(move)
        v1 = teacher.features(b1)
        reward = worst_reply_reward(board, move, label, use_black_reply=lookahead_black)
        transitions.append(
            TransitionData(
                v0=v0,
                v1=v1,
                label=1 if reward > eps else 0,
                action=move,
                reward=reward,
            )
        )
    return transitions


def add_goal_memory_from_vector(
    learner: BaselineLearner,
    teacher: KRKTeacher,
    feature_vector: np.ndarray,
    label: str,
    min_mature_for_goals: int,
    current_goal_sensor_ids: List[int] | None = None,
) -> List[int] | None:
    """Record a stage-specific goal memory in the current mature sensor basis."""
    if len(learner.get_mature_sensors()) < min_mature_for_goals:
        return current_goal_sensor_ids
    sensor_ids = current_goal_sensor_ids
    if sensor_ids is None:
        sensor_ids = [s.id for s in learner.get_mature_sensors()]
    if not sensor_ids:
        return sensor_ids
    s0 = compute_sensor_vectors_batch(learner, feature_vector[None, :], sensor_ids)[0]
    learner.add_goal_memory(s0, label=label, sensor_ids=sensor_ids)
    return sensor_ids


def protected_goal_sensor_ids(learner: BaselineLearner, allow_prune_foundation: bool = False) -> set[int]:
    """Return sensor IDs that should not be pruned because goal memories depend on them."""
    if allow_prune_foundation:
        return set()
    protected: set[int] = set()
    for goal in learner.goal_memories:
        if getattr(goal, "sensor_ids", None):
            protected.update(int(sid) for sid in goal.sensor_ids)
    return protected


def pruning_profile_for_cycle(cycle: int, total_cycles: int, has_goal_signal: bool) -> str:
    """Default curriculum pruning schedule."""
    if total_cycles <= 0:
        return "explore"
    if not has_goal_signal:
        return "explore"
    return "explore" if cycle < int(total_cycles * 0.3) else "consolidate"


def update_learner_from_transitions(
    learner: BaselineLearner,
    transitions: List[TransitionData],
    max_actuators_per_stage: int,
    max_actuators_total: int,
    delta_eps: float,
    top_k: int,
    goal_sensor_ids: List[int] | None = None,
    curriculum_label: str | None = None,
    pruning_profile: str = "explore",
    protected_sensor_ids: set[int] | None = None,
) -> Dict[str, Any]:
    """Shared update logic for sensors/actuators."""
    if not transitions:
        counts = {
            "sensors": len(learner.sensors),
            "actuators": len(learner.actuators),
        }
        return {
            "newly_promoted": [],
            "pruned_count": 0,
            "newly_created_actuators": 0,
            "pruned_sensor_ids": [],
            "pruned_actuator_ids": [],
            "merged_actuator_ids": [],
            "candidate_actuator_count": 0,
            "pre_prune_counts": counts,
            "post_prune_counts": counts,
            "pruning_profile": pruning_profile,
        }
    if pruning_profile not in PRUNING_PROFILES:
        raise ValueError(f"Unknown pruning_profile: {pruning_profile}")
    protected_sensor_ids = protected_sensor_ids or set()

    # Prepare batches
    v0_batch = [t.v0 for t in transitions]
    v1_batch = [t.v1 for t in transitions]
    labels = np.array([t.label for t in transitions])
    
    # Compute weights from dense rewards
    weights = []
    for t in transitions:
        if t.label == 1:
            w = min(max(t.reward, 0.0), 1.0) if t.reward > 0 else 1.0
        else:
            w = min(max(-t.reward, 0.0), 1.0) if t.reward < 0 else 1.0
        weights.append(w)
    weights = learner.backend.array(weights, dtype=torch.float32 if learner.backend.use_torch else np.float32)

    # Batch apply all sensors
    outputs0 = learner.batch_apply_sensors(v0_batch)
    outputs1 = learner.batch_apply_sensors(v1_batch)

    # Prepare masks/weights on correct device
    if learner.backend.use_torch:
        labels_t = torch.as_tensor(labels).to(learner.backend.device)
        pos_mask = (labels_t == 1)
        neg_mask = (labels_t == 0)
        weights_t = torch.as_tensor(weights).to(learner.backend.device)
    else:
        pos_mask = (labels == 1)
        neg_mask = (labels == 0)
        weights_t = np.array(weights)

    # Update sensor XP
    for sensor in learner.sensors:
        # Apply weights to deltas
        delta_t_raw = outputs1[sensor.id] - outputs0[sensor.id]
        delta_t_weighted = delta_t_raw * weights_t
        
        delta_pos = delta_t_weighted[pos_mask]
        delta_neg = delta_t_weighted[neg_mask]
        
        xp = compute_sensor_xp(
            sensor,
            delta_pos,
            delta_neg,
            backend=learner.backend
        )
        sensor.xp = xp
        sensor.activations += len(transitions)
        sensor.cycles_alive += 1
        
        # Track good/bad hits for stats
        if delta_pos.shape[0] > 0:
            sensor.good_hits += 1
        if delta_neg.shape[0] > 0:
            sensor.bad_hits += 1

    # Promote/prune
    newly_promoted = []
    for sensor in learner.sensors:
        if should_promote_sensor(sensor):
            sensor.is_mature = True
            newly_promoted.append(sensor.id)

    initial_count = len(learner.sensors)
    pre_prune_counts = {
        "sensors": len(learner.sensors),
        "actuators": len(learner.actuators),
    }
    if pruning_profile == "frozen":
        xp_prune_threshold = -float("inf")
        min_cycles_before_prune = 10**9
    elif pruning_profile == "consolidate":
        xp_prune_threshold = 0.25
        min_cycles_before_prune = 3
    else:
        xp_prune_threshold = 0.05
        min_cycles_before_prune = 5

    pruned_sensor_ids = [
        s.id
        for s in learner.sensors
        if (
            s.id not in protected_sensor_ids
            and not s.is_mature
            and s.xp <= xp_prune_threshold
            and s.cycles_alive >= min_cycles_before_prune
        )
    ]
    learner.sensors = [
        s for s in learner.sensors
        if s.id not in set(pruned_sensor_ids)
    ]
    pruned_count = initial_count - len(learner.sensors)

    # Actuator extraction from positives
    mature_sensors = learner.get_mature_sensors()
    newly_created_actuators = 0
    merged_actuator_ids: List[int] = []
    candidate_actuator_count = 0
    pruned_actuator_ids: List[int] = []
    if len(mature_sensors) >= 3:
        positive_trans = [t for t in transitions if t.label == 1]
        if positive_trans:
            actuator_specs = extract_actuator_patterns(
                positive_trans,
                mature_sensors,
                eps=0.1,
                top_k=top_k,
                backend=learner.backend,
                goal_sensor_ids=goal_sensor_ids,
            )
            candidate_actuator_count = len(actuator_specs)
            for spec in actuator_specs:
                existing = find_similar_actuator(
                    learner.actuators,
                    spec,
                    similarity_threshold=0.9,
                    delta_eps=delta_eps,
                )
                if existing:
                    existing.actuator_spec.goal_delta = (
                        0.8 * existing.actuator_spec.goal_delta +
                        0.2 * spec.goal_delta
                    )
                    existing.xp += 0.1
                    existing.activations += 1
                    if curriculum_label is not None and not getattr(existing, "curriculum_label", None):
                        existing.curriculum_label = curriculum_label
                    merged_actuator_ids.append(existing.id)
                else:
                    actuator = Terminal(
                        id=learner._next_actuator_id,
                        stage=learner.stage,
                        role=TerminalRole.ACTUATOR,
                        actuator_spec=spec
                    )
                    actuator.xp = float(np.mean(np.abs(spec.goal_delta)))
                    actuator.curriculum_label = curriculum_label
                    learner._next_actuator_id += 1
                    learner.actuators.append(actuator)
                    newly_created_actuators += 1

            before_cap_ids = {a.id for a in learner.actuators}
            learner.actuators, pruned_actuators = enforce_actuator_cap(
                learner.actuators,
                stage=learner.stage,
                max_actuators=max_actuators_per_stage,
            )
            after_stage_cap_ids = {a.id for a in learner.actuators}
            learner.actuators, _ = enforce_actuator_cap_total(
                learner.actuators,
                max_total=max_actuators_total,
            )
            after_total_cap_ids = {a.id for a in learner.actuators}
            pruned_actuator_ids = sorted(
                (before_cap_ids - after_stage_cap_ids)
                | (after_stage_cap_ids - after_total_cap_ids)
            )

    return {
        "newly_promoted": newly_promoted,
        "pruned_count": pruned_count,
        "newly_created_actuators": newly_created_actuators,
        "pruned_sensor_ids": pruned_sensor_ids,
        "pruned_actuator_ids": pruned_actuator_ids,
        "merged_actuator_ids": sorted(set(merged_actuator_ids)),
        "candidate_actuator_count": candidate_actuator_count,
        "pre_prune_counts": pre_prune_counts,
        "post_prune_counts": {
            "sensors": len(learner.sensors),
            "actuators": len(learner.actuators),
        },
        "pruning_profile": pruning_profile,
    }

def main() -> None:
    parser = argparse.ArgumentParser(description="Stage-0/1 chained baseline training for KRK")
    parser.add_argument("--load-learner", type=Path, help="Path to existing learner pickle to start from")
    parser.add_argument("--stage0-cycles", type=int, default=50)
    parser.add_argument("--stage1-cycles", type=int, default=50)
    parser.add_argument("--max-curriculum-stage", type=int, default=1,
                        help="Run explicit KRK landmark stages after Stage 1 up to this index")
    parser.add_argument("--landmark-cycles", type=int, default=10,
                        help="Cycles per explicit KRK landmark stage when --max-curriculum-stage > 1")
    parser.add_argument("--samples-per-cycle", type=int, default=100)
    parser.add_argument("--initial-sensors", type=int, default=20)
    parser.add_argument("--spawn-interval", type=int, default=10)
    parser.add_argument("--sensors-per-spawn", type=int, default=5)
    parser.add_argument("--output-dir", type=Path, default=Path("snapshots/baseline_krk_chain"))
    parser.add_argument("--save-learner", type=Path, default=Path("snapshots/baseline_krk_chain/final_learner.pkl"))
    parser.add_argument("--goal-eps", type=float, default=0.08)
    parser.add_argument("--max-goals", type=int, default=200)
    parser.add_argument("--min-mature-for-goals", type=int, default=8)
    parser.add_argument("--max-actuators-per-stage", type=int, default=30)
    parser.add_argument("--max-actuators-total", type=int, default=0)
    parser.add_argument("--delta-eps", type=float, default=0.22)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--stage1-reward-scale", type=float, default=1.0,
                        help="Scale factor applied to Stage-1 dense rewards before XP updates")
    parser.add_argument("--feature-set", choices=["legacy", "krk_rich_v1"], default="legacy",
                        help="Feature vector used by baseline sensors")
    parser.add_argument("--allow-prune-foundation", action="store_true", default=False,
                        help="Allow pruning sensors referenced by active goal memories")
    parser.add_argument("--device", type=str, default="auto", help="Device (cpu, cuda, auto, numpy)")
    parser.add_argument("--batch-size", type=int, default=256, help="Batch size for sensor application")
    parser.add_argument("--seed", type=int, default=None, help="Optional RNG seed for replayable runs")
    parser.add_argument("--snapshot-every", type=int, default=1,
                        help="Write lightweight topology snapshot every N cycles (0 disables)")
    parser.add_argument("--goal-feature-idx", type=int, default=None,
                        help="Index of the goal feature bit (e.g. is_checkmate)")
    parser.add_argument("--seed-goal-sensor", action="store_true", default=True,
                        help="Seed a goal sensor template (on by default)")
    parser.add_argument("--no-seed-goal-sensor", action="store_false", dest="seed_goal_sensor",
                        help="Disable seeding the goal sensor template")
    parser.add_argument("--stage0-balance-corners", action="store_true", default=False,
                        help="Balance Stage 0 samples across corners for mate-in-1 positions")
    parser.add_argument(
        "--stage1-position-mode",
        type=str,
        default="mate_in_2",
        choices=["mate_in_2", "random", "hybrid"],
        help="Stage-1 sampling source: forced mate-in-2, random KRK, or hybrid mix",
    )
    parser.add_argument(
        "--stage1-hybrid-random-ratio",
        type=float,
        default=0.2,
        help="When stage1-position-mode=hybrid, probability of sampling random KRK",
    )
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)
        if torch is not None:
            torch.manual_seed(args.seed)

    teacher = KRKTeacher(feature_set=args.feature_set)
    
    if args.load_learner and args.load_learner.exists():
        print(f"Loading existing learner from: {args.load_learner}")
        with open(args.load_learner, 'rb') as f:
            learner = pickle.load(f)
        if getattr(learner, "feature_dim", teacher.feature_dim) != teacher.feature_dim:
            raise ValueError(
                "Loaded learner feature dimension does not match selected feature set: "
                f"learner={getattr(learner, 'feature_dim', None)} "
                f"teacher={teacher.feature_dim} feature_set={args.feature_set}"
            )
        # Update device if requested
        if args.device != learner.device:
            from recon_lite_hector.learning.baseline import ComputeBackend
            learner.device = args.device
            learner.backend = ComputeBackend(device=args.device)
        print(f"  Loaded {len(learner.sensors)} sensors, {len(learner.actuators)} actuators")
    else:
        learner = BaselineLearner(
            feature_dim=teacher.feature_dim,
            stage=0,
            goal_eps=args.goal_eps,
            max_goals=args.max_goals,
            device=args.device,
        )
        for _ in range(args.initial_sensors):
            learner.sensors.append(learner.spawn_sensor())
        print(f"Created new learner on {args.device}")
    learner.feature_set = args.feature_set
    learner.feature_names = tuple(getattr(teacher, "feature_names", ()))
    learner.goal_feature_index = int(getattr(teacher, "goal_feature_index", 13))

    goal_feature_idx = args.goal_feature_idx if args.goal_feature_idx is not None else get_goal_feature_index(teacher)
    if args.seed_goal_sensor:
        # Seed if not already present
        if not goal_signal_sensor_ids(learner, goal_feature_idx):
            seed_goal_sensor(learner, goal_feature_idx)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    goal_sensor_ids: List[int] | None = None

    if learner.stage == 0 and args.stage0_cycles > 0:
        print("=" * 70)
        print("Stage 0: Mate-in-1")
        print("=" * 70)
        
        for cycle in range(args.stage0_cycles):
            transitions = []
            corner_targets = []
            if args.stage0_balance_corners:
                per_corner = max(1, args.samples_per_cycle // 4)
                corner_targets = (
                    [chess.A1] * per_corner
                    + [chess.A8] * per_corner
                    + [chess.H1] * per_corner
                    + [chess.H8] * per_corner
                )
                random.shuffle(corner_targets)
            for _ in range(args.samples_per_cycle):
                b0 = None
                if corner_targets:
                    target = corner_targets.pop()
                    try:
                        b0 = generate_krk_mate_in_1_position(target_corner=target)
                    except RuntimeError:
                        b0 = None
                if b0 is None:
                    b0 = generate_krk_mate_in_1_position()
                transitions.extend(teacher.label_transitions(b0))
                # Store goal prototypes only after enough mature sensors
                if len(learner.get_mature_sensors()) >= args.min_mature_for_goals:
                    if goal_sensor_ids is None:
                        goal_sensor_ids = [s.id for s in learner.get_mature_sensors()]
                    v0 = teacher.features(b0)
                    # compute_sensor_vectors_batch returns [Batch, Sensors], we only need first row
                    s0 = compute_sensor_vectors_batch(learner, v0[None, :], goal_sensor_ids)[0]
                    learner.add_goal_memory(
                        s0,
                        label="mate_in_1",
                        sensor_ids=goal_sensor_ids,
                    )

            stats = update_learner_from_transitions(
                learner,
                transitions,
                max_actuators_per_stage=args.max_actuators_per_stage,
                max_actuators_total=args.max_actuators_total,
                delta_eps=args.delta_eps,
                top_k=args.top_k,
                goal_sensor_ids=goal_signal_sensor_ids(learner, goal_feature_idx),
                curriculum_label="mate_in_1",
                pruning_profile=pruning_profile_for_cycle(
                    cycle,
                    args.stage0_cycles,
                    bool(learner.goal_memories),
                ),
                protected_sensor_ids=protected_goal_sensor_ids(
                    learner,
                    allow_prune_foundation=args.allow_prune_foundation,
                ),
            )

            if args.snapshot_every and cycle % args.snapshot_every == 0:
                export_learner_cycle_snapshot(
                    learner,
                    args.output_dir,
                    stage_name="stage0_mate_in_1",
                    cycle=cycle,
                    transitions=transitions,
                    stats=stats,
                )

            if cycle % 10 == 0 or stats["newly_promoted"] or stats["newly_created_actuators"]:
                mature = len(learner.get_mature_sensors())
                print(f"Cycle {cycle:3d}: sensors={len(learner.sensors)} (mature={mature}) "
                      f"actuators={len(learner.actuators)} goal_prototypes={len(learner.goal_memories)}")

            if cycle % args.spawn_interval == 0 and cycle > 0:
                for _ in range(args.sensors_per_spawn):
                    learner.sensors.append(learner.spawn_sensor())
    else:
        print(f"Skipping Stage 0 (Learner stage: {learner.stage}, Cycles requested: {args.stage0_cycles})")

    print("=" * 70)
    print("Stage 1: Backchain to Mate-in-1 goals")
    print("=" * 70)
    learner.stage = 1
    if goal_sensor_ids is None:
        goal_sensor_ids = [s.id for s in learner.get_mature_sensors()]

    usable_goal_memories = [
        g for g in learner.goal_memories
        if g.label == "mate_in_1" and goal_sensor_ids and g.s0.shape == (len(goal_sensor_ids),)
    ]
    if args.stage1_cycles > 0 and (not goal_sensor_ids or not usable_goal_memories):
        print(
            "Skipping Stage 1: Stage 0 did not produce mature sensors and mate_in_1 "
            "goal prototypes. Increase --stage0-cycles/--samples-per-cycle or lower "
            "--min-mature-for-goals for exploratory runs."
        )
        args.stage1_cycles = 0

    for cycle in range(args.stage1_cycles):
        transitions = []
        stage1_gen_fallbacks = 0
        for _ in range(args.samples_per_cycle):
            if args.stage1_position_mode == "random":
                b0 = generate_random_krk_position()
            elif args.stage1_position_mode == "hybrid":
                if random.random() < args.stage1_hybrid_random_ratio:
                    b0 = generate_random_krk_position()
                else:
                    try:
                        b0 = generate_stage1_mate_in_2_position()
                    except RuntimeError:
                        stage1_gen_fallbacks += 1
                        b0 = generate_random_krk_position()
            else:
                # Default: curated Stage-1 should be mate-in-2 and close to Stage-0 basin.
                try:
                    b0 = generate_stage1_mate_in_2_position()
                except RuntimeError:
                    stage1_gen_fallbacks += 1
                    b0 = generate_random_krk_position()
            goal_vectors = [
                g.s0 for g in learner.goal_memories
                if g.label == "mate_in_1" and g.s0.shape == (len(goal_sensor_ids),)
            ]
            stage_transitions = label_transitions_by_goal(
                learner,
                b0,
                goal_vectors,
                goal_sensor_ids,
                teacher=teacher,
                lookahead_black=True,
                opponent_mode="max",
            )
            if args.stage1_reward_scale != 1.0:
                for t in stage_transitions:
                    t.reward *= float(args.stage1_reward_scale)
            transitions.extend(stage_transitions)

        stage1_goal_sensor_ids: List[int] | None = None
        for t in (t for t in transitions if t.label == 1):
            stage1_goal_sensor_ids = add_goal_memory_from_vector(
                learner,
                teacher,
                t.v1,
                label="stage0_basin",
                min_mature_for_goals=args.min_mature_for_goals,
                current_goal_sensor_ids=stage1_goal_sensor_ids,
            )

        stats = update_learner_from_transitions(
            learner,
            transitions,
            max_actuators_per_stage=args.max_actuators_per_stage,
            max_actuators_total=args.max_actuators_total,
            delta_eps=args.delta_eps,
            top_k=args.top_k,
            goal_sensor_ids=goal_signal_sensor_ids(learner, goal_feature_idx),
            curriculum_label="stage0_basin",
            pruning_profile=pruning_profile_for_cycle(
                cycle,
                args.stage1_cycles,
                any(g.label == "stage0_basin" for g in learner.goal_memories),
            ),
            protected_sensor_ids=protected_goal_sensor_ids(
                learner,
                allow_prune_foundation=args.allow_prune_foundation,
            ),
        )

        if args.snapshot_every and cycle % args.snapshot_every == 0:
            export_learner_cycle_snapshot(
                learner,
                args.output_dir,
                stage_name="stage1_backchain",
                cycle=cycle,
                transitions=transitions,
                stats=stats,
            )

        if cycle % 10 == 0 or stats["newly_promoted"] or stats["newly_created_actuators"]:
            mature = len(learner.get_mature_sensors())
            print(f"Cycle {cycle:3d}: sensors={len(learner.sensors)} (mature={mature}) "
                  f"actuators={len(learner.actuators)} goal_prototypes={len(learner.goal_memories)}")
            if stage1_gen_fallbacks:
                print(f"  Stage-1 generation fallbacks to random KRK: {stage1_gen_fallbacks}")

        if cycle % args.spawn_interval == 0 and cycle > 0:
            for _ in range(args.sensors_per_spawn):
                learner.sensors.append(learner.spawn_sensor())

    landmark_specs = specs_through(args.max_curriculum_stage)
    for spec in landmark_specs:
        print("=" * 70)
        print(f"Stage {spec.stage_index}: {spec.label}")
        print("=" * 70)
        learner.stage = spec.stage_index
        stage_goal_sensor_ids: List[int] | None = None

        for cycle in range(args.landmark_cycles):
            transitions = []
            stage_gen_fallbacks = 0
            for _ in range(args.samples_per_cycle):
                try:
                    b0 = select_stage_position(spec.source_stage_names)
                    if b0.turn != chess.WHITE or not b0.is_valid() or b0.is_game_over():
                        raise ValueError("stale or unsuitable KRK curriculum position")
                except Exception:
                    stage_gen_fallbacks += 1
                    b0 = generate_random_krk_position()
                transitions.extend(
                    label_transitions_by_landmark(
                        teacher,
                        b0,
                        label=spec.label,
                        lookahead_black=True,
                    )
                )

            positive_count = 0
            for t in (t for t in transitions if t.label == 1):
                stage_goal_sensor_ids = add_goal_memory_from_vector(
                    learner,
                    teacher,
                    t.v1,
                    label=spec.label,
                    min_mature_for_goals=args.min_mature_for_goals,
                    current_goal_sensor_ids=stage_goal_sensor_ids,
                )
                positive_count += 1
                if positive_count >= min(20, args.max_goals):
                    break

            stats = update_learner_from_transitions(
                learner,
                transitions,
                max_actuators_per_stage=args.max_actuators_per_stage,
                max_actuators_total=args.max_actuators_total,
                delta_eps=args.delta_eps,
                top_k=args.top_k,
                goal_sensor_ids=None,
                curriculum_label=spec.label,
                pruning_profile=pruning_profile_for_cycle(
                    cycle,
                    args.landmark_cycles,
                    any(g.label == spec.label for g in learner.goal_memories),
                ),
                protected_sensor_ids=protected_goal_sensor_ids(
                    learner,
                    allow_prune_foundation=args.allow_prune_foundation,
                ),
            )

            if args.snapshot_every and cycle % args.snapshot_every == 0:
                export_learner_cycle_snapshot(
                    learner,
                    args.output_dir,
                    stage_name=f"stage{spec.stage_index}_{spec.label}",
                    cycle=cycle,
                    transitions=transitions,
                    stats=stats,
                )

            if cycle % 10 == 0 or stats["newly_promoted"] or stats["newly_created_actuators"]:
                mature = len(learner.get_mature_sensors())
                print(
                    f"Cycle {cycle:3d}: sensors={len(learner.sensors)} (mature={mature}) "
                    f"actuators={len(learner.actuators)} goal_prototypes={len(learner.goal_memories)} "
                    f"profile={stats['pruning_profile']}"
                )
                if stage_gen_fallbacks:
                    print(f"  Stage generation fallbacks to random KRK: {stage_gen_fallbacks}")

            if cycle % args.spawn_interval == 0 and cycle > 0:
                for _ in range(args.sensors_per_spawn):
                    learner.sensors.append(learner.spawn_sensor())

    # Save learner pickle
    args.save_learner.parent.mkdir(parents=True, exist_ok=True)
    with open(args.save_learner, "wb") as f:
        pickle.dump(learner, f)
    print(f"\nSaved learner: {args.save_learner}")


if __name__ == "__main__":
    main()
