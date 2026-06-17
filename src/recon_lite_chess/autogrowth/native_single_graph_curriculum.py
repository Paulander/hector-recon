"""TG26o native ReCoN graph version of the TG26n curriculum.

This module intentionally does not reuse ``SingleGraphKRKNetwork.choose``.
It materializes learned sensor terminals, actuator affordance terminals, SCRIPT
wrappers, and SUB/SUR/POR/RET pairs as a real ``recon_lite.Graph``. Runtime
evaluation uses ``FormalReConEngine`` ticks; the only trainer-side duties are
curriculum scheduling and reward labels.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable, Mapping

import chess

from recon_lite import FormalReConEngine, Graph, LinkType, Node, NodeState, NodeType
from recon_lite_hector.nodes.stem_cell import StemCellState

from .curated_replay_curriculum import _mate2_buckets
from .curated_terminal_curriculum import curated_stage_entries
from .features import validate_learner_record
from .foundation_curriculum import _forced_mate_in_two_first_moves, _mate_moves, _move_reward
from .single_graph_curriculum import SingleGraphCurriculumConfig
from .terminal_substrate import _bucket, _delta_bucket, extract_terminal_feature_vector, terminal_action_feature_keys


ROOT_ID = "tg26o_root"


@dataclass(frozen=True)
class NativeSingleGraphConfig:
    include_symmetries: bool = True
    train_repetitions: int = 5
    continuation_repetitions: int = 2
    eta_m3: float = 0.10
    max_abs_local_weight: float = 1.0
    terminal_score_scale: float = 1.0
    triplet_credit_scale: float = 0.35
    mature_min_abs_weight: float = 0.20
    mate1_threshold: float = 0.98
    mate2_threshold: float = 0.95
    max_ticks: int = 18
    max_samples: int = 32
    indexed_scheduler: bool = True
    tick_feature_terminals: bool = False
    max_mate1_positions: int | None = None
    max_mate2_positions: int | None = None

    @classmethod
    def from_tg26n(cls, config: SingleGraphCurriculumConfig) -> "NativeSingleGraphConfig":
        return cls(
            include_symmetries=config.include_symmetries,
            train_repetitions=config.train_repetitions,
            continuation_repetitions=config.continuation_repetitions,
            eta_m3=config.eta_m3,
            max_abs_local_weight=config.max_abs_local_weight,
            terminal_score_scale=config.terminal_score_scale,
            triplet_credit_scale=config.triplet_credit_scale,
            mature_min_abs_weight=config.triplet_mature_min_abs_weight,
            mate1_threshold=config.mate1_threshold,
            mate2_threshold=config.mate2_threshold,
            max_samples=config.max_samples,
        )


@dataclass(frozen=True)
class NativeSingleGraphResult:
    config: NativeSingleGraphConfig
    dataset: dict[str, Any]
    mate1: dict[str, Any]
    maturation: dict[str, Any]
    mate2: dict[str, Any]
    graph: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26p_native_scheduler.v0",
            "checkpoint": "TG26p_native_scheduler_foundation",
            "config": asdict(self.config),
            "purity_boundary": {
                "native_recon_graph_execution": True,
                "feature_terminals_are_NodeType_TERMINAL": True,
                "feature_terminals_remain_graph_nodes": True,
                "runtime_ticks_individual_feature_terminals": self.config.tick_feature_terminals,
                "actuator_affordances_are_NodeType_TERMINAL": True,
                "triplets_are_SCRIPT_TERMINAL_subgraphs_with_actuator_terminals": True,
                "sub_sur_por_ret_are_real_edges": True,
                "python_batch_scorer_used_for_runtime_choice": False,
                "hardcoded_mate1_handoff": False,
                "stage_labels_learner_visible": False,
                "direct_provider_override": False,
                "runtime_tablebase_or_dtm_move_source": False,
            },
            "dataset": self.dataset,
            "mate1": self.mate1,
            "maturation": self.maturation,
            "mate2": self.mate2,
            "graph": self.graph,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


class NativeReConKRKGraph:
    """A native graph that grows real ReCoN triplet subgraphs."""

    def __init__(self, *, config: NativeSingleGraphConfig) -> None:
        self.config = config
        self.graph = Graph()
        self.graph.add_node(Node(ROOT_ID, NodeType.SCRIPT, meta={
            "origin": "tg26o_native_single_graph",
            "confirm_policy": "or",
            "tier": "mature",
        }))
        self.triplet_ids: set[str] = set()
        self.triplet_nodes: dict[str, set[str]] = {}
        self.triplet_trainable_edges: dict[str, list[Any]] = {}
        self.m3_update_count = 0
        self.m4_event_count = 0
        self.runtime_choice_count = 0
        self.scheduler_stats = {
            "indexed_scheduler_used": self.config.indexed_scheduler,
            "choose_calls": 0,
            "empty_candidate_calls": 0,
            "candidate_triplets_ticked": 0,
            "triplets_skipped_by_index": 0,
            "active_nodes_ticked": 0,
            "feature_terminals_skipped_by_scheduler": 0,
            "full_graph_node_resets_avoided": 0,
            "formal_ticks_run": 0,
        }

    def choose(self, board: chess.Board, *, masked_triplets: set[str] | None = None) -> chess.Move | None:
        audit = self.audit_choice(board, masked_triplets=masked_triplets)
        selected = audit.get("selected_move")
        if selected is None:
            return None
        return chess.Move.from_uci(str(selected))

    def audit_choice(self, board: chess.Board, *, masked_triplets: set[str] | None = None) -> dict[str, Any]:
        legal = {move.uci(): move for move in board.legal_moves}
        if not legal:
            return {
                "selected_move": None,
                "candidate_triplet_count": 0,
                "confirmed_candidate_count": 0,
                "confirmed_candidates": [],
            }
        candidate_triplets = self._candidate_triplets_for_board(board, legal)
        if masked_triplets:
            candidate_triplets = candidate_triplets - masked_triplets
        self.scheduler_stats["choose_calls"] += 1
        self.scheduler_stats["candidate_triplets_ticked"] += len(candidate_triplets)
        self.scheduler_stats["triplets_skipped_by_index"] += max(0, len(self.triplet_ids) - len(candidate_triplets))
        if self.config.indexed_scheduler:
            if not candidate_triplets:
                self.scheduler_stats["empty_candidate_calls"] += 1
                return {
                    "selected_move": None,
                    "candidate_triplet_count": 0,
                    "confirmed_candidate_count": 0,
                    "confirmed_candidates": [],
                }
            active_nodes = self._active_nodes_for_triplets(candidate_triplets)
            self.scheduler_stats["active_nodes_ticked"] += len(active_nodes)
            self.scheduler_stats["full_graph_node_resets_avoided"] += max(0, len(self.graph.nodes) - len(active_nodes))
            self._reset_runtime_states(active_nodes)
        else:
            active_nodes = None
            self._reset_runtime_states()
        env: dict[str, Any] = {"board": board}
        engine = FormalReConEngine(self.graph, validate_pairs=False, record_trace=False)
        engine.request(ROOT_ID)
        engine.run(
            max_ticks=self.config.max_ticks,
            env=env,
            active_nodes=active_nodes,
            until=(
                (lambda _engine: self._candidate_triplets_settled(candidate_triplets))
                if self.config.indexed_scheduler
                else None
            ),
        )
        self.scheduler_stats["formal_ticks_run"] += engine.tick
        candidates = self._confirmed_action_candidates(legal, candidate_triplets if self.config.indexed_scheduler else None)
        if not candidates:
            return {
                "selected_move": None,
                "candidate_triplet_count": len(candidate_triplets),
                "confirmed_candidate_count": 0,
                "confirmed_candidates": [],
            }
        candidates.sort(reverse=True)
        self.runtime_choice_count += 1
        return {
            "selected_move": candidates[0][1],
            "selected_triplet": candidates[0][2],
            "selected_score": round(float(candidates[0][0]), 6),
            "candidate_triplet_count": len(candidate_triplets),
            "confirmed_candidate_count": len(candidates),
            "confirmed_candidates": [
                {"score": round(float(score), 6), "move": move_uci, "triplet_id": triplet_id}
                for score, move_uci, triplet_id in candidates[:16]
            ],
        }

    def train_action_rewards(self, board: chess.Board, *, rewards: Mapping[str, float], stage: str) -> dict[str, int]:
        updates = {"positive": 0, "negative": 0, "neutral": 0}
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            reward = float(rewards.get(move.uci(), 0.0))
            triplet_id = self.ensure_triplet(board, move, stage=stage)
            self._apply_m3(triplet_id, reward=reward)
            if reward > 0.0:
                updates["positive"] += 1
            elif reward < 0.0:
                updates["negative"] += 1
            else:
                updates["neutral"] += 1
        return updates

    def ensure_triplet(self, board: chess.Board, move: chess.Move, *, stage: str) -> str:
        before_keys, action_delta_keys, after_keys = _triplet_keys(board, move)
        triplet_id = _triplet_id(before_keys, action_delta_keys, after_keys)
        if triplet_id in self.triplet_ids:
            return triplet_id

        ids = _TripletNodeIds(triplet_id)
        created_node_ids: set[str] = set()
        for node in (
            Node(ids.triplet, NodeType.SCRIPT, meta=_candidate_meta("SCRIPT", stage, role="triplet", action_uci=move.uci())),
            Node(ids.before_script, NodeType.SCRIPT, meta=_candidate_meta("SCRIPT", stage, role="before_script", action_uci=move.uci())),
            Node(ids.action_script, NodeType.SCRIPT, meta=_candidate_meta("SCRIPT", stage, role="action_script", action_uci=move.uci())),
            Node(ids.after_script, NodeType.SCRIPT, meta=_candidate_meta("SCRIPT", stage, role="after_script", action_uci=move.uci())),
            Node(ids.before_terminal, NodeType.TERMINAL, predicate=_pattern_predicate("before", move.uci(), before_keys), meta=_terminal_meta(stage, "before", move.uci(), before_keys)),
            Node(ids.delta_terminal, NodeType.TERMINAL, predicate=_pattern_predicate("delta", move.uci(), action_delta_keys), meta=_terminal_meta(stage, "delta", move.uci(), action_delta_keys)),
            Node(ids.after_terminal, NodeType.TERMINAL, predicate=_pattern_predicate("after", move.uci(), after_keys), meta=_terminal_meta(stage, "after", move.uci(), after_keys)),
            Node(ids.action, NodeType.TERMINAL, predicate=_action_predicate(move.uci()), meta=_action_meta(stage, move.uci())),
        ):
            self.graph.add_node(node)
            created_node_ids.add(node.nid)

        created_edges: list[Any] = []
        created_edges.extend(self._add_hierarchy_pair(ROOT_ID, ids.triplet, trainable=True, weight=0.0))
        created_edges.extend(self._add_hierarchy_pair(ids.triplet, ids.before_script, trainable=True, weight=0.0))
        created_edges.extend(self._add_hierarchy_pair(ids.triplet, ids.action_script, trainable=True, weight=0.0))
        created_edges.extend(self._add_hierarchy_pair(ids.triplet, ids.after_script, trainable=True, weight=0.0))
        created_edges.extend(self._add_hierarchy_pair(ids.before_script, ids.before_terminal, trainable=True, weight=0.0))
        created_edges.extend(self._add_hierarchy_pair(ids.action_script, ids.delta_terminal, trainable=True, weight=0.0))
        created_edges.extend(self._add_hierarchy_pair(ids.action_script, ids.action, trainable=True, weight=0.0))
        created_edges.extend(self._add_hierarchy_pair(ids.after_script, ids.after_terminal, trainable=True, weight=0.0))
        for role, parent_id, keys in (
            ("before_feature", ids.before_script, before_keys),
            ("delta_feature", ids.action_script, action_delta_keys),
            ("after_feature", ids.after_script, after_keys),
        ):
            for key in keys:
                feature_id = _feature_terminal_id(triplet_id, role, key)
                self.graph.add_node(
                    Node(
                        feature_id,
                        NodeType.TERMINAL,
                        predicate=_single_key_predicate(role, move.uci(), key),
                        meta=_feature_terminal_meta(stage, role, move.uci(), key),
                    )
                )
                created_node_ids.add(feature_id)
                created_edges.extend(self._add_hierarchy_pair(parent_id, feature_id, trainable=True, weight=0.0))
        created_edges.extend(self._add_sequence_pair(ids.before_script, ids.action_script, trainable=True, weight=0.0))
        created_edges.extend(self._add_sequence_pair(ids.action_script, ids.after_script, trainable=True, weight=0.0))
        for node_id in created_node_ids:
            self.graph.nodes[node_id].meta["triplet_id"] = triplet_id
        self.triplet_ids.add(triplet_id)
        self.triplet_nodes[triplet_id] = created_node_ids
        self.triplet_trainable_edges[triplet_id] = created_edges
        return triplet_id

    def mature_existing_graph(self) -> dict[str, Any]:
        matured_nodes = 0
        matured_edges = 0
        for node in self.graph.nodes.values():
            if node.nid == ROOT_ID:
                continue
            if abs(float(node.meta.get("local_weight", 0.0))) >= self.config.mature_min_abs_weight:
                if node.meta.get("tier") != "mature":
                    matured_nodes += 1
                node.meta["tier"] = "mature"
                node.meta["stem_cell_state"] = StemCellState.MATURE.name
                node.meta["mature_reason"] = "native_single_graph_curriculum_stage_completion"
        for edge in self.graph.edges:
            if edge.meta.get("trainable") and abs(float(edge.w)) >= self.config.mature_min_abs_weight:
                if edge.meta.get("tier") != "mature":
                    matured_edges += 1
                edge.meta["tier"] = "mature"
                edge.meta["stem_cell_state"] = StemCellState.MATURE.name
        self.m4_event_count += int(matured_nodes > 0 or matured_edges > 0)
        return {
            "matured_node_count": matured_nodes,
            "matured_edge_count": matured_edges,
            "total_node_count": len(self.graph.nodes),
            "total_edge_count": len(self.graph.edges),
            "m4_event_count": self.m4_event_count,
        }

    def to_dict(self) -> dict[str, Any]:
        node_type_counts: dict[str, int] = {}
        for node in self.graph.nodes.values():
            node_type_counts[node.ntype.name] = node_type_counts.get(node.ntype.name, 0) + 1
        edge_type_counts: dict[str, int] = {}
        for edge in self.graph.edges:
            edge_type_counts[edge.ltype.name] = edge_type_counts.get(edge.ltype.name, 0) + 1
        top_edges = sorted(
            (
                {
                    "src": edge.src,
                    "dst": edge.dst,
                    "type": edge.ltype.name,
                    "weight": round(float(edge.w), 6),
                    "tier": edge.meta.get("tier", "trial"),
                }
                for edge in self.graph.edges
                if edge.meta.get("trainable")
            ),
            key=lambda item: item["weight"],
            reverse=True,
        )
        return {
            "native_recon_graph": True,
            "root_id": ROOT_ID,
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
            "triplet_count": len(self.triplet_ids),
            "node_type_counts": node_type_counts,
            "actuator_terminal_count": sum(
                1 for node in self.graph.nodes.values() if node.meta.get("terminal_kind") == "actuator_affordance"
            ),
            "edge_type_counts": edge_type_counts,
            "formal_pairs_valid": _formal_pairs_valid(self.graph),
            "mature_node_count": sum(1 for node in self.graph.nodes.values() if node.meta.get("tier") == "mature"),
            "mature_edge_count": sum(1 for edge in self.graph.edges if edge.meta.get("tier") == "mature"),
            "m3_update_count": self.m3_update_count,
            "runtime_choice_count": self.runtime_choice_count,
            "scheduler_stats": dict(self.scheduler_stats),
            "top_positive_trainable_edges": top_edges[:24],
            "top_negative_trainable_edges": sorted(top_edges, key=lambda item: item["weight"])[:24],
        }

    def graph_diagnostics(self, *, prune_weight_threshold: float = -0.20) -> dict[str, Any]:
        tier_counts: dict[str, int] = {}
        state_counts: dict[str, int] = {}
        local_weights: list[float] = []
        for node in self.graph.nodes.values():
            tier = str(node.meta.get("tier", "unlabeled"))
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            state_name = str(node.meta.get("stem_cell_state", "UNLABELED"))
            state_counts[state_name] = state_counts.get(state_name, 0) + 1
            if "local_weight" in node.meta:
                local_weights.append(float(node.meta.get("local_weight", 0.0)))
        trainable_edges = [edge for edge in self.graph.edges if edge.meta.get("trainable")]
        edge_weights = [float(edge.w) for edge in trainable_edges]
        saturated_nodes_pos = sum(1 for weight in local_weights if weight >= self.config.max_abs_local_weight)
        saturated_nodes_neg = sum(1 for weight in local_weights if weight <= -self.config.max_abs_local_weight)
        saturated_edges_pos = sum(1 for weight in edge_weights if weight >= self.config.max_abs_local_weight)
        saturated_edges_neg = sum(1 for weight in edge_weights if weight <= -self.config.max_abs_local_weight)
        root_weights: dict[str, float] = {}
        for triplet_id in self.triplet_ids:
            edge = self.graph.get_edge(ROOT_ID, triplet_id, LinkType.SUB)
            if edge is not None:
                root_weights[triplet_id] = float(edge.w)
        prune_candidates = sorted(
            (triplet_id for triplet_id, weight in root_weights.items() if weight <= prune_weight_threshold),
            key=lambda item: root_weights[item],
        )
        equivalent_keys: dict[tuple[str, str, str], int] = {}
        for triplet_id in self.triplet_ids:
            ids = _TripletNodeIds(triplet_id)
            key = (
                str(self.graph.nodes[ids.before_terminal].meta.get("pattern_hash")),
                str(self.graph.nodes[ids.delta_terminal].meta.get("pattern_hash")),
                str(self.graph.nodes[ids.after_terminal].meta.get("pattern_hash")),
            )
            equivalent_keys[key] = equivalent_keys.get(key, 0) + 1
        duplicate_equivalent = sum(count - 1 for count in equivalent_keys.values() if count > 1)
        return {
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
            "triplet_count": len(self.triplet_ids),
            "tier_counts": tier_counts,
            "stem_cell_state_counts": state_counts,
            "dead_node_count": tier_counts.get("dead", 0) + state_counts.get("DEAD", 0),
            "no_op_node_count": sum(1 for weight in local_weights if abs(weight) < 1e-12),
            "trainable_edge_count": len(trainable_edges),
            "no_op_edge_count": sum(1 for weight in edge_weights if abs(weight) < 1e-12),
            "weight_saturation": {
                "node_positive_saturated": saturated_nodes_pos,
                "node_negative_saturated": saturated_nodes_neg,
                "edge_positive_saturated": saturated_edges_pos,
                "edge_negative_saturated": saturated_edges_neg,
                "max_abs_local_weight": self.config.max_abs_local_weight,
            },
            "collapse_indicators": {
                "positive_saturated_total": saturated_nodes_pos + saturated_edges_pos,
                "negative_saturated_total": saturated_nodes_neg + saturated_edges_neg,
                "zero_weight_total": sum(1 for weight in local_weights if abs(weight) < 1e-12)
                + sum(1 for weight in edge_weights if abs(weight) < 1e-12),
            },
            "duplicate_equivalent_triplet_count": duplicate_equivalent,
            "prune_candidate_count": len(prune_candidates),
            "prune_candidate_triplets": prune_candidates[:64],
            "prune_weight_threshold": prune_weight_threshold,
        }

    def triplets_by_stage(self, stage_predicate) -> set[str]:
        selected: set[str] = set()
        for triplet_id in self.triplet_ids:
            stages = {
                str(self.graph.nodes[node_id].meta.get("stage_diagnostic", ""))
                for node_id in self.triplet_nodes.get(triplet_id, set())
            }
            if any(stage_predicate(stage) for stage in stages):
                selected.add(triplet_id)
        return selected

    def _add_hierarchy_pair(self, parent: str, child: str, *, trainable: bool, weight: float) -> list[Any]:
        trainable_edges: list[Any] = []
        self.graph.add_hierarchy_pair(parent, child)
        sub = self.graph.get_edge(parent, child, LinkType.SUB)
        sur = self.graph.get_edge(child, parent, LinkType.SUR)
        if sub is not None:
            sub.w = float(weight)
            sub.meta.update({"trainable": trainable, "tier": "trial", "stem_cell_state": StemCellState.TRIAL.name})
            if trainable:
                trainable_edges.append(sub)
        if sur is not None:
            sur.meta.update({"structural_fixed": True})
        return trainable_edges

    def _add_sequence_pair(self, predecessor: str, successor: str, *, trainable: bool, weight: float) -> list[Any]:
        trainable_edges: list[Any] = []
        self.graph.add_sequence_pair(predecessor, successor)
        por = self.graph.get_edge(predecessor, successor, LinkType.POR)
        ret = self.graph.get_edge(successor, predecessor, LinkType.RET)
        if por is not None:
            por.w = float(weight)
            por.meta.update({"trainable": trainable, "tier": "trial", "stem_cell_state": StemCellState.TRIAL.name})
            if trainable:
                trainable_edges.append(por)
        if ret is not None:
            ret.meta.update({"structural_fixed": True})
        return trainable_edges

    def _apply_m3(self, triplet_id: str, *, reward: float) -> None:
        ids = _TripletNodeIds(triplet_id)
        bounded_reward = max(-1.0, min(1.0, reward))
        node_ids = [
            ids.triplet,
            ids.before_script,
            ids.action_script,
            ids.after_script,
            ids.before_terminal,
            ids.delta_terminal,
            ids.after_terminal,
            ids.action,
        ]
        for node_id in self.triplet_nodes.get(triplet_id, set()):
            node = self.graph.nodes[node_id]
            if node.ntype == NodeType.TERMINAL:
                node_ids.append(node.nid)
        for node_id in node_ids:
            node = self.graph.nodes[node_id]
            node.meta["request_exposures"] = int(node.meta.get("request_exposures", 0)) + 1
            if bounded_reward > 0.0:
                node.meta["confirm_count"] = int(node.meta.get("confirm_count", 0)) + 1
            node.meta["local_weight"] = _bounded(
                float(node.meta.get("local_weight", 0.0)) + self.config.eta_m3 * bounded_reward,
                self.config.max_abs_local_weight,
            )
        for edge in self.triplet_trainable_edges.get(triplet_id, []):
            edge.w = _bounded(float(edge.w) + self.config.eta_m3 * bounded_reward, self.config.max_abs_local_weight)
            self.m3_update_count += 1

    def _reset_runtime_states(self, node_ids: Iterable[str] | None = None) -> None:
        nodes = self.graph.nodes.values() if node_ids is None else (self.graph.nodes[nid] for nid in node_ids if nid in self.graph.nodes)
        for node in nodes:
            node.state = NodeState.INACTIVE
            node.tick_entered = -1

    def _candidate_triplets_for_board(self, board: chess.Board, legal: Mapping[str, chess.Move]) -> set[str]:
        triplets: set[str] = set()
        for move in legal.values():
            triplet_id = _triplet_id(*_triplet_keys(board, move))
            if triplet_id in self.triplet_ids:
                triplets.add(triplet_id)
        return triplets

    def _active_nodes_for_triplets(self, triplet_ids: Iterable[str]) -> set[str]:
        active = {ROOT_ID}
        for triplet_id in triplet_ids:
            for node_id in self.triplet_nodes.get(triplet_id, set()):
                node = self.graph.nodes[node_id]
                if (
                    not self.config.tick_feature_terminals
                    and node.meta.get("role") in {"before_feature", "delta_feature", "after_feature"}
                ):
                    self.scheduler_stats["feature_terminals_skipped_by_scheduler"] += 1
                    continue
                active.add(node_id)
        return active

    def _candidate_triplets_settled(self, triplet_ids: Iterable[str]) -> bool:
        terminal_states = {NodeState.TRUE, NodeState.CONFIRMED, NodeState.FAILED}
        for triplet_id in triplet_ids:
            ids = _TripletNodeIds(triplet_id)
            if self.graph.nodes[ids.triplet].state not in terminal_states:
                return False
            if self.graph.nodes[ids.action].state not in terminal_states:
                return False
        return True

    def _confirmed_action_candidates(
        self,
        legal: Mapping[str, chess.Move],
        triplet_ids: Iterable[str] | None = None,
    ) -> list[tuple[float, str, str]]:
        candidates: list[tuple[float, str, str]] = []
        for triplet_id in (self.triplet_ids if triplet_ids is None else triplet_ids):
            ids = _TripletNodeIds(triplet_id)
            triplet = self.graph.nodes[ids.triplet]
            action = self.graph.nodes[ids.action]
            if triplet.state not in (NodeState.TRUE, NodeState.CONFIRMED):
                continue
            if action.state not in (NodeState.TRUE, NodeState.CONFIRMED):
                continue
            move_uci = str(action.meta["action_uci"])
            if move_uci not in legal:
                continue
            triplet_weight = float(self.graph.get_edge(ROOT_ID, ids.triplet, LinkType.SUB).w)  # type: ignore[union-attr]
            terminal_score, active_count = self._confirmed_terminal_score(triplet_id)
            terminal_score /= max(1, active_count)
            score = self.config.terminal_score_scale * terminal_score + self.config.triplet_credit_scale * triplet_weight
            candidates.append((score, move_uci, triplet_id))
        return candidates

    def _confirmed_terminal_score(self, triplet_id: str) -> tuple[float, int]:
        score = 0.0
        count = 0
        for node in self.graph.nodes.values():
            if node.meta.get("triplet_id") != triplet_id:
                continue
            if node.ntype != NodeType.TERMINAL:
                continue
            if node.meta.get("role") not in {"before_feature", "delta_feature", "after_feature"}:
                continue
            if str(node.meta.get("terminal_key", "")).startswith("action_pattern:"):
                continue
            if node.state not in (NodeState.TRUE, NodeState.CONFIRMED):
                continue
            score += float(node.meta.get("local_weight", 0.0))
            count += 1
        return score, count


@dataclass(frozen=True)
class _TripletNodeIds:
    triplet_id: str

    @property
    def triplet(self) -> str:
        return self.triplet_id

    @property
    def before_script(self) -> str:
        return f"{self.triplet_id}_before_script"

    @property
    def action_script(self) -> str:
        return f"{self.triplet_id}_action_script"

    @property
    def after_script(self) -> str:
        return f"{self.triplet_id}_after_script"

    @property
    def before_terminal(self) -> str:
        return f"{self.triplet_id}_before_terminal"

    @property
    def delta_terminal(self) -> str:
        return f"{self.triplet_id}_delta_terminal"

    @property
    def after_terminal(self) -> str:
        return f"{self.triplet_id}_after_terminal"

    @property
    def action(self) -> str:
        return f"{self.triplet_id}_action"


def run_native_single_graph_curriculum(
    *,
    config: NativeSingleGraphConfig | None = None,
) -> NativeSingleGraphResult:
    cfg = config or NativeSingleGraphConfig()
    entries = curated_stage_entries(include_symmetries=cfg.include_symmetries)
    mate1_fens = _unique(
        entry.fen
        for entry in entries
        if entry.stage_name == "Mate_In_1" and entry.mate_in_one_moves
    )
    buckets = _mate2_buckets(entries)
    mate2_fens = _unique(fen for bucket in buckets for fen in bucket["fens"])
    raw_mate1_count = len(mate1_fens)
    raw_mate2_count = len(mate2_fens)
    if cfg.max_mate1_positions is not None:
        mate1_fens = mate1_fens[: cfg.max_mate1_positions]
    if cfg.max_mate2_positions is not None:
        mate2_fens = mate2_fens[: cfg.max_mate2_positions]
    graph = NativeReConKRKGraph(config=cfg)

    started = perf_counter()
    mate1_training = _train_mate1_stage(graph, mate1_fens, config=cfg)
    mate1_training["duration_seconds"] = round(perf_counter() - started, 6)
    started = perf_counter()
    mate1_eval = _evaluate_mate1_stage(graph, mate1_fens, config=cfg)
    mate1_eval["duration_seconds"] = round(perf_counter() - started, 6)
    started = perf_counter()
    maturation = graph.mature_existing_graph()
    maturation["duration_seconds"] = round(perf_counter() - started, 6)
    started = perf_counter()
    mate2_training = _train_mate2_stage(graph, mate2_fens, config=cfg)
    mate2_training["duration_seconds"] = round(perf_counter() - started, 6)
    started = perf_counter()
    mate2_eval = _evaluate_mate2_stage(graph, mate2_fens, config=cfg)
    mate2_eval["duration_seconds"] = round(perf_counter() - started, 6)
    if mate2_eval["conversion_rate"] >= cfg.mate2_threshold:
        graph.m4_event_count += 1
    decision = {
        "checkpoint_pass": (
            mate1_eval["accuracy"] >= cfg.mate1_threshold
            and mate2_eval["conversion_rate"] >= cfg.mate2_threshold
            and mate2_eval["same_graph_second_move_count"] > 0
            and _formal_pairs_valid(graph.graph)
        ),
        "mate1_threshold": cfg.mate1_threshold,
        "mate2_threshold": cfg.mate2_threshold,
        "m4_mate1_maturation_event_count": maturation["m4_event_count"],
        "m4_mate2_consolidation_event_count": int(mate2_eval["conversion_rate"] >= cfg.mate2_threshold),
        "next_step": (
            "use native graph runtime as early KRK foundation"
            if mate2_eval["conversion_rate"] >= cfg.mate2_threshold
            else "repair native graph parity before edge/fence"
        ),
    }
    return NativeSingleGraphResult(
        config=cfg,
        dataset={
            "source": "src/recon_lite_chess/training/krk_curriculum.py::KRK_STAGES",
            "include_symmetries": cfg.include_symmetries,
            "mate1_position_count": len(mate1_fens),
            "raw_mate1_position_count": raw_mate1_count,
            "max_mate1_positions": cfg.max_mate1_positions,
            "mate2_bucket_count": len(buckets),
            "mate2_position_count": len(mate2_fens),
            "raw_mate2_position_count": raw_mate2_count,
            "max_mate2_positions": cfg.max_mate2_positions,
            "raw_mate2_bucket_entry_count": sum(len(bucket["fens"]) for bucket in buckets),
            "bounded_position_cap_active": (
                cfg.max_mate1_positions is not None or cfg.max_mate2_positions is not None
            ),
        },
        mate1={"training": mate1_training, "evaluation": mate1_eval},
        maturation=maturation,
        mate2={"training": mate2_training, "evaluation": mate2_eval},
        graph=graph.to_dict(),
        decision=decision,
    )


def _train_mate1_stage(
    graph: NativeReConKRKGraph,
    fens: Iterable[str],
    *,
    config: NativeSingleGraphConfig,
) -> dict[str, Any]:
    totals = {"positive": 0, "negative": 0, "neutral": 0}
    records = 0
    for fen in tuple(fens):
        for _ in range(config.train_repetitions):
            board = chess.Board(fen)
            positives = {move.uci() for move in _mate_moves(board)}
            rewards = {move.uci(): _move_reward(board, move, positive_moves=positives) for move in board.legal_moves}
            updates = graph.train_action_rewards(board, rewards=rewards, stage="Mate_In_1")
            records += 1
            for key in totals:
                totals[key] += updates[key]
    return {
        "train_records": records,
        "positive_updates": totals["positive"],
        "negative_updates": totals["negative"],
        "neutral_updates": totals["neutral"],
        "m3_update_count": graph.m3_update_count,
        "node_count": len(graph.graph.nodes),
        "edge_count": len(graph.graph.edges),
        "triplet_count": len(graph.triplet_ids),
    }


def _train_mate2_stage(
    graph: NativeReConKRKGraph,
    fens: Iterable[str],
    *,
    config: NativeSingleGraphConfig,
) -> dict[str, Any]:
    totals = {"positive": 0, "negative": 0, "neutral": 0}
    continuation_records = 0
    first_records = 0
    chain_positive_total = 0
    no_chain_positive = 0
    for fen in tuple(fens):
        board = chess.Board(fen)
        forced = tuple(_forced_mate_in_two_first_moves(board))
        for _ in range(config.continuation_repetitions):
            for first in forced:
                after_first = board.copy(stack=False)
                after_first.push(first)
                for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                    before_mate = after_first.copy(stack=False)
                    before_mate.push(reply)
                    positives = {move.uci() for move in _mate_moves(before_mate)}
                    rewards = {move.uci(): _move_reward(before_mate, move, positive_moves=positives) for move in before_mate.legal_moves}
                    graph.train_action_rewards(before_mate, rewards=rewards, stage="Mate_In_2_continuation_experience")
                    continuation_records += 1
        chain_positives = _same_graph_chain_positive_first_moves(graph, board)
        for _ in range(config.train_repetitions):
            chain_positive_total += len(chain_positives)
            no_chain_positive += int(not chain_positives)
            rewards = {move.uci(): _move_reward(board, move, positive_moves=chain_positives) for move in board.legal_moves}
            updates = graph.train_action_rewards(board, rewards=rewards, stage="Mate_In_2_first_move")
            first_records += 1
            for key in totals:
                totals[key] += updates[key]
    return {
        "first_move_train_records": first_records,
        "continuation_experience_records": continuation_records,
        "chain_positive_total": chain_positive_total,
        "no_chain_positive_record_count": no_chain_positive,
        "positive_updates": totals["positive"],
        "negative_updates": totals["negative"],
        "neutral_updates": totals["neutral"],
        "m3_update_count": graph.m3_update_count,
        "node_count": len(graph.graph.nodes),
        "edge_count": len(graph.graph.edges),
        "triplet_count": len(graph.triplet_ids),
        "continuation_experience_uses_same_native_graph": True,
    }


def _evaluate_mate1_stage(
    graph: NativeReConKRKGraph,
    fens: Iterable[str],
    *,
    config: NativeSingleGraphConfig,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    correct = 0
    for fen in tuple(fens):
        board = chess.Board(fen)
        move = graph.choose(board)
        mates = {item.uci() for item in _mate_moves(board)}
        ok = move is not None and move.uci() in mates
        correct += int(ok)
        rows.append({"fen": fen, "selected": None if move is None else move.uci(), "correct_mates": sorted(mates), "correct": ok})
    total = len(rows)
    return {"position_count": total, "correct_count": correct, "accuracy": 0.0 if total == 0 else correct / total, "samples": rows[:config.max_samples]}


def _evaluate_mate2_stage(
    graph: NativeReConKRKGraph,
    fens: Iterable[str],
    *,
    config: NativeSingleGraphConfig,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    first_success = 0
    converted = 0
    reply_total = 0
    reply_mated = 0
    same_graph_second_move_count = 0
    for fen in tuple(fens):
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        first = graph.choose(board)
        first_ok = first is not None and first.uci() in forced
        first_success += int(first_ok)
        all_replies_mated = False
        reply_rows: list[dict[str, Any]] = []
        if first is not None:
            after_first = board.copy(stack=False)
            after_first.push(first)
            all_replies_mated = True
            for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                before_mate = after_first.copy(stack=False)
                before_mate.push(reply)
                second = graph.choose(before_mate)
                mates = {move.uci() for move in _mate_moves(before_mate)}
                ok = second is not None and second.uci() in mates
                reply_total += 1
                reply_mated += int(ok)
                same_graph_second_move_count += int(second is not None)
                all_replies_mated = all_replies_mated and ok
                reply_rows.append({
                    "black_reply": reply.uci(),
                    "native_graph_selected_second": None if second is None else second.uci(),
                    "correct_mates": sorted(mates),
                    "mated": ok,
                })
        converted += int(first_ok and all_replies_mated)
        rows.append({
            "fen": fen,
            "native_graph_selected_first": None if first is None else first.uci(),
            "forced_first_moves": sorted(forced),
            "first_move_success": first_ok,
            "all_replies_mated_by_native_graph": all_replies_mated,
            "reply_checks": reply_rows[:8],
        })
    total = len(rows)
    return {
        "position_count": total,
        "first_move_success_count": first_success,
        "first_move_success_rate": 0.0 if total == 0 else first_success / total,
        "conversion_count": converted,
        "conversion_rate": 0.0 if total == 0 else converted / total,
        "native_graph_reply_mate_rate": 0.0 if reply_total == 0 else reply_mated / reply_total,
        "same_graph_second_move_count": same_graph_second_move_count,
        "hardcoded_mate1_handoff": False,
        "samples": rows[:config.max_samples],
    }


def _same_graph_chain_positive_first_moves(graph: NativeReConKRKGraph, board: chess.Board) -> set[str]:
    positives: set[str] = set()
    for first in sorted(board.legal_moves, key=lambda item: item.uci()):
        if _mate_moves(board):
            continue
        after_first = board.copy(stack=False)
        after_first.push(first)
        replies = list(after_first.legal_moves)
        if not replies:
            continue
        all_replies_mated = True
        for reply in replies:
            before_mate = after_first.copy(stack=False)
            before_mate.push(reply)
            second = graph.choose(before_mate)
            mates = {move.uci() for move in _mate_moves(before_mate)}
            if second is None or second.uci() not in mates:
                all_replies_mated = False
                break
        if all_replies_mated:
            positives.add(first.uci())
    return positives


def _candidate_meta(node_type: str, stage: str, *, role: str, action_uci: str) -> dict[str, Any]:
    return {
        "origin": "tg26o_native_single_graph",
        "node_type": node_type,
        "role": role,
        "action_uci": action_uci,
        "tier": "trial",
        "stem_cell_state": StemCellState.TRIAL.name,
        "stage_diagnostic": stage,
        "stage_label_learner_visible": False,
        "local_weight": 0.0,
        "request_exposures": 0,
        "confirm_count": 0,
    }


def _terminal_meta(stage: str, role: str, action_uci: str, keys: tuple[str, ...]) -> dict[str, Any]:
    payload = _candidate_meta("TERMINAL", stage, role=role, action_uci=action_uci)
    payload.update({
        "pattern_key_count": len(keys),
        "pattern_hash": _hash_keys(keys),
    })
    return payload


def _action_meta(stage: str, action_uci: str) -> dict[str, Any]:
    payload = _candidate_meta("TERMINAL", stage, role="action_affordance", action_uci=action_uci)
    payload["terminal_kind"] = "actuator_affordance"
    payload["environment_affordance"] = True
    payload["actuator_terminal"] = True
    payload["chooses_move_directly"] = False
    return payload


def _feature_terminal_meta(stage: str, role: str, action_uci: str, key: str) -> dict[str, Any]:
    payload = _candidate_meta("TERMINAL", stage, role=role, action_uci=action_uci)
    payload.update({
        "terminal_key": key,
        "pattern_hash": _hash_keys((key,)),
    })
    return payload


def _pattern_predicate(role: str, action_uci: str, expected_keys: tuple[str, ...]):
    expected = frozenset(expected_keys)

    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        board = env["board"]
        move = chess.Move.from_uci(action_uci)
        if move not in board.legal_moves:
            node.activation.value = 0.0
            return True, False
        before_keys, action_delta_keys, after_keys = _triplet_keys(board, move)
        actual = {
            "before": frozenset(before_keys),
            "delta": frozenset(action_delta_keys),
            "after": frozenset(after_keys),
        }[role]
        success = expected == actual
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _single_key_predicate(role: str, action_uci: str, expected_key: str):
    key_role = {
        "before_feature": "before",
        "delta_feature": "delta",
        "after_feature": "after",
    }[role]

    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        board = env["board"]
        move = chess.Move.from_uci(action_uci)
        if move not in board.legal_moves:
            node.activation.value = 0.0
            return True, False
        before_keys, action_delta_keys, after_keys = _triplet_keys(board, move)
        actual = {
            "before": before_keys,
            "delta": action_delta_keys,
            "after": after_keys,
        }[key_role]
        success = expected_key in actual
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _action_predicate(action_uci: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        board = env["board"]
        move = chess.Move.from_uci(action_uci)
        success = move in board.legal_moves
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _triplet_keys(board: chess.Board, move: chess.Move) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    after = board.copy(stack=False)
    after.push(move)
    before_features = extract_terminal_feature_vector(board)
    after_features = extract_terminal_feature_vector(after)
    before_keys = tuple(f"before_terminal:{key}={_bucket(value)}" for key, value in sorted(before_features.items()))
    after_keys = tuple(f"after_terminal:{key}={_bucket(value)}" for key, value in sorted(after_features.items()))
    action_delta_keys = [
        key
        for key, _scale in terminal_action_feature_keys(board, move)
        if key.startswith("action_pattern:")
    ]
    action_delta_keys.extend(_native_precise_action_keys(board, move))
    for key in sorted(before_features.keys() & after_features.keys()):
        action_delta_keys.append(f"delta_terminal:{key}={_delta_bucket(after_features[key] - before_features[key])}")
    validate_learner_record([*before_keys, *action_delta_keys, *after_keys])
    return before_keys, tuple(action_delta_keys), after_keys


def _native_precise_action_keys(board: chess.Board, move: chess.Move) -> list[str]:
    piece = board.piece_at(move.from_square)
    return [
        f"native_action_exact:piece_type={0 if piece is None else int(piece.piece_type)}",
        f"native_action_exact:from_file={chess.square_file(move.from_square)}",
        f"native_action_exact:from_rank={chess.square_rank(move.from_square)}",
        f"native_action_exact:to_file={chess.square_file(move.to_square)}",
        f"native_action_exact:to_rank={chess.square_rank(move.to_square)}",
    ]


def _triplet_id(before_keys: tuple[str, ...], action_delta_keys: tuple[str, ...], after_keys: tuple[str, ...]) -> str:
    digest = _hash_keys((*before_keys, *action_delta_keys, *after_keys))[:16]
    return f"tg26o_triplet_{digest}"


def _feature_terminal_id(triplet_id: str, role: str, key: str) -> str:
    digest = _hash_keys((triplet_id, role, key))[:16]
    return f"{triplet_id}_{role}_{digest}"


def _hash_keys(keys: tuple[str, ...]) -> str:
    return hashlib.sha1("\n".join(keys).encode("utf-8")).hexdigest()


def _bounded(value: float, max_abs: float) -> float:
    return max(-max_abs, min(max_abs, value))


def _formal_pairs_valid(graph: Graph) -> bool:
    try:
        graph.validate_formal_pairs()
    except ValueError:
        return False
    return True


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))
