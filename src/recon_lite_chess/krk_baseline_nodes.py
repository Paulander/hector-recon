"""
KRK Baseline Node Factories

Factory functions for creating ReCoN nodes from compiled baseline topology.
These are referenced in krk_entry_topology.json.
"""

import numpy as np
from typing import Dict, Any
import chess

from recon_lite.graph import Node, NodeType
from recon_lite_chess.triplets import AfterCondition, cosine_similarity as terminal_cosine_similarity
from recon_lite_hector.learning.baseline import apply_sensor
from recon_lite_chess.baseline_teacher import KRKTeacher
from recon_lite_chess.training.krk_landmarks import LANDMARK_LABELS, worst_reply_reward


_teacher_cache: Dict[str, KRKTeacher] = {}


def _teacher_for_feature_set(feature_set: str | None) -> KRKTeacher:
    """Return a cached teacher for the topology's feature vector contract."""
    key = feature_set or "legacy"
    if key not in _teacher_cache:
        _teacher_cache[key] = KRKTeacher(feature_set=key)
    return _teacher_cache[key]


def create_krk_entry_root(node_id=None):
    """
    Create KRK entry root node with blackboard caching.
    
    Extracts features once per tick and caches in blackboard.
    """
    actual_id = node_id or "krk_entry"
    
    def predicate(node, env):
        # Initialize blackboard if needed
        if "blackboard" not in node.meta:
            node.meta["blackboard"] = {}
        blackboard = env.setdefault("blackboard", node.meta["blackboard"])
        node.meta["blackboard"] = blackboard
        feature_set = node.meta.get("feature_set", blackboard.get("feature_set", "legacy"))
        blackboard["feature_set"] = feature_set
        teacher = _teacher_for_feature_set(feature_set)

        # Extract features ONCE per tick
        if "krk_features" not in blackboard:
            board = env.get("board")
            if board:
                features = teacher.features(board)
                blackboard["krk_features"] = features

        # Initialize caches
        blackboard.setdefault("sensor_outputs", {})
        blackboard.setdefault("sensor_specs", {})
        # Suggestions are per external decision, not per internal ReCoN tick.
        # Legs can fire at different depths, so clearing this every tick makes
        # later/deeper timing dominate selection instead of score.
        env.setdefault("actuator_suggestions", [])
        # Goal bank: hydrate from node.meta if present, otherwise init empty (online growth)
        if "goal_bank" not in blackboard:
            if node.meta.get("goal_bank"):
                blackboard["goal_bank"] = node.meta.get("goal_bank")
            else:
                blackboard["goal_bank"] = {
                    "label": node.meta.get("goal_label", "mate_in_1"),
                    "goals": [],
                    "sensor_specs": {},
                    "sensor_weights": {},
                    "goal_eps": float(node.meta.get("goal_eps", 0.08)),
                }
        if "goal_banks" not in blackboard:
            blackboard["goal_banks"] = node.meta.get("goal_banks", {}) or {}
        blackboard["goal_label"] = node.meta.get("goal_label", "mate_in_1")
        blackboard["goal_normalize"] = node.meta.get("goal_normalize", True)
        blackboard["goal_weight"] = node.meta.get("goal_weight", 0.7)
        blackboard["goal_lookahead"] = node.meta.get("goal_lookahead", "max")
        blackboard["goal_min_overlap"] = node.meta.get("goal_min_overlap", 8)
        blackboard["goal_handoff_threshold"] = node.meta.get("goal_handoff_threshold", 0.2)
        node.meta["goal_bank"] = blackboard.get("goal_bank")
        blackboard["successor_affordance_layer_enabled"] = bool(
            env.get(
                "successor_affordance_layer_enabled",
                blackboard.get(
                    "successor_affordance_layer_enabled",
                    node.meta.get("successor_affordance_layer_enabled", False),
                ),
            )
        )
        blackboard["successor_contract_gate_enabled"] = bool(
            env.get(
                "successor_contract_gate_enabled",
                blackboard.get(
                    "successor_contract_gate_enabled",
                    node.meta.get("successor_contract_gate_enabled", False),
                ),
            )
        )
        blackboard["successor_contract_mismatch_penalty"] = float(
            env.get(
                "successor_contract_mismatch_penalty",
                blackboard.get(
                    "successor_contract_mismatch_penalty",
                    node.meta.get("successor_contract_mismatch_penalty", 10.0),
                ),
            )
        )
        blackboard["successor_role_license_enabled"] = bool(
            env.get(
                "successor_role_license_enabled",
                blackboard.get(
                    "successor_role_license_enabled",
                    node.meta.get("successor_role_license_enabled", False),
                ),
            )
        )
        blackboard["successor_role_license_bonus"] = float(
            env.get(
                "successor_role_license_bonus",
                blackboard.get(
                    "successor_role_license_bonus",
                    node.meta.get("successor_role_license_bonus", 0.05),
                ),
            )
        )

        # Compute current goal distance (for handoff gating) when goal bank exists
        if blackboard.get("goal_bank") and blackboard.get("krk_features") is not None:
            dist, overlap = _goal_distance_from_features(
                blackboard["krk_features"],
                blackboard.get("goal_bank"),
                normalize=blackboard.get("goal_normalize", True),
                min_overlap=int(blackboard.get("goal_min_overlap", 8)),
            )
            blackboard["goal_distance_now"] = dist
            blackboard["goal_overlap_now"] = overlap
            thresh = float(blackboard.get("goal_handoff_threshold", 0.2))
            blackboard["goal_ready"] = (dist is not None and dist <= thresh)

        # Keep root in WAITING so children can run this tick
        return False, False
    
    return Node(
        nid=actual_id,
        ntype=NodeType.SCRIPT,
        predicate=predicate
    )


def create_krk_context_terminal(node_id=None):
    """Create a visible KRK geometric/context terminal.

    These terminals write graph-visible source terms into the blackboard. They
    are safe to run even when the successor layer is disabled; actuator scoring
    only reads them when explicitly enabled.
    """
    actual_id = node_id or "krk_context_terminal"

    def predicate(node, env):
        blackboard = env.get("blackboard")
        board = env.get("board")
        if not blackboard or not board:
            return False, False
        if not blackboard.get("successor_affordance_layer_enabled", False):
            return False, True
        term = node.meta.get("term")
        if not term:
            return False, False
        terms_for_board = _krk_context_terms_for_board(board, blackboard)
        value = terms_for_board.get(term, False)
        terms = blackboard.setdefault("krk_visible_terms", {})
        terms[term] = bool(value)
        node.meta["last_value"] = bool(value)
        return bool(value), True

    return Node(nid=actual_id, ntype=NodeType.TERMINAL, predicate=predicate)


def create_krk_successor_affordance(node_id=None):
    """Create a visible successor-affordance SCRIPT node.

    The node computes a score from visible context terms and records the source
    terms/veto terms. It does not select moves by itself.
    """
    actual_id = node_id or "krk_successor_affordance"

    def predicate(node, env):
        blackboard = env.get("blackboard")
        if not blackboard:
            return False, False
        if not blackboard.get("successor_affordance_layer_enabled", False):
            return False, True
        terms = blackboard.get("krk_visible_terms", {})
        source_terms = list(node.meta.get("source_terms", []))
        veto_terms = list(node.meta.get("veto_terms", []))
        required_terms = list(node.meta.get("required_terms", []))
        score = _score_visible_affordance(terms, source_terms, veto_terms, required_terms)
        missing_required = [term for term in required_terms if not terms.get(term, False)]
        active_veto = [term for term in veto_terms if terms.get(term, False)]
        contract_met = not missing_required and not active_veto
        skill_id = node.meta.get("successor_skill_id") or node.meta.get("skill_id") or actual_id
        role_id = node.meta.get("role_id") or skill_id
        provider_skill_ids = list(node.meta.get("provider_skill_ids", [])) or [skill_id]
        payload = {
            "successor": skill_id,
            "role_id": role_id,
            "provider_skill_ids": provider_skill_ids,
            "score": score,
            "source_terms": [term for term in source_terms if terms.get(term)],
            "veto_terms": active_veto,
            "required_terms": required_terms,
            "missing_required_terms": missing_required,
            "contract_met": contract_met,
            "enabled": bool(blackboard.get("successor_affordance_layer_enabled", False)),
        }
        blackboard.setdefault("krk_successor_affordances", {})[skill_id] = payload
        blackboard.setdefault("krk_successor_role_affordances", {})[role_id] = payload
        provider_licenses = blackboard.setdefault("krk_successor_provider_licenses", {})
        for provider_id in provider_skill_ids:
            provider_payload = provider_licenses.setdefault(provider_id, {})
            if isinstance(provider_payload, dict):
                provider_payload[role_id] = payload
            else:
                provider_licenses[provider_id] = {role_id: payload}
        node.meta["last_successor_affordance"] = payload
        return score > float(node.meta.get("confirm_threshold", 0.0)), True

    return Node(nid=actual_id, ntype=NodeType.SCRIPT, predicate=predicate)


def create_krk_affordance_marker_terminal(node_id=None):
    """Marker terminal that prevents affordance SCRIPTs from auto-confirming before predicate execution."""
    actual_id = node_id or "krk_affordance_marker"

    def predicate(node, env):
        return True, True

    return Node(nid=actual_id, ntype=NodeType.TERMINAL, predicate=predicate)


def create_krk_hub(node_id=None):
    """
    Create Hub node with bandit selection.
    
    Selects which Leg to activate based on bandit scores.
    """
    actual_id = node_id or "krk_hub"
    
    def predicate(node, env):
        # For now, just pass through
        # Bandit logic will be added later
        # Keep hub waiting so children get requested
        return False, False
    
    return Node(
        nid=actual_id,
        ntype=NodeType.SCRIPT,
        predicate=predicate
    )


def create_leg_script(node_id=None):
    """Create Leg SCRIPT node (simple pass-through)"""
    actual_id = node_id or "leg_script"
    
    def predicate(node, env):
        # Keep leg waiting so children get requested
        return False, False
    
    return Node(
        nid=actual_id,
        ntype=NodeType.SCRIPT,
        predicate=predicate
    )


def create_act_script(node_id=None):
    """Create actuator wrapper SCRIPT node."""
    actual_id = node_id or "act_script"
    
    def predicate(node, env):
        # Keep actuator wrapper waiting so child terminal runs
        return False, False
    
    return Node(
        nid=actual_id,
        ntype=NodeType.SCRIPT,
        predicate=predicate
    )


def create_and_gate(node_id=None):
    """
    Create AND-gate SCRIPT node.
    
    All children must confirm for this to confirm.
    """
    actual_id = node_id or "and_gate"
    
    def predicate(node, env):
        # Aggregation handled by engine
        # Keep AND gate waiting so children can confirm
        return False, False
    
    return Node(
        nid=actual_id,
        ntype=NodeType.SCRIPT,
        predicate=predicate
    )


def create_sensor_terminal(node_id=None):
    """
    Create sensor TERMINAL node.
    
    Reads cached features from blackboard, applies readout, caches output.
    """
    actual_id = node_id or "sensor_terminal"
    
    def predicate(node, env):
        blackboard = env.get("blackboard")
        if not blackboard:
            return False, False
        
        # Read cached features
        features = blackboard.get("krk_features")
        if features is None:
            return False, False
        
        # Apply sensor readout
        readout_type = node.meta.get("readout_type", "identity")
        feature_mask_keys = node.meta.get("feature_mask_keys", [])
        readout_params = node.meta.get("readout_params", {})
        
        # Convert feature keys to mask
        feature_mask = np.zeros(len(features), dtype=bool)
        for key in feature_mask_keys:
            # Extract index from "feature_X" format
            if key.startswith("feature_"):
                idx = int(key.split("_")[1])
                if idx < len(features):
                    feature_mask[idx] = True
        
        # Handle case where no features selected
        if not np.any(feature_mask):
            return False, False
        
        # Apply readout
        sub_v = features[feature_mask]
        try:
            output = apply_readout(sub_v, readout_type, readout_params)
        except Exception as e:
            print(f"Warning: Sensor {node.nid} readout failed: {e}")
            return False, False
        
        # Cache output + spec for actuators
        blackboard["sensor_outputs"][node.nid] = output
        weight = None
        if "baseline_xp" in node.meta:
            try:
                weight = 1.0 + max(0.0, float(node.meta.get("baseline_xp", 0.0)))
            except Exception:
                weight = None
        blackboard["sensor_specs"][node.nid] = {
            "readout_type": readout_type,
            "feature_mask_keys": feature_mask_keys,
            "readout_params": readout_params,
            "weight": weight,
        }
        
        # Store in node state
        if not hasattr(node, 'state') or node.state is None:
            node.state = {}
        node.meta["output"] = output
        
        return True, True
    
    return Node(
        nid=actual_id,
        ntype=NodeType.TERMINAL,
        predicate=predicate
    )


def create_actuator_terminal(node_id=None):
    """
    Create actuator TERMINAL node.
    
    Scores moves by similarity to goal_delta, selects best move.
    """
    actual_id = node_id or "actuator_terminal"
    
    def predicate(node, env):
        blackboard = env.get("blackboard")
        if not blackboard:
            return False, False
        sensor_outputs = blackboard.get("sensor_outputs", {})
        sensor_specs = blackboard.get("sensor_specs", {})
        
        # Get targets and goal_delta
        targets = node.meta.get("targets", [])
        goal_delta = node.meta.get("goal_delta", {})
        stage = int(node.meta.get("stage", 0))

        # Optional eval/training filter: only allow selected actuator stages.
        # This is useful for isolating Stage-1 behavior in diagnostics.
        stage_filter = blackboard.get("stage_filter")
        if stage_filter is not None:
            try:
                if stage != int(stage_filter):
                    return False, False
            except Exception:
                pass
        
        if not targets or not goal_delta:
            return False, False
        
        # Get current sensor values
        s0 = {}
        for target_id in targets:
            if target_id in sensor_outputs:
                s0[target_id] = sensor_outputs[target_id]
        
        if len(s0) != len(targets):
            return False, False  # Not all sensors available
        
        # Determine spotlight weight (handoff A + C)
        features = blackboard.get("krk_features")
        mate_possible = False
        if features is not None and len(features) > 12:
            mate_possible = features[12] >= 0.5  # can_deliver_mate

        goal_ready = bool(blackboard.get("goal_ready"))
        # Stage bias: spotlight tactical (stage 0) when goal basin reached AND mate is visible
        if goal_ready and mate_possible:
            stage_weight = 3.0 if stage == 0 else 0.2
        elif mate_possible:
            stage_weight = 2.5 if stage == 0 else 0.5
        else:
            stage_weight = 0.7 if stage == 0 else 1.0

        # Optional goal bank for backchaining (pure terminal-space objective)
        goal_banks = blackboard.get("goal_banks", {}) or {}
        default_goal_bank = blackboard.get("goal_bank")
        default_goal_label = blackboard.get("goal_label", "mate_in_1")
        goal_label = node.meta.get("target_goal_label") or default_goal_label
        goal_bank = goal_banks.get(goal_label) if isinstance(goal_banks, dict) else None
        if goal_bank is None:
            goal_bank = default_goal_bank
            goal_label = default_goal_label
        goal_normalize = blackboard.get("goal_normalize", True)
        goal_weight = float(blackboard.get("goal_weight", 0.7))
        goal_progress_weight = float(blackboard.get("goal_progress_weight", 100.0))
        goal_lookahead = blackboard.get("goal_lookahead", "max")
        min_goal_overlap = float(blackboard.get("goal_min_overlap", 8))
        curriculum_label = node.meta.get("curriculum_label")
        skill_id = node.meta.get("skill_id")
        forced_successor_skill = blackboard.get("forced_successor_skill")
        if forced_successor_skill and skill_id != forced_successor_skill:
            return False, False
        use_landmark_runtime_reward = curriculum_label in LANDMARK_LABELS and stage >= 2
        goal_entries = []
        if goal_bank and stage > 0:
            if isinstance(goal_bank, dict) and goal_bank.get("label") == goal_label:
                goal_entries = goal_bank.get("goals", [])

        # Score each legal move
        board = env.get("board")
        if not board:
            return False, False
        
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return False, False
        
        scores = {}
        move_meta: Dict[Any, Dict[str, Any]] = {}
        for move in legal_moves:
            # Simulate move
            board_copy = board.copy()
            board_copy.push(move)
            is_mate = board_copy.is_checkmate()
            is_draw = board_copy.is_stalemate() or board_copy.is_insufficient_material()
            reply_draw_or_rook_loss_risk = False
            
            # Get new features
            teacher = _teacher_for_feature_set(blackboard.get("feature_set", "legacy"))
            features_1 = teacher.features(board_copy)
            
            # Compute Δs for target sensors
            delta_s = []
            for target_id in targets:
                spec = sensor_specs.get(target_id)
                if spec is None:
                    base_id = target_id.split("_post_")[0]
                    spec = sensor_specs.get(base_id)
                if spec is None:
                    continue
                
                s1 = _apply_spec_to_features(spec, features_1)
                if s1 is None:
                    continue
                
                # Compute delta
                delta = s1 - s0[target_id]
                delta_s.append(delta)
            
            if len(delta_s) == 0:
                continue
                
            # Score by similarity to goal_delta
            goal_deltas = [goal_delta[t] for t in targets if t in goal_delta][:len(delta_s)]
            similarity = cosine_similarity(delta_s, goal_deltas)
            actuator_xp = float(node.meta.get("baseline_xp", 0.0))
            similarity_score = similarity * stage_weight * (1.0 + max(0.0, actuator_xp))
            score = similarity_score

            # Goal distance shaping (Stage > 0 only)
            if goal_entries:
                def _goal_distance_for_board(b):
                    f = teacher.features(b)
                    # Build current sensor map by stable id (graph specs + goal specs)
                    s_goal: Dict[str, float] = {}
                    goal_specs = {}
                    if isinstance(goal_bank, dict):
                        goal_specs = goal_bank.get("sensor_specs", {}) or {}
                    merged_specs = dict(goal_specs)
                    merged_specs.update(sensor_specs)
                    for sid_key, spec in merged_specs.items():
                        val = _apply_spec_to_features(spec, f)
                        if val is not None:
                            s_goal[sid_key] = float(val)
                    if not s_goal:
                        return None

                    def _dist(entry):
                        gvals = entry.get("values", {})
                        keys = set(s_goal.keys()) & set(gvals.keys())
                        if not keys:
                            return None
                        weights = np.array([
                            _goal_weight_for_sensor(k, goal_bank, merged_specs)
                            for k in keys
                        ], dtype=np.float32)
                        weight_sum = float(np.sum(weights))
                        if weight_sum < min_goal_overlap:
                            return None
                        vec_cur = np.array([s_goal[k] for k in keys], dtype=np.float32)
                        vec_goal = np.array([gvals[k] for k in keys], dtype=np.float32)
                        if goal_normalize:
                            vec_cur = vec_cur / (np.sqrt(np.sum(weights * (vec_cur ** 2))) + 1e-6)
                            vec_goal = vec_goal / (np.sqrt(np.sum(weights * (vec_goal ** 2))) + 1e-6)
                        diff = vec_cur - vec_goal
                        return float(np.sqrt(np.sum(weights * (diff ** 2))))

                    best = None
                    for entry in goal_entries:
                        d = _dist(entry)
                        if d is None:
                            continue
                        if best is None or d < best:
                            best = d
                    return best

                d0 = blackboard.get("goal_distance_now") if goal_label == default_goal_label else None
                if d0 is None:
                    d0 = _goal_distance_for_board(board)

                # If lookahead enabled, evaluate after one black reply (worst-case by default)
                d1 = None
                if goal_lookahead and goal_lookahead != "none":
                    d1_candidates = []
                    for reply in board_copy.legal_moves:
                        b2 = board_copy.copy()
                        b2.push(reply)
                        if (
                            b2.is_stalemate()
                            or b2.is_insufficient_material()
                            or not list(b2.pieces(chess.ROOK, chess.WHITE))
                        ):
                            reply_draw_or_rook_loss_risk = True
                        d2 = _goal_distance_for_board(b2)
                        if d2 is not None:
                            d1_candidates.append(d2)
                    if d1_candidates:
                        d1 = max(d1_candidates) if goal_lookahead == "max" else min(d1_candidates)
                else:
                    d1 = _goal_distance_for_board(board_copy)

                move_meta[move] = {
                    "is_mate": is_mate,
                    "is_draw": is_draw,
                    "reply_draw_or_rook_loss_risk": reply_draw_or_rook_loss_risk,
                    "goal_dist": d1,
                    "goal_dist_before": d0,
                }
                if d1 is not None:
                    if d0 is not None:
                        # Align runtime with Stage-1 training/eval: prefer moves
                        # that reduce distance to the learned mate-in-1 basin.
                        goal_progress = float(d0) - float(d1)
                        if use_landmark_runtime_reward:
                            landmark_score = worst_reply_reward(
                                board,
                                move,
                                curriculum_label,
                                use_black_reply=bool(goal_lookahead and goal_lookahead != "none"),
                            )
                            score = (0.45 * landmark_score) + (0.55 * goal_progress) + (0.001 * similarity_score)
                            move_meta[move]["landmark_reward"] = landmark_score
                            move_meta[move]["goal_progress"] = goal_progress
                        else:
                            score = (goal_progress_weight * goal_progress) + (0.001 * similarity_score)
                    else:
                        score = (goal_weight * (-float(d1))) + (0.001 * similarity_score)
            else:
                move_meta[move] = {
                    "is_mate": is_mate,
                    "is_draw": is_draw,
                    "reply_draw_or_rook_loss_risk": reply_draw_or_rook_loss_risk,
                    "goal_dist": None,
                }

            if is_mate:
                score += 1_000_000.0
            elif is_draw or reply_draw_or_rook_loss_risk:
                # Do not let raw delta-s similarity select a stalemate/draw
                # or a tactically loose move where Black can remove the rook.
                score -= 1_000_000.0

            if blackboard.get("successor_affordance_layer_enabled"):
                score = _apply_successor_affordance_bias(
                    score,
                    skill_id=skill_id,
                    curriculum_label=curriculum_label,
                    blackboard=blackboard,
                    move_meta=move_meta[move],
                )

            scores[move] = score
        
        if not scores:
            return False, False
        
        # Select best move
        best_move = max(scores, key=scores.get)
        best_score = scores[best_move]
        best_meta = move_meta.get(best_move, {})
        
        # Store suggestions in environment, keep best across actuators
        suggestions = env.setdefault("actuator_suggestions", [])
        suggestions.append({
            "actuator": node.nid,
            "move": best_move,
            "score": best_score,
            "stage": stage,
            "curriculum_label": node.meta.get("curriculum_label"),
            "target_goal_label": goal_label,
            "meta": best_meta,
        })
        
        best = max(suggestions, key=lambda s: s["score"])
        env["suggested_move"] = best["move"].uci()
        env["move_confidence"] = best["score"]
        env["suggested_actuator"] = best["actuator"]

        # Optional online goal discovery: disabled by default so evaluation and
        # normal play do not mutate the goal basin while scoring a decision.
        allow_goal_promotion = bool(
            env.get("allow_online_goal_promotion")
            or blackboard.get("allow_online_goal_promotion")
        )
        if allow_goal_promotion and best["actuator"] == node.nid:
            should_promote = False
            if best_meta.get("is_mate"):
                should_promote = True
            else:
                d1 = best_meta.get("goal_dist")
                thresh = float(blackboard.get("goal_handoff_threshold", 0.2))
                if d1 is not None and d1 <= thresh:
                    should_promote = True
            if should_promote:
                _promote_goal_from_outputs(blackboard)
        
        # Store in node state
        if not hasattr(node, 'state') or node.state is None:
            node.state = {}
        node.meta["move"] = best_move.uci()
        node.meta["confidence"] = best_score
        
        return True, True
    
    return Node(
        nid=actual_id,
        ntype=NodeType.TERMINAL,
        predicate=predicate
    )


def _krk_context_terms_for_board(
    board: chess.Board,
    blackboard: Dict[str, Any] | None = None,
) -> Dict[str, bool]:
    """Compute/cache the visible KRK context vector once per board state."""
    cache_key = (board.board_fen(), bool(board.turn))
    if blackboard is not None:
        cache = blackboard.setdefault("krk_context_terms_cache", {})
        cached = cache.get(cache_key)
        if isinstance(cached, dict):
            blackboard["krk_context_terms_cache_hits"] = int(
                blackboard.get("krk_context_terms_cache_hits", 0)
            ) + 1
            return cached
    terms = _compute_krk_context_terms(board)
    if blackboard is not None:
        cache = blackboard.setdefault("krk_context_terms_cache", {})
        cache[cache_key] = terms
        blackboard["krk_context_terms_cache_misses"] = int(
            blackboard.get("krk_context_terms_cache_misses", 0)
        ) + 1
    return terms


def _evaluate_krk_context_term(board: chess.Board, term: str) -> bool:
    return bool(_compute_krk_context_terms(board).get(term, False))


def _compute_krk_context_terms(board: chess.Board) -> Dict[str, bool]:
    wk_sq = next(iter(board.pieces(chess.KING, chess.WHITE)), None)
    bk_sq = next(iter(board.pieces(chess.KING, chess.BLACK)), None)
    wr_sq = next(iter(board.pieces(chess.ROOK, chess.WHITE)), None)
    if wk_sq is None or bk_sq is None or wr_sq is None:
        return {}

    wk_file, wk_rank = chess.square_file(wk_sq), chess.square_rank(wk_sq)
    bk_file, bk_rank = chess.square_file(bk_sq), chess.square_rank(bk_sq)
    wr_file, wr_rank = chess.square_file(wr_sq), chess.square_rank(wr_sq)
    edge_distance = min(bk_file, 7 - bk_file, bk_rank, 7 - bk_rank)
    rook_king_distance = max(abs(wr_file - bk_file), abs(wr_rank - bk_rank))
    king_rook_distance = max(abs(wk_file - wr_file), abs(wk_rank - wr_rank))
    king_distance = max(abs(wk_file - bk_file), abs(wk_rank - bk_rank))
    if rook_king_distance > 1:
        rook_safe = True
    else:
        capture = chess.Move(bk_sq, wr_sq)
        reply_board = board.copy(stack=False)
        reply_board.turn = chess.BLACK
        rook_safe = capture not in reply_board.legal_moves or king_rook_distance <= 1
    king_support = king_rook_distance <= 2 or king_distance <= 2
    same_line_cut = wr_file == bk_file or wr_rank == bk_rank
    fence_exists = rook_safe and (edge_distance == 0 or (same_line_cut and rook_king_distance >= 2))
    fence_stable = fence_exists and king_support
    box_width = wr_file if bk_file < wr_file else 7 - wr_file
    box_height = wr_rank if bk_rank < wr_rank else 7 - wr_rank
    box_width = max(1, box_width)
    box_height = max(1, box_height)
    box_area = box_width * box_height
    mate_basin_available = board.turn == chess.WHITE and any(
        _move_checkmates(board, move) for move in board.legal_moves
    )
    enemy_between_axis = (
        (wk_file == bk_file == wr_file and min(wk_rank, wr_rank) < bk_rank < max(wk_rank, wr_rank))
        or (wk_rank == bk_rank == wr_rank and min(wk_file, wr_file) < bk_file < max(wk_file, wr_file))
    )
    enemy_king_near_edge = edge_distance <= 1
    post_fence_conversion_needed = fence_exists and not mate_basin_available
    rook_has_safe_lateral_transfer = _rook_has_safe_lateral_transfer(board, wr_sq, bk_sq)
    safe_rook_long_transfer_available = _safe_rook_transfer_available(
        board, wr_sq, min_distance=3
    )
    safe_rook_edge_transfer_available = _safe_rook_transfer_available(
        board, wr_sq, min_distance=2, require_edge_destination=True
    )
    safe_check_available = _safe_check_available(board)
    king_support_improvement_move_exists = _king_support_improvement_move_exists(
        board, wk_sq, bk_sq, wr_sq
    )
    corner_distance = min(
        max(abs(bk_file - file_), abs(bk_rank - rank_))
        for file_, rank_ in ((0, 0), (0, 7), (7, 0), (7, 7))
    )
    edge_trap_shape_available = (
        fence_exists
        and enemy_king_near_edge
        and rook_safe
        and post_fence_conversion_needed
        and rook_has_safe_lateral_transfer
    )
    edge_trap_close_geometry = edge_trap_shape_available and king_support
    wrong_tempo_geometry = (
        fence_exists
        and enemy_king_near_edge
        and enemy_between_axis
        and not king_support
        and rook_safe
        and post_fence_conversion_needed
    )

    values = {
        "fence_exists": fence_exists,
        "fence_stable": fence_stable,
        "fence_needs_repair": fence_exists and not fence_stable,
        "fence_already_satisfied": fence_exists and fence_stable,
        "post_fence_conversion_needed": post_fence_conversion_needed,
        "enemy_king_not_at_edge": edge_distance > 0,
        "enemy_king_edge_distance_bin": edge_distance >= 2,
        "enemy_king_near_edge": enemy_king_near_edge,
        "box_area_large": box_area >= 12,
        "box_shrink_available": box_area >= 6 and fence_exists,
        "white_king_support_available": king_support,
        "white_king_can_improve_support": _white_king_can_improve_support(board, wk_sq, bk_sq),
        "king_support_improvement_move_exists": king_support_improvement_move_exists,
        "wrong_tempo_detected": fence_exists and not king_support,
        "wrong_tempo_geometry": wrong_tempo_geometry,
        "mate_in_one_available": mate_basin_available,
        # Backwards-compatible alias for older compiled topologies. The term
        # really means immediate mate availability, not basin membership.
        "mate_basin_available": mate_basin_available,
        "goal_basin_proximity_low": False,
        "goal_distance_can_decrease": False,
        "enemy_king_restricted": fence_exists or edge_distance <= 1,
        "king_approach_after_fence_available": (
            post_fence_conversion_needed and rook_safe and king_support_improvement_move_exists
        ),
        "enemy_between_king_and_rook_axis": enemy_between_axis,
        "edge_trap_shape_available": edge_trap_shape_available,
        "edge_trap_close_geometry": edge_trap_close_geometry,
        "enemy_between_geometry": edge_trap_shape_available and enemy_between_axis,
        "rook_has_safe_lateral_transfer": rook_has_safe_lateral_transfer,
        "safe_rook_long_transfer_available": safe_rook_long_transfer_available,
        "safe_rook_edge_transfer_available": safe_rook_edge_transfer_available,
        "safe_check_available": safe_check_available,
        "rook_transfer_after_fence_available": (
            post_fence_conversion_needed
            and rook_safe
            and rook_has_safe_lateral_transfer
            and safe_rook_long_transfer_available
        ),
        "edge_rook_transfer_recovery_available": (
            post_fence_conversion_needed
            and rook_safe
            and enemy_king_near_edge
            and safe_rook_edge_transfer_available
        ),
        "corner_net_pressure_available": (
            post_fence_conversion_needed
            and rook_safe
            and enemy_king_near_edge
            and corner_distance <= 2
            and (safe_rook_edge_transfer_available or safe_check_available)
        ),
        "rook_safe": rook_safe,
        "cut_stable": fence_stable,
        "black_king_escape_available": edge_distance > 0,
    }
    return {key: bool(value) for key, value in values.items()}


def _move_checkmates(board: chess.Board, move: chess.Move) -> bool:
    if move not in board.legal_moves:
        return False
    b2 = board.copy()
    b2.push(move)
    return b2.is_checkmate()


def _rook_has_safe_lateral_transfer(
    board: chess.Board,
    wr_sq: chess.Square,
    bk_sq: chess.Square,
) -> bool:
    if board.turn != chess.WHITE:
        return False
    wr_file = chess.square_file(wr_sq)
    wr_rank = chess.square_rank(wr_sq)
    for move in board.legal_moves:
        if move.from_square != wr_sq:
            continue
        to_file = chess.square_file(move.to_square)
        to_rank = chess.square_rank(move.to_square)
        if to_file == wr_file and to_rank == wr_rank:
            continue
        if to_file != wr_file and to_rank != wr_rank:
            continue
        b2 = board.copy(stack=False)
        b2.push(move)
        if b2.is_game_over():
            return True
        capture = chess.Move(bk_sq, move.to_square)
        b2.turn = chess.BLACK
        if capture not in b2.legal_moves:
            return True
    return False


def _rook_safe_after_white_move(board: chess.Board, move: chess.Move) -> bool:
    if move not in board.legal_moves:
        return False
    b2 = board.copy(stack=False)
    b2.push(move)
    if b2.is_checkmate():
        return True
    wr_sqs = list(b2.pieces(chess.ROOK, chess.WHITE))
    wk_sqs = list(b2.pieces(chess.KING, chess.WHITE))
    bk_sqs = list(b2.pieces(chess.KING, chess.BLACK))
    if not wr_sqs or not wk_sqs or not bk_sqs:
        return False
    wr_sq = wr_sqs[0]
    wk_sq = wk_sqs[0]
    bk_sq = bk_sqs[0]
    if chess.square_distance(wr_sq, bk_sq) > 1:
        return True
    capture = chess.Move(bk_sq, wr_sq)
    b2.turn = chess.BLACK
    return capture not in b2.legal_moves or chess.square_distance(wk_sq, wr_sq) <= 1


def _safe_rook_transfer_available(
    board: chess.Board,
    wr_sq: chess.Square,
    *,
    min_distance: int = 2,
    require_edge_destination: bool = False,
) -> bool:
    if board.turn != chess.WHITE:
        return False
    wr_file = chess.square_file(wr_sq)
    wr_rank = chess.square_rank(wr_sq)
    for move in board.legal_moves:
        if move.from_square != wr_sq:
            continue
        to_file = chess.square_file(move.to_square)
        to_rank = chess.square_rank(move.to_square)
        if max(abs(to_file - wr_file), abs(to_rank - wr_rank)) < min_distance:
            continue
        if require_edge_destination and to_file not in (0, 7) and to_rank not in (0, 7):
            continue
        if _rook_safe_after_white_move(board, move):
            return True
    return False


def _safe_check_available(board: chess.Board) -> bool:
    if board.turn != chess.WHITE:
        return False
    for move in board.legal_moves:
        if not board.gives_check(move):
            continue
        if move.from_square in board.pieces(chess.ROOK, chess.WHITE):
            if not _rook_safe_after_white_move(board, move):
                continue
        return True
    return False


def _king_support_improvement_move_exists(
    board: chess.Board,
    wk_sq: chess.Square,
    bk_sq: chess.Square,
    wr_sq: chess.Square,
) -> bool:
    if board.turn != chess.WHITE:
        return False
    current_to_black = chess.square_distance(wk_sq, bk_sq)
    current_to_rook = chess.square_distance(wk_sq, wr_sq)
    for move in board.legal_moves:
        if move.from_square != wk_sq:
            continue
        improves_black = chess.square_distance(move.to_square, bk_sq) < current_to_black
        improves_rook = chess.square_distance(move.to_square, wr_sq) < current_to_rook
        if not improves_black and not improves_rook:
            continue
        b2 = board.copy(stack=False)
        b2.push(move)
        if b2.is_checkmate() or not b2.is_check():
            return True
    return False


def _white_king_can_improve_support(
    board: chess.Board,
    wk_sq: chess.Square,
    bk_sq: chess.Square,
) -> bool:
    if board.turn != chess.WHITE:
        return False
    current = chess.square_distance(wk_sq, bk_sq)
    for move in board.legal_moves:
        if move.from_square != wk_sq:
            continue
        if chess.square_distance(move.to_square, bk_sq) < current:
            return True
    return False


def _score_visible_affordance(
    terms: Dict[str, bool],
    source_terms: list[str],
    veto_terms: list[str],
    required_terms: list[str],
) -> float:
    if any(terms.get(term, False) for term in veto_terms):
        return 0.0
    if any(not terms.get(term, False) for term in required_terms):
        return 0.0
    if not source_terms:
        return 0.0
    active = sum(1 for term in source_terms if terms.get(term, False))
    return float(active) / float(len(source_terms))


def _apply_successor_affordance_bias(
    score: float,
    *,
    skill_id: str | None,
    curriculum_label: str | None,
    blackboard: Dict[str, Any],
    move_meta: Dict[str, Any],
) -> float:
    canonical = skill_id or _canonical_krk_skill_id(curriculum_label)
    affordances = blackboard.get("krk_successor_affordances", {})
    payload = affordances.get(canonical, {})
    affordance_score = float(payload.get("score", 0.0) or 0.0)
    terms = blackboard.get("krk_visible_terms", {})
    fence_satisfied = bool(terms.get("fence_already_satisfied", False))
    fence_needs_repair = bool(terms.get("fence_needs_repair", False))
    bias_weight = float(blackboard.get("successor_affordance_bias_weight", 0.05))
    raw_score = float(score)
    visible_affordance_bonus = bias_weight * affordance_score
    adjusted = raw_score + visible_affordance_bonus
    move_meta["raw_score_before_role_bonus"] = raw_score
    move_meta["visible_affordance_bonus"] = visible_affordance_bonus
    role_licenses = _provider_role_licenses(canonical, blackboard)
    if blackboard.get("successor_role_license_enabled", False) and role_licenses:
        best_license = max(role_licenses, key=lambda item: float(item.get("score", 0.0) or 0.0))
        role_bonus_weight = float(blackboard.get("successor_role_license_bonus", 0.05))
        role_bonus = role_bonus_weight * float(best_license.get("score", 0.0) or 0.0)
        adjusted += role_bonus
        move_meta["visible_role_license_bonus"] = role_bonus
        move_meta["role_bonus_total"] = role_bonus
        move_meta["role_bonus_by_role"] = {
            str(item.get("role_id") or item.get("successor") or ""): (
                role_bonus_weight * float(item.get("score", 0.0) or 0.0)
            )
            for item in role_licenses
        }
        move_meta["visible_role_licenses"] = [
            {
                "role_id": str(item.get("role_id") or item.get("successor") or ""),
                "score": float(item.get("score", 0.0) or 0.0),
                "source_terms": list(item.get("source_terms", [])),
                "provider_skill_ids": list(item.get("provider_skill_ids", [])),
            }
            for item in role_licenses
        ]
    if _visible_contract_gate_applies(canonical, payload, affordances, blackboard):
        penalty = float(blackboard.get("successor_contract_mismatch_penalty", 10.0))
        adjusted -= penalty
        move_meta["visible_contract_gate_penalty"] = penalty
        move_meta["visible_contract_gate_reason"] = {
            "skill_id": canonical,
            "missing_required_terms": list(payload.get("missing_required_terms", [])),
            "veto_terms": list(payload.get("veto_terms", [])),
            "eligible_alternatives": _eligible_successor_ids(affordances, exclude=canonical),
        }
    if canonical == "krk.fence_established" and fence_satisfied and not fence_needs_repair:
        adjusted -= float(blackboard.get("same_skill_satisfied_penalty", 0.05))
        move_meta["same_skill_satisfied_penalty"] = True
    move_meta["score_after_role_bonus"] = adjusted
    move_meta["visible_successor_affordance"] = payload
    return adjusted


def _provider_role_licenses(provider_id: str, blackboard: Dict[str, Any]) -> list[Dict[str, Any]]:
    """Return visible role contracts that license a provider skill.

    Missing role contracts are intentionally neutral. A role can add visible
    support only when its own required terms are confirmed and veto terms are
    absent.
    """
    licenses = blackboard.get("krk_successor_provider_licenses", {}).get(provider_id, {})
    if isinstance(licenses, dict):
        iterable = licenses.values()
    elif isinstance(licenses, list):
        iterable = licenses
    else:
        return []
    visible: list[Dict[str, Any]] = []
    for item in iterable:
        if not isinstance(item, dict):
            continue
        if bool(item.get("contract_met", False)) and float(item.get("score", 0.0) or 0.0) > 0.0:
            visible.append(item)
    return visible


def _visible_contract_gate_applies(
    canonical: str,
    payload: Dict[str, Any],
    affordances: Dict[str, Any],
    blackboard: Dict[str, Any],
) -> bool:
    """Return whether an opt-in visible contract penalty should apply.

    This is deliberately a penalty, not a hidden router. The move still comes
    from normal actuator scoring; the visible contract only prevents an
    overconfident skill from dominating when its own visible preconditions are
    unmet and another visible successor has support.
    """
    if not blackboard.get("successor_contract_gate_enabled", False):
        return False
    if not payload:
        return False
    if bool(payload.get("contract_met", False)):
        return False
    if not _eligible_successor_ids(affordances, exclude=canonical):
        return False
    return True


def _eligible_successor_ids(affordances: Dict[str, Any], *, exclude: str | None = None) -> list[str]:
    eligible: list[str] = []
    for skill_id, entry in affordances.items():
        if skill_id == exclude or not isinstance(entry, dict):
            continue
        if bool(entry.get("contract_met", False)) and float(entry.get("score", 0.0) or 0.0) > 0.0:
            eligible.append(str(skill_id))
    return sorted(eligible)


def _canonical_krk_skill_id(curriculum_label: str | None) -> str:
    raw = curriculum_label or "uncategorized"
    normalized = "".join(ch if ch.isalnum() else "_" for ch in raw.lower()).strip("_")
    return f"krk.{normalized or 'uncategorized'}"


def create_triplet_after_terminal(node_id=None):
    """Create a TERMINAL that verifies a chosen move's terminal-space delta."""
    actual_id = node_id or "triplet_after"

    def predicate(node, env):
        blackboard = env.get("blackboard")
        board = env.get("board")
        if not blackboard or not board:
            return False, False

        move = env.get("suggested_move") or env.get("chosen_move")
        if move is None:
            return False, False
        if isinstance(move, str):
            try:
                move = chess.Move.from_uci(move)
            except Exception:
                return True, False
        if move not in board.legal_moves:
            return True, False

        targets = tuple(node.meta.get("targets", ()))
        goal_delta = dict(node.meta.get("goal_delta", {}))
        if not targets or not goal_delta:
            return True, False

        sensor_outputs = blackboard.get("sensor_outputs", {})
        sensor_specs = blackboard.get("sensor_specs", {})
        before: Dict[str, float] = {}
        after: Dict[str, float] = {}

        board_after = board.copy()
        board_after.push(move)
        teacher = _teacher_for_feature_set(blackboard.get("feature_set", "legacy"))
        features_after = teacher.features(board_after)

        for target_id in targets:
            if target_id not in sensor_outputs:
                continue
            spec = sensor_specs.get(target_id)
            if spec is None:
                base_id = target_id.split("_post_")[0]
                spec = sensor_specs.get(base_id)
            if spec is None:
                continue
            after_value = _apply_spec_to_features(spec, features_after)
            if after_value is None:
                continue
            before[target_id] = float(sensor_outputs[target_id])
            after[target_id] = float(after_value)

        condition = AfterCondition(
            targets=targets,
            goal_delta=goal_delta,
            min_similarity=float(node.meta.get("min_similarity", 0.0)),
            max_error=node.meta.get("max_error"),
        )
        match = condition.evaluate(before, after)
        blackboard.setdefault("triplet_after_matches", {})[node.nid] = {
            "matched": match.matched,
            "score": match.score,
            "details": match.details,
        }
        node.meta["last_after_match"] = {
            "matched": match.matched,
            "score": match.score,
            "details": match.details,
        }
        return True, bool(match.matched)

    return Node(
        nid=actual_id,
        ntype=NodeType.TERMINAL,
        predicate=predicate,
    )


# Helper functions

def apply_readout(sub_v: np.ndarray, readout_type: str, params: Dict) -> float:
    """Apply sensor readout function"""
    if len(sub_v) == 0:
        return 0.0
        
    if readout_type == "identity":
        if len(sub_v) != 1:
            # Fallback to mean if multiple features
            return float(np.mean(sub_v))
        return float(sub_v[0])
    
    elif readout_type == "sum":
        return float(np.sum(sub_v))
    
    elif readout_type == "mean":
        return float(np.mean(sub_v))
    
    elif readout_type == "min":
        return float(np.min(sub_v))
    
    elif readout_type == "max":
        return float(np.max(sub_v))
    
    elif readout_type == "threshold":
        threshold = params.get("threshold", 0.5)
        return 1.0 if np.mean(sub_v) > threshold else 0.0
    
    else:
        # Default to mean for unknown types
        return float(np.mean(sub_v))


def _apply_spec_to_features(spec: Dict[str, Any], features: np.ndarray) -> float | None:
    """Apply a sensor spec dict to features, returning a scalar or None."""
    readout_type = spec.get("readout_type", "identity")
    feature_mask_keys = spec.get("feature_mask_keys", [])
    readout_params = spec.get("readout_params", {})

    feature_mask = np.zeros(len(features), dtype=bool)
    for key in feature_mask_keys:
        if key.startswith("feature_"):
            idx = int(key.split("_")[1])
            if idx < len(features):
                feature_mask[idx] = True

    if not np.any(feature_mask):
        return None

    sub_v = features[feature_mask]
    try:
        return apply_readout(sub_v, readout_type, readout_params)
    except Exception:
        return None


def _goal_distance_from_values(
    current: Dict[str, float],
    goal_bank: Dict[str, Any] | None,
    normalize: bool = True,
    min_overlap: float = 8,
) -> tuple[float | None, int | None]:
    """Compute min distance to goal prototypes using a values dict (sensor_id -> value)."""
    if not goal_bank or not isinstance(goal_bank, dict):
        return None, None
    goals = goal_bank.get("goals", [])
    if not goals or not current:
        return None, None
    sensor_specs = goal_bank.get("sensor_specs", {}) or {}

    best = None
    best_idx = None
    for idx, entry in enumerate(goals):
        gvals = entry.get("values", {})
        keys = set(current.keys()) & set(gvals.keys())
        if not keys:
            continue
        weights = np.array([
            _goal_weight_for_sensor(k, goal_bank, sensor_specs)
            for k in keys
        ], dtype=np.float32)
        weight_sum = float(np.sum(weights))
        if weight_sum < min_overlap:
            continue
        vec_cur = np.array([current[k] for k in keys], dtype=np.float32)
        vec_goal = np.array([gvals[k] for k in keys], dtype=np.float32)
        if normalize:
            vec_cur = vec_cur / (np.sqrt(np.sum(weights * (vec_cur ** 2))) + 1e-6)
            vec_goal = vec_goal / (np.sqrt(np.sum(weights * (vec_goal ** 2))) + 1e-6)
        diff = vec_cur - vec_goal
        dist = float(np.sqrt(np.sum(weights * (diff ** 2))))
        if best is None or dist < best:
            best = dist
            best_idx = idx
    return best, best_idx


def _promote_goal_from_outputs(blackboard: Dict[str, Any]) -> None:
    """Promote current sensor outputs into the goal bank (local, online)."""
    goal_bank = blackboard.get("goal_bank")
    if not isinstance(goal_bank, dict):
        return
    sensor_outputs = blackboard.get("sensor_outputs", {}) or {}
    sensor_specs = blackboard.get("sensor_specs", {}) or {}
    if not sensor_outputs:
        return

    # Ensure sensor specs/weights are present in goal bank
    goal_specs = goal_bank.setdefault("sensor_specs", {})
    goal_weights = goal_bank.setdefault("sensor_weights", {})
    for sid, spec in sensor_specs.items():
        if sid not in goal_specs:
            goal_specs[sid] = spec
        if sid not in goal_weights:
            w = spec.get("weight")
            try:
                w_val = float(w) if w is not None else 1.0
            except Exception:
                w_val = 1.0
            goal_weights[sid] = w_val

    # Build stable values dict
    values = {sid: float(val) for sid, val in sensor_outputs.items()}

    # Merge with existing goals if close
    goal_eps = float(goal_bank.get("goal_eps", 0.08))
    normalize = bool(blackboard.get("goal_normalize", True))
    min_overlap = float(blackboard.get("goal_min_overlap", 8))
    dist, idx = _goal_distance_from_values(values, goal_bank, normalize=normalize, min_overlap=min_overlap)
    if dist is not None and dist <= goal_eps and idx is not None:
        entry = goal_bank["goals"][idx]
        entry["count"] = int(entry.get("count", 1)) + 1
        return

    # Add new goal entry
    goal_bank.setdefault("goals", []).append({
        "values": values,
        "count": 1,
    })


def _goal_distance_from_features(
    features: np.ndarray,
    goal_bank: Dict[str, Any] | None,
    normalize: bool = True,
    min_overlap: float = 8,
) -> tuple[float | None, float]:
    """Compute min distance to goal prototypes in stable sensor-id space."""
    if not goal_bank or not isinstance(goal_bank, dict):
        return None, 0
    goals = goal_bank.get("goals", [])
    if not goals:
        return None, 0
    sensor_specs = goal_bank.get("sensor_specs", {}) or {}

    current: Dict[str, float] = {}
    for sid_key, spec in sensor_specs.items():
        val = _apply_spec_to_features(spec, features)
        if val is not None:
            current[sid_key] = float(val)

    if not current:
        return None, 0

    best = None
    best_overlap = 0.0
    for entry in goals:
        gvals = entry.get("values", {})
        keys = set(current.keys()) & set(gvals.keys())
        if not keys:
            continue
        weights = np.array([
            _goal_weight_for_sensor(k, goal_bank, sensor_specs)
            for k in keys
        ], dtype=np.float32)
        weight_sum = float(np.sum(weights))
        if weight_sum < min_overlap:
            continue
        vec_cur = np.array([current[k] for k in keys], dtype=np.float32)
        vec_goal = np.array([gvals[k] for k in keys], dtype=np.float32)
        if normalize:
            vec_cur = vec_cur / (np.sqrt(np.sum(weights * (vec_cur ** 2))) + 1e-6)
            vec_goal = vec_goal / (np.sqrt(np.sum(weights * (vec_goal ** 2))) + 1e-6)
        diff = vec_cur - vec_goal
        dist = float(np.sqrt(np.sum(weights * (diff ** 2))))
        if best is None or dist < best:
            best = dist
            best_overlap = weight_sum

    return best, best_overlap


def _goal_weight_for_sensor(
    sensor_id: str,
    goal_bank: Dict[str, Any] | None,
    sensor_specs: Dict[str, Any],
) -> float:
    """Resolve a stable weight for a sensor id (XP-weighted if available)."""
    if isinstance(goal_bank, dict):
        weight_map = goal_bank.get("sensor_weights", {}) or {}
        if sensor_id in weight_map:
            try:
                return float(weight_map[sensor_id])
            except Exception:
                pass
    spec = sensor_specs.get(sensor_id, {}) or {}
    for key in ("weight", "xp"):
        if key in spec and spec[key] is not None:
            try:
                return 1.0 + max(0.0, float(spec[key]))
            except Exception:
                continue
    return 1.0


def cosine_similarity(a: list, b: list) -> float:
    """Compute cosine similarity between two vectors"""
    return terminal_cosine_similarity(a, b)
