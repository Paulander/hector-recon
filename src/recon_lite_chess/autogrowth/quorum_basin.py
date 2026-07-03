"""Static quorum basin recognizers over dieted KRK percepts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import chess

from recon_lite import FormalReConEngine, Graph, Node, NodeState, NodeType

from .features import extract_learner_features


ROOT_ID = "phase2_basin_root"
MATE_IN_ONE_BASIN_ID = "mate_in_1_basin"
ESCAPE_RESTRICTED_ID = "mate_in_1_escape_restricted"
EDGE_RELATIVE_OPPOSITION_ID = "mate_in_1_edge_relative_opposition"
RANK_EDGE_OPPOSITION_ID = "mate_in_1_rank_edge_opposition"
FILE_EDGE_OPPOSITION_ID = "mate_in_1_file_edge_opposition"
BLACK_KING_ON_RANK_EDGE_ID = "mate_in_1_black_king_on_rank_edge"
BLACK_KING_ON_FILE_EDGE_ID = "mate_in_1_black_king_on_file_edge"


@dataclass(frozen=True)
class PerceptAtom:
    node_id: str
    feature_name: str
    op: str
    expected: float
    reason: str


def _compare(value: float, op: str, expected: float) -> bool:
    if op == "eq":
        return value == expected
    if op == "le":
        return value <= expected
    if op == "ge":
        return value >= expected
    raise ValueError(f"unsupported percept atom operator: {op!r}")


def _percept_predicate(atom: PerceptAtom) -> Callable[[Node, dict[str, Any]], tuple[bool, bool]]:
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        value = float(env["features"][atom.feature_name])
        success = _compare(value, atom.op, atom.expected)
        node.meta["last_value"] = value
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def mate_in_one_basin_atoms() -> tuple[PerceptAtom, ...]:
    """Return the hand-derived atoms for the initial Mate-in-1 basin."""

    unavailable = tuple(
        PerceptAtom(
            node_id=f"atom_bk_neighbor_{direction}_blocked",
            feature_name=f"bk_neighbor_{direction}_available",
            op="eq",
            expected=0.0,
            reason="black king neighbor is statically unavailable",
        )
        for direction in ("n", "ne", "e", "se", "s", "sw", "w", "nw")
    )
    return (
        PerceptAtom("atom_white_to_move", "side_white_to_move", "eq", 1.0, "white has the mating turn"),
        PerceptAtom("atom_rook_present", "rook_present", "eq", 1.0, "rook material exists"),
        PerceptAtom("atom_rook_safe", "rook_attacked_by_black", "eq", 0.0, "rook is not immediately loose"),
        PerceptAtom("atom_black_king_edge", "black_king_on_edge", "eq", 1.0, "rook mate needs the defender on an edge"),
        PerceptAtom(
            "atom_black_king_rank_zero",
            "black_king_rank",
            "eq",
            0.0,
            "black king is on the south rank edge",
        ),
        PerceptAtom(
            "atom_black_king_rank_seven",
            "black_king_rank",
            "eq",
            7.0,
            "black king is on the north rank edge",
        ),
        PerceptAtom(
            "atom_black_king_file_zero",
            "black_king_file",
            "eq",
            0.0,
            "black king is on the west file edge",
        ),
        PerceptAtom(
            "atom_black_king_file_seven",
            "black_king_file",
            "eq",
            7.0,
            "black king is on the east file edge",
        ),
        PerceptAtom(
            "atom_rank_edge_along_delta_zero",
            "king_delta_file_abs",
            "eq",
            0.0,
            "on a rank edge, the kings align along the edge axis",
        ),
        PerceptAtom(
            "atom_rank_edge_perpendicular_delta_two",
            "king_delta_rank_abs",
            "eq",
            2.0,
            "on a rank edge, the white king is two ranks inward",
        ),
        PerceptAtom(
            "atom_file_edge_along_delta_zero",
            "king_delta_rank_abs",
            "eq",
            0.0,
            "on a file edge, the kings align along the edge axis",
        ),
        PerceptAtom(
            "atom_file_edge_perpendicular_delta_two",
            "king_delta_file_abs",
            "eq",
            2.0,
            "on a file edge, the white king is two files inward",
        ),
        PerceptAtom(
            "atom_rook_not_adjacent_to_black_king",
            "white_rook_to_black_king_distance",
            "ge",
            2.0,
            "rook has checking room and is not adjacent to the defender",
        ),
        *unavailable,
    )


def _add_quorum_script(graph: Graph, node_id: str, *, role: str, policy: str, k: int | None = None) -> None:
    meta: dict[str, Any] = {"role": role, "confirm_policy": policy}
    if k is not None:
        meta["confirm_k"] = int(k)
    graph.add_node(Node(node_id, NodeType.SCRIPT, meta=meta))


def _add_percept_atom(graph: Graph, atom: PerceptAtom, parent: str) -> None:
    graph.add_node(
        Node(
            atom.node_id,
            NodeType.TERMINAL,
            predicate=_percept_predicate(atom),
            meta={
                "role": "atomic_percept_terminal",
                "feature_name": atom.feature_name,
                "op": atom.op,
                "expected": atom.expected,
                "reason": atom.reason,
            },
        )
    )
    graph.add_hierarchy_pair(parent, atom.node_id)


def build_mate_in_one_basin_graph() -> Graph:
    """Build the fixed recognizer graph; no positions or labels are stored."""

    graph = Graph()
    graph.add_node(Node(ROOT_ID, NodeType.SCRIPT))
    _add_quorum_script(graph, MATE_IN_ONE_BASIN_ID, role="mate_in_1_basin", policy="and")
    _add_quorum_script(
        graph,
        ESCAPE_RESTRICTED_ID,
        role="mobility_restriction_quorum",
        policy="k_of_n",
        k=4,
    )
    _add_quorum_script(
        graph,
        EDGE_RELATIVE_OPPOSITION_ID,
        role="edge_relative_opposition_quorum",
        policy="k_of_n",
        k=1,
    )
    _add_quorum_script(graph, RANK_EDGE_OPPOSITION_ID, role="rank_edge_opposition_quorum", policy="and")
    _add_quorum_script(graph, FILE_EDGE_OPPOSITION_ID, role="file_edge_opposition_quorum", policy="and")
    _add_quorum_script(
        graph,
        BLACK_KING_ON_RANK_EDGE_ID,
        role="black_king_rank_edge_selector",
        policy="k_of_n",
        k=1,
    )
    _add_quorum_script(
        graph,
        BLACK_KING_ON_FILE_EDGE_ID,
        role="black_king_file_edge_selector",
        policy="k_of_n",
        k=1,
    )
    graph.add_hierarchy_pair(ROOT_ID, MATE_IN_ONE_BASIN_ID)
    graph.add_hierarchy_pair(MATE_IN_ONE_BASIN_ID, ESCAPE_RESTRICTED_ID)
    graph.add_hierarchy_pair(MATE_IN_ONE_BASIN_ID, EDGE_RELATIVE_OPPOSITION_ID)
    graph.add_hierarchy_pair(EDGE_RELATIVE_OPPOSITION_ID, RANK_EDGE_OPPOSITION_ID)
    graph.add_hierarchy_pair(EDGE_RELATIVE_OPPOSITION_ID, FILE_EDGE_OPPOSITION_ID)
    graph.add_hierarchy_pair(RANK_EDGE_OPPOSITION_ID, BLACK_KING_ON_RANK_EDGE_ID)
    graph.add_hierarchy_pair(FILE_EDGE_OPPOSITION_ID, BLACK_KING_ON_FILE_EDGE_ID)

    for atom in mate_in_one_basin_atoms():
        if atom.node_id.startswith("atom_bk_neighbor_"):
            parent = ESCAPE_RESTRICTED_ID
        elif atom.node_id in {"atom_black_king_rank_zero", "atom_black_king_rank_seven"}:
            parent = BLACK_KING_ON_RANK_EDGE_ID
        elif atom.node_id in {"atom_black_king_file_zero", "atom_black_king_file_seven"}:
            parent = BLACK_KING_ON_FILE_EDGE_ID
        elif atom.node_id.startswith("atom_rank_edge_"):
            parent = RANK_EDGE_OPPOSITION_ID
        elif atom.node_id.startswith("atom_file_edge_"):
            parent = FILE_EDGE_OPPOSITION_ID
        else:
            parent = MATE_IN_ONE_BASIN_ID
        _add_percept_atom(graph, atom, parent)

    graph.validate_formal_pairs()
    return graph


def run_mate_in_one_basin_recognizer(
    board: chess.Board,
    *,
    max_ticks: int = 32,
    record_trace: bool = True,
) -> dict[str, Any]:
    """Execute the fixed Mate-in-1 basin recognizer on one board."""

    graph = build_mate_in_one_basin_graph()
    features = extract_learner_features(board)
    engine = FormalReConEngine(graph, record_trace=record_trace)
    engine.request(ROOT_ID)
    trace = engine.run(
        max_ticks=max_ticks,
        env={"board": board, "features": features},
        until=lambda _engine: graph.nodes[ROOT_ID].state in (NodeState.CONFIRMED, NodeState.FAILED),
    )
    atom_states = {
        node_id: {
            "state": node.state.name,
            "feature_name": node.meta.get("feature_name"),
            "last_value": node.meta.get("last_value"),
        }
        for node_id, node in sorted(graph.nodes.items())
        if node.meta.get("role") == "atomic_percept_terminal"
    }
    script_states = {
        node_id: node.state.name
        for node_id, node in sorted(graph.nodes.items())
        if node.ntype == NodeType.SCRIPT
    }
    confirmed = graph.nodes[MATE_IN_ONE_BASIN_ID].state == NodeState.CONFIRMED
    return {
        "confirmed": confirmed,
        "root_state": graph.nodes[ROOT_ID].state.name,
        "basin_state": graph.nodes[MATE_IN_ONE_BASIN_ID].state.name,
        "escape_restricted_state": graph.nodes[ESCAPE_RESTRICTED_ID].state.name,
        "edge_relative_opposition_state": graph.nodes[EDGE_RELATIVE_OPPOSITION_ID].state.name,
        "ticks": engine.tick,
        "features": features,
        "atom_states": atom_states,
        "script_states": script_states,
        "trace": trace,
    }
