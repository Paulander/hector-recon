"""
Stage-0/1 chained baseline training for KRK.

Stage 0: Learn sensors/actuators from mate-in-1 transitions.
Stage 1: Backchain using goal memories from Stage 0 (move closer to mate-in-1 goals).
"""

import argparse
import importlib.util
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
    landmark_reward,
    select_stage_position,
    specs_through,
    worst_reply_reward,
)
from recon_lite_chess.training.adaptive_curriculum import (
    StagePassCriteria,
    make_eval_result,
    record_curriculum_event,
)


PRUNING_PROFILES = {"explore", "consolidate", "frozen"}


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


_BASELINE_TO_RECON = None
_KRK_ENTRY_EVAL = None
_STAGE1_EVAL = None
_LANDMARK_EVAL = None


def _baseline_to_recon_module():
    global _BASELINE_TO_RECON
    if _BASELINE_TO_RECON is None:
        _BASELINE_TO_RECON = _load_script_module(
            "baseline_to_recon_adaptive",
            Path(__file__).parent / "baseline_to_recon.py",
        )
    return _BASELINE_TO_RECON


def _stage1_eval_module():
    global _STAGE1_EVAL
    if _STAGE1_EVAL is None:
        _STAGE1_EVAL = _load_script_module(
            "test_stage1_backchain_adaptive",
            Path(__file__).parent / "test_stage1_backchain.py",
        )
    return _STAGE1_EVAL


def _krk_entry_eval_module():
    global _KRK_ENTRY_EVAL
    if _KRK_ENTRY_EVAL is None:
        _KRK_ENTRY_EVAL = _load_script_module(
            "test_krk_entry_adaptive",
            Path(__file__).parent / "test_krk_entry.py",
        )
    return _KRK_ENTRY_EVAL


def _landmark_eval_module():
    global _LANDMARK_EVAL
    if _LANDMARK_EVAL is None:
        _LANDMARK_EVAL = _load_script_module(
            "test_krk_landmark_progress_adaptive",
            Path(__file__).parent / "test_krk_landmark_progress.py",
        )
    return _LANDMARK_EVAL


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


def _goal_vectors_for_labels(
    learner: BaselineLearner,
    labels: List[str],
    sensor_ids: List[int],
) -> List[np.ndarray]:
    return [
        g.s0
        for g in learner.goal_memories
        if g.label in labels and g.s0.shape == (len(sensor_ids),)
    ]


def lower_stage_goal_sensor_ids(learner: BaselineLearner) -> List[int]:
    """Prefer stable sensor basis from stage0_basin, fallback to mate_in_1."""
    for label in ("stage0_basin", "mate_in_1"):
        for goal in learner.goal_memories:
            if goal.label == label and getattr(goal, "sensor_ids", None):
                return list(goal.sensor_ids)
    return [s.id for s in learner.get_mature_sensors()]


def _weighted_min_goal_distance(
    learner: BaselineLearner,
    feature_vector: np.ndarray,
    goal_vectors: List[np.ndarray],
    sensor_ids: List[int],
) -> float:
    if not goal_vectors or not sensor_ids:
        return float("inf")
    s_vec = compute_sensor_vectors_batch(learner, feature_vector[None, :], sensor_ids)[0]
    if learner.backend.use_torch:
        s_vec = s_vec.detach().cpu().numpy()
    sensor_by_id = {s.id: s for s in learner.sensors}
    weights = np.array(
        [1.0 + max(0.0, float(getattr(sensor_by_id.get(sid), "xp", 0.0))) for sid in sensor_ids],
        dtype=np.float32,
    )
    cur = np.asarray(s_vec, dtype=np.float32)
    cur = cur / (np.sqrt(np.sum(weights * (cur ** 2))) + 1e-6)
    best = None
    for goal in goal_vectors:
        goal_np = goal.detach().cpu().numpy() if learner.backend.use_torch and hasattr(goal, "detach") else goal
        g = np.asarray(goal_np, dtype=np.float32)
        if g.shape != cur.shape:
            continue
        g = g / (np.sqrt(np.sum(weights * (g ** 2))) + 1e-6)
        dist = float(np.sqrt(np.sum(weights * ((cur - g) ** 2))))
        if best is None or dist < best:
            best = dist
    return best if best is not None else float("inf")


def label_transitions_by_combined_landmark_goal(
    learner: BaselineLearner,
    teacher: KRKTeacher,
    board: chess.Board,
    label: str,
    sensor_ids: List[int],
    eps: float = 1e-3,
    lookahead_black: bool = True,
    landmark_weight: float = 0.45,
    basin_weight: float = 0.55,
) -> List[TransitionData]:
    """Label moves by Stage-2 landmark progress plus lower-stage basin progress."""
    transitions: List[TransitionData] = []
    v0 = teacher.features(board)
    goal_vectors = _goal_vectors_for_labels(learner, ["stage0_basin"], sensor_ids)
    if not goal_vectors:
        goal_vectors = _goal_vectors_for_labels(learner, ["mate_in_1"], sensor_ids)
    d0 = _weighted_min_goal_distance(learner, v0, goal_vectors, sensor_ids)

    def outcome_reward(outcome: chess.Board) -> float:
        lm = landmark_reward(board, outcome, label)
        basin_progress = 0.0
        if d0 != float("inf") and goal_vectors:
            d1 = _weighted_min_goal_distance(learner, teacher.features(outcome), goal_vectors, sensor_ids)
            if d1 != float("inf"):
                basin_progress = d0 - d1
        reward = (landmark_weight * lm) + (basin_weight * basin_progress)
        if outcome.is_checkmate():
            reward += 2.0
        if outcome.is_stalemate():
            reward -= 1.0
        if len(outcome.pieces(chess.ROOK, chess.WHITE)) == 0:
            reward -= 1.0
        return float(reward)

    for move in board.legal_moves:
        b1 = board.copy()
        b1.push(move)
        v1 = teacher.features(b1)
        if lookahead_black and not b1.is_game_over():
            replies = list(b1.legal_moves)
            rewards = []
            for reply in replies:
                b2 = b1.copy()
                b2.push(reply)
                rewards.append(outcome_reward(b2))
            reward = min(rewards) if rewards else outcome_reward(b1)
        else:
            reward = outcome_reward(b1)
        transitions.append(
            TransitionData(v0=v0, v1=v1, label=1 if reward > eps else 0, action=move, reward=reward)
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


def usable_goal_memory_count(
    learner: BaselineLearner,
    label: str,
    sensor_ids: List[int] | None,
) -> int:
    """Count goal memories that match the current sensor basis."""
    if not sensor_ids:
        return 0
    return sum(
        1
        for goal in learner.goal_memories
        if goal.label == label and goal.s0.shape == (len(sensor_ids),)
    )


def ensure_stage0_goal_memories(
    learner: BaselineLearner,
    teacher: KRKTeacher,
    args: argparse.Namespace,
    sensor_ids: List[int] | None,
) -> List[int] | None:
    """Seed mate-in-1 goal memories once Stage 0 has a usable mature basis."""
    if len(learner.get_mature_sensors()) < args.min_mature_for_goals:
        return sensor_ids
    if sensor_ids is None:
        sensor_ids = [s.id for s in learner.get_mature_sensors()]
    if not sensor_ids or usable_goal_memory_count(learner, "mate_in_1", sensor_ids) > 0:
        return sensor_ids

    targets = [chess.A1, chess.A8, chess.H1, chess.H8]
    sample_count = min(max(8, len(targets)), max(8, min(args.samples_per_cycle, 32)))
    for idx in range(sample_count):
        try:
            board = generate_krk_mate_in_1_position(target_corner=targets[idx % len(targets)])
        except RuntimeError:
            board = generate_krk_mate_in_1_position()
        vector = teacher.features(board)
        s0 = compute_sensor_vectors_batch(learner, vector[None, :], sensor_ids)[0]
        learner.add_goal_memory(s0, label="mate_in_1", sensor_ids=sensor_ids)
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


def pass_criteria_for_label(label: str) -> StagePassCriteria:
    """Return default mastery criteria for a curriculum label."""
    if label == "mate_in_1":
        return StagePassCriteria(min_mate_rate=0.98, max_no_move_rate=0.01)
    if label == "stage0_basin":
        return StagePassCriteria(
            min_improved_rate=0.95,
            min_optimal_rate=0.90,
            max_worsened_rate=0.02,
            min_avg_reward=0.0,
        )
    if label.startswith("edge_trap"):
        return StagePassCriteria(
            min_improved_rate=0.70,
            max_worsened_rate=0.20,
            min_avg_reward=0.0,
            min_mate_playout_rate=0.65,
            max_draw_rate=0.10,
            max_max_plies_rate=0.25,
        )
    return StagePassCriteria(min_improved_rate=0.70, max_worsened_rate=0.20, min_avg_reward=0.0)


def _jsonable_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Drop verbose/non-JSON helper data from evaluator stats."""
    payload = dict(stats)
    payload.pop("records", None)
    return payload


def save_learner_checkpoint(learner: BaselineLearner, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        pickle.dump(learner, fh)


def compile_checkpoint_for_eval(learner: BaselineLearner, output_dir: Path, label: str, cycle: int) -> tuple[Path, Path]:
    """Save and compile a temporary learner checkpoint for runtime evaluation."""
    eval_dir = output_dir / "adaptive_eval" / label / f"cycle_{cycle:04d}"
    learner_path = eval_dir / "learner.pkl"
    topology_path = eval_dir / "topology.json"
    save_learner_checkpoint(learner, learner_path)
    _baseline_to_recon_module().compile_baseline_to_topology(learner_path, topology_path)
    return learner_path, topology_path


def adaptive_stage_state() -> Dict[str, Any]:
    return {"best_score": -float("inf"), "best_cycle": None, "patience_used": 0, "passed": False}


def record_and_checkpoint_adaptive_eval(
    *,
    learner: BaselineLearner,
    output_dir: Path,
    label: str,
    cycle: int,
    metrics: Dict[str, Any],
    state: Dict[str, Any],
    patience: int,
) -> bool:
    """Record eval, save best checkpoint, and return True when stage passes."""
    criteria = pass_criteria_for_label(label)
    result = make_eval_result(label, cycle, _jsonable_stats(metrics), criteria)
    history_path = output_dir / "curriculum_history.json"

    improved = result.score > float(state.get("best_score", -float("inf"))) + 1e-9
    if improved:
        state["best_score"] = result.score
        state["best_cycle"] = cycle
        state["patience_used"] = 0
        best_path = output_dir / "best_learner.pkl"
        stage_best_path = output_dir / "best_by_stage" / f"{label}.pkl"
        save_learner_checkpoint(learner, best_path)
        save_learner_checkpoint(learner, stage_best_path)
    else:
        state["patience_used"] = int(state.get("patience_used", 0)) + 1
        best_path = output_dir / "best_learner.pkl"
        stage_best_path = output_dir / "best_by_stage" / f"{label}.pkl"

    record_curriculum_event(
        history_path,
        {
            "type": "stage_eval",
            "stage_label": label,
            "cycle": cycle,
            "result": result,
            "best_score": state.get("best_score"),
            "best_cycle": state.get("best_cycle"),
            "patience_used": state.get("patience_used"),
            "patience": patience,
            "best_checkpoint": str(best_path),
            "stage_best_checkpoint": str(stage_best_path),
        },
    )
    if result.passed:
        state["passed"] = True
        return True
    return False


def should_adaptive_eval(args: argparse.Namespace, cycle: int) -> bool:
    return (
        bool(args.adaptive_curriculum)
        and cycle + 1 >= args.min_cycles_per_stage
        and ((cycle + 1) % max(1, args.eval_every) == 0)
    )


def evaluate_stage0_checkpoint(learner: BaselineLearner, args: argparse.Namespace, cycle: int) -> Dict[str, Any]:
    _learner_path, topology_path = compile_checkpoint_for_eval(learner, args.output_dir, "mate_in_1", cycle)
    mod = _krk_entry_eval_module()
    graph = mod.load_krk_entry_topology(topology_path)
    stats = mod.run_evaluation(graph, num_positions=max(10, int(args.adaptive_eval_samples)))
    stats["confidences"] = [float(v) for v in stats.get("confidences", [])]
    for key in ("region_total", "region_fail", "corner_fail"):
        if key in stats:
            stats[key] = {str(k): int(v) for k, v in stats[key].items()}
    return stats


def evaluate_stage1_checkpoint(learner: BaselineLearner, args: argparse.Namespace, cycle: int) -> Dict[str, Any]:
    learner_path, topology_path = compile_checkpoint_for_eval(learner, args.output_dir, "stage0_basin", cycle)
    return _stage1_eval_module().evaluate_stage1_backchain(
        topology_path,
        learner_path,
        samples=max(10, int(args.adaptive_eval_samples)),
        seed=args.seed or 7,
        stage_filter=1,
        position_mode=args.stage1_position_mode,
        verbose=False,
    )


def evaluate_landmark_checkpoint(
    learner: BaselineLearner,
    args: argparse.Namespace,
    cycle: int,
    spec_label: str,
    source_stage_names: tuple[str, ...],
    stage_filter: int,
) -> Dict[str, Any]:
    _learner_path, topology_path = compile_checkpoint_for_eval(learner, args.output_dir, spec_label, cycle)
    return _landmark_eval_module().evaluate_landmark_progress(
        topology_path,
        label=spec_label,
        samples=max(10, int(args.adaptive_eval_samples)),
        seed=args.seed or 7,
        stage_filter=stage_filter,
        position_mode="curriculum",
        source_stage_names=source_stage_names,
        playout_max_plies=int(args.adaptive_playout_max_plies),
        black_policy="adversarial",
        verbose=False,
    )


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
    parser.add_argument("--adaptive-curriculum", action="store_true", default=False,
                        help="Train stages until pass/plateau criteria instead of fixed cycle counts")
    parser.add_argument("--eval-every", type=int, default=5,
                        help="Adaptive mode: evaluate every N cycles after min-cycles-per-stage")
    parser.add_argument("--patience", type=int, default=3,
                        help="Adaptive mode: stop a stage after this many eval windows without improvement")
    parser.add_argument("--min-cycles-per-stage", type=int, default=10,
                        help="Adaptive mode: minimum cycles before a stage can pass")
    parser.add_argument("--max-cycles-per-stage", type=int, default=80,
                        help="Adaptive mode: maximum cycles per stage")
    parser.add_argument("--adaptive-eval-samples", type=int, default=50,
                        help="Adaptive mode: samples per validation evaluation")
    parser.add_argument("--adaptive-playout-max-plies", type=int, default=80,
                        help="Adaptive mode: max plies for landmark playout validation")
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
    if args.adaptive_curriculum:
        history_path = args.output_dir / "curriculum_history.json"
        history_path.write_text(json.dumps({"events": []}, indent=2) + "\n", encoding="utf-8")

    goal_sensor_ids: List[int] | None = None

    if learner.stage == 0 and args.stage0_cycles > 0:
        print("=" * 70)
        print("Stage 0: Mate-in-1")
        print("=" * 70)
        
        stage0_cycles = args.max_cycles_per_stage if args.adaptive_curriculum else args.stage0_cycles
        stage0_state = adaptive_stage_state()
        for cycle in range(stage0_cycles):
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
                    stage0_cycles,
                    bool(learner.goal_memories),
                ),
                protected_sensor_ids=protected_goal_sensor_ids(
                    learner,
                    allow_prune_foundation=args.allow_prune_foundation,
                ),
            )
            goal_sensor_ids = ensure_stage0_goal_memories(learner, teacher, args, goal_sensor_ids)

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

            if should_adaptive_eval(args, cycle):
                if usable_goal_memory_count(learner, "mate_in_1", goal_sensor_ids) == 0:
                    print(
                        f"Adaptive Stage 0 eval deferred at cycle {cycle}: "
                        "no usable mate_in_1 goal memories yet."
                    )
                    continue
                metrics = evaluate_stage0_checkpoint(learner, args, cycle)
                if record_and_checkpoint_adaptive_eval(
                    learner=learner,
                    output_dir=args.output_dir,
                    label="mate_in_1",
                    cycle=cycle,
                    metrics=metrics,
                    state=stage0_state,
                    patience=args.patience,
                ):
                    print(f"Adaptive Stage 0 passed at cycle {cycle}")
                    break
                if stage0_state["patience_used"] >= args.patience:
                    print(f"Adaptive Stage 0 plateaued at cycle {cycle}; stopping curriculum.")
                    args.stage1_cycles = 0
                    args.max_curriculum_stage = 1
                    break
        if args.adaptive_curriculum and not stage0_state.get("passed", False):
            print("Adaptive Stage 0 did not pass; stopping before Stage 1.")
            args.stage1_cycles = 0
            args.max_curriculum_stage = 1
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
    stage1_requested = args.stage1_cycles > 0
    if args.stage1_cycles > 0 and (not goal_sensor_ids or not usable_goal_memories):
        print(
            "Skipping Stage 1: Stage 0 did not produce mature sensors and mate_in_1 "
            "goal prototypes. Increase --stage0-cycles/--samples-per-cycle or lower "
            "--min-mature-for-goals for exploratory runs."
        )
        args.stage1_cycles = 0

    stage1_cycles = args.max_cycles_per_stage if args.adaptive_curriculum and args.stage1_cycles > 0 else args.stage1_cycles
    stage1_state = adaptive_stage_state()
    for cycle in range(stage1_cycles):
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
                stage1_cycles,
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

        if should_adaptive_eval(args, cycle):
            metrics = evaluate_stage1_checkpoint(learner, args, cycle)
            if record_and_checkpoint_adaptive_eval(
                learner=learner,
                output_dir=args.output_dir,
                label="stage0_basin",
                cycle=cycle,
                metrics=metrics,
                state=stage1_state,
                patience=args.patience,
            ):
                print(f"Adaptive Stage 1 passed at cycle {cycle}")
                break
            if stage1_state["patience_used"] >= args.patience:
                print(f"Adaptive Stage 1 plateaued at cycle {cycle}; stopping before landmark stages.")
                args.max_curriculum_stage = 1
                break
    if args.adaptive_curriculum and stage1_requested and not stage1_state.get("passed", False):
        print("Adaptive Stage 1 did not pass; stopping before landmark stages.")
        args.max_curriculum_stage = 1

    landmark_specs = specs_through(args.max_curriculum_stage)
    for spec in landmark_specs:
        print("=" * 70)
        print(f"Stage {spec.stage_index}: {spec.label}")
        print("=" * 70)
        learner.stage = spec.stage_index
        stage_goal_sensor_ids: List[int] | None = None
        landmark_cycles = args.max_cycles_per_stage if args.adaptive_curriculum else args.landmark_cycles
        landmark_state = adaptive_stage_state()

        for cycle in range(landmark_cycles):
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
                if spec.label.startswith("edge_trap"):
                    transitions.extend(
                        label_transitions_by_combined_landmark_goal(
                            learner,
                            teacher,
                            b0,
                            label=spec.label,
                            sensor_ids=lower_stage_goal_sensor_ids(learner),
                            lookahead_black=True,
                        )
                    )
                else:
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
                    landmark_cycles,
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

            if should_adaptive_eval(args, cycle):
                metrics = evaluate_landmark_checkpoint(
                    learner,
                    args,
                    cycle,
                    spec.label,
                    spec.source_stage_names,
                    spec.stage_index,
                )
                if record_and_checkpoint_adaptive_eval(
                    learner=learner,
                    output_dir=args.output_dir,
                    label=spec.label,
                    cycle=cycle,
                    metrics=metrics,
                    state=landmark_state,
                    patience=args.patience,
                ):
                    print(f"Adaptive stage {spec.label} passed at cycle {cycle}")
                    break
                if landmark_state["patience_used"] >= args.patience:
                    print(f"Adaptive stage {spec.label} plateaued at cycle {cycle}; stopping curriculum.")
                    break
        if args.adaptive_curriculum and not landmark_state.get("passed", False):
            break

    # Save learner pickle
    args.save_learner.parent.mkdir(parents=True, exist_ok=True)
    with open(args.save_learner, "wb") as f:
        pickle.dump(learner, f)
    print(f"\nSaved learner: {args.save_learner}")


if __name__ == "__main__":
    main()
