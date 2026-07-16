"""Fail-closed native child availability and real completion observation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import chess

from recon_lite import (
    AnonymousChoiceGenome,
    AnonymousChoiceOption,
    ChildResponse,
    FormalReConEngine,
    FrameContext,
    FrameKind,
    Graph,
    Node,
    NodeState,
    NodeType,
    child_response_terminal,
)

from .native_authority_handover import (
    ACTUATOR_PREFIX,
    ChildQuery,
    GraphActuation,
    NativeR0Organism,
)


@dataclass(frozen=True)
class RealChildObservation:
    response: ChildResponse
    actuation: GraphActuation | None
    observed_terminal: str | None
    completion_confirmed: bool
    local_competence_failure: bool
    successor_fen: str
    fabricated_terminal_reward: bool = False


@dataclass(frozen=True)
class CorrectedHandoverDecision:
    actuation: GraphActuation
    exploit_actuation: GraphActuation | None
    exploration_actuation: GraphActuation | None
    selection_mode: str
    response_slots: Mapping[str, tuple[ChildQuery, ...]]
    exploit_root_state: str
    exploit_actuator_multiplicity: int
    actuator_multiplicity: int
    host_fallback_count: int = 0


class FailClosedNativeHandoverGenome:
    """Exploit only through AVAILABLE; explore through a separate graph root."""

    ROOT_ID = "handover_exploit_root"

    def decide_from_available_slots(
        self,
        board: chess.Board,
        slots: Mapping[str, tuple[ChildQuery, ...]],
        frames: Mapping[tuple[str, int], FrameContext],
        *,
        disconnected: bool = False,
    ) -> CorrectedHandoverDecision:
        legal = tuple(sorted(board.legal_moves, key=lambda move: move.uci()))
        if not legal:
            raise RuntimeError("cannot decide without legal actions")
        graph, env = _materialize_fail_closed_choice(
            legal, slots, frames=frames, disconnected=disconnected
        )
        engine = FormalReConEngine(graph, record_trace=False)
        engine.request(self.ROOT_ID)
        engine.run(
            max_ticks=80,
            env=env,
            until=lambda item: item.g.nodes[self.ROOT_ID].state
            in {NodeState.CONFIRMED, NodeState.FAILED},
        )
        emitted = engine.emitted_actuator_identities(self.ROOT_ID)
        if len(emitted) > 1:
            raise RuntimeError("exploit graph emitted multiple actuators")
        exploit = None
        if emitted:
            selected_id = str(graph.nodes[self.ROOT_ID].meta["choice_selected_child"])
            option = graph.nodes[selected_id]
            exploit = _graph_actuation(
                emitted[0],
                option_identity=str(option.meta["anonymous_option_identity"]),
                activation=float(option.activation.value),
                candidate_count=len(legal),
                formal_ticks=engine.tick,
            )
        exploration = None
        if exploit is None:
            exploration = _emit_graph_exploration(legal)
        selected = exploit or exploration
        if selected is None:
            raise RuntimeError("graph exploration failed to emit an actuator")
        return CorrectedHandoverDecision(
            actuation=selected,
            exploit_actuation=exploit,
            exploration_actuation=exploration,
            selection_mode="exploit" if exploit is not None else "explore",
            response_slots={key: tuple(value) for key, value in slots.items()},
            exploit_root_state=graph.nodes[self.ROOT_ID].state.name,
            exploit_actuator_multiplicity=len(emitted),
            actuator_multiplicity=1,
        )


def observe_real_child(
    organism: NativeR0Organism,
    board: chess.Board,
) -> RealChildObservation:
    """Execute the child policy and its declared completion on the real board."""

    actuation = organism.emit_action(board)
    grounded = bool(organism.provenance.grounded and organism.provenance.can_emit)
    grounding_source = organism.provenance.grounding_source if grounded else None
    if actuation is None:
        response = ChildResponse(
            child_id=organism.provenance.child_id,
            confirmed=False,
            policy_response=False,
            available=False,
            expected_value=0.0,
            uncertainty=organism.provenance.uncertainty,
            grounded=grounded,
            grounding_source=grounding_source,
        )
        return RealChildObservation(
            response=response,
            actuation=None,
            observed_terminal=None,
            completion_confirmed=False,
            local_competence_failure=True,
            successor_fen=board.fen(),
        )
    move = chess.Move.from_uci(actuation.move_uci)
    if move not in board.legal_moves:
        raise RuntimeError("graph emitted illegal real child actuator")
    board.push(move)
    observed_terminal = observed_terminal_kind(board)
    expected = getattr(organism.provenance, "completion_terminal_kind", "mate")
    completion = formally_confirm_completion(
        expected_terminal=expected, observed_terminal=observed_terminal
    )
    response = ChildResponse(
        child_id=organism.provenance.child_id,
        confirmed=completion,
        policy_response=True,
        available=completion,
        expected_value=(organism.provenance.consolidated_value if completion else 0.0),
        uncertainty=organism.provenance.uncertainty,
        grounded=grounded,
        grounding_source=grounding_source,
    )
    return RealChildObservation(
        response=response,
        actuation=actuation,
        observed_terminal=observed_terminal,
        completion_confirmed=completion,
        local_competence_failure=not completion,
        successor_fen=board.fen(),
    )


def observe_query_completion(
    organism: NativeR0Organism,
    board: chess.Board,
    query: ChildQuery,
) -> RealChildObservation:
    """Execute an already-emitted policy response on a diagnostic real clone."""

    if query.actuation is None:
        return observe_real_child_without_response(organism, board)
    move = chess.Move.from_uci(query.actuation.move_uci)
    if move not in board.legal_moves:
        raise RuntimeError("diagnostic child actuator is illegal")
    board.push(move)
    observed_terminal = observed_terminal_kind(board)
    expected = getattr(organism.provenance, "completion_terminal_kind", "mate")
    completion = formally_confirm_completion(
        expected_terminal=expected, observed_terminal=observed_terminal
    )
    grounded = bool(organism.provenance.grounded and organism.provenance.can_emit)
    response = ChildResponse(
        child_id=organism.provenance.child_id,
        confirmed=completion,
        policy_response=True,
        available=completion,
        expected_value=(organism.provenance.consolidated_value if completion else 0.0),
        uncertainty=organism.provenance.uncertainty,
        grounded=grounded,
        grounding_source=(organism.provenance.grounding_source if grounded else None),
    )
    return RealChildObservation(
        response=response,
        actuation=query.actuation,
        observed_terminal=observed_terminal,
        completion_confirmed=completion,
        local_competence_failure=not completion,
        successor_fen=board.fen(),
    )


def observe_real_child_without_response(
    organism: NativeR0Organism, board: chess.Board
) -> RealChildObservation:
    grounded = bool(organism.provenance.grounded and organism.provenance.can_emit)
    response = ChildResponse(
        child_id=organism.provenance.child_id,
        confirmed=False,
        policy_response=False,
        available=False,
        expected_value=0.0,
        uncertainty=organism.provenance.uncertainty,
        grounded=grounded,
        grounding_source=(organism.provenance.grounding_source if grounded else None),
    )
    return RealChildObservation(
        response=response, actuation=None, observed_terminal=None,
        completion_confirmed=False, local_competence_failure=True,
        successor_fen=board.fen(),
    )


def formally_confirm_completion(
    *, expected_terminal: str, observed_terminal: str | None
) -> bool:
    graph = Graph()
    graph.add_node(Node("completion_root", NodeType.SCRIPT))
    graph.add_node(Node(
        "declared_completion", NodeType.TERMINAL,
        predicate=_declared_completion_terminal,
        meta={"expected_terminal": str(expected_terminal)},
    ))
    graph.add_hierarchy_pair("completion_root", "declared_completion")
    frame = FrameContext(
        frame_id="real-child-completion", kind=FrameKind.REAL,
        values={"observed_terminal": observed_terminal},
    )
    engine = FormalReConEngine(graph, record_trace=False)
    engine.request("completion_root")
    engine.run(
        max_ticks=12, env=frame.to_env_overlay(),
        until=lambda item: item.g.nodes["completion_root"].state
        in {NodeState.CONFIRMED, NodeState.FAILED},
    )
    return graph.nodes["completion_root"].state == NodeState.CONFIRMED


def response_with_availability(
    organism: NativeR0Organism, query: ChildQuery, *, available: bool
) -> ChildQuery:
    """Laboratory-only Boolean availability injection for named controls."""

    policy_response = bool(query.actuation is not None or query.response.policy_response)
    grounded = bool(organism.provenance.grounded and organism.provenance.can_emit)
    response = ChildResponse(
        child_id=organism.provenance.child_id,
        confirmed=bool(available), policy_response=policy_response,
        available=bool(available),
        expected_value=(organism.provenance.consolidated_value if available else 0.0),
        uncertainty=organism.provenance.uncertainty, grounded=grounded,
        grounding_source=(organism.provenance.grounding_source if grounded else None),
    )
    return ChildQuery(
        response=response, actuation=query.actuation, frame_id=query.frame_id,
        persistent_mutation_count=query.persistent_mutation_count,
        effect_attempts=query.effect_attempts,
        active_competence_signal_ids=query.active_competence_signal_ids,
        availability_provenance={
            "authority": "laboratory_boolean_injection",
            "injected_available": bool(available),
        },
    )


def any_action_confirms_completion(
    organism: NativeR0Organism, board: chess.Board
) -> bool:
    expected = getattr(organism.provenance, "completion_terminal_kind", "mate")
    for move in board.legal_moves:
        successor = board.copy(stack=False)
        successor.push(move)
        if formally_confirm_completion(
            expected_terminal=expected,
            observed_terminal=observed_terminal_kind(successor),
        ):
            return True
    return False


def observed_terminal_kind(board: chess.Board) -> str | None:
    if board.is_checkmate():
        return "mate"
    if board.is_stalemate():
        return "stalemate"
    if not board.pieces(chess.ROOK, chess.WHITE):
        return "rook_loss"
    if board.is_insufficient_material():
        return "draw"
    return None


def _declared_completion_terminal(
    node: Node, env: Mapping[str, Any]
) -> tuple[bool, bool]:
    observed = env.get("observed_terminal")
    expected = str(node.meta["expected_terminal"])
    success = observed == expected
    node.activation.value = 1.0 if success else 0.0
    node.meta["last_observed_terminal"] = observed
    return True, success


def _materialize_fail_closed_choice(
    legal: Sequence[chess.Move],
    slots: Mapping[str, tuple[ChildQuery, ...]],
    *, frames: Mapping[tuple[str, int], FrameContext],
    disconnected: bool,
) -> tuple[Graph, dict[str, Any]]:
    graph = Graph()
    graph.add_node(Node(
        FailClosedNativeHandoverGenome.ROOT_ID, NodeType.SCRIPT,
        meta={"confirm_policy": "choice", "role": "exploitative_handover"},
    ))
    virtual_frames: dict[str, FrameContext] = {}
    for index, move in enumerate(legal):
        move_uci = move.uci()
        option_id = f"fail_closed_option_{index}"
        actuator_id = f"fail_closed_actuator_{index}"
        replies_id = f"all_replies_available_{index}"
        graph.add_node(Node(option_id, NodeType.SCRIPT, meta={
            "confirm_policy": "and",
            "anonymous_option_identity": f"action_leg_{index}",
            "actuator_identity": f"{ACTUATOR_PREFIX}{move_uci}",
            "choice_strength_aggregation": "minimum",
            "choice_strength_require_all": True,
        }))
        graph.add_node(Node(
            actuator_id, NodeType.TERMINAL, predicate=_legal_actuator_terminal,
            meta={"actuator_identity": f"{ACTUATOR_PREFIX}{move_uci}"},
        ))
        graph.add_node(Node(
            replies_id, NodeType.SCRIPT,
            meta={"confirm_policy": "and", "generic_quantifier": "all"},
        ))
        graph.add_hierarchy_pair(FailClosedNativeHandoverGenome.ROOT_ID, option_id)
        graph.add_hierarchy_pair(option_id, actuator_id)
        graph.add_hierarchy_pair(option_id, replies_id)
        response_ids: list[str] = []
        queries = slots.get(move_uci, ())
        if disconnected or not queries:
            unavailable_id = f"unavailable_channel_{index}"
            graph.add_node(Node(
                unavailable_id, NodeType.TERMINAL, predicate=_unavailable_terminal,
                meta={"terminal_kind": "AVAILABLE_DISCONNECTED"},
            ))
            graph.add_hierarchy_pair(replies_id, unavailable_id)
            response_ids.append(unavailable_id)
        else:
            for reply_index, query in enumerate(queries):
                response_id = f"available_response_{index}_{reply_index}"
                response_key = f"available_value_{index}_{reply_index}"
                graph.add_node(Node(
                    response_id, NodeType.TERMINAL,
                    predicate=child_response_terminal,
                    meta={"response_key": response_key, "terminal_kind": "AVAILABLE"},
                ))
                graph.add_hierarchy_pair(replies_id, response_id)
                response_ids.append(response_id)
                source = frames[(move_uci, reply_index)]
                virtual_frames[response_id] = FrameContext(
                    frame_id=source.frame_id, kind=FrameKind.VIRTUAL,
                    values={response_key: query.response},
                    parent_frame_id=source.parent_frame_id,
                    hypothetical_action=move_uci,
                )
        graph.nodes[option_id].meta["choice_strength_node_ids"] = response_ids
    env = {
        "legal_actuator_identities": {
            f"{ACTUATOR_PREFIX}{move.uci()}" for move in legal
        },
        "virtual_frames": virtual_frames,
    }
    return graph, env


def _emit_graph_exploration(legal: Sequence[chess.Move]) -> GraphActuation:
    options = tuple(
        AnonymousChoiceOption(
            identity=f"exploration_leg_{index}",
            actuator_identity=f"{ACTUATOR_PREFIX}{move.uci()}",
            activation=0.0, confirmed=True,
        )
        for index, move in enumerate(legal)
    )
    emission = AnonymousChoiceGenome().emit(options)
    return _graph_actuation(
        emission.actuator_identity, option_identity=emission.option_identity,
        activation=emission.activation, candidate_count=len(options),
        formal_ticks=emission.formal_ticks,
    )


def _graph_actuation(
    actuator_identity: str, *, option_identity: str, activation: float,
    candidate_count: int, formal_ticks: int,
) -> GraphActuation:
    if not actuator_identity.startswith(ACTUATOR_PREFIX):
        raise RuntimeError("graph emitted invalid chess actuator")
    return GraphActuation(
        actuator_identity=actuator_identity,
        move_uci=actuator_identity[len(ACTUATOR_PREFIX):],
        option_identity=option_identity, activation=float(activation),
        candidate_count=int(candidate_count), formal_ticks=int(formal_ticks),
    )


def _legal_actuator_terminal(
    node: Node, env: Mapping[str, Any]
) -> tuple[bool, bool]:
    identity = str(node.meta["actuator_identity"])
    success = identity in env.get("legal_actuator_identities", ())
    node.activation.value = 1.0 if success else 0.0
    return True, success


def _unavailable_terminal(
    node: Node, _env: Mapping[str, Any]
) -> tuple[bool, bool]:
    node.activation.value = 0.0
    return True, False
