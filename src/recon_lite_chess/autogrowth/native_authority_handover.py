"""Trainer-free native R0 inference and graph-owned R0->R1 handover."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
import copy
import hashlib
import json
import math
from pathlib import Path
import pickle
from typing import Any, Iterable, Iterator, Mapping, Sequence
from unittest.mock import patch

import chess

from recon_lite import (
    AnonymousChoiceGenome,
    AnonymousChoiceOption,
    ChildResponse,
    FormalReConEngine,
    FrameContext,
    FrameEffectFirewall,
    FrameKind,
    Graph,
    LinkType,
    Node,
    NodeState,
    NodeType,
    child_response_terminal,
    prediction_residual_terminal,
)
from recon_lite_hector.learning import IntrinsicCreditEngine

from .native_single_graph_curriculum import (
    ROOT_ID,
    NativeReConKRKGraph,
    _TripletNodeIds,
    _triplet_keys,
)


SCHEMA_VERSION = "native_r0_authority_organism.v1"
ACTUATOR_PREFIX = "chess_move:"
_TERMINAL_STATES = {NodeState.TRUE, NodeState.CONFIRMED, NodeState.FAILED}


class HostAuthorityViolation(RuntimeError):
    """Raised when an experimental path attempts an obsolete host choice."""


@contextmanager
def native_authority_tripwires() -> Iterator[dict[str, int]]:
    """Fail hard if the experimental path reaches retired host authority."""

    counts = {
        "weighted_selector": 0,
        "provider_fallback": 0,
        "child_priority": 0,
    }

    def weighted(*_args: Any, **_kwargs: Any) -> Any:
        counts["weighted_selector"] += 1
        raise HostAuthorityViolation("old Python weighted selector is forbidden")

    def provider(*_args: Any, **_kwargs: Any) -> Any:
        counts["provider_fallback"] += 1
        raise HostAuthorityViolation("old child provider fallback is forbidden")

    def priority(*_args: Any, **_kwargs: Any) -> Any:
        counts["child_priority"] += 1
        raise HostAuthorityViolation("_choose_with_child_priority is forbidden")

    module = "recon_lite_chess.autogrowth.native_intrinsic_curriculum"
    with (
        patch.object(NativeReConKRKGraph, "choose", weighted),
        patch.object(NativeReConKRKGraph, "audit_choice", weighted),
        patch(f"{module}._r0_available", provider),
        patch(f"{module}._r0_available_with_dispatch_cache", provider),
        patch(f"{module}._choose_with_child_priority", priority),
    ):
        yield counts


@dataclass(frozen=True)
class FrozenCompetenceProvenance:
    child_id: str
    mature: bool
    grounded: bool
    can_emit: bool
    consolidated_value: float
    uncertainty: float
    terminal_evidence: int
    causal_confirmations: int
    grounding_level: int | None
    grounding_source: str
    completion_terminal_kind: str = "mate"

    @classmethod
    def from_credit(cls, credit: IntrinsicCreditEngine, child_id: str) -> "FrozenCompetenceProvenance":
        state = credit.states[child_id]
        confidence = state.confidence(credit.config)
        return cls(
            child_id=child_id,
            mature=bool(state.mature),
            grounded=state.grounding_level is not None,
            can_emit=state.can_emit(credit.config),
            consolidated_value=float(state.slow_value),
            uncertainty=max(0.0, min(1.0, 1.0 - confidence)),
            terminal_evidence=int(state.terminal_evidence),
            causal_confirmations=int(state.causal_confirmations),
            grounding_level=state.grounding_level,
            grounding_source=(
                f"observed_terminal_outcomes:{state.terminal_evidence};"
                f"paired_causal_confirmations:{state.causal_confirmations}"
            ),
        )


@dataclass(frozen=True)
class GraphActuation:
    actuator_identity: str
    move_uci: str
    option_identity: str
    activation: float
    candidate_count: int
    formal_ticks: int
    graph_owned: bool = True
    host_fallback: bool = False


@dataclass(frozen=True)
class GraphTerminalSignal:
    identity: str
    role: str
    source_node_identity: str
    terminal_kind: str
    provenance: str
    stem_cell_identity: str | None = None


@dataclass(frozen=True)
class GraphSignalTrace:
    frame_id: str
    frame_kind: str
    source_organism_identity: str
    source_state_identity: str
    option_identity: str
    actuation: GraphActuation
    confirmed_base_terminal_node_ids: tuple[str, ...]
    confirmed_mature_composite_ids: tuple[str, ...]
    terminal_signals: tuple[GraphTerminalSignal, ...]

    @property
    def ordered_signal_identities(self) -> tuple[str, ...]:
        return tuple(signal.identity for signal in self.terminal_signals)

    def canonical_manifest(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "frame_kind": self.frame_kind,
            "source_organism_identity": self.source_organism_identity,
            "source_state_identity": self.source_state_identity,
            "option_identity": self.option_identity,
            "actuation": asdict(self.actuation),
            "confirmed_base_terminal_node_ids": list(
                self.confirmed_base_terminal_node_ids
            ),
            "confirmed_mature_composite_ids": list(
                self.confirmed_mature_composite_ids
            ),
            "terminal_signals": [asdict(item) for item in self.terminal_signals],
        }

    def digest(self) -> str:
        return hashlib.sha256(
            json.dumps(
                self.canonical_manifest(), sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True)
class _OptionSignalCapture:
    option_identity: str
    base_terminal_node_ids: tuple[str, ...]
    mature_composite_ids: tuple[str, ...]
    terminal_signals: tuple[GraphTerminalSignal, ...]


@dataclass(frozen=True)
class DreamFirewallCanary:
    rejected_operations: tuple[str, ...]
    persistent_mutation_count: int
    board_isolated: bool
    clone_mutations_exercised: tuple[str, ...]


@dataclass(frozen=True)
class ChildQuery:
    response: ChildResponse
    actuation: GraphActuation | None
    frame_id: str
    persistent_mutation_count: int
    effect_attempts: tuple[Mapping[str, Any], ...]
    active_competence_signal_ids: tuple[str, ...] = ()
    availability_provenance: Mapping[str, Any] | None = None
    graph_signal_trace: GraphSignalTrace | None = None



class NativeR0DreamSession:
    """One isolated graph clone reused across frame-local child requests."""

    def __init__(self, organism: "NativeR0Organism") -> None:
        self.organism = organism
        self.persistent_digest = organism.persistent_state_audit()[
            "exact_state_sha256"
        ]
        self.virtual_graph = copy.deepcopy(organism.graph)
        self.virtual_credit = copy.deepcopy(organism.credit)
        self.closed = False

    def request(self, frame: FrameContext) -> ChildQuery:
        if self.closed:
            raise RuntimeError("dream session is closed")
        if frame.kind is not FrameKind.VIRTUAL:
            raise ValueError("R0 child requests require a virtual frame")
        runtime = frame.to_env_overlay()
        firewall = FrameEffectFirewall()
        runtime["__frame_effects__"] = firewall
        board = runtime.get("board")
        if not isinstance(board, chess.Board):
            raise TypeError("virtual R0 frame requires a chess.Board")
        virtual = NativeR0Organism(
            graph=self.virtual_graph,
            credit=self.virtual_credit,
            provenance=self.organism.provenance,
            frozen_triplet_ids=self.organism.frozen_triplet_ids,
            source_manifest=self.organism.source_manifest,
            retrieval_budget_per_actuator=self.organism.retrieval_budget_per_actuator,
        )
        actuation, signal_trace = virtual.emit_action_with_trace(frame)
        mutation_count = int(
            self.organism.persistent_state_audit()["exact_state_sha256"]
            != self.persistent_digest
        )
        if mutation_count:
            raise RuntimeError("virtual R0 request mutated the persistent organism")
        policy_response = actuation is not None
        grounded = bool(
            self.organism.provenance.grounded
            and self.organism.provenance.can_emit
        )
        response = ChildResponse(
            child_id=self.organism.provenance.child_id,
            confirmed=policy_response,
            policy_response=policy_response,
            available=policy_response,
            expected_value=(
                self.organism.provenance.consolidated_value
                if policy_response
                else 0.0
            ),
            uncertainty=self.organism.provenance.uncertainty,
            grounded=grounded,
            grounding_source=(
                self.organism.provenance.grounding_source if grounded else None
            ),
        )
        return ChildQuery(
            response=response,
            actuation=actuation,
            frame_id=frame.frame_id,
            persistent_mutation_count=mutation_count,
            effect_attempts=tuple(dict(row) for row in firewall.attempts),
            graph_signal_trace=signal_trace,
        )

    def close(self) -> None:
        if (
            self.organism.persistent_state_audit()["exact_state_sha256"]
            != self.persistent_digest
        ):
            raise RuntimeError("dream session leaked into the persistent organism")
        self.closed = True


@dataclass
class NativeR0Organism:
    """Serialized learned graph plus generic genome; no trainer is retained."""

    graph: NativeReConKRKGraph
    credit: IntrinsicCreditEngine
    provenance: FrozenCompetenceProvenance
    frozen_triplet_ids: frozenset[str]
    source_manifest: Mapping[str, Any]
    retrieval_budget_per_actuator: int = 16
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported organism schema: {self.schema_version}")
        if not self.provenance.can_emit:
            raise ValueError("R0 organism must be mature, grounded, and causally confirmed")
        if not self.frozen_triplet_ids:
            raise ValueError("R0 organism requires a non-empty frozen learned graph")
        if self.retrieval_budget_per_actuator < 1:
            raise ValueError("retrieval_budget_per_actuator must be positive")
        self.trace_state_identity()

    def __getstate__(self) -> dict[str, Any]:
        """Serialize learned state with canonical transient runtime values."""

        state = dict(self.__dict__)
        graph = copy.deepcopy(self.graph)
        graph.normalize_inference_runtime()
        state["graph"] = graph
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)
        if not hasattr(self, "retrieval_budget_per_actuator"):
            self.retrieval_budget_per_actuator = 16
        self.graph.normalize_inference_runtime()
        if not hasattr(self, "_trace_state_identity_cache"):
            self.trace_state_identity()

    def persistent_state_audit(self) -> Mapping[str, str]:
        """Hash every persistent component, including unnormalized runtime fields."""

        exact_graph = copy.deepcopy(self.graph)
        for node in exact_graph.graph.nodes.values():
            node.predicate = None
        exact_payload = {
            "graph_dict": exact_graph.__dict__,
            "credit": copy.deepcopy(self.credit),
            "provenance": self.provenance,
            "frozen_triplet_ids": self.frozen_triplet_ids,
            "source_manifest": dict(self.source_manifest),
            "retrieval_budget": self.retrieval_budget_per_actuator,
            "schema_version": self.schema_version,
        }
        topology = {
            "nodes": sorted(
                (nid, node.ntype.name)
                for nid, node in self.graph.graph.nodes.items()
            ),
            "edges": sorted(
                (edge.src, edge.dst, edge.ltype.name)
                for edge in self.graph.graph.edges
            ),
            "triplet_ids": sorted(self.graph.triplet_ids),
            "triplet_nodes": {
                key: sorted(value)
                for key, value in sorted(self.graph.triplet_nodes.items())
            },
            "composite_members": {
                key: list(value)
                for key, value in sorted(
                    self.graph.composite_member_ids.items()
                )
            },
        }
        weights = {
            "edges": sorted(
                (
                    edge.src,
                    edge.dst,
                    edge.ltype.name,
                    float(edge.w),
                )
                for edge in self.graph.graph.edges
            ),
            "node_local_weights": sorted(
                (
                    nid,
                    float(node.meta.get("local_weight", 0.0)),
                )
                for nid, node in self.graph.graph.nodes.items()
            ),
        }
        lifecycle = {
            "composite_cells": {
                key: cell.to_dict()
                for key, cell in sorted(self.graph.composite_cells.items())
            },
            "pruned_terminal_ids": sorted(self.graph.pruned_terminal_ids),
            "pruned_triplet_ids": sorted(self.graph.pruned_triplet_ids),
            "disabled_composite_ids": sorted(
                self.graph.disabled_composite_ids
            ),
            "provenance": asdict(self.provenance),
        }
        def digest(value: Any) -> str:
            return hashlib.sha256(
                pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            ).hexdigest()
        return {
            "topology_sha256": digest(topology),
            "weights_sha256": digest(weights),
            "credit_sha256": digest(self.credit),
            "lifecycle_sha256": digest(lifecycle),
            "exact_state_sha256": digest(exact_payload),
            "serialized_state_sha256": hashlib.sha256(
                pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)
            ).hexdigest(),
        }
    def trace_state_identity(self) -> str:
        cached = getattr(self, "_trace_state_identity_cache", None)
        if cached is not None:
            return str(cached)
        audit = self.persistent_state_audit()
        payload = {key: audit[key] for key in (
            "topology_sha256", "weights_sha256", "credit_sha256",
            "lifecycle_sha256",
        )}
        identity = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()
        self._trace_state_identity_cache = identity
        return identity

    def source_organism_identity(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "child_id": self.provenance.child_id,
            "frozen_policy_token": self.graph.frozen_policy_token,
            "frozen_triplet_ids": sorted(self.frozen_triplet_ids),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()

    def emit_action_with_trace(
        self, frame: FrameContext
    ) -> tuple[GraphActuation | None, GraphSignalTrace | None]:
        """Emit exactly one action and its immutable selected-option trace."""

        if not isinstance(frame, FrameContext):
            raise TypeError("trace-native R0 execution requires FrameContext")
        runtime = frame.to_env_overlay()
        board = runtime.get("board")
        if not isinstance(board, chess.Board):
            raise TypeError("trace-native R0 frame requires a chess.Board")
        source_state_identity = self.trace_state_identity()
        runtime_policy = self.graph.frame_runtime_copy()
        options, ticks, captures = _formal_native_options(
            runtime_policy,
            board,
            allowed_triplets=self.frozen_triplet_ids,
            per_actuator_budget=self.retrieval_budget_per_actuator,
        )
        if not options:
            return None, None
        emission = AnonymousChoiceGenome().emit(options)
        if not emission.actuator_identity.startswith(ACTUATOR_PREFIX):
            raise RuntimeError("formal graph emitted a non-chess actuator identity")
        move_uci = emission.actuator_identity[len(ACTUATOR_PREFIX):]
        if move_uci not in {move.uci() for move in board.legal_moves}:
            raise RuntimeError("formal graph emitted an illegal actuator identity")
        actuation = GraphActuation(
            actuator_identity=emission.actuator_identity,
            move_uci=move_uci,
            option_identity=emission.option_identity,
            activation=emission.activation,
            candidate_count=len(options),
            formal_ticks=ticks + emission.formal_ticks,
        )
        capture = captures.get(emission.option_identity)
        if capture is None:
            raise RuntimeError("selected graph option has no frame-local trace")
        policy_signal = GraphTerminalSignal(
            identity="internal:policy_response",
            role="POLICY_RESPONSE",
            source_node_identity=emission.option_identity,
            terminal_kind="graph_choice_actuator",
            provenance="selected_graph_option_emitted_actuator",
        )
        trace = GraphSignalTrace(
            frame_id=frame.frame_id,
            frame_kind=frame.kind.name,
            source_organism_identity=self.source_organism_identity(),
            source_state_identity=source_state_identity,
            option_identity=emission.option_identity,
            actuation=actuation,
            confirmed_base_terminal_node_ids=capture.base_terminal_node_ids,
            confirmed_mature_composite_ids=capture.mature_composite_ids,
            terminal_signals=tuple(sorted(
                (*capture.terminal_signals, policy_signal),
                key=lambda item: item.identity,
            )),
        )
        return actuation, trace

    def emit_action(self, board: chess.Board) -> GraphActuation | None:
        """Historical action-only facade; production competence uses traces."""

        frame = FrameContext(
            frame_id="legacy-action:" + hashlib.sha256(
                board.fen().encode("utf-8")
            ).hexdigest(),
            kind=FrameKind.REAL,
            values={"board": board},
        )
        actuation, _trace = self.emit_action_with_trace(frame)
        return actuation


    def request_child(self, frame: FrameContext) -> ChildQuery:
        """Formally request the actual frozen R0 graph in an isolated dream."""

        session = NativeR0DreamSession(self)
        try:
            return session.request(frame)
        finally:
            session.close()

    def dream_session(self) -> NativeR0DreamSession:
        return NativeR0DreamSession(self)

    def save(self, path: str | Path) -> Mapping[str, Any]:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)
        output.write_bytes(payload)
        metadata = {
            "schema_version": self.schema_version,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "byte_count": len(payload),
            "frozen_triplet_count": len(self.frozen_triplet_ids),
            "frozen_policy_token": self.graph.frozen_policy_token,
            "provenance": asdict(self.provenance),
            "trainer_object_serialized": False,
            "organism_parts": [
                "serialized_learned_graph",
                "generic_choice_genome",
                "generic_credit_and_grounding_state",
            ],
        }
        output.with_suffix(output.suffix + ".json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return metadata

    @classmethod
    def load(cls, path: str | Path) -> "NativeR0Organism":
        source = Path(path)
        payload = source.read_bytes()
        metadata_path = source.with_suffix(source.suffix + ".json")
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if hashlib.sha256(payload).hexdigest() != metadata["sha256"]:
                raise RuntimeError("R0 organism artifact hash mismatch")
        restored = pickle.loads(payload)
        if not isinstance(restored, cls):
            raise TypeError("artifact is not a NativeR0Organism")
        if restored.schema_version != SCHEMA_VERSION:
            raise ValueError("R0 organism schema mismatch")
        if not hasattr(restored, "retrieval_budget_per_actuator"):
            restored.retrieval_budget_per_actuator = 16
        return restored


@dataclass(frozen=True)
class HandoverDecision:
    actuation: GraphActuation
    response_slots: Mapping[str, tuple[ChildQuery, ...]]
    graph_node_count: int
    graph_edge_count: int
    actuator_multiplicity: int
    planted_response_count: int
    host_fallback_count: int


class NativeHandoverGenome:
    """Materialize anonymous all-replies and exactly-one action topology."""

    def query_child_slots(
        self,
        board: chess.Board,
        child: NativeR0Organism,
        *,
        session_audit: Any | None = None,
    ) -> tuple[
        dict[str, tuple[ChildQuery, ...]],
        dict[tuple[str, int], FrameContext],
    ]:
        """Measure actual child emissions; make no choice and expose no scores."""

        legal = tuple(sorted(board.legal_moves, key=lambda move: move.uci()))
        slots: dict[str, tuple[ChildQuery, ...]] = {}
        successor_frames: dict[tuple[str, int], FrameContext] = {}
        session = (
            child.dream_session()
            if session_audit is None
            else child.dream_session(audit=session_audit)
        )
        try:
            for move in legal:
                after = board.copy(stack=False)
                after.push(move)
                queries: list[ChildQuery] = []
                for reply_index, reply in enumerate(
                    sorted(after.legal_moves, key=lambda item: item.uci())
                ):
                    successor = after.copy(stack=False)
                    successor.push(reply)
                    frame = FrameContext(
                        frame_id=f"dream:{move.uci()}:{reply.uci()}",
                        kind=FrameKind.VIRTUAL,
                        values={"board": successor},
                        hypothetical_action=move.uci(),
                    )
                    successor_frames[(move.uci(), reply_index)] = frame
                    queries.append(session.request(frame))
                slots[move.uci()] = tuple(queries)
        finally:
            session.close()
        return slots, successor_frames

    def decide(
        self,
        board: chess.Board,
        child: NativeR0Organism,
        *,
        arm: str,
        shuffle_seed: int = 0,
    ) -> HandoverDecision:
        slots, frames = self.query_child_slots(board, child)
        return self.decide_from_measured_slots(
            board,
            slots,
            frames,
            arm=arm,
            shuffle_seed=shuffle_seed,
        )

    def decide_from_measured_slots(
        self,
        board: chess.Board,
        measured_slots: Mapping[str, tuple[ChildQuery, ...]],
        successor_frames: Mapping[tuple[str, int], FrameContext],
        *,
        arm: str,
        shuffle_seed: int = 0,
    ) -> HandoverDecision:
        """Route exact child emissions through paired graph controls."""

        if arm not in {"actual_child", "disconnected", "shuffled"}:
            raise ValueError(f"unsupported handover arm: {arm}")
        legal = tuple(sorted(board.legal_moves, key=lambda move: move.uci()))
        if not legal:
            raise RuntimeError("cannot decide without legal actions")
        slots = {key: tuple(value) for key, value in measured_slots.items()}
        if arm == "shuffled":
            slots = _shuffle_response_slots(slots, seed=shuffle_seed)
        graph, env = _materialize_parent_choice(
            legal,
            slots,
            frames=successor_frames,
            connect_child=arm != "disconnected",
        )
        engine = FormalReConEngine(graph, record_trace=False)
        engine.request("handover_choice_root")
        engine.run(
            max_ticks=64,
            env=env,
            until=lambda item: item.g.nodes["handover_choice_root"].state
            in {NodeState.CONFIRMED, NodeState.FAILED},
        )
        emitted = engine.emitted_actuator_identities("handover_choice_root")
        actuator = engine.emit_exactly_one_actuator("handover_choice_root")
        move_uci = actuator[len(ACTUATOR_PREFIX):]
        selected_id = str(
            graph.nodes["handover_choice_root"].meta["choice_selected_child"]
        )
        option = graph.nodes[selected_id]
        actuation = GraphActuation(
            actuator_identity=actuator,
            move_uci=move_uci,
            option_identity=str(option.meta["anonymous_option_identity"]),
            activation=float(option.activation.value),
            candidate_count=len(legal),
            formal_ticks=engine.tick,
        )
        return HandoverDecision(
            actuation=actuation,
            response_slots=slots,
            graph_node_count=len(graph.nodes),
            graph_edge_count=len(graph.edges),
            actuator_multiplicity=len(emitted),
            planted_response_count=0,
            host_fallback_count=0,
        )


def run_dream_firewall_canary(
    organism: NativeR0Organism,
    board: chess.Board,
) -> DreamFirewallCanary:
    """Exercise capability rejection and explicit clone isolation."""

    graph_before = _pickle_digest(organism.graph)
    credit_before = _pickle_digest(organism.credit)
    board_before = board.fen()
    frame = FrameContext(
        frame_id="dream-firewall-canary",
        kind=FrameKind.VIRTUAL,
        values={"board": board},
        hypothetical_action="anonymous-canary",
    )
    runtime = frame.to_env_overlay()
    runtime_board = runtime["board"]
    assert isinstance(runtime_board, chess.Board)
    virtual_graph = copy.deepcopy(organism.graph)
    virtual_credit = copy.deepcopy(organism.credit)
    firewall = FrameEffectFirewall()
    operations = (
        ("weight", firewall.update_weight),
        ("lifecycle", firewall.update_lifecycle),
        ("reservoir", firewall.update_reservoir),
        ("maturity", firewall.set_maturity),
        ("reward", firewall.reward),
        ("topology", firewall.update_topology),
        ("actuation", firewall.actuate),
    )
    for name, operation in operations:
        try:
            operation(name)
        except Exception:
            pass
    clone_mutations: list[str] = []
    if virtual_graph.graph.edges:
        virtual_graph.graph.edges[0].w = 999.0
        clone_mutations.append("weight")
    virtual_graph.graph.nodes[ROOT_ID].meta["dream_lifecycle"] = "mutated"
    clone_mutations.append("lifecycle")
    virtual_graph.graph.add_node(Node("dream_only_topology", NodeType.TERMINAL))
    clone_mutations.append("topology")
    virtual_credit.states[organism.provenance.child_id].mature = False
    clone_mutations.append("maturity")
    moves = list(runtime_board.legal_moves)
    if moves:
        runtime_board.push(moves[0])
        clone_mutations.append("board")
    persistent = int(_pickle_digest(organism.graph) != graph_before)
    persistent += int(_pickle_digest(organism.credit) != credit_before)
    persistent += int(board.fen() != board_before)
    return DreamFirewallCanary(
        rejected_operations=tuple(str(row["operation"]) for row in firewall.attempts),
        persistent_mutation_count=persistent,
        board_isolated=board.fen() == board_before,
        clone_mutations_exercised=tuple(clone_mutations),
    )


def measure_prediction_residual(imagined: ChildResponse, observed: ChildResponse) -> float:
    """Record raw residual on a real frame; never create credit or maturity."""

    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    graph.add_node(Node(
        "prediction_residual",
        NodeType.TERMINAL,
        predicate=prediction_residual_terminal,
    ))
    graph.add_hierarchy_pair("root", "prediction_residual")
    frame = FrameContext(
        frame_id="observed-successor",
        kind=FrameKind.REAL,
        values={
            "imagined_child_response": imagined,
            "observed_child_response": observed,
        },
    )
    engine = FormalReConEngine(graph, record_trace=False)
    engine.request("root")
    engine.run(max_ticks=12, env=frame.to_env_overlay(), until=lambda item: item.g.nodes["root"].state in _TERMINAL_STATES)
    return float(graph.nodes["prediction_residual"].activation.value)


def _formal_native_options(
    policy: NativeReConKRKGraph,
    board: chess.Board,
    *,
    allowed_triplets: Iterable[str],
    per_actuator_budget: int,
) -> tuple[tuple[AnonymousChoiceOption, ...], int, dict[str, _OptionSignalCapture]]:
    """Formally confirm graph branches without the legacy Python selector."""

    legal = {move.uci(): move for move in board.legal_moves}
    allowed = frozenset(allowed_triplets)
    pairs: list[tuple[str, str, int]] = []
    seen: set[tuple[str, str]] = set()
    if policy.config.shared_feature_atoms:
        for move_uci, move in legal.items():
            keys = _triplet_keys(board, move, key_mode=policy.config.key_mode)
            retrieved = policy._triplets_from_active_shared_atoms(keys)
            for rank, triplet_id in enumerate(retrieved[: max(1, int(per_actuator_budget))]):
                pair = (triplet_id, move_uci)
                if triplet_id in allowed and pair not in seen:
                    seen.add(pair)
                    pairs.append((triplet_id, move_uci, rank))
    else:
        for triplet_id, move_uci in policy._candidate_triplets_for_board(board, legal).items():
            if triplet_id in allowed:
                pairs.append((triplet_id, move_uci, 0))
    options: list[AnonymousChoiceOption] = []
    total_ticks = 0
    captures: dict[str, _OptionSignalCapture] = {}

    for triplet_id, move_uci, _rank in pairs:
        ids = _TripletNodeIds(triplet_id)
        active_nodes = policy._active_nodes_for_triplets({triplet_id})
        policy._reset_runtime_states(active_nodes)
        env: dict[str, Any] = {
            "board": board,
            "candidate_move_by_triplet": {triplet_id: move_uci},
            "shared_atom_move_uci": move_uci,
        }
        engine = FormalReConEngine(policy.graph, validate_pairs=False, record_trace=False)
        engine.request(ROOT_ID)
        engine.run(
            max_ticks=policy.config.max_ticks,
            env=env,
            active_nodes=active_nodes,
            until=lambda _item, current=triplet_id: policy._candidate_triplets_settled({current}),
        )
        total_ticks += engine.tick
        triplet = policy.graph.nodes[ids.triplet]
        action = policy.graph.nodes[ids.action]
        if triplet.state not in {NodeState.TRUE, NodeState.CONFIRMED}:
            continue
        if action.state not in {NodeState.TRUE, NodeState.CONFIRMED}:
            continue
        if move_uci not in legal:
            continue
        stored = str(triplet.meta.get("action_uci", action.meta["action_uci"]))
        root_edge = policy.graph.get_edge(ROOT_ID, ids.triplet, LinkType.SUB)
        triplet_weight = float(root_edge.w) if root_edge is not None and move_uci == stored else 0.0
        terminal_score, terminal_count = policy._confirmed_terminal_score(triplet_id)
        composite_score, composite_count = policy._confirmed_composite_score(triplet_id)
        normalization = str(policy.config.terminal_score_normalization).lower()
        if normalization == "mean":
            terminal_score /= max(1, terminal_count)
            composite_score /= max(1, composite_count)
        elif normalization == "sqrt":
            terminal_score /= math.sqrt(max(1, terminal_count))
            composite_score /= math.sqrt(max(1, composite_count))
        elif normalization != "sum":
            raise ValueError("unsupported terminal score normalization")
        combined_terminal_score = math.fsum(
            (terminal_score, composite_score)
        )
        strength = math.fsum((
            policy.config.terminal_score_scale * combined_terminal_score,
            policy.config.triplet_credit_scale * triplet_weight,
        ))
        option_identity = f"{triplet_id}:{move_uci}"
        base_ids = tuple(sorted(
            node_id for node_id in policy.triplet_nodes.get(triplet_id, set())
            if node_id in policy.graph.nodes
            and policy.graph.nodes[node_id].ntype == NodeType.TERMINAL
            and policy.graph.nodes[node_id].meta.get("shared_feature_atom")
            and node_id not in policy.pruned_terminal_ids
            and policy.graph.nodes[node_id].state
            in {NodeState.TRUE, NodeState.CONFIRMED}
        ))
        mature_composites: list[tuple[str, str]] = []
        for composite_id, cell in sorted(policy.composite_cells.items()):
            instance_id = policy.composite_node_by_triplet.get(
                (composite_id, triplet_id)
            )
            if (
                cell.state.name == "MATURE"
                and composite_id not in policy.disabled_composite_ids
                and instance_id is not None
                and policy.graph.nodes[instance_id].state
                in {NodeState.TRUE, NodeState.CONFIRMED}
            ):
                mature_composites.append((composite_id, instance_id))
        base_signals = tuple(
            GraphTerminalSignal(
                identity=node_id,
                role="BASE_TERMINAL",
                source_node_identity=node_id,
                terminal_kind=str(
                    policy.graph.nodes[node_id].meta.get(
                        "terminal_kind", "shared_feature_atom"
                    )
                ),
                provenance="selected_option_confirmed_terminal",
            )
            for node_id in base_ids
        )
        composite_signals = tuple(
            GraphTerminalSignal(
                identity=composite_id,
                role="MATURE_COMPOSITE",
                source_node_identity=instance_id,
                terminal_kind="stem_cell_composite",
                provenance="selected_option_confirmed_mature_composite",
                stem_cell_identity=composite_id,
            )
            for composite_id, instance_id in mature_composites
        )
        captures[option_identity] = _OptionSignalCapture(
            option_identity=option_identity,
            base_terminal_node_ids=base_ids,
            mature_composite_ids=tuple(
                item[0] for item in mature_composites
            ),
            terminal_signals=tuple(sorted(
                (*base_signals, *composite_signals),
                key=lambda item: item.identity,
            )),
        )

        options.append(AnonymousChoiceOption(
            identity=option_identity,
            actuator_identity=f"{ACTUATOR_PREFIX}{move_uci}",
            activation=float(strength),
            confirmed=True,
        ))
    return tuple(options), total_ticks, captures


def _always_legal_actuator(node: Node, env: Mapping[str, Any]) -> tuple[bool, bool]:
    legal = env.get("legal_actuator_identities", ())
    identity = str(node.meta.get("actuator_identity", ""))
    node.activation.value = 0.0
    return True, identity in legal


def _materialize_parent_choice(
    legal: Sequence[chess.Move],
    slots: Mapping[str, tuple[ChildQuery, ...]],
    *,
    frames: Mapping[tuple[str, int], FrameContext],
    connect_child: bool,
) -> tuple[Graph, dict[str, Any]]:
    graph = Graph()
    graph.add_node(Node("handover_choice_root", NodeType.SCRIPT, meta={
        "confirm_policy": "choice",
        "genome_primitive": "anonymous_exactly_one_choice",
    }))
    virtual_frames: dict[str, FrameContext] = {}
    for action_index, move in enumerate(legal):
        move_uci = move.uci()
        option_id = f"handover_option_{action_index}"
        actuator_id = f"handover_actuator_{action_index}"
        all_replies_id = f"handover_all_replies_{action_index}"
        response_ids: list[str] = []
        graph.add_node(Node(option_id, NodeType.SCRIPT, meta={
            "confirm_policy": "k_of_n",
            "confirm_k": 1,
            "anonymous_option_identity": f"action_leg_{action_index}",
            "actuator_identity": f"{ACTUATOR_PREFIX}{move_uci}",
            "choice_strength_node_ids": response_ids,
            "choice_strength_require_all": True,
            "choice_strength_aggregation": "minimum",
        }))
        graph.add_node(Node(actuator_id, NodeType.TERMINAL, predicate=_always_legal_actuator, meta={
            "terminal_kind": "environment_actuator_affordance",
            "actuator_identity": f"{ACTUATOR_PREFIX}{move_uci}",
        }))
        graph.add_hierarchy_pair("handover_choice_root", option_id)
        graph.add_hierarchy_pair(option_id, actuator_id)
        queries = slots.get(move_uci, ())
        if queries:
            graph.add_node(Node(all_replies_id, NodeType.SCRIPT, meta={
                "confirm_policy": "and",
                "generic_quantifier": "all",
            }))
            for reply_index, query in enumerate(queries):
                response_id = f"handover_child_response_{action_index}_{reply_index}"
                response_key = f"child_response_{action_index}_{reply_index}"
                response_ids.append(response_id)
                graph.add_node(Node(response_id, NodeType.TERMINAL, predicate=child_response_terminal, meta={
                    "terminal_kind": "CHILD_RESPONSE",
                    "response_key": response_key,
                    "response_origin": "actual_frozen_child_graph",
                }))
                graph.add_hierarchy_pair(all_replies_id, response_id)
                source_frame = frames.get((move_uci, reply_index))
                if source_frame is None:
                    source_frame = FrameContext(
                        frame_id=f"shuffled:{move_uci}:{reply_index}",
                        kind=FrameKind.VIRTUAL,
                        values={},
                        hypothetical_action=move_uci,
                    )
                virtual_frames[response_id] = FrameContext(
                    frame_id=source_frame.frame_id,
                    kind=FrameKind.VIRTUAL,
                    values={response_key: query.response},
                    parent_frame_id=source_frame.parent_frame_id,
                    hypothetical_action=move_uci,
                )
            if connect_child:
                graph.add_hierarchy_pair(option_id, all_replies_id)
        graph.nodes[option_id].meta["choice_strength_node_ids"] = response_ids if connect_child else []
    env = {
        "legal_actuator_identities": {f"{ACTUATOR_PREFIX}{move.uci()}" for move in legal},
        "virtual_frames": virtual_frames,
    }
    return graph, env


def _shuffle_response_slots(
    slots: Mapping[str, tuple[ChildQuery, ...]],
    *,
    seed: int,
) -> dict[str, tuple[ChildQuery, ...]]:
    ordered = sorted(slots)
    flat = [query for action in ordered for query in slots[action]]
    if len(flat) > 1:
        offset = 1 + (abs(int(seed)) % (len(flat) - 1))
        flat = flat[offset:] + flat[:offset]
    shuffled: dict[str, tuple[ChildQuery, ...]] = {}
    cursor = 0
    for action in ordered:
        width = len(slots[action])
        shuffled[action] = tuple(flat[cursor: cursor + width])
        cursor += width
    return shuffled


def _pickle_digest(value: Any) -> str:
    return hashlib.sha256(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)).hexdigest()
