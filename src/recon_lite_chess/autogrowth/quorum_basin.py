"""Static quorum basin recognizers over dieted KRK percepts."""

from __future__ import annotations

from dataclasses import dataclass, field
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any, Callable, Iterable, Mapping, Sequence

import chess

from recon_lite import FormalReConEngine, Graph, LinkType, Node, NodeState, NodeType

from .features import extract_learner_features
from .terminal_substrate import TerminalAffordanceLearner, terminal_action_feature_keys


ROOT_ID = "phase2_basin_root"
MATE_IN_ONE_SKILL_ROOT_ID = "phase2_mate_in_1_skill_root"
MATE_IN_ONE_SKILL_ID = "mate_in_1_skill"
MATE_IN_ONE_RECOGNIZER_STEP_ID = "mate_in_1_basin_recognizer_step"
MATE_IN_TWO_SKILL_ROOT_ID = "phase2_mate_in_2_skill_root"
MATE_IN_TWO_SKILL_ID = "mate_in_2_skill"
ENTER_MATE_TWO_SKILL_ROOT_ID = "phase2_enter_mate_in_2_skill_root"
ENTER_MATE_TWO_SKILL_ID = "enter_mate_in_2_skill"
CHASE_TO_MATE_SKILL_ROOT_ID = "phase2_chase_to_mate_skill_root"
CHASE_TO_MATE_SKILL_ID = "chase_to_mate_skill"
CHASE_DEFER_MATE2_STEP_ID = "chase_defer_mate2_step"
CHASE_ROOK_ESCAPE_STEP_ID = "chase_rook_escape_slide_step"
CHASE_KING_APPROACH_STEP_ID = "chase_king_approach_step"
CHASE_ROOK_TEMPO_STEP_ID = "chase_rook_tempo_step"
FENCE_ESTABLISHED_ROOT_ID = "phase2_fence_established_root"
FENCE_ESTABLISHED_ID = "fence_established"
FENCE_EDGE_SELECTOR_ID = "fence_nearest_edge_selector"
FENCE_ROOK_SAFETY_ID = "fence_rook_safety"
ESTABLISH_FENCE_SKILL_ROOT_ID = "phase2_establish_fence_skill_root"
ESTABLISH_FENCE_SKILL_ID = "establish_fence_skill"
FENCE_REPLY_QUANTIFIER_ROOT_ID = "phase2_fence_reply_quantifier_root"
FENCE_REPLY_QUANTIFIER_ID = "establish_fence_reply_quantifier"
REPLY_QUANTIFIER_ROOT_ID = "phase2_reply_quantifier_root"
REPLY_QUANTIFIER_ID = "mate_in_2_reply_quantifier"
MATE_IN_ONE_BASIN_ID = "mate_in_1_basin"
ESCAPE_RESTRICTED_ID = "mate_in_1_escape_restricted"
KING_SUPPORT_GEOMETRY_ID = "mate_in_1_king_support_geometry"
EDGE_RELATIVE_OPPOSITION_ID = "mate_in_1_edge_relative_opposition"
RANK_EDGE_OPPOSITION_ID = "mate_in_1_rank_edge_opposition"
FILE_EDGE_OPPOSITION_ID = "mate_in_1_file_edge_opposition"
BLACK_KING_ON_RANK_EDGE_ID = "mate_in_1_black_king_on_rank_edge"
BLACK_KING_ON_FILE_EDGE_ID = "mate_in_1_black_king_on_file_edge"
CORNER_KNIGHT_SUPPORT_ID = "mate_in_1_corner_knight_support"
DELIVER_EDGE_MATE_SCRIPT_ID = "deliver_edge_mate_step"
DELIVER_EDGE_MATE_ACTUATOR_ID = "deliver_edge_mate"
FENCE_WEST_EDGE_ID = "fence_west_edge_branch"
FENCE_EAST_EDGE_ID = "fence_east_edge_branch"
FENCE_SOUTH_EDGE_ID = "fence_south_edge_branch"
FENCE_NORTH_EDGE_ID = "fence_north_edge_branch"
KRK_POLICY_ROOT_ID = "krk_policy"
MATE_IN_TWO_GATE_ID = "mate_in_2_chain_confidence_gate"
CANONICAL_DIETED_FALLBACK_ID = "canonical_dieted_scorer_fallback"

_BK_NEIGHBOR_DIRECTIONS = ("n", "ne", "e", "se", "s", "sw", "w", "nw")


@dataclass(frozen=True)
class PerceptAtom:
    node_id: str
    feature_name: str
    op: str
    expected: float
    reason: str


def _prefixed(prefix: str, node_id: str) -> str:
    return f"{prefix}{node_id}" if prefix else node_id


def _base_id(prefix: str, node_id: str) -> str:
    return node_id.removeprefix(prefix) if prefix and node_id.startswith(prefix) else node_id


def _safe_move_id(move: chess.Move) -> str:
    return move.uci().replace("-", "_")


def _position_repetition_key(board: chess.Board) -> str:
    return " ".join(
        [
            board.board_fen(),
            "w" if board.turn == chess.WHITE else "b",
            board.castling_xfen(),
            chess.square_name(board.ep_square) if board.ep_square is not None else "-",
        ]
    )


def _after_move_repetition_key(board: chess.Board, move: chess.Move) -> str:
    after = board.copy(stack=False)
    after.push(move)
    return _position_repetition_key(after)


def _move_confirms_zero_reply_mate(board: chess.Board, move: chess.Move) -> bool:
    if move not in board.legal_moves:
        return False
    after = board.copy(stack=False)
    after.push(move)
    return after.legal_moves.count() == 0 and after.is_check()


@dataclass
class FrozenMate2FirstScorer:
    """Frozen exported mate2-first terminal scorer used only for request ordering."""

    terminal_weights: dict[str, float]
    source_path: Path
    source_sha256: str
    source_terminal_count: int
    feature_cache: dict[str, dict[str, float]] = field(default_factory=dict)

    def score_move(self, board: chess.Board, move: chess.Move) -> float:
        return sum(
            self.terminal_weights.get(terminal_key, 0.0)
            for terminal_key, _scale in terminal_action_feature_keys(
                board,
                move,
                feature_cache=self.feature_cache,
            )
        )

    def order_moves(self, board: chess.Board, moves: Sequence[chess.Move]) -> tuple[chess.Move, ...]:
        rows = [
            (self.score_move(board, move), move.uci(), move)
            for move in moves
        ]
        rows.sort(key=lambda row: (row[0], row[1]), reverse=True)
        return tuple(row[-1] for row in rows)

    def rank_move(self, board: chess.Board, move: chess.Move) -> int | None:
        ordered = self.order_moves(
            board,
            tuple(sorted(board.legal_moves, key=lambda item: item.uci())),
        )
        for index, candidate in enumerate(ordered, start=1):
            if candidate == move:
                return index
        return None


def load_canonical_mate2_first_scorer(
    *,
    brief_path: str | Path = "docs/BRIEF.md",
) -> FrozenMate2FirstScorer:
    """Load the canonical dieted parent scorer named and hashed in ``docs/BRIEF.md``."""

    brief = Path(brief_path).read_text(encoding="utf-8").splitlines()
    source_path: Path | None = None
    expected_hash: str | None = None
    for line in brief:
        if line.startswith("Canonical dieted parent:"):
            source_path = Path(line.split(":", 1)[1].strip())
        elif line.startswith("Canonical sha256:"):
            expected_hash = line.split(":", 1)[1].strip()
    if source_path is None or expected_hash is None:
        raise ValueError(f"canonical dieted parent and hash not found in {brief_path}")
    actual_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError(
            f"canonical dieted parent hash mismatch: expected {expected_hash}, got {actual_hash}"
        )

    payload = json.loads(source_path.read_text(encoding="utf-8"))
    summary = payload["graph_summary"]["top_mate2_first_terminals"]
    weights: dict[str, float] = {}
    for bucket in ("top_positive_terminals", "top_negative_terminals"):
        for row in summary.get(bucket, []):
            learner_visible = row.get("learner_visible", {})
            terminal_key = learner_visible.get("terminal_key")
            if terminal_key:
                weights[str(terminal_key)] = float(learner_visible["local_weight"])
    if not weights:
        raise ValueError(f"no exported mate2_first terminal weights found in {source_path}")
    return FrozenMate2FirstScorer(
        terminal_weights=weights,
        source_path=source_path,
        source_sha256=actual_hash,
        source_terminal_count=int(summary.get("terminal_count", len(weights))),
    )


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


def mate_in_one_basin_atoms(*, prefix: str = "") -> tuple[PerceptAtom, ...]:
    """Return the hand-derived atoms for the initial Mate-in-1 basin."""

    unavailable = tuple(
        PerceptAtom(
            node_id=_prefixed(prefix, f"atom_bk_neighbor_{direction}_blocked"),
            feature_name=f"bk_neighbor_{direction}_available",
            op="eq",
            expected=0.0,
            reason="black king neighbor is statically unavailable",
        )
        for direction in _BK_NEIGHBOR_DIRECTIONS
    )
    return (
        PerceptAtom(
            _prefixed(prefix, "atom_white_to_move"),
            "side_white_to_move",
            "eq",
            1.0,
            "white has the mating turn",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_rook_present"),
            "rook_present",
            "eq",
            1.0,
            "rook material exists",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_rook_safe"),
            "rook_attacked_by_black",
            "eq",
            0.0,
            "rook is not immediately loose",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_black_king_edge"),
            "black_king_on_edge",
            "eq",
            1.0,
            "rook mate needs the defender on an edge",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_black_king_corner"),
            "black_king_corner_distance",
            "eq",
            0.0,
            "corner wall supplies two escape constraints",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_corner_king_knight_support"),
            "king_pair_knight_distance_like",
            "eq",
            1.0,
            "white king has board-interior knight-distance corner support",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_black_king_rank_zero"),
            "black_king_rank",
            "eq",
            0.0,
            "black king is on the south rank edge",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_black_king_rank_seven"),
            "black_king_rank",
            "eq",
            7.0,
            "black king is on the north rank edge",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_black_king_file_zero"),
            "black_king_file",
            "eq",
            0.0,
            "black king is on the west file edge",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_black_king_file_seven"),
            "black_king_file",
            "eq",
            7.0,
            "black king is on the east file edge",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_rank_edge_along_delta_zero"),
            "king_delta_file_abs",
            "eq",
            0.0,
            "on a rank edge, the kings align along the edge axis",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_rank_edge_perpendicular_delta_two"),
            "king_delta_rank_abs",
            "eq",
            2.0,
            "on a rank edge, the white king is two ranks inward",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_file_edge_along_delta_zero"),
            "king_delta_rank_abs",
            "eq",
            0.0,
            "on a file edge, the kings align along the edge axis",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_file_edge_perpendicular_delta_two"),
            "king_delta_file_abs",
            "eq",
            2.0,
            "on a file edge, the white king is two files inward",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_rook_not_adjacent_to_black_king"),
            "white_rook_to_black_king_distance",
            "ge",
            2.0,
            "rook has checking room and is not adjacent to the defender",
        ),
        *unavailable,
    )


def fence_established_atoms(*, prefix: str = "") -> tuple[PerceptAtom, ...]:
    """Return the static atoms for the rook-fence recognizer."""

    return (
        PerceptAtom(
            _prefixed(prefix, "atom_fence_rook_present"),
            "rook_present",
            "eq",
            1.0,
            "rook material exists for the fence",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_fence_black_king_on_edge"),
            "black_king_on_edge",
            "eq",
            1.0,
            "black king is still edge-side of the fence line",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_fence_rook_not_attacked"),
            "rook_attacked_by_black",
            "eq",
            0.0,
            "rook is not attacked by the black king",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_fence_rook_defended_by_king"),
            "white_king_to_rook_distance",
            "le",
            1.0,
            "white king defends the fenced rook",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_fence_bk_file_west"),
            "black_king_file",
            "eq",
            0.0,
            "nearest edge is the west file",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_fence_wr_file_west_line"),
            "white_rook_file",
            "eq",
            1.0,
            "rook sits one file interior to the west edge",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_fence_bk_file_east"),
            "black_king_file",
            "eq",
            7.0,
            "nearest edge is the east file",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_fence_wr_file_east_line"),
            "white_rook_file",
            "eq",
            6.0,
            "rook sits one file interior to the east edge",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_fence_bk_rank_south"),
            "black_king_rank",
            "eq",
            0.0,
            "nearest edge is the south rank",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_fence_wr_rank_south_line"),
            "white_rook_rank",
            "eq",
            1.0,
            "rook sits one rank interior to the south edge",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_fence_bk_rank_north"),
            "black_king_rank",
            "eq",
            7.0,
            "nearest edge is the north rank",
        ),
        PerceptAtom(
            _prefixed(prefix, "atom_fence_wr_rank_north_line"),
            "white_rook_rank",
            "eq",
            6.0,
            "rook sits one rank interior to the north edge",
        ),
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


def _add_mate_in_one_basin_subgraph(graph: Graph, parent_id: str, *, prefix: str = "") -> None:
    """Attach the fixed basin recognizer under an existing script parent."""

    basin_id = _prefixed(prefix, MATE_IN_ONE_BASIN_ID)
    escape_id = _prefixed(prefix, ESCAPE_RESTRICTED_ID)
    king_support_id = _prefixed(prefix, KING_SUPPORT_GEOMETRY_ID)
    edge_opposition_id = _prefixed(prefix, EDGE_RELATIVE_OPPOSITION_ID)
    rank_edge_opposition_id = _prefixed(prefix, RANK_EDGE_OPPOSITION_ID)
    file_edge_opposition_id = _prefixed(prefix, FILE_EDGE_OPPOSITION_ID)
    rank_edge_id = _prefixed(prefix, BLACK_KING_ON_RANK_EDGE_ID)
    file_edge_id = _prefixed(prefix, BLACK_KING_ON_FILE_EDGE_ID)
    corner_support_id = _prefixed(prefix, CORNER_KNIGHT_SUPPORT_ID)

    _add_quorum_script(graph, basin_id, role="mate_in_1_basin", policy="and")
    _add_quorum_script(
        graph,
        escape_id,
        role="mobility_restriction_quorum",
        policy="k_of_n",
        k=4,
    )
    _add_quorum_script(
        graph,
        king_support_id,
        role="king_support_geometry_quorum",
        policy="k_of_n",
        k=1,
    )
    _add_quorum_script(
        graph,
        edge_opposition_id,
        role="edge_relative_opposition_quorum",
        policy="k_of_n",
        k=1,
    )
    _add_quorum_script(graph, rank_edge_opposition_id, role="rank_edge_opposition_quorum", policy="and")
    _add_quorum_script(graph, file_edge_opposition_id, role="file_edge_opposition_quorum", policy="and")
    _add_quorum_script(
        graph,
        rank_edge_id,
        role="black_king_rank_edge_selector",
        policy="k_of_n",
        k=1,
    )
    _add_quorum_script(
        graph,
        file_edge_id,
        role="black_king_file_edge_selector",
        policy="k_of_n",
        k=1,
    )
    _add_quorum_script(
        graph,
        corner_support_id,
        role="corner_knight_support_quorum",
        policy="and",
    )
    graph.add_hierarchy_pair(parent_id, basin_id)
    graph.add_hierarchy_pair(basin_id, escape_id)
    graph.add_hierarchy_pair(basin_id, king_support_id)
    graph.add_hierarchy_pair(king_support_id, edge_opposition_id)
    graph.add_hierarchy_pair(king_support_id, corner_support_id)
    graph.add_hierarchy_pair(edge_opposition_id, rank_edge_opposition_id)
    graph.add_hierarchy_pair(edge_opposition_id, file_edge_opposition_id)
    graph.add_hierarchy_pair(rank_edge_opposition_id, rank_edge_id)
    graph.add_hierarchy_pair(file_edge_opposition_id, file_edge_id)

    for atom in mate_in_one_basin_atoms(prefix=prefix):
        base_node_id = _base_id(prefix, atom.node_id)
        if base_node_id.startswith("atom_bk_neighbor_"):
            parent = escape_id
        elif base_node_id in {"atom_black_king_corner", "atom_corner_king_knight_support"}:
            parent = corner_support_id
        elif base_node_id in {"atom_black_king_rank_zero", "atom_black_king_rank_seven"}:
            parent = rank_edge_id
        elif base_node_id in {"atom_black_king_file_zero", "atom_black_king_file_seven"}:
            parent = file_edge_id
        elif base_node_id.startswith("atom_rank_edge_"):
            parent = rank_edge_opposition_id
        elif base_node_id.startswith("atom_file_edge_"):
            parent = file_edge_opposition_id
        else:
            parent = basin_id
        _add_percept_atom(graph, atom, parent)


def _add_fence_established_subgraph(graph: Graph, parent_id: str, *, prefix: str = "") -> None:
    """Attach the fixed rook-fence recognizer under an existing script parent."""

    fence_id = _prefixed(prefix, FENCE_ESTABLISHED_ID)
    edge_selector_id = _prefixed(prefix, FENCE_EDGE_SELECTOR_ID)
    safety_id = _prefixed(prefix, FENCE_ROOK_SAFETY_ID)
    west_id = _prefixed(prefix, FENCE_WEST_EDGE_ID)
    east_id = _prefixed(prefix, FENCE_EAST_EDGE_ID)
    south_id = _prefixed(prefix, FENCE_SOUTH_EDGE_ID)
    north_id = _prefixed(prefix, FENCE_NORTH_EDGE_ID)

    _add_quorum_script(graph, fence_id, role="fence_established", policy="and")
    _add_quorum_script(
        graph,
        edge_selector_id,
        role="fence_nearest_edge_selector",
        policy="k_of_n",
        k=1,
    )
    _add_quorum_script(
        graph,
        safety_id,
        role="fence_rook_safety",
        policy="k_of_n",
        k=1,
    )
    _add_quorum_script(graph, west_id, role="fence_west_edge_branch", policy="and")
    _add_quorum_script(graph, east_id, role="fence_east_edge_branch", policy="and")
    _add_quorum_script(graph, south_id, role="fence_south_edge_branch", policy="and")
    _add_quorum_script(graph, north_id, role="fence_north_edge_branch", policy="and")

    graph.add_hierarchy_pair(parent_id, fence_id)
    graph.add_hierarchy_pair(fence_id, edge_selector_id)
    graph.add_hierarchy_pair(fence_id, safety_id)
    graph.add_hierarchy_pair(edge_selector_id, west_id)
    graph.add_hierarchy_pair(edge_selector_id, east_id)
    graph.add_hierarchy_pair(edge_selector_id, south_id)
    graph.add_hierarchy_pair(edge_selector_id, north_id)

    for atom in fence_established_atoms(prefix=prefix):
        base_node_id = _base_id(prefix, atom.node_id)
        if base_node_id in {"atom_fence_rook_not_attacked", "atom_fence_rook_defended_by_king"}:
            parent = safety_id
        elif base_node_id in {"atom_fence_bk_file_west", "atom_fence_wr_file_west_line"}:
            parent = west_id
        elif base_node_id in {"atom_fence_bk_file_east", "atom_fence_wr_file_east_line"}:
            parent = east_id
        elif base_node_id in {"atom_fence_bk_rank_south", "atom_fence_wr_rank_south_line"}:
            parent = south_id
        elif base_node_id in {"atom_fence_bk_rank_north", "atom_fence_wr_rank_north_line"}:
            parent = north_id
        else:
            parent = fence_id
        _add_percept_atom(graph, atom, parent)


def build_mate_in_one_basin_graph() -> Graph:
    """Build the fixed recognizer graph; no positions or labels are stored."""

    graph = Graph()
    graph.add_node(Node(ROOT_ID, NodeType.SCRIPT))
    _add_mate_in_one_basin_subgraph(graph, ROOT_ID)
    graph.validate_formal_pairs()
    return graph


def build_fence_established_graph() -> Graph:
    """Build the fixed rook-fence recognizer graph."""

    graph = Graph()
    graph.add_node(Node(FENCE_ESTABLISHED_ROOT_ID, NodeType.SCRIPT))
    _add_fence_established_subgraph(graph, FENCE_ESTABLISHED_ROOT_ID)
    graph.validate_formal_pairs()
    return graph


def fence_established_geometry(board: chess.Board) -> bool:
    """Trainer-side exact geometry for validating the static fence recognizer."""

    features = extract_learner_features(board)
    if features["rook_present"] != 1.0 or features["black_king_on_edge"] != 1.0:
        return False
    rook_safe = (
        features["rook_attacked_by_black"] == 0.0
        or features["white_king_to_rook_distance"] <= 1.0
    )
    if not rook_safe:
        return False

    west = features["black_king_file"] == 0.0 and features["white_rook_file"] == 1.0
    east = features["black_king_file"] == 7.0 and features["white_rook_file"] == 6.0
    south = features["black_king_rank"] == 0.0 and features["white_rook_rank"] == 1.0
    north = features["black_king_rank"] == 7.0 and features["white_rook_rank"] == 6.0
    return bool(west or east or south or north)


def _stable_fence_after_all_replies(board: chess.Board) -> bool:
    replies = list(board.legal_moves)
    if not replies:
        return board.is_check()
    for reply in replies:
        after_reply = board.copy(stack=False)
        after_reply.push(reply)
        if not fence_established_geometry(after_reply):
            return False
    return True


def _fence_edges_for_board(board: chess.Board) -> tuple[str, ...]:
    black_king = board.king(chess.BLACK)
    rook = _white_rook_square(board)
    if black_king is None or rook is None:
        return ()
    bk_file = chess.square_file(black_king)
    bk_rank = chess.square_rank(black_king)
    rook_file = chess.square_file(rook)
    rook_rank = chess.square_rank(rook)
    edges: list[str] = []
    if bk_file == 0 and rook_file == 1:
        edges.append("west")
    if bk_file == 7 and rook_file == 6:
        edges.append("east")
    if bk_rank == 0 and rook_rank == 1:
        edges.append("south")
    if bk_rank == 7 and rook_rank == 6:
        edges.append("north")
    return tuple(edges)


def _edge_along_coord(square: int, edge: str) -> int:
    if edge in {"west", "east"}:
        return chess.square_rank(square)
    return chess.square_file(square)


def _edge_line_coord(square: int, edge: str) -> int:
    if edge in {"west", "east"}:
        return chess.square_file(square)
    return chess.square_rank(square)


def _edge_fence_line(edge: str) -> int:
    if edge == "west":
        return 1
    if edge == "east":
        return 6
    if edge == "south":
        return 1
    if edge == "north":
        return 6
    raise ValueError(f"unknown edge: {edge}")


def _king_interior_to_edge(white_king: int, black_king: int, edge: str) -> bool:
    wk_file = chess.square_file(white_king)
    wk_rank = chess.square_rank(white_king)
    bk_file = chess.square_file(black_king)
    bk_rank = chess.square_rank(black_king)
    if edge == "west":
        return wk_file > bk_file
    if edge == "east":
        return wk_file < bk_file
    if edge == "south":
        return wk_rank > bk_rank
    if edge == "north":
        return wk_rank < bk_rank
    return False


def _fence_crossing_squares(board: chess.Board, edge: str) -> tuple[int, ...]:
    black_king = board.king(chess.BLACK)
    if black_king is None:
        return ()
    along = _edge_along_coord(black_king, edge)
    line = _edge_fence_line(edge)
    squares: list[int] = []
    for delta in (-1, 0, 1):
        next_along = along + delta
        if not 0 <= next_along <= 7:
            continue
        if edge in {"west", "east"}:
            squares.append(chess.square(line, next_along))
        else:
            squares.append(chess.square(next_along, line))
    return tuple(squares)


def _fence_line_controls_crossing_squares(board: chess.Board, edge: str) -> bool:
    rook = _white_rook_square(board)
    if rook is None:
        return False
    for square in _fence_crossing_squares(board, edge):
        piece = board.piece_at(square)
        if piece is not None and piece.color == chess.WHITE:
            continue
        if rook in board.attackers(chess.WHITE, square):
            continue
        if board.is_attacked_by(chess.WHITE, square):
            continue
        return False
    return True


def _king_support_waypoint_geometry(board: chess.Board) -> bool:
    if not _chase_confinement_intact_geometry(board):
        return False
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)
    if white_king is None or black_king is None:
        return False
    if chess.square_distance(white_king, black_king) > 2:
        return False
    return any(
        _king_interior_to_edge(white_king, black_king, edge)
        for edge in _fence_edges_for_board(board)
    )


def _chase_confinement_intact_geometry(board: chess.Board) -> bool:
    return any(
        _fence_line_controls_crossing_squares(board, edge)
        for edge in _fence_edges_for_board(board)
    )


def _edge_relative_opposition_contact(board: chess.Board) -> bool:
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)
    if white_king is None or black_king is None:
        return False
    wk_file = chess.square_file(white_king)
    wk_rank = chess.square_rank(white_king)
    bk_file = chess.square_file(black_king)
    bk_rank = chess.square_rank(black_king)
    for edge in _fence_edges_for_board(board):
        if edge == "west" and wk_file - bk_file == 2 and wk_rank == bk_rank:
            return True
        if edge == "east" and bk_file - wk_file == 2 and wk_rank == bk_rank:
            return True
        if edge == "south" and wk_rank - bk_rank == 2 and wk_file == bk_file:
            return True
        if edge == "north" and bk_rank - wk_rank == 2 and wk_file == bk_file:
            return True
    return False


def _king_support_contact_geometry(board: chess.Board) -> bool:
    features = extract_learner_features(board)
    return bool(
        features["king_pair_knight_distance_like"] == 1.0
        or _edge_relative_opposition_contact(board)
    )


def _support_target_squares(board: chess.Board) -> tuple[int, ...]:
    black_king = board.king(chess.BLACK)
    if black_king is None:
        return ()
    bk_file = chess.square_file(black_king)
    bk_rank = chess.square_rank(black_king)
    targets: set[int] = set()
    for edge in _fence_edges_for_board(board):
        if edge == "west" and bk_file + 2 <= 7:
            targets.add(chess.square(bk_file + 2, bk_rank))
        elif edge == "east" and bk_file - 2 >= 0:
            targets.add(chess.square(bk_file - 2, bk_rank))
        elif edge == "south" and bk_rank + 2 <= 7:
            targets.add(chess.square(bk_file, bk_rank + 2))
        elif edge == "north" and bk_rank - 2 >= 0:
            targets.add(chess.square(bk_file, bk_rank - 2))
        for file_delta, rank_delta in (
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        ):
            file_idx = bk_file + file_delta
            rank_idx = bk_rank + rank_delta
            if not (0 <= file_idx <= 7 and 0 <= rank_idx <= 7):
                continue
            square = chess.square(file_idx, rank_idx)
            if _king_interior_to_edge(square, black_king, edge):
                targets.add(square)
    return tuple(sorted(targets))


def _king_contact_score(board: chess.Board) -> tuple[int, int, int]:
    if _king_support_contact_geometry(board):
        return (0, 0, 0)
    white_king = board.king(chess.WHITE)
    targets = _support_target_squares(board)
    if white_king is None or not targets:
        return (1, 8, 16)
    wk_file = chess.square_file(white_king)
    wk_rank = chess.square_rank(white_king)
    distances = [
        (
            chess.square_distance(white_king, target),
            abs(wk_file - chess.square_file(target))
            + abs(wk_rank - chess.square_rank(target)),
        )
        for target in targets
    ]
    chebyshev, manhattan = min(distances)
    return (1, chebyshev, manhattan)


def _chase_rook_safe(board: chess.Board) -> bool:
    rook = _white_rook_square(board)
    if rook is None:
        return False
    features = extract_learner_features(board)
    return bool(
        features["rook_attacked_by_black"] == 0.0
        or _white_king_defends_square(board, rook)
    )


def _chase_after_move_valid(
    board: chess.Board,
    move: chess.Move,
    *,
    repetition_counts: Mapping[str, int],
) -> tuple[bool, str, chess.Board | None]:
    if move not in board.legal_moves:
        return False, "illegal", None
    if int(repetition_counts.get(_after_move_repetition_key(board, move), 0)) >= 2:
        return False, "third_occurrence_repetition", None
    after = _after_move(board, move)
    if _white_rook_square(after) is None:
        return False, "rook_lost", after
    if after.is_stalemate():
        return False, "stalemate_delivered", after
    if not _chase_confinement_intact_geometry(after):
        return False, "confinement_crossed", after
    if not _king_support_waypoint_geometry(after):
        return False, "left_waypoint_domain", after
    if not _chase_rook_safe(after):
        return False, "rook_attacked_or_undefended", after
    return True, "ok", after


def _record_chase_rejected_move(
    rejected_moves: list[dict[str, str]] | None,
    *,
    branch: str,
    move: chess.Move,
    reason: str,
) -> None:
    if rejected_moves is None:
        return
    entry = {"branch": branch, "move": move.uci(), "reason": reason}
    if entry not in rejected_moves:
        rejected_moves.append(entry)


def _rook_fence_slide_candidates(
    board: chess.Board,
    *,
    repetition_counts: Mapping[str, int],
    branch: str,
    rejected_moves: list[dict[str, str]] | None = None,
) -> list[tuple[chess.Move, chess.Board, str]]:
    rook = _white_rook_square(board)
    black_king = board.king(chess.BLACK)
    if rook is None or black_king is None:
        return []
    candidates: list[tuple[chess.Move, chess.Board, str]] = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        if move.from_square != rook:
            continue
        for edge in _fence_edges_for_board(board):
            if _edge_line_coord(move.to_square, edge) != _edge_fence_line(edge):
                continue
            if _edge_along_coord(move.to_square, edge) == _edge_along_coord(rook, edge):
                continue
            valid, _reason, after = _chase_after_move_valid(
                board,
                move,
                repetition_counts=repetition_counts,
            )
            if valid and after is not None:
                candidates.append((move, after, edge))
                break
            _record_chase_rejected_move(
                rejected_moves,
                branch=branch,
                move=move,
                reason=_reason,
            )
    return candidates


def _resolve_chase_rook_escape(
    board: chess.Board,
    *,
    repetition_counts: Mapping[str, int],
    rejected_moves: list[dict[str, str]] | None = None,
) -> chess.Move | None:
    rook = _white_rook_square(board)
    black_king = board.king(chess.BLACK)
    if rook is None or black_king is None:
        return None
    candidates = _rook_fence_slide_candidates(
        board,
        repetition_counts=repetition_counts,
        branch="rook_escape_slide",
        rejected_moves=rejected_moves,
    )
    if not candidates:
        return None
    ranked = []
    for move, _after, edge in candidates:
        distance = abs(
            _edge_along_coord(move.to_square, edge)
            - _edge_along_coord(black_king, edge)
        )
        slide = abs(
            _edge_along_coord(move.to_square, edge)
            - _edge_along_coord(rook, edge)
        )
        ranked.append((distance, slide, move.uci(), move))
    ranked.sort(reverse=True)
    return ranked[0][-1]


def _resolve_chase_king_approach(
    board: chess.Board,
    *,
    repetition_counts: Mapping[str, int],
    rejected_moves: list[dict[str, str]] | None = None,
    allow_equal_contact: bool = False,
) -> chess.Move | None:
    white_king = board.king(chess.WHITE)
    if white_king is None:
        return None
    before_score = _king_contact_score(board)
    before_rook_safe = _chase_rook_safe(board)
    ranked: list[tuple[tuple[int, int, int], str, chess.Move]] = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        if move.from_square != white_king:
            continue
        valid, _reason, after = _chase_after_move_valid(
            board,
            move,
            repetition_counts=repetition_counts,
        )
        if not valid or after is None:
            _record_chase_rejected_move(
                rejected_moves,
                branch="king_approach",
                move=move,
                reason=_reason,
            )
            continue
        score = _king_contact_score(after)
        rook_safety_progress = not before_rook_safe and _chase_rook_safe(after)
        if score > before_score:
            continue
        if score == before_score and not (rook_safety_progress or allow_equal_contact):
            continue
        ranked.append((score, move.uci(), move))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return ranked[0][-1] if ranked else None


def _resolve_chase_rook_tempo(
    board: chess.Board,
    *,
    repetition_counts: Mapping[str, int],
    rejected_moves: list[dict[str, str]] | None = None,
) -> chess.Move | None:
    rook = _white_rook_square(board)
    if rook is None:
        return None
    ranked: list[tuple[int, str, chess.Move]] = []
    for move, _after, edge in _rook_fence_slide_candidates(
        board,
        repetition_counts=repetition_counts,
        branch="rook_waiting_tempo",
        rejected_moves=rejected_moves,
    ):
        slide = abs(
            _edge_along_coord(move.to_square, edge)
            - _edge_along_coord(rook, edge)
        )
        ranked.append((slide, move.uci(), move))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return ranked[0][-1] if ranked else None


def resolve_establish_fence_move(board: chess.Board) -> chess.Move | None:
    """Resolve a legal rook move whose fence survives all black replies."""

    rook = _white_rook_square(board)
    if rook is None or board.turn != chess.WHITE:
        return None
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        if move.from_square != rook:
            continue
        after = board.copy(stack=False)
        after.push(move)
        if _stable_fence_after_all_replies(after):
            return move
    return None


def _white_rook_square(board: chess.Board) -> int | None:
    rooks = sorted(board.pieces(chess.ROOK, chess.WHITE))
    return rooks[0] if rooks else None


def _white_king_defends_square(board: chess.Board, square: int) -> bool:
    white_king = board.king(chess.WHITE)
    return white_king is not None and chess.square_distance(white_king, square) <= 1


def _rook_on_black_king_edge_line(
    board: chess.Board,
    *,
    features: dict[str, float],
) -> bool:
    if features["rook_distance_to_black_king_edge_line"] == 0.0:
        return True

    black_king = board.king(chess.BLACK)
    rook = _white_rook_square(board)
    if black_king is None or rook is None:
        return False
    if features["black_king_corner_distance"] != 0.0:
        return False

    return (
        chess.square_file(rook) == chess.square_file(black_king)
        or chess.square_rank(rook) == chess.square_rank(black_king)
    )


def _black_king_along_edge_squares(black_king: int) -> tuple[int, ...]:
    file_idx = chess.square_file(black_king)
    rank_idx = chess.square_rank(black_king)
    squares: set[int] = set()
    if file_idx in (0, 7):
        for rank_delta in (-1, 1):
            rank = rank_idx + rank_delta
            if 0 <= rank <= 7:
                squares.add(chess.square(file_idx, rank))
    if rank_idx in (0, 7):
        for file_delta in (-1, 1):
            file_ = file_idx + file_delta
            if 0 <= file_ <= 7:
                squares.add(chess.square(file_, rank_idx))
    return tuple(sorted(squares))


def _white_covers_with_black_king_vacated(board: chess.Board, square: int) -> bool:
    black_king = board.king(chess.BLACK)
    if black_king is None:
        return False
    vacated = board.copy(stack=False)
    vacated.remove_piece_at(black_king)
    return vacated.is_attacked_by(chess.WHITE, square)


def _has_deliver_edge_mate_geometry(after_board: chess.Board) -> bool:
    rook = _white_rook_square(after_board)
    black_king = after_board.king(chess.BLACK)
    if rook is None or black_king is None:
        return False

    features = extract_learner_features(after_board)
    if not _rook_on_black_king_edge_line(after_board, features=features):
        return False
    if features["rook_attacked_by_black"] > 0.0 and not _white_king_defends_square(
        after_board,
        rook,
    ):
        return False

    return all(
        _white_covers_with_black_king_vacated(after_board, square)
        for square in _black_king_along_edge_squares(black_king)
    )


def resolve_deliver_edge_mate_move(board: chess.Board) -> chess.Move | None:
    """Resolve the requested edge-mate actuator by one-ply rook-move geometry."""

    rook = _white_rook_square(board)
    if rook is None or board.turn != chess.WHITE:
        return None

    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        if move.from_square != rook:
            continue
        after = board.copy(stack=False)
        after.push(move)
        if _has_deliver_edge_mate_geometry(after):
            return move
    return None


def _deliver_edge_mate_predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
    board = env["board"]
    move = resolve_deliver_edge_mate_move(board)
    if move is None:
        node.meta["last_failure"] = "no_legal_rook_move_realized_edge_mate_delta"
        node.activation.value = 0.0
        return True, False

    node.meta["bound_move"] = move.uci()
    node.activation.value = 1.0
    env.setdefault("mate_in_1_skill", {})["bound_move"] = move.uci()
    return True, True


def _add_mate_in_one_skill_subgraph(graph: Graph, parent_id: str, *, prefix: str = "") -> None:
    skill_id = _prefixed(prefix, MATE_IN_ONE_SKILL_ID)
    recognizer_step_id = _prefixed(prefix, MATE_IN_ONE_RECOGNIZER_STEP_ID)
    deliver_step_id = _prefixed(prefix, DELIVER_EDGE_MATE_SCRIPT_ID)
    deliver_actuator_id = _prefixed(prefix, DELIVER_EDGE_MATE_ACTUATOR_ID)

    graph.add_node(
        Node(
            skill_id,
            NodeType.SCRIPT,
            meta={"role": "mate_in_1_skill"},
        )
    )
    graph.add_node(
        Node(
            recognizer_step_id,
            NodeType.SCRIPT,
            meta={"role": "mate_in_1_basin_recognizer_step"},
        )
    )
    _add_mate_in_one_basin_subgraph(graph, recognizer_step_id, prefix=prefix)
    _add_quorum_script(
        graph,
        deliver_step_id,
        role="deliver_edge_mate_step",
        policy="and",
    )
    graph.add_node(
        Node(
            deliver_actuator_id,
            NodeType.TERMINAL,
            predicate=_deliver_edge_mate_predicate,
            meta={
                "role": "actuator_terminal",
                "actuator": "deliver_edge_mate",
                "delta": "rook_distance_to_black_king_edge_line_to_zero",
            },
        )
    )
    graph.add_hierarchy_pair(parent_id, skill_id)
    graph.add_hierarchy_pair(skill_id, recognizer_step_id)
    graph.add_hierarchy_pair(skill_id, deliver_step_id)
    graph.add_hierarchy_pair(deliver_step_id, deliver_actuator_id)
    graph.add_sequence_pair(recognizer_step_id, deliver_step_id)


def build_mate_in_one_skill_graph() -> Graph:
    """Build recognizer POR actuator skill graph; no learned weights are used."""

    graph = Graph()
    graph.add_node(Node(MATE_IN_ONE_SKILL_ROOT_ID, NodeType.SCRIPT))
    _add_mate_in_one_skill_subgraph(graph, MATE_IN_ONE_SKILL_ROOT_ID)
    graph.validate_formal_pairs()
    return graph


def _virtual_frame(board: chess.Board) -> dict[str, Any]:
    framed = board.copy(stack=False)
    return {"board": framed, "features": extract_learner_features(framed)}


def _after_move(board: chess.Board, move: chess.Move) -> chess.Board:
    after = board.copy(stack=False)
    after.push(move)
    return after


def _bind_first_move_predicate(move_uci: str) -> Callable[[Node, dict[str, Any]], tuple[bool, bool]]:
    move = chess.Move.from_uci(move_uci)

    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        board = env["board"]
        if move not in board.legal_moves:
            node.meta["last_failure"] = "candidate_first_move_not_legal"
            node.activation.value = 0.0
            return True, False
        node.meta["bound_move"] = move_uci
        node.activation.value = 1.0
        env.setdefault("mate_in_2_skill", {})["candidate_move"] = move_uci
        return True, True

    return predicate


def _bind_rook_move_predicate(move_uci: str) -> Callable[[Node, dict[str, Any]], tuple[bool, bool]]:
    move = chess.Move.from_uci(move_uci)

    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        board = env["board"]
        rook = _white_rook_square(board)
        if rook is None or move.from_square != rook or move not in board.legal_moves:
            node.meta["last_failure"] = "candidate_rook_move_not_legal"
            node.activation.value = 0.0
            return True, False
        node.meta["bound_move"] = move_uci
        node.activation.value = 1.0
        env.setdefault("establish_fence_skill", {})["candidate_move"] = move_uci
        return True, True

    return predicate


def _zero_reply_predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
    board = env["board"]
    no_replies = board.legal_moves.count() == 0
    in_check = board.is_check()
    success = bool(no_replies and in_check)
    node.meta["zero_reply_in_check"] = bool(in_check)
    node.activation.value = 1.0 if success else 0.0
    return True, success


def _add_rook_move_bind_subgraph(
    graph: Graph,
    parent_id: str,
    *,
    move: chess.Move,
    prefix: str,
) -> str:
    bind_step_id = _prefixed(prefix, "bind_rook_move_step")
    bind_terminal_id = _prefixed(prefix, "bind_rook_move")
    graph.add_node(
        Node(
            bind_step_id,
            NodeType.SCRIPT,
            meta={"role": "establish_fence_bind_rook_move_step", "move": move.uci()},
        )
    )
    graph.add_node(
        Node(
            bind_terminal_id,
            NodeType.TERMINAL,
            predicate=_bind_rook_move_predicate(move.uci()),
            meta={
                "role": "actuator_terminal",
                "actuator": "bind_candidate_rook_fence_move",
                "move": move.uci(),
            },
        )
    )
    graph.add_hierarchy_pair(parent_id, bind_step_id)
    graph.add_hierarchy_pair(bind_step_id, bind_terminal_id)
    return bind_step_id


def _add_first_move_bind_subgraph(
    graph: Graph,
    parent_id: str,
    *,
    move: chess.Move,
    prefix: str,
) -> str:
    bind_step_id = _prefixed(prefix, "bind_first_move_step")
    bind_terminal_id = _prefixed(prefix, "bind_first_move")
    graph.add_node(
        Node(
            bind_step_id,
            NodeType.SCRIPT,
            meta={"role": "mate_in_2_bind_first_move_step", "move": move.uci()},
        )
    )
    graph.add_node(
        Node(
            bind_terminal_id,
            NodeType.TERMINAL,
            predicate=_bind_first_move_predicate(move.uci()),
            meta={
                "role": "actuator_terminal",
                "actuator": "bind_candidate_first_move",
                "move": move.uci(),
            },
        )
    )
    graph.add_hierarchy_pair(parent_id, bind_step_id)
    graph.add_hierarchy_pair(bind_step_id, bind_terminal_id)
    return bind_step_id


def _add_reply_quantifier_subgraph(
    graph: Graph,
    parent_id: str,
    *,
    board: chess.Board,
    prefix: str,
    virtual_frames: dict[str, dict[str, Any]],
) -> tuple[str, int]:
    quantifier_id = _prefixed(prefix, REPLY_QUANTIFIER_ID)
    replies = sorted(board.legal_moves, key=lambda item: item.uci())
    _add_quorum_script(
        graph,
        quantifier_id,
        role="mate_in_2_reply_quantifier",
        policy="k_of_n",
        k=max(1, len(replies)),
    )
    graph.nodes[quantifier_id].meta["reply_count"] = len(replies)
    graph.add_hierarchy_pair(parent_id, quantifier_id)
    virtual_frames[quantifier_id] = _virtual_frame(board)

    if not replies:
        terminal_id = _prefixed(prefix, "zero_reply_semantics")
        graph.add_node(
            Node(
                terminal_id,
                NodeType.TERMINAL,
                predicate=_zero_reply_predicate,
                meta={"role": "reply_quantifier_zero_reply_semantics"},
            )
        )
        graph.add_hierarchy_pair(quantifier_id, terminal_id)
        return quantifier_id, 1

    frame_count = 1
    for reply in replies:
        reply_prefix = f"{prefix}reply_{_safe_move_id(reply)}__"
        reply_child_id = _prefixed(reply_prefix, "reply_child")
        reply_board = _after_move(board, reply)
        graph.add_node(
            Node(
                reply_child_id,
                NodeType.SCRIPT,
                meta={"role": "mate_in_2_reply_child", "reply_move": reply.uci()},
            )
        )
        graph.add_hierarchy_pair(quantifier_id, reply_child_id)
        virtual_frames[reply_child_id] = _virtual_frame(reply_board)
        frame_count += 1
        _add_mate_in_one_skill_subgraph(graph, reply_child_id, prefix=reply_prefix)
    return quantifier_id, frame_count


def _add_fence_reply_quantifier_subgraph(
    graph: Graph,
    parent_id: str,
    *,
    board: chess.Board,
    prefix: str,
    virtual_frames: dict[str, dict[str, Any]],
) -> tuple[str, int]:
    quantifier_id = _prefixed(prefix, FENCE_REPLY_QUANTIFIER_ID)
    replies = sorted(board.legal_moves, key=lambda item: item.uci())
    _add_quorum_script(
        graph,
        quantifier_id,
        role="establish_fence_reply_quantifier",
        policy="k_of_n",
        k=max(1, len(replies)),
    )
    graph.nodes[quantifier_id].meta["reply_count"] = len(replies)
    graph.add_hierarchy_pair(parent_id, quantifier_id)
    virtual_frames[quantifier_id] = _virtual_frame(board)

    if not replies:
        terminal_id = _prefixed(prefix, "zero_reply_semantics")
        graph.add_node(
            Node(
                terminal_id,
                NodeType.TERMINAL,
                predicate=_zero_reply_predicate,
                meta={"role": "reply_quantifier_zero_reply_semantics"},
            )
        )
        graph.add_hierarchy_pair(quantifier_id, terminal_id)
        return quantifier_id, 1

    frame_count = 1
    for reply in replies:
        reply_prefix = f"{prefix}reply_{_safe_move_id(reply)}__"
        reply_child_id = _prefixed(reply_prefix, "fence_reply_child")
        reply_board = _after_move(board, reply)
        graph.add_node(
            Node(
                reply_child_id,
                NodeType.SCRIPT,
                meta={"role": "establish_fence_reply_child", "reply_move": reply.uci()},
            )
        )
        graph.add_hierarchy_pair(quantifier_id, reply_child_id)
        virtual_frames[reply_child_id] = _virtual_frame(reply_board)
        frame_count += 1
        _add_fence_established_subgraph(graph, reply_child_id, prefix=reply_prefix)
    return quantifier_id, frame_count


def build_reply_quantifier_graph(board: chess.Board) -> tuple[Graph, dict[str, dict[str, Any]]]:
    """Build a standalone reply quantifier for a black-to-move virtual board."""

    graph = Graph()
    virtual_frames: dict[str, dict[str, Any]] = {}
    graph.add_node(Node(REPLY_QUANTIFIER_ROOT_ID, NodeType.SCRIPT))
    _add_reply_quantifier_subgraph(
        graph,
        REPLY_QUANTIFIER_ROOT_ID,
        board=board,
        prefix="",
        virtual_frames=virtual_frames,
    )
    graph.validate_formal_pairs()
    return graph, virtual_frames


def build_fence_reply_quantifier_graph(board: chess.Board) -> tuple[Graph, dict[str, dict[str, Any]]]:
    """Build a standalone fence reply quantifier for a black-to-move virtual board."""

    graph = Graph()
    virtual_frames: dict[str, dict[str, Any]] = {}
    graph.add_node(Node(FENCE_REPLY_QUANTIFIER_ROOT_ID, NodeType.SCRIPT))
    _add_fence_reply_quantifier_subgraph(
        graph,
        FENCE_REPLY_QUANTIFIER_ROOT_ID,
        board=board,
        prefix="",
        virtual_frames=virtual_frames,
    )
    graph.validate_formal_pairs()
    return graph, virtual_frames


def _add_mate_in_two_candidate_subgraph(
    graph: Graph,
    parent_id: str,
    *,
    board: chess.Board,
    move: chess.Move,
    virtual_frames: dict[str, dict[str, Any]],
    order_rank: int,
) -> int:
    candidate_prefix = f"candidate_{_safe_move_id(move)}__"
    candidate_id = _prefixed(candidate_prefix, "mate_in_2_candidate")
    after_first = _after_move(board, move)
    graph.add_node(
        Node(
            candidate_id,
            NodeType.SCRIPT,
            meta={
                "role": "mate_in_2_candidate",
                "first_move": move.uci(),
                "candidate_order_rank": int(order_rank),
            },
        )
    )
    graph.add_hierarchy_pair(parent_id, candidate_id)
    bind_step_id = _add_first_move_bind_subgraph(
        graph,
        candidate_id,
        move=move,
        prefix=candidate_prefix,
    )
    quantifier_id, frame_count = _add_reply_quantifier_subgraph(
        graph,
        candidate_id,
        board=after_first,
        prefix=candidate_prefix,
        virtual_frames=virtual_frames,
    )
    graph.add_sequence_pair(bind_step_id, quantifier_id)
    graph.nodes[candidate_id].meta["virtual_frame_count"] = int(frame_count)
    return frame_count


def _add_establish_fence_candidate_subgraph(
    graph: Graph,
    parent_id: str,
    *,
    board: chess.Board,
    move: chess.Move,
    virtual_frames: dict[str, dict[str, Any]],
    order_rank: int,
) -> int:
    candidate_prefix = f"fence_candidate_{_safe_move_id(move)}__"
    candidate_id = _prefixed(candidate_prefix, "establish_fence_candidate")
    after_first = _after_move(board, move)
    graph.add_node(
        Node(
            candidate_id,
            NodeType.SCRIPT,
            meta={
                "role": "establish_fence_candidate",
                "first_move": move.uci(),
                "candidate_order_rank": int(order_rank),
            },
        )
    )
    graph.add_hierarchy_pair(parent_id, candidate_id)
    bind_step_id = _add_rook_move_bind_subgraph(
        graph,
        candidate_id,
        move=move,
        prefix=candidate_prefix,
    )
    quantifier_id, frame_count = _add_fence_reply_quantifier_subgraph(
        graph,
        candidate_id,
        board=after_first,
        prefix=candidate_prefix,
        virtual_frames=virtual_frames,
    )
    graph.add_sequence_pair(bind_step_id, quantifier_id)
    graph.nodes[candidate_id].meta["virtual_frame_count"] = int(frame_count)
    return frame_count


def build_mate_in_two_skill_graph(
    board: chess.Board,
    *,
    lazy_candidates: bool = True,
    move_orderer: Callable[[chess.Board, Sequence[chess.Move]], Sequence[chess.Move]] | None = None,
) -> tuple[Graph, dict[str, dict[str, Any]], dict[str, Any]]:
    """Build exact mate-in-2 skill graph over all legal first moves."""

    graph = Graph()
    virtual_frames: dict[str, dict[str, Any]] = {}
    graph.add_node(Node(MATE_IN_TWO_SKILL_ROOT_ID, NodeType.SCRIPT))
    _add_quorum_script(
        graph,
        MATE_IN_TWO_SKILL_ID,
        role="mate_in_2_skill",
        policy="k_of_n",
        k=1,
    )
    if lazy_candidates:
        graph.nodes[MATE_IN_TWO_SKILL_ID].meta["request_policy"] = "lazy_k_of_n"
    graph.add_hierarchy_pair(MATE_IN_TWO_SKILL_ROOT_ID, MATE_IN_TWO_SKILL_ID)

    legal_moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    if move_orderer is None:
        ordered_moves = legal_moves
    else:
        ordered_moves = tuple(move_orderer(board, legal_moves))
        legal_uci = [move.uci() for move in legal_moves]
        ordered_uci = [move.uci() for move in ordered_moves]
        if len(ordered_uci) != len(legal_uci) or set(ordered_uci) != set(legal_uci):
            raise ValueError("move_orderer must return each legal move exactly once")
    immediate_mates = tuple(
        move for move in ordered_moves if _move_confirms_zero_reply_mate(board, move)
    )
    if immediate_mates:
        immediate_uci = {move.uci() for move in immediate_mates}
        ordered_moves = immediate_mates + tuple(
            move for move in ordered_moves if move.uci() not in immediate_uci
        )

    candidate_count = 0
    frame_count = 0
    candidate_order: list[str] = []
    for order_rank, move in enumerate(ordered_moves, start=1):
        candidate_count += 1
        candidate_order.append(move.uci())
        frame_count += _add_mate_in_two_candidate_subgraph(
            graph,
            MATE_IN_TWO_SKILL_ID,
            board=board,
            move=move,
            virtual_frames=virtual_frames,
            order_rank=order_rank,
        )

    graph.validate_formal_pairs()
    return graph, virtual_frames, {
        "candidate_count": candidate_count,
        "virtual_frame_count": frame_count,
        "candidate_order": candidate_order,
    }


def _always_fail_predicate(node: Node, _env: dict[str, Any]) -> tuple[bool, bool]:
    node.activation.value = 0.0
    return True, False


def build_establish_fence_skill_graph(
    board: chess.Board,
    *,
    lazy_candidates: bool = True,
) -> tuple[Graph, dict[str, dict[str, Any]], dict[str, Any]]:
    """Build exact fence-establishment graph over all legal rook moves."""

    graph = Graph()
    virtual_frames: dict[str, dict[str, Any]] = {}
    graph.add_node(Node(ESTABLISH_FENCE_SKILL_ROOT_ID, NodeType.SCRIPT))
    _add_quorum_script(
        graph,
        ESTABLISH_FENCE_SKILL_ID,
        role="establish_fence_skill",
        policy="k_of_n",
        k=1,
    )
    if lazy_candidates:
        graph.nodes[ESTABLISH_FENCE_SKILL_ID].meta["request_policy"] = "lazy_k_of_n"
    graph.add_hierarchy_pair(ESTABLISH_FENCE_SKILL_ROOT_ID, ESTABLISH_FENCE_SKILL_ID)

    rook = _white_rook_square(board)
    legal_rook_moves = tuple(
        move
        for move in sorted(board.legal_moves, key=lambda item: item.uci())
        if rook is not None and move.from_square == rook
    )
    candidate_order: list[str] = []
    frame_count = 0
    if not legal_rook_moves:
        terminal_id = "establish_fence_no_legal_rook_move"
        graph.add_node(
            Node(
                terminal_id,
                NodeType.TERMINAL,
                predicate=_always_fail_predicate,
                meta={"role": "establish_fence_no_legal_rook_move"},
            )
        )
        graph.add_hierarchy_pair(ESTABLISH_FENCE_SKILL_ID, terminal_id)
    for order_rank, move in enumerate(legal_rook_moves, start=1):
        candidate_order.append(move.uci())
        frame_count += _add_establish_fence_candidate_subgraph(
            graph,
            ESTABLISH_FENCE_SKILL_ID,
            board=board,
            move=move,
            virtual_frames=virtual_frames,
            order_rank=order_rank,
        )

    graph.validate_formal_pairs()
    return graph, virtual_frames, {
        "candidate_count": len(legal_rook_moves),
        "virtual_frame_count": frame_count,
        "candidate_order": candidate_order,
    }


def _descendant_nodes(graph: Graph, node_id: str) -> set[str]:
    descendants: set[str] = set()
    stack = list(graph.children(node_id))
    while stack:
        child = stack.pop()
        if child in descendants:
            continue
        descendants.add(child)
        stack.extend(graph.children(child))
    return descendants


def _mate_in_two_lazy_active_nodes(
    graph: Graph,
    candidate_descendants: dict[str, set[str]],
) -> set[str]:
    active = {MATE_IN_TWO_SKILL_ROOT_ID, MATE_IN_TWO_SKILL_ID}
    for candidate_id in graph.children(MATE_IN_TWO_SKILL_ID):
        active.add(candidate_id)
        if graph.nodes[candidate_id].state != NodeState.INACTIVE:
            active.update(candidate_descendants[candidate_id])
    return active


def _lazy_skill_active_nodes(
    graph: Graph,
    *,
    root_id: str,
    skill_id: str,
    candidate_descendants: dict[str, set[str]],
) -> set[str]:
    active = {root_id, skill_id}
    for candidate_id in graph.children(skill_id):
        active.add(candidate_id)
        if graph.nodes[candidate_id].state != NodeState.INACTIVE:
            active.update(candidate_descendants.get(candidate_id, set()))
    return active


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
        "king_support_geometry_state": graph.nodes[KING_SUPPORT_GEOMETRY_ID].state.name,
        "edge_relative_opposition_state": graph.nodes[EDGE_RELATIVE_OPPOSITION_ID].state.name,
        "corner_knight_support_state": graph.nodes[CORNER_KNIGHT_SUPPORT_ID].state.name,
        "ticks": engine.tick,
        "features": features,
        "atom_states": atom_states,
        "script_states": script_states,
        "trace": trace,
    }


def run_fence_established_recognizer(
    board: chess.Board,
    *,
    max_ticks: int = 32,
    record_trace: bool = True,
) -> dict[str, Any]:
    """Execute the fixed fence recognizer on one board."""

    graph = build_fence_established_graph()
    features = extract_learner_features(board)
    engine = FormalReConEngine(graph, record_trace=record_trace)
    engine.request(FENCE_ESTABLISHED_ROOT_ID)
    trace = engine.run(
        max_ticks=max_ticks,
        env={"board": board, "features": features},
        until=lambda _engine: graph.nodes[FENCE_ESTABLISHED_ROOT_ID].state
        in (NodeState.CONFIRMED, NodeState.FAILED),
    )
    script_states = {
        node_id: node.state.name
        for node_id, node in sorted(graph.nodes.items())
        if node.ntype == NodeType.SCRIPT
    }
    return {
        "confirmed": graph.nodes[FENCE_ESTABLISHED_ID].state == NodeState.CONFIRMED,
        "root_state": graph.nodes[FENCE_ESTABLISHED_ROOT_ID].state.name,
        "fence_state": graph.nodes[FENCE_ESTABLISHED_ID].state.name,
        "edge_selector_state": graph.nodes[FENCE_EDGE_SELECTOR_ID].state.name,
        "rook_safety_state": graph.nodes[FENCE_ROOK_SAFETY_ID].state.name,
        "ticks": engine.tick,
        "features": features,
        "script_states": script_states,
        "trace": trace,
    }


def run_mate_in_one_skill(
    board: chess.Board,
    *,
    max_ticks: int = 48,
    record_trace: bool = True,
) -> dict[str, Any]:
    """Execute the Mate-in-1 recognizer-to-actuator skill on one board."""

    graph = build_mate_in_one_skill_graph()
    features = extract_learner_features(board)
    env: dict[str, Any] = {"board": board, "features": features}
    engine = FormalReConEngine(graph, record_trace=record_trace)
    engine.request(MATE_IN_ONE_SKILL_ROOT_ID)
    trace = engine.run(
        max_ticks=max_ticks,
        env=env,
        until=lambda _engine: graph.nodes[MATE_IN_ONE_SKILL_ROOT_ID].state
        in (NodeState.CONFIRMED, NodeState.FAILED),
    )
    actuator_node = graph.nodes[DELIVER_EDGE_MATE_ACTUATOR_ID]
    script_states = {
        node_id: node.state.name
        for node_id, node in sorted(graph.nodes.items())
        if node.ntype == NodeType.SCRIPT
    }
    return {
        "confirmed": graph.nodes[MATE_IN_ONE_SKILL_ID].state == NodeState.CONFIRMED,
        "root_state": graph.nodes[MATE_IN_ONE_SKILL_ROOT_ID].state.name,
        "skill_state": graph.nodes[MATE_IN_ONE_SKILL_ID].state.name,
        "recognizer_step_state": graph.nodes[MATE_IN_ONE_RECOGNIZER_STEP_ID].state.name,
        "basin_state": graph.nodes[MATE_IN_ONE_BASIN_ID].state.name,
        "actuator_script_state": graph.nodes[DELIVER_EDGE_MATE_SCRIPT_ID].state.name,
        "actuator_state": actuator_node.state.name,
        "bound_move": actuator_node.meta.get("bound_move"),
        "ticks": engine.tick,
        "features": features,
        "script_states": script_states,
        "trace": trace,
    }


def run_reply_quantifier(
    board: chess.Board,
    *,
    max_ticks: int = 96,
    record_trace: bool = True,
) -> dict[str, Any]:
    """Execute the reply quantifier on a black-to-move virtual board."""

    graph, virtual_frames = build_reply_quantifier_graph(board)
    env = {
        "board": board,
        "features": extract_learner_features(board),
        "virtual_frames": virtual_frames,
    }
    engine = FormalReConEngine(graph, record_trace=record_trace)
    engine.request(REPLY_QUANTIFIER_ROOT_ID)
    trace = engine.run(
        max_ticks=max_ticks,
        env=env,
        until=lambda _engine: graph.nodes[REPLY_QUANTIFIER_ROOT_ID].state
        in (NodeState.CONFIRMED, NodeState.FAILED),
    )
    return {
        "confirmed": graph.nodes[REPLY_QUANTIFIER_ID].state == NodeState.CONFIRMED,
        "root_state": graph.nodes[REPLY_QUANTIFIER_ROOT_ID].state.name,
        "quantifier_state": graph.nodes[REPLY_QUANTIFIER_ID].state.name,
        "reply_count": graph.nodes[REPLY_QUANTIFIER_ID].meta.get("reply_count"),
        "virtual_frame_count": len(virtual_frames),
        "trace": trace,
    }


def run_fence_reply_quantifier(
    board: chess.Board,
    *,
    max_ticks: int = 96,
    record_trace: bool = True,
) -> dict[str, Any]:
    """Execute the fence reply quantifier on a black-to-move virtual board."""

    graph, virtual_frames = build_fence_reply_quantifier_graph(board)
    env = {
        "board": board,
        "features": extract_learner_features(board),
        "virtual_frames": virtual_frames,
    }
    engine = FormalReConEngine(graph, record_trace=record_trace)
    engine.request(FENCE_REPLY_QUANTIFIER_ROOT_ID)
    trace = engine.run(
        max_ticks=max_ticks,
        env=env,
        until=lambda _engine: graph.nodes[FENCE_REPLY_QUANTIFIER_ROOT_ID].state
        in (NodeState.CONFIRMED, NodeState.FAILED),
    )
    return {
        "confirmed": graph.nodes[FENCE_REPLY_QUANTIFIER_ID].state == NodeState.CONFIRMED,
        "root_state": graph.nodes[FENCE_REPLY_QUANTIFIER_ROOT_ID].state.name,
        "quantifier_state": graph.nodes[FENCE_REPLY_QUANTIFIER_ID].state.name,
        "reply_count": graph.nodes[FENCE_REPLY_QUANTIFIER_ID].meta.get("reply_count"),
        "virtual_frame_count": len(virtual_frames),
        "trace": trace,
    }


def run_mate_in_two_skill(
    board: chess.Board,
    *,
    max_ticks: int = 2048,
    record_trace: bool = True,
    lazy_candidates: bool = True,
    move_orderer: Callable[[chess.Board, Sequence[chess.Move]], Sequence[chess.Move]] | None = None,
) -> dict[str, Any]:
    """Execute the exact mate-in-2 skill with universal reply confirmation."""

    graph, virtual_frames, counts = build_mate_in_two_skill_graph(
        board,
        lazy_candidates=lazy_candidates,
        move_orderer=move_orderer,
    )
    env = {
        "board": board,
        "features": extract_learner_features(board),
        "virtual_frames": virtual_frames,
    }
    engine = FormalReConEngine(graph, record_trace=record_trace)
    engine.request(MATE_IN_TWO_SKILL_ROOT_ID)
    if lazy_candidates:
        candidate_descendants = {
            candidate_id: _descendant_nodes(graph, candidate_id)
            for candidate_id in graph.children(MATE_IN_TWO_SKILL_ID)
        }
        for _ in range(max(0, max_ticks)):
            engine.step_subset(
                env,
                active_nodes=_mate_in_two_lazy_active_nodes(graph, candidate_descendants),
            )
            if graph.nodes[MATE_IN_TWO_SKILL_ROOT_ID].state in (
                NodeState.CONFIRMED,
                NodeState.FAILED,
            ):
                break
        trace = engine.trace
    else:
        trace = engine.run(
            max_ticks=max_ticks,
            env=env,
            until=lambda _engine: graph.nodes[MATE_IN_TWO_SKILL_ROOT_ID].state
            in (NodeState.CONFIRMED, NodeState.FAILED),
        )

    confirmed_candidates = sorted(
        (
            node.meta["first_move"],
            node_id,
        )
        for node_id, node in graph.nodes.items()
        if node.meta.get("role") == "mate_in_2_candidate"
        and node.state == NodeState.CONFIRMED
    )
    bound_move = confirmed_candidates[0][0] if confirmed_candidates else None
    if bound_move is not None:
        graph.nodes[MATE_IN_TWO_SKILL_ID].meta["bound_move"] = bound_move

    candidate_nodes = [
        (node_id, node)
        for node_id, node in graph.nodes.items()
        if node.meta.get("role") == "mate_in_2_candidate"
    ]
    requested_candidates = [
        (node_id, node)
        for node_id, node in candidate_nodes
        if node.state != NodeState.INACTIVE
    ]
    expanded_virtual_frame_count = sum(
        int(node.meta.get("virtual_frame_count", 0))
        for _node_id, node in requested_candidates
    )
    candidate_order = list(counts["candidate_order"])
    bound_move_rank = (
        candidate_order.index(bound_move) + 1
        if bound_move in candidate_order
        else None
    )

    script_states = {
        node_id: node.state.name
        for node_id, node in sorted(graph.nodes.items())
        if node.ntype == NodeType.SCRIPT
    }
    return {
        "confirmed": graph.nodes[MATE_IN_TWO_SKILL_ID].state == NodeState.CONFIRMED,
        "root_state": graph.nodes[MATE_IN_TWO_SKILL_ROOT_ID].state.name,
        "skill_state": graph.nodes[MATE_IN_TWO_SKILL_ID].state.name,
        "bound_move": bound_move,
        "confirmed_candidate_count": len(confirmed_candidates),
        "candidate_count": counts["candidate_count"],
        "candidate_order": candidate_order,
        "bound_move_rank": bound_move_rank,
        "requested_candidate_count": len(requested_candidates),
        "built_virtual_frame_count": len(virtual_frames),
        "all_candidate_virtual_frame_count": counts["virtual_frame_count"],
        "virtual_frame_count": expanded_virtual_frame_count,
        "expanded_virtual_frame_count": expanded_virtual_frame_count,
        "ticks": engine.tick,
        "script_states": script_states,
        "trace": trace,
    }


def run_establish_fence_skill(
    board: chess.Board,
    *,
    max_ticks: int = 2048,
    record_trace: bool = True,
    lazy_candidates: bool = True,
) -> dict[str, Any]:
    """Execute the exact fence-establishment skill with universal reply confirmation."""

    graph, virtual_frames, counts = build_establish_fence_skill_graph(
        board,
        lazy_candidates=lazy_candidates,
    )
    env = {
        "board": board,
        "features": extract_learner_features(board),
        "virtual_frames": virtual_frames,
    }
    engine = FormalReConEngine(graph, record_trace=record_trace)
    engine.request(ESTABLISH_FENCE_SKILL_ROOT_ID)
    if lazy_candidates:
        candidate_descendants = {
            candidate_id: _descendant_nodes(graph, candidate_id)
            for candidate_id in graph.children(ESTABLISH_FENCE_SKILL_ID)
        }
        for _ in range(max(0, max_ticks)):
            engine.step_subset(
                env,
                active_nodes=_lazy_skill_active_nodes(
                    graph,
                    root_id=ESTABLISH_FENCE_SKILL_ROOT_ID,
                    skill_id=ESTABLISH_FENCE_SKILL_ID,
                    candidate_descendants=candidate_descendants,
                ),
            )
            if graph.nodes[ESTABLISH_FENCE_SKILL_ROOT_ID].state in (
                NodeState.CONFIRMED,
                NodeState.FAILED,
            ):
                break
        trace = engine.trace
    else:
        trace = engine.run(
            max_ticks=max_ticks,
            env=env,
            until=lambda _engine: graph.nodes[ESTABLISH_FENCE_SKILL_ROOT_ID].state
            in (NodeState.CONFIRMED, NodeState.FAILED),
        )

    confirmed_candidates = sorted(
        (
            node.meta["first_move"],
            node_id,
        )
        for node_id, node in graph.nodes.items()
        if node.meta.get("role") == "establish_fence_candidate"
        and node.state == NodeState.CONFIRMED
    )
    bound_move = confirmed_candidates[0][0] if confirmed_candidates else None
    if bound_move is not None:
        graph.nodes[ESTABLISH_FENCE_SKILL_ID].meta["bound_move"] = bound_move

    candidate_nodes = [
        (node_id, node)
        for node_id, node in graph.nodes.items()
        if node.meta.get("role") == "establish_fence_candidate"
    ]
    requested_candidates = [
        (node_id, node)
        for node_id, node in candidate_nodes
        if node.state != NodeState.INACTIVE
    ]
    expanded_virtual_frame_count = sum(
        int(node.meta.get("virtual_frame_count", 0))
        for _node_id, node in requested_candidates
    )
    candidate_order = list(counts["candidate_order"])
    bound_move_rank = (
        candidate_order.index(bound_move) + 1
        if bound_move in candidate_order
        else None
    )

    script_states = {
        node_id: node.state.name
        for node_id, node in sorted(graph.nodes.items())
        if node.ntype == NodeType.SCRIPT
    }
    return {
        "confirmed": graph.nodes[ESTABLISH_FENCE_SKILL_ID].state == NodeState.CONFIRMED,
        "root_state": graph.nodes[ESTABLISH_FENCE_SKILL_ROOT_ID].state.name,
        "skill_state": graph.nodes[ESTABLISH_FENCE_SKILL_ID].state.name,
        "bound_move": bound_move,
        "confirmed_candidate_count": len(confirmed_candidates),
        "candidate_count": counts["candidate_count"],
        "candidate_order": candidate_order,
        "bound_move_rank": bound_move_rank,
        "requested_candidate_count": len(requested_candidates),
        "built_virtual_frame_count": len(virtual_frames),
        "all_candidate_virtual_frame_count": counts["virtual_frame_count"],
        "virtual_frame_count": expanded_virtual_frame_count,
        "expanded_virtual_frame_count": expanded_virtual_frame_count,
        "ticks": engine.tick,
        "script_states": script_states,
        "trace": trace,
    }


CHAIN_CONFIDENCE_OUTPUT_DIR = Path(
    "reports/autogrowth/clean_slate_krk/phase2_chain_confidence_v1"
)
CHAIN_CONFIDENCE_POOL_SCHEMA = "phase2_chain_confidence_pool_row.v0"
CHAIN_CONFIDENCE_MODEL_SCHEMA = "phase2_chain_confidence_weighted_threshold.v0"


def load_chain_confidence_gate(
    *,
    seed: int = 20261211,
    threshold_name: str = "balanced",
    output_dir: str | Path = CHAIN_CONFIDENCE_OUTPUT_DIR,
) -> dict[str, Any]:
    """Load a trained dispatcher gate without changing exact confirmation semantics."""

    path = Path(output_dir) / f"chain_confidence_gate_seed_{int(seed)}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    model = payload["model"]
    if threshold_name not in model["thresholds"]:
        raise ValueError(f"threshold {threshold_name!r} not found in {path}")
    return {
        "artifact_path": str(path),
        "seed": int(seed),
        "threshold_name": threshold_name,
        "threshold": float(model["thresholds"][threshold_name]),
        "model": model,
    }


def fence_or_opposition_recognizer_confirms(board: chess.Board) -> bool:
    """Internal geometry recognizer bit over dieted percepts."""

    features = extract_learner_features(board)
    direct_opposition = (
        features["king_support_chebyshev_distance"] == 2.0
        and (
            features["king_delta_file_abs"] == 0.0
            or features["king_delta_rank_abs"] == 0.0
        )
    )
    rook_fence = (
        features["rook_present"] == 1.0
        and features["rook_attacked_by_black"] == 0.0
        and features["black_king_nearest_edge_distance"] >= 1.0
        and features["rook_black_king_opposite_sides_of_white_king_on_primary_axis"] == 1.0
    )
    return bool(direct_opposition or rook_fence)


def chain_confidence_feature_record(board: chess.Board) -> dict[str, float]:
    """Dieted percepts plus internal recognizer confirmation bits for the gate."""

    features = dict(extract_learner_features(board))
    basin = run_mate_in_one_basin_recognizer(
        board,
        record_trace=False,
    )["confirmed"]
    features["internal_mate_in_1_basin_confirms"] = 1.0 if basin else 0.0
    features["internal_fence_or_opposition_confirms"] = (
        1.0 if fence_or_opposition_recognizer_confirms(board) else 0.0
    )
    return features


def _run_ordered_exact_mate_in_two(
    board: chess.Board,
    *,
    move_orderer: Callable[[chess.Board, Sequence[chess.Move]], Sequence[chess.Move]] | None,
) -> dict[str, Any]:
    legal_moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    moves = legal_moves if move_orderer is None else tuple(move_orderer(board, legal_moves))
    legal_uci = {move.uci() for move in legal_moves}
    if len(moves) != len(legal_moves) or {move.uci() for move in moves} != legal_uci:
        raise ValueError("move_orderer must return each legal move exactly once")

    frames = 0
    requested = 0
    for rank, move in enumerate(moves, start=1):
        after = _after_move(board, move)
        audit = run_reply_quantifier(after, record_trace=False)
        requested += 1
        frames += int(audit["virtual_frame_count"])
        if audit["confirmed"]:
            return {
                "confirmed": True,
                "bound_move": move.uci(),
                "bound_move_rank": rank,
                "frames": frames,
                "requested_candidates": requested,
            }
    return {
        "confirmed": False,
        "bound_move": None,
        "bound_move_rank": None,
        "frames": frames,
        "requested_candidates": requested,
    }


def _write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl_gzip(path: str | Path, rows: Iterable[Mapping[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(output, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True) + "\n")


def _read_jsonl_gzip(path: str | Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def generate_chain_confidence_pool(
    *,
    seed: int,
    positive_count: int = 800,
    random_negative_count: int = 800,
    near_miss_count: int = 800,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Generate a self-distilled mate-in-2 gate pool in JSONL gzip format."""

    from .foundation_curriculum import (
        _forced_mate_in_two_first_moves,
        _generate_forced_mate_in_two_positions,
    )
    from .positions import generate_krk_board

    scorer = load_canonical_mate2_first_scorer()
    orderer_line = (
        "loaded canonical TG46c full-M3 mate2_first artifact "
        f"{scorer.source_path}; used graph_summary.top_mate2_first_terminals "
        f"exported rows, so {len(scorer.terminal_weights)}/{scorer.source_terminal_count} "
        "keys matched because the artifact stores top 10 positive and top 10 negative terminals"
    )

    rng = random.Random(seed)
    used: set[str] = set()
    source_fens: list[tuple[str, str]] = []

    positive_fens = _generate_forced_mate_in_two_positions(
        count=positive_count,
        seed=seed,
        excluded=used,
        max_attempts=max(1_000_000, positive_count * 20_000),
    )
    for fen in positive_fens:
        used.add(fen)
        source_fens.append(("mate2_positive_generator", fen))

    while sum(1 for source, _fen in source_fens if source == "random_non_mate2_generator") < random_negative_count:
        board = generate_krk_board(rng, weakness_zone=False, excluded_fens=used)
        if _forced_mate_in_two_first_moves(board):
            used.add(board.fen())
            continue
        fen = board.fen()
        used.add(fen)
        source_fens.append(("random_non_mate2_generator", fen))

    while sum(1 for source, _fen in source_fens if source == "weakness_near_miss_generator") < near_miss_count:
        board = generate_krk_board(rng, weakness_zone=True, excluded_fens=used)
        fen = board.fen()
        used.add(fen)
        source_fens.append(("weakness_near_miss_generator", fen))

    rows: list[dict[str, Any]] = []
    for index, (source, fen) in enumerate(source_fens):
        board = chess.Board(fen)
        features = chain_confidence_feature_record(board)
        internal = {
            "internal_mate_in_1_basin_confirms": features["internal_mate_in_1_basin_confirms"],
            "internal_fence_or_opposition_confirms": features["internal_fence_or_opposition_confirms"],
        }
        exact = _run_ordered_exact_mate_in_two(
            board,
            move_orderer=scorer.order_moves,
        )
        rows.append({
            "schema_version": CHAIN_CONFIDENCE_POOL_SCHEMA,
            "row_id": index,
            "seed": int(seed),
            "source": source,
            "fen": fen,
            "dieted_percepts": {
                key: value
                for key, value in sorted(features.items())
                if not key.startswith("internal_")
            },
            "internal_terminal_features": internal,
            "gate_features": features,
            "exact_mate_in_2_label": bool(exact["confirmed"]),
            "exact_bound_move": exact["bound_move"],
            "exact_bound_move_order_rank": exact["bound_move_rank"],
            "exact_ordered_frames": exact["frames"],
            "exact_ordered_requested_candidates": exact["requested_candidates"],
            "label_source": "ordered_exact_mate_in_2_skill_reply_quantifier",
        })

    path = Path(output_path) if output_path is not None else (
        CHAIN_CONFIDENCE_OUTPUT_DIR / "pools" / f"chain_confidence_pool_seed_{seed}.jsonl.gz"
    )
    _write_jsonl_gzip(path, rows)
    positives = sum(1 for row in rows if row["exact_mate_in_2_label"])
    summary = {
        "schema_version": "phase2_chain_confidence_pool_summary.v0",
        "seed": int(seed),
        "pool_path": str(path),
        "row_count": len(rows),
        "positive_label_count": positives,
        "negative_label_count": len(rows) - positives,
        "source_counts": {
            source: sum(1 for row in rows if row["source"] == source)
            for source in sorted({row["source"] for row in rows})
        },
        "orderer_line": orderer_line,
    }
    _write_json(path.with_suffix("").with_suffix(".summary.json"), summary)
    return summary


def _gate_base_features(raw: Mapping[str, float], stats: Mapping[str, Mapping[str, float]] | None) -> dict[str, float]:
    values: dict[str, float] = {}
    for key, value in sorted(raw.items()):
        numeric = float(value)
        if stats is not None:
            item = stats[key]
            numeric = (numeric - float(item["mean"])) / max(1e-9, float(item["std"]))
        values[f"raw:{key}"] = numeric
        values[f"bucket:{key}={int(round(float(value)))}"] = 1.0
    return values


def _feature_stats(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, float]]:
    keys = sorted(rows[0]["gate_features"])
    stats: dict[str, dict[str, float]] = {}
    for key in keys:
        values = [float(row["gate_features"][key]) for row in rows]
        avg = sum(values) / len(values)
        var = sum((value - avg) ** 2 for value in values) / len(values)
        stats[key] = {"mean": avg, "std": math.sqrt(var) if var > 1e-12 else 1.0}
    return stats


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def _score_gate_model(model: Mapping[str, Any], features: Mapping[str, float]) -> float:
    weights = model["weights"]
    values = _gate_base_features(features, model["feature_stats"])
    score = float(model["bias"])
    for key, value in values.items():
        score += float(weights.get(key, 0.0)) * value
    return _sigmoid(score)


def score_chain_confidence_gate(
    board: chess.Board,
    gate: Mapping[str, Any],
) -> dict[str, Any]:
    """Score the dispatcher gate on the current board."""

    features = chain_confidence_feature_record(board)
    score = _score_gate_model(gate["model"], features)
    threshold = float(gate["threshold"])
    return {
        "score": score,
        "threshold": threshold,
        "fired": score >= threshold,
        "features": features,
    }


def _policy_trace_message(
    messages: list[dict[str, Any]],
    src: str,
    dst: str,
    link_type: str,
    message: str,
    **meta: Any,
) -> None:
    row = {"src": src, "dst": dst, "link_type": link_type, "message": message}
    if meta:
        row["meta"] = meta
    messages.append(row)


def _policy_result(
    *,
    branch: str,
    bound_move: chess.Move | None,
    frames: int,
    gate_audit: Mapping[str, Any],
    trace_messages: list[dict[str, Any]],
    invocations: Mapping[str, Any],
    scorer: FrozenMate2FirstScorer,
) -> dict[str, Any]:
    fallback = invocations.get("fallback", {})
    return {
        "confirmed": bound_move is not None,
        "branch": branch,
        "bound_move": None if bound_move is None else bound_move.uci(),
        "virtual_frame_count": int(frames),
        "mate2_gate_fired": bool(gate_audit["fired"]),
        "mate2_gate_score": float(gate_audit["score"]),
        "mate2_gate_threshold": float(gate_audit["threshold"]),
        "fallback_repetition_guard_activated": bool(
            fallback.get("repetition_guard_activated", False)
        ),
        "fallback_repetition_guard_masked_count": int(
            fallback.get("repetition_guard_masked_count", 0)
        ),
        "fallback_repetition_guard_lifted": bool(
            fallback.get("repetition_guard_lifted", False)
        ),
        "invocations": dict(invocations),
        "scorer_source_path": str(scorer.source_path),
        "scorer_source_sha256": scorer.source_sha256,
        "trace": [{"tick": 0, "messages": trace_messages}],
    }


def _chase_result(
    *,
    confirmed: bool,
    branch: str,
    bound_move: chess.Move | None,
    reason: str,
    frames: int,
    messages: list[dict[str, Any]],
    gate_audit: Mapping[str, Any],
    rejected_moves: Sequence[Mapping[str, str]] | None = None,
) -> dict[str, Any]:
    _policy_trace_message(
        messages,
        CHASE_TO_MATE_SKILL_ID,
        CHASE_TO_MATE_SKILL_ROOT_ID,
        "SUR",
        "confirm" if confirmed else "fail",
        branch=branch,
        reason=reason,
    )
    return {
        "confirmed": bool(confirmed),
        "root_state": "CONFIRMED" if confirmed else "FAILED",
        "skill_state": "CONFIRMED" if confirmed else "FAILED",
        "branch": branch,
        "branch_fired": branch if confirmed else None,
        "bound_move": None if bound_move is None else bound_move.uci(),
        "failure_reason": None if confirmed else reason,
        "deferred_to_mate2": branch == "defer_mate2",
        "virtual_frame_count": int(frames),
        "mate2_gate_fired": bool(gate_audit["fired"]),
        "mate2_gate_score": float(gate_audit["score"]),
        "mate2_gate_threshold": float(gate_audit["threshold"]),
        "rejected_moves": [dict(item) for item in rejected_moves or ()],
        "trace": [{"tick": 0, "messages": messages}],
    }


def _chase_request_step(
    messages: list[dict[str, Any]],
    step_id: str,
) -> None:
    _policy_trace_message(
        messages,
        CHASE_TO_MATE_SKILL_ID,
        step_id,
        "SUB",
        "request",
    )


def _chase_step_result(
    messages: list[dict[str, Any]],
    step_id: str,
    *,
    confirmed: bool,
    reason: str,
    bound_move: chess.Move | None = None,
) -> None:
    meta: dict[str, Any] = {"reason": reason}
    if bound_move is not None:
        meta["bound_move"] = bound_move.uci()
    _policy_trace_message(
        messages,
        step_id,
        CHASE_TO_MATE_SKILL_ID,
        "SUR",
        "confirm" if confirmed else "fail",
        **meta,
    )


def _chase_continue(
    messages: list[dict[str, Any]],
    step_id: str,
    next_step_id: str,
) -> None:
    _policy_trace_message(
        messages,
        step_id,
        next_step_id,
        "POR",
        "inhibit_request",
    )


def run_chase_to_mate_skill(
    board: chess.Board,
    *,
    gate: Mapping[str, Any] | None = None,
    scorer: FrozenMate2FirstScorer | None = None,
    record_trace: bool = True,
    repetition_counts: Mapping[str, int] | None = None,
    mate2_cache: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run the hand-authored waypoint chase ceiling with one-ply verification only."""

    active_gate = load_chain_confidence_gate() if gate is None else gate
    active_scorer = load_canonical_mate2_first_scorer() if scorer is None else scorer
    active_counts = repetition_counts or {}
    active_cache = {} if mate2_cache is None else mate2_cache
    messages: list[dict[str, Any]] = []
    rejected_moves: list[dict[str, str]] = []
    if record_trace:
        _policy_trace_message(
            messages,
            CHASE_TO_MATE_SKILL_ROOT_ID,
            CHASE_TO_MATE_SKILL_ID,
            "SUB",
            "request",
        )
    gate_audit = score_chain_confidence_gate(board, active_gate)
    frames = 0
    if board.turn != chess.WHITE or board.is_game_over(claim_draw=False):
        return _chase_result(
            confirmed=False,
            branch="not_applicable",
            bound_move=None,
            reason="not_white_to_move_or_game_over",
            frames=frames,
            messages=messages,
            gate_audit=gate_audit,
        )
    if not _king_support_waypoint_geometry(board):
        return _chase_result(
            confirmed=False,
            branch="not_applicable",
            bound_move=None,
            reason="outside_waypoint_domain",
            frames=frames,
            messages=messages,
            gate_audit=gate_audit,
        )

    _chase_request_step(messages, CHASE_DEFER_MATE2_STEP_ID)
    if gate_audit["fired"]:
        mate2 = _edge_mate_exact_mate2_audit(
            board,
            scorer=active_scorer,
            cache=active_cache,
        )
        frames += int(mate2["frames"])
        if mate2["confirmed"]:
            _chase_step_result(
                messages,
                CHASE_DEFER_MATE2_STEP_ID,
                confirmed=True,
                reason="gated_mate2_confirmed_dispatcher_owns_move",
            )
            return _chase_result(
                confirmed=False,
                branch="defer_mate2",
                bound_move=None,
                reason="gated_mate2_confirmed_dispatcher_owns_move",
                frames=frames,
                messages=messages,
                gate_audit=gate_audit,
            )
        defer_reason = "mate2_gate_fired_but_exact_audit_failed"
    else:
        defer_reason = "mate2_gate_not_fired"
    _chase_step_result(
        messages,
        CHASE_DEFER_MATE2_STEP_ID,
        confirmed=False,
        reason=defer_reason,
    )
    _chase_continue(messages, CHASE_DEFER_MATE2_STEP_ID, CHASE_ROOK_ESCAPE_STEP_ID)

    _chase_request_step(messages, CHASE_ROOK_ESCAPE_STEP_ID)
    features = extract_learner_features(board)
    escape_exhausted = False
    if features["rook_attacked_by_black"] == 1.0:
        move = _resolve_chase_rook_escape(
            board,
            repetition_counts=active_counts,
            rejected_moves=rejected_moves,
        )
        if move is None:
            escape_exhausted = True
            _chase_step_result(
                messages,
                CHASE_ROOK_ESCAPE_STEP_ID,
                confirmed=False,
                reason="black_attacks_rook_no_safe_far_slide",
            )
            _chase_continue(messages, CHASE_ROOK_ESCAPE_STEP_ID, CHASE_KING_APPROACH_STEP_ID)
        else:
            _chase_step_result(
                messages,
                CHASE_ROOK_ESCAPE_STEP_ID,
                confirmed=True,
                reason="black_attacks_rook_far_slide_found",
                bound_move=move,
            )
            return _chase_result(
                confirmed=True,
                branch="rook_escape_slide",
                bound_move=move,
                reason="black_attacks_rook_far_slide_found",
                frames=frames,
                messages=messages,
                gate_audit=gate_audit,
                rejected_moves=rejected_moves,
            )
    else:
        _chase_step_result(
            messages,
            CHASE_ROOK_ESCAPE_STEP_ID,
            confirmed=False,
            reason="rook_not_attacked_by_black",
        )
        _chase_continue(messages, CHASE_ROOK_ESCAPE_STEP_ID, CHASE_KING_APPROACH_STEP_ID)

    _chase_request_step(messages, CHASE_KING_APPROACH_STEP_ID)
    if (
        escape_exhausted
        or (not _king_support_contact_geometry(board))
        or (not _chase_rook_safe(board))
    ):
        move = _resolve_chase_king_approach(
            board,
            repetition_counts=active_counts,
            rejected_moves=rejected_moves,
            allow_equal_contact=escape_exhausted,
        )
        if move is None:
            _chase_step_result(
                messages,
                CHASE_KING_APPROACH_STEP_ID,
                confirmed=False,
                reason="no_safe_king_approach_progress",
            )
        else:
            _chase_step_result(
                messages,
                CHASE_KING_APPROACH_STEP_ID,
                confirmed=True,
                reason="king_support_or_rook_safety_progress",
                bound_move=move,
            )
            return _chase_result(
                confirmed=True,
                branch="king_approach",
                bound_move=move,
                reason="king_support_or_rook_safety_progress",
                frames=frames,
                messages=messages,
                gate_audit=gate_audit,
                rejected_moves=rejected_moves,
            )
    else:
        _chase_step_result(
            messages,
            CHASE_KING_APPROACH_STEP_ID,
            confirmed=False,
            reason="support_contact_already_achieved",
        )
    _chase_continue(messages, CHASE_KING_APPROACH_STEP_ID, CHASE_ROOK_TEMPO_STEP_ID)

    _chase_request_step(messages, CHASE_ROOK_TEMPO_STEP_ID)
    if not _king_support_contact_geometry(board):
        _chase_step_result(
            messages,
            CHASE_ROOK_TEMPO_STEP_ID,
            confirmed=False,
            reason="support_contact_not_achieved",
        )
        return _chase_result(
            confirmed=False,
            branch="rook_waiting_tempo",
            bound_move=None,
            reason="support_contact_not_achieved",
            frames=frames,
            messages=messages,
            gate_audit=gate_audit,
            rejected_moves=rejected_moves,
        )
    move = _resolve_chase_rook_tempo(
        board,
        repetition_counts=active_counts,
        rejected_moves=rejected_moves,
    )
    if move is None:
        _chase_step_result(
            messages,
            CHASE_ROOK_TEMPO_STEP_ID,
            confirmed=False,
            reason="no_safe_rook_waiting_slide",
        )
        return _chase_result(
            confirmed=False,
            branch="rook_waiting_tempo",
            bound_move=None,
            reason="no_safe_rook_waiting_slide",
            frames=frames,
            messages=messages,
            gate_audit=gate_audit,
            rejected_moves=rejected_moves,
        )
    _chase_step_result(
        messages,
        CHASE_ROOK_TEMPO_STEP_ID,
        confirmed=True,
        reason="support_contact_rook_waiting_slide",
        bound_move=move,
    )
    return _chase_result(
        confirmed=True,
        branch="rook_waiting_tempo",
        bound_move=move,
        reason="support_contact_rook_waiting_slide",
        frames=frames,
        messages=messages,
        gate_audit=gate_audit,
        rejected_moves=rejected_moves,
    )


def run_krk_policy(
    board: chess.Board,
    *,
    gate: Mapping[str, Any] | None = None,
    scorer: FrozenMate2FirstScorer | None = None,
    record_trace: bool = False,
    repetition_counts: Mapping[str, int] | None = None,
    mate2_cache: dict[str, dict[str, Any]] | None = None,
    enter_cache: dict[str, dict[str, Any]] | None = None,
    enable_chase: bool = False,
) -> dict[str, Any]:
    """Run the Phase 2.7 priority dispatcher over existing graph-native skills."""

    if board.turn != chess.WHITE or board.is_game_over(claim_draw=False):
        return {
            "confirmed": False,
            "branch": "not_applicable",
            "bound_move": None,
            "virtual_frame_count": 0,
            "mate2_gate_fired": False,
            "mate2_gate_score": 0.0,
            "mate2_gate_threshold": 0.0,
            "fallback_repetition_guard_activated": False,
            "fallback_repetition_guard_masked_count": 0,
            "fallback_repetition_guard_lifted": False,
            "invocations": {},
            "scorer_source_path": None,
            "scorer_source_sha256": None,
            "trace": [{"tick": 0, "messages": []}],
        }

    active_gate = load_chain_confidence_gate() if gate is None else gate
    active_scorer = load_canonical_mate2_first_scorer() if scorer is None else scorer
    trace_messages: list[dict[str, Any]] = []
    invocations: dict[str, Any] = {}
    frames = 0
    gate_audit: dict[str, Any] = {
        "fired": False,
        "score": 0.0,
        "threshold": float(active_gate["threshold"]),
    }

    _policy_trace_message(
        trace_messages,
        KRK_POLICY_ROOT_ID,
        MATE_IN_ONE_BASIN_ID,
        "SUB",
        "request",
    )
    basin = run_mate_in_one_basin_recognizer(board, record_trace=record_trace)
    invocations["mate_in_1_basin"] = {"confirmed": bool(basin["confirmed"])}
    _policy_trace_message(
        trace_messages,
        MATE_IN_ONE_BASIN_ID,
        KRK_POLICY_ROOT_ID,
        "SUR",
        "confirm" if basin["confirmed"] else "fail",
    )
    if basin["confirmed"]:
        _policy_trace_message(
            trace_messages,
            KRK_POLICY_ROOT_ID,
            MATE_IN_ONE_SKILL_ID,
            "SUB",
            "request",
        )
        mate1 = run_mate_in_one_skill(board, record_trace=record_trace)
        invocations["mate_in_1_skill"] = {
            "confirmed": bool(mate1["confirmed"]),
            "bound_move": mate1["bound_move"],
        }
        _policy_trace_message(
            trace_messages,
            MATE_IN_ONE_SKILL_ID,
            KRK_POLICY_ROOT_ID,
            "SUR",
            "confirm" if mate1["confirmed"] else "fail",
        )
        if mate1["confirmed"] and mate1["bound_move"] is not None:
            return _policy_result(
                branch="mate_in_1",
                bound_move=chess.Move.from_uci(mate1["bound_move"]),
                frames=frames,
                gate_audit=gate_audit,
                trace_messages=trace_messages,
                invocations=invocations,
                scorer=active_scorer,
            )

    _policy_trace_message(
        trace_messages,
        KRK_POLICY_ROOT_ID,
        MATE_IN_TWO_GATE_ID,
        "SUB",
        "request",
    )
    gate_audit = score_chain_confidence_gate(board, active_gate)
    _policy_trace_message(
        trace_messages,
        MATE_IN_TWO_GATE_ID,
        KRK_POLICY_ROOT_ID,
        "SUR",
        "confirm" if gate_audit["fired"] else "fail",
        score=round(float(gate_audit["score"]), 6),
        threshold=round(float(gate_audit["threshold"]), 6),
    )
    invocations["mate2_gate"] = {
        "fired": bool(gate_audit["fired"]),
        "score": float(gate_audit["score"]),
        "threshold": float(gate_audit["threshold"]),
    }

    if gate_audit["fired"]:
        _policy_trace_message(
            trace_messages,
            KRK_POLICY_ROOT_ID,
            MATE_IN_TWO_SKILL_ID,
            "SUB",
            "request",
        )
        if mate2_cache is None:
            mate2 = run_mate_in_two_skill(
                board,
                record_trace=record_trace,
                move_orderer=active_scorer.order_moves,
            )
            mate2_frames = int(mate2["virtual_frame_count"])
            mate2_rank = mate2["bound_move_rank"]
        else:
            mate2 = _edge_mate_exact_mate2_audit(
                board,
                scorer=active_scorer,
                cache=mate2_cache,
            )
            mate2_frames = int(mate2["frames"])
            mate2_rank = None
        frames += mate2_frames
        invocations["mate_in_2_skill"] = {
            "confirmed": bool(mate2["confirmed"]),
            "bound_move": mate2["bound_move"],
            "virtual_frame_count": mate2_frames,
            "bound_move_rank": mate2_rank,
        }
        _policy_trace_message(
            trace_messages,
            MATE_IN_TWO_SKILL_ID,
            KRK_POLICY_ROOT_ID,
            "SUR",
            "confirm" if mate2["confirmed"] else "fail",
        )
        if mate2["confirmed"] and mate2["bound_move"] is not None:
            return _policy_result(
                branch="mate_in_2",
                bound_move=chess.Move.from_uci(mate2["bound_move"]),
                frames=frames,
                gate_audit=gate_audit,
                trace_messages=trace_messages,
                invocations=invocations,
                scorer=active_scorer,
            )

    _policy_trace_message(
        trace_messages,
        KRK_POLICY_ROOT_ID,
        ENTER_MATE_TWO_SKILL_ID,
        "SUB",
        "request",
    )
    if enter_cache is None:
        enter_mate2 = run_enter_mate2_skill(
            board,
            scorer=active_scorer,
            mate2_cache=mate2_cache,
            record_trace=record_trace,
        )
        enter_frames = int(enter_mate2["virtual_frame_count"])
        enter_rank = enter_mate2["bound_move_rank"]
    else:
        if mate2_cache is None:
            mate2_cache = {}
        enter_mate2 = _edge_mate_enter_mate2_audit(
            board,
            scorer=active_scorer,
            mate2_cache=mate2_cache,
            enter_cache=enter_cache,
        )
        enter_frames = int(enter_mate2["frames"])
        enter_rank = None
    frames += enter_frames
    invocations["enter_mate2_skill"] = {
        "confirmed": bool(enter_mate2["confirmed"]),
        "bound_move": enter_mate2["bound_move"],
        "failed_reply": enter_mate2["failed_reply"],
        "all_reply_count": int(enter_mate2["all_reply_count"]),
        "confirmed_reply_count": int(enter_mate2["confirmed_reply_count"]),
        "virtual_frame_count": enter_frames,
        "bound_move_rank": enter_rank,
        "successor_check_count": int(enter_mate2["successor_check_count"]),
    }
    _policy_trace_message(
        trace_messages,
        ENTER_MATE_TWO_SKILL_ID,
        KRK_POLICY_ROOT_ID,
        "SUR",
        "confirm" if enter_mate2["confirmed"] else "fail",
    )
    if enter_mate2["confirmed"] and enter_mate2["bound_move"] is not None:
        return _policy_result(
            branch="enter_mate2",
            bound_move=chess.Move.from_uci(enter_mate2["bound_move"]),
            frames=frames,
            gate_audit=gate_audit,
            trace_messages=trace_messages,
            invocations=invocations,
            scorer=active_scorer,
        )

    if enable_chase:
        _policy_trace_message(
            trace_messages,
            KRK_POLICY_ROOT_ID,
            CHASE_TO_MATE_SKILL_ID,
            "SUB",
            "request",
        )
        chase = run_chase_to_mate_skill(
            board,
            gate=active_gate,
            scorer=active_scorer,
            record_trace=record_trace,
            repetition_counts=repetition_counts,
            mate2_cache=mate2_cache,
        )
        frames += int(chase["virtual_frame_count"])
        invocations["chase_to_mate_skill"] = {
            "confirmed": bool(chase["confirmed"]),
            "bound_move": chase["bound_move"],
            "branch": chase["branch"],
            "branch_fired": chase["branch_fired"],
            "failure_reason": chase["failure_reason"],
            "virtual_frame_count": int(chase["virtual_frame_count"]),
        }
        _policy_trace_message(
            trace_messages,
            CHASE_TO_MATE_SKILL_ID,
            KRK_POLICY_ROOT_ID,
            "SUR",
            "confirm" if chase["confirmed"] else "fail",
            branch=chase["branch"],
            reason=chase["failure_reason"] or "confirmed",
        )
        if chase["confirmed"] and chase["bound_move"] is not None:
            return _policy_result(
                branch="chase_to_mate",
                bound_move=chess.Move.from_uci(chase["bound_move"]),
                frames=frames,
                gate_audit=gate_audit,
                trace_messages=trace_messages,
                invocations=invocations,
                scorer=active_scorer,
            )

    _policy_trace_message(
        trace_messages,
        KRK_POLICY_ROOT_ID,
        FENCE_ESTABLISHED_ID,
        "SUB",
        "request",
    )
    fence = run_fence_established_recognizer(board, record_trace=record_trace)
    invocations["fence_established"] = {"confirmed": bool(fence["confirmed"])}
    _policy_trace_message(
        trace_messages,
        FENCE_ESTABLISHED_ID,
        KRK_POLICY_ROOT_ID,
        "SUR",
        "confirm" if fence["confirmed"] else "fail",
    )
    if not fence["confirmed"]:
        _policy_trace_message(
            trace_messages,
            KRK_POLICY_ROOT_ID,
            ESTABLISH_FENCE_SKILL_ID,
            "SUB",
            "request",
        )
        establish = run_establish_fence_skill(board, record_trace=record_trace)
        frames += int(establish["virtual_frame_count"])
        invocations["establish_fence_skill"] = {
            "confirmed": bool(establish["confirmed"]),
            "bound_move": establish["bound_move"],
            "virtual_frame_count": int(establish["virtual_frame_count"]),
            "bound_move_rank": establish["bound_move_rank"],
        }
        _policy_trace_message(
            trace_messages,
            ESTABLISH_FENCE_SKILL_ID,
            KRK_POLICY_ROOT_ID,
            "SUR",
            "confirm" if establish["confirmed"] else "fail",
        )
        if establish["confirmed"] and establish["bound_move"] is not None:
            return _policy_result(
                branch="establish_fence",
                bound_move=chess.Move.from_uci(establish["bound_move"]),
                frames=frames,
                gate_audit=gate_audit,
                trace_messages=trace_messages,
                invocations=invocations,
                scorer=active_scorer,
            )

    legal_moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    ordered = active_scorer.order_moves(board, legal_moves)
    active_counts = repetition_counts or {}
    allowed = tuple(
        move for move in ordered
        if int(active_counts.get(_after_move_repetition_key(board, move), 0)) < 2
    )
    guard_activated = len(allowed) < len(ordered)
    guard_lifted = guard_activated and not allowed
    if allowed:
        ordered = allowed
    fallback = ordered[0] if ordered else None
    invocations["fallback"] = {
        "confirmed": fallback is not None,
        "bound_move": None if fallback is None else fallback.uci(),
        "score": 0.0 if fallback is None else active_scorer.score_move(board, fallback),
        "repetition_guard_activated": guard_activated,
        "repetition_guard_masked_count": len(legal_moves) - len(allowed),
        "repetition_guard_lifted": guard_lifted,
    }
    _policy_trace_message(
        trace_messages,
        KRK_POLICY_ROOT_ID,
        CANONICAL_DIETED_FALLBACK_ID,
        "SUB",
        "request",
    )
    _policy_trace_message(
        trace_messages,
        CANONICAL_DIETED_FALLBACK_ID,
        KRK_POLICY_ROOT_ID,
        "SUR",
        "confirm" if fallback is not None else "fail",
    )
    return _policy_result(
        branch="fallback",
        bound_move=fallback,
        frames=frames,
        gate_audit=gate_audit,
        trace_messages=trace_messages,
        invocations=invocations,
        scorer=active_scorer,
    )


def _threshold_metrics(scores: Sequence[float], labels: Sequence[bool], threshold: float) -> dict[str, float | int]:
    tp = sum(score >= threshold and label for score, label in zip(scores, labels))
    fp = sum(score >= threshold and not label for score, label in zip(scores, labels))
    fn = sum(score < threshold and label for score, label in zip(scores, labels))
    tn = sum(score < threshold and not label for score, label in zip(scores, labels))
    precision = 0.0 if tp + fp == 0 else tp / (tp + fp)
    recall = 0.0 if tp + fn == 0 else tp / (tp + fn)
    f1 = 0.0 if precision + recall == 0.0 else 2.0 * precision * recall / (precision + recall)
    return {
        "threshold": float(threshold),
        "true_positive": int(tp),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_negative": int(tn),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _choose_gate_thresholds(scores: Sequence[float], labels: Sequence[bool]) -> dict[str, float]:
    score_tuple = tuple(scores)
    positive_scores = [score for score, label in zip(scores, labels) if label]
    if not positive_scores:
        raise ValueError("chain-confidence training requires positive examples")
    candidates = sorted(set(score_tuple + tuple(score - 1e-12 for score in score_tuple)))
    recall_favoring = 0.0
    metrics = [_threshold_metrics(scores, labels, threshold) for threshold in candidates]
    balanced = max(metrics, key=lambda item: (item["f1"], item["recall"], item["precision"]))["threshold"]
    recall_safe = [item for item in metrics if item["recall"] >= 0.90]
    precision_favoring = max(
        recall_safe or metrics,
        key=lambda item: (item["precision"], item["recall"], item["threshold"]),
    )["threshold"]
    return {
        "recall_favoring": float(recall_favoring),
        "balanced": float(balanced),
        "precision_favoring": float(precision_favoring),
    }


def _stratified_split(
    rows: Sequence[dict[str, Any]],
    *,
    seed: int,
    heldout_fraction: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    positives = [row for row in rows if row["exact_mate_in_2_label"]]
    negatives = [row for row in rows if not row["exact_mate_in_2_label"]]
    rng.shuffle(positives)
    rng.shuffle(negatives)
    pos_heldout = max(1, int(round(len(positives) * heldout_fraction)))
    neg_heldout = max(1, int(round(len(negatives) * heldout_fraction)))
    heldout = positives[:pos_heldout] + negatives[:neg_heldout]
    train = positives[pos_heldout:] + negatives[neg_heldout:]
    rng.shuffle(train)
    rng.shuffle(heldout)
    return train, heldout


def train_chain_confidence_gate(
    rows: Sequence[dict[str, Any]],
    *,
    seed: int,
    heldout_fraction: float = 0.25,
    epochs: int = 80,
    learning_rate: float = 0.04,
    l2: float = 0.0005,
) -> dict[str, Any]:
    """Train a weighted-threshold gate over percept/internal features."""

    train_rows, heldout_rows = _stratified_split(
        list(rows),
        seed=seed,
        heldout_fraction=heldout_fraction,
    )
    stats = _feature_stats(train_rows)
    weights: dict[str, float] = {}
    bias = 0.0
    rng = random.Random(seed)
    pos_count = sum(1 for row in train_rows if row["exact_mate_in_2_label"])
    neg_count = len(train_rows) - pos_count
    pos_weight = len(train_rows) / max(1.0, 2.0 * pos_count)
    neg_weight = len(train_rows) / max(1.0, 2.0 * neg_count)

    for epoch in range(epochs):
        rng.shuffle(train_rows)
        lr = learning_rate / math.sqrt(epoch + 1.0)
        for row in train_rows:
            label = 1.0 if row["exact_mate_in_2_label"] else 0.0
            values = _gate_base_features(row["gate_features"], stats)
            linear = bias + sum(weights.get(key, 0.0) * value for key, value in values.items())
            pred = _sigmoid(linear)
            class_weight = pos_weight if label > 0.5 else neg_weight
            err = (pred - label) * class_weight
            bias -= lr * err
            for key, value in values.items():
                current = weights.get(key, 0.0)
                weights[key] = current - lr * (err * value + l2 * current)
        if not math.isfinite(bias) or any(not math.isfinite(value) for value in weights.values()):
            raise ValueError("chain-confidence training diverged")

    model: dict[str, Any] = {
        "schema_version": CHAIN_CONFIDENCE_MODEL_SCHEMA,
        "seed": int(seed),
        "model_type": "weighted_threshold_logistic",
        "bias": bias,
        "weights": dict(sorted(weights.items())),
        "feature_stats": stats,
        "train_count": len(train_rows),
        "heldout_count": len(heldout_rows),
        "train_positive_count": pos_count,
        "train_negative_count": neg_count,
        "heldout_positive_count": sum(1 for row in heldout_rows if row["exact_mate_in_2_label"]),
        "heldout_negative_count": sum(1 for row in heldout_rows if not row["exact_mate_in_2_label"]),
    }
    train_scores = [_score_gate_model(model, row["gate_features"]) for row in train_rows]
    train_labels = [bool(row["exact_mate_in_2_label"]) for row in train_rows]
    model["thresholds"] = _choose_gate_thresholds(tuple(train_scores), tuple(train_labels))
    model["train_threshold_metrics"] = {
        name: _threshold_metrics(tuple(train_scores), tuple(train_labels), threshold)
        for name, threshold in model["thresholds"].items()
    }
    model["heldout_row_ids"] = [int(row["row_id"]) for row in heldout_rows]
    model["train_row_ids"] = [int(row["row_id"]) for row in train_rows]
    return model


def evaluate_chain_confidence_gate(
    rows: Sequence[dict[str, Any]],
    *,
    model: Mapping[str, Any],
) -> dict[str, Any]:
    labels = [bool(row["exact_mate_in_2_label"]) for row in rows]
    scores = [_score_gate_model(model, row["gate_features"]) for row in rows]
    positives = [row for row in rows if row["exact_mate_in_2_label"]]
    negatives = [row for row in rows if not row["exact_mate_in_2_label"]]
    baseline_positive_frames = [int(row["exact_ordered_frames"]) for row in positives]
    baseline_negative_frames = [int(row["exact_ordered_frames"]) for row in negatives]

    threshold_rows: dict[str, Any] = {}
    for name, threshold in model["thresholds"].items():
        metrics = _threshold_metrics(tuple(scores), tuple(labels), float(threshold))
        positive_frames: list[int] = []
        negative_frames: list[int] = []
        for row, score in zip(rows, scores):
            frames = int(row["exact_ordered_frames"]) if score >= float(threshold) else 0
            if row["exact_mate_in_2_label"]:
                positive_frames.append(frames)
            else:
                negative_frames.append(frames)
        threshold_rows[name] = {
            **metrics,
            "end_to_end_conversion": metrics["recall"],
            "positive_frames_mean": 0.0 if not positive_frames else sum(positive_frames) / len(positive_frames),
            "positive_frames_max": max(positive_frames) if positive_frames else 0,
            "negative_frames_mean": 0.0 if not negative_frames else sum(negative_frames) / len(negative_frames),
            "negative_frames_max": max(negative_frames) if negative_frames else 0,
        }

    return {
        "row_count": len(rows),
        "positive_count": len(positives),
        "negative_count": len(negatives),
        "baseline_ordered_positive_frames_mean": (
            0.0 if not baseline_positive_frames else sum(baseline_positive_frames) / len(baseline_positive_frames)
        ),
        "baseline_ordered_positive_frames_max": max(baseline_positive_frames) if baseline_positive_frames else 0,
        "baseline_ordered_negative_frames_mean": (
            0.0 if not baseline_negative_frames else sum(baseline_negative_frames) / len(baseline_negative_frames)
        ),
        "baseline_ordered_negative_frames_max": max(baseline_negative_frames) if baseline_negative_frames else 0,
        "thresholds": threshold_rows,
    }


def run_chain_confidence_training(
    *,
    pool_seed: int = 20261201,
    train_seeds: Sequence[int] = (20261211, 20261212, 20261213),
    output_dir: str | Path = CHAIN_CONFIDENCE_OUTPUT_DIR,
    regenerate_pool: bool = False,
    positive_count: int = 800,
    random_negative_count: int = 800,
    near_miss_count: int = 800,
) -> dict[str, Any]:
    """Generate/load the Phase 2.5 pool, train 3 gate seeds, and write artifacts."""

    base = Path(output_dir)
    pool_path = base / "pools" / f"chain_confidence_pool_seed_{pool_seed}.jsonl.gz"
    if regenerate_pool or not pool_path.exists():
        pool_summary = generate_chain_confidence_pool(
            seed=pool_seed,
            positive_count=positive_count,
            random_negative_count=random_negative_count,
            near_miss_count=near_miss_count,
            output_path=pool_path,
        )
    else:
        pool_summary = json.loads(pool_path.with_suffix("").with_suffix(".summary.json").read_text(encoding="utf-8"))
    rows = _read_jsonl_gzip(pool_path)

    seed_results: dict[str, Any] = {}
    for seed in train_seeds:
        model = train_chain_confidence_gate(rows, seed=int(seed))
        heldout = [row for row in rows if int(row["row_id"]) in set(model["heldout_row_ids"])]
        eval_result = evaluate_chain_confidence_gate(heldout, model=model)
        payload = {
            "schema_version": "phase2_chain_confidence_gate_result.v0",
            "seed": int(seed),
            "pool_path": str(pool_path),
            "model": model,
            "heldout_eval": eval_result,
        }
        model_path = base / f"chain_confidence_gate_seed_{seed}.json"
        _write_json(model_path, payload)
        heldout_ids = set(model["heldout_row_ids"])
        seed_results[str(seed)] = {
            "artifact_path": str(model_path),
            "heldout_eval": eval_result,
            "thresholds": model["thresholds"],
            "heldout_row_count": len(heldout_ids),
        }

    summary = {
        "schema_version": "phase2_chain_confidence_summary.v0",
        "pool": pool_summary,
        "train_seeds": [int(seed) for seed in train_seeds],
        "seed_results": seed_results,
    }
    _write_json(base / "chain_confidence_summary.json", summary)
    return summary


PHASE28_EDGE_MATE_OUTPUT_DIR = Path(
    "reports/autogrowth/clean_slate_krk/phase2_edge_mate_v1"
)
EDGE_MATE_POOL_SCHEMA = "phase2_edge_mate_pool_row.v0"
EDGE_MATE_RESULT_SCHEMA = "phase2_edge_mate_distance1_training.v0"


@dataclass(frozen=True)
class EdgeMateDistanceTrainingConfig:
    seed: int = 20270201
    output_dir: str = str(PHASE28_EDGE_MATE_OUTPUT_DIR)
    distance1_train_count: int = 300
    distance1_heldout_count: int = 96
    distance2_to5_count: int = 300
    train_seeds: tuple[int, ...] = (20270211, 20270212, 20270213)
    max_generation_attempts: int = 1_500_000
    max_selfplay_games: int = 800
    max_game_plies: int = 110
    max_white_moves_per_episode: int = 2
    eta_m3: float = 0.10
    rich_feature_credit_scale: float = 0.25
    gamma: float = 0.90
    epsilon: float = 0.15
    promotion_abs_weight_threshold: float = 0.05
    promotion_min_credit_events: int = 3


def _edge_mate_edge_distance(square: int | None) -> int:
    if square is None:
        return 8
    return min(
        chess.square_file(square),
        7 - chess.square_file(square),
        chess.square_rank(square),
        7 - chess.square_rank(square),
    )


def _edge_mate_board_from_random_fence_start(rng: random.Random) -> chess.Board | None:
    from .foundation_curriculum import _random_krk_board, _valid_foundation_board

    board = _random_krk_board(rng)
    if not _valid_foundation_board(board):
        return None
    if _edge_mate_edge_distance(board.king(chess.BLACK)) != 0:
        return None
    if not fence_established_geometry(board):
        return None
    return board


def _edge_mate_fixed_seed_black_reply(board: chess.Board, rng: random.Random) -> chess.Move | None:
    if board.turn != chess.BLACK or board.is_game_over(claim_draw=False):
        return None
    replies = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    if not replies:
        return None
    return replies[rng.randrange(len(replies))]


def _edge_mate_internal_terminal_keys(
    board: chess.Board,
    *,
    gate: Mapping[str, Any],
) -> list[str]:
    fence = run_fence_established_recognizer(board, record_trace=False)["confirmed"]
    basin = run_mate_in_one_basin_recognizer(board, record_trace=False)["confirmed"]
    gate_audit = score_chain_confidence_gate(board, gate)
    score = max(0.0, min(1.0, float(gate_audit["score"])))
    decile = min(9, int(score * 10.0))
    return [
        f"internal:fence_established_confirms={int(bool(fence))}",
        f"internal:mate_in_1_basin_confirms={int(bool(basin))}",
        f"internal:mate2_gate_fires={int(bool(gate_audit['fired']))}",
        f"internal:mate2_gate_score_decile={decile}",
    ]


def _edge_mate_terminal_keys(
    board: chess.Board,
    move: chess.Move,
    *,
    gate: Mapping[str, Any] | None = None,
    include_internal: bool = False,
) -> list[str]:
    base = [key for key, _scale in terminal_action_feature_keys(board, move)]
    if not include_internal:
        return base
    if gate is None:
        raise ValueError("gate is required when include_internal=True")
    internal = _edge_mate_internal_terminal_keys(board, gate=gate)
    composed = [
        f"{internal_key}|{base_key}"
        for internal_key in internal
        for base_key in base
    ]
    return base + internal + composed


def _edge_mate_exact_mate2_audit(
    board: chess.Board,
    *,
    scorer: FrozenMate2FirstScorer,
    cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    cache_key = _position_repetition_key(board)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    if board.turn != chess.WHITE or board.is_game_over(claim_draw=False):
        audit = {
            "confirmed": False,
            "bound_move": None,
            "frames": 0,
            "requested_candidate_count": 0,
        }
    else:
        from .foundation_curriculum import _forced_mate_in_two_first_moves

        forced = _forced_mate_in_two_first_moves(board)
        if not forced:
            audit = {
                "confirmed": False,
                "bound_move": None,
                "frames": 0,
                "requested_candidate_count": 0,
            }
        else:
            exact = _run_ordered_exact_mate_in_two(
                board,
                move_orderer=scorer.order_moves,
            )
            audit = {
                "confirmed": bool(exact["confirmed"]),
                "bound_move": exact["bound_move"],
                "frames": int(exact["frames"]),
                "requested_candidate_count": int(exact["requested_candidates"]),
            }
    cache[cache_key] = audit
    return audit


def run_enter_mate2_skill(
    board: chess.Board,
    *,
    scorer: FrozenMate2FirstScorer | None = None,
    mate2_cache: dict[str, dict[str, Any]] | None = None,
    record_trace: bool = True,
) -> dict[str, Any]:
    """Execute the exact distance-1 closure into the certified mate-in-2 manifold."""

    active_scorer = load_canonical_mate2_first_scorer() if scorer is None else scorer
    active_cache = {} if mate2_cache is None else mate2_cache
    messages: list[dict[str, Any]] = []
    if record_trace:
        _policy_trace_message(
            messages,
            ENTER_MATE_TWO_SKILL_ROOT_ID,
            ENTER_MATE_TWO_SKILL_ID,
            "SUB",
            "request",
        )

    if board.turn != chess.WHITE or board.is_game_over(claim_draw=False):
        if record_trace:
            _policy_trace_message(
                messages,
                ENTER_MATE_TWO_SKILL_ID,
                ENTER_MATE_TWO_SKILL_ROOT_ID,
                "SUR",
                "fail",
                reason="not_white_to_move_or_game_over",
            )
        return {
            "confirmed": False,
            "root_state": "FAILED",
            "skill_state": "FAILED",
            "bound_move": None,
            "failed_reply": None,
            "all_reply_count": 0,
            "confirmed_reply_count": 0,
            "candidate_count": 0,
            "requested_candidate_count": 0,
            "successor_check_count": 0,
            "virtual_frame_count": 0,
            "expanded_virtual_frame_count": 0,
            "bound_move_rank": None,
            "trace": [{"tick": 0, "messages": messages}],
        }

    features = extract_learner_features(board)
    if (
        features["black_king_nearest_edge_distance"] != 0.0
        or not fence_established_geometry(board)
    ):
        if record_trace:
            _policy_trace_message(
                messages,
                ENTER_MATE_TWO_SKILL_ID,
                ENTER_MATE_TWO_SKILL_ROOT_ID,
                "SUR",
                "fail",
                reason="outside_edge_mate_distance1_domain",
            )
        return {
            "confirmed": False,
            "root_state": "FAILED",
            "skill_state": "FAILED",
            "bound_move": None,
            "failed_reply": None,
            "all_reply_count": 0,
            "confirmed_reply_count": 0,
            "candidate_count": 0,
            "requested_candidate_count": 0,
            "successor_check_count": 0,
            "virtual_frame_count": 0,
            "expanded_virtual_frame_count": 0,
            "bound_move_rank": None,
            "trace": [{"tick": 0, "messages": messages}],
        }

    legal_moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    ordered = active_scorer.order_moves(board, legal_moves)
    legal_uci = {move.uci() for move in legal_moves}
    if len(ordered) != len(legal_moves) or {move.uci() for move in ordered} != legal_uci:
        raise ValueError("scorer.order_moves must return each legal move exactly once")

    frames = 0
    successor_checks = 0
    for rank, move in enumerate(ordered, start=1):
        if record_trace:
            _policy_trace_message(
                messages,
                ENTER_MATE_TWO_SKILL_ID,
                f"{ENTER_MATE_TWO_SKILL_ID}:{move.uci()}",
                "SUB",
                "request",
            )
        after_white = _after_move(board, move)
        if _white_rook_square(after_white) is None:
            if record_trace:
                _policy_trace_message(
                    messages,
                    f"{ENTER_MATE_TWO_SKILL_ID}:{move.uci()}",
                    ENTER_MATE_TWO_SKILL_ID,
                    "SUR",
                    "fail",
                    reason="rook_lost",
                )
            continue
        if after_white.legal_moves.count() == 0:
            if after_white.is_check():
                if record_trace:
                    _policy_trace_message(
                        messages,
                        f"{ENTER_MATE_TWO_SKILL_ID}:{move.uci()}",
                        ENTER_MATE_TWO_SKILL_ID,
                        "SUR",
                        "confirm",
                        reason="immediate_mate",
                    )
                    _policy_trace_message(
                        messages,
                        ENTER_MATE_TWO_SKILL_ID,
                        ENTER_MATE_TWO_SKILL_ROOT_ID,
                        "SUR",
                        "confirm",
                    )
                return {
                    "confirmed": True,
                    "root_state": "CONFIRMED",
                    "skill_state": "CONFIRMED",
                    "bound_move": move.uci(),
                    "failed_reply": None,
                    "all_reply_count": 0,
                    "confirmed_reply_count": 0,
                    "candidate_count": len(legal_moves),
                    "requested_candidate_count": rank,
                    "successor_check_count": successor_checks,
                    "virtual_frame_count": frames,
                    "expanded_virtual_frame_count": frames,
                    "bound_move_rank": rank,
                    "trace": [{"tick": 0, "messages": messages}],
                }
            if record_trace:
                _policy_trace_message(
                    messages,
                    f"{ENTER_MATE_TWO_SKILL_ID}:{move.uci()}",
                    ENTER_MATE_TWO_SKILL_ID,
                    "SUR",
                    "fail",
                    reason="zero_reply_stalemate",
                )
            continue

        candidate_failed_reply: str | None = None
        confirmed_replies = 0
        replies = tuple(sorted(after_white.legal_moves, key=lambda item: item.uci()))
        for reply in sorted(after_white.legal_moves, key=lambda item: item.uci()):
            successor = _after_move(after_white, reply)
            successor_checks += 1
            if _white_rook_square(successor) is None:
                candidate_failed_reply = reply.uci()
                if record_trace:
                    _policy_trace_message(
                        messages,
                        f"{ENTER_MATE_TWO_SKILL_ID}:{move.uci()}",
                        ENTER_MATE_TWO_SKILL_ID,
                        "SUR",
                        "fail",
                        reply=reply.uci(),
                        reason="reply_captures_rook",
                    )
                break
            if successor.is_stalemate():
                candidate_failed_reply = reply.uci()
                if record_trace:
                    _policy_trace_message(
                        messages,
                        f"{ENTER_MATE_TWO_SKILL_ID}:{move.uci()}",
                        ENTER_MATE_TWO_SKILL_ID,
                        "SUR",
                        "fail",
                        reply=reply.uci(),
                        reason="reply_forces_stalemate",
                    )
                break
            audit = _edge_mate_exact_mate2_audit(
                successor,
                scorer=active_scorer,
                cache=active_cache,
            )
            frames += int(audit["frames"])
            if not audit["confirmed"]:
                candidate_failed_reply = reply.uci()
                if record_trace:
                    _policy_trace_message(
                        messages,
                        f"{ENTER_MATE_TWO_SKILL_ID}:{move.uci()}",
                        ENTER_MATE_TWO_SKILL_ID,
                        "SUR",
                        "fail",
                        reply=reply.uci(),
                        reason="successor_not_exact_mate2",
                    )
                break
            confirmed_replies += 1
        if candidate_failed_reply is None:
            if record_trace:
                _policy_trace_message(
                    messages,
                    f"{ENTER_MATE_TWO_SKILL_ID}:{move.uci()}",
                    ENTER_MATE_TWO_SKILL_ID,
                    "SUR",
                    "confirm",
                    all_reply_count=len(replies),
                )
                _policy_trace_message(
                    messages,
                    ENTER_MATE_TWO_SKILL_ID,
                    ENTER_MATE_TWO_SKILL_ROOT_ID,
                    "SUR",
                    "confirm",
                )
            return {
                "confirmed": True,
                "root_state": "CONFIRMED",
                "skill_state": "CONFIRMED",
                "bound_move": move.uci(),
                "failed_reply": None,
                "all_reply_count": len(replies),
                "confirmed_reply_count": confirmed_replies,
                "candidate_count": len(legal_moves),
                "requested_candidate_count": rank,
                "successor_check_count": successor_checks,
                "virtual_frame_count": frames,
                "expanded_virtual_frame_count": frames,
                "bound_move_rank": rank,
                "trace": [{"tick": 0, "messages": messages}],
            }
        if record_trace:
            _policy_trace_message(
                messages,
                f"{ENTER_MATE_TWO_SKILL_ID}:{move.uci()}",
                ENTER_MATE_TWO_SKILL_ID,
                "SUR",
                "fail",
                failed_reply=candidate_failed_reply,
                confirmed_reply_count=confirmed_replies,
            )

    if record_trace:
        _policy_trace_message(
            messages,
            ENTER_MATE_TWO_SKILL_ID,
            ENTER_MATE_TWO_SKILL_ROOT_ID,
            "SUR",
            "fail",
        )
    return {
        "confirmed": False,
        "root_state": "FAILED",
        "skill_state": "FAILED",
        "bound_move": None,
        "failed_reply": None,
        "all_reply_count": 0,
        "confirmed_reply_count": 0,
        "candidate_count": len(legal_moves),
        "requested_candidate_count": len(legal_moves),
        "successor_check_count": successor_checks,
        "virtual_frame_count": frames,
        "expanded_virtual_frame_count": frames,
        "bound_move_rank": None,
        "trace": [{"tick": 0, "messages": messages}],
    }


def _edge_mate_enter_mate2_audit(
    board: chess.Board,
    *,
    scorer: FrozenMate2FirstScorer,
    mate2_cache: dict[str, dict[str, Any]],
    enter_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    cache_key = _position_repetition_key(board)
    cached = enter_cache.get(cache_key)
    if cached is not None:
        return cached
    audit = run_enter_mate2_skill(
        board,
        scorer=scorer,
        mate2_cache=mate2_cache,
        record_trace=False,
    )
    compact = {
        "confirmed": bool(audit["confirmed"]),
        "bound_move": audit["bound_move"],
        "failed_reply": audit["failed_reply"],
        "all_reply_count": int(audit["all_reply_count"]),
        "confirmed_reply_count": int(audit["confirmed_reply_count"]),
        "frames": int(audit["virtual_frame_count"]),
        "requested_candidate_count": int(audit["requested_candidate_count"]),
        "successor_check_count": int(audit["successor_check_count"]),
    }
    enter_cache[cache_key] = compact
    return compact


def _edge_mate_distance1_row(
    board: chess.Board,
    *,
    row_id: int,
    split: str,
    seed: int,
    scorer: FrozenMate2FirstScorer,
    mate2_cache: dict[str, dict[str, Any]],
    candidate_moves: Sequence[chess.Move] | None = None,
) -> dict[str, Any] | None:
    current = _edge_mate_exact_mate2_audit(board, scorer=scorer, cache=mate2_cache)
    if current["confirmed"]:
        return None

    move_rows: list[dict[str, Any]] = []
    total_frames = int(current["frames"])
    legal_moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    moves = tuple(candidate_moves) if candidate_moves is not None else scorer.order_moves(board, legal_moves)[:12]
    legal_uci = {move.uci() for move in legal_moves}
    for move in moves:
        if move.uci() not in legal_uci:
            continue
        after_white = board.copy(stack=False)
        after_white.push(move)
        if _white_rook_square(after_white) is None or after_white.is_stalemate():
            continue
        replies = tuple(sorted(after_white.legal_moves, key=lambda item: item.uci()))
        if not replies:
            continue
        success_replies: list[str] = []
        reply_frames = 0
        for reply in replies:
            successor = after_white.copy(stack=False)
            successor.push(reply)
            if _white_rook_square(successor) is None or successor.is_stalemate():
                continue
            audit = _edge_mate_exact_mate2_audit(
                successor,
                scorer=scorer,
                cache=mate2_cache,
            )
            reply_frames += int(audit["frames"])
            if audit["confirmed"]:
                success_replies.append(reply.uci())
        total_frames += reply_frames
        if success_replies:
            move_rows.append({
                "move": move.uci(),
                "success_reply_count": len(success_replies),
                "reply_count": len(replies),
                "success_replies": success_replies,
                "label_frames": reply_frames,
            })

    if not move_rows:
        return None
    move_rows.sort(
        key=lambda row: (
            row["success_reply_count"] / max(1, row["reply_count"]),
            row["success_reply_count"],
            row["move"],
        ),
        reverse=True,
    )
    return {
        "schema_version": EDGE_MATE_POOL_SCHEMA,
        "row_id": int(row_id),
        "split": split,
        "seed": int(seed),
        "family": "edge_mate_distance_1",
        "fen": board.fen(),
        "distance_to_exact_mate2_manifold": 1,
        "fence_established": True,
        "black_king_edge_confined": True,
        "positive_moves": [row["move"] for row in move_rows],
        "best_positive_move": move_rows[0]["move"],
        "positive_move_rows": move_rows,
        "exact_label_frames": total_frames,
        "label_source": "one_white_move_then_legal_black_reply_successor_exact_mate_in_2_skill",
        "learner_visible_labels": False,
    }


def _edge_mate_generate_distance1_rows(
    *,
    count: int,
    split: str,
    seed: int,
    scorer: FrozenMate2FirstScorer,
    mate2_cache: dict[str, dict[str, Any]],
    excluded: set[str],
    max_attempts: int,
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    attempts = 0
    while len(rows) < count and attempts < max_attempts:
        attempts += 1
        board = _edge_mate_board_from_random_fence_start(rng)
        if board is None:
            continue
        fen = board.fen()
        if fen in excluded:
            continue
        row = _edge_mate_distance1_row(
            board,
            row_id=len(rows),
            split=split,
            seed=seed,
            scorer=scorer,
            mate2_cache=mate2_cache,
        )
        if row is None:
            continue
        excluded.add(fen)
        rows.append(row)
    if len(rows) < count:
        raise RuntimeError(f"generated {len(rows)} {split} distance-1 rows, needed {count}")
    return rows


def _edge_mate_generate_distance2_to5_rows(
    *,
    count: int,
    seed: int,
    scorer: FrozenMate2FirstScorer,
    gate: Mapping[str, Any],
    config: EdgeMateDistanceTrainingConfig,
    excluded: set[str],
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    game_index = 0
    mate2_cache: dict[str, dict[str, Any]] = {}
    while len(rows) < count and game_index < config.max_selfplay_games:
        start = None
        while start is None:
            start = _edge_mate_board_from_random_fence_start(rng)
        board = start
        repetitions = {_position_repetition_key(board): 1}
        pending: list[dict[str, Any]] = []
        white_index = 0
        plies = 0
        while plies < config.max_game_plies and not board.is_game_over(claim_draw=False):
            if board.turn != chess.WHITE:
                break
            fence_now = fence_established_geometry(board)
            policy = _edge_mate_fast_dispatch(
                board,
                scorer=scorer,
                gate=gate,
                mate2_cache=mate2_cache,
                repetitions=repetitions,
            )
            if fence_now and not policy["mate2_gate_fired"]:
                pending.append({
                    "fen": board.fen(),
                    "white_index": white_index,
                    "branch": policy["branch"],
                })
            if policy["branch"] == "mate_in_2":
                for item in pending:
                    distance = white_index - int(item["white_index"])
                    if 2 <= distance <= 5 and item["fen"] not in excluded:
                        excluded.add(item["fen"])
                        rows.append({
                            "schema_version": EDGE_MATE_POOL_SCHEMA,
                            "row_id": len(rows),
                            "split": "distance_2_to_5",
                            "seed": int(seed),
                            "family": "edge_mate_distance_2_to_5_selfplay",
                            "fen": item["fen"],
                            "distance_to_exact_mate2_manifold": distance,
                            "plies_until_gate_fire": distance * 2,
                            "source_game_index": game_index,
                            "source_branch_at_state": item["branch"],
                            "fence_established": True,
                            "black_king_edge_confined": True,
                            "label_source": "phase2_7b_selfplay_first_mate2_gate_fire",
                            "learner_visible_labels": False,
                        })
                        if len(rows) >= count:
                            break
                break
            move = chess.Move.from_uci(policy["bound_move"]) if policy["bound_move"] else None
            if move is None or move not in board.legal_moves:
                break
            board.push(move)
            plies += 1
            key = _position_repetition_key(board)
            repetitions[key] = repetitions.get(key, 0) + 1
            if board.is_game_over(claim_draw=False) or repetitions[key] >= 3:
                break
            reply = _edge_mate_fixed_seed_black_reply(board, rng)
            if reply is None:
                break
            board.push(reply)
            plies += 1
            key = _position_repetition_key(board)
            repetitions[key] = repetitions.get(key, 0) + 1
            if _white_rook_square(board) is None or repetitions[key] >= 3:
                break
            white_index += 1
        game_index += 1
    if len(rows) < count:
        raise RuntimeError(f"generated {len(rows)} distance-2-to-5 rows, needed {count}")
    return rows


def _edge_mate_fast_dispatch(
    board: chess.Board,
    *,
    scorer: FrozenMate2FirstScorer,
    gate: Mapping[str, Any],
    mate2_cache: dict[str, dict[str, Any]],
    repetitions: Mapping[str, int],
) -> dict[str, Any]:
    from .foundation_curriculum import _mate_moves

    mates = _mate_moves(board)
    if mates:
        return {
            "branch": "mate_in_1",
            "bound_move": mates[0].uci(),
            "mate2_gate_fired": False,
        }
    gate_audit = score_chain_confidence_gate(board, gate)
    if gate_audit["fired"]:
        exact = _edge_mate_exact_mate2_audit(board, scorer=scorer, cache=mate2_cache)
        if exact["confirmed"] and exact["bound_move"] is not None:
            return {
                "branch": "mate_in_2",
                "bound_move": exact["bound_move"],
                "mate2_gate_fired": True,
            }
    if not fence_established_geometry(board):
        fence_move = resolve_establish_fence_move(board)
        if fence_move is not None:
            return {
                "branch": "establish_fence",
                "bound_move": fence_move.uci(),
                "mate2_gate_fired": bool(gate_audit["fired"]),
            }
    legal_moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    ordered = scorer.order_moves(board, legal_moves)
    allowed = tuple(
        move for move in ordered
        if int(repetitions.get(_after_move_repetition_key(board, move), 0)) < 2
    )
    if allowed:
        ordered = allowed
    return {
        "branch": "fallback",
        "bound_move": None if not ordered else ordered[0].uci(),
        "mate2_gate_fired": bool(gate_audit["fired"]),
    }


def generate_edge_mate_curriculum_pools(
    *,
    config: EdgeMateDistanceTrainingConfig = EdgeMateDistanceTrainingConfig(),
) -> dict[str, Any]:
    scorer = load_canonical_mate2_first_scorer()
    gate = load_chain_confidence_gate()
    mate2_cache: dict[str, dict[str, Any]] = {}
    excluded: set[str] = set()
    train = _edge_mate_generate_distance1_rows(
        count=config.distance1_train_count,
        split="train",
        seed=config.seed,
        scorer=scorer,
        mate2_cache=mate2_cache,
        excluded=excluded,
        max_attempts=config.max_generation_attempts,
    )
    heldout = _edge_mate_generate_distance1_rows(
        count=config.distance1_heldout_count,
        split="heldout",
        seed=config.seed + 1,
        scorer=scorer,
        mate2_cache=mate2_cache,
        excluded=excluded,
        max_attempts=config.max_generation_attempts,
    )
    deeper = _edge_mate_generate_distance2_to5_rows(
        count=config.distance2_to5_count,
        seed=config.seed + 2,
        scorer=scorer,
        gate=gate,
        config=config,
        excluded=excluded,
    )
    base = Path(config.output_dir)
    paths = {
        "distance1_train": base / "pools" / "edge_mate_distance1_train.jsonl.gz",
        "distance1_heldout": base / "pools" / "edge_mate_distance1_heldout.jsonl.gz",
        "distance2_to5": base / "pools" / "edge_mate_distance2_to5_selfplay.jsonl.gz",
    }
    _write_jsonl_gzip(paths["distance1_train"], train)
    _write_jsonl_gzip(paths["distance1_heldout"], heldout)
    _write_jsonl_gzip(paths["distance2_to5"], deeper)
    label_frames = [int(row["exact_label_frames"]) for row in train + heldout]
    summary = {
        "schema_version": "phase2_edge_mate_curriculum_summary.v0",
        "seed": int(config.seed),
        "distance1_train_count": len(train),
        "distance1_heldout_count": len(heldout),
        "distance2_to5_count": len(deeper),
        "pool_paths": {key: str(path) for key, path in paths.items()},
        "exact_label_frames_total": sum(label_frames),
        "exact_label_frames_mean": 0.0 if not label_frames else sum(label_frames) / len(label_frames),
        "exact_label_frames_max": max(label_frames) if label_frames else 0,
        "mate2_cache_state_count": len(mate2_cache),
        "distance2_to5_distribution": {
            str(distance): sum(
                int(row["distance_to_exact_mate2_manifold"]) == distance
                for row in deeper
            )
            for distance in range(2, 6)
        },
        "black_policy": "fixed_seed_uniform_legal",
        "graph_native_learned_dispatch_migration": "deferred_after_flat_episode_v1",
    }
    _write_json(base / "edge_mate_curriculum_summary.json", summary)
    return {"summary": summary, "train": train, "heldout": heldout, "deeper": deeper}


def _edge_mate_episode_rollout(
    row: Mapping[str, Any],
    *,
    chooser: Callable[[chess.Board, int, random.Random], chess.Move | None],
    scorer: FrozenMate2FirstScorer,
    rng: random.Random,
    max_white_moves: int,
    mate2_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    board = chess.Board(str(row["fen"]))
    terminal_activations: list[list[str]] = []
    white_moves: list[str] = []
    black_replies: list[str] = []
    frames = 0
    endpoint = "horizon"
    for white_ply in range(max_white_moves):
        audit = _edge_mate_exact_mate2_audit(board, scorer=scorer, cache=mate2_cache)
        frames += int(audit["frames"])
        if audit["confirmed"]:
            endpoint = "mate2_manifold_entered"
            break
        if board.turn != chess.WHITE or board.is_game_over(claim_draw=False):
            endpoint = "terminal"
            break
        move = chooser(board, white_ply, rng)
        if move is None or move not in board.legal_moves:
            endpoint = "illegal"
            break
        terminal_activations.append(_edge_mate_terminal_keys(board, move))
        white_moves.append(move.uci())
        board.push(move)
        if _white_rook_square(board) is None:
            endpoint = "rook_lost"
            break
        if board.is_stalemate():
            endpoint = "stalemate"
            break
        if board.is_checkmate():
            endpoint = "mate_delivered"
            break
        if board.turn != chess.BLACK:
            endpoint = "terminal"
            break
        reply = _edge_mate_fixed_seed_black_reply(board, rng)
        if reply is None:
            endpoint = "mate_delivered" if board.is_check() else "stalemate"
            break
        board.push(reply)
        black_replies.append(reply.uci())
        if _white_rook_square(board) is None:
            endpoint = "rook_lost"
            break
        if board.is_stalemate():
            endpoint = "stalemate"
            break
        audit = _edge_mate_exact_mate2_audit(board, scorer=scorer, cache=mate2_cache)
        frames += int(audit["frames"])
        if audit["confirmed"]:
            endpoint = "mate2_manifold_entered"
            break
        if not fence_established_geometry(board):
            endpoint = "fence_broken"
            break
    success = endpoint in {"mate2_manifold_entered", "mate_delivered"}
    reward_channels = {
        "mate2_manifold_entry": 6.0 if endpoint == "mate2_manifold_entered" else 0.0,
        "mate_delivery": 6.0 if endpoint == "mate_delivered" else 0.0,
        "terminal_failure": -6.0 if endpoint in {"fence_broken", "rook_lost", "stalemate", "illegal"} else 0.0,
        "horizon": -1.0 if endpoint == "horizon" else 0.0,
    }
    trajectory_reward = round(sum(reward_channels.values()), 6)
    return {
        "start_fen": row["fen"],
        "endpoint_type": endpoint,
        "episode_success": success,
        "white_moves": white_moves,
        "black_replies": black_replies,
        "terminal_activations_by_white_ply": terminal_activations,
        "reward_channels": reward_channels,
        "trajectory_reward": trajectory_reward,
        "exact_mate2_frames": frames,
        "learner_visible_labels": False,
    }


def _edge_mate_apply_contrastive_credit(
    learner: TerminalAffordanceLearner,
    *,
    selected: Mapping[str, Any],
    alternative: Mapping[str, Any],
    config: EdgeMateDistanceTrainingConfig,
) -> None:
    selected_activations = selected["terminal_activations_by_white_ply"]
    alternative_activations = alternative["terminal_activations_by_white_ply"]
    total = max(len(selected_activations), len(alternative_activations))
    reward_delta = float(selected["trajectory_reward"]) - float(alternative["trajectory_reward"])
    for index in range(total):
        selected_keys = set(selected_activations[index]) if index < len(selected_activations) else set()
        alternative_keys = set(alternative_activations[index]) if index < len(alternative_activations) else set()
        discount = config.gamma ** max(0, total - index - 1)
        discounted = reward_delta * discount
        terminal_credit = {
            key: discounted for key in sorted(selected_keys - alternative_keys)
        }
        terminal_credit.update({
            key: -discounted for key in sorted(alternative_keys - selected_keys)
        })
        for key, reward in terminal_credit.items():
            terminal = learner.get_terminal(key)
            terminal.update(
                reward=reward,
                eta=config.eta_m3,
                scale=1.0,
                cycle=learner.cycle,
            )
            learner.m3_update_count += 1
        learner.cycle += 1


def _edge_mate_learned_chooser(
    learner: TerminalAffordanceLearner,
    *,
    epsilon: float,
    gate: Mapping[str, Any] | None = None,
    include_internal: bool = False,
) -> Callable[[chess.Board, int, random.Random], chess.Move | None]:
    def choose(board: chess.Board, _white_ply: int, rng: random.Random) -> chess.Move | None:
        moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
        if not moves:
            return None
        if rng.random() < epsilon:
            return moves[rng.randrange(len(moves))]
        if not include_internal:
            return learner.choose(board)
        options = [
            (
                sum(
                    learner.terminals[key].local_weight
                    for key in _edge_mate_terminal_keys(
                        board,
                        move,
                        gate=gate,
                        include_internal=True,
                    )
                    if key in learner.terminals
                ),
                move.uci(),
                move,
            )
            for move in moves
        ]
        options.sort(reverse=True)
        return options[0][-1]

    return choose


def _edge_mate_best_positive_chooser(
    row: Mapping[str, Any],
) -> Callable[[chess.Board, int, random.Random], chess.Move | None]:
    positive = str(row["best_positive_move"])

    def choose(board: chess.Board, white_ply: int, _rng: random.Random) -> chess.Move | None:
        if white_ply == 0:
            move = chess.Move.from_uci(positive)
            if move in board.legal_moves:
                return move
        moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
        return moves[0] if moves else None

    return choose


def _edge_mate_bad_or_random_chooser(
    row: Mapping[str, Any],
) -> Callable[[chess.Board, int, random.Random], chess.Move | None]:
    positives = set(row.get("positive_moves", []))

    def choose(board: chess.Board, _white_ply: int, rng: random.Random) -> chess.Move | None:
        moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
        if not moves:
            return None
        negatives = [move for move in moves if move.uci() not in positives]
        choices = tuple(negatives or moves)
        return choices[rng.randrange(len(choices))]

    return choose


def _edge_mate_fallback_chooser(
    scorer: FrozenMate2FirstScorer,
) -> Callable[[chess.Board, int, random.Random], chess.Move | None]:
    def choose(board: chess.Board, _white_ply: int, _rng: random.Random) -> chess.Move | None:
        moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
        ordered = scorer.order_moves(board, moves)
        return ordered[0] if ordered else None

    return choose


def _edge_mate_random_chooser(
    board: chess.Board,
    _white_ply: int,
    rng: random.Random,
) -> chess.Move | None:
    moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    return None if not moves else moves[rng.randrange(len(moves))]


def _edge_mate_train_one_seed(
    rows: Sequence[Mapping[str, Any]],
    *,
    seed: int,
    scorer: FrozenMate2FirstScorer,
    config: EdgeMateDistanceTrainingConfig,
) -> tuple[TerminalAffordanceLearner, dict[str, Any]]:
    learner = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    mate2_cache: dict[str, dict[str, Any]] = {}
    traces: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if index % 2 == 0:
            selected_chooser = _edge_mate_best_positive_chooser(row)
            alternative_chooser = _edge_mate_bad_or_random_chooser(row)
        else:
            selected_chooser = _edge_mate_learned_chooser(learner, epsilon=config.epsilon)
            alternative_chooser = _edge_mate_best_positive_chooser(row)
        selected = _edge_mate_episode_rollout(
            row,
            chooser=selected_chooser,
            scorer=scorer,
            rng=random.Random(seed + index * 17),
            max_white_moves=config.max_white_moves_per_episode,
            mate2_cache=mate2_cache,
        )
        alternative = _edge_mate_episode_rollout(
            row,
            chooser=alternative_chooser,
            scorer=scorer,
            rng=random.Random(seed + 100_000 + index * 17),
            max_white_moves=config.max_white_moves_per_episode,
            mate2_cache=mate2_cache,
        )
        _edge_mate_apply_contrastive_credit(
            learner,
            selected=selected,
            alternative=alternative,
            config=config,
        )
        traces.append({
            "row_id": row["row_id"],
            "selected_endpoint": selected["endpoint_type"],
            "selected_success": selected["episode_success"],
            "alternative_endpoint": alternative["endpoint_type"],
            "alternative_success": alternative["episode_success"],
            "reward_delta": round(float(selected["trajectory_reward"]) - float(alternative["trajectory_reward"]), 6),
        })
    return learner, {
        "train_trace_count": len(traces),
        "selected_success_count": sum(int(trace["selected_success"]) for trace in traces),
        "alternative_success_count": sum(int(trace["alternative_success"]) for trace in traces),
        "terminal_count": len(learner.terminals),
        "m3_update_count": learner.m3_update_count,
        "mate2_cache_state_count": len(mate2_cache),
    }


def _edge_mate_evaluate_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    chooser: Callable[[chess.Board, int, random.Random], chess.Move | None],
    scorer: FrozenMate2FirstScorer,
    seed: int,
    config: EdgeMateDistanceTrainingConfig,
) -> dict[str, Any]:
    mate2_cache: dict[str, dict[str, Any]] = {}
    traces = [
        _edge_mate_episode_rollout(
            row,
            chooser=chooser,
            scorer=scorer,
            rng=random.Random(seed + index * 31),
            max_white_moves=config.max_white_moves_per_episode,
            mate2_cache=mate2_cache,
        )
        for index, row in enumerate(rows)
    ]
    successes = [trace for trace in traces if trace["episode_success"]]
    endpoint_counts = {
        endpoint: sum(trace["endpoint_type"] == endpoint for trace in traces)
        for endpoint in sorted({trace["endpoint_type"] for trace in traces})
    }
    frames = [int(trace["exact_mate2_frames"]) for trace in traces]
    return {
        "row_count": len(rows),
        "manifold_entry_count": len(successes),
        "manifold_entry_rate": 0.0 if not rows else len(successes) / len(rows),
        "endpoint_counts": endpoint_counts,
        "exact_frames_mean": 0.0 if not frames else sum(frames) / len(frames),
        "exact_frames_max": max(frames) if frames else 0,
        "sample_failures": [
            {
                "fen": rows[index]["fen"],
                "endpoint": trace["endpoint_type"],
                "white_moves": trace["white_moves"],
            }
            for index, trace in enumerate(traces)
            if not trace["episode_success"]
        ][:8],
    }


def _edge_mate_structure_summary(
    learner: TerminalAffordanceLearner,
    *,
    config: EdgeMateDistanceTrainingConfig,
) -> dict[str, Any]:
    promoted_affordances = []
    promoted_vetoes = []
    for key, terminal in sorted(learner.terminals.items()):
        events = terminal.positive_credit + terminal.negative_credit
        if events < config.promotion_min_credit_events:
            continue
        if terminal.local_weight >= config.promotion_abs_weight_threshold:
            promoted_affordances.append(key)
        elif terminal.local_weight <= -config.promotion_abs_weight_threshold:
            promoted_vetoes.append(key)
    return {
        "terminal_count": len(learner.terminals),
        "promoted_affordance_count": len(promoted_affordances),
        "promoted_veto_count": len(promoted_vetoes),
        "top_affordances": promoted_affordances[:12],
        "top_vetoes": promoted_vetoes[:12],
        "promotion_rule": {
            "abs_weight_threshold": config.promotion_abs_weight_threshold,
            "min_credit_events": config.promotion_min_credit_events,
        },
    }


def run_edge_mate_distance1_training(
    *,
    config: EdgeMateDistanceTrainingConfig = EdgeMateDistanceTrainingConfig(),
    regenerate_pools: bool = False,
) -> dict[str, Any]:
    base = Path(config.output_dir)
    summary_path = base / "edge_mate_curriculum_summary.json"
    if regenerate_pools or not summary_path.exists():
        pool_payload = generate_edge_mate_curriculum_pools(config=config)
        pool_summary = pool_payload["summary"]
        train_rows = pool_payload["train"]
        heldout_rows = pool_payload["heldout"]
    else:
        pool_summary = json.loads(summary_path.read_text(encoding="utf-8"))
        train_rows = _read_jsonl_gzip(pool_summary["pool_paths"]["distance1_train"])
        heldout_rows = _read_jsonl_gzip(pool_summary["pool_paths"]["distance1_heldout"])

    scorer = load_canonical_mate2_first_scorer()
    fallback_eval = _edge_mate_evaluate_rows(
        heldout_rows,
        chooser=_edge_mate_fallback_chooser(scorer),
        scorer=scorer,
        seed=config.seed + 50,
        config=config,
    )
    random_eval = _edge_mate_evaluate_rows(
        heldout_rows,
        chooser=_edge_mate_random_chooser,
        scorer=scorer,
        seed=config.seed + 60,
        config=config,
    )

    seed_results: dict[str, Any] = {}
    for seed in config.train_seeds:
        learner, train_summary = _edge_mate_train_one_seed(
            train_rows,
            seed=int(seed),
            scorer=scorer,
            config=config,
        )
        learned_eval = _edge_mate_evaluate_rows(
            heldout_rows,
            chooser=lambda board, white_ply, rng, learner=learner: learner.choose(board),
            scorer=scorer,
            seed=int(seed) + 500,
            config=config,
        )
        seed_results[str(seed)] = {
            "train": train_summary,
            "heldout_eval": learned_eval,
            "structure": _edge_mate_structure_summary(learner, config=config),
            "learner": learner.to_dict(max_terminals=16),
        }

    learned_rates = [
        result["heldout_eval"]["manifold_entry_rate"]
        for result in seed_results.values()
    ]
    fallback_rate = fallback_eval["manifold_entry_rate"]
    stop = all(rate <= fallback_rate for rate in learned_rates)
    result = {
        "schema_version": EDGE_MATE_RESULT_SCHEMA,
        "config": {
            **config.__dict__,
            "train_seeds": list(config.train_seeds),
        },
        "pool_summary": pool_summary,
        "baseline_eval": {
            "fallback_scorer_alone": fallback_eval,
            "random_legal": random_eval,
        },
        "seed_results": seed_results,
        "decision": {
            "status": "stop_learned_not_above_fallback_all_seeds" if stop else "distance1_clears_fallback_baseline",
            "learned_rates": learned_rates,
            "fallback_rate": fallback_rate,
            "random_rate": random_eval["manifold_entry_rate"],
            "black_policy": "fixed_seed_uniform_legal",
            "graph_native_learned_dispatch_migration": "deferred_to_later_phase2_session",
        },
    }
    _write_json(base / "edge_mate_distance1_training_summary.json", result)
    return result


def evaluate_enter_mate2_skill_on_distance1_heldout(
    *,
    config: EdgeMateDistanceTrainingConfig = EdgeMateDistanceTrainingConfig(),
) -> dict[str, Any]:
    base = Path(config.output_dir)
    summary_path = base / "edge_mate_curriculum_summary.json"
    if not summary_path.exists():
        generate_edge_mate_curriculum_pools(config=config)
    pool_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    heldout_rows = _read_jsonl_gzip(pool_summary["pool_paths"]["distance1_heldout"])
    scorer = load_canonical_mate2_first_scorer()
    mate2_cache: dict[str, dict[str, Any]] = {}
    audits = [
        run_enter_mate2_skill(
            chess.Board(row["fen"]),
            scorer=scorer,
            mate2_cache=mate2_cache,
            record_trace=False,
        )
        for row in heldout_rows
    ]
    frames = [int(audit["virtual_frame_count"]) for audit in audits]
    result = {
        "schema_version": "phase2_enter_mate2_distance1_eval.v0",
        "heldout_path": pool_summary["pool_paths"]["distance1_heldout"],
        "row_count": len(heldout_rows),
        "entry_count": sum(int(audit["confirmed"]) for audit in audits),
        "entry_rate": 0.0 if not audits else sum(int(audit["confirmed"]) for audit in audits) / len(audits),
        "frames_mean": 0.0 if not frames else sum(frames) / len(frames),
        "frames_max": max(frames) if frames else 0,
        "requested_candidates_mean": (
            0.0 if not audits else sum(int(audit["requested_candidate_count"]) for audit in audits) / len(audits)
        ),
        "sample_failures": [
            {
                "fen": heldout_rows[index]["fen"],
                "positive_moves": heldout_rows[index].get("positive_moves", []),
                "requested_candidate_count": audits[index]["requested_candidate_count"],
            }
            for index, audit in enumerate(audits)
            if not audit["confirmed"]
        ][:8],
    }
    _write_json(base / "enter_mate2_distance1_eval.json", result)
    return result


def _edge_mate_distance2_row(
    source: Mapping[str, Any],
    *,
    row_id: int,
    split: str,
    scorer: FrozenMate2FirstScorer,
    mate2_cache: dict[str, dict[str, Any]],
    enter_cache: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    board = chess.Board(str(source["fen"]))
    current = _edge_mate_enter_mate2_audit(
        board,
        scorer=scorer,
        mate2_cache=mate2_cache,
        enter_cache=enter_cache,
    )
    if current["confirmed"]:
        return None

    move_rows: list[dict[str, Any]] = []
    total_frames = int(current["frames"])
    legal_moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    for move in scorer.order_moves(board, legal_moves):
        after_white = _after_move(board, move)
        if _white_rook_square(after_white) is None or after_white.is_stalemate():
            continue
        replies = tuple(sorted(after_white.legal_moves, key=lambda item: item.uci()))
        if not replies:
            continue
        success_replies: list[str] = []
        reply_frames = 0
        for reply in replies:
            successor = _after_move(after_white, reply)
            if _white_rook_square(successor) is None or successor.is_stalemate():
                continue
            audit = _edge_mate_enter_mate2_audit(
                successor,
                scorer=scorer,
                mate2_cache=mate2_cache,
                enter_cache=enter_cache,
            )
            reply_frames += int(audit["frames"])
            if audit["confirmed"]:
                success_replies.append(reply.uci())
        total_frames += reply_frames
        if success_replies:
            move_rows.append({
                "move": move.uci(),
                "success_reply_count": len(success_replies),
                "reply_count": len(replies),
                "success_replies": success_replies,
                "label_frames": reply_frames,
            })

    if not move_rows:
        return None
    move_rows.sort(
        key=lambda row: (
            row["success_reply_count"] / max(1, row["reply_count"]),
            row["success_reply_count"],
            row["move"],
        ),
        reverse=True,
    )
    return {
        "schema_version": EDGE_MATE_POOL_SCHEMA,
        "row_id": int(row_id),
        "split": split,
        "seed": int(source.get("seed", 0)),
        "family": "edge_mate_distance_2_certified",
        "fen": board.fen(),
        "distance_to_certified_distance1_manifold": 2,
        "distance_to_exact_mate2_manifold": 2,
        "source_family": source.get("family"),
        "source_row_id": source.get("row_id"),
        "source_game_index": source.get("source_game_index"),
        "fence_established": True,
        "black_king_edge_confined": True,
        "positive_moves": [row["move"] for row in move_rows],
        "best_positive_move": move_rows[0]["move"],
        "positive_move_rows": move_rows,
        "exact_label_frames": total_frames,
        "label_source": "one_white_move_then_legal_black_reply_successor_enter_mate2_skill",
        "learner_visible_labels": False,
    }


def prepare_edge_mate_distance2_stratum(
    *,
    config: EdgeMateDistanceTrainingConfig = EdgeMateDistanceTrainingConfig(),
    regenerate: bool = False,
    heldout_count: int = 64,
) -> dict[str, Any]:
    base = Path(config.output_dir)
    train_path = base / "pools" / "edge_mate_distance2_certified_train.jsonl.gz"
    heldout_path = base / "pools" / "edge_mate_distance2_certified_heldout.jsonl.gz"
    summary_path = base / "edge_mate_distance2_certified_summary.json"
    if not regenerate and train_path.exists() and heldout_path.exists() and summary_path.exists():
        return {
            "summary": json.loads(summary_path.read_text(encoding="utf-8")),
            "train": _read_jsonl_gzip(train_path),
            "heldout": _read_jsonl_gzip(heldout_path),
        }

    curriculum_path = base / "edge_mate_curriculum_summary.json"
    if not curriculum_path.exists():
        generate_edge_mate_curriculum_pools(config=config)
    curriculum_summary = json.loads(curriculum_path.read_text(encoding="utf-8"))
    source_rows = _read_jsonl_gzip(curriculum_summary["pool_paths"]["distance2_to5"])
    source_d2 = [
        row for row in source_rows
        if int(row.get("distance_to_exact_mate2_manifold", -1)) == 2
    ]
    rng = random.Random(config.seed + 80)
    rng.shuffle(source_d2)

    scorer = load_canonical_mate2_first_scorer()
    mate2_cache: dict[str, dict[str, Any]] = {}
    enter_cache: dict[str, dict[str, Any]] = {}
    certified: list[dict[str, Any]] = []
    for source in source_d2:
        row = _edge_mate_distance2_row(
            source,
            row_id=len(certified),
            split="certified_distance2",
            scorer=scorer,
            mate2_cache=mate2_cache,
            enter_cache=enter_cache,
        )
        if row is not None:
            certified.append(row)

    if len(certified) < heldout_count:
        raise RuntimeError(
            f"certified {len(certified)} distance-2 rows, needed heldout_count={heldout_count}"
        )
    train_rows = certified[:-heldout_count]
    heldout_rows = certified[-heldout_count:]
    for index, row in enumerate(train_rows):
        row["row_id"] = index
        row["split"] = "distance2_train"
    for index, row in enumerate(heldout_rows):
        row["row_id"] = index
        row["split"] = "distance2_heldout"

    _write_jsonl_gzip(train_path, train_rows)
    _write_jsonl_gzip(heldout_path, heldout_rows)
    summary = {
        "schema_version": "phase2_edge_mate_distance2_certified_summary.v0",
        "source_path": curriculum_summary["pool_paths"]["distance2_to5"],
        "source_distance2_count": len(source_d2),
        "certified_count": len(certified),
        "train_count": len(train_rows),
        "heldout_count": len(heldout_rows),
        "pool_paths": {
            "distance2_train": str(train_path),
            "distance2_heldout": str(heldout_path),
        },
        "exact_label_frames_total": sum(int(row["exact_label_frames"]) for row in certified),
        "exact_label_frames_mean": (
            0.0 if not certified else sum(int(row["exact_label_frames"]) for row in certified) / len(certified)
        ),
        "exact_label_frames_max": max((int(row["exact_label_frames"]) for row in certified), default=0),
        "mate2_cache_state_count": len(mate2_cache),
        "enter_mate2_cache_state_count": len(enter_cache),
        "label_source": "distance2_relabeled_by_enter_mate2_successor_check",
    }
    _write_json(summary_path, summary)
    return {"summary": summary, "train": train_rows, "heldout": heldout_rows}


def _edge_mate_distance2_episode_rollout(
    row: Mapping[str, Any],
    *,
    chooser: Callable[[chess.Board, int, random.Random], chess.Move | None],
    scorer: FrozenMate2FirstScorer,
    gate: Mapping[str, Any],
    rng: random.Random,
    max_white_moves: int,
    mate2_cache: dict[str, dict[str, Any]],
    enter_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    board = chess.Board(str(row["fen"]))
    terminal_activations: list[list[str]] = []
    white_moves: list[str] = []
    black_replies: list[str] = []
    frames = 0
    endpoint = "horizon"
    for white_ply in range(max_white_moves):
        audit = _edge_mate_enter_mate2_audit(
            board,
            scorer=scorer,
            mate2_cache=mate2_cache,
            enter_cache=enter_cache,
        )
        frames += int(audit["frames"])
        if audit["confirmed"]:
            endpoint = "distance1_manifold_entered"
            break
        if board.turn != chess.WHITE or board.is_game_over(claim_draw=False):
            endpoint = "terminal"
            break
        move = chooser(board, white_ply, rng)
        if move is None or move not in board.legal_moves:
            endpoint = "illegal"
            break
        terminal_activations.append(
            _edge_mate_terminal_keys(
                board,
                move,
                gate=gate,
                include_internal=True,
            )
        )
        white_moves.append(move.uci())
        board.push(move)
        if _white_rook_square(board) is None:
            endpoint = "rook_lost"
            break
        if board.is_stalemate():
            endpoint = "stalemate"
            break
        if board.is_checkmate():
            endpoint = "mate_delivered"
            break
        reply = _edge_mate_fixed_seed_black_reply(board, rng)
        if reply is None:
            endpoint = "mate_delivered" if board.is_check() else "stalemate"
            break
        board.push(reply)
        black_replies.append(reply.uci())
        if _white_rook_square(board) is None:
            endpoint = "rook_lost"
            break
        if board.is_stalemate():
            endpoint = "stalemate"
            break
        audit = _edge_mate_enter_mate2_audit(
            board,
            scorer=scorer,
            mate2_cache=mate2_cache,
            enter_cache=enter_cache,
        )
        frames += int(audit["frames"])
        if audit["confirmed"]:
            endpoint = "distance1_manifold_entered"
            break
        if not fence_established_geometry(board):
            endpoint = "fence_broken"
            break
    success = endpoint in {"distance1_manifold_entered", "mate_delivered"}
    reward_channels = {
        "distance1_manifold_entry": 6.0 if endpoint == "distance1_manifold_entered" else 0.0,
        "mate_delivery": 6.0 if endpoint == "mate_delivered" else 0.0,
        "terminal_failure": -6.0 if endpoint in {"fence_broken", "rook_lost", "stalemate", "illegal"} else 0.0,
        "horizon": -1.0 if endpoint == "horizon" else 0.0,
    }
    trajectory_reward = round(sum(reward_channels.values()), 6)
    return {
        "start_fen": row["fen"],
        "endpoint_type": endpoint,
        "episode_success": success,
        "white_moves": white_moves,
        "black_replies": black_replies,
        "terminal_activations_by_white_ply": terminal_activations,
        "reward_channels": reward_channels,
        "trajectory_reward": trajectory_reward,
        "enter_mate2_frames": frames,
        "learner_visible_labels": False,
    }


def _edge_mate_dispatcher_chooser(
    *,
    scorer: FrozenMate2FirstScorer,
    gate: Mapping[str, Any],
) -> Callable[[chess.Board, int, random.Random], chess.Move | None]:
    def choose(board: chess.Board, _white_ply: int, _rng: random.Random) -> chess.Move | None:
        policy = run_krk_policy(
            board,
            gate=gate,
            scorer=scorer,
            record_trace=False,
            repetition_counts={_position_repetition_key(board): 1},
        )
        return None if policy["bound_move"] is None else chess.Move.from_uci(policy["bound_move"])

    return choose


def _edge_mate_distance2_train_one_seed(
    rows: Sequence[Mapping[str, Any]],
    *,
    seed: int,
    scorer: FrozenMate2FirstScorer,
    gate: Mapping[str, Any],
    config: EdgeMateDistanceTrainingConfig,
) -> tuple[TerminalAffordanceLearner, dict[str, Any]]:
    learner = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    mate2_cache: dict[str, dict[str, Any]] = {}
    enter_cache: dict[str, dict[str, Any]] = {}
    traces: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if index % 2 == 0:
            selected_chooser = _edge_mate_best_positive_chooser(row)
            alternative_chooser = _edge_mate_bad_or_random_chooser(row)
        else:
            selected_chooser = _edge_mate_learned_chooser(
                learner,
                epsilon=config.epsilon,
                gate=gate,
                include_internal=True,
            )
            alternative_chooser = _edge_mate_best_positive_chooser(row)
        selected = _edge_mate_distance2_episode_rollout(
            row,
            chooser=selected_chooser,
            scorer=scorer,
            gate=gate,
            rng=random.Random(seed + index * 17),
            max_white_moves=config.max_white_moves_per_episode,
            mate2_cache=mate2_cache,
            enter_cache=enter_cache,
        )
        alternative = _edge_mate_distance2_episode_rollout(
            row,
            chooser=alternative_chooser,
            scorer=scorer,
            gate=gate,
            rng=random.Random(seed + 100_000 + index * 17),
            max_white_moves=config.max_white_moves_per_episode,
            mate2_cache=mate2_cache,
            enter_cache=enter_cache,
        )
        _edge_mate_apply_contrastive_credit(
            learner,
            selected=selected,
            alternative=alternative,
            config=config,
        )
        traces.append({
            "row_id": row["row_id"],
            "selected_endpoint": selected["endpoint_type"],
            "selected_success": selected["episode_success"],
            "alternative_endpoint": alternative["endpoint_type"],
            "alternative_success": alternative["episode_success"],
            "reward_delta": round(float(selected["trajectory_reward"]) - float(alternative["trajectory_reward"]), 6),
        })
    return learner, {
        "train_trace_count": len(traces),
        "selected_success_count": sum(int(trace["selected_success"]) for trace in traces),
        "alternative_success_count": sum(int(trace["alternative_success"]) for trace in traces),
        "terminal_count": len(learner.terminals),
        "m3_update_count": learner.m3_update_count,
        "mate2_cache_state_count": len(mate2_cache),
        "enter_mate2_cache_state_count": len(enter_cache),
    }


def _edge_mate_distance2_evaluate_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    chooser: Callable[[chess.Board, int, random.Random], chess.Move | None],
    scorer: FrozenMate2FirstScorer,
    gate: Mapping[str, Any],
    seed: int,
    config: EdgeMateDistanceTrainingConfig,
) -> dict[str, Any]:
    mate2_cache: dict[str, dict[str, Any]] = {}
    enter_cache: dict[str, dict[str, Any]] = {}
    traces = [
        _edge_mate_distance2_episode_rollout(
            row,
            chooser=chooser,
            scorer=scorer,
            gate=gate,
            rng=random.Random(seed + index * 31),
            max_white_moves=config.max_white_moves_per_episode,
            mate2_cache=mate2_cache,
            enter_cache=enter_cache,
        )
        for index, row in enumerate(rows)
    ]
    successes = [trace for trace in traces if trace["episode_success"]]
    endpoint_counts = {
        endpoint: sum(trace["endpoint_type"] == endpoint for trace in traces)
        for endpoint in sorted({trace["endpoint_type"] for trace in traces})
    }
    frames = [int(trace["enter_mate2_frames"]) for trace in traces]
    return {
        "row_count": len(rows),
        "distance1_entry_count": len(successes),
        "distance1_entry_rate": 0.0 if not rows else len(successes) / len(rows),
        "endpoint_counts": endpoint_counts,
        "enter_mate2_frames_mean": 0.0 if not frames else sum(frames) / len(frames),
        "enter_mate2_frames_max": max(frames) if frames else 0,
        "sample_failures": [
            {
                "fen": rows[index]["fen"],
                "endpoint": trace["endpoint_type"],
                "white_moves": trace["white_moves"],
            }
            for index, trace in enumerate(traces)
            if not trace["episode_success"]
        ][:8],
    }


def run_edge_mate_distance2_training(
    *,
    config: EdgeMateDistanceTrainingConfig = EdgeMateDistanceTrainingConfig(),
    regenerate_stratum: bool = False,
) -> dict[str, Any]:
    stratum = prepare_edge_mate_distance2_stratum(
        config=config,
        regenerate=regenerate_stratum,
    )
    train_rows = stratum["train"]
    heldout_rows = stratum["heldout"]
    scorer = load_canonical_mate2_first_scorer()
    gate = load_chain_confidence_gate()
    fallback_eval = _edge_mate_distance2_evaluate_rows(
        heldout_rows,
        chooser=_edge_mate_fallback_chooser(scorer),
        scorer=scorer,
        gate=gate,
        seed=config.seed + 150,
        config=config,
    )
    random_eval = _edge_mate_distance2_evaluate_rows(
        heldout_rows,
        chooser=_edge_mate_random_chooser,
        scorer=scorer,
        gate=gate,
        seed=config.seed + 160,
        config=config,
    )
    dispatcher_eval = _edge_mate_distance2_evaluate_rows(
        heldout_rows,
        chooser=_edge_mate_dispatcher_chooser(scorer=scorer, gate=gate),
        scorer=scorer,
        gate=gate,
        seed=config.seed + 170,
        config=config,
    )

    seed_results: dict[str, Any] = {}
    for seed in config.train_seeds:
        learner, train_summary = _edge_mate_distance2_train_one_seed(
            train_rows,
            seed=int(seed),
            scorer=scorer,
            gate=gate,
            config=config,
        )
        learned_eval = _edge_mate_distance2_evaluate_rows(
            heldout_rows,
            chooser=_edge_mate_learned_chooser(
                learner,
                epsilon=0.0,
                gate=gate,
                include_internal=True,
            ),
            scorer=scorer,
            gate=gate,
            seed=int(seed) + 700,
            config=config,
        )
        seed_results[str(seed)] = {
            "train": train_summary,
            "heldout_eval": learned_eval,
            "structure": _edge_mate_structure_summary(learner, config=config),
            "learner": learner.to_dict(max_terminals=16),
        }

    learned_rates = [
        result["heldout_eval"]["distance1_entry_rate"]
        for result in seed_results.values()
    ]
    fallback_rate = fallback_eval["distance1_entry_rate"]
    random_rate = random_eval["distance1_entry_rate"]
    dispatcher_rate = dispatcher_eval["distance1_entry_rate"]
    stop = all(
        rate <= fallback_rate and rate <= random_rate and rate <= dispatcher_rate
        for rate in learned_rates
    )
    instability = (max(learned_rates) - min(learned_rates)) > 0.10 if learned_rates else False
    clears_dispatcher_count = sum(rate > dispatcher_rate for rate in learned_rates)
    status = "stop_learned_not_above_any_baseline_all_seeds" if stop else "distance2_measured"
    if not stop and instability:
        status = "distance2_measured_seed_instability_gt_0_10"
    elif not stop and clears_dispatcher_count >= 2:
        status = "distance2_clears_dispatcher_baseline"

    result = {
        "schema_version": "phase2_edge_mate_distance2_training.v0",
        "config": {
            **config.__dict__,
            "train_seeds": list(config.train_seeds),
        },
        "stratum_summary": stratum["summary"],
        "baseline_eval": {
            "fallback_scorer_alone": fallback_eval,
            "random_legal": random_eval,
            "integrated_dispatcher": dispatcher_eval,
        },
        "seed_results": seed_results,
        "decision": {
            "status": status,
            "learned_rates": learned_rates,
            "fallback_rate": fallback_rate,
            "random_rate": random_rate,
            "dispatcher_rate": dispatcher_rate,
            "seed_spread": 0.0 if not learned_rates else max(learned_rates) - min(learned_rates),
            "clears_dispatcher_seed_count": clears_dispatcher_count,
            "black_policy": "fixed_seed_uniform_legal",
            "exact_one_ply_bright_line": "distance1 closure only; distance2 policy is learned from certified distance1-entry reward",
        },
    }
    _write_json(Path(config.output_dir) / "edge_mate_distance2_training_summary.json", result)
    return result
