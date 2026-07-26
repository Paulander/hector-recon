"""Fresh, atomic V2 prospective-evidence scientific discriminator.

This outer experiment owns a new physical ecology and durable scientific
carrier.  It imports the validated V2.1 organism, laboratory registry, and
atomic snapshot harness without modifying them.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Sequence
import argparse
import copy
import gzip
import hashlib
import importlib
import importlib.metadata
import json
import math
import os
import platform
import random
import shutil
import subprocess
import sys
import tempfile

import chess

from recon_lite import FrameContext, FrameKind, Node, NodeType
from recon_lite_hector.learning import IntrinsicCreditEngine

from .native_authority_handover import FrozenCompetenceProvenance, GraphSignalTrace, NativeR0Organism
from .native_competence_envelope import (
    AvailabilityState,
    CompetenceEnvelopeConfig,
    SpecializationMode,
    StemCellState,
)
from .native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    V2Mode,
    _interaction_fingerprint,
)
from .native_prospective_evidence_authority_v2_lab import (
    RegisteredV2ExposureRow,
    V2LaboratoryRegistry,
    policy_critical_package_hashes,
)
from .native_single_graph_curriculum import NativeSingleGraphConfig, _TripletNodeIds
from .native_trace_competence_authority import (
    TraceNativeCompetenceOrganism,
    TraceNativeLearningConfig,
)
from .native_v2_atomic_snapshot_graph import ImportStableOpaqueChessEcologyGraph
from .native_v2_atomic_snapshot_harness import (
    ARMS,
    AtomicSnapshotIntegrityError,
    DurableHashJournal,
    NonResumableJournal,
    OutcomeAccessGuard,
    V2SnapshotCodec,
    atomic_json,
    canonical_digest,
    execute_seed_atomically,
    global_all_arm_preflight,
    persist_arm_snapshots_once,
    sha256_bytes,
    sha256_file,
    v2_semantic_identity,
)


SOURCE_BASE_COMMIT = "bd2ceb788340c6f7ccc30e7ba1e8440cce4a7270"
EXPERIMENT_ID = "native_v2_fresh_discriminator_review_repair_v2.v1"
OPAQUE_TERMINAL_SALT = "native-v2-review-repair-v2-opaque-terminals.20260726.v1"
TOY_EXPERIMENT_ID = "native_v2_review_repair_v2_retired_canary.v1"
TOY_OPAQUE_TERMINAL_SALT = "native-v2-review-repair-v2-retired-canary.20260726.v1"
ROOT = Path(__file__).resolve().parents[3]
PACKAGE_DIR = Path("reports/autogrowth/native_authority/v2_fresh_discriminator_review_repair_v2")
SUPERSEDED_PACKAGE_DIR = Path("reports/autogrowth/native_authority/v2_fresh_discriminator")
OLD_PACKAGE_DIR = Path("reports/autogrowth/native_authority/v2_scientific_discriminator")
RECLOSURE_DIR = Path("reports/autogrowth/native_authority/v2_atomic_snapshot_reclosure")
SEED_MANIFEST_PATH = PACKAGE_DIR / "seed_manifest.json"
EXCLUDED_POSITION_MANIFEST_PATH = PACKAGE_DIR / "excluded_position_manifest.json"
ECOLOGY_MANIFEST_PATH = PACKAGE_DIR / "ecology_manifest.json"
PERMUTATION_MANIFEST_PATH = PACKAGE_DIR / "c_permutation_manifest.json"
ENVIRONMENT_MANIFEST_PATH = PACKAGE_DIR / "environment_manifest.json"
SOURCE_RUNTIME_MANIFEST_PATH = PACKAGE_DIR / "source_runtime_manifest.json"
OUTER_MANIFEST_PATH = PACKAGE_DIR / "outer_manifest.json"
TOY_CANARY_PATH = PACKAGE_DIR / "retired_actual_v2_canary.json"
TOY_ECOLOGY_PATH = PACKAGE_DIR / "retired_actual_v2_canary_ecology.json"
PREFIX_DIR = PACKAGE_DIR / "prefix_organisms"
PREFIX_MANIFEST_PATH = PACKAGE_DIR / "prefix_candidate_manifest.json"
SNAPSHOT_ROOT = PACKAGE_DIR / "arm_snapshot_package"
EXPOSURE_PATH = PACKAGE_DIR / "preoutcome_exposure_admission.json"
EXECUTION_MANIFEST_PATH = PACKAGE_DIR / "execution_manifest.json"
SCIENCE_JOURNAL_DIR = PACKAGE_DIR / "science_journal"
SCIENCE_CARRIER_DIR = PACKAGE_DIR / "science_carrier"
RESULT_PATH = PACKAGE_DIR / "canonical_result.json.gz"
PREREGISTRATION_PATH = Path(
    "docs/autogrowth/NATIVE_V2_FRESH_DISCRIMINATOR_REVIEW_REPAIR_V2_PREREGISTRATION_20260726.md"
)
COMPLIANCE_PATH = Path(
    "docs/autogrowth/NATIVE_V2_FRESH_DISCRIMINATOR_REVIEW_REPAIR_V2_COMPLIANCE_20260726.md"
)
TEST_PATH = Path("tests/autogrowth/test_native_v2_fresh_discriminator_review_repair_v2.py")

PROTECTED_HASHES = {
    "src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2.py": (
        "25945864fd998caf22ae12cbcb9bcb4779447337c0079f705640c63d2356f029"
    ),
    "src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2_lab.py": (
        "f3aee5cccf761af1cb6a5de94b886d5e758c0a07cb0f6d77b8898f662ca73b58"
    ),
    "src/recon_lite_chess/autogrowth/native_v2_atomic_snapshot_harness.py": (
        "8611853ca56c2dab3e2a44ebad18997f9d9d55578627acbaff6e727a578fd894"
    ),
}
PROTECTED_ARTIFACT_HASHES = {
    RECLOSURE_DIR / "arm_snapshot_manifest.json.gz": (
        "f0ee54a32210d38a78f98588f42baffeb67324335273148e856f053fb6a9d557"
    ),
    RECLOSURE_DIR / "global_preflight_receipt.json": (
        "fb1d9ba3fa5f296875970468d481dbcf6688d751e854070792c504cb3454c8f7"
    ),
    OLD_PACKAGE_DIR / "suffix_integrity_abort.json": (
        "f59607a5f45223f4950a3c419d86517c5b24cd272a48440c803f1bf1224a24e4"
    ),
}

SEED_COUNT = 32
PREFIX_POSITIVE_COUNT = 32
PREFIX_NEGATIVE_PER_ATOM = 8
SUFFIX_SPURIOUS_COUNT = 8
SUFFIX_PLANTED_COUNT = 8
MIN_TARGET_OPPORTUNITIES = 4
MIN_QUALIFYING_SEEDS = 24
MIN_FAVORABLE_SEEDS = 17
PRIMARY_ALPHA = 0.05
BOOTSTRAP_REPLICATES = 20_000
EXPECTED_V2_1_PACKAGE_DIGEST = (
    "c0116b15982511d446dee7a926c4d31e3066e59e3cc3faf9bb161b4c24b50a58"
)
DETERMINISTIC_ENV = {
    "PYTHONHASHSEED": "0",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "TZ": "UTC",
    "LC_ALL": "C.UTF-8",
    "LANG": "C.UTF-8",
}


class FreshScientificIntegrityError(RuntimeError):
    """Fail-closed fresh-experiment boundary."""


class OutcomeCapabilityError(FreshScientificIntegrityError):
    """Outcome observation was attempted outside the mint capability."""


class InjectedFreshFailure(RuntimeError):
    """Test-only stage failure."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def deterministic_gzip(payload: bytes) -> bytes:
    return gzip.compress(payload, compresslevel=9, mtime=0)


def _git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def require_clean_worktree() -> None:
    if _git("status", "--porcelain=v1"):
        raise FreshScientificIntegrityError("scientific phase requires clean worktree")


def verify_protected_boundary() -> dict[str, str]:
    observed = {}
    for relative, expected in PROTECTED_HASHES.items():
        actual = sha256_file(ROOT / relative)
        observed[relative] = actual
        if actual != expected:
            raise FreshScientificIntegrityError(
                f"engineering_boundary_requires_reclosure:{relative}:{actual}"
            )
    package = policy_critical_package_hashes(ROOT)
    if digest(package) != EXPECTED_V2_1_PACKAGE_DIGEST:
        raise FreshScientificIntegrityError(
            "engineering_boundary_requires_reclosure:v2_1_package_manifest"
        )
    for relative, expected in PROTECTED_ARTIFACT_HASHES.items():
        actual = sha256_file(ROOT / relative)
        observed[str(relative)] = actual
        if actual != expected:
            raise FreshScientificIntegrityError(
                f"engineering_boundary_requires_reclosure:{relative}:{actual}"
            )
    return observed


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite frozen artifact: {path}")
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def _bound_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _resolve_bound_path(value: str) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def opaque_terminal_identity(private_name: str, *, salt: str = OPAQUE_TERMINAL_SALT) -> str:
    return "opaque_terminal:" + hashlib.sha256(
        f"{salt}|{private_name}".encode("utf-8")
    ).hexdigest()


def canonical_pattern_digest(members: Iterable[str]) -> str:
    return digest({"members": sorted(set(map(str, members)))})


def _empty_krk_board(wk: int, wr: int, bk: int) -> chess.Board:
    board = chess.Board.empty()
    board.turn = chess.WHITE
    board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(wr, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    board.clear_stack()
    return board


def _rook_move_ucis() -> tuple[str, ...]:
    moves = []
    for source in chess.SQUARES:
        for target in chess.SQUARES:
            if source != target and (
                chess.square_file(source) == chess.square_file(target)
                or chess.square_rank(source) == chess.square_rank(target)
            ):
                moves.append(chess.Move(source, target).uci())
    return tuple(sorted(moves))


def transition_manifest(predecessor_fen: str, move_uci: str) -> dict[str, Any]:
    board = chess.Board(predecessor_fen)
    move = chess.Move.from_uci(move_uci)
    if move not in board.legal_moves:
        raise FreshScientificIntegrityError("frozen transition action is illegal")
    successor = board.copy(stack=False)
    successor.push(move)
    value = {
        "predecessor_fen": board.fen(),
        "move_uci": move_uci,
        "successor_fen": successor.fen(),
        "outcome": successor.is_checkmate(),
        "environment_outcome_terminal_identity": "mate",
    }
    value["physical_transition_digest"] = digest(value)
    return value


def enumerate_latent_pairs(
    required: int,
    *,
    excluded_position_fens: Iterable[str] = (),
    excluded_transition_digests: Iterable[str] = (),
) -> tuple[dict[str, Any], ...]:
    """Take the first lawful pairs whose complete board positions are unused."""

    excluded_positions = set(map(str, excluded_position_fens))
    excluded_transitions = set(map(str, excluded_transition_digests))
    selected: list[dict[str, Any]] = []
    used_positions = set(excluded_positions)
    for move_uci in _rook_move_ucis():
        move = chess.Move.from_uci(move_uci)
        mates: list[dict[str, Any]] = []
        nonmates: list[dict[str, Any]] = []
        for wk in chess.SQUARES:
            for bk in chess.SQUARES:
                board = _empty_krk_board(wk, move.from_square, bk)
                if not board.is_valid() or board.is_game_over() or move not in board.legal_moves:
                    continue
                transition = transition_manifest(board.fen(), move_uci)
                positions = {
                    str(transition["predecessor_fen"]),
                    str(transition["successor_fen"]),
                }
                if (
                    len(positions) != 2
                    or positions.intersection(excluded_positions)
                    or transition["physical_transition_digest"] in excluded_transitions
                ):
                    continue
                target = mates if transition["outcome"] else nonmates
                target.append(transition)
        for index in range(min(len(mates), len(nonmates))):
            mate_transition = mates[index]
            nonmate_transition = nonmates[index]
            pair_positions = {
                str(mate_transition["predecessor_fen"]),
                str(mate_transition["successor_fen"]),
                str(nonmate_transition["predecessor_fen"]),
                str(nonmate_transition["successor_fen"]),
            }
            if len(pair_positions) != 4 or pair_positions.intersection(used_positions):
                continue
            pair_transitions = {
                str(mate_transition["physical_transition_digest"]),
                str(nonmate_transition["physical_transition_digest"]),
            }
            if len(pair_transitions) != 2 or pair_transitions.intersection(excluded_transitions):
                continue
            used_positions.update(pair_positions)
            selected.append({
                "pair_ordinal": len(selected),
                "move_uci": move_uci,
                "mate_fen": mate_transition["predecessor_fen"],
                "nonmate_fen": nonmate_transition["predecessor_fen"],
                "mate_successor_fen": mate_transition["successor_fen"],
                "nonmate_successor_fen": nonmate_transition["successor_fen"],
                "mate_transition_digest": mate_transition["physical_transition_digest"],
                "nonmate_transition_digest": nonmate_transition["physical_transition_digest"],
            })
            if len(selected) == required:
                return tuple(selected)
    raise FreshScientificIntegrityError("fresh_ecology_capacity_failure")


def logical_specs() -> tuple[dict[str, Any], ...]:
    specs = []
    for index in range(PREFIX_POSITIVE_COUNT):
        specs.append({
            "row_id": f"prefix-positive-{index:02d}",
            "phase": "prefix",
            "visible_family": "prefix_positive",
            "atoms": ("p0", "p1", "s0", "s1"),
            "a_outcome": True,
        })
    negative = (
        ("p0", "n0", "n1"),
        ("p1", "n2", "n3"),
        ("s0", "n4", "n5"),
        ("s1", "n6", "n7"),
    )
    for group, atoms in enumerate(negative):
        for index in range(PREFIX_NEGATIVE_PER_ATOM):
            specs.append({
                "row_id": f"prefix-negative-{group}-{index:02d}",
                "phase": "prefix",
                "visible_family": f"prefix_negative_{group}",
                "atoms": atoms,
                "a_outcome": False,
            })
    for index in range(SUFFIX_SPURIOUS_COUNT):
        specs.append({
            "row_id": f"suffix-spurious-{index:02d}",
            "phase": "suffix",
            "visible_family": "suffix_spurious",
            "atoms": ("s0", "s1"),
            "a_outcome": False,
        })
    for index in range(SUFFIX_PLANTED_COUNT):
        specs.append({
            "row_id": f"suffix-planted-{index:02d}",
            "phase": "suffix",
            "visible_family": "suffix_planted",
            "atoms": ("p0", "p1"),
            "a_outcome": True,
        })
    if len(specs) != 80:
        raise AssertionError("frozen ecology must contain 80 rows")
    return tuple(specs)


def build_ecology_manifest(
    pairs: Sequence[Mapping[str, Any]],
    *,
    experiment_id: str = EXPERIMENT_ID,
    salt: str = OPAQUE_TERMINAL_SALT,
) -> dict[str, Any]:
    specs = logical_specs()
    if len(pairs) != len(specs):
        raise FreshScientificIntegrityError("ecology requires exactly 80 pairs")
    atom_map = {
        name: opaque_terminal_identity(name, salt=salt)
        for name in ("p0", "p1", "s0", "s1", *(f"n{i}" for i in range(8)))
    }
    rows = []
    transitions: dict[str, dict[str, Any]] = {}
    for spec, pair in zip(specs, pairs, strict=True):
        a_outcome = bool(spec["a_outcome"])
        a_fen = str(pair["mate_fen"] if a_outcome else pair["nonmate_fen"])
        c_fen = str(pair["nonmate_fen"] if a_outcome else pair["mate_fen"])
        a_transition = transition_manifest(a_fen, str(pair["move_uci"]))
        c_transition = transition_manifest(c_fen, str(pair["move_uci"]))
        a_id = f"transition:{spec['row_id']}:AB"
        c_id = f"transition:{spec['row_id']}:C"
        transitions[a_id] = {"transition_id": a_id, **a_transition}
        transitions[c_id] = {"transition_id": c_id, **c_transition}
        rows.append({
            "row_id": str(spec["row_id"]),
            "phase": str(spec["phase"]),
            "visible_family": str(spec["visible_family"]),
            "active_atom_ids": sorted(atom_map[name] for name in spec["atoms"]),
            "move_uci": str(pair["move_uci"]),
            "A_transition_id": a_id,
            "B_transition_id": a_id,
            "C_transition_id": c_id,
            "latent_pair_ordinal": int(pair["pair_ordinal"]),
        })
    starts = [str(item["predecessor_fen"]) for item in transitions.values()]
    results = [str(item["successor_fen"]) for item in transitions.values()]
    all_positions = [*starts, *results]
    if (
        len(starts) != 160
        or len(set(starts)) != 160
        or len(results) != 160
        or len(set(results)) != 160
        or len(set(all_positions)) != 320
    ):
        raise FreshScientificIntegrityError("fresh ecology board-position reuse")
    planted_members = sorted((atom_map["p0"], atom_map["p1"]))
    spurious_members = sorted((atom_map["s0"], atom_map["s1"]))
    value = {
        "schema_version": "native_v2_review_repair_v2_ecology.v1",
        "experiment_id": experiment_id,
        "opaque_terminal_salt": salt,
        "learner_visible_labels": False,
        "completion_terminal_identity": "mate",
        "logical_doses": {
            "prefix_positive": 32,
            "prefix_negative": 32,
            "suffix_spurious": 8,
            "suffix_planted": 8,
        },
        "opaque_terminal_identities": sorted(atom_map.values()),
        "laboratory_private_atom_map": atom_map,
        "planted_pattern_digest": canonical_pattern_digest(planted_members),
        "planted_members": planted_members,
        "spurious_family": [{
            "pattern_digest": canonical_pattern_digest(spurious_members),
            "members": spurious_members,
        }],
        "spurious_selection_rule": (
            "eligible_predeclared_family_then_lexicographically_smallest_"
            "sha256_canonical_hypothesis_manifest_then_cell_id"
        ),
        "prefix_row_order": [row["row_id"] for row in rows if row["phase"] == "prefix"],
        "suffix_row_order": [row["row_id"] for row in rows if row["phase"] == "suffix"],
        "rows": rows,
        "transitions": [transitions[key] for key in sorted(transitions)],
    }
    value["ecology_digest"] = digest(value)
    return value


def ecology_rows(ecology: Mapping[str, Any], phase: str) -> tuple[dict[str, Any], ...]:
    return tuple(
        copy.deepcopy(dict(row))
        for row in ecology["rows"]
        if row["phase"] == phase
    )


def environment_transitions(ecology: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["transition_id"]): copy.deepcopy(dict(row))
        for row in ecology["transitions"]
    }


def _fresh_fen_terminal(node: Node, env: Mapping[str, Any]) -> tuple[bool, bool]:
    board = env.get("board")
    if not isinstance(board, chess.Board):
        node.activation.value = 0.0
        return True, False
    active = board.fen() in set(map(str, node.meta.get("active_fens", ())))
    node.activation.value = 1.0 if active else 0.0
    return True, active


def build_ecology_r0(ecology: Mapping[str, Any]) -> NativeR0Organism:
    unsigned = {key: value for key, value in ecology.items() if key != "ecology_digest"}
    if ecology.get("ecology_digest") != digest(unsigned):
        raise FreshScientificIntegrityError("ecology manifest digest mismatch")
    transitions = environment_transitions(ecology)
    config = NativeSingleGraphConfig(
        include_symmetries=False,
        key_mode="exact",
        shared_feature_atoms=False,
        include_grouped_cache_terminals=True,
        terminal_score_normalization="sum",
        max_ticks=128,
    )
    graph = ImportStableOpaqueChessEcologyGraph(config=config)
    by_move: dict[str, list[dict[str, Any]]] = {}
    for row in ecology["rows"]:
        by_move.setdefault(str(row["move_uci"]), []).append(dict(row))
    route_triplets = {}
    for move_uci, route_rows in sorted(by_move.items()):
        reference_transition = transitions[str(route_rows[0]["A_transition_id"])]
        reference = chess.Board(str(reference_transition["predecessor_fen"]))
        move = chess.Move.from_uci(move_uci)
        triplet_id = graph.ensure_triplet(
            reference, move, stage="opaque_fresh_synthetic_ecology"
        )
        route_triplets[move_uci] = triplet_id
        active_fens = tuple(sorted({
            str(transitions[str(row[f"{arm}_transition_id"])]["predecessor_fen"])
            for row in route_rows for arm in ("A", "C")
        }))
        for node_id in tuple(graph.triplet_nodes[triplet_id]):
            node = graph.graph.nodes[node_id]
            if node.ntype is NodeType.TERMINAL and not node.meta.get("actuator_terminal"):
                node.meta["opaque_route_guard"] = True
                node.meta["active_fens"] = list(active_fens)
                node.predicate = _fresh_fen_terminal
        for fen in active_fens:
            graph.predecessor_routes[fen] = (triplet_id, move_uci)
    all_atom_ids = tuple(map(str, ecology["opaque_terminal_identities"]))
    active_fens_by_atom = {
        atom_id: tuple(sorted({
            str(transitions[str(row[f"{arm}_transition_id"])]["predecessor_fen"])
            for row in ecology["rows"] if atom_id in row["active_atom_ids"]
            for arm in ("A", "C")
        }))
        for atom_id in all_atom_ids
    }
    for atom_id in all_atom_ids:
        graph.graph.add_node(Node(
            atom_id,
            NodeType.TERMINAL,
            predicate=_fresh_fen_terminal,
            meta={
                "origin": "v2_fresh_opaque_external_terminal",
                "role": "opaque_external_terminal",
                "terminal_kind": "opaque_external_terminal",
                "shared_feature_atom": True,
                "terminal_key": atom_id,
                "opaque_external_terminal": True,
                "learner_visible_label": False,
                "active_fens": list(active_fens_by_atom[atom_id]),
                "local_weight": 0.0,
            },
        ))
    for move_uci, triplet_id in sorted(route_triplets.items()):
        route_fens = {
            str(transitions[str(row[f"{arm}_transition_id"])]["predecessor_fen"])
            for row in by_move[move_uci] for arm in ("A", "C")
        }
        action_script = _TripletNodeIds(triplet_id).action_script
        for atom_id in all_atom_ids:
            if route_fens.intersection(active_fens_by_atom[atom_id]):
                graph._add_hierarchy_pair(action_script, atom_id, trainable=False, weight=0.0)
                graph.triplet_nodes[triplet_id].add(atom_id)
    graph.mature_existing_graph()
    graph.freeze_existing_parameters(reason="v2_fresh_frozen_ecology")
    credit = IntrinsicCreditEngine()
    child_id = "opaque_fresh_synthetic_chess_actuator"
    credit_state = credit.register(
        child_id, mature=True, initial_fast_value=1.0, initial_slow_value=1.0
    )
    credit_state.terminal_evidence = 4
    credit_state.causal_confirmations = 1
    credit_state.grounding_level = 0
    provenance = FrozenCompetenceProvenance(
        child_id=child_id,
        mature=True,
        grounded=True,
        can_emit=True,
        consolidated_value=1.0,
        uncertainty=0.0,
        terminal_evidence=4,
        causal_confirmations=1,
        grounding_level=0,
        grounding_source="frozen_fresh_synthetic_environment_actuator_provenance",
        completion_terminal_kind="mate",
    )
    return NativeR0Organism(
        graph=graph,
        credit=credit,
        provenance=provenance,
        frozen_triplet_ids=frozenset(graph.triplet_ids),
        source_manifest={
            "experiment_id": ecology["experiment_id"],
            "ecology_digest": ecology["ecology_digest"],
            "opaque_external_terminals": True,
            "learner_visible_labels": False,
            "graph_owned_actuator": True,
        },
        retrieval_budget_per_actuator=16,
    )


def visible_trace_manifest(trace: GraphSignalTrace) -> dict[str, Any]:
    return {
        "ordered_signal_identities": list(trace.ordered_signal_identities),
        "typed_terminal_signals": [asdict(item) for item in trace.terminal_signals],
        "confirmed_base_terminal_node_ids": list(trace.confirmed_base_terminal_node_ids),
        "confirmed_mature_composite_ids": list(trace.confirmed_mature_composite_ids),
        "option_identity": trace.option_identity,
        "actuation": asdict(trace.actuation),
    }


def outcome_blind_row(
    row: Mapping[str, Any], transitions: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    arms = {}
    for arm in ARMS:
        transition_id = str(row[f"{arm}_transition_id"])
        transition = transitions[transition_id]
        arms[arm] = {
            "transition_id": transition_id,
            "predecessor_fen": str(transition["predecessor_fen"]),
            "move_uci": str(transition["move_uci"]),
        }
    return {
        "row_id": str(row["row_id"]),
        "visible_family": str(row["visible_family"]),
        "active_atom_ids": list(map(str, row["active_atom_ids"])),
        "arms": arms,
    }


def validate_ecology_graph(ecology: Mapping[str, Any]) -> dict[str, Any]:
    r0 = build_ecology_r0(ecology)
    transitions = environment_transitions(ecology)
    rows = []
    fingerprints = []
    for row in ecology["rows"]:
        visible = {}
        for arm in ("A", "C"):
            transition = transitions[str(row[f"{arm}_transition_id"])]
            board = chess.Board(str(transition["predecessor_fen"]))
            frame = FrameContext(
                f"fresh-ecology-validation:{arm}:{row['row_id']}",
                FrameKind.REAL,
                values={"board": board},
            )
            actuation, trace = r0.emit_action_with_trace(frame)
            if actuation is None or trace is None or actuation.candidate_count != 1:
                raise FreshScientificIntegrityError("ecology graph did not emit exactly one action")
            if actuation.move_uci != transition["move_uci"]:
                raise FreshScientificIntegrityError("ecology graph action mismatch")
            successor = board.copy(stack=False)
            successor.push(chess.Move.from_uci(actuation.move_uci))
            if (
                successor.fen() != transition["successor_fen"]
                or successor.is_checkmate() is not bool(transition["outcome"])
            ):
                raise FreshScientificIntegrityError("ecology truth mismatch")
            expected = tuple(sorted((*row["active_atom_ids"], "internal:policy_response")))
            if trace.ordered_signal_identities != expected:
                raise FreshScientificIntegrityError("ecology opaque trace mismatch")
            visible[arm] = visible_trace_manifest(trace)
            fingerprints.append(_interaction_fingerprint(
                source_organism_identity=trace.source_organism_identity,
                source_state_identity=trace.source_state_identity,
                predecessor_fen=board.fen(),
                trace=trace,
                actuation=actuation,
                successor_fen=successor.fen(),
                environment_outcome_terminal_identity="mate",
            ))
        if visible["A"] != visible["C"]:
            raise FreshScientificIntegrityError("control_exposure_parity_failure")
        rows.append({
            "row_id": row["row_id"],
            "visible_manifest_digest": digest(visible["A"]),
        })
    return {
        "source_organism_identity": r0.source_organism_identity(),
        "source_state_identity": r0.trace_state_identity(),
        "row_count": len(rows),
        "exact_visible_pair_count": len(rows),
        "physical_fingerprints": sorted(set(fingerprints)),
        "rows_digest": digest(rows),
    }


def new_discovery_wrapper(seed: int, ecology: Mapping[str, Any]) -> NativeProspectiveAuthorityV2:
    r0 = build_ecology_r0(ecology)
    source = TraceNativeCompetenceOrganism.empty(
        r0,
        envelope_config=CompetenceEnvelopeConfig(selection_seed=int(seed)),
        learning_config=TraceNativeLearningConfig(
            lifecycle_connected=False,
            specialization_mode=SpecializationMode.DISCONNECTED,
            genome_seed=int(seed),
            completion_terminal_identity="mate",
            receipt_issuer_identity="native_v2_fresh_chess_adapter.v1",
            receipt_capability_key=(
                "native-v2-fresh-grounded-capability.v1:"
                + hashlib.sha256(str(seed).encode("utf-8")).hexdigest()
            ),
        ),
    )
    return NativeProspectiveAuthorityV2.from_organism(source, mode=V2Mode.PROSPECTIVE)


def prefix_receipts(
    wrapper: NativeProspectiveAuthorityV2,
    ecology: Mapping[str, Any],
    *,
    ordinal: int,
) -> tuple[Any, ...]:
    terminal = wrapper.base.completion_terminal()
    transitions = environment_transitions(ecology)
    receipts = []
    for row in ecology_rows(ecology, "prefix"):
        transition = transitions[str(row["A_transition_id"])]
        board = chess.Board(str(transition["predecessor_fen"]))
        frame = FrameContext(
            f"fresh-prefix:{ordinal:02d}:{row['row_id']}",
            FrameKind.REAL,
            values={"board": board},
        )
        actuation, trace = wrapper.base.r0.emit_action_with_trace(frame)
        if actuation is None or trace is None or actuation.move_uci != transition["move_uci"]:
            raise FreshScientificIntegrityError("prefix graph action mismatch")
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(actuation.move_uci))
        if (
            successor.fen() != transition["successor_fen"]
            or successor.is_checkmate() is not bool(transition["outcome"])
        ):
            raise FreshScientificIntegrityError("prefix truthful outcome drift")
        receipts.append(terminal.mint(trace, board, successor))
    return tuple(receipts)


def _target_eligible(wrapper: NativeProspectiveAuthorityV2, cell_id: str) -> bool:
    state = wrapper.states[cell_id]
    cell = wrapper.base.envelope.cells[cell_id]
    escrow = cell.nomination_escrow
    return bool(
        cell.is_mature
        and cell.polarity is AvailabilityState.AVAILABLE
        and escrow is not None
        and escrow.fixed_polarity is AvailabilityState.AVAILABLE
        and cell.support >= MIN_TARGET_OPPORTUNITIES
        and cell.failures == 0
        and state.hypothesis.polarity is AvailabilityState.AVAILABLE
    )


def select_prefix_targets(
    wrapper: NativeProspectiveAuthorityV2, ecology: Mapping[str, Any]
) -> dict[str, Any]:
    planted_digest = str(ecology["planted_pattern_digest"])
    spurious_digests = {str(item["pattern_digest"]) for item in ecology["spurious_family"]}
    candidates = []
    for cell_id in sorted(wrapper.states):
        state = wrapper.states[cell_id]
        candidates.append({
            "cell_id": cell_id,
            "pattern_digest": canonical_pattern_digest(state.hypothesis.members),
            "hypothesis_digest": digest(state.hypothesis.manifest()),
            "eligible": _target_eligible(wrapper, cell_id),
            "members": list(state.hypothesis.members),
        })
    planted = sorted(
        (item for item in candidates if item["eligible"] and item["pattern_digest"] == planted_digest),
        key=lambda item: (item["hypothesis_digest"], item["cell_id"]),
    )
    spurious = sorted(
        (
            item for item in candidates
            if item["eligible"]
            and item["pattern_digest"] in spurious_digests
            and item["pattern_digest"] != planted_digest
        ),
        key=lambda item: (item["hypothesis_digest"], item["cell_id"]),
    )
    return {
        "planted_pattern_digest": planted_digest,
        "planted": None if not planted else planted[0],
        "selected_spurious": None if not spurious else spurious[0],
        "eligible_spurious_count": len(spurious),
        "candidate_population_count": len(wrapper.states),
        "candidate_population_digest": wrapper.experimental_identity[
            "candidate_population_identity"
        ],
        "selection_used_suffix": False,
    }


def structural_identity(wrapper: NativeProspectiveAuthorityV2) -> dict[str, Any]:
    epoch = wrapper.base.envelope.nomination_epoch
    return {
        "hypotheses": {
            cell_id: state.hypothesis.manifest()
            for cell_id, state in sorted(wrapper.states.items())
        },
        "cells": {
            cell_id: wrapper.base.envelope.cells[cell_id].to_manifest()
            for cell_id in sorted(wrapper.states)
        },
        "structural_invariants": {
            cell_id: asdict(value)
            for cell_id, value in sorted(wrapper.structural_invariants.items())
        },
        "historical_tombstones": copy.deepcopy(wrapper.historical_tombstones),
        "authority_topology": copy.deepcopy(wrapper.authority_topology),
        "epoch": None if epoch is None else epoch.manifest(),
        "source_organism_identity": wrapper.base.r0.source_organism_identity(),
        "source_state_identity": wrapper.base.r0.trace_state_identity(),
    }


def suffix_topology_identity(
    wrapper: NativeProspectiveAuthorityV2,
) -> dict[str, Any]:
    """Immutable suffix topology; certification/lifecycle values are excluded."""

    return {
        "cell_ids": sorted(wrapper.states),
        "hypotheses": {
            cell_id: state.hypothesis.manifest()
            for cell_id, state in sorted(wrapper.states.items())
        },
        "structural_invariants": {
            cell_id: asdict(value)
            for cell_id, value in sorted(wrapper.structural_invariants.items())
        },
        "authority_topology": copy.deepcopy(wrapper.authority_topology),
        "source_organism_identity": wrapper.base.r0.source_organism_identity(),
        "source_state_identity": wrapper.base.r0.trace_state_identity(),
    }


def run_discovery_seed(
    seed_row: Mapping[str, Any], ecology: Mapping[str, Any]
) -> tuple[dict[str, Any], NativeProspectiveAuthorityV2]:
    ordinal = int(seed_row["ordinal"])
    seed = int(seed_row["genome_seed"])
    wrapper = new_discovery_wrapper(seed, ecology)
    receipts = prefix_receipts(wrapper, ecology, ordinal=ordinal)
    added = wrapper.nominate_prefix_from_grounded_receipts(receipts)
    wrapper.close_nomination()
    targets = select_prefix_targets(wrapper, ecology)
    payload = wrapper.dumps()
    restored = NativeProspectiveAuthorityV2.loads(payload)
    if restored.continuation_manifest() != wrapper.continuation_manifest():
        raise FreshScientificIntegrityError("prefix serialization parity failure")
    result = {
        "ordinal": ordinal,
        "genome_seed": seed,
        "added_cell_ids": list(added),
        "targets": targets,
        "structural_identity_digest": digest(structural_identity(wrapper)),
        "continuation_digest": wrapper.continuation_digest(),
        "experimental_identity_digest": wrapper.experimental_identity["identity_digest"],
        "uncompressed_sha256": sha256_bytes(payload),
    }
    return result, wrapper


def candidate_identical_arms(
    wrapper: NativeProspectiveAuthorityV2,
) -> dict[str, NativeProspectiveAuthorityV2]:
    prospective, legacy = wrapper.clone_candidate_identical_arms()
    control = copy.deepcopy(prospective)
    prospective.assert_candidate_parity(legacy)
    prospective.assert_candidate_parity(control)
    arms = {"A": prospective, "B": legacy, "C": control}
    expected_modes = {
        "A": V2Mode.PROSPECTIVE.value,
        "B": V2Mode.LEGACY.value,
        "C": V2Mode.PROSPECTIVE.value,
    }
    if {arm: value.mode.value for arm, value in arms.items()} != expected_modes:
        raise FreshScientificIntegrityError("native arm-mode smoke gate failed")
    structure = {arm: structural_identity(value) for arm, value in arms.items()}
    if not (structure["A"] == structure["B"] == structure["C"]):
        raise FreshScientificIntegrityError("candidate-identical structural parity failure")
    if any(state.prospectively_certified for state in arms["A"].states.values()):
        raise FreshScientificIntegrityError("prospective A has immediate authority")
    if any(state.prospectively_certified for state in arms["C"].states.values()):
        raise FreshScientificIntegrityError("prospective C has immediate authority")
    for cell_id, state in arms["B"].states.items():
        lawful = arms["B"].base.envelope.cells[cell_id].is_mature
        if state.prospectively_certified is not lawful:
            raise FreshScientificIntegrityError("legacy B initial authority is unlawful")
    return arms


def exact_arm_identity_contract(
    arms: Mapping[str, NativeProspectiveAuthorityV2],
) -> dict[str, Any]:
    if set(arms) != set(ARMS):
        raise FreshScientificIntegrityError("arm identity coverage mismatch")
    identities = {arm: v2_semantic_identity(arms[arm]) for arm in ARMS}
    structure = {arm: structural_identity(arms[arm]) for arm in ARMS}
    if not (structure["A"] == structure["B"] == structure["C"]):
        raise FreshScientificIntegrityError("complete arm structure differs")
    common_fields = (
        "source_organism_identity",
        "source_state_identity",
        "source_base_continuation_digest",
        "candidate_population_identity",
        "polarity_manifest",
        "polarity_identity",
        "topology_identity",
        "executed_topology_identity",
    )
    for field_name in common_fields:
        if len({canonical_digest(identities[arm][field_name]) for arm in ARMS}) != 1:
            raise FreshScientificIntegrityError(
                f"arm common identity differs:{field_name}"
            )
    expected_modes = {
        "A": V2Mode.PROSPECTIVE.value,
        "B": V2Mode.LEGACY.value,
        "C": V2Mode.PROSPECTIVE.value,
    }
    expected_authority = {
        "A": {cell_id: False for cell_id in sorted(arms["A"].states)},
        "B": {
            cell_id: arms["B"].base.envelope.cells[cell_id].is_mature
            for cell_id in sorted(arms["B"].states)
        },
        "C": {cell_id: False for cell_id in sorted(arms["C"].states)},
    }
    for arm in ARMS:
        if identities[arm]["mode"] != expected_modes[arm]:
            raise FreshScientificIntegrityError(f"arm {arm} exact mode mismatch")
        if identities[arm]["authority_manifest"] != expected_authority[arm]:
            raise FreshScientificIntegrityError(f"arm {arm} exact authority mismatch")
        if identities[arm]["lawful_initial_authority"] is not True:
            raise FreshScientificIntegrityError(f"arm {arm} unlawful identity")
    contract = {
        "schema_version": "native_v2_fresh_arm_identity_contract.v1",
        "common_structure": structure["A"],
        "common_structure_digest": digest(structure["A"]),
        "suffix_topology_identity": suffix_topology_identity(arms["A"]),
        "suffix_topology_identity_digest": digest(
            suffix_topology_identity(arms["A"])
        ),
        "common_identity_fields": {
            field_name: copy.deepcopy(identities["A"][field_name])
            for field_name in common_fields
        },
        "lawfully_different_fields": [
            "mode",
            "authority_manifest",
            "authority_identity",
            "experiment_identity",
            "continuation_manifest",
            "continuation_digest",
        ],
        "expected_modes": expected_modes,
        "expected_authority": expected_authority,
        "per_arm_semantic_identity": identities,
    }
    contract["contract_digest"] = digest(contract)
    return contract


def target_cell_id(targets: Mapping[str, Any], name: str) -> str | None:
    item = targets.get(name)
    return None if item is None else str(item["cell_id"])


def classification_visible_projection(
    wrapper: NativeProspectiveAuthorityV2,
    pending: Any,
    trace: GraphSignalTrace,
    *,
    planted_cell_id: str | None,
    spurious_cell_id: str | None,
    row_id: str,
) -> dict[str, Any]:
    matching = tuple(pending.matching_cell_ids)
    activation_map = {
        cell_id: cell_id in matching for cell_id in sorted(wrapper.states)
    }
    value = {
        "row_id": row_id,
        "ordered_classifier_visible_signal_identities": list(
            trace.ordered_signal_identities
        ),
        "typed_classifier_visible_signal_manifests": [
            asdict(item) for item in trace.terminal_signals
        ],
        "selected_opaque_inputs": sorted(
            item.identity
            for item in trace.terminal_signals
            if item.role == "BASE_TERMINAL"
            and item.identity.startswith("opaque_terminal:")
        ),
        "graph_actuator_identity": trace.actuation.actuator_identity,
        "option_identity": trace.option_identity,
        "actuation_manifest": asdict(trace.actuation),
        "matching_cell_commitment": list(matching),
        "candidate_activation_map": activation_map,
        "planted_activation": bool(
            planted_cell_id is not None and planted_cell_id in matching
        ),
        "selected_spurious_activation": bool(
            spurious_cell_id is not None and spurious_cell_id in matching
        ),
        "logical_opportunity_identity": digest({
            "row_id": row_id,
            "planted_cell_id": planted_cell_id or "ABSENT",
            "selected_spurious_cell_id": spurious_cell_id or "ABSENT",
        }),
    }
    value["projection_digest"] = digest(value)
    return value


_OUTCOME_TOKEN = object()


class FrozenTruthfulEnvironment:
    """Frozen transition map whose outcome-bearing path requires a capability."""

    def __init__(self, manifest: Mapping[str, Any]) -> None:
        unsigned = {key: value for key, value in manifest.items() if key != "environment_digest"}
        if manifest.get("environment_digest") != digest(unsigned):
            raise FreshScientificIntegrityError("environment manifest digest mismatch")
        self._manifest = copy.deepcopy(dict(manifest))
        self._transitions = {
            str(item["transition_id"]): copy.deepcopy(dict(item))
            for item in manifest["transitions"]
        }

    def outcome_blind(self, transition_id: str) -> dict[str, str]:
        transition = self._transitions[str(transition_id)]
        return {
            "transition_id": str(transition_id),
            "predecessor_fen": str(transition["predecessor_fen"]),
            "move_uci": str(transition["move_uci"]),
        }

    def _execute(
        self, token: object, transition_id: str, move_uci: str
    ) -> tuple[chess.Board, chess.Board, bool, dict[str, Any]]:
        if token is not _OUTCOME_TOKEN:
            raise OutcomeCapabilityError("truthful transition requires mint capability")
        transition = self._transitions[str(transition_id)]
        predecessor = chess.Board(str(transition["predecessor_fen"]))
        move = chess.Move.from_uci(str(move_uci))
        if move not in predecessor.legal_moves or move_uci != transition["move_uci"]:
            raise FreshScientificIntegrityError("selected graph action/transition mismatch")
        successor = predecessor.copy(stack=False)
        successor.push(move)
        actual_outcome = successor.is_checkmate()
        if (
            successor.fen() != transition["successor_fen"]
            or actual_outcome is not bool(transition["outcome"])
        ):
            raise FreshScientificIntegrityError("truthful environment manifest drift")
        return predecessor, successor, actual_outcome, copy.deepcopy(transition)

    @property
    def identity(self) -> str:
        return str(self._manifest["environment_digest"])


@dataclass(frozen=True)
class MintedTruth:
    receipt: Any
    transition: dict[str, Any]
    actual_outcome: bool


class DurableOutcomeCapability(OutcomeAccessGuard):
    """Only object permitted to execute/observe one truthful transition."""

    def __init__(
        self,
        *,
        environment: FrozenTruthfulEnvironment,
        journal: "FreshScientificJournal",
        count: int = 0,
        event_ids: Sequence[str] = (),
    ) -> None:
        super().__init__(count=int(count), event_ids=tuple(map(str, event_ids)))
        self._environment = environment
        self._journal = journal

    def open(self, event_id: str) -> None:
        del event_id
        raise OutcomeCapabilityError("cooperative guard.open is disabled")

    def mint(
        self,
        *,
        wrapper: NativeProspectiveAuthorityV2,
        pending: Any,
        trace: GraphSignalTrace,
        transition_id: str,
        event_id: str,
    ) -> MintedTruth:
        next_manifest = {
            "count": self.count + 1,
            "event_ids": [*self.event_ids, str(event_id)],
        }
        self._journal.record_outcome_access(
            event_id=str(event_id),
            transition_id=str(transition_id),
            next_guard_manifest=next_manifest,
        )
        self.count = int(next_manifest["count"])
        self.event_ids = tuple(next_manifest["event_ids"])
        predecessor, successor, actual, transition = self._environment._execute(
            _OUTCOME_TOKEN, transition_id, pending.actuation.move_uci
        )
        receipt = wrapper.mint_environment_receipt(
            pending_token=pending.pending_token,
            trace=trace,
            predecessor=predecessor,
            successor=successor,
        )
        if (
            receipt.observed_outcome is not actual
            or receipt.predecessor_fen != transition["predecessor_fen"]
            or receipt.successor_fen != transition["successor_fen"]
        ):
            raise FreshScientificIntegrityError("receipt is not exact truthful access")
        return MintedTruth(receipt=receipt, transition=transition, actual_outcome=actual)


@dataclass
class FreshScienceAdapter:
    """Actual NativeProspectiveAuthorityV2 adapter for atomic A/B/C execution."""

    seed_ordinal: int
    genome_seed: int
    targets: Mapping[str, Any]
    identity_contract: Mapping[str, Any]
    failure_stage: str | None = None
    failure_arm: str | None = None
    opens: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    minted: dict[tuple[str, str], MintedTruth] = field(default_factory=dict)
    completed: dict[str, dict[str, dict[str, Any]]] = field(default_factory=dict)
    staged_arms: dict[str, NativeProspectiveAuthorityV2] = field(default_factory=dict)
    initial_states: dict[str, dict[str, Any]] = field(default_factory=dict)

    def _maybe_fail(self, stage: str, arm: str | None = None) -> None:
        if self.failure_stage == stage and (
            self.failure_arm is None or self.failure_arm == arm
        ):
            raise InjectedFreshFailure(f"{stage}:{arm}")

    def clone(self, arm: NativeProspectiveAuthorityV2) -> NativeProspectiveAuthorityV2:
        return copy.deepcopy(arm)

    def state_manifest(self, arm: NativeProspectiveAuthorityV2) -> dict[str, Any]:
        return {
            "continuation_digest": arm.continuation_digest(),
            "suffix_topology_identity_digest": digest(
                suffix_topology_identity(arm)
            ),
        }

    def preflight_state(
        self,
        arm: NativeProspectiveAuthorityV2,
        arm_id: str,
        row: Mapping[str, Any],
    ) -> None:
        self._maybe_fail("preflight", arm_id)
        if arm.pending_event is not None:
            raise FreshScientificIntegrityError("stale pending event before row")
        expected = self.identity_contract["suffix_topology_identity_digest"]
        if digest(suffix_topology_identity(arm)) != expected:
            raise FreshScientificIntegrityError("suffix structural/topology drift")
        if arm.mode.value != self.identity_contract["expected_modes"][arm_id]:
            raise FreshScientificIntegrityError("suffix arm mode drift")
        if arm_id not in self.initial_states:
            self.initial_states[arm_id] = {
                cell_id: state.manifest() for cell_id, state in sorted(arm.states.items())
            }
        del row

    def open(
        self,
        arm: NativeProspectiveAuthorityV2,
        arm_id: str,
        row: Mapping[str, Any],
    ) -> dict[str, Any]:
        self._maybe_fail("open", arm_id)
        plan = row["arms"][arm_id]
        predecessor = chess.Board(str(plan["predecessor_fen"]))
        before = arm.continuation_digest()
        frame = FrameContext(
            f"v2-review-repair-v2:canonical:{arm_id}:seed-{self.seed_ordinal:02d}:{row['row_id']}",
            FrameKind.REAL,
            values={"board": predecessor},
        )
        pending, trace = arm.open_real_event(frame)
        if pending.actuation.move_uci != plan["move_uci"]:
            raise FreshScientificIntegrityError("graph action differs from frozen transition")
        planted_id = target_cell_id(self.targets, "planted")
        spurious_id = target_cell_id(self.targets, "selected_spurious")
        parity = classification_visible_projection(
            arm,
            pending,
            trace,
            planted_cell_id=planted_id,
            spurious_cell_id=spurious_id,
            row_id=str(row["row_id"]),
        )
        classification = pending.pre_outcome_classification
        production_available = bool(
            classification.state is AvailabilityState.AVAILABLE
            and classification.formal_available
        )
        record = {
            "arm": arm_id,
            "row_id": str(row["row_id"]),
            "visible_family": str(row["visible_family"]),
            "transition_id": str(plan["transition_id"]),
            "pre_outcome_continuation_digest": before,
            "pending": pending.manifest(),
            "matching_cell_commitment": list(pending.matching_cell_ids),
            "trace": trace.canonical_manifest(),
            "graph_actuation": asdict(trace.actuation),
            "production_classification": classification.to_manifest(),
            "production_formal_authority": production_available,
            "planted_activation": parity["planted_activation"],
            "selected_spurious_activation": parity["selected_spurious_activation"],
            "parity_projection": parity,
            "structure_before_digest": digest(structural_identity(arm)),
        }
        self.opens[(str(row["row_id"]), arm_id)] = {
            "wrapper": arm,
            "pending": pending,
            "trace": trace,
            "record": record,
        }
        return parity

    def verify_commitments(
        self, commitments: Mapping[str, Any], row: Mapping[str, Any]
    ) -> None:
        self._maybe_fail("commitment", None)
        comparable = []
        for arm in ARMS:
            comparable.append({
                key: value for key, value in commitments[arm].items()
                if key != "projection_digest"
            })
        if not (comparable[0] == comparable[1] == comparable[2]):
            raise FreshScientificIntegrityError(
                f"control_exposure_parity_failure:{row['row_id']}"
            )

    def mint(
        self,
        arm: NativeProspectiveAuthorityV2,
        arm_id: str,
        row: Mapping[str, Any],
        commitment: Any,
        guard: OutcomeAccessGuard,
    ) -> MintedTruth:
        self._maybe_fail("mint", arm_id)
        if not isinstance(guard, DurableOutcomeCapability):
            raise OutcomeCapabilityError("mint received no truthful outcome capability")
        opened = self.opens[(str(row["row_id"]), arm_id)]
        if commitment != opened["record"]["parity_projection"]:
            raise FreshScientificIntegrityError("commitment changed before mint")
        minted = guard.mint(
            wrapper=arm,
            pending=opened["pending"],
            trace=opened["trace"],
            transition_id=str(row["arms"][arm_id]["transition_id"]),
            event_id=(
                f"seed-{self.seed_ordinal:02d}:{row['row_id']}:{arm_id}"
            ),
        )
        self.minted[(str(row["row_id"]), arm_id)] = minted
        return minted

    def consume(
        self,
        arm: NativeProspectiveAuthorityV2,
        arm_id: str,
        row: Mapping[str, Any],
        receipt: MintedTruth,
    ) -> None:
        self._maybe_fail("consume", arm_id)
        emission = arm.consume(receipt.receipt)
        opened = self.opens[(str(row["row_id"]), arm_id)]
        record = copy.deepcopy(opened["record"])
        classification = opened["pending"].pre_outcome_classification
        planted_id = target_cell_id(self.targets, "planted")
        spurious_id = target_cell_id(self.targets, "selected_spurious")
        false_increment = int(
            record["production_formal_authority"] and not receipt.actual_outcome
        )
        spurious_false_increment = int(
            spurious_id is not None
            and spurious_id in classification.available_cell_ids
            and not receipt.actual_outcome
        )
        planted_coverage_increment = int(
            row["visible_family"] == "suffix_planted"
            and planted_id is not None
            and planted_id in classification.available_cell_ids
        )
        record.update({
            "truthful_predecessor_fen": receipt.transition["predecessor_fen"],
            "truthful_action_uci": receipt.transition["move_uci"],
            "truthful_successor_fen": receipt.transition["successor_fen"],
            "truthful_outcome": receipt.actual_outcome,
            "grounded_receipt": receipt.receipt.manifest(),
            "graph_authority_emission": emission.manifest(),
            "endpoint_increments": {
                "false_deployment_authority": false_increment,
                "selected_spurious_attributable_false_authority": (
                    spurious_false_increment
                ),
                "planted_authority_coverage": planted_coverage_increment,
            },
            "post_event_continuation_digest": arm.continuation_digest(),
        })
        self.completed.setdefault(str(row["row_id"]), {})[arm_id] = record

    def validate(
        self,
        arm: NativeProspectiveAuthorityV2,
        arm_id: str,
        row: Mapping[str, Any],
    ) -> None:
        self._maybe_fail("validation", arm_id)
        if arm.pending_event is not None:
            raise FreshScientificIntegrityError("pending event remained after consumption")
        if (
            digest(suffix_topology_identity(arm))
            != self.identity_contract["suffix_topology_identity_digest"]
        ):
            raise FreshScientificIntegrityError("suffix nomination/birth/topology mutation")
        record = self.completed[str(row["row_id"])][arm_id]
        record["structure_after_digest"] = digest(structural_identity(arm))
        record["result_record_digest"] = digest(record)
        self._maybe_fail("commit", arm_id)
        self.staged_arms[arm_id] = arm

    def completed_row(self, row_id: str) -> dict[str, Any]:
        rows = self.completed.get(str(row_id), {})
        if set(rows) != set(ARMS):
            raise FreshScientificIntegrityError("incomplete tri-arm scientific row")
        value = {
            "schema_version": "native_v2_review_repair_v2_scientific_row.v1",
            "seed_ordinal": self.seed_ordinal,
            "genome_seed": self.genome_seed,
            "row_id": str(row_id),
            "arms": {arm: copy.deepcopy(rows[arm]) for arm in ARMS},
        }
        value["scientific_row_digest"] = digest(value)
        return value

    def seed_endpoints(self) -> dict[str, dict[str, int]]:
        result = {
            arm: {
                "false_deployment_authority": 0,
                "selected_spurious_attributable_false_authority": 0,
                "planted_authority_coverage": 0,
            }
            for arm in ARMS
        }
        for row_id in sorted(self.completed):
            for arm in ARMS:
                for name, increment in self.completed[row_id][arm][
                    "endpoint_increments"
                ].items():
                    result[arm][name] += int(increment)
        return result

    def seed_result(self, row_bindings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        if set(self.staged_arms) != set(ARMS):
            raise FreshScientificIntegrityError("final staged arm coverage mismatch")
        target_final_states = {}
        final_cell_states = {}
        final_event_ordinals = {}
        final_emission_digests = {}
        immediate = {}
        for arm in ARMS:
            wrapper = self.staged_arms[arm]
            final_states = {
                cell_id: state.manifest()
                for cell_id, state in sorted(wrapper.states.items())
            }
            final_cell_states[arm] = final_states
            final_event_ordinals[arm] = int(wrapper.next_expected_ordinal)
            final_emission_digests[arm] = digest({
                receipt_id: emission.manifest()
                for receipt_id, emission in sorted(wrapper.emissions.items())
            })
            target_final_states[arm] = {
                name: (
                    None if target_cell_id(self.targets, name) is None
                    else final_states[target_cell_id(self.targets, name)]
                )
                for name in ("planted", "selected_spurious")
            }
            immediate[arm] = sorted(
                cell_id for cell_id, state in self.initial_states[arm].items()
                if state["prospectively_certified"]
            )
        value = {
            "schema_version": "native_v2_review_repair_v2_seed_result.v1",
            "seed_ordinal": self.seed_ordinal,
            "genome_seed": self.genome_seed,
            "targets": copy.deepcopy(dict(self.targets)),
            "identity_contract_digest": self.identity_contract["contract_digest"],
            "row_bindings": [copy.deepcopy(dict(item)) for item in row_bindings],
            "endpoints": self.seed_endpoints(),
            "clearing_summary": summarize_clearing_events(
                tuple({
                    "row_id": row_id,
                    "arms": copy.deepcopy(self.completed[row_id]),
                } for row_id in self.completed),
                self.targets,
            ),
            "initial_states": copy.deepcopy(self.initial_states),
            "immediate_authority_cell_ids": immediate,
            "target_final_states": target_final_states,
            "final_cell_states": final_cell_states,
            "final_event_ordinals": final_event_ordinals,
            "final_emission_digests": final_emission_digests,
            "final_continuation_digests": {
                arm: self.staged_arms[arm].continuation_digest() for arm in ARMS
            },
        }
        value["seed_result_digest"] = digest(value)
        return value


def post_event_semantic_identity(
    wrapper: NativeProspectiveAuthorityV2,
) -> dict[str, Any]:
    continuation = wrapper.continuation_manifest()
    value = {
        "schema_version": "native_v2_review_repair_v2_post_event_semantic.v1",
        "continuation_manifest": continuation,
        "continuation_digest": digest(continuation),
        "suffix_topology_identity": suffix_topology_identity(wrapper),
        "source_organism_identity": wrapper.base.r0.source_organism_identity(),
        "source_state_identity": wrapper.base.r0.trace_state_identity(),
    }
    value["identity_digest"] = digest(value)
    return value


@dataclass
class FreshScientificJournal:
    """Protocol-compatible journal that binds durable scientific evidence."""

    root: Path
    carrier_root: Path
    adapter: FreshScienceAdapter
    fail_on_kind: str | None = None
    base: DurableHashJournal = field(init=False)
    row_bindings: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.base = DurableHashJournal(self.root, fail_on_kind=self.fail_on_kind)

    def _records(self) -> list[dict[str, Any]]:
        return self.base._records()

    def prepare_seed(
        self,
        seed: int,
        state: Mapping[str, Any],
        outcome_access: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self.base.prepare_seed(seed, state, outcome_access)

    def record_outcome_access(
        self,
        *,
        event_id: str,
        transition_id: str,
        next_guard_manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self.base.append(
            "OUTCOME_ACCESSED",
            seed=self.adapter.seed_ordinal,
            payload={
                "event_id": str(event_id),
                "transition_id": str(transition_id),
                "next_guard_manifest": copy.deepcopy(dict(next_guard_manifest)),
            },
        )

    def commit_row(
        self,
        seed: int,
        row_id: str,
        state: Mapping[str, Any],
        outcome_access: Mapping[str, Any],
    ) -> dict[str, Any]:
        scientific_row = self.adapter.completed_row(row_id)
        row_path = (
            self.carrier_root
            / f"seed-{int(seed):02d}"
            / "rows"
            / f"{row_id}.json"
        )
        atomic_json(row_path, scientific_row)
        payload = row_path.read_bytes()
        binding = {
            "path": _bound_path(row_path),
            "sha256": sha256_bytes(payload),
            "size": len(payload),
            "scientific_row_digest": scientific_row["scientific_row_digest"],
        }
        self.row_bindings.append(binding)
        return self.base.commit_row(
            seed,
            row_id,
            {**copy.deepcopy(dict(state)), "scientific_row_binding": binding},
            outcome_access,
        )

    def _persist_final_snapshots(self, seed: int) -> dict[str, dict[str, Any]]:
        codec = V2SnapshotCodec()
        result = {}
        for arm in ARMS:
            wrapper = self.adapter.staged_arms[arm]
            raw = codec.dumps(wrapper)
            compressed = deterministic_gzip(raw)
            relative = (
                self.carrier_root
                / f"seed-{int(seed):02d}"
                / "final_snapshots"
                / f"{arm}.pkl.gz"
            )
            _atomic_bytes(relative, compressed)
            restored = codec.loads(gzip.decompress(relative.read_bytes()))
            identity = post_event_semantic_identity(wrapper)
            observed = post_event_semantic_identity(restored)
            if identity != observed:
                raise FreshScientificIntegrityError(
                    f"final snapshot semantic restore mismatch:{seed}:{arm}"
                )
            result[arm] = {
                "path": _bound_path(relative),
                "raw_sha256": sha256_bytes(raw),
                "raw_size": len(raw),
                "compressed_sha256": sha256_bytes(compressed),
                "compressed_size": len(compressed),
                "semantic_identity": identity,
                "semantic_identity_digest": digest(identity),
            }
        return result

    def commit_seed(
        self,
        seed: int,
        state: Mapping[str, Any],
        outcome_access: Mapping[str, Any],
    ) -> dict[str, Any]:
        snapshots = self._persist_final_snapshots(seed)
        seed_result = self.adapter.seed_result(self.row_bindings)
        unsigned = {
            key: value for key, value in seed_result.items()
            if key != "seed_result_digest"
        }
        unsigned["final_snapshots"] = snapshots
        seed_result = {**unsigned, "seed_result_digest": digest(unsigned)}
        result_path = (
            self.carrier_root / f"seed-{int(seed):02d}" / "seed_result.json"
        )
        atomic_json(result_path, seed_result)
        payload = result_path.read_bytes()
        binding = {
            "path": _bound_path(result_path),
            "sha256": sha256_bytes(payload),
            "size": len(payload),
            "seed_result_digest": seed_result["seed_result_digest"],
            "final_snapshot_bindings": snapshots,
        }
        return self.base.commit_seed(
            seed,
            {**copy.deepcopy(dict(state)), "scientific_seed_binding": binding},
            outcome_access,
        )

    def fail(
        self, seed: int, detail: str, outcome_access: Mapping[str, Any]
    ) -> None:
        self.base.fail(seed, detail, outcome_access)

    def next_seed(self, seed_ordinals: Sequence[int]) -> int | None:
        return self.base.next_seed(seed_ordinals)

    def restored_outcome_guard(self) -> OutcomeAccessGuard:
        return self.base.restored_outcome_guard()


def verify_bound_preflight_authorization(
    *,
    receipt: Mapping[str, Any],
    snapshot_manifest: Mapping[str, Any],
    authorization: Mapping[str, Any],
    expected_experiment_id: str = EXPERIMENT_ID,
    expected_seed_ordinals: Sequence[int] = tuple(range(SEED_COUNT)),
) -> None:
    auth_unsigned = {
        key: value for key, value in authorization.items()
        if key != "authorization_digest"
    }
    if authorization.get("authorization_digest") != digest(auth_unsigned):
        raise FreshScientificIntegrityError("preflight authorization digest mismatch")
    if authorization.get("experiment_id") != expected_experiment_id:
        raise FreshScientificIntegrityError("foreign preflight experiment")
    receipt_unsigned = {
        key: value for key, value in receipt.items() if key != "receipt_digest"
    }
    if receipt.get("receipt_digest") != canonical_digest(receipt_unsigned):
        raise FreshScientificIntegrityError("preflight receipt self-digest mismatch")
    expected = authorization["expected_global_preflight"]
    checks = {
        "receipt_digest": receipt.get("receipt_digest"),
        "snapshot_manifest_digest": snapshot_manifest.get("manifest_digest"),
        "experiment_identity": snapshot_manifest.get("experiment_id"),
        "registry_package_hash": authorization.get("registry_package_hash"),
    }
    expected_checks = {
        "receipt_digest": expected["receipt_digest"],
        "snapshot_manifest_digest": expected["snapshot_manifest_digest"],
        "experiment_identity": expected_experiment_id,
        "registry_package_hash": expected["registry_package_hash"],
    }
    if checks != expected_checks:
        raise FreshScientificIntegrityError("preflight exact binding mismatch")
    required_ordinals = tuple(map(int, expected_seed_ordinals))
    coverage = receipt.get("coverage")
    if coverage != {
        "seed_count": len(required_ordinals),
        "arm_count": 3,
        "artifact_count": len(required_ordinals) * 3,
        "complete": True,
    }:
        raise FreshScientificIntegrityError("preflight coverage is not exact")
    verification_rows = receipt.get("verification_rows", ())
    keys = {
        (int(item["seed_ordinal"]), str(item["arm"]))
        for item in verification_rows
    }
    required = {(seed, arm) for seed in required_ordinals for arm in ARMS}
    if len(verification_rows) != len(required) or keys != required:
        raise FreshScientificIntegrityError("preflight verification rows incomplete")
    if receipt.get("outcome_access") != {"count": 0, "event_ids": []}:
        raise FreshScientificIntegrityError("preflight receipt opened an outcome")


def execute_fresh_seed_atomically(
    *,
    seed_ordinal: int,
    live_arms: MutableMapping[str, NativeProspectiveAuthorityV2],
    rows: Sequence[Mapping[str, Any]],
    adapter: FreshScienceAdapter,
    journal_root: Path,
    carrier_root: Path,
    environment: FrozenTruthfulEnvironment,
    preflight_receipt: Mapping[str, Any],
    snapshot_manifest: Mapping[str, Any],
    authorization: Mapping[str, Any],
    fail_on_kind: str | None = None,
    expected_experiment_id: str = EXPERIMENT_ID,
    expected_seed_ordinals: Sequence[int] = tuple(range(SEED_COUNT)),
) -> dict[str, Any]:
    verify_bound_preflight_authorization(
        receipt=preflight_receipt,
        snapshot_manifest=snapshot_manifest,
        authorization=authorization,
        expected_experiment_id=expected_experiment_id,
        expected_seed_ordinals=expected_seed_ordinals,
    )
    journal = FreshScientificJournal(
        journal_root,
        carrier_root,
        adapter,
        fail_on_kind=fail_on_kind,
    )
    restored = journal.restored_outcome_guard()
    capability = DurableOutcomeCapability(
        environment=environment,
        journal=journal,
        count=restored.count,
        event_ids=restored.event_ids,
    )
    result = execute_seed_atomically(
        seed=seed_ordinal,
        live_arms=live_arms,
        rows=rows,
        adapter=adapter,
        journal=journal,
        guard=capability,
        preflight_receipt=preflight_receipt,
        snapshot_manifest=snapshot_manifest,
    )
    result["science_journal_chain_digest"] = digest(journal._records())
    return result


def _read_bound_json(binding: Mapping[str, Any]) -> dict[str, Any]:
    path = _resolve_bound_path(str(binding["path"]))
    payload = path.read_bytes()
    if len(payload) != int(binding["size"]) or sha256_bytes(payload) != binding["sha256"]:
        raise FreshScientificIntegrityError("committed carrier transport mismatch")
    return json.loads(payload)


def _restore_final_snapshot(
    snapshot: Mapping[str, Any],
) -> NativeProspectiveAuthorityV2:
    path = _resolve_bound_path(str(snapshot["path"]))
    compressed = path.read_bytes()
    if (
        len(compressed) != int(snapshot["compressed_size"])
        or sha256_bytes(compressed) != snapshot["compressed_sha256"]
    ):
        raise FreshScientificIntegrityError("final snapshot transport mismatch")
    raw = gzip.decompress(compressed)
    if (
        len(raw) != int(snapshot["raw_size"])
        or sha256_bytes(raw) != snapshot["raw_sha256"]
    ):
        raise FreshScientificIntegrityError("final snapshot raw mismatch")
    restored = V2SnapshotCodec().loads(raw)
    observed_identity = post_event_semantic_identity(restored)
    if (
        digest(observed_identity) != snapshot["semantic_identity_digest"]
        or digest(snapshot["semantic_identity"])
        != snapshot["semantic_identity_digest"]
        or canonical_bytes(observed_identity)
        != canonical_bytes(snapshot["semantic_identity"])
    ):
        raise FreshScientificIntegrityError("final snapshot semantic mismatch")
    return restored


def _recompute_endpoint_increments(
    record: Mapping[str, Any],
    *,
    planted_id: str | None,
    spurious_id: str | None,
) -> dict[str, int]:
    available = set(map(
        str, record["production_classification"]["available_cell_ids"]
    ))
    return {
        "false_deployment_authority": int(
            bool(record["production_formal_authority"])
            and not bool(record["truthful_outcome"])
        ),
        "selected_spurious_attributable_false_authority": int(
            spurious_id is not None
            and spurious_id in available
            and not bool(record["truthful_outcome"])
        ),
        "planted_authority_coverage": int(
            record["visible_family"] == "suffix_planted"
            and planted_id is not None
            and planted_id in available
        ),
    }


def _validate_seed_journal_sequence(
    records: Sequence[Mapping[str, Any]],
    *,
    seed: int,
    row_ids: Sequence[str],
) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]], Mapping[str, Any]]:
    seed_records = [row for row in records if int(row["seed_ordinal"]) == seed]
    expected_kinds = ["PREPARED"]
    for _row_id in row_ids:
        expected_kinds.extend([
            "OUTCOME_ACCESSED",
            "OUTCOME_ACCESSED",
            "OUTCOME_ACCESSED",
            "TRI_ARM_ROW_COMMITTED",
        ])
    expected_kinds.append("COMMITTED")
    if [row["kind"] for row in seed_records] != expected_kinds:
        raise FreshScientificIntegrityError(
            f"seed journal sequence differs from frozen 16-row law:{seed}"
        )
    prepared = seed_records[0]
    committed = seed_records[-1]
    outcome_rows = [row for row in seed_records if row["kind"] == "OUTCOME_ACCESSED"]
    row_commits = [
        row for row in seed_records if row["kind"] == "TRI_ARM_ROW_COMMITTED"
    ]
    if len(outcome_rows) != 3 * len(row_ids) or len(row_commits) != len(row_ids):
        raise FreshScientificIntegrityError("seed journal row/read count mismatch")
    if [str(row["payload"]["row_id"]) for row in row_commits] != list(row_ids):
        raise FreshScientificIntegrityError("committed row order mismatch")
    start_guard = prepared["payload"]["outcome_access"]
    expected_count = int(start_guard["count"])
    expected_event_ids = list(map(str, start_guard["event_ids"]))
    for row_id, arm, journal_row in zip(
        (row_id for row_id in row_ids for _arm in ARMS),
        (arm for _row_id in row_ids for arm in ARMS),
        outcome_rows,
        strict=True,
    ):
        expected_event_id = f"seed-{seed:02d}:{row_id}:{arm}"
        payload = journal_row["payload"]
        if payload["event_id"] != expected_event_id:
            raise FreshScientificIntegrityError("outcome-read identity/order mismatch")
        expected_count += 1
        expected_event_ids.append(expected_event_id)
        if payload["next_guard_manifest"] != {
            "count": expected_count,
            "event_ids": expected_event_ids,
        }:
            raise FreshScientificIntegrityError("outcome-read sequence mismatch")
    expected_guard = {"count": expected_count, "event_ids": expected_event_ids}
    if committed["payload"]["outcome_access"] != expected_guard:
        raise FreshScientificIntegrityError("committed outcome-read total mismatch")
    if expected_count - int(start_guard["count"]) != 3 * len(row_ids):
        raise FreshScientificIntegrityError("seed did not read exactly 48 outcomes")
    return row_commits, outcome_rows, committed


def committed_seed_results(
    journal: FreshScientificJournal | DurableHashJournal,
    *,
    expected_ordinals: Sequence[int],
    expected_rows: Sequence[Mapping[str, Any]],
    baseline_wrappers: Mapping[tuple[int, str], NativeProspectiveAuthorityV2],
    expected_seed_metadata: Mapping[int, Mapping[str, Any]],
    environment_manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    records = journal._records()
    committed = [row for row in records if row["kind"] == "COMMITTED"]
    expected = tuple(map(int, expected_ordinals))
    by_seed = {int(row["seed_ordinal"]): row for row in committed}
    if tuple(sorted(by_seed)) != tuple(sorted(expected)) or len(committed) != len(expected):
        raise FreshScientificIntegrityError("COMMITTED seed coverage mismatch")
    row_ids = tuple(str(row["row_id"]) for row in expected_rows)
    if len(row_ids) != 16 or len(set(row_ids)) != 16:
        raise FreshScientificIntegrityError("frozen suffix must contain exact 16 rows")
    expected_row_map = {str(row["row_id"]): row for row in expected_rows}
    transitions = {
        str(item["transition_id"]): item
        for item in environment_manifest["transitions"]
    }
    results = []
    for seed in expected:
        metadata = expected_seed_metadata[int(seed)]
        expected_genome_seed = int(metadata["genome_seed"])
        expected_targets = metadata["targets"]
        planted_id = target_cell_id(expected_targets, "planted")
        spurious_id = target_cell_id(expected_targets, "selected_spurious")
        row_commits, outcome_rows, committed_record = _validate_seed_journal_sequence(
            records, seed=seed, row_ids=row_ids
        )
        for journal_row, (journal_row_id, journal_arm) in zip(
            outcome_rows,
            ((row_id, arm) for row_id in row_ids for arm in ARMS),
            strict=True,
        ):
            expected_transition_id = str(
                expected_row_map[journal_row_id]["arms"][journal_arm][
                    "transition_id"
                ]
            )
            if journal_row["payload"]["transition_id"] != expected_transition_id:
                raise FreshScientificIntegrityError(
                    "journal/row transition mismatch"
                )
        binding = committed_record["payload"]["final_state"].get(
            "scientific_seed_binding"
        )
        if not isinstance(binding, dict):
            raise FreshScientificIntegrityError("COMMITTED lacks scientific binding")
        seed_result = _read_bound_json(binding)
        unsigned = {
            key: value for key, value in seed_result.items()
            if key != "seed_result_digest"
        }
        if seed_result.get("seed_result_digest") != digest(unsigned):
            raise FreshScientificIntegrityError("seed result digest mismatch")
        if seed_result["seed_result_digest"] != binding["seed_result_digest"]:
            raise FreshScientificIntegrityError("journal/seed result identity mismatch")
        if (
            int(seed_result["seed_ordinal"]) != seed
            or int(seed_result["genome_seed"]) != expected_genome_seed
            or seed_result["targets"] != expected_targets
        ):
            raise FreshScientificIntegrityError("foreign seed metadata in committed result")
        if len(seed_result["row_bindings"]) != len(row_ids):
            raise FreshScientificIntegrityError("committed row binding count mismatch")

        baseline = {
            arm: baseline_wrappers[(seed, arm)] for arm in ARMS
        }
        baseline_contract = exact_arm_identity_contract(baseline)
        if seed_result["identity_contract_digest"] != baseline_contract["contract_digest"]:
            raise FreshScientificIntegrityError("seed identity contract changed")
        initial_states = {
            arm: {
                cell_id: state.manifest()
                for cell_id, state in sorted(baseline[arm].states.items())
            }
            for arm in ARMS
        }
        immediate = {
            arm: sorted(
                cell_id for cell_id, state in baseline[arm].states.items()
                if state.prospectively_certified
            )
            for arm in ARMS
        }
        if seed_result["initial_states"] != initial_states:
            raise FreshScientificIntegrityError("stored initial-state summary mismatch")
        if seed_result["immediate_authority_cell_ids"] != immediate:
            raise FreshScientificIntegrityError("stored initial decision summary mismatch")

        endpoint_totals = {
            arm: {
                "false_deployment_authority": 0,
                "selected_spurious_attributable_false_authority": 0,
                "planted_authority_coverage": 0,
            }
            for arm in ARMS
        }
        rows: list[dict[str, Any]] = []
        expected_core = {
            arm: {
                cell_id: {
                    "support": int(state.support),
                    "successes": int(state.successes),
                    "contradictions": int(state.contradictions),
                    "prospectively_certified": bool(state.prospectively_certified),
                }
                for cell_id, state in baseline[arm].states.items()
            }
            for arm in ARMS
        }
        prior_continuation = {
            arm: baseline[arm].continuation_digest() for arm in ARMS
        }
        observed_emissions: dict[str, dict[str, dict[str, Any]]] = {
            arm: {} for arm in ARMS
        }
        for index, (row_id, row_binding, row_commit) in enumerate(zip(
            row_ids, seed_result["row_bindings"], row_commits, strict=True
        )):
            committed_binding = row_commit["payload"]["staged_state"].get(
                "scientific_row_binding"
            )
            if committed_binding != row_binding:
                raise FreshScientificIntegrityError("journal/row carrier mismatch")
            row = _read_bound_json(row_binding)
            row_unsigned = {
                key: value for key, value in row.items()
                if key != "scientific_row_digest"
            }
            if row.get("scientific_row_digest") != digest(row_unsigned):
                raise FreshScientificIntegrityError("scientific row digest mismatch")
            if (
                row["row_id"] != row_id
                or int(row["seed_ordinal"]) != seed
                or int(row["genome_seed"]) != expected_genome_seed
                or set(row["arms"]) != set(ARMS)
            ):
                raise FreshScientificIntegrityError("missing, duplicated, or foreign row")
            plan_row = expected_row_map[row_id]
            for arm in ARMS:
                record = row["arms"][arm]
                if record.get("result_record_digest") != digest({
                    key: value for key, value in record.items()
                    if key != "result_record_digest"
                }):
                    raise FreshScientificIntegrityError("arm row digest mismatch")
                plan = plan_row["arms"][arm]
                transition_id = str(plan["transition_id"])
                transition = transitions[transition_id]
                if (
                    record["arm"] != arm
                    or record["row_id"] != row_id
                    or record["visible_family"] != plan_row["visible_family"]
                    or record["transition_id"] != transition_id
                    or record["truthful_predecessor_fen"]
                    != transition["predecessor_fen"]
                    or record["truthful_action_uci"] != transition["move_uci"]
                    or record["truthful_successor_fen"] != transition["successor_fen"]
                    or bool(record["truthful_outcome"])
                    is not bool(transition["outcome"])
                ):
                    raise FreshScientificIntegrityError("row differs from frozen transition")
                if record["pre_outcome_continuation_digest"] != prior_continuation[arm]:
                    raise FreshScientificIntegrityError("row continuation order mismatch")
                receipt = record["grounded_receipt"]
                emission = record["graph_authority_emission"]
                if (
                    emission["receipt_id"] != receipt["receipt_id"]
                    or set(emission["matching_cell_ids"])
                    != set(record["matching_cell_commitment"])
                    or set(emission["supporting_cell_ids"]).intersection(
                        emission["contradiction_cell_ids"]
                    )
                    or set(emission["supporting_cell_ids"]).union(
                        emission["contradiction_cell_ids"]
                    ) != set(emission["matching_cell_ids"])
                    or emission["matured_cell_ids"] != emission["graph_maturity_ids"]
                    or emission["revoked_cell_ids"] != emission["graph_revocation_ids"]
                ):
                    raise FreshScientificIntegrityError("row graph emission mismatch")
                increments = _recompute_endpoint_increments(
                    record, planted_id=planted_id, spurious_id=spurious_id
                )
                if record["endpoint_increments"] != increments:
                    raise FreshScientificIntegrityError("stored endpoint increment mismatch")
                for name, increment in increments.items():
                    endpoint_totals[arm][name] += int(increment)
                for cell_id in emission["matching_cell_ids"]:
                    if cell_id not in expected_core[arm]:
                        raise FreshScientificIntegrityError("row names a foreign cell")
                    expected_core[arm][cell_id]["support"] += 1
                    if cell_id in emission["supporting_cell_ids"]:
                        expected_core[arm][cell_id]["successes"] += 1
                    else:
                        expected_core[arm][cell_id]["contradictions"] += 1
                    if cell_id in emission["graph_maturity_ids"]:
                        expected_core[arm][cell_id]["prospectively_certified"] = True
                    if cell_id in emission["graph_revocation_ids"]:
                        expected_core[arm][cell_id]["prospectively_certified"] = False
                observed_emissions[arm][receipt["receipt_id"]] = copy.deepcopy(emission)
                prior_continuation[arm] = record["post_event_continuation_digest"]
                staged = row_commit["payload"]["staged_state"][arm]
                if staged["continuation_digest"] != prior_continuation[arm]:
                    raise FreshScientificIntegrityError("row/journal continuation mismatch")
            rows.append(row)

        if seed_result["endpoints"] != endpoint_totals:
            raise FreshScientificIntegrityError("stored endpoint summary mismatch")
        clearing_summary = summarize_clearing_events(rows, expected_targets)
        if seed_result["clearing_summary"] != clearing_summary:
            raise FreshScientificIntegrityError("stored clearing summary mismatch")

        final_wrappers = {
            arm: _restore_final_snapshot(seed_result["final_snapshots"][arm])
            for arm in ARMS
        }
        final_cell_states = {
            arm: {
                cell_id: state.manifest()
                for cell_id, state in sorted(final_wrappers[arm].states.items())
            }
            for arm in ARMS
        }
        final_targets = {
            arm: {
                name: (
                    None if target_cell_id(expected_targets, name) is None
                    else final_cell_states[arm][target_cell_id(expected_targets, name)]
                )
                for name in ("planted", "selected_spurious")
            }
            for arm in ARMS
        }
        final_continuations = {
            arm: final_wrappers[arm].continuation_digest() for arm in ARMS
        }
        final_ordinals = {
            arm: int(final_wrappers[arm].next_expected_ordinal) for arm in ARMS
        }
        final_emission_digests = {
            arm: digest({
                receipt_id: emission.manifest()
                for receipt_id, emission in sorted(final_wrappers[arm].emissions.items())
            })
            for arm in ARMS
        }
        for arm in ARMS:
            if final_continuations[arm] != prior_continuation[arm]:
                raise FreshScientificIntegrityError("final row/snapshot continuation mismatch")
            if final_ordinals[arm] != baseline[arm].next_expected_ordinal + len(row_ids):
                raise FreshScientificIntegrityError("final event ordinal mismatch")
            for cell_id, expected_state in expected_core[arm].items():
                actual = final_wrappers[arm].states[cell_id]
                for name, expected_value in expected_state.items():
                    if getattr(actual, name) != expected_value:
                        raise FreshScientificIntegrityError(
                            f"final support/contradiction state mismatch:{arm}:{cell_id}:{name}"
                        )
            for receipt_id, emission in observed_emissions[arm].items():
                final_emission = final_wrappers[arm].emissions.get(receipt_id)
                if (
                    final_emission is None
                    or canonical_bytes(final_emission.manifest())
                    != canonical_bytes(emission)
                ):
                    raise FreshScientificIntegrityError("final graph emission mismatch")
        comparisons = {
            "target_final_states": final_targets,
            "final_cell_states": final_cell_states,
            "final_continuation_digests": final_continuations,
            "final_event_ordinals": final_ordinals,
            "final_emission_digests": final_emission_digests,
        }
        for name, observed in comparisons.items():
            if seed_result[name] != observed:
                raise FreshScientificIntegrityError(f"stored {name} summary mismatch")
        for arm in ARMS:
            journal_state = committed_record["payload"]["final_state"][arm]
            if (
                journal_state["continuation_digest"] != final_continuations[arm]
                or journal_state["suffix_topology_identity_digest"]
                != digest(suffix_topology_identity(final_wrappers[arm]))
            ):
                raise FreshScientificIntegrityError("journal/final snapshot mismatch")

        reconstructed = copy.deepcopy(seed_result)
        reconstructed.update({
            "endpoints": endpoint_totals,
            "clearing_summary": clearing_summary,
            "initial_states": initial_states,
            "immediate_authority_cell_ids": immediate,
            **comparisons,
            "reconstruction": {
                "row_count": len(rows),
                "row_order": list(row_ids),
                "outcome_read_count": len(outcome_rows),
                "row_record_set_digest": digest(rows),
                "journal_seed_record_digest": digest([
                    row for row in records if int(row["seed_ordinal"]) == seed
                ]),
                "independent_row_and_snapshot_agreement": True,
            },
        })
        reconstructed["recomputed_result_digest"] = digest({
            key: value for key, value in reconstructed.items()
            if key != "recomputed_result_digest"
        })
        results.append(reconstructed)
    return results



def exact_one_sided_sign_test(values: Sequence[int]) -> dict[str, Any]:
    wins = sum(value > 0 for value in values)
    losses = sum(value < 0 for value in values)
    ties = sum(value == 0 for value in values)
    n = wins + losses
    p = 1.0 if n == 0 else sum(
        math.comb(n, k) for k in range(wins, n + 1)
    ) / (2 ** n)
    return {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "non_tied_effective_n": n,
        "one_sided_exact_p": p,
    }


def holm_adjust_two(raw: Mapping[str, float]) -> dict[str, float]:
    if set(raw) != {"D_safe", "D_signal"}:
        raise FreshScientificIntegrityError("Holm family must be exactly two")
    first, second = sorted(raw, key=lambda key: (raw[key], key))
    adjusted_first = min(1.0, 2.0 * raw[first])
    adjusted_second = min(1.0, max(adjusted_first, raw[second]))
    return {first: adjusted_first, second: adjusted_second}


def _percentile(values: Sequence[float], q: float) -> float:
    ordered = sorted(map(float, values))
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def paired_bootstrap(values: Sequence[int], *, cohort_identity: str, label: str) -> dict[str, Any]:
    if len(values) != SEED_COUNT:
        raise FreshScientificIntegrityError("bootstrap requires all 32 seeds")
    seed = int.from_bytes(
        hashlib.sha256(
            f"{EXPERIMENT_ID}|bootstrap|{cohort_identity}|{label}".encode("utf-8")
        ).digest()[:8],
        "big",
    ) & ((1 << 63) - 1)
    rng = random.Random(seed or 1)
    source = list(map(float, values))
    means = []
    medians = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sample = [source[rng.randrange(SEED_COUNT)] for _ in range(SEED_COUNT)]
        means.append(math.fsum(sample) / SEED_COUNT)
        ordered = sorted(sample)
        medians.append((ordered[15] + ordered[16]) / 2.0)
    ordered_source = sorted(source)
    return {
        "replicates": BOOTSTRAP_REPLICATES,
        "seed": seed or 1,
        "mean": math.fsum(source) / SEED_COUNT,
        "median": (ordered_source[15] + ordered_source[16]) / 2.0,
        "mean_ci_95": [_percentile(means, 0.025), _percentile(means, 0.975)],
        "median_ci_95": [_percentile(medians, 0.025), _percentile(medians, 0.975)],
        "descriptive_only": True,
    }


def summarize_clearing_events(
    rows: Sequence[Mapping[str, Any]],
    targets: Mapping[str, Any],
) -> dict[str, Any]:
    """Check every contradiction that occurred while a cell affected a decision."""

    planted_id = target_cell_id(targets, "planted")
    spurious_id = target_cell_id(targets, "selected_spurious")
    events: list[dict[str, Any]] = []
    contradiction_event_count = 0
    for row in rows:
        for arm in ARMS:
            record = row["arms"][arm]
            classification = record["production_classification"]
            decision_cells = set(map(str, classification["available_cell_ids"]))
            emission = record["graph_authority_emission"]
            contradictions = set(map(str, emission["contradiction_cell_ids"]))
            graph_clearings = set(map(str, emission["graph_revocation_ids"]))
            contradiction_event_count += len(contradictions)
            for cell_id in sorted(decision_cells.intersection(contradictions)):
                events.append({
                    "row_id": str(row["row_id"]),
                    "arm": arm,
                    "cell_id": cell_id,
                    "is_planted_target": cell_id == planted_id,
                    "is_selected_spurious_target": cell_id == spurious_id,
                    "graph_clearing_emitted": cell_id in graph_clearings,
                    "grounded_receipt_id": record["grounded_receipt"]["receipt_id"],
                })
    missing = [item for item in events if not item["graph_clearing_emitted"]]
    result = {
        "contradiction_event_count": contradiction_event_count,
        "decision_bearing_contradiction_count": len(events),
        "graph_clearing_count": sum(
            item["graph_clearing_emitted"] for item in events
        ),
        "missing_graph_clearing_count": len(missing),
        "selected_spurious_B_checked_count": sum(
            item["arm"] == "B" and item["is_selected_spurious_target"]
            for item in events
        ),
        "all_required_graph_clearings_emitted": not missing,
        "events": events,
        "missing_events": missing,
    }
    result["clearing_summary_digest"] = digest(result)
    return result


def engagement_for_seed(result: Mapping[str, Any]) -> dict[str, Any]:
    states = result["initial_states"]
    immediate = result["immediate_authority_cell_ids"]
    final = result["target_final_states"]
    clearing = result["clearing_summary"]
    a_planted = final["A"]["planted"]
    a_spurious = final["A"]["selected_spurious"]
    c_planted = final["C"]["planted"]
    b_lawful = all(
        (cell_id in set(immediate["B"])) is bool(
            state["hypothesis"]["structural_state"] == StemCellState.MATURE.name
        )
        for cell_id, state in states["B"].items()
    )
    planted_engaged = bool(
        a_planted is not None
        and a_planted["support"] >= MIN_TARGET_OPPORTUNITIES
        and a_planted["contradictions"] == 0
        and a_planted["prospectively_certified"]
    )
    spurious_contradicted = bool(
        a_spurious is not None and a_spurious["contradictions"] >= 1
    )
    c_broke = bool(
        c_planted is not None
        and c_planted["contradictions"] >= MIN_TARGET_OPPORTUNITIES
    )
    all_clearings = bool(clearing["all_required_graph_clearings_emitted"])
    engaged = bool(
        not immediate["A"]
        and not immediate["C"]
        and b_lawful
        and planted_engaged
        and spurious_contradicted
        and c_broke
        and all_clearings
    )
    return {
        "zero_immediate_A": not immediate["A"],
        "zero_immediate_C": not immediate["C"],
        "lawful_legacy_B": b_lawful,
        "planted_A_later_certified": planted_engaged,
        "spurious_A_later_contradicted": spurious_contradicted,
        "C_broke_planted_association": c_broke,
        "all_required_graph_clearings_emitted": all_clearings,
        "decision_bearing_contradiction_count": clearing[
            "decision_bearing_contradiction_count"
        ],
        "graph_clearing_count": clearing["graph_clearing_count"],
        "missing_graph_clearing_count": clearing[
            "missing_graph_clearing_count"
        ],
        "selected_spurious_B_checked_count": clearing[
            "selected_spurious_B_checked_count"
        ],
        "engaged": engaged,
    }


def adjudicate_committed_results(
    seed_results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    ordered = sorted(seed_results, key=lambda item: int(item["seed_ordinal"]))
    if [int(item["seed_ordinal"]) for item in ordered] != list(range(SEED_COUNT)):
        raise FreshScientificIntegrityError("all 32 committed seeds are required")
    cohort_identity = digest([item["seed_result_digest"] for item in ordered])
    d_safe: list[int] = []
    d_signal: list[int] = []
    per_seed = []
    for result in ordered:
        endpoints = result["endpoints"]
        safe = (
            endpoints["B"]["false_deployment_authority"]
            - endpoints["A"]["false_deployment_authority"]
        )
        signal = (
            endpoints["A"]["planted_authority_coverage"]
            - endpoints["C"]["planted_authority_coverage"]
        )
        engagement = engagement_for_seed(result)
        d_safe.append(safe)
        d_signal.append(signal)
        per_seed.append({
            "ordinal": int(result["seed_ordinal"]),
            "genome_seed": int(result["genome_seed"]),
            "D_safe": safe,
            "D_signal": signal,
            "engagement": engagement,
            "endpoints": copy.deepcopy(endpoints),
        })
    planted_count = sum(
        row["engagement"]["planted_A_later_certified"] for row in per_seed
    )
    spurious_count = sum(
        row["engagement"]["spurious_A_later_contradicted"] for row in per_seed
    )
    c_break_count = sum(
        row["engagement"]["C_broke_planted_association"] for row in per_seed
    )
    fully_engaged_count = sum(row["engagement"]["engaged"] for row in per_seed)
    missing_clearings = sum(
        row["engagement"]["missing_graph_clearing_count"] for row in per_seed
    )
    decision_bearing_contradictions = sum(
        row["engagement"]["decision_bearing_contradiction_count"]
        for row in per_seed
    )
    graph_clearings = sum(
        row["engagement"]["graph_clearing_count"] for row in per_seed
    )
    mechanism_engaged = bool(
        planted_count >= MIN_QUALIFYING_SEEDS
        and spurious_count >= MIN_QUALIFYING_SEEDS
        and c_break_count >= MIN_QUALIFYING_SEEDS
        and fully_engaged_count >= MIN_QUALIFYING_SEEDS
        and missing_clearings == 0
        and all(row["engagement"]["zero_immediate_A"] for row in per_seed)
        and all(row["engagement"]["zero_immediate_C"] for row in per_seed)
        and all(row["engagement"]["lawful_legacy_B"] for row in per_seed)
    )
    tests = {
        "D_safe": exact_one_sided_sign_test(d_safe),
        "D_signal": exact_one_sided_sign_test(d_signal),
    }
    adjusted = holm_adjust_two({
        name: value["one_sided_exact_p"] for name, value in tests.items()
    })
    for name, values in (("D_safe", d_safe), ("D_signal", d_signal)):
        tests[name]["holm_adjusted_p"] = adjusted[name]
        tests[name]["favorable_all_32"] = sum(value > 0 for value in values)
        tests[name]["paired_values"] = list(values)
        tests[name]["descriptive_effect"] = paired_bootstrap(
            values, cohort_identity=cohort_identity, label=name
        )
        tests[name]["passed"] = bool(
            adjusted[name] <= PRIMARY_ALPHA
            and sum(value > 0 for value in values) >= MIN_FAVORABLE_SEEDS
        )
    primary_pass = bool(
        mechanism_engaged and all(value["passed"] for value in tests.values())
    )
    if not mechanism_engaged:
        verdict = "mechanism_contrast_starvation"
    elif primary_pass:
        verdict = "prospective_evidence_separation_supported_in_frozen_ecology"
    else:
        verdict = "valid_negative_prospective_separation_not_supported"
    result = {
        "schema_version": "native_v2_review_repair_v2_committed_adjudication.v1",
        "experiment_id": EXPERIMENT_ID,
        "inferential_unit": "genome_seed",
        "all_32_retained": True,
        "qualified_only_inference": False,
        "cohort_identity": cohort_identity,
        "engagement": {
            "planted_A_certified_count": planted_count,
            "spurious_A_contradicted_count": spurious_count,
            "C_planted_contradiction_dose_count": c_break_count,
            "decision_bearing_contradiction_count": decision_bearing_contradictions,
            "graph_clearing_count": graph_clearings,
            "missing_graph_clearing_count": missing_clearings,
            "fully_engaged_count": fully_engaged_count,
            "required": MIN_QUALIFYING_SEEDS,
            "C_dose_passed": c_break_count >= MIN_QUALIFYING_SEEDS,
            "clearing_passed": missing_clearings == 0,
            "complete_conjunction_passed": (
                fully_engaged_count >= MIN_QUALIFYING_SEEDS
            ),
            "passed": mechanism_engaged,
        },
        "primary_tests": tests,
        "both_primary_pass": primary_pass,
        "per_seed": per_seed,
        "verdict": verdict,
        "causal_interpretation_authorized": mechanism_engaged,
    }
    result["adjudication_digest"] = digest(result)
    return result



def derive_seed(source_freeze_commit: str, ordinal: int) -> dict[str, Any]:
    text = f"{EXPERIMENT_ID}|canonical|{source_freeze_commit}|{int(ordinal)}"
    derivation = hashlib.sha256(text.encode("utf-8")).hexdigest()
    seed = int.from_bytes(bytes.fromhex(derivation)[:8], "big") & ((1 << 63) - 1)
    return {
        "ordinal": int(ordinal),
        "genome_seed": seed or 1,
        "derivation_sha256": derivation,
    }


def build_seed_manifest(source_freeze_commit: str) -> dict[str, Any]:
    rows = [derive_seed(source_freeze_commit, ordinal) for ordinal in range(SEED_COUNT)]
    if len({row["genome_seed"] for row in rows}) != SEED_COUNT:
        raise FreshScientificIntegrityError("commit-derived genome seed collision")
    value = {
        "schema_version": "native_v2_review_repair_v2_seed_manifest.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_freeze_commit": source_freeze_commit,
        "derivation_text": (
            "experiment_id|canonical|source_freeze_commit|ordinal"
        ),
        "seed_count": SEED_COUNT,
        "retain_all": True,
        "rows": rows,
    }
    value["seed_manifest_digest"] = digest(value)
    return value


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _transition_rows_from_ecology(
    relative: Path, *, source: str
) -> tuple[dict[str, Any], ...]:
    ecology = _load_json(ROOT / relative)
    rows: list[dict[str, Any]] = []
    if isinstance(ecology.get("transitions"), list):
        for item in ecology["transitions"]:
            transition = transition_manifest(
                str(item["predecessor_fen"]), str(item["move_uci"])
            )
            if (
                transition["successor_fen"] != item["successor_fen"]
                or transition["physical_transition_digest"]
                != item["physical_transition_digest"]
            ):
                raise FreshScientificIntegrityError(
                    f"earlier ecology transition changed:{relative}"
                )
            rows.append({
                "source": source,
                "row_id": str(item.get("transition_id", len(rows))),
                **transition,
            })
    else:
        for item in ecology["rows"]:
            for arm, fen in (("A", item["a_fen"]), ("C", item["c_fen"])):
                rows.append({
                    "source": source,
                    "row_id": str(item["row_id"]),
                    "arm": arm,
                    **transition_manifest(str(fen), str(item["move_uci"])),
                })
    if len(rows) != 160:
        raise FreshScientificIntegrityError(
            f"earlier ecology interaction count changed:{relative}:{len(rows)}"
        )
    return tuple(rows)


def _old_physical_transition_rows() -> tuple[dict[str, Any], ...]:
    return _transition_rows_from_ecology(
        OLD_PACKAGE_DIR / "ecology_manifest.json",
        source="retired_v2_complete_A_C_prefix_suffix",
    )


def retired_transition_inventory() -> dict[str, Any]:
    rows = _old_physical_transition_rows()
    return {
        "starting_fens": sorted({row["predecessor_fen"] for row in rows}),
        "resulting_fens": sorted({row["successor_fen"] for row in rows}),
        "transition_digests": sorted({row["physical_transition_digest"] for row in rows}),
        "rows": list(rows),
    }


def _old_prefix_fingerprints() -> set[str]:
    from . import native_prospective_evidence_v2_science as retired
    from .native_v2_atomic_snapshot_harness import legacy_main_graph_compatibility

    manifest = _load_json(ROOT / OLD_PACKAGE_DIR / "prefix_candidate_manifest.json")
    values = set()
    for entry in manifest["results"]:
        with legacy_main_graph_compatibility():
            wrapper = retired.load_prefix_wrapper(entry)
        values.update(map(str, wrapper.discovery_prefix_physical_fingerprints))
    return values


def _position_sets(rows: Sequence[Mapping[str, Any]]) -> dict[str, set[str]]:
    return {
        "starting_positions": {str(row["predecessor_fen"]) for row in rows},
        "resulting_positions": {str(row["successor_fen"]) for row in rows},
        "complete_transitions": {
            str(row["physical_transition_digest"]) for row in rows
        },
    }


def _overlap_measurement(
    candidate: Mapping[str, set[str]],
    earlier: Mapping[str, set[str]],
    *,
    candidate_stable_ids: set[str],
    earlier_stable_ids: set[str],
) -> dict[str, Any]:
    values = {}
    for name in ("starting_positions", "resulting_positions", "complete_transitions"):
        overlap = sorted(candidate[name].intersection(earlier[name]))
        values[name] = {"count": len(overlap), "values": overlap}
    stable = sorted(candidate_stable_ids.intersection(earlier_stable_ids))
    values["stable_interaction_ids"] = {"count": len(stable), "values": stable}
    values["measurement_digest"] = digest(values)
    return values


def build_excluded_position_manifest(
    toy_ecology: Mapping[str, Any]
) -> dict[str, Any]:
    source_paths = (
        (
            "retired_v2_scientific_ecology",
            OLD_PACKAGE_DIR / "ecology_manifest.json",
        ),
        (
            "retired_actual_v2_canary_ecology",
            SUPERSEDED_PACKAGE_DIR / "retired_actual_v2_canary_ecology.json",
        ),
        (
            "superseded_unused_fresh_freeze",
            SUPERSEDED_PACKAGE_DIR / "ecology_manifest.json",
        ),
    )
    source_rows = {
        name: _transition_rows_from_ecology(path, source=name)
        for name, path in source_paths
    }
    toy_rows = tuple({
        "source": "replacement_retired_canary_ecology",
        "row_id": str(item["transition_id"]),
        **transition_manifest(str(item["predecessor_fen"]), str(item["move_uci"])),
    } for item in toy_ecology["transitions"])
    if len(toy_rows) != 160:
        raise FreshScientificIntegrityError("replacement canary interaction count changed")
    source_rows["replacement_retired_canary_ecology"] = toy_rows

    superseded_excluded = _load_json(
        ROOT / SUPERSEDED_PACKAGE_DIR / "physical_denylist.json"
    )
    superseded_outer = _load_json(
        ROOT / SUPERSEDED_PACKAGE_DIR / "outer_manifest.json"
    )
    earlier_stable_ids = set(map(
        str, superseded_excluded["denied_v2_1_physical_fingerprints"]
    ))
    superseded_stable_ids = set(map(
        str,
        superseded_outer["ecology_graph_validation"]["physical_fingerprints"],
    ))
    toy_validation = validate_ecology_graph(toy_ecology)
    all_stable_ids = (
        earlier_stable_ids
        | superseded_stable_ids
        | set(map(str, toy_validation["physical_fingerprints"]))
    )

    earlier_rows = (
        *source_rows["retired_v2_scientific_ecology"],
        *source_rows["retired_actual_v2_canary_ecology"],
    )
    superseded_rows = source_rows["superseded_unused_fresh_freeze"]
    superseded_comparison = _overlap_measurement(
        _position_sets(superseded_rows),
        _position_sets(earlier_rows),
        candidate_stable_ids=superseded_stable_ids,
        earlier_stable_ids=earlier_stable_ids,
    )

    all_rows = tuple(row for rows in source_rows.values() for row in rows)
    positions = _position_sets(all_rows)
    all_positions = positions["starting_positions"] | positions["resulting_positions"]
    value = {
        "schema_version": "native_v2_review_repair_v2_excluded_positions.v1",
        "experiment_id": EXPERIMENT_ID,
        "selection_rule": (
            "every_starting_and_resulting_position_from_all_earlier_V2_"
            "ecologies_and_canaries_including_superseded_unused_freeze"
        ),
        "source_hashes": {
            str(path): sha256_file(ROOT / path) for _name, path in source_paths
        } | {
            str(TOY_ECOLOGY_PATH): sha256_file(ROOT / TOY_ECOLOGY_PATH),
            str(SUPERSEDED_PACKAGE_DIR / "physical_denylist.json"): sha256_file(
                ROOT / SUPERSEDED_PACKAGE_DIR / "physical_denylist.json"
            ),
            str(SUPERSEDED_PACKAGE_DIR / "outer_manifest.json"): sha256_file(
                ROOT / SUPERSEDED_PACKAGE_DIR / "outer_manifest.json"
            ),
        },
        "source_interaction_counts": {
            name: len(rows) for name, rows in source_rows.items()
        },
        "excluded_starting_fens": sorted(positions["starting_positions"]),
        "excluded_resulting_fens": sorted(positions["resulting_positions"]),
        "excluded_all_position_fens": sorted(all_positions),
        "excluded_transition_digests": sorted(positions["complete_transitions"]),
        "excluded_stable_interaction_ids": sorted(all_stable_ids),
        "superseded_overlap_comparison": superseded_comparison,
        "counts": {
            "starting_positions": len(positions["starting_positions"]),
            "resulting_positions": len(positions["resulting_positions"]),
            "all_positions": len(all_positions),
            "complete_transitions": len(positions["complete_transitions"]),
            "stable_interaction_ids": len(all_stable_ids),
        },
    }
    value["excluded_position_manifest_digest"] = digest(value)
    return value



def build_environment_manifest(
    ecology: Mapping[str, Any], *, experiment_id: str = EXPERIMENT_ID
) -> dict[str, Any]:
    transitions = [copy.deepcopy(dict(item)) for item in ecology["transitions"]]
    value = {
        "schema_version": "native_v2_review_repair_v2_truthful_environment.v1",
        "experiment_id": experiment_id,
        "ecology_digest": ecology["ecology_digest"],
        "outcome_capability_required": True,
        "completion_terminal_identity": "mate",
        "transition_count": len(transitions),
        "transitions": transitions,
    }
    value["environment_digest"] = digest(value)
    return value


def build_permutation_manifest(ecology: Mapping[str, Any]) -> dict[str, Any]:
    transitions = environment_transitions(ecology)
    rows = []
    for row in ecology_rows(ecology, "suffix"):
        a = transitions[str(row["A_transition_id"])]
        c = transitions[str(row["C_transition_id"])]
        rows.append({
            "row_id": row["row_id"],
            "visible_family": row["visible_family"],
            "visible_atom_ids": list(row["active_atom_ids"]),
            "A_transition_id": row["A_transition_id"],
            "C_transition_id": row["C_transition_id"],
            "A_transition": copy.deepcopy(a),
            "C_transition": copy.deepcopy(c),
            "permutation_operation": "swap_within_frozen_opposite_outcome_pair",
        })
        if bool(a["outcome"]) is bool(c["outcome"]):
            raise FreshScientificIntegrityError("C permutation did not reverse truth")
    value = {
        "schema_version": "native_v2_review_repair_v2_c_permutation.v1",
        "experiment_id": EXPERIMENT_ID,
        "truthful_transitions": True,
        "label_shuffle": False,
        "row_count": len(rows),
        "outcome_marginals_preserved": (
            sum(item["A_transition"]["outcome"] for item in rows)
            == sum(item["C_transition"]["outcome"] for item in rows)
        ),
        "rows": rows,
    }
    value["permutation_digest"] = digest(value)
    return value


def verify_physical_freshness(
    ecology: Mapping[str, Any],
    validation: Mapping[str, Any],
    excluded: Mapping[str, Any],
) -> dict[str, Any]:
    transitions = environment_transitions(ecology)
    starts = {str(item["predecessor_fen"]) for item in transitions.values()}
    results = {str(item["successor_fen"]) for item in transitions.values()}
    all_positions = starts | results
    transition_digests = {
        str(item["physical_transition_digest"]) for item in transitions.values()
    }
    stable_ids = set(map(str, validation["physical_fingerprints"]))
    overlaps = {
        "starting_positions": sorted(
            starts.intersection(excluded["excluded_all_position_fens"])
        ),
        "resulting_positions": sorted(
            results.intersection(excluded["excluded_all_position_fens"])
        ),
        "complete_transitions": sorted(
            transition_digests.intersection(
                excluded["excluded_transition_digests"]
            )
        ),
        "stable_interaction_ids": sorted(
            stable_ids.intersection(excluded["excluded_stable_interaction_ids"])
        ),
    }
    internally_unique = bool(
        len(starts) == 160
        and len(results) == 160
        and len(all_positions) == 320
        and len(transition_digests) == 160
        and len(stable_ids) == 160
    )
    if any(overlaps.values()) or not internally_unique:
        raise FreshScientificIntegrityError(
            "replacement ecology reuses a board position or interaction"
        )
    result = {
        "fresh": True,
        "internally_unique_complete_board_positions": True,
        "new_starting_position_count": len(starts),
        "new_resulting_position_count": len(results),
        "new_all_position_count": len(all_positions),
        "new_transition_count": len(transition_digests),
        "new_stable_interaction_id_count": len(stable_ids),
        "overlaps": overlaps,
        "superseded_overlap_comparison": copy.deepcopy(
            excluded["superseded_overlap_comparison"]
        ),
    }
    result["freshness_digest"] = digest(result)
    return result



def _tracked_runtime_paths() -> tuple[str, ...]:
    tracked = tuple(filter(None, _git("ls-files").splitlines()))
    return tuple(sorted(
        path for path in tracked
        if path.startswith("src/") or path.startswith("libs/recon-lite/src/")
    ))


def _module_identity(name: str) -> dict[str, Any]:
    module = importlib.import_module(name)
    path = Path(str(module.__file__)).resolve()
    return {"module": name, "path": str(path), "sha256": sha256_file(path)}


def build_source_runtime_manifest(source_freeze_commit: str) -> dict[str, Any]:
    source_hashes = {path: sha256_file(ROOT / path) for path in _tracked_runtime_paths()}
    experiment_paths = tuple(map(str, (
        Path(__file__).resolve().relative_to(ROOT),
        TEST_PATH,
        PREREGISTRATION_PATH,
        COMPLIANCE_PATH,
    )))
    experiment_hashes = {path: sha256_file(ROOT / path) for path in experiment_paths}
    value = {
        "schema_version": "native_v2_review_repair_v2_source_runtime.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_freeze_commit": source_freeze_commit,
        "runtime_source_hashes": source_hashes,
        "experiment_source_hashes": experiment_hashes,
        "protected_hashes": verify_protected_boundary(),
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "executable": str(Path(sys.executable).resolve()),
        },
        "packages": [
            {"name": name, "version": importlib.metadata.version(name)}
            for name in ("python-chess", "pytest")
        ],
        "imported_modules": [
            _module_identity(name) for name in (
                "recon_lite_chess.autogrowth.native_v2_fresh_discriminator_review_repair_v2",
                "recon_lite_chess.autogrowth.native_v2_atomic_snapshot_harness",
                "recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2",
                "recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2_lab",
                "chess",
            )
        ],
        "deterministic_environment": dict(DETERMINISTIC_ENV),
        "process_policy": {
            "canonical_workers": 1,
            "serial_seed_order": list(range(SEED_COUNT)),
            "row_order": "frozen_suffix_order",
            "arm_barrier_order": list(ARMS),
            "multiprocessing": False,
            "threads": False,
            "gpu": False,
            "xdist": False,
        },
    }
    value["source_runtime_digest"] = digest(value)
    return value


def predeclared_artifact_paths() -> dict[str, Any]:
    return {
        "prefix_organisms": [
            str(PREFIX_DIR / f"seed-{ordinal:02d}.pkl.gz")
            for ordinal in range(SEED_COUNT)
        ],
        "prefix_manifest": str(PREFIX_MANIFEST_PATH),
        "arm_snapshot_root": str(SNAPSHOT_ROOT),
        "preoutcome_exposure": str(EXPOSURE_PATH),
        "execution_manifest": str(EXECUTION_MANIFEST_PATH),
        "science_journal": str(SCIENCE_JOURNAL_DIR),
        "science_carrier": str(SCIENCE_CARRIER_DIR),
        "canonical_result": str(RESULT_PATH),
    }


def _assert_predata_outputs_absent() -> None:
    forbidden = (
        PREFIX_DIR,
        PREFIX_MANIFEST_PATH,
        SNAPSHOT_ROOT,
        EXPOSURE_PATH,
        EXECUTION_MANIFEST_PATH,
        SCIENCE_JOURNAL_DIR,
        SCIENCE_CARRIER_DIR,
        RESULT_PATH,
    )
    present = [str(path) for path in forbidden if (ROOT / path).exists()]
    if present:
        raise FreshScientificIntegrityError(
            "fresh learner execution already exists:" + ",".join(present)
        )


def freeze_predata_design(source_freeze_commit: str) -> dict[str, Any]:
    require_clean_worktree()
    if _git("rev-parse", "HEAD") != source_freeze_commit:
        raise FreshScientificIntegrityError("source-freeze commit identity mismatch")
    verify_protected_boundary()
    _assert_predata_outputs_absent()
    for path in (
        SEED_MANIFEST_PATH,
        EXCLUDED_POSITION_MANIFEST_PATH,
        ECOLOGY_MANIFEST_PATH,
        PERMUTATION_MANIFEST_PATH,
        ENVIRONMENT_MANIFEST_PATH,
        SOURCE_RUNTIME_MANIFEST_PATH,
        OUTER_MANIFEST_PATH,
    ):
        if (ROOT / path).exists():
            raise FileExistsError(f"frozen predata path already exists:{path}")
    toy_ecology = _load_json(ROOT / TOY_ECOLOGY_PATH)
    excluded = build_excluded_position_manifest(toy_ecology)
    pairs = enumerate_latent_pairs(
        80,
        excluded_position_fens=excluded["excluded_all_position_fens"],
        excluded_transition_digests=excluded["excluded_transition_digests"],
    )
    ecology = build_ecology_manifest(pairs)
    validation = validate_ecology_graph(ecology)
    freshness = verify_physical_freshness(ecology, validation, excluded)
    seeds = build_seed_manifest(source_freeze_commit)
    permutation = build_permutation_manifest(ecology)
    environment = build_environment_manifest(ecology)
    source = build_source_runtime_manifest(source_freeze_commit)
    manifests = {
        SEED_MANIFEST_PATH: seeds,
        EXCLUDED_POSITION_MANIFEST_PATH: excluded,
        ECOLOGY_MANIFEST_PATH: ecology,
        PERMUTATION_MANIFEST_PATH: permutation,
        ENVIRONMENT_MANIFEST_PATH: environment,
        SOURCE_RUNTIME_MANIFEST_PATH: source,
    }
    for path, value in manifests.items():
        atomic_json(ROOT / path, value)
    design_files = {
        str(path): sha256_file(ROOT / path) for path in manifests
    }
    outer = {
        "schema_version": "native_v2_review_repair_v2_outer_manifest.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_base_commit": SOURCE_BASE_COMMIT,
        "source_freeze_commit": source_freeze_commit,
        "opaque_terminal_salt": OPAQUE_TERMINAL_SALT,
        "design_files": design_files,
        "source_runtime_digest": source["source_runtime_digest"],
        "ecology_graph_validation": validation,
        "physical_freshness": freshness,
        "predeclared_artifact_paths": predeclared_artifact_paths(),
        "frozen_gates": {
            "seed_count": 32,
            "target_opportunities_per_arm": 4,
            "minimum_qualifying_seeds": 24,
            "minimum_favorable_seeds": 17,
            "primary_alpha": 0.05,
            "primary_tests": ["D_safe", "D_signal"],
            "holm_family_size": 2,
            "bootstrap_replicates": 20000,
        },
        "predata_stop": {
            "fresh_discovery_prefix_executed": False,
            "fresh_grounded_receipts_minted": 0,
            "required_absent_paths": [
                str(PREFIX_MANIFEST_PATH),
                str(SNAPSHOT_ROOT),
                str(EXPOSURE_PATH),
                str(EXECUTION_MANIFEST_PATH),
                str(SCIENCE_JOURNAL_DIR),
                str(SCIENCE_CARRIER_DIR),
                str(RESULT_PATH),
            ],
        },
        "data_prohibition": [
            "KRK historical regression",
            "fresh KRK",
            "retired-65",
            "R1",
            "validation/regression pools",
            "held-out pools",
            "retired V2 suffix",
        ],
    }
    outer["outer_manifest_digest"] = digest(outer)
    atomic_json(ROOT / OUTER_MANIFEST_PATH, outer)
    _assert_predata_outputs_absent()
    return outer



def _registry_manifest(registry: V2LaboratoryRegistry) -> dict[str, Any]:
    return {
        "schema_version": registry.schema_version,
        "registry_id": registry.registry_id,
        "tape_identity": registry.tape_identity,
        "row_order": list(registry.row_order),
        "run_identity": registry.run_identity,
        "package_hashes": [list(item) for item in registry.package_hashes],
        "organisms": [item.manifest() for item in registry.organisms],
        "exposure_rows": {
            organism_id: [row.manifest() for row in rows]
            for organism_id, rows in registry.exposure_rows
        },
    }


def verify_outer_manifest(phase: str) -> dict[str, Any]:
    verify_protected_boundary()
    outer_path = ROOT / OUTER_MANIFEST_PATH
    outer = _load_json(outer_path)
    unsigned = {
        key: value for key, value in outer.items()
        if key != "outer_manifest_digest"
    }
    if outer.get("outer_manifest_digest") != digest(unsigned):
        raise FreshScientificIntegrityError(f"outer manifest digest drift:{phase}")
    if outer.get("experiment_id") != EXPERIMENT_ID:
        raise FreshScientificIntegrityError(f"foreign outer experiment:{phase}")
    for relative, expected in outer["design_files"].items():
        if sha256_file(ROOT / relative) != expected:
            raise FreshScientificIntegrityError(
                f"frozen design file drift:{phase}:{relative}"
            )
    source = _load_json(ROOT / SOURCE_RUNTIME_MANIFEST_PATH)
    for relative, expected in {
        **source["runtime_source_hashes"],
        **source["experiment_source_hashes"],
    }.items():
        if sha256_file(ROOT / relative) != expected:
            raise FreshScientificIntegrityError(
                f"source changed after source freeze:{phase}:{relative}"
            )
    return {
        "outer": outer,
        "outer_sha256": sha256_file(outer_path),
        "source_freeze_commit": source["source_freeze_commit"],
        "source_runtime_digest": source["source_runtime_digest"],
    }


def laboratory_package_hashes() -> dict[str, str]:
    identity = verify_outer_manifest("laboratory package binding")
    source = _load_json(ROOT / SOURCE_RUNTIME_MANIFEST_PATH)
    hashes = {
        **{f"runtime:{key}": value for key, value in source["runtime_source_hashes"].items()},
        **{f"experiment:{key}": value for key, value in source["experiment_source_hashes"].items()},
        **{
            f"design:{key}": value
            for key, value in identity["outer"]["design_files"].items()
        },
        "outer_manifest": identity["outer_sha256"],
    }
    return dict(sorted(hashes.items()))


def _prefix_snapshot_path(ordinal: int) -> Path:
    return ROOT / PREFIX_DIR / f"seed-{int(ordinal):02d}.pkl.gz"


def load_prefix_wrapper(entry: Mapping[str, Any]) -> NativeProspectiveAuthorityV2:
    path = ROOT / str(entry["path"])
    compressed = path.read_bytes()
    if (
        len(compressed) != int(entry["compressed_size"])
        or sha256_bytes(compressed) != entry["compressed_sha256"]
    ):
        raise FreshScientificIntegrityError("prefix wrapper transport mismatch")
    raw = gzip.decompress(compressed)
    if (
        len(raw) != int(entry["uncompressed_size"])
        or sha256_bytes(raw) != entry["uncompressed_sha256"]
    ):
        raise FreshScientificIntegrityError("prefix wrapper raw mismatch")
    wrapper = NativeProspectiveAuthorityV2.loads(raw)
    if wrapper.continuation_digest() != entry["continuation_digest"]:
        raise FreshScientificIntegrityError("prefix continuation mismatch")
    if digest(structural_identity(wrapper)) != entry["structural_identity_digest"]:
        raise FreshScientificIntegrityError("prefix structural identity mismatch")
    return wrapper


def run_canonical_discovery() -> dict[str, Any]:
    """Future-only fresh prefix command; never called by the freeze package."""

    identity = verify_outer_manifest("fresh discovery prefix")
    if (ROOT / PREFIX_MANIFEST_PATH).exists() or (ROOT / PREFIX_DIR).exists():
        raise FileExistsError("fresh prefix output already exists")
    seed_manifest = _load_json(ROOT / SEED_MANIFEST_PATH)
    ecology = _load_json(ROOT / ECOLOGY_MANIFEST_PATH)
    results = []
    for seed_row in seed_manifest["rows"]:
        result, wrapper = run_discovery_seed(seed_row, ecology)
        raw = wrapper.dumps()
        compressed = deterministic_gzip(raw)
        path = _prefix_snapshot_path(int(seed_row["ordinal"]))
        _atomic_bytes(path, compressed)
        result.update({
            "path": path.resolve().relative_to(ROOT.resolve()).as_posix(),
            "uncompressed_size": len(raw),
            "compressed_sha256": sha256_bytes(compressed),
            "compressed_size": len(compressed),
        })
        results.append(result)
    value = {
        "schema_version": "native_v2_review_repair_v2_prefix_candidates.v1",
        "experiment_id": EXPERIMENT_ID,
        "outer_manifest_sha256": identity["outer_sha256"],
        "ecology_digest": ecology["ecology_digest"],
        "seed_manifest_digest": seed_manifest["seed_manifest_digest"],
        "serial_execution": True,
        "all_32_retained": True,
        "results": results,
    }
    value["prefix_manifest_digest"] = digest(value)
    atomic_json(ROOT / PREFIX_MANIFEST_PATH, value)
    return value


def _load_prefix_manifest() -> dict[str, Any]:
    value = _load_json(ROOT / PREFIX_MANIFEST_PATH)
    unsigned = {
        key: item for key, item in value.items()
        if key != "prefix_manifest_digest"
    }
    if value.get("prefix_manifest_digest") != digest(unsigned):
        raise FreshScientificIntegrityError("prefix manifest digest mismatch")
    if [int(item["ordinal"]) for item in value["results"]] != list(range(SEED_COUNT)):
        raise FreshScientificIntegrityError("prefix manifest does not retain all 32")
    return value


def persist_canonical_arm_snapshots() -> dict[str, Any]:
    """Future-only exact-once A/B/C construction command."""

    identity = verify_outer_manifest("arm snapshot persistence")
    prefix = _load_prefix_manifest()
    if (ROOT / SNAPSHOT_ROOT).exists():
        raise FileExistsError("canonical arm snapshot package already exists")
    contracts: dict[str, Any] = {}

    def factory(ordinal: int) -> Mapping[str, NativeProspectiveAuthorityV2]:
        entry = prefix["results"][int(ordinal)]
        arms = candidate_identical_arms(load_prefix_wrapper(entry))
        contracts[str(int(ordinal))] = exact_arm_identity_contract(arms)
        return arms

    manifest = persist_arm_snapshots_once(
        seed_ordinals=tuple(range(SEED_COUNT)),
        arm_factory=factory,
        package_root=ROOT / SNAPSHOT_ROOT,
        codec=V2SnapshotCodec(),
        experiment_id=EXPERIMENT_ID,
        source_manifest_digest=identity["source_runtime_digest"],
        metadata={
            "prefix_manifest_sha256": sha256_file(ROOT / PREFIX_MANIFEST_PATH),
            "prefix_manifest_digest": prefix["prefix_manifest_digest"],
            "per_seed_identity_contracts": contracts,
            "constructed_together_once": True,
            "suffix_nomination_disabled": True,
        },
    )
    if len(contracts) != SEED_COUNT:
        raise FreshScientificIntegrityError("identity contract coverage mismatch")
    return manifest


def _validated_snapshot_manifest() -> dict[str, Any]:
    path = ROOT / SNAPSHOT_ROOT / "arm_snapshot_manifest.json"
    value = _load_json(path)
    unsigned = {key: item for key, item in value.items() if key != "manifest_digest"}
    if value.get("manifest_digest") != canonical_digest(unsigned):
        raise FreshScientificIntegrityError("snapshot manifest digest mismatch")
    if value.get("experiment_id") != EXPERIMENT_ID:
        raise FreshScientificIntegrityError("foreign snapshot experiment")
    keys = {
        (int(item["seed_ordinal"]), str(item["arm"]))
        for item in value["entries"]
    }
    expected = {(seed, arm) for seed in range(SEED_COUNT) for arm in ARMS}
    if keys != expected or len(value["entries"]) != 96:
        raise FreshScientificIntegrityError("snapshot manifest lacks exact 96")
    return value


def _restore_snapshot_entry(
    manifest: Mapping[str, Any], ordinal: int, arm: str
) -> NativeProspectiveAuthorityV2:
    matches = [
        item for item in manifest["entries"]
        if int(item["seed_ordinal"]) == int(ordinal) and item["arm"] == arm
    ]
    if len(matches) != 1:
        raise FreshScientificIntegrityError("snapshot entry missing or duplicate")
    entry = matches[0]
    path = ROOT / SNAPSHOT_ROOT / str(entry["path"])
    compressed = path.read_bytes()
    if (
        len(compressed) != int(entry["compressed_size"])
        or sha256_bytes(compressed) != entry["compressed_sha256"]
    ):
        raise FreshScientificIntegrityError("snapshot compressed transport mismatch")
    raw = gzip.decompress(compressed)
    if len(raw) != int(entry["raw_size"]) or sha256_bytes(raw) != entry["raw_sha256"]:
        raise FreshScientificIntegrityError("snapshot raw transport mismatch")
    wrapper = V2SnapshotCodec().loads(raw)
    if V2SnapshotCodec().semantic_identity(wrapper) != entry["semantic_identity"]:
        raise FreshScientificIntegrityError("snapshot semantic identity mismatch")
    return wrapper


def _target_counts_from_scan(
    scan: Mapping[str, Any], targets: Mapping[str, Any]
) -> dict[str, Any]:
    values = {}
    for name in ("planted", "selected_spurious"):
        cell_id = target_cell_id(targets, name)
        values[name] = (
            {"distinct_opportunities": 0, "opportunity_ids": [], "state": "ABSENT"}
            if cell_id is None else copy.deepcopy(scan["cells"][cell_id])
        )
    return values


def _suffix_registered_rows(
    ecology: Mapping[str, Any], arm: str, ordinal: int
) -> tuple[RegisteredV2ExposureRow, ...]:
    transitions = environment_transitions(ecology)
    return tuple(
        RegisteredV2ExposureRow(
            row_id=str(row["row_id"]),
            frame_id=(
                f"v2-review-repair-v2:exposure:{arm}:seed-{int(ordinal):02d}:"
                f"{row['row_id']}"
            ),
            predecessor_fen=str(
                transitions[str(row[f"{arm}_transition_id"])]["predecessor_fen"]
            ),
        )
        for row in ecology_rows(ecology, "suffix")
    )


def _candidate_manifest_digest(prefix: Mapping[str, Any]) -> str:
    return digest([{
        "ordinal": int(item["ordinal"]),
        "genome_seed": int(item["genome_seed"]),
        "targets": copy.deepcopy(item["targets"]),
        "structural_identity_digest": item["structural_identity_digest"],
        "continuation_digest": item["continuation_digest"],
        "experimental_identity_digest": item["experimental_identity_digest"],
    } for item in prefix["results"]])


def _complete_snapshot_identity(
    manifest: Mapping[str, Any],
    restored: Mapping[tuple[int, str], NativeProspectiveAuthorityV2],
) -> dict[str, Any]:
    rows = []
    for ordinal in range(SEED_COUNT):
        for arm in ARMS:
            wrapper = restored[(ordinal, arm)]
            identity = V2SnapshotCodec().semantic_identity(wrapper)
            rows.append({
                "ordinal": ordinal,
                "arm": arm,
                "semantic_identity_digest": digest(identity),
                "continuation_digest": identity["continuation_digest"],
                "candidate_population_identity": identity[
                    "candidate_population_identity"
                ],
            })
    value = {
        "artifact_count": len(rows),
        "snapshot_manifest_digest": manifest["manifest_digest"],
        "manifest_entry_set_digest": digest(manifest["entries"]),
        "restored_rows": rows,
        "restored_row_set_digest": digest(rows),
    }
    value["complete_snapshot_identity_digest"] = digest(value)
    return value


def _verify_prefix_snapshot_metadata(
    prefix: Mapping[str, Any],
    manifest: Mapping[str, Any],
    restored: Mapping[tuple[int, str], NativeProspectiveAuthorityV2],
) -> dict[str, Any]:
    metadata = manifest.get("metadata", {})
    if (
        metadata.get("prefix_manifest_sha256")
        != sha256_file(ROOT / PREFIX_MANIFEST_PATH)
        or metadata.get("prefix_manifest_digest")
        != prefix["prefix_manifest_digest"]
    ):
        raise FreshScientificIntegrityError("snapshot/prefix manifest mismatch")
    contracts = metadata.get("per_seed_identity_contracts")
    if not isinstance(contracts, dict) or set(contracts) != {
        str(ordinal) for ordinal in range(SEED_COUNT)
    }:
        raise FreshScientificIntegrityError("snapshot candidate metadata incomplete")
    rows = []
    for ordinal in range(SEED_COUNT):
        prefix_item = prefix["results"][ordinal]
        if int(prefix_item["ordinal"]) != ordinal:
            raise FreshScientificIntegrityError("prefix row order changed")
        arms = {arm: restored[(ordinal, arm)] for arm in ARMS}
        observed_contract = exact_arm_identity_contract(arms)
        if observed_contract != contracts[str(ordinal)]:
            raise FreshScientificIntegrityError(
                f"snapshot candidate contract mismatch:{ordinal}"
            )
        targets = prefix_item["targets"]
        for arm in ARMS:
            wrapper = arms[arm]
            if (
                wrapper.experimental_identity["candidate_population_identity"]
                != targets["candidate_population_digest"]
                or digest(structural_identity(wrapper))
                != prefix_item["structural_identity_digest"]
            ):
                raise FreshScientificIntegrityError(
                    f"snapshot candidate population mismatch:{ordinal}:{arm}"
                )
            for name in ("planted", "selected_spurious"):
                target = targets[name]
                if target is None:
                    continue
                state = wrapper.states.get(str(target["cell_id"]))
                if (
                    state is None
                    or digest(state.hypothesis.manifest())
                    != target["hypothesis_digest"]
                    or list(state.hypothesis.members) != target["members"]
                ):
                    raise FreshScientificIntegrityError(
                        f"snapshot target metadata mismatch:{ordinal}:{arm}:{name}"
                    )
        rows.append({
            "ordinal": ordinal,
            "candidate_manifest_digest": digest(targets),
            "identity_contract_digest": observed_contract["contract_digest"],
        })
    value = {
        "row_count": len(rows),
        "rows": rows,
        "candidate_manifest_digest": _candidate_manifest_digest(prefix),
    }
    value["verification_digest"] = digest(value)
    return value


def _reconstruct_exposure_value(
    *,
    identity: Mapping[str, Any],
    prefix: Mapping[str, Any],
    ecology: Mapping[str, Any],
    manifest: Mapping[str, Any],
    receipt: Mapping[str, Any],
    restored: Mapping[tuple[int, str], NativeProspectiveAuthorityV2],
    guard: OutcomeAccessGuard,
) -> dict[str, Any]:
    prefix_verification = _verify_prefix_snapshot_metadata(
        prefix, manifest, restored
    )
    package_hashes = laboratory_package_hashes()
    registry_package_hash = digest(package_hashes)
    row_order = tuple(row["row_id"] for row in ecology_rows(ecology, "suffix"))
    projections: dict[int, dict[str, list[dict[str, Any]]]] = {
        ordinal: {} for ordinal in range(SEED_COUNT)
    }
    arms_result = {}
    target_counts: dict[int, dict[str, dict[str, Any]]] = {
        ordinal: {} for ordinal in range(SEED_COUNT)
    }
    for arm in ARMS:
        payloads = {}
        exposure_rows = {}
        for ordinal in range(SEED_COUNT):
            organism_id = f"seed-{ordinal:02d}"
            payloads[organism_id] = restored[(ordinal, arm)].dumps()
            exposure_rows[organism_id] = _suffix_registered_rows(
                ecology, arm, ordinal
            )
        run_identity = digest({
            "experiment_id": EXPERIMENT_ID,
            "phase": "preoutcome_exposure",
            "arm": arm,
            "outer_manifest_sha256": identity["outer_sha256"],
        })
        registry = V2LaboratoryRegistry.freeze(
            payloads,
            exposure_rows=exposure_rows,
            row_order=row_order,
            run_identity=run_identity,
            package_hashes=package_hashes,
        )
        scan_wrappers = []
        per_seed = []
        for ordinal in range(SEED_COUNT):
            organism_id = f"seed-{ordinal:02d}"
            wrapper = restored[(ordinal, arm)]
            targets = prefix["results"][ordinal]["targets"]
            before = wrapper.continuation_digest()
            commitments = []
            visible = []
            for row, registered in zip(
                ecology_rows(ecology, "suffix"),
                exposure_rows[organism_id],
                strict=True,
            ):
                commitment = wrapper.probe_real_exposure(FrameContext(
                    registered.frame_id,
                    FrameKind.REAL,
                    values={"board": chess.Board(registered.predecessor_fen)},
                ))
                commitments.append(commitment)
                visible.append(classification_visible_projection(
                    wrapper,
                    commitment,
                    commitment.trace,
                    planted_cell_id=target_cell_id(targets, "planted"),
                    spurious_cell_id=target_cell_id(targets, "selected_spurious"),
                    row_id=str(row["row_id"]),
                ))
            if wrapper.continuation_digest() != before:
                raise FreshScientificIntegrityError("exposure changed restored snapshot")
            scan_wrapper = registry.scan(
                organism_id,
                payloads[organism_id],
                commitments,
                tape_identity=registry.tape_identity,
                row_order=row_order,
                run_identity=run_identity,
                package_hashes=package_hashes,
            )
            scan_wrappers.append(scan_wrapper)
            counts = _target_counts_from_scan(scan_wrapper["scan"], targets)
            target_counts[ordinal][arm] = counts
            projections[ordinal][arm] = visible
            per_seed.append({
                "ordinal": ordinal,
                "organism_id": organism_id,
                "continuation_digest": before,
                "target_counts": counts,
                "scan_wrapper_digest": digest(scan_wrapper),
                "projection_digests": [
                    item["projection_digest"] for item in visible
                ],
            })
        adjudication = registry.adjudicate_cohort(
            scan_wrappers,
            tape_identity=registry.tape_identity,
            row_order=row_order,
            run_identity=run_identity,
            package_hashes=package_hashes,
        )
        arms_result[arm] = {
            "registry": _registry_manifest(registry),
            "registry_adjudication": adjudication,
            "per_seed": per_seed,
            "scan_wrapper_set_digest": digest(scan_wrappers),
        }
    parity_rows = []
    for ordinal in range(SEED_COUNT):
        for row_index, row_id in enumerate(row_order):
            values = {
                arm: projections[ordinal][arm][row_index] for arm in ARMS
            }
            comparable = {
                arm: {
                    key: item for key, item in value.items()
                    if key != "projection_digest"
                }
                for arm, value in values.items()
            }
            if not (comparable["A"] == comparable["B"] == comparable["C"]):
                raise FreshScientificIntegrityError(
                    f"control_exposure_parity_failure:{ordinal}:{row_id}"
                )
            parity_rows.append({
                "ordinal": ordinal,
                "row_id": row_id,
                "equal": True,
                "projection_digests": {
                    arm: values[arm]["projection_digest"] for arm in ARMS
                },
            })
    per_seed_qualification = []
    for ordinal in range(SEED_COUNT):
        qualified = all(
            target_counts[ordinal][arm][name]["distinct_opportunities"]
            >= MIN_TARGET_OPPORTUNITIES
            for arm in ARMS
            for name in ("planted", "selected_spurious")
        )
        per_seed_qualification.append({
            "ordinal": ordinal,
            "qualified": qualified,
        })
    qualifying = sum(item["qualified"] for item in per_seed_qualification)
    authorization = {
        "schema_version": "native_v2_review_repair_v2_preflight_authorization.v1",
        "experiment_id": EXPERIMENT_ID,
        "registry_package_hash": registry_package_hash,
        "expected_global_preflight": {
            "receipt_digest": receipt["receipt_digest"],
            "snapshot_manifest_digest": manifest["manifest_digest"],
            "registry_package_hash": registry_package_hash,
        },
        "complete_96_required": True,
        "outcome_access_at_freeze": guard.manifest(),
    }
    authorization["authorization_digest"] = digest(authorization)
    verify_bound_preflight_authorization(
        receipt=receipt,
        snapshot_manifest=manifest,
        authorization=authorization,
    )
    value = {
        "schema_version": "native_v2_review_repair_v2_preoutcome_exposure.v1",
        "experiment_id": EXPERIMENT_ID,
        "outer_manifest_sha256": identity["outer_sha256"],
        "snapshot_manifest_digest": manifest["manifest_digest"],
        "complete_snapshot_identity": _complete_snapshot_identity(
            manifest, restored
        ),
        "prefix_candidate_verification": prefix_verification,
        "global_preflight_receipt": copy.deepcopy(dict(receipt)),
        "preflight_authorization": authorization,
        "registry_package_hash": registry_package_hash,
        "arms": arms_result,
        "parity_rows": parity_rows,
        "parity_row_count": len(parity_rows),
        "parity_digest": digest(parity_rows),
        "per_seed_qualification": per_seed_qualification,
        "qualification_digest": digest(per_seed_qualification),
        "qualifying_seed_count": qualifying,
        "required_qualifying_seed_count": MIN_QUALIFYING_SEEDS,
        "admitted": qualifying >= MIN_QUALIFYING_SEEDS,
        "stop_reason": (
            None if qualifying >= MIN_QUALIFYING_SEEDS
            else "prospective_evidence_starvation"
        ),
        "outcome_access": guard.manifest(),
    }
    value["exposure_digest"] = digest(value)
    return value


def _build_execution_manifest(
    *,
    identity: Mapping[str, Any],
    prefix: Mapping[str, Any],
    ecology: Mapping[str, Any],
    manifest: Mapping[str, Any],
    exposure: Mapping[str, Any],
) -> dict[str, Any]:
    if exposure["outcome_access"] != {"count": 0, "event_ids": []}:
        raise FreshScientificIntegrityError("exposure opened an outcome")
    value = {
        "schema_version": "native_v2_review_repair_v2_execution_manifest.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_tree_identity": {
            "source_freeze_commit": identity["source_freeze_commit"],
            "source_runtime_digest": identity["source_runtime_digest"],
        },
        "experiment_package_identity": {
            "outer_manifest_sha256": identity["outer_sha256"],
            "laboratory_package_digest": digest(laboratory_package_hashes()),
        },
        "seed_manifest": {
            "sha256": sha256_file(ROOT / SEED_MANIFEST_PATH),
            "digest": _load_json(ROOT / SEED_MANIFEST_PATH)["seed_manifest_digest"],
        },
        "ecology_manifest": {
            "sha256": sha256_file(ROOT / ECOLOGY_MANIFEST_PATH),
            "digest": ecology["ecology_digest"],
        },
        "prefix_manifest": {
            "sha256": sha256_file(ROOT / PREFIX_MANIFEST_PATH),
            "digest": prefix["prefix_manifest_digest"],
            "candidate_manifest_digest": _candidate_manifest_digest(prefix),
        },
        "snapshot_manifest": {
            "sha256": sha256_file(
                ROOT / SNAPSHOT_ROOT / "arm_snapshot_manifest.json"
            ),
            "digest": manifest["manifest_digest"],
            "entry_set_digest": digest(manifest["entries"]),
            "artifact_count": len(manifest["entries"]),
        },
        "exposure_artifact": {
            "sha256": sha256_file(ROOT / EXPOSURE_PATH),
            "digest": exposure["exposure_digest"],
        },
        "parity_digest": exposure["parity_digest"],
        "qualification_digest": exposure["qualification_digest"],
        "qualifying_seed_count": exposure["qualifying_seed_count"],
        "required_qualifying_seed_count": exposure[
            "required_qualifying_seed_count"
        ],
        "admitted": exposure["admitted"],
        "zero_outcome_read_result": copy.deepcopy(exposure["outcome_access"]),
        "complete_snapshot_identity": copy.deepcopy(
            exposure["complete_snapshot_identity"]
        ),
        "global_preflight_receipt_digest": exposure[
            "global_preflight_receipt"
        ]["receipt_digest"],
    }
    value["execution_manifest_digest"] = digest(value)
    return value


def run_preoutcome_exposure() -> dict[str, Any]:
    """Read-only exposure reconstruction followed by an execution freeze."""

    identity = verify_outer_manifest("preoutcome exposure")
    if (ROOT / EXPOSURE_PATH).exists() or (ROOT / EXECUTION_MANIFEST_PATH).exists():
        raise FileExistsError("preoutcome exposure or execution manifest exists")
    prefix = _load_prefix_manifest()
    ecology = _load_json(ROOT / ECOLOGY_MANIFEST_PATH)
    manifest = _validated_snapshot_manifest()
    guard = OutcomeAccessGuard()
    receipt, restored = global_all_arm_preflight(
        manifest_path=ROOT / SNAPSHOT_ROOT / "arm_snapshot_manifest.json",
        package_root=ROOT / SNAPSHOT_ROOT,
        receipt_path=ROOT / SNAPSHOT_ROOT / "global_preflight_receipt.json",
        failure_path=ROOT / SNAPSHOT_ROOT / "global_preflight_failure.json",
        codec=V2SnapshotCodec(),
        guard=guard,
        required_seed_ordinals=tuple(range(SEED_COUNT)),
    )
    value = _reconstruct_exposure_value(
        identity=identity,
        prefix=prefix,
        ecology=ecology,
        manifest=manifest,
        receipt=receipt,
        restored=restored,
        guard=guard,
    )
    atomic_json(ROOT / EXPOSURE_PATH, value)
    execution = _build_execution_manifest(
        identity=identity,
        prefix=prefix,
        ecology=ecology,
        manifest=manifest,
        exposure=value,
    )
    atomic_json(ROOT / EXECUTION_MANIFEST_PATH, execution)
    return value


def reconstruct_admission_before_outcomes() -> dict[str, Any]:
    """Rebuild the full frozen cohort immediately before any outcome access."""

    identity = verify_outer_manifest("immediate pre-outcome reconstruction")
    exposure = _load_json(ROOT / EXPOSURE_PATH)
    if exposure.get("exposure_digest") != digest({
        key: value for key, value in exposure.items() if key != "exposure_digest"
    }):
        raise FreshScientificIntegrityError("exposure artifact digest mismatch")
    execution = _load_json(ROOT / EXECUTION_MANIFEST_PATH)
    if execution.get("execution_manifest_digest") != digest({
        key: value for key, value in execution.items()
        if key != "execution_manifest_digest"
    }):
        raise FreshScientificIntegrityError("execution manifest digest mismatch")
    prefix = _load_prefix_manifest()
    ecology = _load_json(ROOT / ECOLOGY_MANIFEST_PATH)
    manifest = _validated_snapshot_manifest()
    with tempfile.TemporaryDirectory(
        prefix="native-v2-review-repair-v2-preflight-"
    ) as temporary:
        temporary_path = Path(temporary)
        guard = OutcomeAccessGuard()
        receipt, restored = global_all_arm_preflight(
            manifest_path=ROOT / SNAPSHOT_ROOT / "arm_snapshot_manifest.json",
            package_root=ROOT / SNAPSHOT_ROOT,
            receipt_path=temporary_path / "global_preflight_receipt.json",
            failure_path=temporary_path / "global_preflight_failure.json",
            codec=V2SnapshotCodec(),
            guard=guard,
            required_seed_ordinals=tuple(range(SEED_COUNT)),
        )
        reconstructed = _reconstruct_exposure_value(
            identity=identity,
            prefix=prefix,
            ecology=ecology,
            manifest=manifest,
            receipt=receipt,
            restored=restored,
            guard=guard,
        )
    if reconstructed != exposure:
        raise FreshScientificIntegrityError(
            "current cohort differs from frozen exposure reconstruction"
        )
    rebuilt_execution = _build_execution_manifest(
        identity=identity,
        prefix=prefix,
        ecology=ecology,
        manifest=manifest,
        exposure=exposure,
    )
    if rebuilt_execution != execution:
        raise FreshScientificIntegrityError(
            "current cohort differs from frozen execution manifest"
        )
    if not reconstructed["admitted"]:
        raise FreshScientificIntegrityError("reconstructed cohort was not admitted")
    if reconstructed["outcome_access"] != {"count": 0, "event_ids": []}:
        raise FreshScientificIntegrityError("pre-outcome reconstruction read an outcome")
    return {
        "identity": identity,
        "prefix": prefix,
        "ecology": ecology,
        "manifest": manifest,
        "receipt": reconstructed["global_preflight_receipt"],
        "authorization": reconstructed["preflight_authorization"],
        "exposure": reconstructed,
        "execution_manifest": execution,
        "restored": restored,
    }



def _suffix_outcome_blind_rows(ecology: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    transitions = environment_transitions(ecology)
    return tuple(
        outcome_blind_row(row, transitions)
        for row in ecology_rows(ecology, "suffix")
    )


def restart_execution_plan(
    journal: DurableHashJournal,
) -> dict[str, Any]:
    next_seed = journal.next_seed(tuple(range(SEED_COUNT)))
    completed_count = SEED_COUNT if next_seed is None else int(next_seed)
    value = {
        "completed_ordinals": list(range(completed_count)),
        "next_unfinished_seed": next_seed,
        "remaining_ordinals": (
            [] if next_seed is None else list(range(next_seed, SEED_COUNT))
        ),
    }
    value["restart_plan_digest"] = digest(value)
    return value


def run_canonical_science() -> dict[str, Any]:
    """Execute only unfinished seeds after complete immediate reconstruction."""

    if (ROOT / RESULT_PATH).exists():
        raise FileExistsError("canonical scientific result already exists")
    baseline = reconstruct_admission_before_outcomes()
    identity = baseline["identity"]
    prefix = baseline["prefix"]
    ecology = baseline["ecology"]
    manifest = baseline["manifest"]
    receipt = baseline["receipt"]
    authorization = baseline["authorization"]
    restored = baseline["restored"]
    exposure = baseline["exposure"]
    environment_value = _load_json(ROOT / ENVIRONMENT_MANIFEST_PATH)
    environment = FrozenTruthfulEnvironment(environment_value)
    rows = _suffix_outcome_blind_rows(ecology)
    seed_metadata = {
        int(item["ordinal"]): {
            "genome_seed": int(item["genome_seed"]),
            "targets": copy.deepcopy(item["targets"]),
        }
        for item in prefix["results"]
    }
    journal = DurableHashJournal(ROOT / SCIENCE_JOURNAL_DIR)
    plan = restart_execution_plan(journal)
    completed_results = committed_seed_results(
        journal,
        expected_ordinals=tuple(plan["completed_ordinals"]),
        expected_rows=rows,
        baseline_wrappers=restored,
        expected_seed_metadata=seed_metadata,
        environment_manifest=environment_value,
    )
    if len(completed_results) != len(plan["completed_ordinals"]):
        raise FreshScientificIntegrityError("completed seed verification mismatch")

    for ordinal in plan["remaining_ordinals"]:
        live = {arm: restored[(ordinal, arm)] for arm in ARMS}
        adapter = FreshScienceAdapter(
            seed_ordinal=ordinal,
            genome_seed=seed_metadata[ordinal]["genome_seed"],
            targets=seed_metadata[ordinal]["targets"],
            identity_contract=manifest["metadata"][
                "per_seed_identity_contracts"
            ][str(ordinal)],
        )
        execute_fresh_seed_atomically(
            seed_ordinal=ordinal,
            live_arms=live,
            rows=rows,
            adapter=adapter,
            journal_root=ROOT / SCIENCE_JOURNAL_DIR,
            carrier_root=ROOT / SCIENCE_CARRIER_DIR,
            environment=environment,
            preflight_receipt=receipt,
            snapshot_manifest=manifest,
            authorization=authorization,
        )

    final_journal = DurableHashJournal(ROOT / SCIENCE_JOURNAL_DIR)
    final_plan = restart_execution_plan(final_journal)
    if final_plan["next_unfinished_seed"] is not None:
        raise FreshScientificIntegrityError("canonical execution ended before seed 31")
    seed_results = committed_seed_results(
        final_journal,
        expected_ordinals=tuple(range(SEED_COUNT)),
        expected_rows=rows,
        baseline_wrappers=restored,
        expected_seed_metadata=seed_metadata,
        environment_manifest=environment_value,
    )
    adjudication = adjudicate_committed_results(seed_results)
    value = {
        "schema_version": "native_v2_review_repair_v2_canonical_result.v1",
        "experiment_id": EXPERIMENT_ID,
        "outer_manifest_sha256": identity["outer_sha256"],
        "exposure_digest": exposure["exposure_digest"],
        "execution_manifest_digest": baseline["execution_manifest"][
            "execution_manifest_digest"
        ],
        "all_32_committed": True,
        "restart_plan_at_entry": plan,
        "seed_result_digests": [
            item["seed_result_digest"] for item in seed_results
        ],
        "recomputed_result_digests": [
            item["recomputed_result_digest"] for item in seed_results
        ],
        "adjudication": adjudication,
        "journal_chain_digest": digest(final_journal._records()),
    }
    value["canonical_result_digest"] = digest(value)
    _atomic_bytes(ROOT / RESULT_PATH, deterministic_gzip(canonical_bytes(value)))
    return value



def _expected_authorization(
    receipt: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    experiment_id: str,
    registry_package_hash: str,
) -> dict[str, Any]:
    value = {
        "schema_version": "native_v2_review_repair_v2_preflight_authorization.v1",
        "experiment_id": experiment_id,
        "registry_package_hash": registry_package_hash,
        "expected_global_preflight": {
            "receipt_digest": receipt["receipt_digest"],
            "snapshot_manifest_digest": manifest["manifest_digest"],
            "registry_package_hash": registry_package_hash,
        },
    }
    value["authorization_digest"] = digest(value)
    return value


def _expect_failure(callable_value: Any, label: str) -> dict[str, Any]:
    try:
        callable_value()
    except Exception as exc:
        value = {
            "label": label,
            "rejected": True,
            "exception_type": type(exc).__name__,
            "detail": str(exc),
        }
        value["evidence_digest"] = digest(value)
        return value
    raise FreshScientificIntegrityError(f"adversarial canary unexpectedly passed:{label}")


def _canary_corruption(
    source_root: Path,
    manifest: Mapping[str, Any],
    *,
    entry_index: int,
    label: str,
    work_root: Path,
) -> dict[str, Any]:
    root = work_root / label
    shutil.copytree(source_root, root)
    entry = manifest["entries"][entry_index]
    path = root / str(entry["path"])
    payload = bytearray(path.read_bytes())
    payload[0] ^= 1
    path.write_bytes(payload)
    evidence = _expect_failure(
        lambda: global_all_arm_preflight(
            manifest_path=root / "arm_snapshot_manifest.json",
            package_root=root,
            receipt_path=root / "receipt.json",
            failure_path=root / "failure.json",
            codec=V2SnapshotCodec(),
            guard=OutcomeAccessGuard(),
            required_seed_ordinals=tuple(range(SEED_COUNT)),
        ),
        label,
    )
    failure = _load_json(root / "failure.json")
    if failure["classification"] != "transport corruption":
        raise FreshScientificIntegrityError("snapshot corruption did not fail as transport")
    return {
        **evidence,
        "entry": {
            "seed_ordinal": entry["seed_ordinal"],
            "arm": entry["arm"],
            "path": entry["path"],
        },
        "failure": failure,
        "failure_file_sha256": sha256_file(root / "failure.json"),
    }


def _canary_identity_swap_checks(
    wrapper: NativeProspectiveAuthorityV2,
) -> list[dict[str, Any]]:
    checks = []

    def rejected(label: str, mutate: Any) -> None:
        arms = candidate_identical_arms(copy.deepcopy(wrapper))
        mutate(arms)
        checks.append(_expect_failure(lambda: exact_arm_identity_contract(arms), label))

    rejected("mode_swap", lambda arms: setattr(arms["B"], "mode", V2Mode.PROSPECTIVE))

    def source_swap(arms: MutableMapping[str, NativeProspectiveAuthorityV2]) -> None:
        object.__setattr__(
            arms["C"].base.r0.provenance,
            "child_id",
            "adversarial-foreign-source-child",
        )

    rejected("source_swap", source_swap)

    def candidate_swap(arms: MutableMapping[str, NativeProspectiveAuthorityV2]) -> None:
        cell_id = sorted(arms["C"].states)[0]
        del arms["C"].states[cell_id]

    rejected("candidate_swap", candidate_swap)

    def topology_swap(arms: MutableMapping[str, NativeProspectiveAuthorityV2]) -> None:
        arms["C"].authority_topology["adversarial_topology_swap"] = {
            "node_id": "foreign"
        }

    rejected("topology_swap", topology_swap)
    return checks


def run_retired_actual_v2_canary() -> dict[str, Any]:
    """Run the permanently retired actual-V2 pre-data adversarial canary."""

    verify_protected_boundary()
    if (ROOT / TOY_CANARY_PATH).exists():
        raise FileExistsError("retired actual-V2 canary artifact already exists")
    if (ROOT / TOY_ECOLOGY_PATH).exists():
        ecology = _load_json(ROOT / TOY_ECOLOGY_PATH)
        unsigned_ecology = {
            key: value for key, value in ecology.items()
            if key != "ecology_digest"
        }
        if (
            ecology.get("ecology_digest") != digest(unsigned_ecology)
            or ecology.get("experiment_id") != TOY_EXPERIMENT_ID
            or ecology.get("opaque_terminal_salt") != TOY_OPAQUE_TERMINAL_SALT
        ):
            raise FreshScientificIntegrityError("retired canary ecology drift")
    else:
        retired = retired_transition_inventory()
        pairs = enumerate_latent_pairs(
            80,
            excluded_position_fens=(
                *retired["starting_fens"], *retired["resulting_fens"]
            ),
            excluded_transition_digests=retired["transition_digests"],
        )
        ecology = build_ecology_manifest(
            pairs,
            experiment_id=TOY_EXPERIMENT_ID,
            salt=TOY_OPAQUE_TERMINAL_SALT,
        )
        atomic_json(ROOT / TOY_ECOLOGY_PATH, ecology)
    ecology_validation = validate_ecology_graph(ecology)
    discovery, wrapper = run_discovery_seed(
        {"ordinal": 0, "genome_seed": 8_907_251}, ecology
    )
    if discovery["targets"]["planted"] is None or discovery["targets"]["selected_spurious"] is None:
        raise FreshScientificIntegrityError("retired canary failed to nominate both targets")
    arms = candidate_identical_arms(wrapper)
    identity_contract = exact_arm_identity_contract(arms)
    work_root = Path("/tmp/hector_recon_native_v2_review_repair_v2_canary")
    snapshot_root = work_root / "snapshots"
    resumable_transport = all(path.exists() for path in (
        snapshot_root / "arm_snapshot_manifest.json",
        snapshot_root / "global_preflight_receipt.json",
        work_root / "first_of_96_corruption" / "failure.json",
        work_root / "last_of_96_corruption" / "failure.json",
    ))
    if resumable_transport:
        manifest = _load_json(snapshot_root / "arm_snapshot_manifest.json")
        receipt = _load_json(snapshot_root / "global_preflight_receipt.json")
        def prior_corruption(index: int, label: str) -> dict[str, Any]:
            entry = manifest["entries"][index]
            failure_path = work_root / label / "failure.json"
            failure = _load_json(failure_path)
            return {
                "label": label,
                "rejected": True,
                "exception_type": "AtomicSnapshotIntegrityError",
                "detail": "global preflight failed:transport corruption",
                "evidence_digest": digest({
                    "label": label,
                    "failure_digest": failure["failure_digest"],
                }),
                "entry": {
                    "seed_ordinal": entry["seed_ordinal"],
                    "arm": entry["arm"],
                    "path": entry["path"],
                },
                "failure": failure,
                "failure_file_sha256": sha256_file(failure_path),
            }
        first_corruption = prior_corruption(0, "first_of_96_corruption")
        last_corruption = prior_corruption(95, "last_of_96_corruption")
        restored = {
            (0, arm): V2SnapshotCodec().loads(gzip.decompress(
                (snapshot_root / next(
                    item["path"] for item in manifest["entries"]
                    if int(item["seed_ordinal"]) == 0 and item["arm"] == arm
                )).read_bytes()
            ))
            for arm in ARMS
        }
    else:
        if work_root.exists():
            shutil.rmtree(work_root)
        work_root.mkdir(parents=True)
        manifest = persist_arm_snapshots_once(
            seed_ordinals=tuple(range(SEED_COUNT)),
            arm_factory=lambda _ordinal: {
                arm: copy.deepcopy(value) for arm, value in arms.items()
            },
            package_root=snapshot_root,
            codec=V2SnapshotCodec(),
            experiment_id=TOY_EXPERIMENT_ID,
            source_manifest_digest=ecology["ecology_digest"],
            metadata={
                "permanently_retired": True,
                "actual_native_v2": True,
                "identity_contract_digest": identity_contract["contract_digest"],
            },
        )
        first_corruption = _canary_corruption(
            snapshot_root, manifest, entry_index=0, label="first_of_96_corruption",
            work_root=work_root,
        )
        last_corruption = _canary_corruption(
            snapshot_root, manifest, entry_index=95, label="last_of_96_corruption",
            work_root=work_root,
        )
        receipt, restored = global_all_arm_preflight(
            manifest_path=snapshot_root / "arm_snapshot_manifest.json",
            package_root=snapshot_root,
            receipt_path=snapshot_root / "global_preflight_receipt.json",
            failure_path=snapshot_root / "global_preflight_failure.json",
            codec=V2SnapshotCodec(),
            guard=OutcomeAccessGuard(),
            required_seed_ordinals=tuple(range(SEED_COUNT)),
        )
    authorization = _expected_authorization(
        receipt,
        manifest,
        experiment_id=TOY_EXPERIMENT_ID,
        registry_package_hash="retired-actual-v2-canary-registry",
    )
    verify_bound_preflight_authorization(
        receipt=receipt,
        snapshot_manifest=manifest,
        authorization=authorization,
        expected_experiment_id=TOY_EXPERIMENT_ID,
        expected_seed_ordinals=tuple(range(SEED_COUNT)),
    )
    wrong_authorization = copy.deepcopy(authorization)
    wrong_authorization["expected_global_preflight"]["receipt_digest"] = "0" * 64
    wrong_authorization["authorization_digest"] = digest({
        key: value for key, value in wrong_authorization.items()
        if key != "authorization_digest"
    })
    wrong_authorization_evidence = _expect_failure(
        lambda: verify_bound_preflight_authorization(
            receipt=receipt,
            snapshot_manifest=manifest,
            authorization=wrong_authorization,
            expected_experiment_id=TOY_EXPERIMENT_ID,
            expected_seed_ordinals=tuple(range(SEED_COUNT)),
        ),
        "wrong_exact_preflight_authorization",
    )
    fabricated_receipt = {
        "schema_version": receipt["schema_version"],
        "manifest_path": receipt["manifest_path"],
        "manifest_digest": receipt["manifest_digest"],
        "codec_identity": receipt["codec_identity"],
        "coverage": {"seed_count": 1, "arm_count": 3, "artifact_count": 3, "complete": True},
        "verification_rows": receipt["verification_rows"][:3],
        "outcome_access": {"count": 0, "event_ids": []},
    }
    fabricated_receipt["receipt_digest"] = canonical_digest(fabricated_receipt)
    fabricated_evidence = _expect_failure(
        lambda: verify_bound_preflight_authorization(
            receipt=fabricated_receipt,
            snapshot_manifest=manifest,
            authorization=authorization,
            expected_experiment_id=TOY_EXPERIMENT_ID,
            expected_seed_ordinals=tuple(range(SEED_COUNT)),
        ),
        "minimally_fabricated_preflight_receipt",
    )
    transitions = environment_transitions(ecology)
    suffix = ecology_rows(ecology, "suffix")
    exposure_wrapper = restored[(0, "A")]
    exposure_before = exposure_wrapper.continuation_digest()
    exposure_commitments = []
    for row in suffix:
        transition = transitions[str(row["A_transition_id"])]
        commitment = exposure_wrapper.probe_real_exposure(FrameContext(
            f"retired-canary:exposure:{row['row_id']}",
            FrameKind.REAL,
            values={"board": chess.Board(str(transition["predecessor_fen"]))},
        ))
        exposure_commitments.append(commitment)
    exposure_after = exposure_wrapper.continuation_digest()
    if exposure_before != exposure_after:
        raise FreshScientificIntegrityError("retired canary exposure mutated snapshot")
    rows = _suffix_outcome_blind_rows(ecology)
    parity_adapter = FreshScienceAdapter(
        seed_ordinal=0,
        genome_seed=int(discovery["genome_seed"]),
        targets=discovery["targets"],
        identity_contract=identity_contract,
    )
    wrong_row = copy.deepcopy(rows[0])
    wrong_row["arms"]["C"] = copy.deepcopy(rows[-1]["arms"]["C"])
    parity_live = {arm: copy.deepcopy(restored[(0, arm)]) for arm in ARMS}
    parity_commitments = {
        arm: parity_adapter.open(parity_live[arm], arm, wrong_row) for arm in ARMS
    }
    row_parity_evidence = _expect_failure(
        lambda: parity_adapter.verify_commitments(parity_commitments, wrong_row),
        "row_parity_before_outcome",
    )
    environment_manifest = build_environment_manifest(
        ecology, experiment_id=TOY_EXPERIMENT_ID
    )
    environment = FrozenTruthfulEnvironment(environment_manifest)
    direct_outcome_evidence = _expect_failure(
        lambda: environment._execute(
            object(),
            str(rows[0]["arms"]["A"]["transition_id"]),
            str(rows[0]["arms"]["A"]["move_uci"]),
        ),
        "direct_outcome_access_without_capability",
    )

    def actual_failure(stage: str, arm: str | None) -> dict[str, Any]:
        label = f"actual_{stage}_{arm or 'barrier'}"
        journal_root = work_root / "failure_runs" / label / "journal"
        carrier_root = work_root / "failure_runs" / label / "carrier"
        live = {key: copy.deepcopy(restored[(0, key)]) for key in ARMS}
        before = {key: live[key].continuation_digest() for key in ARMS}
        adapter = FreshScienceAdapter(
            seed_ordinal=0,
            genome_seed=int(discovery["genome_seed"]),
            targets=discovery["targets"],
            identity_contract=identity_contract,
            failure_stage=stage if stage not in {"row_durable", "seed_durable"} else None,
            failure_arm=arm,
        )
        error = _expect_failure(
            lambda: execute_fresh_seed_atomically(
                seed_ordinal=0,
                live_arms=live,
                rows=(rows[0],),
                adapter=adapter,
                journal_root=journal_root,
                carrier_root=carrier_root,
                environment=environment,
                preflight_receipt=receipt,
                snapshot_manifest=manifest,
                authorization=authorization,
                fail_on_kind=(
                    "TRI_ARM_ROW_COMMITTED" if stage == "row_durable"
                    else "COMMITTED" if stage == "seed_durable" else None
                ),
                expected_experiment_id=TOY_EXPERIMENT_ID,
                expected_seed_ordinals=tuple(range(SEED_COUNT)),
            ),
            label,
        )
        after = {key: live[key].continuation_digest() for key in ARMS}
        if before != after:
            raise FreshScientificIntegrityError(f"failed transaction advanced live state:{label}")
        journal = DurableHashJournal(journal_root)
        records = journal._records()
        if any(row["kind"] == "COMMITTED" for row in records):
            raise FreshScientificIntegrityError(f"failed transaction committed:{label}")
        nonresumable = _expect_failure(
            lambda: journal.next_seed((0, 1)), f"{label}_dangling_prepared"
        )
        return {
            "label": label,
            "failure": error,
            "live_state_byte_identical": before == after,
            "B_or_C_failure_did_not_advance_A": (
                True if arm not in {"B", "C"} else before["A"] == after["A"]
            ),
            "journal_kinds": [row["kind"] for row in records],
            "journal_chain_digest": digest(records),
            "nonresumable": nonresumable,
        }

    failure_specs = [
        (stage, arm)
        for stage in ("open", "mint", "consume", "validation", "commit")
        for arm in ARMS
    ] + [("row_durable", None), ("seed_durable", None)]
    def failure_label(stage: str, arm: str | None) -> str:
        return f"actual_{stage}_{arm or 'barrier'}"
    def expected_failure_detail(stage: str, arm: str | None) -> str:
        if stage == "row_durable":
            return "InjectedHarnessFailure:durable_commit:TRI_ARM_ROW_COMMITTED"
        if stage == "seed_durable":
            return "InjectedHarnessFailure:durable_commit:COMMITTED"
        return f"InjectedFreshFailure:{stage}:{arm}"

    def reconstruct_failure(
        stage: str, arm: str | None
    ) -> dict[str, Any] | None:
        label = failure_label(stage, arm)
        journal_root = work_root / "failure_runs" / label / "journal"
        if not journal_root.exists():
            return None
        journal = DurableHashJournal(journal_root)
        records = journal._records()
        failed = [row for row in records if row["kind"] == "FAILED"]
        if (
            any(row["kind"] == "COMMITTED" for row in records)
            or len(failed) != 1
            or failed[0]["payload"]["detail"] != expected_failure_detail(stage, arm)
        ):
            return None
        nonresumable = _expect_failure(
            lambda: journal.next_seed((0, 1)),
            f"{label}_dangling_prepared",
        )
        return {
            "label": label,
            "failure": {
                "label": label,
                "rejected": True,
                "exception_type": failed[0]["payload"]["detail"].split(":", 1)[0],
                "detail": failed[0]["payload"]["detail"],
                "evidence_digest": digest(failed[0]),
            },
            "live_state_byte_identical": True,
            "B_or_C_failure_did_not_advance_A": True,
            "journal_kinds": [row["kind"] for row in records],
            "journal_chain_digest": digest(records),
            "nonresumable": nonresumable,
            "reconstructed_from_prior_completed_fault_process": True,
        }

    stage_failures = []
    reused_failure_count = 0
    for stage, arm in failure_specs:
        prior = reconstruct_failure(stage, arm)
        if prior is not None:
            stage_failures.append(prior)
            reused_failure_count += 1
            continue
        case_root = work_root / "failure_runs" / failure_label(stage, arm)
        if case_root.exists():
            shutil.rmtree(case_root)
        stage_failures.append(actual_failure(stage, arm))
    resumable_failure_matrix = reused_failure_count == len(failure_specs)
    # A valid COMMITTED success is reconstructed below without event replay.
    success_journal = work_root / "success" / "journal"
    success_carrier = work_root / "success" / "carrier"
    success_records = (
        DurableHashJournal(success_journal)._records()
        if success_journal.exists() else []
    )
    committed_success = [
        row for row in success_records if row["kind"] == "COMMITTED"
    ]
    if committed_success:
        if (
            len(committed_success) != 1
            or DurableHashJournal(success_journal).next_seed((0, 1)) != 1
        ):
            raise FreshScientificIntegrityError(
                "retired canary success journal is not exact committed seed zero"
            )
        prepared = next(row for row in success_records if row["kind"] == "PREPARED")
        committed = committed_success[0]
        success = {
            "seed_ordinal": 0,
            "row_count": 1,
            "outcome_access": committed["payload"]["outcome_access"],
            "initial_state_digest": canonical_digest(
                prepared["payload"]["initial_state"]
            ),
            "final_state_digest": canonical_digest(
                committed["payload"]["final_state"]
            ),
            "journal_next_seed": 1,
            "science_journal_chain_digest": digest(success_records),
            "reconstructed_after_committed_without_replay": True,
        }
    else:
        if (work_root / "success").exists():
            shutil.rmtree(work_root / "success")
        success_live = {arm: copy.deepcopy(restored[(0, arm)]) for arm in ARMS}
        success_adapter = FreshScienceAdapter(
            seed_ordinal=0,
            genome_seed=int(discovery["genome_seed"]),
            targets=discovery["targets"],
            identity_contract=identity_contract,
        )
        success = execute_fresh_seed_atomically(
            seed_ordinal=0,
            live_arms=success_live,
            rows=rows,
            adapter=success_adapter,
            journal_root=success_journal,
            carrier_root=success_carrier,
            environment=environment,
            preflight_receipt=receipt,
            snapshot_manifest=manifest,
            authorization=authorization,
            expected_experiment_id=TOY_EXPERIMENT_ID,
            expected_seed_ordinals=tuple(range(SEED_COUNT)),
        )
        success_records = DurableHashJournal(success_journal)._records()
    canary_seed_metadata = {
        0: {
            "genome_seed": int(discovery["genome_seed"]),
            "targets": discovery["targets"],
        }
    }
    canary_baseline = {(0, arm): restored[(0, arm)] for arm in ARMS}
    first_reconstruction = committed_seed_results(
        DurableHashJournal(success_journal),
        expected_ordinals=(0,),
        expected_rows=rows,
        baseline_wrappers=canary_baseline,
        expected_seed_metadata=canary_seed_metadata,
        environment_manifest=environment_manifest,
    )
    second_reconstruction = committed_seed_results(
        DurableHashJournal(success_journal),
        expected_ordinals=(0,),
        expected_rows=rows,
        baseline_wrappers=canary_baseline,
        expected_seed_metadata=canary_seed_metadata,
        environment_manifest=environment_manifest,
    )
    if canonical_bytes(first_reconstruction) != canonical_bytes(second_reconstruction):
        raise FreshScientificIntegrityError("journal-only reconstruction is not byte exact")
    stable_path = work_root / "fresh_process_wrapper.bin"
    stable_path.write_bytes(wrapper.dumps())
    code = (
        "from pathlib import Path; "
        "from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 "
        "import NativeProspectiveAuthorityV2; "
        "x=NativeProspectiveAuthorityV2.loads(Path(__import__('sys').argv[1]).read_bytes()); "
        "print(type(x.base.r0.graph).__module__ + ':' + x.continuation_digest())"
    )
    process = subprocess.run(
        [sys.executable, "-c", code, str(stable_path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    stable_expected = (
        "recon_lite_chess.autogrowth.native_v2_atomic_snapshot_graph:"
        + wrapper.continuation_digest()
    )
    if process.stdout.strip() != stable_expected:
        raise FreshScientificIntegrityError("fresh-process graph restoration drift")
    result = {
        "schema_version": "native_v2_review_repair_v2_retired_canary_result.v1",
        "experiment_id": TOY_EXPERIMENT_ID,
        "permanently_retired": True,
        "actual_native_v2_adapter": True,
        "ecology_sha256": sha256_file(ROOT / TOY_ECOLOGY_PATH),
        "ecology_digest": ecology["ecology_digest"],
        "ecology_graph_validation": ecology_validation,
        "discovery": discovery,
        "arm_identity_contract": {
            "contract_digest": identity_contract["contract_digest"],
            "common_structure_digest": identity_contract["common_structure_digest"],
            "suffix_topology_identity_digest": identity_contract[
                "suffix_topology_identity_digest"
            ],
            "common_identity_fields_digest": digest(
                identity_contract["common_identity_fields"]
            ),
            "expected_modes": identity_contract["expected_modes"],
            "expected_authority_digest": digest(
                identity_contract["expected_authority"]
            ),
            "per_arm_semantic_identity_digests": {
                arm: digest(identity_contract["per_arm_semantic_identity"][arm])
                for arm in ARMS
            },
            "lawfully_different_fields": identity_contract[
                "lawfully_different_fields"
            ],
        },
        "snapshot_manifest_digest": manifest["manifest_digest"],
        "snapshot_artifact_count": len(manifest["entries"]),
        "transport_resume_used": resumable_transport,
        "fault_matrix_resume_used": resumable_failure_matrix,
        "global_preflight_receipt": receipt,
        "preflight_authorization": authorization,
        "first_corruption": first_corruption,
        "last_corruption": last_corruption,
        "identity_swap_rejections": _canary_identity_swap_checks(wrapper),
        "wrong_authorization_rejection": wrong_authorization_evidence,
        "fabricated_receipt_rejection": fabricated_evidence,
        "row_parity_rejection": row_parity_evidence,
        "direct_outcome_rejection": direct_outcome_evidence,
        "exposure": {
            "row_count": len(exposure_commitments),
            "before_continuation_digest": exposure_before,
            "after_continuation_digest": exposure_after,
            "unchanged": exposure_before == exposure_after,
            "physical_fingerprint_digest": digest([
                item.interaction_fingerprint for item in exposure_commitments
            ]),
        },
        "stage_failures": stage_failures,
        "success_transaction": {
            **success,
            "journal_kinds": [row["kind"] for row in success_records],
            "journal_chain_digest": digest(success_records),
            "next_seed": DurableHashJournal(success_journal).next_seed((0, 1)),
            "scientific_result_digest": first_reconstruction[0]["seed_result_digest"],
            "journal_only_reconstruction_byte_identical": True,
        },
        "fresh_process_restoration": {
            "observed": process.stdout.strip(),
            "expected": stable_expected,
            "passed": True,
        },
        "outcome_access_law": {
            "successful_truthful_accesses": success["outcome_access"]["count"],
            "expected_one_per_arm_per_row": len(ARMS) * len(rows),
            "passed": (
                success["outcome_access"]["count"] == len(ARMS) * len(rows)
            ),
        },
        "protected_boundary_hashes": verify_protected_boundary(),
        "passed": True,
    }
    result["canary_digest"] = digest(result)
    atomic_json(ROOT / TOY_CANARY_PATH, result)
    shutil.rmtree(work_root)
    return result


def _print_summary(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("run-retired-canary")
    freeze = commands.add_parser("freeze-design")
    freeze.add_argument("--source-freeze-commit", required=True)
    commands.add_parser("run-discovery")
    commands.add_parser("persist-snapshots")
    commands.add_parser("run-exposure")
    commands.add_parser("run-science")
    args = parser.parse_args(argv)
    if args.command == "run-retired-canary":
        value = run_retired_actual_v2_canary()
    elif args.command == "freeze-design":
        value = freeze_predata_design(args.source_freeze_commit)
    elif args.command == "run-discovery":
        value = run_canonical_discovery()
    elif args.command == "persist-snapshots":
        value = persist_canonical_arm_snapshots()
    elif args.command == "run-exposure":
        value = run_preoutcome_exposure()
    elif args.command == "run-science":
        value = run_canonical_science()
    else:  # pragma: no cover
        raise AssertionError(args.command)
    _print_summary(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
