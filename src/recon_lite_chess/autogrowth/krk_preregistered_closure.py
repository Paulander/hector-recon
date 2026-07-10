"""The single preregistered v1 KRK ecological closure.

This is intentionally a bounded measurement instrument.  It reuses the frozen
Stage-B flat host and the graph-native composite runtime, but it does not add a
new curriculum, authored skill, or candidate lifecycle.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from hashlib import sha256
from itertools import combinations
import json
import math
from pathlib import Path
import random
from statistics import NormalDist
from typing import Any, Iterable, Mapping, Sequence

import chess

from recon_lite_hector.nodes.stem_cell import StemCellState

from .foundation_curriculum import (
    _forced_mate_in_two_first_moves,
    _mate_moves,
    _valid_foundation_board,
)
from .measurement_integrity import (
    CounterfactualSnapshot,
    apply_live_routing_weight,
    holm_adjusted_pvalues,
    live_population_item,
    paired_binary_outcomes,
)
from .native_single_graph_curriculum import NativeReConKRKGraph, NativeSingleGraphConfig
from .stage_b_ecological_discovery_probe import (
    StageBEcologicalDiscoveryConfig,
    _GraphNativeCompositeRuntime,
    _after_move_repetition_key,
    _generic_child_pool,
    _legal_without_third_repetition,
    _load_weight_table,
    _percept_signature,
    _position_repetition_key,
    _sealed_action_keys,
    _white_rook_square,
    fence_established_geometry,
)


DEFAULT_OUTPUT_DIR = Path("reports/autogrowth/krk_preregistered_closure")
PREREGISTRATION_NAME = "preregistration.json"
SPLITS = ("train", "validation", "final_test")
EXPERIMENT_SEEDS = (20273101, 20273102, 20273103, 20273104, 20273105)
FLAT_HOST_BY_SEED = {
    20273101: 20272911,
    20273102: 20272912,
    20273103: 20272913,
    20273104: 20272911,
    20273105: 20272912,
}
FLAT_WEIGHT_DIR = Path(
    "reports/autogrowth/clean_slate_krk/phase2_9a_action_firewall"
)
PRIOR_POOL_PATHS = (
    Path("reports/autogrowth/clean_slate_krk/phase2_9_overnight/stage_a_rows.json"),
    Path("reports/autogrowth/clean_slate_krk/phase2_9_overnight/stage_b_rows.json"),
    Path("reports/autogrowth/clean_slate_krk/phase2_9_overnight/stage_c_fence_rung_starts.json"),
    Path("reports/autogrowth/clean_slate_krk/phase2_9_overnight/stage_c_general_starts.json"),
    Path("reports/autogrowth/clean_slate_krk/phase2_9_overnight/stage_c_mate_lte2_starts.json"),
)
QUOTAS = {
    "train": {3: 52, 4: 51, 5: 51, 6: 51, 7: 51},
    "validation": {3: 51, 4: 52, 5: 51, 6: 51, 7: 51},
    "final_test": {3: 51, 4: 51, 5: 52, 6: 51, 7: 51},
}
ROW_START = {"train": 100000, "validation": 200000, "final_test": 300000}


@dataclass(frozen=True)
class ClosureConfig:
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    pool_seed: int = 20273100
    experiment_seeds: tuple[int, ...] = EXPERIMENT_SEEDS
    maximum_plies: int = 128
    maximum_cells_per_topology: int = 32
    minimum_train_support: int = 4
    minimum_firing_rows: int = 8
    maximum_generation_attempts: int = 1_000_000
    l_doses: tuple[float, ...] = (1.0, 3.0, 9.0, 27.0)
    alpha: float = 0.05
    noninferiority_margin: float = -6.0 / 256.0


@dataclass(frozen=True)
class CellSpec:
    spec_id: str
    topology: str
    children: tuple[str, ...]
    source_signature: str
    source_match_mode: str
    confirm_k: int
    train_support: int
    nomination_score: float
    member_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["children"] = list(self.children)
        payload["member_ids"] = list(self.member_ids)
        return payload


@dataclass
class SeedState:
    seed: int
    flat_seed: int
    weights: Mapping[str, float]
    train_evaluation: dict[str, Any]
    validation_baseline: dict[str, Any]
    validation_noop: dict[str, Any]
    specs: dict[str, list[CellSpec]]
    runtime: _GraphNativeCompositeRuntime
    snapshot: CounterfactualSnapshot
    snapshot_sha256: str
    spec_to_composite: dict[str, str]
    coverage: dict[str, Any]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value: Any) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _piece_squares(board: chess.Board) -> tuple[int, int, int]:
    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    rook = _white_rook_square(board)
    if wk is None or bk is None or rook is None:
        raise ValueError("not a K+R versus K board")
    return wk, rook, bk


def _d4_square_tuples(board: chess.Board) -> tuple[tuple[int, int, int], ...]:
    def transform(square: int, variant: int) -> int:
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        coords = (
            (file, rank),
            (7 - file, rank),
            (file, 7 - rank),
            (7 - file, 7 - rank),
            (rank, file),
            (7 - rank, file),
            (rank, 7 - file),
            (7 - rank, 7 - file),
        )
        out_file, out_rank = coords[variant]
        return chess.square(out_file, out_rank)

    pieces = _piece_squares(board)
    return tuple(
        tuple(transform(square, variant) for square in pieces)
        for variant in range(8)
    )


def canonical_orbit_id(board: chess.Board) -> str:
    canonical = min(_d4_square_tuples(board))
    return f"krk_d4_{_hash(canonical)[:20]}"


def _extract_fens(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for child in value.values():
            yield from _extract_fens(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            yield from _extract_fens(child)
    elif isinstance(value, str) and value.count("/") == 7:
        try:
            chess.Board(value)
        except ValueError:
            return
        yield value


def _prior_exclusions() -> tuple[set[str], set[str]]:
    fens: set[str] = set()
    orbits: set[str] = set()
    for path in PRIOR_POOL_PATHS:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for fen in _extract_fens(payload):
            board = chess.Board(fen)
            if _white_rook_square(board) is None:
                continue
            fens.add(board.fen())
            orbits.add(canonical_orbit_id(board))
    return fens, orbits


def _stratum(board: chess.Board) -> int:
    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    if wk is None or bk is None:
        return -1
    return chess.square_distance(wk, bk)


def _eligible_stage_b_board(board: chess.Board) -> bool:
    distance = _stratum(board)
    return bool(
        _valid_foundation_board(board)
        and distance in {3, 4, 5, 6, 7}
        and fence_established_geometry(board)
        and not _mate_moves(board)
        and not _forced_mate_in_two_first_moves(board)
    )


class PoolCapacityError(RuntimeError):
    """The frozen population cannot satisfy the preregistered split quotas."""


def _enumerate_eligible_orbit_boards() -> dict[int, list[chess.Board]]:
    by_stratum: dict[int, list[chess.Board]] = defaultdict(list)
    seen_orbits: set[str] = set()
    for wk in chess.SQUARES:
        for rook in chess.SQUARES:
            if rook == wk:
                continue
            for bk in chess.SQUARES:
                if bk in {wk, rook}:
                    continue
                board = chess.Board(None)
                board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                board.set_piece_at(rook, chess.Piece(chess.ROOK, chess.WHITE))
                board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
                board.turn = chess.WHITE
                board.castling_rights = 0
                board.ep_square = None
                board.halfmove_clock = 0
                board.fullmove_number = 1
                if not _eligible_stage_b_board(board):
                    continue
                orbit_id = canonical_orbit_id(board)
                if orbit_id in seen_orbits:
                    continue
                seen_orbits.add(orbit_id)
                by_stratum[_stratum(board)].append(board)
    return by_stratum


def generate_fresh_pools(
    *,
    config: ClosureConfig = ClosureConfig(),
    force: bool = False,
) -> dict[str, Any]:
    """Generate the frozen pools without loading FINAL-TEST into selection code."""

    output_dir = Path(config.output_dir)
    prereg_path = output_dir / PREREGISTRATION_NAME
    prereg_bytes = prereg_path.read_bytes()
    prereg_sha = sha256(prereg_bytes).hexdigest()
    manifest_path = output_dir / "split_manifest.json"
    if manifest_path.exists() and not force:
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    prior_fens, prior_orbits = _prior_exclusions()
    population = _enumerate_eligible_orbit_boards()
    available = {
        distance: [
            board
            for board in population.get(distance, ())
            if board.fen() not in prior_fens
            and canonical_orbit_id(board) not in prior_orbits
        ]
        for distance in sorted({distance for quotas in QUOTAS.values() for distance in quotas})
    }
    required = {
        distance: sum(QUOTAS[split].get(distance, 0) for split in SPLITS)
        for distance in available
    }
    shortages = {
        str(distance): {
            "required": required[distance],
            "available": len(available[distance]),
            "shortfall": required[distance] - len(available[distance]),
        }
        for distance in available
        if len(available[distance]) < required[distance]
    }
    if shortages:
        failure = {
            "schema_version": "krk_closure_pool_capacity_failure.v1",
            "stop_rule": "fresh_exact_stratified_orbit_disjoint_pools_cannot_be_generated",
            "preregistration_sha256": prereg_sha,
            "generator_seed": config.pool_seed,
            "raw_eligible_orbits_by_stratum": {
                str(distance): len(population.get(distance, ()))
                for distance in sorted(available)
            },
            "available_after_named_prior_orbit_exclusion": {
                str(distance): len(available[distance])
                for distance in sorted(available)
            },
            "required_across_splits": {
                str(distance): required[distance] for distance in sorted(required)
            },
            "shortages": shortages,
            "prior_exact_fen_exclusion_count": len(prior_fens),
            "prior_orbit_exclusion_count": len(prior_orbits),
            "final_test_touch_count": 0,
            "experimental_arms_executed": False,
        }
        _write_json(output_dir / "pool_generation_failure.json", failure)
        _write_json(
            output_dir / "final_test_touch.json",
            {"touch_count": 0, "touched": False, "unlocked": False},
        )
        _write_json(
            output_dir / "summary.json",
            {
                "schema_version": "krk_preregistered_ecological_closure_result.v1",
                "status": "stopped_before_experimentation",
                "stop_rule": failure["stop_rule"],
                "pool_generation": failure,
                "arm_by_seed_table": [
                    {
                        "seed": seed,
                        "frozen_host_baseline": "not_run",
                        "noop": "not_run",
                        "exact_point": "not_run",
                        "signature_coarsened": "not_run",
                        "widened": "not_run",
                        "matched_random": "not_run",
                        "constructed_ceiling": "not_run",
                    }
                    for seed in config.experiment_seeds
                ],
                "measurement_gate": {"status": "not_run"},
                "coverage_gate": {"status": "not_run"},
                "selectivity_gate": {"status": "not_run"},
                "heldout_causal_gate": {"status": "not_run"},
                "final_test": {
                    "touched": False,
                    "touch_count": 0,
                    "status": "never_unlocked",
                },
                "interpretation": (
                    "The preregistered fresh-pool population is too small after the "
                    "frozen orbit exclusions. This is an instrument/pool-capacity stop, "
                    "not evidence for or against ecological composition."
                ),
                "krk_freeze": (
                    "This was the single authorized v1 KRK ecological closure. KRK is "
                    "now frozen as a regression/transfer benchmark; no rescue closure "
                    "is authorized."
                ),
                "next_research_question": (
                    "KPK opposition and tempo under a fresh domain-specific preregistration."
                ),
            },
        )
        raise PoolCapacityError(_canonical_json(failure))

    rng = random.Random(config.pool_seed)
    for boards in available.values():
        rng.shuffle(boards)
    accepted: dict[str, list[dict[str, Any]]] = {split: [] for split in SPLITS}
    counts: dict[str, Counter[int]] = {split: Counter() for split in SPLITS}
    for distance in sorted(available):
        cursor = 0
        for split in SPLITS:
            quota = QUOTAS[split].get(distance, 0)
            for board in available[distance][cursor : cursor + quota]:
                orbit_id = canonical_orbit_id(board)
                accepted[split].append(
                    {
                        "row_id": -1,
                        "fen": board.fen(),
                        "stratum": f"wk_bk_chebyshev_{distance}",
                        "stratum_distance": distance,
                        "group_id": orbit_id,
                        "orbit_id": orbit_id,
                    }
                )
                counts[split][distance] += 1
            cursor += quota
    for split in SPLITS:
        rng.shuffle(accepted[split])
        for index, row in enumerate(accepted[split]):
            row["row_id"] = ROW_START[split] + index

    split_manifest: dict[str, Any] = {
        "schema_version": "krk_closure_split_manifest.v1",
        "preregistration_sha256": prereg_sha,
        "generator_seed": config.pool_seed,
        "generation_method": "exact eligible-orbit enumeration then seed-shuffle sampling without replacement",
        "prior_exact_fen_exclusion_count": len(prior_fens),
        "prior_orbit_exclusion_count": len(prior_orbits),
        "splits": {},
        "cross_split_exact_disjoint": True,
        "cross_split_orbit_disjoint": True,
        "final_test_touch_count": 0,
    }
    for split in SPLITS:
        payload = {
            "schema_version": "krk_closure_rows.v1",
            "split": split,
            "preregistration_sha256": prereg_sha,
            "generator_seed": config.pool_seed,
            "rows": accepted[split],
        }
        digest = _hash(payload)
        filename = f"{split}_rows.json"
        _write_json(output_dir / filename, payload)
        split_manifest["splits"][split] = {
            "path": str(output_dir / filename),
            "sha256": digest,
            "row_count": len(accepted[split]),
            "row_ids": [row["row_id"] for row in accepted[split]],
            "group_ids": [row["group_id"] for row in accepted[split]],
            "stratum_counts": {
                str(distance): counts[split][distance] for distance in sorted(QUOTAS[split])
            },
        }
    _validate_generated_manifest(split_manifest, accepted)
    _write_json(manifest_path, split_manifest)
    _write_json(
        output_dir / "final_test_touch.json",
        {"touch_count": 0, "touched": False, "unlocked": False},
    )
    return split_manifest


def _validate_generated_manifest(
    manifest: Mapping[str, Any],
    rows: Mapping[str, Sequence[Mapping[str, Any]]],
) -> None:
    all_fens: set[str] = set()
    all_orbits: set[str] = set()
    for split in SPLITS:
        split_rows = list(rows[split])
        expected_size = sum(QUOTAS[split].values())
        if len(split_rows) != expected_size:
            raise AssertionError(f"{split} does not contain {expected_size} rows")
        observed = Counter(int(row["stratum_distance"]) for row in split_rows)
        if dict(observed) != QUOTAS[split]:
            raise AssertionError(f"{split} quotas differ: {dict(observed)}")
        fens = {str(row["fen"]) for row in split_rows}
        orbits = {str(row["orbit_id"]) for row in split_rows}
        if len(fens) != expected_size or len(orbits) != expected_size:
            raise AssertionError(f"{split} contains duplicate exact rows or orbits")
        if all_fens.intersection(fens) or all_orbits.intersection(orbits):
            raise AssertionError("cross-split exact or orbit leakage")
        all_fens.update(fens)
        all_orbits.update(orbits)
        if len(manifest["splits"][split]["row_ids"]) != expected_size:
            raise AssertionError("manifest row IDs incomplete")


def _load_split(output_dir: Path, manifest: Mapping[str, Any], split: str) -> list[dict[str, Any]]:
    info = manifest["splits"][split]
    payload = json.loads(Path(info["path"]).read_text(encoding="utf-8"))
    if _hash(payload) != str(info["sha256"]):
        raise AssertionError(f"{split} manifest hash mismatch")
    return list(payload["rows"])


class _FrozenFlatScoreProvider:
    def __init__(self, weights: Mapping[str, float]) -> None:
        self.weights = dict(weights)

    def __call__(self, board: chess.Board, _counts: Mapping[Any, int]) -> Mapping[str, float]:
        return {
            move.uci(): sum(self.weights.get(key, 0.0) for key in _sealed_action_keys(board, move))
            for move in board.legal_moves
        }


def _flat_move(
    board: chess.Board,
    counts: Mapping[Any, int],
    provider: _FrozenFlatScoreProvider,
) -> chess.Move | None:
    legal = _legal_without_third_repetition(board, counts)
    if not legal:
        legal = tuple(sorted(board.legal_moves, key=lambda move: move.uci()))
    if not legal:
        return None
    scores = provider(board, counts)
    return max(legal, key=lambda move: (float(scores.get(move.uci(), 0.0)), move.uci()))


def deterministic_greedy_black(board: chess.Board) -> chess.Move | None:
    if board.turn != chess.BLACK or board.is_game_over(claim_draw=False):
        return None
    ranked: list[tuple[tuple[int, int, int, int, str], chess.Move]] = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        successor = board.copy(stack=False)
        successor.push(move)
        rook_captured = int(_white_rook_square(successor) is None)
        bk = successor.king(chess.BLACK)
        wk = successor.king(chess.WHITE)
        king_distance = 0 if bk is None or wk is None else chess.square_distance(bk, wk)
        centrality = 0 if bk is None else min(
            chess.square_file(bk),
            7 - chess.square_file(bk),
            chess.square_rank(bk),
            7 - chess.square_rank(bk),
        )
        ranked.append(
            (
                (
                    rook_captured,
                    king_distance,
                    centrality,
                    successor.legal_moves.count(),
                    move.uci(),
                ),
                move,
            )
        )
    return max(ranked, key=lambda item: item[0])[1] if ranked else None


def _terminal_result(board: chess.Board) -> tuple[str, bool, float] | None:
    if _white_rook_square(board) is None:
        return "rook_lost", False, -1.0
    if not board.is_game_over(claim_draw=True):
        return None
    outcome = board.outcome(claim_draw=True)
    if outcome is not None and outcome.winner is chess.WHITE:
        return "white_checkmate_win", True, 1.0
    if outcome is not None and outcome.winner is chess.BLACK:
        return "black_win", False, -1.0
    return "draw", False, 0.0


def _rollout(
    row: Mapping[str, Any],
    *,
    provider: _FrozenFlatScoreProvider,
    seed: int,
    maximum_plies: int,
    selector: Any | None = None,
) -> dict[str, Any]:
    board = chess.Board(str(row["fen"]))
    counts: Counter[Any] = Counter(
        {_position_repetition_key(board): 1, board._transposition_key(): 1}
    )
    actions: list[str] = []
    frames: list[dict[str, Any]] = []
    active_ids: set[str] = set()
    predicate_ids: set[str] = set()
    responsible_ids: set[str] = set()
    endpoint = "horizon"
    success = False
    reward = 0.0
    for ply in range(maximum_plies):
        terminal = _terminal_result(board)
        if terminal is not None:
            endpoint, success, reward = terminal
            break
        if board.turn is chess.WHITE:
            if selector is None:
                move = _flat_move(board, counts, provider)
                decision: dict[str, Any] = {
                    "move": move,
                    "active_ids": (),
                    "predicate_ids": (),
                    "responsible_ids": (),
                }
            else:
                decision = selector(board, counts, int(row["row_id"]), ply)
                move = decision.get("move")
            if move is None or move not in board.legal_moves:
                endpoint, success, reward = "illegal", False, -1.0
                break
            keys = tuple(_sealed_action_keys(board, move))
            frames.append(
                {
                    "row_id": int(row["row_id"]),
                    "ply": ply,
                    "fen": board.fen(),
                    "move": move.uci(),
                    "keys": list(keys),
                    "source_signature": _percept_signature(keys),
                }
            )
            actions.append(move.uci())
            active_ids.update(map(str, decision.get("active_ids", ())))
            predicate_ids.update(map(str, decision.get("predicate_ids", ())))
            responsible_ids.update(map(str, decision.get("responsible_ids", ())))
        else:
            move = deterministic_greedy_black(board)
            if move is None:
                terminal = _terminal_result(board)
                if terminal is None:
                    endpoint, success, reward = "illegal_black", False, -1.0
                else:
                    endpoint, success, reward = terminal
                break
        if int(counts.get(_after_move_repetition_key(board, move), 0)) >= 2:
            endpoint, success, reward = "draw", False, 0.0
            break
        board.push(move)
        counts[_position_repetition_key(board)] += 1
        counts[board._transposition_key()] += 1
    trace_digest = _hash(
        {
            "row_id": int(row["row_id"]),
            "actions": actions,
            "endpoint": endpoint,
            "active": sorted(active_ids),
            "predicate": sorted(predicate_ids),
            "responsible": sorted(responsible_ids),
            "seed": seed,
        }
    )
    return {
        "row_id": int(row["row_id"]),
        "success": success,
        "reward": reward,
        "endpoint": endpoint,
        "selected_actions": actions,
        "frames": frames,
        "active_composite_ids": sorted(active_ids),
        "predicate_evaluated_ids": sorted(predicate_ids),
        "selected_responsible_ids": sorted(responsible_ids),
        "trace_digest": trace_digest,
    }


def _evaluate_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    provider: _FrozenFlatScoreProvider,
    seed: int,
    maximum_plies: int,
    split: str,
    manifest_sha256: str,
    arm: str,
    route: str,
    dose: float | None = None,
    selector: Any | None = None,
    snapshot_sha256: str = "frozen_host_no_cells",
    interventions: Mapping[str, Mapping[str, float]] | None = None,
) -> dict[str, Any]:
    results = [
        _rollout(
            row,
            provider=provider,
            seed=seed,
            maximum_plies=maximum_plies,
            selector=selector,
        )
        for row in rows
    ]
    runner_config = {
        "black_reply_policy": "deterministic_greedy_black",
        "seed": seed,
        "seed_schedule": "fixed experiment seed; frozen manifest order",
        "judge_version": "actual_terminal_game_result.v1",
        "fence_check_timing": "recognizer_not_used_for_credit_or_termination",
        "tick_budget": 80,
        "tie_break": "score_then_descending_uci",
        "maximum_plies": maximum_plies,
        "deterministic_row_order": [int(row["row_id"]) for row in rows],
    }
    runner_hash = _hash(runner_config)
    records = []
    for result, source in zip(results, rows, strict=True):
        records.append(
            {
                "split": split,
                "manifest_sha256": manifest_sha256,
                "row_id": int(source["row_id"]),
                "fen": str(source["fen"]),
                "stratum": str(source["stratum"]),
                "orbit_id": str(source["orbit_id"]),
                "experiment_seed": seed,
                "flat_host_seed": FLAT_HOST_BY_SEED.get(seed),
                "opponent_policy": "deterministic_greedy_black",
                "arm": arm,
                "route": route,
                "dose": dose,
                "selected_actions": result["selected_actions"],
                "success": result["success"],
                "terminal_endpoint": result["endpoint"],
                "active_composite_ids": result["active_composite_ids"],
                "predicate_evaluated_ids": result["predicate_evaluated_ids"],
                "selected_responsible_ids": result["selected_responsible_ids"],
                "requested_intervention": dict(interventions or {}),
                "observed_intervention": dict(interventions or {}),
                "trace_digest": result["trace_digest"],
                "runner_config_sha256": runner_hash,
                "snapshot_sha256": snapshot_sha256,
            }
        )
    return {
        "arm": arm,
        "route": route,
        "dose": dose,
        "split": split,
        "manifest_sha256": manifest_sha256,
        "seed": seed,
        "wins": sum(int(result["success"]) for result in results),
        "reward_sum": sum(float(result["reward"]) for result in results),
        "endpoint_counts": dict(sorted(Counter(result["endpoint"] for result in results).items())),
        "success_by_row": {str(result["row_id"]): bool(result["success"]) for result in results},
        "reward_by_row": {str(result["row_id"]): float(result["reward"]) for result in results},
        "action_by_row": {str(result["row_id"]): result["selected_actions"] for result in results},
        "endpoint_by_row": {str(result["row_id"]): result["endpoint"] for result in results},
        "trace_digest_by_row": {str(result["row_id"]): result["trace_digest"] for result in results},
        "frames": [frame for result in results for frame in result["frames"]],
        "row_records": records,
        "runner_config": runner_config,
    }


def _assert_noop_parity(
    baseline: Mapping[str, Any],
    noop: Mapping[str, Any],
) -> dict[str, Any]:
    fields = (
        "success_by_row",
        "reward_by_row",
        "action_by_row",
        "endpoint_by_row",
        "trace_digest_by_row",
    )
    # Trace digests include neither the arm name nor the no-op label.
    for field in fields:
        if baseline[field] != noop[field]:
            raise AssertionError(f"no-op parity failed for {field}")
    return {"passed": True, "fields": list(fields), "paired_difference": 0.0}


def _action_pairs(keys: Iterable[str]) -> tuple[tuple[str, str], ...]:
    action_keys = [
        key for key in _generic_child_pool(keys)
        if str(key).startswith("action_pattern:")
    ][:6]
    return tuple(combinations(action_keys, 2))


def _nominees(
    frames: Sequence[Mapping[str, Any]],
    *,
    reward_by_row: Mapping[str, float],
    topology: str,
    minimum_support: int,
    limit: int,
) -> list[CellSpec]:
    samples: dict[Any, list[float]] = defaultdict(list)
    all_rewards: list[float] = []
    for frame in frames:
        reward = float(reward_by_row[str(frame["row_id"])])
        all_rewards.append(reward)
        for pair in _action_pairs(frame["keys"]):
            key: Any = (
                (str(frame["source_signature"]), pair)
                if topology == "exact_point"
                else pair
            )
            samples[key].append(reward)
    global_mean = sum(all_rewards) / max(1, len(all_rewards))
    ranked: list[tuple[float, int, str, CellSpec]] = []
    for key, rewards in samples.items():
        support = len(rewards)
        if support < minimum_support:
            continue
        score = sum(rewards) / support - global_mean
        if score <= 0.0:
            continue
        if topology == "exact_point":
            signature, pair = key
            source_mode = "exact"
        else:
            signature, pair = "*", key
            source_mode = "wildcard"
        stable = _hash([topology, signature, pair])
        spec = CellSpec(
            spec_id=f"{topology}_{stable[:16]}",
            topology=topology,
            children=tuple(pair),
            source_signature=str(signature),
            source_match_mode=source_mode,
            confirm_k=2,
            train_support=support,
            nomination_score=score,
        )
        ranked.append((score, support, spec.spec_id, spec))
    ranked.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return [item[-1] for item in ranked[:limit]]


def _widen(point_specs: Sequence[CellSpec], *, limit: int) -> list[CellSpec]:
    remaining = list(point_specs)
    widened: list[CellSpec] = []
    while remaining and len(widened) < limit:
        anchor = remaining.pop(0)
        children = set(anchor.children)
        members = [anchor]
        kept: list[CellSpec] = []
        for candidate in remaining:
            union = children.union(candidate.children)
            if children.intersection(candidate.children) and len(union) <= 6:
                children = union
                members.append(candidate)
            else:
                kept.append(candidate)
        remaining = kept
        ordered_children = tuple(sorted(children))
        stable = _hash(["widened", ordered_children, [member.spec_id for member in members]])
        widened.append(
            CellSpec(
                spec_id=f"widened_{stable[:16]}",
                topology="widened",
                children=ordered_children,
                source_signature="*",
                source_match_mode="wildcard",
                confirm_k=2,
                train_support=sum(member.train_support for member in members),
                nomination_score=max(member.nomination_score for member in members),
                member_ids=tuple(member.spec_id for member in members),
            )
        )
    return widened


def _spec_matches(spec: CellSpec, frame: Mapping[str, Any]) -> bool:
    if (
        spec.source_match_mode == "exact"
        and spec.source_signature != str(frame["source_signature"])
    ):
        return False
    active = set(map(str, frame["keys"]))
    return sum(child in active for child in spec.children) >= spec.confirm_k


def _frequency_deciles(frames: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    frequencies = Counter(
        str(key)
        for frame in frames
        for key in frame["keys"]
        if str(key).startswith("action_pattern:")
    )
    ordered = sorted(frequencies, key=lambda key: (frequencies[key], key))
    return {
        key: min(9, index * 10 // max(1, len(ordered)))
        for index, key in enumerate(ordered)
    }


def _matched_random_specs(
    widened: Sequence[CellSpec],
    *,
    train_frames: Sequence[Mapping[str, Any]],
    validation_frames: Sequence[Mapping[str, Any]],
    seed: int,
) -> list[CellSpec]:
    deciles = _frequency_deciles(train_frames)
    by_decile: dict[int, list[str]] = defaultdict(list)
    for key, decile in deciles.items():
        by_decile[decile].append(key)
    all_keys = sorted(deciles)
    controls: list[CellSpec] = []
    for rank, target in enumerate(widened):
        target_rate = sum(_spec_matches(target, frame) for frame in validation_frames)
        target_deciles = [deciles.get(child, 0) for child in target.children]
        draws: list[tuple[int, str, tuple[str, ...]]] = []
        for draw_index in range(64):
            rng = random.Random(seed + 41000 + rank * 1000 + draw_index)
            chosen: list[str] = []
            for decile in target_deciles:
                pool = [key for key in by_decile.get(decile, all_keys) if key not in chosen]
                if not pool:
                    pool = [key for key in all_keys if key not in chosen]
                if not pool:
                    break
                chosen.append(pool[rng.randrange(len(pool))])
            if len(chosen) != len(target.children):
                continue
            children = tuple(sorted(chosen))
            probe = CellSpec(
                spec_id="probe",
                topology="matched_random",
                children=children,
                source_signature="*",
                source_match_mode="wildcard",
                confirm_k=target.confirm_k,
                train_support=0,
                nomination_score=0.0,
            )
            firing = sum(_spec_matches(probe, frame) for frame in validation_frames)
            draws.append((abs(firing - target_rate), _hash(children), children))
        if not draws:
            continue
        _, stable, children = min(draws)
        controls.append(
            CellSpec(
                spec_id=f"matched_random_{stable[:16]}",
                topology="matched_random",
                children=children,
                source_signature="*",
                source_match_mode="wildcard",
                confirm_k=target.confirm_k,
                train_support=0,
                nomination_score=0.0,
                member_ids=(target.spec_id,),
            )
        )
    return controls


def build_topology_specs(
    train_evaluation: Mapping[str, Any],
    validation_baseline: Mapping[str, Any],
    *,
    config: ClosureConfig,
    seed: int,
) -> dict[str, list[CellSpec]]:
    points = _nominees(
        train_evaluation["frames"],
        reward_by_row=train_evaluation["reward_by_row"],
        topology="exact_point",
        minimum_support=config.minimum_train_support,
        limit=config.maximum_cells_per_topology,
    )
    signatures = _nominees(
        train_evaluation["frames"],
        reward_by_row=train_evaluation["reward_by_row"],
        topology="signature_coarsened",
        minimum_support=config.minimum_train_support,
        limit=config.maximum_cells_per_topology,
    )
    widened = _widen(points, limit=config.maximum_cells_per_topology)
    random_specs = _matched_random_specs(
        widened,
        train_frames=train_evaluation["frames"],
        validation_frames=validation_baseline["frames"],
        seed=seed,
    )
    return {
        "exact_point": points,
        "signature_coarsened": signatures,
        "widened": widened,
        "matched_random": random_specs,
    }


def _runtime_config() -> StageBEcologicalDiscoveryConfig:
    return StageBEcologicalDiscoveryConfig(
        ecology_mode="stem_cell_graph",
        max_advisory_weight=27.0,
        real_native_engine_max_ticks=80,
        real_native_probation_enabled=True,
        real_native_conditional_gate_enabled=True,
        real_native_conditional_gate_mode="action_pattern_eligibility",
        real_native_conditional_gate_states=("MATURE",),
    )


def _materialize_runtime(
    specs: Mapping[str, Sequence[CellSpec]],
    *,
    seed: int,
) -> tuple[_GraphNativeCompositeRuntime, dict[str, str]]:
    graph = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            max_mate1_positions=0,
            max_mate2_positions=0,
        )
    )
    runtime = _GraphNativeCompositeRuntime(_runtime_config(), graph, seed=seed)
    mapping: dict[str, str] = {}
    for topology in ("exact_point", "signature_coarsened", "widened", "matched_random"):
        for rank, spec in enumerate(specs[topology]):
            item = runtime.spawn(
                spec.children,
                trigger=f"krk_closure_{topology}_{seed}_{rank}",
                birth_segment="krk_preregistered_closure_train",
                birth_row_id=-1,
                source_signature=spec.source_signature,
                source_match_mode=spec.source_match_mode,
                confirm_k=spec.confirm_k,
            )
            cid = str(item["composite_id"])
            mapping[spec.spec_id] = cid
            item["state"] = "MATURE"
            item["routing_weight_override"] = 0.0
            item["closure_topology"] = topology
            item["closure_spec_id"] = spec.spec_id
            runtime.cells[cid].state = StemCellState.MATURE
            node = graph.graph.nodes[str(item["node_id"])]
            node.meta["stem_cell_state"] = StemCellState.MATURE.name
            node.meta["closure_topology"] = topology
            node.meta["closure_spec_id"] = spec.spec_id
    return runtime, mapping


def _snapshot_digest(
    runtime: _GraphNativeCompositeRuntime,
    mapping: Mapping[str, str],
) -> str:
    return _hash(
        {
            "mapping": dict(sorted(mapping.items())),
            "population": {
                cid: {
                    "children": item["children"],
                    "source_signature": item["source_signature"],
                    "source_match_mode": item.get("source_match_mode"),
                    "confirm_k": item.get("confirm_k"),
                    "state": item["state"],
                    "routing_weight_override": item.get("routing_weight_override"),
                }
                for cid, item in sorted(runtime.population.items())
            },
            "nodes": sorted(runtime.native_graph.graph.nodes),
            "edges": [
                (edge.src, edge.dst, edge.ltype.name, edge.w)
                for edge in runtime.native_graph.graph.edges
            ],
        }
    )


def _formal_coverage(
    runtime: _GraphNativeCompositeRuntime,
    specs: Mapping[str, Sequence[CellSpec]],
    mapping: Mapping[str, str],
    frames: Sequence[Mapping[str, Any]],
    *,
    minimum_firing_rows: int,
) -> dict[str, Any]:
    coverage: dict[str, Any] = {}
    for topology, family in specs.items():
        rows_by_spec: dict[str, set[int]] = {spec.spec_id: set() for spec in family}
        evaluated_by_spec: Counter[str] = Counter()
        for spec in family:
            cid = mapping[spec.spec_id]
            item = live_population_item(runtime, cid)
            seen_rows: set[int] = set()
            for frame in frames:
                row_id = int(frame["row_id"])
                if row_id in seen_rows or not _spec_matches(spec, frame):
                    continue
                seen_rows.add(row_id)
                board = chess.Board(str(frame["fen"]))
                move = chess.Move.from_uci(str(frame["move"]))
                result = runtime.evaluate_composite(item, board, move)
                if result["predicate_evaluated"]:
                    evaluated_by_spec[spec.spec_id] += 1
                if result["confirmed"]:
                    rows_by_spec[spec.spec_id].add(row_id)
        adequate_ids = [
            spec_id
            for spec_id, row_ids in rows_by_spec.items()
            if len(row_ids) >= minimum_firing_rows
            and evaluated_by_spec[spec_id] >= minimum_firing_rows
        ]
        nominee_count = len(family)
        coverage[topology] = {
            "nominee_count": nominee_count,
            "evaluated_nominee_count": sum(
                int(evaluated_by_spec[spec.spec_id] > 0) for spec in family
            ),
            "adequate_cell_count": len(adequate_ids),
            "adequate_cell_fraction": (
                0.0 if nominee_count == 0 else len(adequate_ids) / nominee_count
            ),
            "adequate_cell_ids": adequate_ids,
            "firing_rows_by_cell": {
                spec_id: len(row_ids) for spec_id, row_ids in rows_by_spec.items()
            },
            "predicate_evaluations_by_cell": dict(evaluated_by_spec),
            "firing_row_fraction": (
                0.0
                if not frames
                else len(set().union(*rows_by_spec.values())) / len({int(frame["row_id"]) for frame in frames})
            ),
        }
    return coverage


def _route_selector(
    runtime: _GraphNativeCompositeRuntime,
    provider: _FrozenFlatScoreProvider,
    enabled_ids: set[str],
    *,
    route: str,
    seed: int,
) -> Any:
    def choose(
        board: chess.Board,
        counts: Mapping[Any, int],
        row_id: int,
        ply: int,
    ) -> dict[str, Any]:
        legal = _legal_without_third_repetition(board, counts)
        if not legal:
            legal = tuple(sorted(board.legal_moves, key=lambda move: move.uci()))
        base_scores = provider(board, counts)
        scored: list[dict[str, Any]] = []
        for move in legal:
            keys = tuple(_sealed_action_keys(board, move))
            frame = {
                "row_id": row_id,
                "ply": ply,
                "fen": board.fen(),
                "move": move.uci(),
                "keys": keys,
                "source_signature": _percept_signature(keys),
            }
            active: list[str] = []
            evaluated: list[str] = []
            additive = 0.0
            for cid in sorted(enabled_ids):
                item = live_population_item(runtime, cid)
                spec = CellSpec(
                    spec_id=str(item["closure_spec_id"]),
                    topology=str(item["closure_topology"]),
                    children=tuple(map(str, item["children"])),
                    source_signature=str(item["source_signature"]),
                    source_match_mode=str(item.get("source_match_mode", "exact")),
                    confirm_k=int(item.get("confirm_k", len(item["children"]))),
                    train_support=0,
                    nomination_score=0.0,
                )
                if not _spec_matches(spec, frame):
                    continue
                evaluation = runtime.evaluate_composite(item, board, move)
                if evaluation["predicate_evaluated"]:
                    evaluated.append(cid)
                if evaluation["confirmed"]:
                    active.append(cid)
                    if route == "L":
                        additive += float(item.get("routing_weight_override", 0.0))
            scored.append(
                {
                    "move": move,
                    "base_score": float(base_scores.get(move.uci(), 0.0)),
                    "score": float(base_scores.get(move.uci(), 0.0)) + additive,
                    "active": active,
                    "evaluated": evaluated,
                }
            )
        if route == "G" and any(item["active"] for item in scored):
            candidates = [item for item in scored if item["active"]]
            selected = max(candidates, key=lambda item: (item["base_score"], item["move"].uci()))
        else:
            selected = max(scored, key=lambda item: (item["score"], item["move"].uci()))
        base = max(scored, key=lambda item: (item["base_score"], item["move"].uci()))
        changed = selected["move"] != base["move"]
        return {
            "move": selected["move"],
            "active_ids": selected["active"],
            "predicate_ids": selected["evaluated"],
            "responsible_ids": selected["active"] if changed else (),
            "seed": seed,
        }

    return choose


def _prepare_route(
    state: SeedState,
    *,
    topology: str,
    route: str,
    dose: float | None,
) -> tuple[set[str], dict[str, Mapping[str, float]]]:
    state.snapshot.restore(state.runtime)
    spec_ids = {spec.spec_id for spec in state.specs[topology]}
    enabled = {state.spec_to_composite[spec_id] for spec_id in spec_ids}
    interventions: dict[str, Mapping[str, float]] = {}
    for cid in sorted(enabled):
        item = live_population_item(state.runtime, cid)
        if route == "G":
            item["state"] = "MATURE"
            state.runtime.cells[cid].state = StemCellState.MATURE
            interventions[cid] = {
                "requested_binary_gate": 1.0,
                "observed_binary_gate": float(item["state"] == "MATURE"),
            }
        elif route == "L":
            item["state"] = "TRIAL"
            state.runtime.cells[cid].state = StemCellState.TRIAL
            interventions[cid] = apply_live_routing_weight(
                state.runtime, cid, float(dose or 1.0)
            )
        else:
            raise ValueError(f"unknown route: {route}")
    return enabled, interventions


def _evaluate_configuration(
    state: SeedState,
    rows: Sequence[Mapping[str, Any]],
    *,
    split: str,
    manifest_sha256: str,
    topology: str,
    route: str,
    dose: float | None,
    config: ClosureConfig,
) -> dict[str, Any]:
    enabled, interventions = _prepare_route(
        state, topology=topology, route=route, dose=dose
    )
    provider = _FrozenFlatScoreProvider(state.weights)
    selector = _route_selector(
        state.runtime,
        provider,
        enabled,
        route=route,
        seed=state.seed,
    )
    return _evaluate_rows(
        rows,
        provider=provider,
        seed=state.seed,
        maximum_plies=config.maximum_plies,
        split=split,
        manifest_sha256=manifest_sha256,
        arm=topology,
        route=route,
        dose=dose,
        selector=selector,
        snapshot_sha256=state.snapshot_sha256,
        interventions=interventions,
    )


def _paired_comparison(
    left: Sequence[bool],
    right: Sequence[bool],
    *,
    alpha: float,
    noninferiority_margin: float,
) -> dict[str, Any]:
    paired = paired_binary_outcomes(
        left,
        right,
        confidence=1.0 - alpha,
        noninferiority_margin=noninferiority_margin,
    )
    favorable = int(paired["favorable"])
    unfavorable = int(paired["unfavorable"])
    discordants = favorable + unfavorable
    raw_p = _exact_upper_sign_p(favorable, discordants)
    balance = _wilson_interval(favorable, discordants, confidence=1.0 - alpha)
    return {
        **paired,
        "raw_p": raw_p,
        "balance_wilson_low": balance[0],
        "balance_wilson_high": balance[1],
        "noninferiority_pass": float(paired["ci_low"]) >= noninferiority_margin,
    }


def _exact_upper_sign_p(favorable: int, discordants: int) -> float:
    if discordants <= 0:
        return 1.0
    return sum(
        math.comb(discordants, value)
        for value in range(favorable, discordants + 1)
    ) / (2**discordants)


def _wilson_interval(
    success: int,
    total: int,
    *,
    confidence: float,
) -> tuple[float, float]:
    if total <= 0:
        return 0.0, 1.0
    z = NormalDist().inv_cdf(1.0 - (1.0 - confidence) / 2.0)
    p = success / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denominator
    radius = z * math.sqrt(
        p * (1.0 - p) / total + z * z / (4.0 * total * total)
    ) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def _outcomes(evaluations: Sequence[Mapping[str, Any]]) -> list[bool]:
    return [
        bool(value)
        for evaluation in evaluations
        for value in evaluation["success_by_row"].values()
    ]


def _adequate_topologies(states: Sequence[SeedState]) -> dict[str, bool]:
    return {
        topology: sum(
            int(state.coverage[topology]["adequate_cell_count"] > 0)
            for state in states
        ) >= 3
        for topology in ("exact_point", "signature_coarsened", "widened", "matched_random")
    }


def _select_configurations(
    states: Sequence[SeedState],
    evaluations: Mapping[str, Mapping[str, Sequence[Mapping[str, Any]]]],
    *,
    adequate: Mapping[str, bool],
    alpha: float,
    noninferiority_margin: float,
) -> tuple[dict[str, str], dict[str, Any]]:
    baseline = _outcomes([state.validation_baseline for state in states])
    selected: dict[str, str] = {}
    table: dict[str, Any] = {}
    for topology, configs in evaluations.items():
        rows: list[tuple[tuple[Any, ...], str, dict[str, Any]]] = []
        for config_id, per_seed in configs.items():
            outcomes = _outcomes(per_seed)
            comparison = _paired_comparison(
                outcomes,
                baseline,
                alpha=alpha,
                noninferiority_margin=noninferiority_margin,
            )
            route, _, dose_text = config_id.partition(":")
            dose = None if not dose_text else float(dose_text)
            key = (
                int(bool(adequate[topology])),
                comparison["favorable"] - comparison["unfavorable"],
                sum(outcomes),
                int(route == "G"),
                -float(dose or 0.0),
                config_id,
            )
            rows.append((key, config_id, comparison))
        _, chosen, comparison = max(rows, key=lambda row: row[0])
        selected[topology] = chosen
        table[topology] = {
            "selected": chosen,
            "adequately_detectable": bool(adequate[topology]),
            "comparison_vs_baseline": comparison,
            "candidates": {
                config_id: candidate for _, config_id, candidate in rows
            },
        }
    return selected, table


def _selected_evaluations(
    evaluations: Mapping[str, Mapping[str, Sequence[Mapping[str, Any]]]],
    selected: Mapping[str, str],
) -> dict[str, Sequence[Mapping[str, Any]]]:
    return {
        topology: evaluations[topology][config_id]
        for topology, config_id in selected.items()
    }


def _primary_comparisons(
    selected_evaluations: Mapping[str, Sequence[Mapping[str, Any]]],
    baseline_evaluations: Sequence[Mapping[str, Any]],
    *,
    alpha: float,
    noninferiority_margin: float,
) -> dict[str, Any]:
    outcomes = {
        topology: _outcomes(per_seed)
        for topology, per_seed in selected_evaluations.items()
    }
    baseline = _outcomes(baseline_evaluations)
    family = (
        ("point_selected_vs_baseline", outcomes["exact_point"], baseline),
        ("signature_selected_vs_baseline", outcomes["signature_coarsened"], baseline),
        ("widened_selected_vs_baseline", outcomes["widened"], baseline),
        ("random_selected_vs_baseline", outcomes["matched_random"], baseline),
        ("widened_selected_vs_random_selected", outcomes["widened"], outcomes["matched_random"]),
    )
    rows = [
        (
            name,
            _paired_comparison(
                left,
                right,
                alpha=alpha,
                noninferiority_margin=noninferiority_margin,
            ),
        )
        for name, left, right in family
    ]
    holm = holm_adjusted_pvalues(
        [comparison["raw_p"] for _, comparison in rows],
        alpha=alpha,
    )
    result: dict[str, Any] = {}
    for (name, comparison), adjusted in zip(rows, holm, strict=True):
        result[name] = {
            **comparison,
            "holm_adjusted_p": adjusted["adjusted_p"],
            "holm_threshold": adjusted["holm_threshold"],
            "holm_rejected": adjusted["rejected"],
        }
    return result


def _validation_unlocked(
    comparisons: Mapping[str, Mapping[str, Any]],
    adequate: Mapping[str, bool],
    *,
    alpha: float,
) -> bool:
    names = {
        "exact_point": "point_selected_vs_baseline",
        "signature_coarsened": "signature_selected_vs_baseline",
        "widened": "widened_selected_vs_baseline",
    }
    return any(
        bool(
            adequate[topology]
            and comparisons[name]["favorable"] > comparisons[name]["unfavorable"]
            and comparisons[name]["balance_wilson_low"] > 0.5
            and comparisons[name]["holm_adjusted_p"] <= alpha
        )
        for topology, name in names.items()
    )


def _compact_evaluation(evaluation: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "arm": evaluation["arm"],
        "route": evaluation["route"],
        "dose": evaluation["dose"],
        "seed": evaluation["seed"],
        "wins": evaluation["wins"],
        "reward_sum": evaluation["reward_sum"],
        "endpoint_counts": evaluation["endpoint_counts"],
        "row_count": len(evaluation["success_by_row"]),
        "manifest_sha256": evaluation["manifest_sha256"],
    }


def _write_rows(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(_canonical_json(record) + "\n" for record in records),
        encoding="utf-8",
    )


def _constructed_ceiling() -> dict[str, Any]:
    # Lazy import avoids loading the large historical ladder for pool-only users.
    from .persistent_staged_ladder import _phase50_constructed_gate_flip_proof

    proof = _phase50_constructed_gate_flip_proof(_runtime_config())
    return {
        "passed": bool(proof.get("passed", False)),
        "kind": "sealed_constructed_FormalReCon_binary_gate_move_flip",
        "evaluation_only": True,
        "proof": proof,
    }


def _seed_state(
    *,
    seed: int,
    train_rows: Sequence[Mapping[str, Any]],
    validation_rows: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    config: ClosureConfig,
) -> SeedState:
    flat_seed = FLAT_HOST_BY_SEED[seed]
    weights = _load_weight_table(
        FLAT_WEIGHT_DIR / f"stage_d_B_sealed_seed_{flat_seed}_weights.json"
    )
    provider = _FrozenFlatScoreProvider(weights)
    train = _evaluate_rows(
        train_rows,
        provider=provider,
        seed=seed,
        maximum_plies=config.maximum_plies,
        split="train",
        manifest_sha256=manifest["splits"]["train"]["sha256"],
        arm="frozen_host_training_experience",
        route="baseline",
    )
    validation = _evaluate_rows(
        validation_rows,
        provider=provider,
        seed=seed,
        maximum_plies=config.maximum_plies,
        split="validation",
        manifest_sha256=manifest["splits"]["validation"]["sha256"],
        arm="frozen_host_baseline",
        route="baseline",
    )
    noop = _evaluate_rows(
        validation_rows,
        provider=provider,
        seed=seed,
        maximum_plies=config.maximum_plies,
        split="validation",
        manifest_sha256=manifest["splits"]["validation"]["sha256"],
        arm="noop",
        route="noop",
    )
    _assert_noop_parity(validation, noop)
    specs = build_topology_specs(train, validation, config=config, seed=seed)
    runtime, mapping = _materialize_runtime(specs, seed=seed)
    snapshot = CounterfactualSnapshot.capture(runtime)
    snapshot_sha = _snapshot_digest(runtime, mapping)
    coverage = _formal_coverage(
        runtime,
        specs,
        mapping,
        validation["frames"],
        minimum_firing_rows=config.minimum_firing_rows,
    )
    snapshot.restore(runtime)
    return SeedState(
        seed=seed,
        flat_seed=flat_seed,
        weights=weights,
        train_evaluation=train,
        validation_baseline=validation,
        validation_noop=noop,
        specs=specs,
        runtime=runtime,
        snapshot=snapshot,
        snapshot_sha256=snapshot_sha,
        spec_to_composite=mapping,
        coverage=coverage,
    )


def _interpretation(
    *,
    measurement_pass: bool,
    adequate: Mapping[str, bool],
    validation_unlocked: bool,
    final_comparisons: Mapping[str, Mapping[str, Any]] | None,
    selected: Mapping[str, str],
    alpha: float,
) -> str:
    if not measurement_pass:
        return "The closure is invalid as a scientific experiment."
    if not any(adequate[topology] for topology in ("exact_point", "signature_coarsened", "widened")):
        return (
            "Outcome-only credit did not produce an adequately detectable ecology at the "
            "preregistered scale; no positive or causal-null classification is made, and "
            "the v1 KRK ecological line nevertheless closes."
        )
    if not validation_unlocked or final_comparisons is None:
        return (
            "The current v1 KRK ecology/representation/routing intervention produced no "
            "validation-qualified causal benefit at the preregistered scale."
        )
    widened = final_comparisons["widened_selected_vs_baseline"]
    selective = final_comparisons["widened_selected_vs_random_selected"]
    if (
        selected["widened"] == "G"
        and widened["holm_adjusted_p"] <= alpha
        and widened["balance_wilson_low"] > 0.5
        and widened["noninferiority_pass"]
        and selective["holm_adjusted_p"] <= alpha
        and selective["balance_wilson_low"] > 0.5
    ):
        return (
            "Under outcome-only ecological credit and repaired measurement, content-blind "
            "widening produced a selective causal benefit through binary gating in the "
            "current frozen KRK host."
        )
    if selected["widened"].startswith("L:") and widened["holm_adjusted_p"] <= alpha:
        return (
            "Discovered/widened structure has additive causal utility under the tested "
            "host, but conditional non-linear routing was not established."
        )
    if (
        widened["holm_adjusted_p"] <= alpha
        and selective["holm_adjusted_p"] > alpha
    ):
        return "The benefit is not selective to the widening operator or discovered content."
    return (
        "The current v1 KRK ecology/representation/routing intervention produced no "
        "detectable causal benefit at the preregistered scale."
    )


def run_krk_preregistered_closure(
    *,
    config: ClosureConfig = ClosureConfig(),
    generate_pools: bool = True,
) -> dict[str, Any]:
    """Run validation, and touch FINAL-TEST once only if the frozen gate unlocks it."""

    output_dir = Path(config.output_dir)
    manifest = (
        generate_fresh_pools(config=config)
        if generate_pools
        else json.loads((output_dir / "split_manifest.json").read_text(encoding="utf-8"))
    )
    # Selection code deliberately loads only these two row files.
    train_rows = _load_split(output_dir, manifest, "train")
    validation_rows = _load_split(output_dir, manifest, "validation")
    states = [
        _seed_state(
            seed=seed,
            train_rows=train_rows,
            validation_rows=validation_rows,
            manifest=manifest,
            config=config,
        )
        for seed in config.experiment_seeds
    ]
    noop_table = [
        {
            "seed": state.seed,
            **_assert_noop_parity(state.validation_baseline, state.validation_noop),
        }
        for state in states
    ]
    oracle = _constructed_ceiling()
    measurement_pass = bool(
        oracle["passed"] and all(row["passed"] for row in noop_table)
    )
    adequate = _adequate_topologies(states)
    all_records = [
        record
        for state in states
        for evaluation in (
            state.train_evaluation,
            state.validation_baseline,
            state.validation_noop,
        )
        for record in evaluation["row_records"]
    ]
    validation_evaluations: dict[str, dict[str, list[dict[str, Any]]]] = {
        topology: {"G": [], **{f"L:{dose:g}": [] for dose in config.l_doses}}
        for topology in ("exact_point", "signature_coarsened", "widened", "matched_random")
    }
    selected: dict[str, str] = {}
    selection_table: dict[str, Any] = {}
    validation_comparisons: dict[str, Any] = {}
    validation_unlocked = False
    if measurement_pass and any(adequate.values()):
        for state in states:
            for topology, configs in validation_evaluations.items():
                gate_eval = _evaluate_configuration(
                    state,
                    validation_rows,
                    split="validation",
                    manifest_sha256=manifest["splits"]["validation"]["sha256"],
                    topology=topology,
                    route="G",
                    dose=None,
                    config=config,
                )
                configs["G"].append(gate_eval)
                all_records.extend(gate_eval["row_records"])
                for dose in config.l_doses:
                    dose_eval = _evaluate_configuration(
                        state,
                        validation_rows,
                        split="validation",
                        manifest_sha256=manifest["splits"]["validation"]["sha256"],
                        topology=topology,
                        route="L",
                        dose=dose,
                        config=config,
                    )
                    configs[f"L:{dose:g}"].append(dose_eval)
                    all_records.extend(dose_eval["row_records"])
        selected, selection_table = _select_configurations(
            states,
            validation_evaluations,
            adequate=adequate,
            alpha=config.alpha,
            noninferiority_margin=config.noninferiority_margin,
        )
        validation_comparisons = _primary_comparisons(
            _selected_evaluations(validation_evaluations, selected),
            [state.validation_baseline for state in states],
            alpha=config.alpha,
            noninferiority_margin=config.noninferiority_margin,
        )
        validation_unlocked = _validation_unlocked(
            validation_comparisons,
            adequate,
            alpha=config.alpha,
        )

    final_touch_count = 0
    final_evaluations: dict[str, list[dict[str, Any]]] = {}
    final_comparisons: dict[str, Any] | None = None
    if validation_unlocked:
        _write_json(
            output_dir / "final_test_touch.json",
            {"touch_count": 0, "touched": False, "unlocked": True},
        )
        final_rows = _load_split(output_dir, manifest, "final_test")
        final_touch_count = 1
        _write_json(
            output_dir / "final_test_touch.json",
            {"touch_count": 1, "touched": True, "unlocked": True},
        )
        final_baselines: list[dict[str, Any]] = []
        for state in states:
            provider = _FrozenFlatScoreProvider(state.weights)
            baseline = _evaluate_rows(
                final_rows,
                provider=provider,
                seed=state.seed,
                maximum_plies=config.maximum_plies,
                split="final_test",
                manifest_sha256=manifest["splits"]["final_test"]["sha256"],
                arm="frozen_host_baseline",
                route="baseline",
            )
            noop = _evaluate_rows(
                final_rows,
                provider=provider,
                seed=state.seed,
                maximum_plies=config.maximum_plies,
                split="final_test",
                manifest_sha256=manifest["splits"]["final_test"]["sha256"],
                arm="noop",
                route="noop",
            )
            _assert_noop_parity(baseline, noop)
            final_baselines.append(baseline)
            all_records.extend(baseline["row_records"])
            all_records.extend(noop["row_records"])
            for topology, config_id in selected.items():
                route, _, dose_text = config_id.partition(":")
                evaluation = _evaluate_configuration(
                    state,
                    final_rows,
                    split="final_test",
                    manifest_sha256=manifest["splits"]["final_test"]["sha256"],
                    topology=topology,
                    route=route,
                    dose=None if not dose_text else float(dose_text),
                    config=config,
                )
                final_evaluations.setdefault(topology, []).append(evaluation)
                all_records.extend(evaluation["row_records"])
        final_comparisons = _primary_comparisons(
            final_evaluations,
            final_baselines,
            alpha=config.alpha,
            noninferiority_margin=config.noninferiority_margin,
        )

    interpretation = _interpretation(
        measurement_pass=measurement_pass,
        adequate=adequate,
        validation_unlocked=validation_unlocked,
        final_comparisons=final_comparisons,
        selected=selected,
        alpha=config.alpha,
    )
    rows_path = output_dir / "rows.jsonl"
    _write_rows(rows_path, all_records)
    summary = {
        "schema_version": "krk_preregistered_ecological_closure_result.v1",
        "config": asdict(config),
        "preregistration_sha256": manifest["preregistration_sha256"],
        "split_manifest": manifest,
        "measurement_gate": {
            "passed": measurement_pass,
            "noop": noop_table,
            "constructed_ceiling": oracle,
        },
        "coverage_gate": {
            "adequate_by_topology": adequate,
            "per_seed": [
                {"seed": state.seed, "coverage": state.coverage}
                for state in states
            ],
        },
        "validation": {
            "selected_configurations": selected,
            "selection_table": selection_table,
            "primary_comparisons": validation_comparisons,
            "freeze_gate_passed": validation_unlocked,
            "per_arm_per_seed": {
                topology: {
                    config_id: [_compact_evaluation(item) for item in per_seed]
                    for config_id, per_seed in configs.items()
                }
                for topology, configs in validation_evaluations.items()
            },
        },
        "final_test": {
            "touched": bool(final_touch_count),
            "touch_count": final_touch_count,
            "manifest_sha256": manifest["splits"]["final_test"]["sha256"],
            "primary_comparisons": final_comparisons,
            "per_arm_per_seed": {
                topology: [_compact_evaluation(item) for item in per_seed]
                for topology, per_seed in final_evaluations.items()
            },
        },
        "selectivity_gate": {
            "passed": bool(
                final_comparisons
                and final_comparisons["widened_selected_vs_random_selected"]["holm_rejected"]
                and final_comparisons["widened_selected_vs_random_selected"]["balance_wilson_low"] > 0.5
            ),
        },
        "heldout_causal_gate": {
            "passed": bool(
                final_comparisons
                and any(
                    comparison["holm_rejected"]
                    and comparison["balance_wilson_low"] > 0.5
                    and comparison["noninferiority_pass"]
                    for name, comparison in final_comparisons.items()
                    if name.endswith("_vs_baseline")
                    and not name.startswith("random_")
                )
            ),
        },
        "candidate_populations": [
            {
                "seed": state.seed,
                "topologies": {
                    topology: [spec.to_dict() for spec in specs]
                    for topology, specs in state.specs.items()
                },
                "snapshot_sha256": state.snapshot_sha256,
            }
            for state in states
        ],
        "interpretation": interpretation,
        "krk_freeze": (
            "This was the single authorized v1 KRK ecological closure. KRK is now frozen "
            "as a regression/transfer benchmark; no rescue closure is authorized."
        ),
        "next_research_question": (
            "KPK opposition and tempo: can outcome-only ecology discover selective "
            "temporal/conjunctive option structure that transfer cannot avoid?"
        ),
        "artifacts": {
            "row_jsonl": str(rows_path),
            "split_manifest": str(output_dir / "split_manifest.json"),
            "final_touch_record": str(output_dir / "final_test_touch.json"),
        },
    }
    _write_json(output_dir / "summary.json", summary)
    return summary
