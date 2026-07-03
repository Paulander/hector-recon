"""Static quorum basin recognizers over dieted KRK percepts."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Sequence

import chess

from recon_lite import FormalReConEngine, Graph, LinkType, Node, NodeState, NodeType

from .features import extract_learner_features
from .terminal_substrate import terminal_action_feature_keys


ROOT_ID = "phase2_basin_root"
MATE_IN_ONE_SKILL_ROOT_ID = "phase2_mate_in_1_skill_root"
MATE_IN_ONE_SKILL_ID = "mate_in_1_skill"
MATE_IN_ONE_RECOGNIZER_STEP_ID = "mate_in_1_basin_recognizer_step"
MATE_IN_TWO_SKILL_ROOT_ID = "phase2_mate_in_2_skill_root"
MATE_IN_TWO_SKILL_ID = "mate_in_2_skill"
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


def build_mate_in_one_basin_graph() -> Graph:
    """Build the fixed recognizer graph; no positions or labels are stored."""

    graph = Graph()
    graph.add_node(Node(ROOT_ID, NodeType.SCRIPT))
    _add_mate_in_one_basin_subgraph(graph, ROOT_ID)
    graph.validate_formal_pairs()
    return graph


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


def _zero_reply_predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
    board = env["board"]
    no_replies = board.legal_moves.count() == 0
    in_check = board.is_check()
    success = bool(no_replies and in_check)
    node.meta["zero_reply_in_check"] = bool(in_check)
    node.activation.value = 1.0 if success else 0.0
    return True, success


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
