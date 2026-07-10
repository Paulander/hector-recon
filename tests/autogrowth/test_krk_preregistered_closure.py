from __future__ import annotations

import json
from pathlib import Path

import chess
import pytest

from recon_lite_hector.nodes.stem_cell import StemCellState

from recon_lite_chess.autogrowth import krk_preregistered_closure as closure
from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
)
from recon_lite_chess.autogrowth.stage_b_ecological_discovery_probe import (
    _GraphNativeCompositeRuntime,
    _percept_signature,
    _sealed_action_keys,
)


def _board() -> chess.Board:
    return chess.Board("8/8/8/4k3/8/2K5/8/R7 w - - 0 1")


def test_canonical_orbit_is_invariant_under_d4_symmetry() -> None:
    board = _board()
    expected = closure.canonical_orbit_id(board)
    for transform in (
        chess.flip_horizontal,
        chess.flip_vertical,
        chess.flip_diagonal,
        chess.flip_anti_diagonal,
    ):
        assert closure.canonical_orbit_id(board.transform(transform)) == expected


def test_fresh_generator_persists_exact_orbit_disjoint_manifests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "closure"
    output.mkdir()
    (output / "preregistration.json").write_text(
        json.dumps({"status": "test-frozen"}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(closure, "PRIOR_POOL_PATHS", ())
    monkeypatch.setattr(
        closure,
        "QUOTAS",
        {
            "train": {3: 1},
            "validation": {4: 1},
            "final_test": {5: 1},
        },
    )
    def board(wk: int, rook: int, bk: int) -> chess.Board:
        item = chess.Board(None)
        item.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        item.set_piece_at(rook, chess.Piece(chess.ROOK, chess.WHITE))
        item.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        item.turn = chess.WHITE
        return item

    monkeypatch.setattr(
        closure,
        "_enumerate_eligible_orbit_boards",
        lambda: {
            3: [board(chess.A1, chess.H1, chess.D4)],
            4: [board(chess.A1, chess.H2, chess.E5)],
            5: [board(chess.A1, chess.H3, chess.F6)],
        },
    )
    config = closure.ClosureConfig(
        output_dir=str(output),
        maximum_generation_attempts=10000,
    )
    manifest = closure.generate_fresh_pools(config=config)

    assert {split: manifest["splits"][split]["row_count"] for split in closure.SPLITS} == {
        "train": 1,
        "validation": 1,
        "final_test": 1,
    }
    groups = {
        split: set(manifest["splits"][split]["group_ids"])
        for split in closure.SPLITS
    }
    assert groups["train"].isdisjoint(groups["validation"])
    assert groups["train"].isdisjoint(groups["final_test"])
    assert groups["validation"].isdisjoint(groups["final_test"])
    assert json.loads((output / "final_test_touch.json").read_text())["touch_count"] == 0


def test_graph_native_composite_supports_opt_in_wildcard_k_of_n() -> None:
    board = _board()
    move = sorted(board.legal_moves, key=lambda item: item.uci())[0]
    active = list(_sealed_action_keys(board, move))
    assert len(active) >= 2
    graph = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            max_mate1_positions=0,
            max_mate2_positions=0,
        )
    )
    runtime = _GraphNativeCompositeRuntime(closure._runtime_config(), graph, seed=7)
    item = runtime.spawn(
        [active[0], active[1], "action_pattern:never_present_for_test=1"],
        trigger="unit_wildcard_quorum",
        birth_segment="unit",
        birth_row_id=1,
        source_signature="different_signature",
        source_match_mode="wildcard",
        confirm_k=2,
    )
    item["state"] = "MATURE"
    runtime.cells[str(item["composite_id"])].state = StemCellState.MATURE
    result = runtime.evaluate_composite(item, board, move)

    assert result["predicate_evaluated"] is True
    assert result["confirmed"] is True
    assert item["confirm_k"] == 2
    assert item["source_match_mode"] == "wildcard"


def test_capacity_stop_persists_summary_without_touching_final(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "closure"
    output.mkdir()
    (output / "preregistration.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(closure, "PRIOR_POOL_PATHS", ())
    monkeypatch.setattr(
        closure,
        "QUOTAS",
        {
            "train": {3: 1},
            "validation": {3: 1},
            "final_test": {3: 1},
        },
    )
    monkeypatch.setattr(
        closure,
        "_enumerate_eligible_orbit_boards",
        lambda: {3: [_board()]},
    )

    with pytest.raises(closure.PoolCapacityError):
        closure.generate_fresh_pools(
            config=closure.ClosureConfig(output_dir=str(output))
        )

    summary = json.loads((output / "summary.json").read_text())
    touch = json.loads((output / "final_test_touch.json").read_text())
    assert summary["status"] == "stopped_before_experimentation"
    assert summary["measurement_gate"]["status"] == "not_run"
    assert touch == {"touch_count": 0, "touched": False, "unlocked": False}


def test_exact_cells_retain_exact_source_and_all_children_defaults() -> None:
    board = _board()
    move = sorted(board.legal_moves, key=lambda item: item.uci())[0]
    active = list(_sealed_action_keys(board, move))
    graph = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            max_mate1_positions=0,
            max_mate2_positions=0,
        )
    )
    runtime = _GraphNativeCompositeRuntime(closure._runtime_config(), graph, seed=8)
    item = runtime.spawn(
        active[:2],
        trigger="unit_exact_default",
        birth_segment="unit",
        birth_row_id=1,
        source_signature=_percept_signature(active),
    )

    assert item["source_match_mode"] == "exact"
    assert item["confirm_k"] == len(item["children"])


def test_outcome_credit_uses_only_terminal_result_and_noop_is_exact() -> None:
    board = chess.Board("8/8/8/8/8/2K5/1R6/k7 w - - 0 1")
    row = {
        "row_id": 1,
        "fen": board.fen(),
        "stratum": "test",
        "orbit_id": "test-orbit",
    }
    provider = closure._FrozenFlatScoreProvider({})
    left = closure._evaluate_rows(
        [row],
        provider=provider,
        seed=9,
        maximum_plies=8,
        split="validation",
        manifest_sha256="hash",
        arm="baseline",
        route="baseline",
    )
    right = closure._evaluate_rows(
        [row],
        provider=provider,
        seed=9,
        maximum_plies=8,
        split="validation",
        manifest_sha256="hash",
        arm="noop",
        route="noop",
    )

    assert closure._assert_noop_parity(left, right)["passed"] is True
    assert set(left["reward_by_row"].values()) <= {-1.0, 0.0, 1.0}
    assert left["runner_config"]["judge_version"] == "actual_terminal_game_result.v1"


def test_paired_statistics_report_sign_balance_and_noninferiority() -> None:
    comparison = closure._paired_comparison(
        [True] * 9 + [False],
        [False] * 9 + [True],
        alpha=0.05,
        noninferiority_margin=-6 / 256,
    )

    assert comparison["favorable"] == 9
    assert comparison["unfavorable"] == 1
    assert comparison["raw_p"] < 0.05
    assert comparison["balance_wilson_low"] > 0.5
