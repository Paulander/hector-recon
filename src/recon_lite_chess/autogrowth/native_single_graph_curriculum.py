"""TG26o native ReCoN graph version of the TG26n curriculum.

This module intentionally does not reuse ``SingleGraphKRKNetwork.choose``.
It materializes learned sensor terminals, actuator affordance terminals, SCRIPT
wrappers, and SUB/SUR/POR/RET pairs as a real ``recon_lite.Graph``. Runtime
evaluation uses ``FormalReConEngine`` ticks; the only trainer-side duties are
curriculum scheduling and reward labels.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
import copy
import hashlib
import json
import math
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable, Mapping

import chess

from recon_lite import (
    AnonymousChoiceGenome,
    AnonymousChoiceOption,
    FormalReConEngine,
    Graph,
    LinkType,
    Node,
    NodeState,
    NodeType,
)
from recon_lite_hector.nodes.stem_cell import StemCellState, StemCellTerminal

from .curated_replay_curriculum import _mate2_buckets
from .curated_terminal_curriculum import curated_stage_entries
from .features import validate_learner_record
from .foundation_curriculum import _forced_mate_in_two_first_moves, _mate_moves, _move_reward
from .single_graph_curriculum import SingleGraphCurriculumConfig
from .terminal_substrate import _bucket, _delta_bucket, extract_terminal_feature_vector, terminal_action_feature_keys


ROOT_ID = "tg26o_root"
_TRANSIENT_NODE_META_KEYS = frozenset({
    "activation_count",
    "choice_selected",
    "choice_selected_child",
    "emitted_actuator_identity",
})


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
    key_mode: str = "exact"
    prototype_distance_threshold: int = 12
    max_prototype_candidates_per_move: int = 3
    max_prototype_scan_triplets: int = 256
    shared_feature_atoms: bool = False
    shared_projection_atoms: bool = False
    include_grouped_cache_terminals: bool = True
    shared_atom_min_overlap: int = 2
    max_shared_atom_candidates_per_choice: int = 12
    prune_redundant_exact_terminals: bool = False
    score_action_pattern_atoms: bool = False
    score_hierarchy_edge_weights: bool = False
    terminal_score_normalization: str = "mean"
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
class NativeLocalTrainingDecision:
    """One graph-local training action selected through anonymous emission.

    ``source`` identifies the best already-confirmed native candidate that
    supplied the pre-emission value.  It is deliberately kept separate from
    ``triplet_id``: the latter is the exact local triplet emitted for this
    board/action and may be newly materialized.  ``prediction`` is the
    pre-emission native raw value used by TD (never the exploration bonus),
    while ``exact_confirmation_score_raw`` records the post-emission exact
    confirmation independently.  ``policy_supported`` is stricter than legal
    emission: it is true only when a persistent, formally confirmed native
    source supplied the pre-emission value.  Training may explore an
    unsupported legal pattern after materializing it; read-only evaluation
    must abstain when this field is false.
    """

    move_uci: str
    triplet_id: str
    pattern_id: str
    source: str | None
    prediction: float
    confirmed: bool
    policy_supported: bool
    raw_value: float
    normalized_value: float
    exploration_bonus: float
    activation: float
    pattern_exposure: int
    total_current_pattern_exposures: int
    alias_index: int
    alias_group_size: int
    source_move_uci: str | None
    source_score_raw: float | None
    exact_confirmation_score_raw: float | None
    prediction_source: str
    formal_ticks: int
    materialized_after_emission: bool
    audit_candidate_count: int
    pattern_count: int

    @property
    def move(self) -> chess.Move:
        """Return the emitted legal action for legacy tuple-style callers."""

        return chess.Move.from_uci(self.move_uci)

    @property
    def selected_move(self) -> str:
        return self.move_uci

    @property
    def selected_triplet(self) -> str:
        return self.triplet_id

    @property
    def graph_prediction(self) -> float:
        return self.prediction

    @property
    def exact_prediction(self) -> float | None:
        return self.exact_confirmation_score_raw

    @property
    def selected_score_raw(self) -> float:
        return self.prediction

    @property
    def selected_score(self) -> float:
        return round(self.prediction, 6)

    @property
    def source_triplet_id(self) -> str | None:
        return self.source

    def __iter__(self):
        """Allow compatibility unpacking as ``move, id, confirmed, value``."""

        yield self.move
        yield self.triplet_id
        yield self.confirmed
        yield self.prediction

    def to_manifest(self) -> dict[str, Any]:
        """Return a JSON-safe decision manifest, including explicit aliases."""

        payload = asdict(self)
        payload.update({
            "selected_move": self.move_uci,
            "selected_triplet": self.triplet_id,
            "graph_prediction": float(self.prediction),
            "selected_score_raw": float(self.prediction),
            "selected_score": round(float(self.prediction), 6),
        })
        return payload

    def to_dict(self) -> dict[str, Any]:
        """Compatibility alias for callers that use result-style records."""

        return self.to_manifest()


# The shorter name is useful to callers that do not need the module prefix;
# retaining one concrete dataclass keeps the snapshot/type identity stable.
LocalTrainingDecision = NativeLocalTrainingDecision


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
            "confirm_policy": "k_of_n",
            "confirm_k": 1,
            # Root-level request count is the graph-owned total used by the
            # local UCB-style action selector.  It is incremented only after
            # an anonymous choice has emitted a legal actuator, so read-only
            # audits/queries cannot change exposure statistics.
            "request_exposures": 0,
            "tier": "mature",
        }))
        self.triplet_ids: set[str] = set()
        self.triplet_nodes: dict[str, set[str]] = {}
        self.triplet_trainable_edges: dict[str, list[Any]] = {}
        self.triplet_pattern_key_cache: dict[str, set[str]] = {}
        self.shared_atom_ids_by_key: dict[tuple[str, str], str] = {}
        self.shared_atom_triplets: dict[str, set[str]] = {}
        self.shared_atom_key_by_id: dict[str, tuple[str, str]] = {}
        self.pruned_terminal_ids: set[str] = set()
        self.pruned_triplet_ids: set[str] = set()
        self.frozen_policy_triplet_ids: frozenset[str] = frozenset()
        self.frozen_policy_token: str | None = None
        self.composite_cells: dict[str, StemCellTerminal] = {}
        self.composite_member_ids: dict[str, tuple[str, ...]] = {}
        self.composite_triplets: dict[str, set[str]] = {}
        self.composite_node_by_triplet: dict[tuple[str, str], str] = {}
        self.disabled_composite_ids: set[str] = set()
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
            "prototype_distance_evaluations": 0,
            "prototype_scan_truncated_calls": 0,
            "shared_atom_retrieval_calls": 0,
            "shared_atom_retrieved_triplets": 0,
            "shared_atom_candidate_pairs_before_cap": 0,
            "shared_atom_candidate_pairs_after_cap": 0,
        }

    def __deepcopy__(self, memo: dict[int, Any]) -> "NativeReConKRKGraph":
        """Clone once for experimental arms without invoking pickle sanitization."""

        restored = self.__class__.__new__(self.__class__)
        memo[id(self)] = restored
        for key, value in self.__dict__.items():
            setattr(restored, key, copy.deepcopy(value, memo))
        return restored

    def canonical_semantic_manifest(self) -> dict[str, Any]:
        """Return the complete process-stable learned/structural graph state.

        Frame-local node activation and diagnostic scheduler counters are
        intentionally absent.  Ordered graph rows, behaviorally active
        adjacency indexes, graph-owned retrieval indexes, and trainable-edge
        aliases are all bound explicitly.
        """

        edge_ordinals = {
            id(edge): ordinal for ordinal, edge in enumerate(self.graph.edges)
        }
        edge_by_key_rows = []
        for (src, dst, ltype), edge in self.graph.edge_by_key.items():
            ordinal = edge_ordinals.get(id(edge))
            if ordinal is None or (
                edge.src, edge.dst, edge.ltype
            ) != (src, dst, ltype):
                raise ValueError(
                    "native graph edge index is detached or inconsistent"
                )
            edge_by_key_rows.append((src, dst, ltype.name, ordinal))

        trainable_rows: dict[str, list[tuple[str, str, str, int]]] = {}
        for triplet_id, edges in sorted(self.triplet_trainable_edges.items()):
            rows: list[tuple[str, str, str, int]] = []
            for edge in edges:
                ordinal = edge_ordinals.get(id(edge))
                if ordinal is None:
                    raise ValueError(
                        "trainable-edge index is detached from graph edges"
                    )
                rows.append((edge.src, edge.dst, edge.ltype.name, ordinal))
            trainable_rows[triplet_id] = rows

        return {
            "schema": "native_recon_krk_semantic_state.v1",
            "config": asdict(self.config),
            "graph": {
                "nodes": [
                    {
                        "id": node_id,
                        "node_nid": node.nid,
                        "type": node.ntype.name,
                        "meta": {
                            key: copy.deepcopy(value)
                            for key, value in node.meta.items()
                            if key not in _TRANSIENT_NODE_META_KEYS
                        },
                    }
                    for node_id, node in self.graph.nodes.items()
                ],
                "edges": [
                    {
                        "src": edge.src,
                        "dst": edge.dst,
                        "type": edge.ltype.name,
                        "weight": float(edge.w),
                        "meta": copy.deepcopy(edge.meta),
                    }
                    for edge in self.graph.edges
                ],
                "edge_by_key": edge_by_key_rows,
                "out": [
                    (src, ltype.name, list(destinations))
                    for (src, ltype), destinations in self.graph.out.items()
                ],
                "inc": [
                    (dst, ltype.name, list(sources))
                    for (dst, ltype), sources in self.graph.inc.items()
                ],
                "parent": [
                    (node_id, parent_id)
                    for node_id, parent_id in self.graph.parent.items()
                ],
                "parents_fanin": [
                    (node_id, list(parent_ids))
                    for node_id, parent_ids
                    in self.graph.parents_fanin.items()
                ],
            },
            "triplet_ids": sorted(self.triplet_ids),
            "triplet_nodes": {
                key: sorted(value)
                for key, value in sorted(self.triplet_nodes.items())
            },
            "triplet_trainable_edges": trainable_rows,
            "triplet_pattern_key_cache": {
                key: sorted(value)
                for key, value
                in sorted(self.triplet_pattern_key_cache.items())
            },
            "shared_atom_ids_by_key": sorted(
                (str(role), str(pattern_key), atom_id)
                for (role, pattern_key), atom_id
                in self.shared_atom_ids_by_key.items()
            ),
            "shared_atom_triplets": {
                key: sorted(value)
                for key, value in sorted(self.shared_atom_triplets.items())
            },
            "shared_atom_key_by_id": sorted(
                (atom_id, str(role), str(pattern_key))
                for atom_id, (role, pattern_key)
                in self.shared_atom_key_by_id.items()
            ),
            "pruned_terminal_ids": sorted(self.pruned_terminal_ids),
            "pruned_triplet_ids": sorted(self.pruned_triplet_ids),
            "frozen_policy_triplet_ids": sorted(
                self.frozen_policy_triplet_ids
            ),
            "frozen_policy_token": self.frozen_policy_token,
            "composite_cells": {
                key: cell.to_dict()
                for key, cell in sorted(self.composite_cells.items())
            },
            "composite_member_ids": {
                key: list(value)
                for key, value in sorted(self.composite_member_ids.items())
            },
            "composite_triplets": {
                key: sorted(value)
                for key, value in sorted(self.composite_triplets.items())
            },
            "composite_node_by_triplet": sorted(
                (composite_id, triplet_id, node_id)
                for (composite_id, triplet_id), node_id
                in self.composite_node_by_triplet.items()
            ),
            "disabled_composite_ids": sorted(self.disabled_composite_ids),
            "m3_update_count": int(self.m3_update_count),
            "m4_event_count": int(self.m4_event_count),
        }

    def normalize_inference_runtime(self) -> None:
        """Canonicalize frame-local state without touching learned evidence."""

        for node in self.graph.nodes.values():
            node.state = NodeState.INACTIVE
            node.tick_entered = -1
            node.activation.reset(0.0)
            for key in (
                "emitted_actuator_identity",
                "choice_selected_child",
                "choice_selected",
            ):
                node.meta.pop(key, None)
        self.runtime_choice_count = 0
        self.triplet_pattern_key_cache = {}
        for key, value in tuple(self.scheduler_stats.items()):
            if key == "indexed_scheduler_used":
                self.scheduler_stats[key] = bool(self.config.indexed_scheduler)
            elif isinstance(value, (int, float)):
                self.scheduler_stats[key] = 0

    def frame_runtime_copy(self) -> "NativeReConKRKGraph":
        """Return a deep-isolated policy runtime for exactly one frame."""

        runtime = copy.deepcopy(self)
        runtime.normalize_inference_runtime()
        return runtime

    def __getstate__(self) -> dict[str, Any]:
        """Return an exact snapshot state without unpickleable predicate closures."""

        # Copy the complete state in one memoized operation.  In particular,
        # ``triplet_trainable_edges`` must continue to reference the same Edge
        # objects as ``graph.edges`` after a round trip; copying only ``graph``
        # would serialize a second, detached set of trainable edges.
        state = copy.deepcopy(self.__dict__)
        graph = state["graph"]
        for node in graph.nodes.values():
            node.predicate = None
        state["snapshot_schema_version"] = "native_recon_krk_graph.v1"
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        schema = state.pop("snapshot_schema_version", None)
        if schema != "native_recon_krk_graph.v1":
            raise ValueError(f"unsupported native graph snapshot schema: {schema!r}")
        self.__dict__.update(state)
        # v1 snapshots predate local-choice cap telemetry.  These counters are
        # diagnostic only, so a missing field resumes at zero without changing
        # learned graph semantics.
        for key in (
            "shared_atom_candidate_pairs_before_cap",
            "shared_atom_candidate_pairs_after_cap",
        ):
            self.scheduler_stats.setdefault(key, 0)
        self._rebind_triplet_trainable_edges()
        self._validate_derived_graph_indexes()
        self._restore_runtime_predicates()

    def _rebind_triplet_trainable_edges(self) -> None:
        """Restore and verify the trainable-edge index's object aliases.

        Snapshots written by the original v1 serializer contain value-equal
        detached Edge objects in ``triplet_trainable_edges``.  Rebinding them
        on load is deterministic because the native graph forbids duplicate
        directed/link-type edge identities.
        """

        canonical_by_key: dict[tuple[str, str, Any], Any] = {}
        for edge in self.graph.edges:
            key = (edge.src, edge.dst, edge.ltype)
            if key in canonical_by_key:
                raise ValueError(
                    "native graph snapshot has duplicate edge identity"
                )
            if self.graph.edge_by_key.get(key) is not edge:
                raise ValueError(
                    "native graph edge index does not reference canonical edge"
                )
            canonical_by_key[key] = edge

        rebound: dict[str, list[Any]] = {}
        for triplet_id, indexed_edges in self.triplet_trainable_edges.items():
            rebound_edges: list[Any] = []
            for indexed in indexed_edges:
                key = (indexed.src, indexed.dst, indexed.ltype)
                canonical = canonical_by_key.get(key)
                if canonical is None:
                    raise ValueError(
                        "trainable-edge index references an absent graph edge"
                    )
                if indexed.w != canonical.w or indexed.meta != canonical.meta:
                    raise ValueError(
                        "trainable-edge index differs from canonical graph edge"
                    )
                rebound_edges.append(canonical)
            rebound[str(triplet_id)] = rebound_edges
        self.triplet_trainable_edges = rebound

    def _validate_derived_graph_indexes(self) -> None:
        expected_out: dict[tuple[str, Any], list[str]] = {}
        expected_inc: dict[tuple[str, Any], list[str]] = {}
        expected_parent = {node_id: None for node_id in self.graph.nodes}
        expected_fanin = {
            node_id: []
            for node_id, node in self.graph.nodes.items()
            if node.ntype is NodeType.TERMINAL
        }
        expected_edge_by_key: dict[tuple[str, str, Any], Any] = {}
        if any(
            node.nid != node_id
            for node_id, node in self.graph.nodes.items()
        ):
            raise ValueError("native graph node index differs from node identity")
        for edge in self.graph.edges:
            if edge.src not in self.graph.nodes or edge.dst not in self.graph.nodes:
                raise ValueError("native graph edge references an absent node")
            key = (edge.src, edge.dst, edge.ltype)
            if key in expected_edge_by_key:
                raise ValueError("native graph has duplicate edge identity")
            expected_edge_by_key[key] = edge
            expected_out.setdefault((edge.src, edge.ltype), []).append(edge.dst)
            expected_inc.setdefault((edge.dst, edge.ltype), []).append(edge.src)
            if edge.ltype is not LinkType.SUB:
                continue
            destination = self.graph.nodes[edge.dst]
            if destination.ntype is NodeType.TERMINAL:
                expected_fanin[edge.dst].append(edge.src)
                if expected_parent[edge.dst] is None:
                    expected_parent[edge.dst] = edge.src
            else:
                if expected_parent[edge.dst] is not None:
                    raise ValueError(
                        "native graph SCRIPT has multiple SUB parents"
                    )
                expected_parent[edge.dst] = edge.src

        if (
            self.graph.out != expected_out
            or self.graph.inc != expected_inc
            or self.graph.parent != expected_parent
            or self.graph.parents_fanin != expected_fanin
            or set(self.graph.edge_by_key) != set(expected_edge_by_key)
            or any(
                self.graph.edge_by_key[key] is not edge
                for key, edge in expected_edge_by_key.items()
            )
        ):
            raise ValueError("native graph derived indexes are inconsistent")

    def _restore_runtime_predicates(self) -> None:
        """Rebuild generic runtime predicates solely from persisted node metadata."""

        for node in self.graph.nodes.values():
            if node.ntype != NodeType.TERMINAL:
                continue
            role = str(node.meta.get("role", ""))
            action_uci = str(node.meta.get("action_uci", "0000"))
            if node.meta.get("terminal_kind") == "actuator_affordance":
                node.predicate = _action_predicate(action_uci)
            elif node.meta.get("grouped_cache_terminal"):
                pattern_role = {
                    "before_feature": "before",
                    "delta_feature": "delta",
                    "after_feature": "after",
                }.get(role, role)
                node.predicate = _pattern_predicate(
                    pattern_role,
                    action_uci,
                    tuple(str(key) for key in node.meta.get("pattern_keys", ())),
                    self.config.key_mode,
                    self.config.prototype_distance_threshold,
                )
            elif node.meta.get("shared_feature_atom"):
                node.predicate = _shared_atom_predicate(
                    role,
                    str(node.meta["terminal_key"]),
                    self.config.key_mode,
                )
            elif role in {"before_feature", "delta_feature", "after_feature"}:
                node.predicate = _single_key_predicate(
                    role,
                    action_uci,
                    str(node.meta["terminal_key"]),
                    self.config.key_mode,
                    self.config.prototype_distance_threshold,
                )
            elif node.predicate is None:
                raise ValueError(
                    f"cannot restore predicate for terminal {node.nid!r} role={role!r}"
                )

    def choose(self, board: chess.Board, *, masked_triplets: set[str] | None = None) -> chess.Move | None:
        audit = self.audit_choice(board, masked_triplets=masked_triplets)
        selected = audit.get("selected_move")
        if selected is None:
            return None
        return chess.Move.from_uci(str(selected))

    def choose_local_training_action(
        self,
        board: chess.Board,
        stage_diagnostic: str,
    ) -> NativeLocalTrainingDecision:
        """Emit one exploratory action and grow only its exact branch."""

        decision = self._choose_local_action(
            board,
            stage_diagnostic=stage_diagnostic,
            exploration_enabled=True,
            materialize_emitted=True,
        )
        if decision is None:
            raise AssertionError("exploratory local choice produced no decision")
        return decision

    def choose_local_policy_action(
        self,
        board: chess.Board,
    ) -> NativeLocalTrainingDecision | None:
        """Emit the learned local policy or abstain without native support.

        Runtime terminal states and scheduler counters remain diagnostic; no
        node/edge, exposure, or weight is created or changed by this query.
        Unsupported novel patterns do not enter policy competition, so their
        zero baseline cannot suppress a supported negative-valued option.
        """

        return self._choose_local_action(
            board,
            stage_diagnostic="read_only_local_policy",
            exploration_enabled=False,
            materialize_emitted=False,
        )

    def _choose_local_action(
        self,
        board: chess.Board,
        *,
        stage_diagnostic: str,
        exploration_enabled: bool,
        materialize_emitted: bool,
    ) -> NativeLocalTrainingDecision | None:
        """Choose one R1 training action from graph-local pattern competition.

        The read-only audit runs before any new triplet is grown.  Every legal
        move receives an exact local-pattern identity, including patterns with
        no current native source (raw value zero).  A fresh anonymous choice
        graph then emits one actuator.  Only that emitted move is materialized
        and confirmed, which keeps exploration outcome-blind and prevents a
        pre-emission ``ensure_triplet`` call from changing the competition.
        """

        legal = {
            move.uci(): move
            for move in sorted(board.legal_moves, key=lambda item: item.uci())
        }
        if not legal:
            raise ValueError("training position has no legal action")

        full_candidates = self._full_audit_candidates(board, legal)

        # A generalized/prototype source can offer more than one native
        # candidate for a move.  Keep the strongest source deterministically,
        # independently of the audit's compact top-16 reporting view.
        best_by_move: dict[str, tuple[float, str]] = {}
        for score, move_uci, source_triplet_id in full_candidates:
            if move_uci not in legal or not math.isfinite(float(score)):
                continue
            candidate = (float(score), str(source_triplet_id))
            previous = best_by_move.get(move_uci)
            if previous is None or candidate[0] > previous[0] or (
                candidate[0] == previous[0] and candidate[1] < previous[1]
            ):
                best_by_move[move_uci] = candidate

        moves_by_pattern: dict[str, list[str]] = {}
        for move_uci, move in legal.items():
            # This is intentionally the canonical local identity used by both
            # grouping and post-emission parity checks.  It contains no FEN,
            # epoch, position hash, or external action/oracle label.
            pattern_id = _triplet_id(
                *_triplet_keys(board, move, key_mode=self.config.key_mode)
            )
            moves_by_pattern.setdefault(pattern_id, []).append(move_uci)

        pattern_rows: list[dict[str, Any]] = []
        for pattern_id in sorted(moves_by_pattern):
            member_moves = tuple(sorted(moves_by_pattern[pattern_id]))
            member_candidates = [
                (best_by_move[move_uci][0], move_uci, best_by_move[move_uci][1])
                for move_uci in member_moves
                if move_uci in best_by_move
            ]
            member_candidates.sort(
                key=lambda row: (-float(row[0]), str(row[1]), str(row[2]))
            )
            best_member = member_candidates[0] if member_candidates else None
            raw_value = 0.0 if best_member is None else float(best_member[0])
            source_move_uci = None if best_member is None else str(best_member[1])
            source_triplet_id = None if best_member is None else str(best_member[2])
            pattern_exposure = self._local_pattern_exposure(
                pattern_id,
            )
            normalized_value = raw_value / (1.0 + abs(raw_value))
            alias_index = pattern_exposure % max(1, len(member_moves))
            pattern_rows.append({
                "pattern_id": pattern_id,
                "member_moves": member_moves,
                "representative_move_uci": member_moves[alias_index],
                "alias_index": alias_index,
                "alias_group_size": len(member_moves),
                "raw_value": raw_value,
                "normalized_value": normalized_value,
                "pattern_exposure": pattern_exposure,
                "source": source_triplet_id,
                "source_move_uci": source_move_uci,
                "source_score_raw": None if best_member is None else raw_value,
            })

        # Exploration is local to the alternatives active in this choice.
        # A global graph-root counter made novelty pressure grow because of
        # unrelated positions and could prevent a credited pattern from ever
        # being revisited.  This is the ordinary UCB local-population term:
        # each option reads only its own exposure and the summed exposures of
        # its present competitors.  The harness supplies no action ordering.
        total_exposures = sum(
            int(row["pattern_exposure"]) for row in pattern_rows
        )
        for row in pattern_rows:
            pattern_exposure = int(row["pattern_exposure"])
            if not exploration_enabled:
                exploration_bonus = 0.0
            elif pattern_exposure == 0:
                # A never-tried local alternative has maximal bounded novelty.
                # This also gives the formal choice graph a positive signal at
                # a genuinely empty start without consulting a global clock.
                exploration_bonus = 1.0
            else:
                exploration_bonus = min(
                    1.0,
                    math.sqrt(
                        max(
                            0.0,
                            2.0
                            * math.log1p(max(0, total_exposures))
                            / (1.0 + pattern_exposure),
                        )
                    ),
                )
            row["exploration_bonus"] = exploration_bonus
            row["activation"] = float(row["normalized_value"]) + exploration_bonus

        if not exploration_enabled:
            pattern_rows = [
                row for row in pattern_rows if row["source"] is not None
            ]
            if not pattern_rows:
                return None

        # The generic genome owns exactly-one arbitration.  The deterministic
        # order makes ties reproducible while leaving score comparison inside
        # the formal choice primitive.
        pattern_rows.sort(key=lambda row: (-float(row["activation"]), str(row["pattern_id"])))
        options = tuple(
            AnonymousChoiceOption(
                identity=str(row["pattern_id"]),
                actuator_identity=str(row["representative_move_uci"]),
                activation=float(row["activation"]),
                confirmed=True,
            )
            for row in pattern_rows
        )
        choice = AnonymousChoiceGenome().emit(
            options,
            max_ticks=max(1, int(self.config.max_ticks)),
        )
        selected_pattern_id = str(choice.option_identity)
        selected_row = next(
            row for row in pattern_rows if row["pattern_id"] == selected_pattern_id
        )
        selected_move_uci = str(choice.actuator_identity)
        if selected_move_uci not in legal:
            raise AssertionError(
                "anonymous local choice emitted a non-legal actuator"
            )

        emitted_pattern_id = _triplet_id(
            *_triplet_keys(
                board,
                legal[selected_move_uci],
                key_mode=self.config.key_mode,
            )
        )
        if emitted_pattern_id != selected_pattern_id:
            raise AssertionError(
                "anonymous choice pattern identity disagrees with emitted move"
            )
        exact_triplet_preexisting = emitted_pattern_id in self.triplet_ids
        exact_triplet_id = emitted_pattern_id
        if materialize_emitted:
            exact_triplet_id = self.ensure_triplet(
                board,
                legal[selected_move_uci],
                stage=stage_diagnostic,
            )
        if exact_triplet_id != emitted_pattern_id:
            raise AssertionError(
                "materialized local triplet identity disagrees with emission"
            )
        exact_confirmation = (
            self.confirm_candidate(
                board,
                triplet_id=exact_triplet_id,
                move_uci=selected_move_uci,
            )
            if exact_triplet_id in self.triplet_ids
            else {}
        )
        exact_score = exact_confirmation.get("selected_score_raw")
        exact_confirmed = (
            exact_confirmation.get("selected_move") == selected_move_uci
            and exact_confirmation.get("selected_triplet") == exact_triplet_id
        )
        # TD must see the native exploitation estimate that won the local
        # competition.  The exploration bonus is a choice-time activation,
        # not a value estimate, and a newly materialized exact branch often
        # confirms with score zero.  Preserve that exact score separately.
        prediction = float(selected_row["raw_value"])
        prediction_source = "pre_emission_native_raw"

        self.runtime_choice_count += 1
        return NativeLocalTrainingDecision(
            move_uci=selected_move_uci,
            triplet_id=exact_triplet_id,
            pattern_id=selected_pattern_id,
            source=(
                None
                if selected_row["source"] is None
                else str(selected_row["source"])
            ),
            prediction=prediction,
            confirmed=bool(exact_confirmed),
            policy_supported=bool(selected_row["source"] is not None),
            raw_value=float(selected_row["raw_value"]),
            normalized_value=float(selected_row["normalized_value"]),
            exploration_bonus=float(selected_row["exploration_bonus"]),
            activation=float(selected_row["activation"]),
            pattern_exposure=int(selected_row["pattern_exposure"]),
            total_current_pattern_exposures=int(total_exposures),
            alias_index=int(selected_row["alias_index"]),
            alias_group_size=int(selected_row["alias_group_size"]),
            source_move_uci=(
                None
                if selected_row["source_move_uci"] is None
                else str(selected_row["source_move_uci"])
            ),
            source_score_raw=(
                None
                if selected_row["source_score_raw"] is None
                else float(selected_row["source_score_raw"])
            ),
            exact_confirmation_score_raw=(
                None
                if exact_score is None or not math.isfinite(float(exact_score))
                else float(exact_score)
            ),
            prediction_source=prediction_source,
            formal_ticks=int(choice.formal_ticks)
            + int(exact_confirmation.get("formal_ticks_run", 0) or 0),
            materialized_after_emission=bool(
                materialize_emitted and not exact_triplet_preexisting
            ),
            audit_candidate_count=len(full_candidates),
            pattern_count=len(pattern_rows),
        )

    def _root_request_exposures(self) -> int:
        """Read the graph root's cumulative local-choice exposure count."""

        root = self.graph.nodes[ROOT_ID]
        try:
            return max(0, int(root.meta.get("request_exposures", 0)))
        except (TypeError, ValueError):
            return 0

    def _local_pattern_exposure(
        self,
        pattern_id: str,
    ) -> int:
        """Return prior exposure for the exact current local pattern only."""

        if pattern_id not in self.triplet_ids:
            return 0
        triplet_node = self.graph.nodes.get(_TripletNodeIds(pattern_id).triplet)
        if triplet_node is None:
            return 0
        try:
            return max(0, int(triplet_node.meta.get("request_exposures", 0)))
        except (TypeError, ValueError):
            return 0

    def _triplet_local_utility(self, triplet_id: str) -> float:
        """Return the learned feature utility available before a runtime tick.

        Retrieval happens before candidate terminals have been evaluated for
        the current board, so ``_confirmed_terminal_score`` cannot be used as
        a retrieval signal: it intentionally only scores terminals that are
        active in the current frame.  The persistent local weights are the
        outcome-blind signal available at this boundary.  Keep the same
        terminal roles and normalization family as runtime scoring, while
        adding the native root edge credit that represents an exact action's
        local history.
        """

        local_values: list[float] = []
        triplet_node = self.graph.nodes.get(_TripletNodeIds(triplet_id).triplet)
        if triplet_node is not None and triplet_node.nid not in self.pruned_terminal_ids:
            triplet_value = float(triplet_node.meta.get("local_weight", 0.0))
            if math.isfinite(triplet_value):
                local_values.append(triplet_value)
        for node_id in sorted(self.triplet_nodes.get(triplet_id, set())):
            node = self.graph.nodes[node_id]
            if node.nid in self.pruned_terminal_ids:
                continue
            if node.ntype != NodeType.TERMINAL and node.meta.get("role") != "composition_feature":
                continue
            if node.meta.get("role") not in {
                "before_feature",
                "delta_feature",
                "after_feature",
                "projection_feature",
                "composition_feature",
            }:
                continue
            value = float(node.meta.get("local_weight", 0.0))
            if math.isfinite(value):
                local_values.append(value)

        normalization = str(self.config.terminal_score_normalization).lower()
        if not local_values:
            local_score = 0.0
        elif normalization == "mean":
            local_score = math.fsum(local_values) / len(local_values)
        elif normalization == "sqrt":
            local_score = math.fsum(local_values) / math.sqrt(len(local_values))
        elif normalization == "sum":
            local_score = math.fsum(local_values)
        else:
            raise ValueError(
                "terminal_score_normalization must be mean, sqrt, or sum"
            )

        return math.fsum((
            self.config.terminal_score_scale * local_score,
            self.config.triplet_credit_scale * self._triplet_root_weight(triplet_id),
        ))

    def _retrieval_candidate_pairs_for_legal(
        self,
        board: chess.Board,
        legal: Mapping[str, chess.Move],
        *,
        masked_triplets: set[str] | None = None,
    ) -> list[tuple[str, str, int]]:
        """Build deterministic bounded source pairs for each legal action.

        Every action gets its strongest learned incumbent first.  The
        remaining per-action slots are filled by retrieval-ranked challengers
        (shared-atom overlap for the shared substrate, or nearest-prototype
        rank for the older generalized substrate).  Exact sources are added
        explicitly and therefore never suppress generalized sources merely
        because the exact triplet has already materialized.
        """

        per_move: dict[str, list[tuple[str, str, int]]] = {}
        per_move_limit = max(0, int(self.config.max_prototype_candidates_per_move))
        for move_uci, move in sorted(legal.items()):
            keys = _triplet_keys(board, move, key_mode=self.config.key_mode)
            exact_id = _triplet_id(*keys)
            rows: dict[str, tuple[int, bool]] = {}

            def add_candidate(
                candidate_id: str,
                retrieval_rank: int,
                *,
                exact: bool = False,
            ) -> None:
                candidate_id = str(candidate_id)
                if candidate_id not in self.triplet_ids:
                    return
                if candidate_id in self.pruned_triplet_ids:
                    return
                if masked_triplets and candidate_id in masked_triplets:
                    return
                previous = rows.get(candidate_id)
                current = (int(retrieval_rank), bool(exact))
                if previous is None or current[0] < previous[0] or (
                    current[0] == previous[0] and current[1] and not previous[1]
                ):
                    rows[candidate_id] = current

            if exact_id in self.triplet_ids:
                # Exact is intentionally a first-class candidate, not a
                # short-circuit that prevents generalized retrieval.  Its
                # negative retrieval rank is a structural locality marker so
                # a global bounded cap cannot discard the current action's
                # exact incumbent in favour of aliases of that same source.
                add_candidate(exact_id, -1, exact=True)

            if self.config.shared_feature_atoms:
                generalized = self._triplets_from_active_shared_atoms(keys)
            elif self.config.key_mode != "exact":
                generalized = tuple(
                    candidate_id
                    for candidate_id, _distance in self._nearest_triplets_for_keys(keys)
                )
            else:
                generalized = ()
            for retrieval_rank, candidate_id in enumerate(generalized):
                add_candidate(
                    candidate_id,
                    retrieval_rank,
                )

            if not rows:
                continue

            # A zero configured retrieval width has no meaningful generalized
            # candidate slot, but an already-materialized exact source remains
            # a valid native incumbent.  This keeps exact lookup monotonic.
            limit = max(1, per_move_limit) if exact_id in rows else per_move_limit
            if limit <= 0:
                continue

            incumbent = min(
                rows,
                key=lambda candidate_id: (
                    -self._triplet_local_utility(candidate_id),
                    rows[candidate_id][0],
                    0 if rows[candidate_id][1] else 1,
                    candidate_id,
                ),
            )
            exact_candidate = exact_id if exact_id in rows else None
            ordered_ids: list[str] = []
            if exact_candidate is not None:
                ordered_ids.append(exact_candidate)
            if incumbent not in ordered_ids:
                ordered_ids.append(incumbent)
            challengers = sorted(
                (
                    candidate_id
                    for candidate_id in rows
                    if candidate_id not in ordered_ids
                ),
                key=lambda candidate_id: (
                    rows[candidate_id][0],
                    -self._triplet_local_utility(candidate_id),
                    candidate_id,
                ),
            )
            ordered_ids.extend(challengers)
            ordered_ids = ordered_ids[:limit]
            per_move[move_uci] = [
                (candidate_id, move_uci, rows[candidate_id][0])
                for candidate_id in ordered_ids
            ]

        return [
            candidate
            for move_uci in sorted(per_move)
            for candidate in per_move[move_uci]
        ]

    def _cap_shared_candidate_pairs(
        self,
        candidate_pairs: Iterable[tuple[str, str, int]],
    ) -> list[tuple[str, str, int]]:
        """Apply the global shared-source cap with incumbent-first fairness."""

        cap = max(0, int(self.config.max_shared_atom_candidates_per_choice))
        if cap == 0:
            return []
        unique: dict[tuple[str, str], tuple[str, str, int]] = {}
        for triplet_id, move_uci, retrieval_rank in candidate_pairs:
            pair = (str(triplet_id), str(move_uci))
            candidate = (pair[0], pair[1], int(retrieval_rank))
            previous = unique.get(pair)
            if previous is None or candidate[2] < previous[2]:
                unique[pair] = candidate
        rows = sorted(
            unique.values(),
            key=lambda row: (row[1], row[2], row[0]),
        )
        if len(rows) <= cap:
            return rows

        by_move: dict[str, list[tuple[str, str, int]]] = {}
        for row in rows:
            by_move.setdefault(row[1], []).append(row)
        for move_uci in by_move:
            by_move[move_uci].sort(
                key=lambda row: (
                    -self._triplet_local_utility(row[0]),
                    row[2],
                    row[0],
                    row[1],
                )
            )

        selected: list[tuple[str, str, int]] = []
        selected_pairs: set[tuple[str, str]] = set()
        exacts = [row for row in rows if row[2] < 0]
        exacts.sort(
            key=lambda row: (
                -self._triplet_local_utility(row[0]),
                row[1],
                row[0],
            )
        )
        # Materialized exact branches are the most local learned evidence and
        # must survive before generalized aliases consume a global cap.  The
        # number of exact branches active on a novel board is normally small;
        # if it alone exceeds the cap, learned utility adjudicates them.
        for row in exacts:
            if len(selected) >= cap:
                break
            selected.append(row)
            selected_pairs.add((row[0], row[1]))

        incumbents = [by_move[move_uci][0] for move_uci in sorted(by_move)]
        incumbents.sort(
            key=lambda row: (
                -self._triplet_local_utility(row[0]),
                row[2],
                row[1],
                row[0],
            )
        )
        # Give each represented action its strongest incumbent before spending
        # any remaining capacity on challengers.  If the cap is smaller than
        # the number of represented actions, utility decides which incumbents
        # can be represented and the UCI key keeps the choice replayable.
        represented_moves = {row[1] for row in selected}
        for row in incumbents:
            if len(selected) >= cap:
                break
            if row[1] in represented_moves:
                continue
            selected.append(row)
            selected_pairs.add((row[0], row[1]))
            represented_moves.add(row[1])

        challengers = [
            row
            for row in rows
            if (row[0], row[1]) not in selected_pairs
        ]
        challengers.sort(
            key=lambda row: (
                row[2],
                -self._triplet_local_utility(row[0]),
                row[0],
                row[1],
            )
        )
        selected.extend(challengers[: max(0, cap - len(selected))])
        return selected

    def _full_audit_candidates(
        self,
        board: chess.Board,
        legal: Mapping[str, chess.Move] | None = None,
        *,
        masked_triplets: set[str] | None = None,
    ) -> list[tuple[float, str, str]]:
        """Return bounded confirmed ``(score, move, source)`` candidates.

        ``audit_choice`` intentionally keeps a compact 16-row report for
        historical artifacts.  Local training needs the complete source set,
        including one source/move pair for every legal alias, so it uses this
        internal helper instead of parsing that presentation slice.
        """

        legal_map = (
            dict(legal)
            if legal is not None
            else {
                move.uci(): move
                for move in sorted(board.legal_moves, key=lambda item: item.uci())
            }
        )
        if not legal_map:
            return []

        candidate_pairs = self._retrieval_candidate_pairs_for_legal(
            board,
            legal_map,
            masked_triplets=masked_triplets,
        )

        if self.config.shared_feature_atoms and len(candidate_pairs) > self.config.max_shared_atom_candidates_per_choice:
            self.scheduler_stats["shared_atom_candidate_pairs_before_cap"] += len(candidate_pairs)
            candidate_pairs = self._cap_shared_candidate_pairs(candidate_pairs)
            self.scheduler_stats["shared_atom_candidate_pairs_after_cap"] += len(candidate_pairs)

        self.scheduler_stats["choose_calls"] += 1
        self.scheduler_stats["candidate_triplets_ticked"] += len(
            {triplet_id for triplet_id, _move_uci, _rank in candidate_pairs}
        )
        self.scheduler_stats["triplets_skipped_by_index"] += max(
            0,
            len(self.triplet_ids)
            - len({triplet_id for triplet_id, _move_uci, _rank in candidate_pairs}),
        )
        if not candidate_pairs:
            self.scheduler_stats["empty_candidate_calls"] += 1
            return []

        candidates: list[tuple[float, str, str]] = []
        triplet_key_cache: dict[
            tuple[str, str, str],
            tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]],
        ] = {}
        for triplet_id, move_uci, _retrieval_rank in candidate_pairs:
            active_nodes = (
                self._active_nodes_for_triplets({triplet_id})
                if self.config.indexed_scheduler
                else None
            )
            if active_nodes is None:
                self._reset_runtime_states()
            else:
                self.scheduler_stats["active_nodes_ticked"] += len(active_nodes)
                self.scheduler_stats["full_graph_node_resets_avoided"] += max(
                    0, len(self.graph.nodes) - len(active_nodes)
                )
                self._reset_runtime_states(active_nodes)
            env: dict[str, Any] = {
                "board": board,
                "candidate_move_by_triplet": {triplet_id: move_uci},
                "shared_atom_move_uci": move_uci,
                "__triplet_keys_cache": triplet_key_cache,
            }
            engine = FormalReConEngine(
                self.graph,
                validate_pairs=False,
                record_trace=False,
            )
            engine.request(ROOT_ID)
            until = None
            if self.config.indexed_scheduler:
                until = lambda _engine, current_triplet=triplet_id: self._candidate_triplets_settled(
                    {current_triplet}
                )
            engine.run(
                max_ticks=self.config.max_ticks,
                env=env,
                active_nodes=active_nodes,
                until=until,
            )
            self.scheduler_stats["formal_ticks_run"] += engine.tick
            candidates.extend(
                self._confirmed_action_candidates(
                    legal_map,
                    {triplet_id},
                    candidate_move_by_triplet={triplet_id: move_uci},
                )
            )
        return candidates

    def confirm_candidate(self, board: chess.Board, *, triplet_id: str, move_uci: str) -> dict[str, Any]:
        legal = {move.uci(): move for move in board.legal_moves}
        if move_uci not in legal or triplet_id not in self.triplet_ids:
            return {
                "selected_move": None,
                "candidate_triplet_count": 0,
                "confirmed_candidate_count": 0,
                "confirmed_candidates": [],
            }
        active_nodes = self._active_nodes_for_triplets({triplet_id})
        self._reset_runtime_states(active_nodes)
        env: dict[str, Any] = {
            "board": board,
            "candidate_move_by_triplet": {triplet_id: move_uci},
            "shared_atom_move_uci": move_uci,
        }
        engine = FormalReConEngine(self.graph, validate_pairs=False, record_trace=False)
        engine.request(ROOT_ID)
        engine.run(
            max_ticks=self.config.max_ticks,
            env=env,
            active_nodes=active_nodes,
            until=lambda _engine: self._candidate_triplets_settled({triplet_id}),
        )
        candidates = self._confirmed_action_candidates(
            legal,
            {triplet_id},
            candidate_move_by_triplet={triplet_id: move_uci},
        )
        candidates.sort(reverse=True)
        return {
            "selected_move": None if not candidates else candidates[0][1],
            "selected_triplet": None if not candidates else candidates[0][2],
            "selected_score_raw": None if not candidates else float(candidates[0][0]),
            "selected_score": None if not candidates else round(float(candidates[0][0]), 6),
            "candidate_triplet_count": 1,
            "confirmed_candidate_count": len(candidates),
            "confirmed_candidates": [
                {"score": round(float(score), 6), "move": candidate_move, "triplet_id": candidate_triplet}
                for score, candidate_move, candidate_triplet in candidates[:16]
            ],
            "formal_ticks_run": engine.tick,
        }

    def audit_choice(self, board: chess.Board, *, masked_triplets: set[str] | None = None) -> dict[str, Any]:
        legal = {move.uci(): move for move in board.legal_moves}
        if not legal:
            return {
                "selected_move": None,
                "candidate_triplet_count": 0,
                "confirmed_candidate_count": 0,
                "confirmed_candidates": [],
            }
        if self.config.shared_feature_atoms:
            return self._audit_choice_shared_atoms(board, legal, masked_triplets=masked_triplets)
        candidate_moves = self._candidate_triplets_for_board(board, legal)
        if masked_triplets:
            candidate_moves = {triplet_id: move for triplet_id, move in candidate_moves.items() if triplet_id not in masked_triplets}
        candidate_triplets = set(candidate_moves)
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
        env: dict[str, Any] = {"board": board, "candidate_move_by_triplet": candidate_moves}
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
        candidates = self._confirmed_action_candidates(
            legal,
            candidate_triplets if self.config.indexed_scheduler else None,
            candidate_move_by_triplet=candidate_moves,
        )
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
            "selected_score_raw": float(candidates[0][0]),
            "selected_score": round(float(candidates[0][0]), 6),
            "candidate_triplet_count": len(candidate_triplets),
            "confirmed_candidate_count": len(candidates),
            "confirmed_candidates": [
                {"score": round(float(score), 6), "move": move_uci, "triplet_id": triplet_id}
                for score, move_uci, triplet_id in candidates[:16]
            ],
        }

    def _audit_choice_shared_atoms(
        self,
        board: chess.Board,
        legal: Mapping[str, chess.Move],
        *,
        masked_triplets: set[str] | None = None,
    ) -> dict[str, Any]:
        candidate_pairs = self._retrieval_candidate_pairs_for_legal(
            board,
            legal,
            masked_triplets=masked_triplets,
        )
        if len(candidate_pairs) > self.config.max_shared_atom_candidates_per_choice:
            self.scheduler_stats["shared_atom_candidate_pairs_before_cap"] += len(candidate_pairs)
            candidate_pairs = self._cap_shared_candidate_pairs(candidate_pairs)
            self.scheduler_stats["shared_atom_candidate_pairs_after_cap"] += len(candidate_pairs)
        unique_triplets = {triplet_id for triplet_id, _move, _rank in candidate_pairs}
        self.scheduler_stats["choose_calls"] += 1
        self.scheduler_stats["candidate_triplets_ticked"] += len(candidate_pairs)
        self.scheduler_stats["triplets_skipped_by_index"] += max(0, len(self.triplet_ids) - len(unique_triplets))
        if not candidate_pairs:
            self.scheduler_stats["empty_candidate_calls"] += 1
            return {
                "selected_move": None,
                "candidate_triplet_count": 0,
                "confirmed_candidate_count": 0,
                "confirmed_candidates": [],
            }
        candidates: list[tuple[float, str, str]] = []
        triplet_key_cache: dict[tuple[str, str, str], tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = {}
        for triplet_id, move_uci, _retrieval_rank in candidate_pairs:
            active_nodes = self._active_nodes_for_triplets({triplet_id})
            self.scheduler_stats["active_nodes_ticked"] += len(active_nodes)
            self.scheduler_stats["full_graph_node_resets_avoided"] += max(0, len(self.graph.nodes) - len(active_nodes))
            self._reset_runtime_states(active_nodes)
            env: dict[str, Any] = {
                "board": board,
                "candidate_move_by_triplet": {triplet_id: move_uci},
                "shared_atom_move_uci": move_uci,
                "__triplet_keys_cache": triplet_key_cache,
            }
            engine = FormalReConEngine(self.graph, validate_pairs=False, record_trace=False)
            engine.request(ROOT_ID)
            engine.run(
                max_ticks=self.config.max_ticks,
                env=env,
                active_nodes=active_nodes,
                until=lambda _engine, current_triplet=triplet_id: self._candidate_triplets_settled({current_triplet}),
            )
            self.scheduler_stats["formal_ticks_run"] += engine.tick
            candidates.extend(
                self._confirmed_action_candidates(
                    legal,
                    {triplet_id},
                    candidate_move_by_triplet={triplet_id: move_uci},
                )
            )
        if not candidates:
            return {
                "selected_move": None,
                "candidate_triplet_count": len(candidate_pairs),
                "unique_candidate_triplet_count": len(unique_triplets),
                "confirmed_candidate_count": 0,
                "confirmed_candidates": [],
            }
        candidates.sort(reverse=True)
        self.runtime_choice_count += 1
        return {
            "selected_move": candidates[0][1],
            "selected_triplet": candidates[0][2],
            "selected_score_raw": float(candidates[0][0]),
            "selected_score": round(float(candidates[0][0]), 6),
            "candidate_triplet_count": len(candidate_pairs),
            "unique_candidate_triplet_count": len(unique_triplets),
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

    def apply_intrinsic_td(
        self,
        board: chess.Board,
        move: chess.Move,
        *,
        td_error: float,
        stage_diagnostic: str,
    ) -> str:
        """Apply one outcome-grounded TD error to an observed action branch.

        Unlike train_action_rewards, this method neither enumerates rewards for
        unplayed legal moves nor accepts a positive-move label set. The caller
        must first execute/observe this exact action and derive the scalar from
        the generic intrinsic-credit engine.
        """

        if move not in board.legal_moves:
            raise ValueError(f"cannot credit illegal observed move: {move.uci()}")
        triplet_id = self.ensure_triplet(board, move, stage=stage_diagnostic)
        self._apply_m3(triplet_id, reward=float(td_error))
        # A local exposure is an outcome-grounded observed action, not a
        # prospective audit or anonymous choice query.  Keep the total on the
        # graph root so the next local selector can compute its bonus without
        # introducing a second exposure ledger.
        root = self.graph.nodes[ROOT_ID]
        root.meta["request_exposures"] = self._root_request_exposures() + 1
        return triplet_id

    def learned_state_audit(self) -> dict[str, Any]:
        """Return the minimal state needed to certify an empty learned start."""

        trainable_edges = [edge for edge in self.graph.edges if edge.meta.get("trainable")]
        return {
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
            "triplet_count": len(self.triplet_ids),
            "trainable_edge_count": len(trainable_edges),
            "nonzero_trainable_edge_count": sum(abs(float(edge.w)) > 1e-15 for edge in trainable_edges),
            "nonzero_local_weight_node_count": sum(
                abs(float(node.meta.get("local_weight", 0.0))) > 1e-15
                for node in self.graph.nodes.values()
            ),
            "m3_update_count": self.m3_update_count,
            "m4_event_count": self.m4_event_count,
        }

    def ensure_triplet(self, board: chess.Board, move: chess.Move, *, stage: str) -> str:
        before_keys, action_delta_keys, after_keys = _triplet_keys(board, move, key_mode=self.config.key_mode)
        triplet_id = _triplet_id(before_keys, action_delta_keys, after_keys)
        if triplet_id in self.triplet_ids:
            return triplet_id

        ids = _TripletNodeIds(triplet_id)
        created_private_node_ids: set[str] = set()
        active_node_ids: set[str] = set()
        base_nodes = [
            Node(ids.triplet, NodeType.SCRIPT, meta=_candidate_meta("SCRIPT", stage, role="triplet", action_uci=move.uci())),
            Node(ids.before_script, NodeType.SCRIPT, meta=_candidate_meta("SCRIPT", stage, role="before_script", action_uci=move.uci())),
            Node(ids.action_script, NodeType.SCRIPT, meta=_candidate_meta("SCRIPT", stage, role="action_script", action_uci=move.uci())),
            Node(ids.after_script, NodeType.SCRIPT, meta=_candidate_meta("SCRIPT", stage, role="after_script", action_uci=move.uci())),
            Node(ids.action, NodeType.TERMINAL, predicate=_action_predicate(move.uci()), meta=_action_meta(stage, move.uci())),
        ]
        if self.config.include_grouped_cache_terminals:
            base_nodes.extend([
                Node(ids.before_terminal, NodeType.TERMINAL, predicate=_pattern_predicate("before", move.uci(), before_keys, self.config.key_mode, self.config.prototype_distance_threshold), meta=_terminal_meta(stage, "before", move.uci(), before_keys)),
                Node(ids.delta_terminal, NodeType.TERMINAL, predicate=_pattern_predicate("delta", move.uci(), action_delta_keys, self.config.key_mode, self.config.prototype_distance_threshold), meta=_terminal_meta(stage, "delta", move.uci(), action_delta_keys)),
                Node(ids.after_terminal, NodeType.TERMINAL, predicate=_pattern_predicate("after", move.uci(), after_keys, self.config.key_mode, self.config.prototype_distance_threshold), meta=_terminal_meta(stage, "after", move.uci(), after_keys)),
            ])
        for node in base_nodes:
            self.graph.add_node(node)
            created_private_node_ids.add(node.nid)
            active_node_ids.add(node.nid)

        created_edges: list[Any] = []
        created_edges.extend(self._add_hierarchy_pair(ROOT_ID, ids.triplet, trainable=True, weight=0.0))
        created_edges.extend(self._add_hierarchy_pair(ids.triplet, ids.before_script, trainable=True, weight=0.0))
        created_edges.extend(self._add_hierarchy_pair(ids.triplet, ids.action_script, trainable=True, weight=0.0))
        created_edges.extend(self._add_hierarchy_pair(ids.triplet, ids.after_script, trainable=True, weight=0.0))
        created_edges.extend(self._add_hierarchy_pair(ids.action_script, ids.action, trainable=True, weight=0.0))
        if self.config.include_grouped_cache_terminals:
            created_edges.extend(self._add_hierarchy_pair(ids.before_script, ids.before_terminal, trainable=True, weight=0.0))
            created_edges.extend(self._add_hierarchy_pair(ids.action_script, ids.delta_terminal, trainable=True, weight=0.0))
            created_edges.extend(self._add_hierarchy_pair(ids.after_script, ids.after_terminal, trainable=True, weight=0.0))
        for role, parent_id, keys in (
            ("before_feature", ids.before_script, before_keys),
            ("delta_feature", ids.action_script, action_delta_keys),
            ("after_feature", ids.after_script, after_keys),
        ):
            for key in keys:
                if self.config.shared_feature_atoms:
                    feature_id = self._ensure_shared_feature_atom(role, key, stage=stage, action_uci=move.uci())
                    self.shared_atom_triplets.setdefault(feature_id, set()).add(triplet_id)
                    self.graph.nodes[feature_id].meta["reuse_count"] = len(self.shared_atom_triplets[feature_id])
                else:
                    feature_id = _feature_terminal_id(triplet_id, role, key)
                    self.graph.add_node(
                        Node(
                            feature_id,
                            NodeType.TERMINAL,
                            predicate=_single_key_predicate(role, move.uci(), key, self.config.key_mode, self.config.prototype_distance_threshold),
                            meta=_feature_terminal_meta(stage, role, move.uci(), key),
                        )
                    )
                    created_private_node_ids.add(feature_id)
                created_edges.extend(self._add_hierarchy_pair(parent_id, feature_id, trainable=True, weight=0.0))
                active_node_ids.add(feature_id)
        if self.config.shared_feature_atoms and self.config.shared_projection_atoms:
            for key in _projection_atom_keys(before_keys, action_delta_keys, after_keys):
                feature_id = self._ensure_shared_feature_atom("projection_feature", key, stage=stage, action_uci=move.uci())
                self.shared_atom_triplets.setdefault(feature_id, set()).add(triplet_id)
                self.graph.nodes[feature_id].meta["reuse_count"] = len(self.shared_atom_triplets[feature_id])
                created_edges.extend(self._add_hierarchy_pair(ids.action_script, feature_id, trainable=True, weight=0.0))
                active_node_ids.add(feature_id)
        created_edges.extend(self._add_sequence_pair(ids.before_script, ids.action_script, trainable=True, weight=0.0))
        created_edges.extend(self._add_sequence_pair(ids.action_script, ids.after_script, trainable=True, weight=0.0))
        for node_id in created_private_node_ids:
            self.graph.nodes[node_id].meta["triplet_id"] = triplet_id
        self.triplet_ids.add(triplet_id)
        self.triplet_nodes[triplet_id] = active_node_ids
        self.triplet_trainable_edges[triplet_id] = created_edges
        self.triplet_pattern_key_cache[triplet_id] = set((*before_keys, *action_delta_keys, *after_keys))
        return triplet_id

    def _ensure_shared_feature_atom(self, role: str, key: str, *, stage: str, action_uci: str) -> str:
        atom_key = (role, key)
        existing = self.shared_atom_ids_by_key.get(atom_key)
        if existing is not None:
            return existing
        atom_id = _shared_feature_atom_id(role, key)
        self.graph.add_node(
            Node(
                atom_id,
                NodeType.TERMINAL,
                predicate=_shared_atom_predicate(role, key, self.config.key_mode),
                meta=_shared_feature_atom_meta(stage, role, action_uci, key),
            )
        )
        self.shared_atom_ids_by_key[atom_key] = atom_id
        self.shared_atom_key_by_id[atom_id] = atom_key
        return atom_id

    def materialize_shared_composite(
        self,
        member_atom_ids: Iterable[str],
        triplet_ids: Iterable[str],
        *,
        stage: str,
    ) -> str:
        """Create native per-parent AND circuits sharing one candidate lifecycle."""

        members = tuple(sorted(dict.fromkeys(map(str, member_atom_ids))))
        if len(members) < 2:
            raise ValueError("a shared composite requires at least two distinct atoms")
        for member_id in members:
            node = self.graph.nodes.get(member_id)
            if node is None or not node.meta.get("shared_feature_atom"):
                raise ValueError(f"composite member is not a shared feature atom: {member_id}")
        composite_id = f"tg26s_stem_composite_{_hash_keys(members)[:20]}"
        if composite_id not in self.composite_cells:
            cell = StemCellTerminal(composite_id)
            cell.state = StemCellState.TRIAL
            cell.xp = cell.XP_INITIAL
            cell.is_composition = True
            cell.children = list(members)
            cell.depth = 1
            cell.trial_parent_id = ROOT_ID
            cell.metadata.update(
                {
                    "composition_operator": "and",
                    "candidate_generation_used_outcome_label": False,
                    "stage_label_learner_visible": False,
                }
            )
            self.composite_cells[composite_id] = cell
            self.composite_member_ids[composite_id] = members
            self.composite_triplets[composite_id] = set()

        for triplet_id in tuple(dict.fromkeys(map(str, triplet_ids))):
            if triplet_id not in self.triplet_ids:
                raise ValueError(f"unknown composite parent triplet: {triplet_id}")
            if not set(members).issubset(self.triplet_nodes.get(triplet_id, set())):
                raise ValueError(
                    f"composite members did not coactivate in parent triplet: {triplet_id}"
                )
            key = (composite_id, triplet_id)
            if key in self.composite_node_by_triplet:
                continue
            instance_id = (
                f"{composite_id}_{hashlib.sha1(triplet_id.encode("utf-8")).hexdigest()[:12]}"
            )
            meta = _candidate_meta(
                "SCRIPT",
                stage,
                role="composition_feature",
                action_uci="",
            )
            meta.update(
                {
                    "origin": "native_stem_cell_composite",
                    "confirm_policy": "k_of_n",
                    "confirm_k": len(members),
                    "stem_cell_id": composite_id,
                    "composition_operator": "and",
                    "composition_member_ids": list(members),
                    "candidate_local_stats": self.composite_cells[
                        composite_id
                    ].candidate_stats.to_dict(),
                    "parent_triplet_id": triplet_id,
                }
            )
            self.graph.add_node(Node(instance_id, NodeType.SCRIPT, meta=meta))
            for member_id in members:
                self._add_hierarchy_pair(
                    instance_id,
                    member_id,
                    trainable=False,
                    weight=0.0,
                )
            parent_id = _TripletNodeIds(triplet_id).action_script
            attachment_edges = self._add_hierarchy_pair(
                parent_id,
                instance_id,
                trainable=True,
                weight=0.0,
            )
            self.triplet_nodes[triplet_id].add(instance_id)
            self.triplet_trainable_edges[triplet_id].extend(attachment_edges)
            self.composite_triplets[composite_id].add(triplet_id)
            self.composite_node_by_triplet[key] = instance_id
        reuse_count = len(self.composite_triplets[composite_id])
        for triplet_id in self.composite_triplets[composite_id]:
            instance_id = self.composite_node_by_triplet[(composite_id, triplet_id)]
            self.graph.nodes[instance_id].meta["reuse_count"] = reuse_count
        return composite_id

    def rank_shared_composite_candidates(
        self,
        triplet_ids: Iterable[str],
        *,
        max_candidates: int = 8,
        max_atoms_per_triplet: int = 18,
        min_support: int = 2,
    ) -> tuple[dict[str, Any], ...]:
        """Rank selective coactivations using only native outcome-trained state."""

        selected_triplets = tuple(
            sorted(triplet_id for triplet_id in set(triplet_ids) if triplet_id in self.triplet_ids)
        )
        atom_support: dict[str, int] = {}
        atom_signal: dict[str, float] = {}
        pair_support: dict[tuple[str, str], int] = {}
        pair_signal: dict[tuple[str, str], float] = {}
        pair_parents: dict[tuple[str, str], list[str]] = {}
        for triplet_id in selected_triplets:
            root_edge = self.graph.get_edge(ROOT_ID, triplet_id, LinkType.SUB)
            signal = 0.0 if root_edge is None else float(root_edge.w)
            eligible = [
                node_id
                for node_id in self.triplet_nodes.get(triplet_id, set())
                if self.graph.nodes[node_id].meta.get("shared_feature_atom")
                and node_id not in self.pruned_terminal_ids
            ]
            eligible.sort(
                key=lambda node_id: (
                    int(self.graph.nodes[node_id].meta.get("reuse_count", 0)),
                    abs(float(self.graph.nodes[node_id].meta.get("local_weight", 0.0))),
                    node_id,
                ),
                reverse=True,
            )
            eligible = sorted(eligible[: max(2, int(max_atoms_per_triplet))])
            for atom_id in eligible:
                atom_support[atom_id] = atom_support.get(atom_id, 0) + 1
                atom_signal[atom_id] = atom_signal.get(atom_id, 0.0) + signal
            for pair in combinations(eligible, 2):
                pair_support[pair] = pair_support.get(pair, 0) + 1
                pair_signal[pair] = pair_signal.get(pair, 0.0) + signal
                pair_parents.setdefault(pair, []).append(triplet_id)

        rows: list[dict[str, Any]] = []
        for pair, support in pair_support.items():
            if support < max(1, int(min_support)):
                continue
            member_supports = (atom_support[pair[0]], atom_support[pair[1]])
            if support >= min(member_supports):
                continue
            pair_mean = pair_signal[pair] / support
            member_means = (
                atom_signal[pair[0]] / member_supports[0],
                atom_signal[pair[1]] / member_supports[1],
            )
            contrast = abs(pair_mean - member_means[0]) + abs(
                pair_mean - member_means[1]
            )
            score = math.sqrt(support) * (abs(pair_mean) + contrast)
            rows.append(
                {
                    "candidate_id": f"tg26s_stem_composite_{_hash_keys(pair)[:20]}",
                    "member_atom_ids": list(pair),
                    "support": support,
                    "member_supports": list(member_supports),
                    "pair_outcome_signal_mean": pair_mean,
                    "proposal_valence": (
                        "positive"
                        if pair_mean > 0.0
                        else "negative"
                        if pair_mean < 0.0
                        else "neutral"
                    ),
                    "member_outcome_signal_means": list(member_means),
                    "selectivity_contrast": contrast,
                    "proposal_score": score,
                    "parent_triplet_ids": sorted(pair_parents[pair]),
                    "activation_signature_sha256": hashlib.sha256(
                        "\n".join(sorted(pair_parents[pair])).encode("utf-8")
                    ).hexdigest(),
                    "candidate_generation_used_outcome_label": False,
                    "candidate_generation_signal": "native_root_edge_weight",
                }
            )
        rows.sort(
            key=lambda row: (
                float(row["proposal_score"]),
                int(row["support"]),
                str(row["candidate_id"]),
            ),
            reverse=True,
        )
        limit = max(0, int(max_candidates))
        selected: list[dict[str, Any]] = []
        seen_activation_signatures: set[str] = set()

        def add_distinct(candidates: Iterable[dict[str, Any]], count: int) -> None:
            for row in candidates:
                if count <= 0 or len(selected) >= limit:
                    return
                signature = str(row["activation_signature_sha256"])
                if signature in seen_activation_signatures:
                    continue
                seen_activation_signatures.add(signature)
                selected.append(row)
                count -= 1

        positive_target = (limit + 1) // 2
        negative_target = limit // 2
        add_distinct(
            (row for row in rows if row["proposal_valence"] == "positive"),
            positive_target,
        )
        add_distinct(
            (row for row in rows if row["proposal_valence"] == "negative"),
            negative_target,
        )
        add_distinct(rows, limit - len(selected))
        selected.sort(
            key=lambda row: (
                float(row["proposal_score"]),
                int(row["support"]),
                str(row["candidate_id"]),
            ),
            reverse=True,
        )
        return tuple(selected)

    def matched_random_shared_composite_candidates(
        self,
        triplet_ids: Iterable[str],
        reference_candidates: Iterable[Mapping[str, Any]],
        *,
        seed: int,
        max_atoms_per_triplet: int = 18,
        min_support: int = 2,
    ) -> tuple[dict[str, Any], ...]:
        """Choose identity-randomized controls matched on coactivation support."""

        references = tuple(reference_candidates)
        if not references:
            return ()
        universe = list(
            self.rank_shared_composite_candidates(
                triplet_ids,
                max_candidates=100_000,
                max_atoms_per_triplet=max_atoms_per_triplet,
                min_support=min_support,
            )
        )
        reference_ids = {str(row["candidate_id"]) for row in references}
        available = [
            row for row in universe if str(row["candidate_id"]) not in reference_ids
        ]
        selected: list[dict[str, Any]] = []
        for reference in references:
            if not available:
                break
            reference_member_support = sorted(map(int, reference["member_supports"]))

            def match_key(row: Mapping[str, Any]) -> tuple[int, int, str]:
                member_support = sorted(map(int, row["member_supports"]))
                member_distance = sum(
                    abs(left - right)
                    for left, right in zip(
                        reference_member_support,
                        member_support,
                        strict=True,
                    )
                )
                tie = hashlib.sha256(
                    f"{int(seed)}:{str(row['candidate_id'])}".encode("utf-8")
                ).hexdigest()
                return (
                    abs(int(reference["support"]) - int(row["support"])),
                    member_distance,
                    tie,
                )

            chosen = min(available, key=match_key)
            available.remove(chosen)
            control = dict(chosen)
            control.update(
                {
                    "control_kind": "support_matched_identity_random",
                    "matched_reference_candidate_id": reference["candidate_id"],
                    "joint_support_distance": abs(
                        int(reference["support"]) - int(chosen["support"])
                    ),
                    "control_selection_used_outcome_signal": False,
                    "control_tie_break": "seeded_candidate_identity_sha256",
                }
            )
            selected.append(control)
        return tuple(selected)

    def set_composite_enabled(self, composite_id: str, *, enabled: bool) -> None:
        if composite_id not in self.composite_cells:
            raise KeyError(composite_id)
        if enabled:
            self.disabled_composite_ids.discard(composite_id)
        else:
            self.disabled_composite_ids.add(composite_id)

    def record_composite_intervention(
        self,
        composite_id: str,
        *,
        enabled_return: float,
        disabled_return: float,
        cycle: int,
    ) -> str:
        cell = self.composite_cells[composite_id]
        delta = float(enabled_return) - float(disabled_return)
        cell.update_xp(delta)
        valence = "positive" if delta >= 0.05 else "negative" if delta <= -0.05 else "neutral"
        cell.candidate_stats.survival_stats.last_confirm_cycle = int(cycle)
        for triplet_id in self.composite_triplets[composite_id]:
            node_id = self.composite_node_by_triplet[(composite_id, triplet_id)]
            node = self.graph.nodes[node_id]
            node.meta["candidate_local_stats"] = cell.candidate_stats.to_dict()
            node.meta["intervention_enabled_return"] = float(enabled_return)
            node.meta["intervention_disabled_return"] = float(disabled_return)
            node.meta["intervention_valence"] = valence
        return valence

    def consolidate_composite_candidate(self, composite_id: str) -> dict[str, Any]:
        cell = self.composite_cells[composite_id]
        decision = cell.candidate_stats.decision(xp=cell.xp)
        if decision == "mature":
            cell.state = StemCellState.MATURE
            self.disabled_composite_ids.discard(composite_id)
        elif decision in {"suppress", "demote"}:
            cell.state = StemCellState.PRUNED
            self.disabled_composite_ids.add(composite_id)
        for triplet_id in self.composite_triplets[composite_id]:
            node_id = self.composite_node_by_triplet[(composite_id, triplet_id)]
            node = self.graph.nodes[node_id]
            node.meta["stem_cell_state"] = cell.state.name
            node.meta["tier"] = (
                "mature"
                if cell.state == StemCellState.MATURE
                else "dead"
                if cell.state == StemCellState.PRUNED
                else "trial"
            )
            node.meta["candidate_local_stats"] = cell.candidate_stats.to_dict()
            node.meta["candidate_decision"] = decision
        self.m4_event_count += int(decision in {"mature", "suppress", "demote"})
        return {
            "composite_id": composite_id,
            "decision": decision,
            "state": cell.state.name,
            "xp": cell.xp,
            "candidate_local_stats": cell.candidate_stats.to_dict(),
            "enabled": composite_id not in self.disabled_composite_ids,
        }

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

    def freeze_existing_parameters(self, *, reason: str) -> dict[str, Any]:
        """Consolidate the current topology while leaving future growth plastic."""

        frozen_nodes = 0
        for node in self.graph.nodes.values():
            if "local_weight" not in node.meta:
                continue
            if not node.meta.get("plasticity_frozen"):
                frozen_nodes += 1
            node.meta["plasticity_frozen"] = True
            node.meta["plasticity_freeze_reason"] = str(reason)
        frozen_edges = 0
        for edge in self.graph.edges:
            if not edge.meta.get("trainable"):
                continue
            if not edge.meta.get("plasticity_frozen"):
                frozen_edges += 1
            edge.meta["plasticity_frozen"] = True
            edge.meta["plasticity_freeze_reason"] = str(reason)
        self.frozen_policy_triplet_ids = frozenset(self.triplet_ids)
        self.frozen_policy_token = self._compute_frozen_policy_token(
            self.frozen_policy_triplet_ids
        )
        return {
            "frozen_node_parameter_count": frozen_nodes,
            "frozen_edge_parameter_count": frozen_edges,
            "frozen_policy_triplet_count": len(self.frozen_policy_triplet_ids),
            "frozen_policy_token": self.frozen_policy_token,
        }

    def frozen_child_policy_token(
        self,
        allowed_triplets: Iterable[str],
    ) -> str | None:
        allowed = frozenset(allowed_triplets)
        if allowed != self.frozen_policy_triplet_ids:
            return None
        return self.frozen_policy_token

    def _compute_frozen_policy_token(self, triplet_ids: Iterable[str]) -> str:
        selected = frozenset(triplet_ids)
        node_ids = {ROOT_ID}
        for triplet_id in selected:
            node_ids.update(self.triplet_nodes.get(triplet_id, ()))
        node_rows = [
            (
                node_id,
                self.graph.nodes[node_id].ntype.name,
                float(self.graph.nodes[node_id].meta.get("local_weight", 0.0)),
                bool(self.graph.nodes[node_id].meta.get("plasticity_frozen", False)),
            )
            for node_id in sorted(node_ids)
            if node_id in self.graph.nodes
        ]
        edge_rows = sorted(
            (
                edge.src,
                edge.dst,
                edge.ltype.name,
                float(edge.w),
                bool(edge.meta.get("trainable", False)),
                bool(edge.meta.get("plasticity_frozen", False)),
            )
            for edge in self.graph.edges
            if edge.src in node_ids and edge.dst in node_ids
        )
        encoded = json.dumps(
            {"triplets": sorted(selected), "nodes": node_rows, "edges": edge_rows},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def apply_shared_atom_pruning(self, *, terminal_threshold: float = -0.20, triplet_threshold: float = -0.25) -> dict[str, Any]:
        pruned_shared_atoms = 0
        pruned_exact_terminals = 0
        for node in self.graph.nodes.values():
            if node.ntype != NodeType.TERMINAL:
                continue
            utility = float(node.meta.get("survival_utility", node.meta.get("local_weight", 0.0)))
            if utility > terminal_threshold:
                continue
            if int(node.meta.get("confirm_count", 0)) > 0:
                continue
            if node.meta.get("shared_feature_atom"):
                pruned_shared_atoms += int(node.nid not in self.pruned_terminal_ids)
            elif node.meta.get("role") in {"before_feature", "delta_feature", "after_feature", "projection_feature"}:
                pruned_exact_terminals += int(node.nid not in self.pruned_terminal_ids)
            else:
                continue
            node.meta["tier"] = "dead"
            node.meta["stem_cell_state"] = StemCellState.PRUNED.name
            node.meta["quarantine_reason"] = "low_generic_utility_without_positive_confirmation"
            self.pruned_terminal_ids.add(node.nid)
        pruned_triplets = 0
        for triplet_id in self.triplet_ids:
            if self._triplet_root_weight(triplet_id) > triplet_threshold:
                continue
            ids = _TripletNodeIds(triplet_id)
            node = self.graph.nodes[ids.triplet]
            if int(node.meta.get("confirm_count", 0)) > 0:
                continue
            pruned_triplets += int(triplet_id not in self.pruned_triplet_ids)
            node.meta["tier"] = "dead"
            node.meta["stem_cell_state"] = StemCellState.PRUNED.name
            node.meta["quarantine_reason"] = "low_root_weight_without_positive_confirmation"
            self.pruned_triplet_ids.add(triplet_id)
        return {
            "pruned_shared_atom_count": pruned_shared_atoms,
            "pruned_exact_terminal_count": pruned_exact_terminals,
            "pruned_triplet_count": pruned_triplets,
            "terminal_threshold": terminal_threshold,
            "triplet_threshold": triplet_threshold,
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
            "composite_candidate_count": len(self.composite_cells),
            "enabled_composite_candidate_count": len(self.composite_cells) - len(self.disabled_composite_ids),
            "composite_candidates": {
                cell_id: cell.to_dict() for cell_id, cell in sorted(self.composite_cells.items())
            },
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
            if all(node_id in self.graph.nodes for node_id in (ids.before_terminal, ids.delta_terminal, ids.after_terminal)):
                key = (
                    str(self.graph.nodes[ids.before_terminal].meta.get("pattern_hash")),
                    str(self.graph.nodes[ids.delta_terminal].meta.get("pattern_hash")),
                    str(self.graph.nodes[ids.after_terminal].meta.get("pattern_hash")),
                )
            else:
                key = tuple(sorted(self.triplet_pattern_key_cache.get(triplet_id, set())))  # type: ignore[assignment]
            equivalent_keys[key] = equivalent_keys.get(key, 0) + 1
        duplicate_equivalent = sum(count - 1 for count in equivalent_keys.values() if count > 1)
        shared_atoms = [node for node in self.graph.nodes.values() if node.meta.get("shared_feature_atom")]
        pruned_shared_atom_count = sum(
            1 for node_id in self.pruned_terminal_ids if self.graph.nodes[node_id].meta.get("shared_feature_atom")
        )
        pruned_exact_terminal_count = len(self.pruned_terminal_ids) - pruned_shared_atom_count
        triplet_local_feature_terminal_count = sum(
            1
            for node in self.graph.nodes.values()
            if node.ntype == NodeType.TERMINAL
            and node.meta.get("role") in {"before_feature", "delta_feature", "after_feature", "projection_feature"}
            and not node.meta.get("shared_feature_atom")
        )
        grouped_cache_terminal_count = sum(
            1
            for node in self.graph.nodes.values()
            if node.ntype == NodeType.TERMINAL and node.meta.get("grouped_cache_terminal")
        )
        return {
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
            "triplet_count": len(self.triplet_ids),
            "shared_atom_count": len(shared_atoms),
            "reused_atom_count": sum(1 for node in shared_atoms if int(node.meta.get("reuse_count", 0)) > 1),
            "triplet_local_feature_terminal_count": triplet_local_feature_terminal_count,
            "grouped_cache_terminal_count": grouped_cache_terminal_count,
            "shared_atom_stats": self.shared_atom_diagnostics(),
            "pruned_exact_terminal_count": pruned_exact_terminal_count,
            "pruned_shared_atom_count": pruned_shared_atom_count,
            "pruned_triplet_count": len(self.pruned_triplet_ids),
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
            "scheduler_stats": dict(self.scheduler_stats),
        }

    def shared_atom_diagnostics(self, *, max_atoms: int = 24) -> dict[str, Any]:
        atoms = [node for node in self.graph.nodes.values() if node.meta.get("shared_feature_atom")]

        def row(node: Node) -> dict[str, Any]:
            request_exposures = int(node.meta.get("request_exposures", 0))
            confirm_count = int(node.meta.get("confirm_count", 0))
            negative_count = int(node.meta.get("negative_confirm_count", 0))
            false_positive_count = int(node.meta.get("false_positive_count", 0))
            return {
                "node_id": node.nid,
                "terminal_key": node.meta.get("terminal_key"),
                "role": node.meta.get("role"),
                "reuse_count": int(node.meta.get("reuse_count", 0)),
                "activation_count": int(node.meta.get("activation_count", 0)),
                "request_exposures": request_exposures,
                "confirm_count": confirm_count,
                "negative_confirm_count": negative_count,
                "false_positive_count": false_positive_count,
                "positive_correlation": 0.0 if request_exposures == 0 else round(confirm_count / request_exposures, 6),
                "negative_correlation": 0.0 if request_exposures == 0 else round(negative_count / request_exposures, 6),
                "context_coverage": int(node.meta.get("reuse_count", 0)),
                "context_precision": 0.0
                if confirm_count + false_positive_count == 0
                else round(confirm_count / (confirm_count + false_positive_count), 6),
                "local_weight": round(float(node.meta.get("local_weight", 0.0)), 6),
                "survival_utility": round(float(node.meta.get("survival_utility", 0.0)), 6),
                "tier": node.meta.get("tier", "trial"),
            }

        rows = [row(node) for node in atoms]
        return {
            "atom_activation_distribution": _distribution([item["activation_count"] for item in rows]),
            "atom_confirmation_distribution": _distribution([item["confirm_count"] for item in rows]),
            "atom_false_positive_distribution": _distribution([item["false_positive_count"] for item in rows]),
            "top_positive_atoms": sorted(rows, key=lambda item: (item["local_weight"], item["confirm_count"]), reverse=True)[:max_atoms],
            "top_negative_atoms": sorted(rows, key=lambda item: (item["local_weight"], item["negative_confirm_count"]))[:max_atoms],
            "top_reused_atoms": sorted(rows, key=lambda item: item["reuse_count"], reverse=True)[:max_atoms],
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
        mutable_shared_ids = {
            node_id
            for node_id in self.triplet_nodes.get(triplet_id, set())
            if self.graph.nodes[node_id].meta.get("shared_feature_atom")
            and not self.graph.nodes[node_id].meta.get("plasticity_frozen")
        }
        shared_credit_scale = self._shared_feature_credit_scale(
            len(mutable_shared_ids)
        )
        node_ids = [
            ids.triplet,
            ids.before_script,
            ids.action_script,
            ids.after_script,
            ids.action,
        ]
        for maybe_id in (ids.before_terminal, ids.delta_terminal, ids.after_terminal):
            if maybe_id in self.graph.nodes:
                node_ids.append(maybe_id)
        for node_id in self.triplet_nodes.get(triplet_id, set()):
            node = self.graph.nodes[node_id]
            if node.ntype == NodeType.TERMINAL or node.meta.get("role") == "composition_feature":
                node_ids.append(node.nid)
        for node_id in dict.fromkeys(node_ids):
            node = self.graph.nodes[node_id]
            stem_cell_id = node.meta.get("stem_cell_id")
            cell = self.composite_cells.get(str(stem_cell_id)) if stem_cell_id else None
            if cell is not None:
                cell.record_candidate_request(parent_id=triplet_id)
                active = node.state in (NodeState.TRUE, NodeState.CONFIRMED)
                if active:
                    cell.record_candidate_activation(parent_id=triplet_id)
                    valence = (
                        "positive"
                        if bounded_reward > 0.0
                        else "negative"
                        if bounded_reward < 0.0
                        else "neutral"
                    )
                    cell.record_candidate_correlation(valence)
                node.meta["candidate_local_stats"] = cell.candidate_stats.to_dict()
                if not active:
                    continue
            node.meta["request_exposures"] = int(node.meta.get("request_exposures", 0)) + 1
            if bounded_reward > 0.0:
                node.meta["confirm_count"] = int(node.meta.get("confirm_count", 0)) + 1
            elif bounded_reward < 0.0:
                node.meta["negative_confirm_count"] = int(node.meta.get("negative_confirm_count", 0)) + 1
                if node.meta.get("shared_feature_atom"):
                    node.meta["false_positive_count"] = int(node.meta.get("false_positive_count", 0)) + 1
            if node.meta.get("plasticity_frozen"):
                continue
            local_reward = (
                bounded_reward * shared_credit_scale
                if node_id in mutable_shared_ids
                else bounded_reward
            )
            node.meta["local_weight"] = _bounded(
                float(node.meta.get("local_weight", 0.0))
                + self.config.eta_m3 * local_reward,
                self.config.max_abs_local_weight,
            )
            if node.meta.get("shared_feature_atom"):
                node.meta["positive_correlation"] = (
                    int(node.meta.get("confirm_count", 0)) / max(1, int(node.meta.get("request_exposures", 0)))
                )
                node.meta["negative_correlation"] = (
                    int(node.meta.get("negative_confirm_count", 0)) / max(1, int(node.meta.get("request_exposures", 0)))
                )
                node.meta["context_coverage"] = int(node.meta.get("reuse_count", 0))
                node.meta["context_precision"] = (
                    int(node.meta.get("confirm_count", 0))
                    / max(1, int(node.meta.get("confirm_count", 0)) + int(node.meta.get("false_positive_count", 0)))
                )
                node.meta["survival_utility"] = (
                    float(node.meta.get("local_weight", 0.0))
                    + 0.01 * int(node.meta.get("reuse_count", 0))
                    - 0.02 * int(node.meta.get("false_positive_count", 0))
                )
        for edge in self.triplet_trainable_edges.get(triplet_id, []):
            if edge.meta.get("plasticity_frozen"):
                continue
            edge.w = _bounded(float(edge.w) + self.config.eta_m3 * bounded_reward, self.config.max_abs_local_weight)
            self.m3_update_count += 1

    def _shared_feature_credit_scale(self, shared_count: int) -> float:
        """Conserve one event's generalized score across shared features.

        A triplet can activate scores of shared atoms.  Giving every atom the
        full TD error duplicates one environmental observation and lets a
        single lucky action lift unrelated choices.  Match responsibility to
        the same aggregation norm used by policy scoring, so the bundle's
        aggregate update is exactly one ordinary local update before bounds.
        Exact/private nodes and edges retain the full action-specific credit.
        """

        count = max(0, int(shared_count))
        if count <= 1:
            return 1.0
        normalization = str(self.config.terminal_score_normalization).lower()
        if normalization == "mean":
            return 1.0
        if normalization == "sqrt":
            return 1.0 / math.sqrt(count)
        if normalization == "sum":
            return 1.0 / count
        raise ValueError(
            "terminal_score_normalization must be mean, sqrt, or sum"
        )

    def _reset_runtime_states(self, node_ids: Iterable[str] | None = None) -> None:
        nodes = self.graph.nodes.values() if node_ids is None else (self.graph.nodes[nid] for nid in node_ids if nid in self.graph.nodes)
        for node in nodes:
            node.state = NodeState.INACTIVE
            node.tick_entered = -1

    def _candidate_triplets_for_board(self, board: chess.Board, legal: Mapping[str, chess.Move]) -> dict[str, str]:
        triplets: dict[str, str] = {}
        for move in legal.values():
            keys = _triplet_keys(board, move, key_mode=self.config.key_mode)
            triplet_id = _triplet_id(*keys)
            if triplet_id in self.triplet_ids:
                triplets[triplet_id] = move.uci()
            if self.config.shared_feature_atoms:
                for candidate_id in self._triplets_from_active_shared_atoms(keys):
                    triplets.setdefault(candidate_id, move.uci())
            elif self.config.key_mode != "exact":
                for candidate_id, _distance in self._nearest_triplets_for_keys(keys):
                    triplets.setdefault(candidate_id, move.uci())
        return triplets

    def _triplets_from_active_shared_atoms(
        self,
        keys: tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]],
    ) -> tuple[str, ...]:
        active_atoms = self._shared_atom_ids_for_keys(keys)
        overlap: dict[str, int] = {}
        for atom_id in active_atoms:
            for triplet_id in self.shared_atom_triplets.get(atom_id, set()):
                overlap[triplet_id] = overlap.get(triplet_id, 0) + 1
        self.scheduler_stats["shared_atom_retrieval_calls"] += 1
        self.scheduler_stats["shared_atom_retrieved_triplets"] += len(overlap)
        ranked = [
            (triplet_id, count)
            for triplet_id, count in overlap.items()
            if count >= self.config.shared_atom_min_overlap
            and triplet_id not in self.pruned_triplet_ids
        ]
        ranked.sort(
            key=lambda row: (
                -row[1],
                -self._triplet_local_utility(row[0]),
                row[0],
            )
        )
        limit = max(0, int(self.config.max_prototype_candidates_per_move))
        if limit == 0 or not ranked:
            return ()

        # Retrieval order is deliberately hybrid: reserve one slot for the
        # strongest learned utility even when overlap puts it below the normal
        # cutoff, then spend the remaining slots on overlap-ranked challengers.
        incumbent = min(
            ranked,
            key=lambda row: (
                -self._triplet_local_utility(row[0]),
                -row[1],
                row[0],
            ),
        )
        selected = [incumbent[0]]
        selected.extend(
            triplet_id
            for triplet_id, _count in ranked
            if triplet_id != incumbent[0]
        )
        return tuple(selected[:limit])

    def _shared_atom_ids_for_keys(
        self,
        keys: tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]],
    ) -> set[str]:
        active: set[str] = set()
        for role, role_keys in (
            ("before_feature", keys[0]),
            ("delta_feature", keys[1]),
            ("after_feature", keys[2]),
        ):
            for key in role_keys:
                atom_id = self.shared_atom_ids_by_key.get((role, key))
                if atom_id is not None:
                    active.add(atom_id)
        if self.config.shared_projection_atoms:
            for key in _projection_atom_keys(*keys):
                atom_id = self.shared_atom_ids_by_key.get(("projection_feature", key))
                if atom_id is not None:
                    active.add(atom_id)
        return active

    def _triplet_root_weight(self, triplet_id: str) -> float:
        edge = self.graph.get_edge(ROOT_ID, triplet_id, LinkType.SUB)
        return float(edge.w) if edge is not None else 0.0

    def _nearest_triplets_for_keys(
        self,
        keys: tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]],
    ) -> list[tuple[str, int]]:
        target = set((*keys[0], *keys[1], *keys[2]))
        candidates: list[tuple[int, str]] = []
        scan_triplets = self._prototype_scan_triplets()
        if len(scan_triplets) < len(self.triplet_ids):
            self.scheduler_stats["prototype_scan_truncated_calls"] += 1
        for triplet_id in scan_triplets:
            candidate_keys = self._triplet_pattern_key_set(triplet_id)
            distance = len(target ^ candidate_keys)
            self.scheduler_stats["prototype_distance_evaluations"] += 1
            if distance <= self.config.prototype_distance_threshold * 3:
                candidates.append((distance, triplet_id))
        candidates.sort()
        return [(triplet_id, distance) for distance, triplet_id in candidates[: self.config.max_prototype_candidates_per_move]]

    def _prototype_scan_triplets(self) -> tuple[str, ...]:
        if len(self.triplet_ids) <= self.config.max_prototype_scan_triplets:
            return tuple(self.triplet_ids)

        def root_weight(triplet_id: str) -> float:
            edge = self.graph.get_edge(ROOT_ID, triplet_id, LinkType.SUB)
            return abs(float(edge.w)) if edge is not None else 0.0

        ranked = sorted(self.triplet_ids, key=lambda item: (root_weight(item), item), reverse=True)
        return tuple(ranked[: self.config.max_prototype_scan_triplets])

    def _triplet_pattern_key_set(self, triplet_id: str) -> set[str]:
        if triplet_id in self.triplet_pattern_key_cache:
            return self.triplet_pattern_key_cache[triplet_id]
        ids = _TripletNodeIds(triplet_id)
        keys: set[str] = set()
        for node_id in (ids.before_terminal, ids.delta_terminal, ids.after_terminal):
            keys.update(self.graph.nodes[node_id].meta.get("pattern_keys", []))
        self.triplet_pattern_key_cache[triplet_id] = keys
        return keys

    def _active_nodes_for_triplets(self, triplet_ids: Iterable[str]) -> set[str]:
        active = {ROOT_ID}
        for triplet_id in triplet_ids:
            for node_id in self.triplet_nodes.get(triplet_id, set()):
                node = self.graph.nodes[node_id]
                if (
                    not self.config.tick_feature_terminals
                    and node.meta.get("role") in {"before_feature", "delta_feature", "after_feature", "projection_feature"}
                    and not node.meta.get("shared_feature_atom")
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
            for node_id in self.triplet_nodes.get(triplet_id, set()):
                node = self.graph.nodes[node_id]
                if (
                    node.meta.get("role") == "composition_feature"
                    and node.state not in terminal_states
                ):
                    return False
        return True

    def _confirmed_action_candidates(
        self,
        legal: Mapping[str, chess.Move],
        triplet_ids: Iterable[str] | None = None,
        candidate_move_by_triplet: Mapping[str, str] | None = None,
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
            move_uci = str((candidate_move_by_triplet or {}).get(triplet_id, action.meta["action_uci"]))
            if move_uci not in legal:
                continue
            stored_action_uci = str(triplet.meta.get("action_uci", action.meta["action_uci"]))
            triplet_weight = (
                float(self.graph.get_edge(ROOT_ID, ids.triplet, LinkType.SUB).w)  # type: ignore[union-attr]
                if move_uci == stored_action_uci
                else 0.0
            )
            terminal_score, active_count = self._confirmed_terminal_score(triplet_id)
            composite_score, composite_count = self._confirmed_composite_score(triplet_id)
            normalization = str(self.config.terminal_score_normalization).lower()
            if normalization == "mean":
                terminal_score /= max(1, active_count)
                composite_score /= max(1, composite_count)
            elif normalization == "sqrt":
                terminal_score /= math.sqrt(max(1, active_count))
                composite_score /= math.sqrt(max(1, composite_count))
            elif normalization != "sum":
                raise ValueError(
                    "terminal_score_normalization must be mean, sqrt, or sum"
                )
            combined_terminal_score = math.fsum(
                (terminal_score, composite_score)
            )
            score = math.fsum((
                self.config.terminal_score_scale * combined_terminal_score,
                self.config.triplet_credit_scale * triplet_weight,
            ))
            candidates.append((score, move_uci, triplet_id))
        return candidates

    def _confirmed_terminal_score(self, triplet_id: str) -> tuple[float, int]:
        ids = _TripletNodeIds(triplet_id)
        count = 0
        contributions: list[tuple[str, float]] = []
        for node_id in sorted(self.triplet_nodes.get(triplet_id, set())):
            node = self.graph.nodes[node_id]
            if node.nid in self.pruned_terminal_ids:
                continue
            if node.ntype != NodeType.TERMINAL:
                continue
            if node.meta.get("role") not in {"before_feature", "delta_feature", "after_feature", "projection_feature"}:
                continue
            if (
                str(node.meta.get("terminal_key", "")).startswith("action_pattern:")
                and not self.config.score_action_pattern_atoms
            ):
                continue
            if node.state not in (NodeState.TRUE, NodeState.CONFIRMED):
                continue
            contributions.append((
                f"{node_id}:local_weight",
                float(node.meta.get("local_weight", 0.0)),
            ))
            if self.config.score_hierarchy_edge_weights:
                parent_id = {
                    "before_feature": ids.before_script,
                    "delta_feature": ids.action_script,
                    "projection_feature": ids.action_script,
                    "after_feature": ids.after_script,
                }[str(node.meta["role"])]
                hierarchy_edge = self.graph.get_edge(
                    parent_id,
                    node.nid,
                    LinkType.SUB,
                )
                if (
                    hierarchy_edge is not None
                    and hierarchy_edge.meta.get("trainable")
                ):
                    contributions.append((
                        f"{parent_id}->{node.nid}:sub_weight",
                        float(hierarchy_edge.w),
                    ))
            count += 1
        return math.fsum(
            value for _identity, value in sorted(contributions)
        ), count


    def _confirmed_composite_score(self, triplet_id: str) -> tuple[float, int]:
        count = 0
        parent_id = _TripletNodeIds(triplet_id).action_script
        contributions: list[tuple[str, float]] = []
        for node_id in sorted(self.triplet_nodes.get(triplet_id, set())):
            node = self.graph.nodes[node_id]
            if node.meta.get("role") != "composition_feature":
                continue
            if str(node.meta.get("stem_cell_id")) in self.disabled_composite_ids:
                continue
            if node.state not in (NodeState.TRUE, NodeState.CONFIRMED):
                continue
            contributions.append((
                f"{node_id}:local_weight",
                float(node.meta.get("local_weight", 0.0)),
            ))
            if self.config.score_hierarchy_edge_weights:
                edge = self.graph.get_edge(parent_id, node_id, LinkType.SUB)
                if edge is not None and edge.meta.get("trainable"):
                    contributions.append((
                        f"{parent_id}->{node_id}:sub_weight",
                        float(edge.w),
                    ))
            count += 1
        return math.fsum(
            value for _identity, value in sorted(contributions)
        ), count


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
    payload = {
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
    if node_type == "SCRIPT":
        payload.update({"confirm_policy": "k_of_n", "confirm_k": 1})
    return payload


def _terminal_meta(stage: str, role: str, action_uci: str, keys: tuple[str, ...]) -> dict[str, Any]:
    payload = _candidate_meta("TERMINAL", stage, role=role, action_uci=action_uci)
    payload.update({
        "pattern_key_count": len(keys),
        "pattern_hash": _hash_keys(keys),
        "pattern_keys": list(keys),
        "grouped_cache_terminal": True,
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
        "shared_feature_atom": False,
    })
    return payload


def _shared_feature_atom_meta(stage: str, role: str, action_uci: str, key: str) -> dict[str, Any]:
    payload = _candidate_meta("TERMINAL", stage, role=role, action_uci=action_uci)
    payload.update({
        "terminal_key": key,
        "pattern_hash": _hash_keys((role, key)),
        "shared_feature_atom": True,
        "terminal_kind": "shared_feature_atom",
        "fan_in_allowed": True,
        "reuse_count": 0,
        "activation_count": 0,
        "negative_confirm_count": 0,
        "false_positive_count": 0,
        "positive_correlation": 0.0,
        "negative_correlation": 0.0,
        "context_coverage": 0,
        "context_precision": 0.0,
        "last_confirm_cycle": -1,
        "survival_utility": 0.0,
    })
    return payload


def _pattern_predicate(role: str, action_uci: str, expected_keys: tuple[str, ...], key_mode: str, distance_threshold: int):
    expected = frozenset(expected_keys)

    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        board = env["board"]
        move = _resolve_runtime_move(node, env, action_uci)
        if move not in board.legal_moves:
            node.activation.value = 0.0
            return True, False
        before_keys, action_delta_keys, after_keys = _cached_runtime_triplet_keys(
            env,
            board,
            move,
            key_mode=key_mode,
        )
        actual = {
            "before": frozenset(before_keys),
            "delta": frozenset(action_delta_keys),
            "after": frozenset(after_keys),
        }[role]
        success = _prototype_match(expected, actual, key_mode=key_mode, distance_threshold=distance_threshold)
        node.activation.value = _prototype_activation(expected, actual, key_mode=key_mode, distance_threshold=distance_threshold)
        return True, success

    return predicate


def _single_key_predicate(role: str, action_uci: str, expected_key: str, key_mode: str, distance_threshold: int):
    key_role = {
        "before_feature": "before",
        "delta_feature": "delta",
        "after_feature": "after",
    }[role]

    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        board = env["board"]
        move = _resolve_runtime_move(node, env, action_uci)
        if move not in board.legal_moves:
            node.activation.value = 0.0
            return True, False
        before_keys, action_delta_keys, after_keys = _cached_runtime_triplet_keys(
            env,
            board,
            move,
            key_mode=key_mode,
        )
        actual = {
            "before": before_keys,
            "delta": action_delta_keys,
            "after": after_keys,
        }[key_role]
        success = expected_key in actual if key_mode == "exact" else True
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _shared_atom_predicate(role: str, expected_key: str, key_mode: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        board = env["board"]
        if "shared_atom_move_uci" in env:
            move = chess.Move.from_uci(str(env["shared_atom_move_uci"]))
        else:
            move = _resolve_runtime_move(node, env, str(node.meta.get("action_uci", "0000")))
        if move not in board.legal_moves:
            node.activation.value = 0.0
            return True, False
        before_keys, action_delta_keys, after_keys = _cached_runtime_triplet_keys(
            env,
            board,
            move,
            key_mode=key_mode,
        )
        actual = {
            "before_feature": before_keys,
            "delta_feature": action_delta_keys,
            "after_feature": after_keys,
            "projection_feature": _projection_atom_keys(before_keys, action_delta_keys, after_keys),
        }[role]
        success = expected_key in actual
        if success:
            node.meta["activation_count"] = int(node.meta.get("activation_count", 0)) + 1
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _cached_runtime_triplet_keys(
    env: dict[str, Any],
    board: chess.Board,
    move: chess.Move,
    *,
    key_mode: str,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    cache = env.setdefault("__triplet_keys_cache", {})
    key = (board.fen(), move.uci(), str(key_mode))
    cached = cache.get(key)
    if cached is None:
        cached = _triplet_keys(board, move, key_mode=key_mode)
        cache[key] = cached
    return cached


def _prototype_match(
    expected: frozenset[str],
    actual: frozenset[str],
    *,
    key_mode: str,
    distance_threshold: int,
) -> bool:
    if key_mode == "exact":
        return expected == actual
    return len(expected ^ actual) <= distance_threshold


def _prototype_activation(
    expected: frozenset[str],
    actual: frozenset[str],
    *,
    key_mode: str,
    distance_threshold: int,
) -> float:
    if key_mode == "exact":
        return 1.0 if expected == actual else 0.0
    distance = len(expected ^ actual)
    return max(0.0, 1.0 - (distance / max(1, distance_threshold + 1)))


def _action_predicate(action_uci: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        board = env["board"]
        move = _resolve_runtime_move(node, env, action_uci)
        success = move in board.legal_moves
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _resolve_runtime_move(node: Node, env: dict[str, Any], fallback_uci: str) -> chess.Move:
    triplet_id = node.meta.get("triplet_id")
    move_uci = env.get("candidate_move_by_triplet", {}).get(triplet_id, fallback_uci)
    return chess.Move.from_uci(str(move_uci))


def _triplet_keys(board: chess.Board, move: chess.Move, *, key_mode: str = "exact") -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    after = board.copy(stack=False)
    after.push(move)
    before_features = extract_terminal_feature_vector(board)
    after_features = extract_terminal_feature_vector(after)
    before_keys = tuple(
        f"before_terminal:{key}={_bucket(value)}"
        for key, value in sorted(_mode_features(before_features, key_mode=key_mode).items())
    )
    after_keys = tuple(
        f"after_terminal:{key}={_bucket(value)}"
        for key, value in sorted(_mode_features(after_features, key_mode=key_mode).items())
    )
    action_delta_keys = [
        key
        for key, _scale in terminal_action_feature_keys(board, move)
        if key.startswith("action_pattern:")
    ]
    if key_mode == "exact":
        action_delta_keys.extend(_native_precise_action_keys(board, move))
    else:
        action_delta_keys = [key for key in action_delta_keys if _keep_generalized_action_key(key)]
    before_mode = _mode_features(before_features, key_mode=key_mode)
    after_mode = _mode_features(after_features, key_mode=key_mode)
    for key in sorted(before_mode.keys() & after_mode.keys()):
        action_delta_keys.append(f"delta_terminal:{key}={_delta_bucket(after_mode[key] - before_mode[key])}")
    validate_learner_record([*before_keys, *action_delta_keys, *after_keys])
    return before_keys, tuple(action_delta_keys), after_keys


def _mode_features(features: Mapping[str, float], *, key_mode: str) -> dict[str, float]:
    if key_mode == "exact":
        return dict(features)
    payload = {
        key: value
        for key, value in features.items()
        if key not in {
            "white_king_file",
            "white_king_rank",
            "white_rook_file",
            "white_rook_rank",
            "black_king_file",
            "black_king_rank",
        }
    }
    if key_mode == "canonical":
        for key in (
            "black_king_nearest_edge_distance",
            "white_king_to_black_king_distance",
            "white_rook_to_black_king_distance",
            "white_king_to_rook_distance",
            "black_reply_mobility",
            "rook_attacked_by_black",
            "is_check",
            "is_checkmate",
            "is_stalemate",
        ):
            if key in features:
                payload[f"canonical:{key}"] = features[key]
    return payload


def _keep_generalized_action_key(key: str) -> bool:
    forbidden_parts = (
        "from_file_edge_distance",
        "from_rank_edge_distance",
        "to_file_edge_distance",
        "to_rank_edge_distance",
    )
    return not any(part in key for part in forbidden_parts)


def _projection_atom_keys(
    before_keys: tuple[str, ...],
    action_delta_keys: tuple[str, ...],
    after_keys: tuple[str, ...],
) -> tuple[str, ...]:
    before = set(before_keys)
    delta = set(action_delta_keys)
    after = set(after_keys)
    projections: list[str] = []
    if "before_terminal:feature_hub_enemy_king_at_edge=1" in before and "before_terminal:king_same_rank=1" in before:
        projections.append("projection_atom:before:edge_and_same_rank_relation")
    if "before_terminal:feature_hub_enemy_king_at_edge=1" in before and "before_terminal:king_same_file=1" in before:
        projections.append("projection_atom:before:edge_and_same_file_relation")
    if "before_terminal:rook_safe=1" in before and any(key == "before_terminal:black_reply_mobility=1" or key == "before_terminal:black_reply_mobility=0" for key in before):
        projections.append("projection_atom:before:rook_safe_low_reply_mobility")
    if "action_pattern:gives_check=1" in delta and "action_pattern:rook_attacked_after=0" in delta:
        projections.append("projection_atom:action:gives_check_and_rook_safe_after")
    if "action_pattern:gives_check=1" in delta and "action_pattern:black_reply_mobility_after=0" in delta:
        projections.append("projection_atom:action:gives_check_and_zero_reply_mobility")
    if "delta_terminal:black_reply_mobility=negative" in delta:
        projections.append("projection_atom:delta:reply_mobility_decreases")
    if "delta_terminal:black_king_nearest_edge_distance=negative" in delta:
        projections.append("projection_atom:delta:edge_distance_decreases")
    if "delta_terminal:confinement_area=negative" in delta:
        projections.append("projection_atom:delta:confinement_area_decreases")
    if "after_terminal:black_reply_mobility=0" in after and "after_terminal:is_stalemate=0" in after:
        projections.append("projection_atom:after:zero_reply_mobility_not_stalemate")
    if "after_terminal:is_check=1" in after and "after_terminal:rook_safe=1" in after:
        projections.append("projection_atom:after:check_and_rook_safe")
    if "after_terminal:rook_attacked_by_black=0" in after and "after_terminal:is_stalemate=0" in after:
        projections.append("projection_atom:after:safe_rook_non_stalemate")
    validate_learner_record(projections)
    return tuple(sorted(dict.fromkeys(projections)))


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


def _shared_feature_atom_id(role: str, key: str) -> str:
    digest = _hash_keys((role, key))[:20]
    return f"tg26s_shared_atom_{digest}"


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


def _distribution(values: Iterable[int]) -> dict[str, Any]:
    ordered = sorted(int(value) for value in values)
    if not ordered:
        return {"count": 0, "min": 0, "p50": 0, "p90": 0, "max": 0}

    def percentile(fraction: float) -> int:
        index = min(len(ordered) - 1, int(round((len(ordered) - 1) * fraction)))
        return ordered[index]

    return {
        "count": len(ordered),
        "min": ordered[0],
        "p50": percentile(0.50),
        "p90": percentile(0.90),
        "max": ordered[-1],
    }
