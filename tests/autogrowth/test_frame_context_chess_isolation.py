from __future__ import annotations

import chess

from recon_lite import (
    FrameContext,
    FrameKind,
    Graph,
    Node,
    NodeState,
    NodeType,
    VirtualFrameExecutor,
)


def test_virtual_evaluation_deep_isolates_real_chess_board() -> None:
    board = chess.Board()
    source_fen = board.fen()
    frame = FrameContext(
        "chess-dream",
        FrameKind.VIRTUAL,
        {"board": board},
        hypothetical_action="e2e4",
    )
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    observations: list[tuple[bool, bool, str]] = []

    def mutate_runtime_board(
        _node: Node,
        env: dict[str, object],
    ) -> tuple[bool, bool]:
        runtime_board = env["board"]
        runtime_frame = env["__frame_context__"]
        assert isinstance(runtime_board, chess.Board)
        assert isinstance(runtime_frame, FrameContext)
        frame_board = runtime_frame.values["board"]
        assert isinstance(frame_board, chess.Board)
        observations.append((
            runtime_board is frame_board,
            runtime_board is board,
            runtime_board.fen(),
        ))
        runtime_board.push(chess.Move.from_uci("e2e4"))
        return True, True

    graph.add_node(Node(
        "board_terminal",
        NodeType.TERMINAL,
        predicate=mutate_runtime_board,
    ))
    graph.add_hierarchy_pair("root", "board_terminal")
    result = VirtualFrameExecutor().evaluate(graph, "root", frame)

    assert result.root_state == NodeState.CONFIRMED
    assert observations == [(True, False, source_fen)]
    assert board.fen() == source_fen
    frame_board = frame.values["board"]
    assert isinstance(frame_board, chess.Board)
    assert frame_board.fen() == source_fen
