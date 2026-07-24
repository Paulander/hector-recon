"""Outer-only V2 prospective-evidence scientific discriminator.

The validated V2.1 engine is imported unchanged.  This module owns the frozen
synthetic chess ecology, outer identity layers, target-specific exposure gate,
canonical runner, and paired seed-level adjudication.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from concurrent.futures import ProcessPoolExecutor
import copy
import gzip
import hashlib
import importlib
import importlib.metadata
import json
import math
import multiprocessing
import os
from pathlib import Path
import pickle
import platform
import random
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind, Node, NodeState, NodeType
from recon_lite_hector.learning import IntrinsicCreditEngine

from .native_authority_handover import (
    FrozenCompetenceProvenance,
    GraphActuation,
    GraphSignalTrace,
    NativeR0Organism,
)
from .native_competence_envelope import (
    AvailabilityState,
    CompetenceEnvelopeConfig,
    SpecializationMode,
    StemCellState,
)
from .native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    ProspectiveV2IntegrityError,
    V2Mode,
    _sha,
)
from .native_prospective_evidence_authority_v2_lab import (
    RegisteredV2ExposureRow,
    V2LaboratoryRegistry,
    policy_critical_package_hashes,
)
from .native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
    _TripletNodeIds,
)
from .native_trace_competence_authority import (
    TraceNativeCompetenceOrganism,
    TraceNativeLearningConfig,
)


BASELINE_COMMIT = "cd0c739f69558030c3bc81daf292af068c6f54d6"
BASELINE_PACKAGE_MANIFEST = (
    "c0116b15982511d446dee7a926c4d31e3066e59e3cc3faf9bb161b4c24b50a58"
)
PROTECTED_HASHES = {
    "src/recon_lite_chess/autogrowth/"
    "native_prospective_evidence_authority_v2.py": (
        "25945864fd998caf22ae12cbcb9bcb4779447337c0079f705640c63d2356f029"
    ),
    "src/recon_lite_chess/autogrowth/"
    "native_prospective_evidence_authority_v2_lab.py": (
        "f3aee5cccf761af1cb6a5de94b886d5e758c0a07cb0f6d77b8898f662ca73b58"
    ),
}
EXPERIMENT_ID = "native_v2_prospective_scientific_discriminator.v1"
OUTER_MANIFEST_KEY = "outer_scientific_manifest"
ROOT = Path(__file__).resolve().parents[3]
PACKAGE_DIR = Path(
    "reports/autogrowth/native_authority/v2_scientific_discriminator"
)
SEED_MANIFEST_PATH = PACKAGE_DIR / "seed_manifest.json"
ECOLOGY_MANIFEST_PATH = PACKAGE_DIR / "ecology_manifest.json"
PERMUTATION_MANIFEST_PATH = PACKAGE_DIR / "c_permutation_manifest.json"
SOURCE_RUNTIME_MANIFEST_PATH = PACKAGE_DIR / "source_runtime_manifest.json"
OUTER_MANIFEST_PATH = PACKAGE_DIR / "outer_manifest.json"
TOY_PARITY_PATH = PACKAGE_DIR / "retired_toy_parity.json"
PREFIX_DIR = PACKAGE_DIR / "prefix_organisms"
PREFIX_MANIFEST_PATH = PACKAGE_DIR / "prefix_candidate_manifest.json"
EXPOSURE_PATH = PACKAGE_DIR / "preoutcome_exposure_admission.json"
RESULT_PATH = PACKAGE_DIR / "canonical_result.json.gz"
PREREGISTRATION_PATH = Path(
    "docs/autogrowth/"
    "NATIVE_PROSPECTIVE_EVIDENCE_V2_SCIENCE_PREREGISTRATION_20260724.md"
)
COMPLIANCE_PATH = Path(
    "docs/autogrowth/"
    "NATIVE_PROSPECTIVE_EVIDENCE_V2_SCIENCE_COMPLIANCE_20260724.md"
)
TEST_PATH = Path(
    "tests/autogrowth/test_native_prospective_evidence_v2_science.py"
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
PRIMARY_ALPHA = 0.05
MIN_QUALIFYING_SEEDS = 24
MIN_FAVORABLE_SEEDS = 17
MIN_TARGET_OPPORTUNITIES = 4
SEED_COUNT = 32
PREFIX_POSITIVE_COUNT = 32
PREFIX_NEGATIVE_PER_ATOM = 8
SUFFIX_SPURIOUS_COUNT = 8
SUFFIX_PLANTED_COUNT = 8
BOOTSTRAP_REPLICATES = 20_000


class ScientificIntegrityError(RuntimeError):
    """Fail-closed outer laboratory or manifest boundary."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _atomic_json(path: str | Path, value: Any, *, replace: bool = False) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not replace:
        raise FileExistsError(f"refusing to overwrite frozen artifact: {target}")
    payload = json.dumps(
        value, indent=2, sort_keys=True, allow_nan=False
    ).encode("utf-8") + b"\n"
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(target)


def _gzip_bytes(payload: bytes) -> bytes:
    import io
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as handle:
        handle.write(payload)
    return buffer.getvalue()


def _git(*args: str) -> str:
    return subprocess.check_output(
        ("git", *args), cwd=ROOT, text=True
    ).strip()


def require_clean_worktree() -> None:
    if _git("status", "--porcelain=v1"):
        raise ScientificIntegrityError("scientific phase requires clean worktree")


def verify_protected_boundary() -> None:
    for relative, expected in PROTECTED_HASHES.items():
        observed = sha256_file(ROOT / relative)
        if observed != expected:
            raise ScientificIntegrityError(
                f"engineering_boundary_requires_reclosure:{relative}:{observed}"
            )
    package = policy_critical_package_hashes(ROOT)
    digest = hashlib.sha256(
        json.dumps(
            package, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    if digest != BASELINE_PACKAGE_MANIFEST:
        raise ScientificIntegrityError(
            "engineering_boundary_requires_reclosure:package_manifest"
        )


def opaque_terminal_identity(private_name: str) -> str:
    return "opaque_terminal:" + hashlib.sha256(
        f"{EXPERIMENT_ID}|{private_name}".encode("utf-8")
    ).hexdigest()


def canonical_pattern_digest(members: Iterable[str]) -> str:
    return sha256_json({"members": sorted(set(map(str, members)))})


def _fen_terminal(node: Node, env: Mapping[str, Any]) -> tuple[bool, bool]:
    board = env.get("board")
    if not isinstance(board, chess.Board):
        node.activation.value = 0.0
        return True, False
    active = board.fen() in set(map(str, node.meta.get("active_fens", ())))
    node.activation.value = 1.0 if active else 0.0
    return True, active


class OpaqueChessEcologyGraph(NativeReConKRKGraph):
    """Native graph with frozen, opaque FEN-backed external terminals."""

    def __init__(self, *, config: NativeSingleGraphConfig) -> None:
        super().__init__(config=config)
        self.predecessor_routes: dict[str, tuple[str, str]] = {}

    def _candidate_triplets_for_board(
        self,
        board: chess.Board,
        legal: Mapping[str, chess.Move],
    ) -> dict[str, str]:
        route = self.predecessor_routes.get(board.fen())
        if route is None:
            return {}
        triplet_id, move_uci = route
        if move_uci not in legal:
            raise RuntimeError("frozen ecology route emitted an illegal move")
        return {triplet_id: move_uci}

    def _restore_runtime_predicates(self) -> None:
        super()._restore_runtime_predicates()
        for node in self.graph.nodes.values():
            if node.meta.get("opaque_external_terminal"):
                node.predicate = _fen_terminal
            elif node.meta.get("opaque_route_guard"):
                node.predicate = _fen_terminal


@dataclass(frozen=True)
class EcologyRow:
    row_id: str
    phase: str
    visible_family: str
    active_atom_ids: tuple[str, ...]
    move_uci: str
    a_fen: str
    c_fen: str
    a_outcome: bool
    c_outcome: bool
    latent_pair_id: str

    def manifest(self) -> dict[str, Any]:
        return asdict(self)


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
            if source == target:
                continue
            if (
                chess.square_file(source) == chess.square_file(target)
                or chess.square_rank(source) == chess.square_rank(target)
            ):
                moves.append(chess.Move(source, target).uci())
    return tuple(sorted(moves))


def _latent_pair_pool(required: int) -> tuple[dict[str, Any], ...]:
    selected: list[dict[str, Any]] = []
    used_fens: set[str] = set()
    for move_uci in _rook_move_ucis():
        move = chess.Move.from_uci(move_uci)
        mates: list[str] = []
        nonmates: list[str] = []
        for wk in chess.SQUARES:
            for bk in chess.SQUARES:
                board = _empty_krk_board(wk, move.from_square, bk)
                if (
                    not board.is_valid()
                    or board.is_game_over()
                    or move not in board.legal_moves
                ):
                    continue
                successor = board.copy(stack=False)
                successor.push(move)
                target = mates if successor.is_checkmate() else nonmates
                if board.fen() not in used_fens and board.fen() not in target:
                    target.append(board.fen())
        pair_count = min(len(mates), len(nonmates), 6)
        for index in range(pair_count):
            mate_fen = mates[index]
            nonmate_fen = nonmates[index]
            if mate_fen in used_fens or nonmate_fen in used_fens:
                continue
            used_fens.update((mate_fen, nonmate_fen))
            selected.append({
                "pair_id": f"latent-pair-{len(selected):03d}",
                "move_uci": move_uci,
                "mate_fen": mate_fen,
                "nonmate_fen": nonmate_fen,
            })
            if len(selected) == required:
                return tuple(selected)
    raise ScientificIntegrityError("route_a_pairing_impossible")


def _logical_specs() -> tuple[dict[str, Any], ...]:
    specs: list[dict[str, Any]] = []
    for index in range(PREFIX_POSITIVE_COUNT):
        specs.append({
            "row_id": f"prefix-positive-{index:02d}",
            "phase": "prefix",
            "family": "prefix_positive",
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
                "family": f"prefix_negative_{group}",
                "atoms": atoms,
                "a_outcome": False,
            })
    for index in range(SUFFIX_SPURIOUS_COUNT):
        specs.append({
            "row_id": f"suffix-spurious-{index:02d}",
            "phase": "suffix",
            "family": "suffix_spurious",
            "atoms": ("s0", "s1"),
            "a_outcome": False,
        })
    for index in range(SUFFIX_PLANTED_COUNT):
        specs.append({
            "row_id": f"suffix-planted-{index:02d}",
            "phase": "suffix",
            "family": "suffix_planted",
            "atoms": ("p0", "p1"),
            "a_outcome": True,
        })
    return tuple(specs)


def generate_ecology_manifest() -> dict[str, Any]:
    specs = _logical_specs()
    pairs = _latent_pair_pool(len(specs))
    atom_map = {
        name: opaque_terminal_identity(name)
        for name in ("p0", "p1", "s0", "s1", *(f"n{i}" for i in range(8)))
    }
    rows: list[EcologyRow] = []
    for spec, pair in zip(specs, pairs, strict=True):
        a_outcome = bool(spec["a_outcome"])
        a_fen = pair["mate_fen"] if a_outcome else pair["nonmate_fen"]
        c_fen = pair["nonmate_fen"] if a_outcome else pair["mate_fen"]
        rows.append(EcologyRow(
            row_id=str(spec["row_id"]),
            phase=str(spec["phase"]),
            visible_family=str(spec["family"]),
            active_atom_ids=tuple(sorted(atom_map[item] for item in spec["atoms"])),
            move_uci=str(pair["move_uci"]),
            a_fen=a_fen,
            c_fen=c_fen,
            a_outcome=a_outcome,
            c_outcome=not a_outcome,
            latent_pair_id=str(pair["pair_id"]),
        ))
    if len({row.a_fen for row in rows} | {row.c_fen for row in rows}) != 2 * len(rows):
        raise ScientificIntegrityError("latent transition reuse")
    prefix = tuple(row for row in rows if row.phase == "prefix")
    suffix = tuple(row for row in rows if row.phase == "suffix")
    planted_members = tuple(sorted((atom_map["p0"], atom_map["p1"])))
    spurious_members = tuple(sorted((atom_map["s0"], atom_map["s1"])))
    manifest = {
        "schema_version": "native_v2_science_ecology.v1",
        "experiment_id": EXPERIMENT_ID,
        "learner_visible_labels": False,
        "completion_terminal_identity": "mate",
        "opaque_terminal_identities": sorted(atom_map.values()),
        "laboratory_private_atom_map": atom_map,
        "planted_pattern_digest": canonical_pattern_digest(planted_members),
        "planted_members": list(planted_members),
        "spurious_family": [{
            "pattern_digest": canonical_pattern_digest(spurious_members),
            "members": list(spurious_members),
        }],
        "spurious_selection_rule": (
            "eligible_predeclared_family_then_lexicographically_smallest_"
            "sha256_canonical_hypothesis_manifest_then_cell_id"
        ),
        "prefix_row_order": [row.row_id for row in prefix],
        "suffix_row_order": [row.row_id for row in suffix],
        "rows": [row.manifest() for row in rows],
        "outcome_marginals": {
            "prefix_a": {
                "true": sum(row.a_outcome for row in prefix),
                "false": sum(not row.a_outcome for row in prefix),
            },
            "suffix_a": {
                "true": sum(row.a_outcome for row in suffix),
                "false": sum(not row.a_outcome for row in suffix),
            },
            "suffix_c": {
                "true": sum(row.c_outcome for row in suffix),
                "false": sum(not row.c_outcome for row in suffix),
            },
        },
    }
    manifest["ecology_digest"] = sha256_json(manifest)
    return manifest


def _rows(ecology: Mapping[str, Any], phase: str) -> tuple[EcologyRow, ...]:
    return tuple(
        EcologyRow(
            row_id=str(row["row_id"]),
            phase=str(row["phase"]),
            visible_family=str(row["visible_family"]),
            active_atom_ids=tuple(map(str, row["active_atom_ids"])),
            move_uci=str(row["move_uci"]),
            a_fen=str(row["a_fen"]),
            c_fen=str(row["c_fen"]),
            a_outcome=bool(row["a_outcome"]),
            c_outcome=bool(row["c_outcome"]),
            latent_pair_id=str(row["latent_pair_id"]),
        )
        for row in ecology["rows"]
        if row["phase"] == phase
    )


def _route_terminal_predicate(node: Node, env: Mapping[str, Any]) -> tuple[bool, bool]:
    return _fen_terminal(node, env)


def build_ecology_r0(ecology: Mapping[str, Any]) -> NativeR0Organism:
    if ecology.get("ecology_digest") != sha256_json({
        key: value for key, value in ecology.items() if key != "ecology_digest"
    }):
        raise ScientificIntegrityError("ecology manifest digest mismatch")
    config = NativeSingleGraphConfig(
        include_symmetries=False,
        key_mode="exact",
        shared_feature_atoms=False,
        include_grouped_cache_terminals=True,
        terminal_score_normalization="sum",
        max_ticks=128,
    )
    graph = OpaqueChessEcologyGraph(config=config)
    rows = _rows(ecology, "prefix") + _rows(ecology, "suffix")
    by_move: dict[str, list[EcologyRow]] = {}
    for row in rows:
        by_move.setdefault(row.move_uci, []).append(row)
    route_triplets: dict[str, str] = {}
    for move_uci, route_rows in sorted(by_move.items()):
        reference = chess.Board(route_rows[0].a_fen)
        move = chess.Move.from_uci(move_uci)
        if move not in reference.legal_moves:
            raise ScientificIntegrityError("frozen route reference is illegal")
        triplet_id = graph.ensure_triplet(
            reference, move, stage="opaque_synthetic_ecology"
        )
        route_triplets[move_uci] = triplet_id
        active_fens = tuple(sorted({
            fen for row in route_rows for fen in (row.a_fen, row.c_fen)
        }))
        for node_id in tuple(graph.triplet_nodes[triplet_id]):
            node = graph.graph.nodes[node_id]
            if node.ntype is not NodeType.TERMINAL:
                continue
            if node.meta.get("actuator_terminal"):
                continue
            node.meta["opaque_route_guard"] = True
            node.meta["active_fens"] = list(active_fens)
            node.predicate = _route_terminal_predicate
        for row in route_rows:
            graph.predecessor_routes[row.a_fen] = (triplet_id, move_uci)
            graph.predecessor_routes[row.c_fen] = (triplet_id, move_uci)

    all_atom_ids = tuple(map(str, ecology["opaque_terminal_identities"]))
    active_fens_by_atom = {
        atom_id: tuple(sorted({
            fen
            for row in rows
            if atom_id in row.active_atom_ids
            for fen in (row.a_fen, row.c_fen)
        }))
        for atom_id in all_atom_ids
    }
    for atom_id in all_atom_ids:
        graph.graph.add_node(Node(
            atom_id,
            NodeType.TERMINAL,
            predicate=_fen_terminal,
            meta={
                "origin": "v2_science_opaque_external_terminal",
                "role": "opaque_external_terminal",
                "terminal_kind": "opaque_external_terminal",
                "shared_feature_atom": True,
                # The native snapshot loader requires terminal_key for every
                # shared atom before this subclass restores its opaque predicate.
                "terminal_key": atom_id,
                "opaque_external_terminal": True,
                "learner_visible_label": False,
                "active_fens": list(active_fens_by_atom[atom_id]),
                "local_weight": 0.0,
            },
        ))
    for move_uci, triplet_id in sorted(route_triplets.items()):
        route_fens = {
            fen for row in by_move[move_uci] for fen in (row.a_fen, row.c_fen)
        }
        active_atoms = tuple(
            atom_id for atom_id in all_atom_ids
            if route_fens.intersection(active_fens_by_atom[atom_id])
        )
        action_script = _TripletNodeIds(triplet_id).action_script
        for atom_id in active_atoms:
            graph._add_hierarchy_pair(
                action_script, atom_id, trainable=False, weight=0.0
            )
            graph.triplet_nodes[triplet_id].add(atom_id)
    graph.mature_existing_graph()
    graph.freeze_existing_parameters(reason="v2_science_frozen_ecology")

    credit = IntrinsicCreditEngine()
    child_id = "opaque_synthetic_chess_actuator"
    credit_state = credit.register(
        child_id,
        mature=True,
        initial_fast_value=1.0,
        initial_slow_value=1.0,
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
        grounding_source="frozen_synthetic_environment_actuator_provenance",
        completion_terminal_kind="mate",
    )
    return NativeR0Organism(
        graph=graph,
        credit=credit,
        provenance=provenance,
        frozen_triplet_ids=frozenset(graph.triplet_ids),
        source_manifest={
            "experiment_id": EXPERIMENT_ID,
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
        "confirmed_base_terminal_node_ids": list(
            trace.confirmed_base_terminal_node_ids
        ),
        "confirmed_mature_composite_ids": list(
            trace.confirmed_mature_composite_ids
        ),
        "option_identity": trace.option_identity,
        "actuation": asdict(trace.actuation),
    }


def validate_ecology_graph(ecology: Mapping[str, Any]) -> dict[str, Any]:
    r0 = build_ecology_r0(ecology)
    rows = _rows(ecology, "prefix") + _rows(ecology, "suffix")
    validations = []
    for row in rows:
        arm_manifests = {}
        for arm, fen, outcome in (
            ("a", row.a_fen, row.a_outcome),
            ("c", row.c_fen, row.c_outcome),
        ):
            board = chess.Board(fen)
            frame = FrameContext(
                f"ecology-validation:{arm}:{row.row_id}",
                FrameKind.REAL,
                values={"board": board},
            )
            actuation, trace = r0.emit_action_with_trace(frame)
            if actuation is None or trace is None:
                raise ScientificIntegrityError("ecology graph emitted no action")
            if actuation.move_uci != row.move_uci or actuation.candidate_count != 1:
                raise ScientificIntegrityError("ecology graph actuation mismatch")
            successor = board.copy(stack=False)
            successor.push(chess.Move.from_uci(actuation.move_uci))
            if successor.is_checkmate() is not outcome:
                raise ScientificIntegrityError("ecology outcome is not truthful")
            expected_signals = tuple(sorted((
                *row.active_atom_ids, "internal:policy_response"
            )))
            if trace.ordered_signal_identities != expected_signals:
                raise ScientificIntegrityError("opaque terminal trace mismatch")
            arm_manifests[arm] = visible_trace_manifest(trace)
        if arm_manifests["a"] != arm_manifests["c"]:
            raise ScientificIntegrityError("control_exposure_parity_failure")
        validations.append({
            "row_id": row.row_id,
            "visible_manifest_digest": sha256_json(arm_manifests["a"]),
            "a_outcome": row.a_outcome,
            "c_outcome": row.c_outcome,
        })
    return {
        "source_organism_identity": r0.source_organism_identity(),
        "source_state_identity": r0.trace_state_identity(),
        "row_count": len(rows),
        "exact_visible_pair_count": len(validations),
        "rows": validations,
        "validation_digest": sha256_json(validations),
    }


def _tracked_runtime_paths() -> tuple[str, ...]:
    tracked = tuple(filter(None, _git("ls-files").splitlines()))
    paths = tuple(sorted(
        path for path in tracked
        if path.startswith("src/") or path.startswith("libs/recon-lite/src/")
    ))
    if not paths:
        raise ScientificIntegrityError("tracked runtime source tree is empty")
    return paths


def _required_experiment_paths() -> tuple[str, ...]:
    return tuple(map(str, (
        Path(__file__).resolve().relative_to(ROOT),
        TEST_PATH,
        PREREGISTRATION_PATH,
        COMPLIANCE_PATH,
    )))


def _configuration_paths() -> tuple[str, ...]:
    candidates = (
        "pyproject.toml", "uv.lock", ".python-version", "pytest.ini",
        "ruff.toml", "setup.cfg", "tox.ini",
    )
    return tuple(path for path in candidates if (ROOT / path).is_file())


def _module_identity(name: str) -> dict[str, Any]:
    module = importlib.import_module(name)
    raw_path = getattr(module, "__file__", None)
    if raw_path is None:
        raise ScientificIntegrityError(f"imported module has no path: {name}")
    path = Path(raw_path).resolve()
    result = {
        "module": name,
        "resolved_path": str(path),
        "sha256": sha256_file(path),
        "repository_owned": False,
    }
    try:
        relative = path.relative_to(ROOT)
    except ValueError:
        pass
    else:
        relative_text = str(relative)
        source_owned = (
            relative_text.startswith("src/")
            or relative_text.startswith("libs/recon-lite/src/")
        )
        if source_owned:
            result["repository_owned"] = True
            result["repository_relative_path"] = relative_text
    return result


def _package_version(distribution: str) -> dict[str, str]:
    return {
        "distribution": distribution,
        "version": importlib.metadata.version(distribution),
    }


def canonical_worker_count() -> int:
    toy_path = ROOT / TOY_PARITY_PATH
    if not toy_path.is_file():
        raise ScientificIntegrityError("retired toy parity artifact is absent")
    toy = json.loads(toy_path.read_text(encoding="utf-8"))
    expected = sha256_json({
        key: value for key, value in toy.items()
        if key != "toy_parity_digest"
    })
    if toy.get("toy_parity_digest") != expected:
        raise ScientificIntegrityError("retired toy parity digest mismatch")
    policy = toy.get("canonical_process_policy")
    if policy == "two_process_spawn" and toy.get("passed") is True:
        return 2
    if policy == "serial" and toy.get("passed") is False:
        return 1
    raise ScientificIntegrityError("retired toy parity policy is inconsistent")


def build_source_runtime_manifest(pre_science_commit: str) -> dict[str, Any]:
    runtime_paths = _tracked_runtime_paths()
    required = _required_experiment_paths()
    tracked = set(filter(None, _git("ls-files").splitlines()))
    missing = sorted(set(required).difference(tracked))
    if missing:
        raise ScientificIntegrityError(
            "experiment source must be committed before freeze: " + ",".join(missing)
        )
    source_hashes = {
        path: sha256_file(ROOT / path) for path in runtime_paths
    }
    experiment_hashes = {
        path: sha256_file(ROOT / path) for path in required
    }
    configuration_hashes = {
        path: sha256_file(ROOT / path) for path in _configuration_paths()
    }
    modules = tuple(
        _module_identity(name) for name in (
            "chess", "recon_lite", "recon_lite_chess",
            "recon_lite_hector",
            "recon_lite_chess.autogrowth."
            "native_prospective_evidence_v2_science",
            "recon_lite_chess.autogrowth."
            "native_prospective_evidence_authority_v2",
            "recon_lite_chess.autogrowth."
            "native_prospective_evidence_authority_v2_lab",
        )
    )
    for row in modules:
        if row["repository_owned"]:
            relative = str(row["repository_relative_path"])
            expected = source_hashes.get(relative) or experiment_hashes.get(relative)
            if expected != row["sha256"]:
                raise ScientificIntegrityError(
                    f"imported repository module is not source-bound: {relative}"
                )
    manifest = {
        "schema_version": "native_v2_science_source_runtime.v1",
        "experiment_id": EXPERIMENT_ID,
        "baseline_commit": BASELINE_COMMIT,
        "pre_science_commit": str(pre_science_commit),
        "protected_hashes": dict(PROTECTED_HASHES),
        "v2_1_package_manifest": BASELINE_PACKAGE_MANIFEST,
        "runtime_source_hashes": source_hashes,
        "experiment_source_hashes": experiment_hashes,
        "configuration_hashes": configuration_hashes,
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "version_info": list(sys.version_info[:5]),
            "executable": str(Path(sys.executable).resolve()),
        },
        "packages": [
            _package_version("python-chess"),
            _package_version("pytest"),
        ],
        "imported_modules": list(modules),
        "deterministic_environment": dict(DETERMINISTIC_ENV),
        "process_policy": {
            "canonical_workers": canonical_worker_count(),
            "worker_start_method": (
                "spawn" if canonical_worker_count() == 2 else None
            ),
            "seed_assignment": (
                "ordinal_modulo_two" if canonical_worker_count() == 2
                else "all_ordinals_in_frozen_order_serial"
            ),
            "arms_within_seed": "A_then_B_then_C_sequential",
            "threads": False,
            "gpu": False,
            "shared_rng": False,
            "mutable_cross_worker_state": False,
            "aggregation_order": "seed_ordinal_then_arm_then_row",
        },
    }
    manifest["source_runtime_digest"] = sha256_json(manifest)
    return manifest


def derive_seed(commit: str, ordinal: int, *, namespace: str = "canonical") -> int:
    digest = hashlib.sha256(
        f"{EXPERIMENT_ID}|{namespace}|{commit}|{ordinal}".encode("utf-8")
    ).digest()
    seed = int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)
    return seed or 1


def generate_seed_manifest(pre_science_commit: str) -> dict[str, Any]:
    rows = [
        {
            "ordinal": ordinal,
            "genome_seed": derive_seed(pre_science_commit, ordinal),
            "derivation_sha256": hashlib.sha256(
                f"{EXPERIMENT_ID}|canonical|{pre_science_commit}|{ordinal}".encode(
                    "utf-8"
                )
            ).hexdigest(),
        }
        for ordinal in range(SEED_COUNT)
    ]
    if len({row["genome_seed"] for row in rows}) != SEED_COUNT:
        raise ScientificIntegrityError("commit-derived genome seed collision")
    manifest = {
        "schema_version": "native_v2_science_seeds.v1",
        "experiment_id": EXPERIMENT_ID,
        "derivation_commit": pre_science_commit,
        "seed_count": SEED_COUNT,
        "retain_all": True,
        "rows": rows,
    }
    manifest["seed_manifest_digest"] = sha256_json(manifest)
    return manifest


def generate_c_permutation_manifest(ecology: Mapping[str, Any]) -> dict[str, Any]:
    suffix = _rows(ecology, "suffix")
    rows = [{
        "row_id": row.row_id,
        "latent_pair_id": row.latent_pair_id,
        "a_transition": {
            "predecessor_fen": row.a_fen,
            "move_uci": row.move_uci,
            "outcome": row.a_outcome,
        },
        "c_transition": {
            "predecessor_fen": row.c_fen,
            "move_uci": row.move_uci,
            "outcome": row.c_outcome,
        },
        "visible_family": row.visible_family,
        "visible_atom_ids": list(row.active_atom_ids),
        "permutation_operation": "swap_within_frozen_opposite_outcome_pair",
    } for row in suffix]
    manifest = {
        "schema_version": "native_v2_science_c_permutation.v1",
        "experiment_id": EXPERIMENT_ID,
        "truthful_transitions": True,
        "label_shuffle": False,
        "outcome_marginals_preserved": (
            sum(row.a_outcome for row in suffix)
            == sum(row.c_outcome for row in suffix)
        ),
        "rows": rows,
    }
    manifest["permutation_digest"] = sha256_json(manifest)
    return manifest


def require_deterministic_environment() -> None:
    mismatches = {
        key: {"required": value, "observed": os.environ.get(key)}
        for key, value in DETERMINISTIC_ENV.items()
        if os.environ.get(key) != value
    }
    if mismatches:
        raise ScientificIntegrityError(
            "deterministic environment mismatch:" + json.dumps(
                mismatches, sort_keys=True
            )
        )


def freeze_design(pre_science_commit: str) -> dict[str, Any]:
    require_clean_worktree()
    require_deterministic_environment()
    verify_protected_boundary()
    if _git("rev-parse", "HEAD") != pre_science_commit:
        raise ScientificIntegrityError("pre-science commit identity mismatch")
    for path in (
        SEED_MANIFEST_PATH, ECOLOGY_MANIFEST_PATH, PERMUTATION_MANIFEST_PATH,
        SOURCE_RUNTIME_MANIFEST_PATH, OUTER_MANIFEST_PATH,
    ):
        if (ROOT / path).exists():
            raise FileExistsError(f"frozen design path already exists: {path}")
    ecology = generate_ecology_manifest()
    graph_validation = validate_ecology_graph(ecology)
    seeds = generate_seed_manifest(pre_science_commit)
    permutation = generate_c_permutation_manifest(ecology)
    source_runtime = build_source_runtime_manifest(pre_science_commit)
    _atomic_json(ROOT / SEED_MANIFEST_PATH, seeds)
    _atomic_json(ROOT / ECOLOGY_MANIFEST_PATH, ecology)
    _atomic_json(ROOT / PERMUTATION_MANIFEST_PATH, permutation)
    _atomic_json(ROOT / SOURCE_RUNTIME_MANIFEST_PATH, source_runtime)
    if not (ROOT / TOY_PARITY_PATH).is_file():
        raise ScientificIntegrityError("retired toy parity artifact is absent")
    design_files = {
        str(path): sha256_file(ROOT / path)
        for path in (
            SEED_MANIFEST_PATH, ECOLOGY_MANIFEST_PATH,
            PERMUTATION_MANIFEST_PATH, TOY_PARITY_PATH,
        )
    }
    predeclared_paths = {
        "toy_parity": str(TOY_PARITY_PATH),
        "prefix_organisms": [
            str(prefix_artifact_path(index)) for index in range(SEED_COUNT)
        ],
        "prefix_candidate_manifest": str(PREFIX_MANIFEST_PATH),
        "preoutcome_exposure": str(EXPOSURE_PATH),
        "canonical_result": str(RESULT_PATH),
    }
    outer = {
        "schema_version": "native_v2_science_outer_manifest.v1",
        "experiment_id": EXPERIMENT_ID,
        "baseline_commit": BASELINE_COMMIT,
        "pre_science_commit": pre_science_commit,
        "source_runtime_manifest": {
            "path": str(SOURCE_RUNTIME_MANIFEST_PATH),
            "sha256": sha256_file(ROOT / SOURCE_RUNTIME_MANIFEST_PATH),
            "digest": source_runtime["source_runtime_digest"],
        },
        "design_files": design_files,
        "ecology_graph_validation": graph_validation,
        "predeclared_artifact_paths": predeclared_paths,
        "frozen_gates": {
            "seed_count": SEED_COUNT,
            "target_opportunities_per_arm": MIN_TARGET_OPPORTUNITIES,
            "minimum_qualifying_seeds": MIN_QUALIFYING_SEEDS,
            "minimum_favorable_seeds": MIN_FAVORABLE_SEEDS,
            "primary_alpha": PRIMARY_ALPHA,
            "primary_tests": ["D_safe", "D_signal"],
            "holm_family_size": 2,
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        },
        "data_prohibition": [
            "KRK historical regression", "fresh KRK", "retired-65",
            "R1", "validation pools", "regression pools", "held-out pools",
        ],
    }
    outer["outer_manifest_digest"] = sha256_json(outer)
    _atomic_json(ROOT / OUTER_MANIFEST_PATH, outer)
    return outer


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify_outer_manifest(phase: str) -> dict[str, Any]:
    require_deterministic_environment()
    verify_protected_boundary()
    outer = _load_json(ROOT / OUTER_MANIFEST_PATH)
    expected_digest = sha256_json({
        key: value for key, value in outer.items()
        if key != "outer_manifest_digest"
    })
    if outer.get("outer_manifest_digest") != expected_digest:
        raise ScientificIntegrityError("outer manifest digest mismatch")
    source_path = ROOT / outer["source_runtime_manifest"]["path"]
    if sha256_file(source_path) != outer["source_runtime_manifest"]["sha256"]:
        raise ScientificIntegrityError("source runtime manifest file mismatch")
    source = _load_json(source_path)
    if source.get("source_runtime_digest") != sha256_json({
        key: value for key, value in source.items()
        if key != "source_runtime_digest"
    }):
        raise ScientificIntegrityError("source runtime digest mismatch")
    for group in (
        "runtime_source_hashes", "experiment_source_hashes",
        "configuration_hashes",
    ):
        for relative, expected in source[group].items():
            if sha256_file(ROOT / relative) != expected:
                raise ScientificIntegrityError(
                    f"source/runtime drift before {phase}: {relative}"
                )
    for row in source["imported_modules"]:
        current = _module_identity(str(row["module"]))
        if current != row:
            raise ScientificIntegrityError(
                f"import path/version drift before {phase}: {row['module']}"
            )
    current_packages = [
        _package_version(str(row["distribution"]))
        for row in source["packages"]
    ]
    if current_packages != source["packages"]:
        raise ScientificIntegrityError(f"package version drift before {phase}")
    for relative, expected in outer["design_files"].items():
        if sha256_file(ROOT / relative) != expected:
            raise ScientificIntegrityError(
                f"design artifact drift before {phase}: {relative}"
            )
    ecology = _load_json(ROOT / ECOLOGY_MANIFEST_PATH)
    if ecology.get("ecology_digest") != sha256_json({
        key: value for key, value in ecology.items()
        if key != "ecology_digest"
    }):
        raise ScientificIntegrityError("ecology digest mismatch")
    seeds = _load_json(ROOT / SEED_MANIFEST_PATH)
    if seeds.get("seed_manifest_digest") != sha256_json({
        key: value for key, value in seeds.items()
        if key != "seed_manifest_digest"
    }):
        raise ScientificIntegrityError("seed manifest digest mismatch")
    permutation = _load_json(ROOT / PERMUTATION_MANIFEST_PATH)
    if permutation.get("permutation_digest") != sha256_json({
        key: value for key, value in permutation.items()
        if key != "permutation_digest"
    }):
        raise ScientificIntegrityError("C permutation digest mismatch")
    return {
        "phase": str(phase),
        "outer_manifest_sha256": sha256_file(ROOT / OUTER_MANIFEST_PATH),
        "outer_manifest_digest": outer["outer_manifest_digest"],
        "source_runtime_digest": source["source_runtime_digest"],
        "verified": True,
    }


def prefix_artifact_path(ordinal: int) -> Path:
    return PREFIX_DIR / f"seed_{int(ordinal):02d}.pkl.gz"


def _new_discovery_wrapper(seed: int, ecology: Mapping[str, Any]) -> NativeProspectiveAuthorityV2:
    r0 = build_ecology_r0(ecology)
    config = CompetenceEnvelopeConfig(selection_seed=int(seed))
    source = TraceNativeCompetenceOrganism.empty(
        r0,
        envelope_config=config,
        learning_config=TraceNativeLearningConfig(
            lifecycle_connected=False,
            specialization_mode=SpecializationMode.DISCONNECTED,
            genome_seed=int(seed),
            completion_terminal_identity="mate",
            receipt_issuer_identity="native_v2_science_chess_adapter.v1",
            receipt_capability_key=(
                "native-v2-science-grounded-capability.v1:"
                + hashlib.sha256(str(seed).encode("utf-8")).hexdigest()
            ),
        ),
    )
    return NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )


def _prefix_receipts(
    wrapper: NativeProspectiveAuthorityV2,
    ecology: Mapping[str, Any],
    *,
    ordinal: int,
) -> tuple[Any, ...]:
    terminal = wrapper.base.completion_terminal()
    receipts = []
    for row in _rows(ecology, "prefix"):
        board = chess.Board(row.a_fen)
        frame = FrameContext(
            f"canonical-prefix:{ordinal:02d}:{row.row_id}",
            FrameKind.REAL,
            values={"board": board},
        )
        actuation, trace = wrapper.base.r0.emit_action_with_trace(frame)
        if actuation is None or trace is None:
            raise ScientificIntegrityError("prefix graph emitted no action")
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(actuation.move_uci))
        if successor.is_checkmate() is not row.a_outcome:
            raise ScientificIntegrityError("prefix outcome association drift")
        expected = tuple(sorted((*row.active_atom_ids, "internal:policy_response")))
        if trace.ordered_signal_identities != expected:
            raise ScientificIntegrityError("prefix visible signal drift")
        receipts.append(terminal.mint(trace, board, successor))
    return tuple(receipts)


def _target_eligible(
    wrapper: NativeProspectiveAuthorityV2,
    cell_id: str,
) -> bool:
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


def _canonical_hypothesis_digest(wrapper: NativeProspectiveAuthorityV2, cell_id: str) -> str:
    return sha256_json(wrapper.states[cell_id].hypothesis.manifest())


def select_prefix_targets(
    wrapper: NativeProspectiveAuthorityV2,
    ecology: Mapping[str, Any],
) -> dict[str, Any]:
    planted_digest = str(ecology["planted_pattern_digest"])
    spurious_digests = {
        str(item["pattern_digest"]) for item in ecology["spurious_family"]
    }
    candidates = []
    for cell_id in sorted(wrapper.states):
        state = wrapper.states[cell_id]
        pattern_digest = canonical_pattern_digest(state.hypothesis.members)
        candidates.append({
            "cell_id": cell_id,
            "pattern_digest": pattern_digest,
            "hypothesis_digest": _canonical_hypothesis_digest(wrapper, cell_id),
            "eligible": _target_eligible(wrapper, cell_id),
            "members": list(state.hypothesis.members),
        })
    planted = sorted(
        (
            item for item in candidates
            if item["pattern_digest"] == planted_digest and item["eligible"]
        ),
        key=lambda item: (item["hypothesis_digest"], item["cell_id"]),
    )
    spurious = sorted(
        (
            item for item in candidates
            if item["pattern_digest"] in spurious_digests
            and item["pattern_digest"] != planted_digest
            and item["eligible"]
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


def _candidate_population_snapshot(wrapper: NativeProspectiveAuthorityV2) -> dict[str, Any]:
    return {
        "states": {
            cell_id: state.manifest()
            for cell_id, state in sorted(wrapper.states.items())
        },
        "cells": {
            cell_id: wrapper.base.envelope.cells[cell_id].to_manifest()
            for cell_id in sorted(wrapper.states)
        },
        "historical_tombstones": copy.deepcopy(wrapper.historical_tombstones),
        "structural_invariants": {
            cell_id: asdict(value)
            for cell_id, value in sorted(wrapper.structural_invariants.items())
        },
        "authority_topology": copy.deepcopy(wrapper.authority_topology),
        "epoch": wrapper.base.envelope.nomination_epoch.manifest(),
        "source_state_identity": wrapper.base.r0.trace_state_identity(),
    }


def run_discovery_seed(
    seed_row: Mapping[str, Any],
    ecology: Mapping[str, Any],
) -> dict[str, Any]:
    ordinal = int(seed_row["ordinal"])
    seed = int(seed_row["genome_seed"])
    wrapper = _new_discovery_wrapper(seed, ecology)
    receipts = _prefix_receipts(wrapper, ecology, ordinal=ordinal)
    added = wrapper.nominate_prefix_from_grounded_receipts(receipts)
    wrapper.close_nomination()
    targets = select_prefix_targets(wrapper, ecology)
    snapshot = _candidate_population_snapshot(wrapper)
    payload = wrapper.dumps()
    restored = NativeProspectiveAuthorityV2.loads(payload)
    if restored.continuation_manifest() != wrapper.continuation_manifest():
        raise ScientificIntegrityError("prefix serialization parity failure")
    return {
        "ordinal": ordinal,
        "genome_seed": seed,
        "added_cell_ids": list(added),
        "targets": targets,
        "population_snapshot_digest": sha256_json(snapshot),
        "continuation_digest": wrapper.continuation_digest(),
        "experimental_identity_digest": wrapper.experimental_identity[
            "identity_digest"
        ],
        "uncompressed_sha256": hashlib.sha256(payload).hexdigest(),
        "payload": payload,
    }


def _science_worker_prefix(args: tuple[dict[str, Any], dict[str, Any]]) -> list[dict[str, Any]]:
    seed_rows, ecology = args
    results = []
    for row in seed_rows:
        result = run_discovery_seed(row, ecology)
        payload = result.pop("payload")
        compressed = _gzip_bytes(payload)
        output = ROOT / prefix_artifact_path(int(row["ordinal"]))
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            raise FileExistsError(f"prefix artifact already exists: {output}")
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_bytes(compressed)
        temporary.replace(output)
        result["artifact"] = {
            "path": str(prefix_artifact_path(int(row["ordinal"]))),
            "compressed_sha256": hashlib.sha256(compressed).hexdigest(),
            "uncompressed_sha256": hashlib.sha256(payload).hexdigest(),
            "byte_count": len(compressed),
        }
        results.append(result)
    return results


def _partition_seed_rows(rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    partitions = ([], [])
    for row in rows:
        partitions[int(row["ordinal"]) % 2].append(dict(row))
    return partitions


def run_prefix_cohort(*, workers: int = 2) -> dict[str, Any]:
    required_workers = canonical_worker_count()
    if workers != required_workers:
        raise ScientificIntegrityError(
            f"canonical prefix requires {required_workers} worker(s)"
        )
    identity_before = verify_outer_manifest("discovery-prefix execution")
    if (ROOT / PREFIX_MANIFEST_PATH).exists():
        raise FileExistsError("prefix candidate manifest already exists")
    ecology = _load_json(ROOT / ECOLOGY_MANIFEST_PATH)
    seeds = _load_json(ROOT / SEED_MANIFEST_PATH)
    rows = tuple(seeds["rows"])
    for ordinal in range(SEED_COUNT):
        if (ROOT / prefix_artifact_path(ordinal)).exists():
            raise FileExistsError("canonical prefix artifact already exists")
    if workers == 2:
        partitions = _partition_seed_rows(rows)
        context = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=2, mp_context=context) as executor:
            batches = list(executor.map(
                _science_worker_prefix,
                ((partitions[0], ecology), (partitions[1], ecology)),
            ))
        results = [item for batch in batches for item in batch]
    elif workers == 1:
        results = _science_worker_prefix((list(map(dict, rows)), ecology))
    else:
        raise ValueError("canonical prefix supports one or two workers")
    results.sort(key=lambda item: int(item["ordinal"]))
    if [item["ordinal"] for item in results] != list(range(SEED_COUNT)):
        raise ScientificIntegrityError("prefix cohort omitted or duplicated a seed")
    identity_after = verify_outer_manifest("candidate freeze")
    if identity_after["source_runtime_digest"] != identity_before["source_runtime_digest"]:
        raise ScientificIntegrityError("source/runtime identity drifted during prefix")
    manifest = {
        "schema_version": "native_v2_science_prefix_candidates.v1",
        "experiment_id": EXPERIMENT_ID,
        "outer_manifest_sha256": identity_before["outer_manifest_sha256"],
        "source_runtime_digest": identity_before["source_runtime_digest"],
        "seed_manifest_sha256": sha256_file(ROOT / SEED_MANIFEST_PATH),
        "ecology_manifest_sha256": sha256_file(ROOT / ECOLOGY_MANIFEST_PATH),
        "all_32_retained": True,
        "results": results,
        "nomination": {
            "planted_present": sum(item["targets"]["planted"] is not None for item in results),
            "spurious_present": sum(item["targets"]["selected_spurious"] is not None for item in results),
            "both_present": sum(
                item["targets"]["planted"] is not None
                and item["targets"]["selected_spurious"] is not None
                for item in results
            ),
        },
    }
    manifest["prefix_manifest_digest"] = sha256_json(manifest)
    _atomic_json(ROOT / PREFIX_MANIFEST_PATH, manifest)
    return manifest


def load_prefix_wrapper(entry: Mapping[str, Any]) -> NativeProspectiveAuthorityV2:
    artifact = entry["artifact"]
    compressed = (ROOT / artifact["path"]).read_bytes()
    if hashlib.sha256(compressed).hexdigest() != artifact["compressed_sha256"]:
        raise ScientificIntegrityError("prefix artifact compressed hash mismatch")
    payload = gzip.decompress(compressed)
    if hashlib.sha256(payload).hexdigest() != artifact["uncompressed_sha256"]:
        raise ScientificIntegrityError("prefix artifact raw hash mismatch")
    wrapper = NativeProspectiveAuthorityV2.loads(payload)
    if wrapper.continuation_digest() != entry["continuation_digest"]:
        raise ScientificIntegrityError("prefix continuation mismatch")
    if wrapper.experimental_identity["identity_digest"] != entry[
        "experimental_identity_digest"
    ]:
        raise ScientificIntegrityError("prefix experimental identity mismatch")
    return wrapper


def _arm_parity_projection(wrapper: NativeProspectiveAuthorityV2) -> dict[str, Any]:
    epoch = wrapper.base.envelope.nomination_epoch
    if epoch is None or not epoch.nomination_closed:
        raise ScientificIntegrityError("arm nomination is not closed")
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
            key: asdict(value)
            for key, value in sorted(wrapper.structural_invariants.items())
        },
        "historical_tombstones": copy.deepcopy(wrapper.historical_tombstones),
        "frozen_candidate_manifest": list(epoch.frozen_candidate_manifest),
        "frozen_candidate_manifest_digest": epoch.frozen_candidate_manifest_digest,
        "authority_topology": copy.deepcopy(wrapper.authority_topology),
        "candidate_population_identity": wrapper.experimental_identity[
            "candidate_population_identity"
        ],
        "source_organism_identity": wrapper.base.r0.source_organism_identity(),
        "source_state_identity": wrapper.base.r0.trace_state_identity(),
    }


def candidate_identical_arms(
    wrapper: NativeProspectiveAuthorityV2,
) -> dict[str, NativeProspectiveAuthorityV2]:
    prospective, legacy = wrapper.clone_candidate_identical_arms()
    control = copy.deepcopy(prospective)
    prospective.assert_candidate_parity(legacy)
    prospective.assert_candidate_parity(control)
    projections = {
        "A": _arm_parity_projection(prospective),
        "B": _arm_parity_projection(legacy),
        "C": _arm_parity_projection(control),
    }
    if not (projections["A"] == projections["B"] == projections["C"]):
        raise ScientificIntegrityError("candidate-identical arm parity failure")
    if any(state.prospectively_certified for state in prospective.states.values()):
        raise ScientificIntegrityError("prospective A has immediate authority")
    if any(state.prospectively_certified for state in control.states.values()):
        raise ScientificIntegrityError("prospective C has immediate authority")
    for cell_id, state in legacy.states.items():
        lawful = legacy.base.envelope.cells[cell_id].is_mature
        if state.prospectively_certified is not lawful:
            raise ScientificIntegrityError("legacy authority is not lawful same-ledger maturity")
    return {"A": prospective, "B": legacy, "C": control}



def laboratory_package_hashes() -> dict[str, str]:
    """Bind the unchanged V2.1 layer plus the complete outer manifest."""

    hashes = policy_critical_package_hashes(ROOT)
    hashes[OUTER_MANIFEST_KEY] = sha256_file(ROOT / OUTER_MANIFEST_PATH)
    return hashes


def _suffix_frame_id(arm: str, ordinal: int, row_id: str, *, phase: str) -> str:
    return f"v2-science:{phase}:{arm}:seed-{ordinal:02d}:{row_id}"


def _arm_input(row: EcologyRow, arm: str) -> tuple[str, bool]:
    if arm in {"A", "B"}:
        return row.a_fen, row.a_outcome
    if arm == "C":
        return row.c_fen, row.c_outcome
    raise ValueError(f"unknown arm: {arm}")


def _classification_visible_projection(
    wrapper: NativeProspectiveAuthorityV2,
    commitment: Any,
    *,
    planted_cell_id: str | None,
    spurious_cell_id: str | None,
    row_id: str,
) -> dict[str, Any]:
    trace = commitment.trace
    matching = tuple(commitment.matching_cell_ids)
    activation_map = {
        cell_id: cell_id in matching for cell_id in sorted(wrapper.states)
    }
    target_digest = sha256_json({
        "planted": (
            "ABSENT" if planted_cell_id is None
            else wrapper.states[planted_cell_id].hypothesis.manifest()
        ),
        "selected_spurious": (
            "ABSENT" if spurious_cell_id is None
            else wrapper.states[spurious_cell_id].hypothesis.manifest()
        ),
    })
    projection = {
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
        "planted_activation": (
            False if planted_cell_id is None else planted_cell_id in matching
        ),
        "selected_spurious_activation": (
            False if spurious_cell_id is None else spurious_cell_id in matching
        ),
        "logical_opportunity_identity": sha256_json({
            "row_id": row_id,
            "frozen_target_digest": target_digest,
        }),
    }
    projection["projection_digest"] = sha256_json(projection)
    return projection


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


def _build_preoutcome_arm_cohort(
    arm: str,
    prefix_manifest: Mapping[str, Any],
    ecology: Mapping[str, Any],
) -> tuple[
    dict[str, bytes],
    dict[str, NativeProspectiveAuthorityV2],
    dict[str, Sequence[RegisteredV2ExposureRow]],
]:
    payloads: dict[str, bytes] = {}
    wrappers: dict[str, NativeProspectiveAuthorityV2] = {}
    exposure_rows: dict[str, Sequence[RegisteredV2ExposureRow]] = {}
    suffix = _rows(ecology, "suffix")
    for entry in prefix_manifest["results"]:
        ordinal = int(entry["ordinal"])
        organism_id = f"seed-{ordinal:02d}"
        original = load_prefix_wrapper(entry)
        wrapper = candidate_identical_arms(original)[arm]
        payloads[organism_id] = wrapper.dumps()
        wrappers[organism_id] = wrapper
        exposure_rows[organism_id] = tuple(
            RegisteredV2ExposureRow(
                row_id=row.row_id,
                frame_id=_suffix_frame_id(
                    arm, ordinal, row.row_id, phase="exposure"
                ),
                predecessor_fen=_arm_input(row, arm)[0],
            )
            for row in suffix
        )
    return payloads, wrappers, exposure_rows


def _target_counts_from_scan(
    scan: Mapping[str, Any],
    *,
    planted_cell_id: str | None,
    spurious_cell_id: str | None,
) -> dict[str, Any]:
    cells = scan["cells"]
    planted = (
        {"distinct_opportunities": 0, "opportunity_ids": []}
        if planted_cell_id is None else cells[planted_cell_id]
    )
    spurious = (
        {"distinct_opportunities": 0, "opportunity_ids": []}
        if spurious_cell_id is None else cells[spurious_cell_id]
    )
    return {
        "planted": copy.deepcopy(planted),
        "selected_spurious": copy.deepcopy(spurious),
    }


def run_preoutcome_exposure() -> dict[str, Any]:
    identity_before = verify_outer_manifest("suffix exposure")
    if (ROOT / EXPOSURE_PATH).exists():
        raise FileExistsError("preoutcome exposure artifact already exists")
    prefix = _load_json(ROOT / PREFIX_MANIFEST_PATH)
    if prefix.get("prefix_manifest_digest") != sha256_json({
        key: value for key, value in prefix.items()
        if key != "prefix_manifest_digest"
    }):
        raise ScientificIntegrityError("prefix candidate manifest mismatch")
    ecology = _load_json(ROOT / ECOLOGY_MANIFEST_PATH)
    suffix = _rows(ecology, "suffix")
    row_order = tuple(row.row_id for row in suffix)
    package_hashes = laboratory_package_hashes()
    arm_records: dict[str, Any] = {}
    parity_by_seed: dict[int, dict[str, list[dict[str, Any]]]] = {
        index: {} for index in range(SEED_COUNT)
    }

    for arm in ("A", "B", "C"):
        payloads, wrappers, exposure_rows = _build_preoutcome_arm_cohort(
            arm, prefix, ecology
        )
        run_identity = sha256_json({
            "experiment_id": EXPERIMENT_ID,
            "phase": "preoutcome_exposure",
            "arm": arm,
            "outer_manifest": identity_before["outer_manifest_sha256"],
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
            wrapper = wrappers[organism_id]
            entry = prefix["results"][ordinal]
            targets = entry["targets"]
            planted_cell_id = (
                None if targets["planted"] is None
                else str(targets["planted"]["cell_id"])
            )
            spurious_cell_id = (
                None if targets["selected_spurious"] is None
                else str(targets["selected_spurious"]["cell_id"])
            )
            commitments = []
            visible_rows = []
            before = wrapper.continuation_digest()
            for row in suffix:
                fen, _ = _arm_input(row, arm)
                frame = FrameContext(
                    _suffix_frame_id(
                        arm, ordinal, row.row_id, phase="exposure"
                    ),
                    FrameKind.REAL,
                    values={"board": chess.Board(fen)},
                )
                commitment = wrapper.probe_real_exposure(frame)
                commitments.append(commitment)
                visible_rows.append(_classification_visible_projection(
                    wrapper,
                    commitment,
                    planted_cell_id=planted_cell_id,
                    spurious_cell_id=spurious_cell_id,
                    row_id=row.row_id,
                ))
            if wrapper.continuation_digest() != before:
                raise ScientificIntegrityError("exposure mutated live organism")
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
            target_counts = _target_counts_from_scan(
                scan_wrapper["scan"],
                planted_cell_id=planted_cell_id,
                spurious_cell_id=spurious_cell_id,
            )
            parity_by_seed[ordinal][arm] = visible_rows
            per_seed.append({
                "ordinal": ordinal,
                "organism_id": organism_id,
                "payload_sha256": hashlib.sha256(
                    payloads[organism_id]
                ).hexdigest(),
                "continuation_digest": wrapper.continuation_digest(),
                "planted_cell_id": planted_cell_id,
                "selected_spurious_cell_id": spurious_cell_id,
                "target_counts": target_counts,
                "target_qualified": bool(
                    planted_cell_id is not None
                    and spurious_cell_id is not None
                    and target_counts["planted"]["distinct_opportunities"]
                    >= MIN_TARGET_OPPORTUNITIES
                    and target_counts["selected_spurious"][
                        "distinct_opportunities"
                    ] >= MIN_TARGET_OPPORTUNITIES
                ),
                "scan_wrapper_digest": sha256_json(scan_wrapper),
                "scan_digest": scan_wrapper["scan_digest"],
                "visible_row_projection_digests": [
                    row["projection_digest"] for row in visible_rows
                ],
                "physical_fingerprints": [
                    item.interaction_fingerprint for item in commitments
                ],
            })
        adjudication = registry.adjudicate_cohort(
            scan_wrappers,
            tape_identity=registry.tape_identity,
            row_order=row_order,
            run_identity=run_identity,
            package_hashes=package_hashes,
        )
        arm_records[arm] = {
            "registry": _registry_manifest(registry),
            "registry_adjudication": adjudication,
            "per_seed": per_seed,
            "complete_scan_wrapper_set_digest": sha256_json(scan_wrappers),
        }

    parity_failures = []
    parity_rows = []
    for ordinal in range(SEED_COUNT):
        for row_index, row in enumerate(suffix):
            projections = {
                arm: parity_by_seed[ordinal][arm][row_index]
                for arm in ("A", "B", "C")
            }
            comparable = {
                arm: {
                    key: value for key, value in projection.items()
                    if key != "projection_digest"
                }
                for arm, projection in projections.items()
            }
            equal = comparable["A"] == comparable["B"] == comparable["C"]
            row_record = {
                "ordinal": ordinal,
                "row_id": row.row_id,
                "equal": equal,
                "A_digest": projections["A"]["projection_digest"],
                "B_digest": projections["B"]["projection_digest"],
                "C_digest": projections["C"]["projection_digest"],
                "logical_opportunity_identity": projections["A"][
                    "logical_opportunity_identity"
                ],
            }
            parity_rows.append(row_record)
            if not equal:
                parity_failures.append({
                    **row_record,
                    "projections": projections,
                })
    if parity_failures:
        stop_reason = "control_exposure_parity_failure"
        qualifying_count = 0
    else:
        qualifying_ordinals = []
        for ordinal in range(SEED_COUNT):
            if all(
                arm_records[arm]["per_seed"][ordinal]["target_qualified"]
                for arm in ("A", "B", "C")
            ):
                qualifying_ordinals.append(ordinal)
        qualifying_count = len(qualifying_ordinals)
        stop_reason = (
            None if qualifying_count >= MIN_QUALIFYING_SEEDS
            else "targeted_prospective_evidence_starvation"
        )
    identity_after = verify_outer_manifest("preoutcome adjudication")
    result = {
        "schema_version": "native_v2_science_preoutcome.v1",
        "experiment_id": EXPERIMENT_ID,
        "identity_before": identity_before,
        "identity_after": identity_after,
        "row_count_per_arm": len(suffix),
        "all_32_retained": True,
        "registry_package_hashes": dict(package_hashes),
        "arms": arm_records,
        "row_parity": {
            "required": True,
            "passed": not parity_failures,
            "failure_count": len(parity_failures),
            "rows": parity_rows,
            "failures": parity_failures,
        },
        "targeted_exposure": {
            "qualifying_count": qualifying_count,
            "required": MIN_QUALIFYING_SEEDS,
            "admitted": stop_reason is None,
        },
        "suffix_outcomes_opened": False,
        "stop_reason": stop_reason,
    }
    result["preoutcome_digest"] = sha256_json(result)
    _atomic_json(ROOT / EXPOSURE_PATH, result)
    return result



def _target_id(targets: Mapping[str, Any], name: str) -> str | None:
    item = targets[name]
    return None if item is None else str(item["cell_id"])


def _execute_suffix_arm(
    wrapper: NativeProspectiveAuthorityV2,
    *,
    arm: str,
    ordinal: int,
    ecology: Mapping[str, Any],
    targets: Mapping[str, Any],
) -> dict[str, Any]:
    suffix = _rows(ecology, "suffix")
    planted_id = _target_id(targets, "planted")
    spurious_id = _target_id(targets, "selected_spurious")
    start_digest = wrapper.continuation_digest()
    start_states = {
        cell_id: state.manifest()
        for cell_id, state in sorted(wrapper.states.items())
    }
    immediate_authority = sorted(
        cell_id for cell_id, state in wrapper.states.items()
        if state.prospectively_certified
    )
    false_authority = 0
    spurious_false_authority = 0
    planted_coverage = 0
    rows = []
    for row in suffix:
        fen, frozen_outcome = _arm_input(row, arm)
        predecessor = chess.Board(fen)
        frame = FrameContext(
            _suffix_frame_id(
                arm, ordinal, row.row_id, phase="canonical"
            ),
            FrameKind.REAL,
            values={"board": predecessor},
        )
        pending, trace = wrapper.open_real_event(frame)
        classification = pending.pre_outcome_classification
        production_available = bool(
            classification.state is AvailabilityState.AVAILABLE
            and classification.formal_available
        )
        selected_move = chess.Move.from_uci(
            pending.actuation.move_uci
        )
        if selected_move not in predecessor.legal_moves:
            raise ScientificIntegrityError("graph emitted illegal suffix action")
        successor = predecessor.copy(stack=False)
        successor.push(selected_move)
        actual_outcome = successor.is_checkmate()
        if actual_outcome is not frozen_outcome:
            raise ScientificIntegrityError(
                "truthful suffix outcome differs from frozen ecology"
            )
        planted_active = bool(
            planted_id is not None and planted_id in pending.matching_cell_ids
        )
        spurious_active = bool(
            spurious_id is not None and spurious_id in pending.matching_cell_ids
        )
        if production_available and not actual_outcome:
            false_authority += 1
        if (
            spurious_id is not None
            and spurious_id in classification.available_cell_ids
            and not actual_outcome
        ):
            spurious_false_authority += 1
        if (
            row.visible_family == "suffix_planted"
            and planted_id is not None
            and planted_id in classification.available_cell_ids
        ):
            planted_coverage += 1
        receipt = wrapper.mint_environment_receipt(
            pending_token=pending.pending_token,
            trace=trace,
            predecessor=predecessor,
            successor=successor,
        )
        if receipt.observed_outcome is not actual_outcome:
            raise ScientificIntegrityError("receipt fabricated an outcome")
        emission = wrapper.consume(receipt)
        rows.append({
            "row_id": row.row_id,
            "visible_family": row.visible_family,
            "frame_id": frame.frame_id,
            "pre_outcome_continuation_digest": start_digest if not rows else rows[-1][
                "post_outcome_continuation_digest"
            ],
            "pending": pending.manifest(),
            "trace": trace.canonical_manifest(),
            "production_graph_authority": classification.to_manifest(),
            "production_deployable_available": production_available,
            "planted_active": planted_active,
            "selected_spurious_active": spurious_active,
            "actual_successor_fen": successor.fen(),
            "actual_checkmate": actual_outcome,
            "receipt": receipt.manifest(),
            "emission": emission.manifest(),
            "post_outcome_continuation_digest": wrapper.continuation_digest(),
        })
    final_states = {
        cell_id: state.manifest()
        for cell_id, state in sorted(wrapper.states.items())
    }
    final_payload = wrapper.dumps()
    return {
        "arm": arm,
        "start_continuation_digest": start_digest,
        "start_states": start_states,
        "immediate_authority_cell_ids": immediate_authority,
        "events": rows,
        "endpoints": {
            "false_deployment_authority": false_authority,
            "selected_spurious_attributable_false_authority": (
                spurious_false_authority
            ),
            "planted_authority_coverage": planted_coverage,
        },
        "target_final_states": {
            "planted": (
                None if planted_id is None else final_states[planted_id]
            ),
            "selected_spurious": (
                None if spurious_id is None else final_states[spurious_id]
            ),
        },
        "final_continuation_digest": wrapper.continuation_digest(),
        "final_serialized_sha256": hashlib.sha256(final_payload).hexdigest(),
        "final_state_manifest_digest": sha256_json(
            wrapper.continuation_manifest()
        ),
    }


def _run_canonical_suffix_seed(
    args: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
) -> dict[str, Any]:
    entry, ecology, expected = args
    ordinal = int(entry["ordinal"])
    original = load_prefix_wrapper(entry)
    arms = candidate_identical_arms(original)
    results = {}
    for arm in ("A", "B", "C"):
        payload = arms[arm].dumps()
        expected_sha = expected[arm][ordinal]
        observed_sha = hashlib.sha256(payload).hexdigest()
        if observed_sha != expected_sha:
            raise ScientificIntegrityError(
                f"preoutcome arm bytes changed before suffix:{ordinal}:{arm}"
            )
        results[arm] = _execute_suffix_arm(
            arms[arm],
            arm=arm,
            ordinal=ordinal,
            ecology=ecology,
            targets=entry["targets"],
        )
    return {
        "ordinal": ordinal,
        "genome_seed": int(entry["genome_seed"]),
        "qualifying_targets_present": bool(
            entry["targets"]["planted"] is not None
            and entry["targets"]["selected_spurious"] is not None
        ),
        "targets": copy.deepcopy(entry["targets"]),
        "arms": results,
    }


def _science_worker_suffix(
    args: tuple[
        list[dict[str, Any]], dict[str, Any], dict[str, dict[int, str]]
    ],
) -> list[dict[str, Any]]:
    entries, ecology, expected = args
    return [
        _run_canonical_suffix_seed((entry, ecology, expected))
        for entry in entries
    ]


def exact_one_sided_sign_test(values: Sequence[int | float]) -> dict[str, Any]:
    wins = sum(value > 0 for value in values)
    losses = sum(value < 0 for value in values)
    ties = len(values) - wins - losses
    n = wins + losses
    p = (
        1.0 if n == 0 else
        sum(math.comb(n, k) for k in range(wins, n + 1)) / (2 ** n)
    )
    return {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "non_tied_effective_n": n,
        "one_sided_exact_p": p,
    }


def holm_adjust_two(raw: Mapping[str, float]) -> dict[str, float]:
    if set(raw) != {"D_safe", "D_signal"}:
        raise ValueError("Holm family is frozen to exactly two primary tests")
    ordered = sorted(raw, key=lambda key: (raw[key], key))
    first, second = ordered
    adjusted_first = min(1.0, 2.0 * raw[first])
    adjusted_second = min(1.0, max(adjusted_first, raw[second]))
    return {first: adjusted_first, second: adjusted_second}


def _percentile(values: Sequence[float], q: float) -> float:
    ordered = sorted(float(item) for item in values)
    if not ordered:
        return float("nan")
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def paired_bootstrap(values: Sequence[int], *, label: str) -> dict[str, Any]:
    if len(values) != SEED_COUNT:
        raise ValueError("paired bootstrap requires all 32 seeds")
    seed = derive_seed(
        sha256_file(ROOT / OUTER_MANIFEST_PATH),
        0,
        namespace=f"bootstrap:{label}",
    )
    rng = random.Random(seed)
    means = []
    medians = []
    source = list(map(float, values))
    for _ in range(BOOTSTRAP_REPLICATES):
        sample = [source[rng.randrange(SEED_COUNT)] for _ in range(SEED_COUNT)]
        means.append(math.fsum(sample) / SEED_COUNT)
        ordered = sorted(sample)
        medians.append((ordered[15] + ordered[16]) / 2.0)
    ordered_source = sorted(source)
    return {
        "replicates": BOOTSTRAP_REPLICATES,
        "seed": seed,
        "mean": math.fsum(source) / SEED_COUNT,
        "median": (ordered_source[15] + ordered_source[16]) / 2.0,
        "mean_ci_95": [_percentile(means, 0.025), _percentile(means, 0.975)],
        "median_ci_95": [
            _percentile(medians, 0.025), _percentile(medians, 0.975)
        ],
        "descriptive_only": True,
    }


def _engagement_for_seed(seed_result: Mapping[str, Any]) -> dict[str, Any]:
    arms = seed_result["arms"]
    a_planted = arms["A"]["target_final_states"]["planted"]
    a_spurious = arms["A"]["target_final_states"]["selected_spurious"]
    c_planted = arms["C"]["target_final_states"]["planted"]
    a_immediate = bool(arms["A"]["immediate_authority_cell_ids"])
    c_immediate = bool(arms["C"]["immediate_authority_cell_ids"])
    b_start = arms["B"]["start_states"]
    b_immediate = set(arms["B"]["immediate_authority_cell_ids"])
    b_lawful = all(
        (cell_id in b_immediate) is bool(
            state["hypothesis"]["structural_state"] == StemCellState.MATURE.name
        )
        for cell_id, state in b_start.items()
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
    c_broke_planted = bool(
        c_planted is not None
        and c_planted["contradictions"] >= MIN_TARGET_OPPORTUNITIES
    )
    return {
        "zero_immediate_A": not a_immediate,
        "zero_immediate_C": not c_immediate,
        "lawful_legacy_B": b_lawful,
        "planted_A_later_certified": planted_engaged,
        "spurious_A_later_contradicted": spurious_contradicted,
        "C_broke_planted_association": c_broke_planted,
        "engaged": bool(
            not a_immediate and not c_immediate and b_lawful
            and planted_engaged and spurious_contradicted and c_broke_planted
        ),
    }


def adjudicate_suffix_results(
    seed_results: Sequence[Mapping[str, Any]],
    preoutcome: Mapping[str, Any],
) -> dict[str, Any]:
    ordered = sorted(seed_results, key=lambda item: int(item["ordinal"]))
    if [item["ordinal"] for item in ordered] != list(range(SEED_COUNT)):
        raise ScientificIntegrityError("suffix omitted, duplicated, or reordered a seed")
    d_safe = []
    d_signal = []
    per_seed = []
    for result in ordered:
        arms = result["arms"]
        safe = (
            arms["B"]["endpoints"]["false_deployment_authority"]
            - arms["A"]["endpoints"]["false_deployment_authority"]
        )
        signal = (
            arms["A"]["endpoints"]["planted_authority_coverage"]
            - arms["C"]["endpoints"]["planted_authority_coverage"]
        )
        d_safe.append(safe)
        d_signal.append(signal)
        engagement = _engagement_for_seed(result)
        per_seed.append({
            "ordinal": result["ordinal"],
            "genome_seed": result["genome_seed"],
            "D_safe": safe,
            "D_signal": signal,
            "engagement": engagement,
            "endpoints": {
                arm: copy.deepcopy(arms[arm]["endpoints"])
                for arm in ("A", "B", "C")
            },
        })
    engagement_count = sum(row["engagement"]["engaged"] for row in per_seed)
    planted_count = sum(
        row["engagement"]["planted_A_later_certified"] for row in per_seed
    )
    spurious_count = sum(
        row["engagement"]["spurious_A_later_contradicted"] for row in per_seed
    )
    mechanism_engaged = bool(
        planted_count >= MIN_QUALIFYING_SEEDS
        and spurious_count >= MIN_QUALIFYING_SEEDS
        and all(row["engagement"]["zero_immediate_A"] for row in per_seed)
        and all(row["engagement"]["zero_immediate_C"] for row in per_seed)
        and all(row["engagement"]["lawful_legacy_B"] for row in per_seed)
    )
    tests = {
        "D_safe": exact_one_sided_sign_test(d_safe),
        "D_signal": exact_one_sided_sign_test(d_signal),
    }
    adjusted = holm_adjust_two({
        key: value["one_sided_exact_p"] for key, value in tests.items()
    })
    for name, values in (("D_safe", d_safe), ("D_signal", d_signal)):
        tests[name]["holm_adjusted_p"] = adjusted[name]
        tests[name]["favorable_all_32"] = sum(value > 0 for value in values)
        tests[name]["paired_values"] = list(values)
        tests[name]["descriptive_effect"] = paired_bootstrap(values, label=name)
        tests[name]["passed"] = bool(
            adjusted[name] <= PRIMARY_ALPHA
            and sum(value > 0 for value in values) >= MIN_FAVORABLE_SEEDS
        )
    primary_pass = bool(
        mechanism_engaged and all(item["passed"] for item in tests.values())
    )
    if not mechanism_engaged:
        verdict = "mechanism_contrast_starvation"
    elif primary_pass:
        verdict = "prospective_evidence_separation_supported_in_frozen_ecology"
    else:
        verdict = "valid_negative_prospective_separation_not_supported"
    pooled = {
        arm: {
            metric: sum(
                result["arms"][arm]["endpoints"][metric]
                for result in ordered
            )
            for metric in (
                "false_deployment_authority",
                "selected_spurious_attributable_false_authority",
                "planted_authority_coverage",
            )
        }
        for arm in ("A", "B", "C")
    }
    return {
        "inferential_unit": "genome_seed",
        "all_32_retained": True,
        "qualified_only_inference": False,
        "engagement": {
            "planted_A_certified_count": planted_count,
            "spurious_A_contradicted_count": spurious_count,
            "fully_engaged_count": engagement_count,
            "required": MIN_QUALIFYING_SEEDS,
            "passed": mechanism_engaged,
        },
        "primary_tests": tests,
        "both_primary_pass": primary_pass,
        "per_seed": per_seed,
        "pooled_descriptive_totals": pooled,
        "verdict": verdict,
        "causal_interpretation_authorized": mechanism_engaged,
        "preoutcome_admission_digest": preoutcome["preoutcome_digest"],
    }


def run_canonical_suffix(*, workers: int = 2) -> dict[str, Any]:
    required_workers = canonical_worker_count()
    if workers != required_workers:
        raise ScientificIntegrityError(
            f"canonical suffix requires {required_workers} worker(s)"
        )
    identity_before = verify_outer_manifest("canonical suffix consumption")
    preoutcome = _load_json(ROOT / EXPOSURE_PATH)
    if preoutcome.get("preoutcome_digest") != sha256_json({
        key: value for key, value in preoutcome.items()
        if key != "preoutcome_digest"
    }):
        raise ScientificIntegrityError("preoutcome artifact digest mismatch")
    if preoutcome.get("stop_reason") is not None:
        raise ScientificIntegrityError(
            "suffix forbidden after preoutcome stop:" + str(
                preoutcome["stop_reason"]
            )
        )
    if preoutcome.get("suffix_outcomes_opened") is not False:
        raise ScientificIntegrityError("suffix preoutcome phase is not pristine")
    if (ROOT / RESULT_PATH).exists():
        raise FileExistsError("canonical result already exists")
    prefix = _load_json(ROOT / PREFIX_MANIFEST_PATH)
    ecology = _load_json(ROOT / ECOLOGY_MANIFEST_PATH)
    expected = {
        arm: {
            int(item["ordinal"]): str(item["payload_sha256"])
            for item in preoutcome["arms"][arm]["per_seed"]
        }
        for arm in ("A", "B", "C")
    }
    entries = list(map(dict, prefix["results"]))
    if workers == 2:
        partitions = _partition_seed_rows(entries)
        context = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=2, mp_context=context) as executor:
            batches = list(executor.map(
                _science_worker_suffix,
                (
                    (partitions[0], ecology, expected),
                    (partitions[1], ecology, expected),
                ),
            ))
        seed_results = [item for batch in batches for item in batch]
    elif workers == 1:
        seed_results = _science_worker_suffix((entries, ecology, expected))
    else:
        raise ValueError("canonical suffix supports one or two workers")
    seed_results.sort(key=lambda item: int(item["ordinal"]))
    adjudication = adjudicate_suffix_results(seed_results, preoutcome)
    identity_after = verify_outer_manifest("canonical suffix closure")
    result = {
        "schema_version": "native_v2_science_canonical_result.v1",
        "experiment_id": EXPERIMENT_ID,
        "identity_before": identity_before,
        "identity_after": identity_after,
        "protected_v2_1_test_certificate": {
            "test_count": 1013,
            "carried_forward": True,
            "basis": "all protected hashes and complete outer runtime source unchanged",
        },
        "preoutcome": {
            "path": str(EXPOSURE_PATH),
            "sha256": sha256_file(ROOT / EXPOSURE_PATH),
            "digest": preoutcome["preoutcome_digest"],
            "targeted_exposure": preoutcome["targeted_exposure"],
            "row_parity": {
                "passed": preoutcome["row_parity"]["passed"],
                "failure_count": preoutcome["row_parity"]["failure_count"],
            },
        },
        "seed_results": seed_results,
        "adjudication": adjudication,
        "limitations": [
            "synthetic mechanism test conditional on one frozen ecology",
            "not KRK generalization evidence",
            "not R1 evidence",
            "not evidence for arbitrary environments",
        ],
    }
    result["canonical_result_digest"] = sha256_json(result)
    payload = _canonical_bytes(result)
    compressed = _gzip_bytes(payload)
    target = ROOT / RESULT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(compressed)
    temporary.replace(target)
    return {
        "path": str(RESULT_PATH),
        "compressed_sha256": hashlib.sha256(compressed).hexdigest(),
        "uncompressed_sha256": hashlib.sha256(payload).hexdigest(),
        "compressed_bytes": len(compressed),
        "canonical_result_digest": result["canonical_result_digest"],
        "verdict": adjudication["verdict"],
        "primary": adjudication["primary_tests"],
    }



def _run_toy_seed(seed_row: Mapping[str, Any], ecology: Mapping[str, Any]) -> dict[str, Any]:
    discovery = run_discovery_seed(seed_row, ecology)
    wrapper = NativeProspectiveAuthorityV2.loads(discovery["payload"])
    arms = candidate_identical_arms(wrapper)
    arm_results = {}
    for arm in ("A", "B", "C"):
        result = _execute_suffix_arm(
            arms[arm],
            arm=arm,
            ordinal=int(seed_row["ordinal"]),
            ecology=ecology,
            targets=discovery["targets"],
        )
        arm_results[arm] = {
            "start_continuation_digest": result["start_continuation_digest"],
            "endpoints": result["endpoints"],
            "target_final_states": result["target_final_states"],
            "final_continuation_digest": result["final_continuation_digest"],
            "final_serialized_sha256": result["final_serialized_sha256"],
            "event_digest": sha256_json(result["events"]),
        }
    scientific = {
        "ordinal": int(seed_row["ordinal"]),
        "genome_seed": int(seed_row["genome_seed"]),
        "targets": discovery["targets"],
        "prefix_continuation_digest": discovery["continuation_digest"],
        "prefix_payload_sha256": discovery["uncompressed_sha256"],
        "arms": arm_results,
    }
    scientific["scientific_payload_digest"] = sha256_json(scientific)
    return scientific


def _toy_worker(
    args: tuple[list[dict[str, Any]], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows, ecology = args
    return [_run_toy_seed(row, ecology) for row in rows]


def run_retired_toy_parity(*, toy_seed_count: int = 2) -> dict[str, Any]:
    if not 1 <= toy_seed_count <= 4:
        raise ValueError("retired toy cohort is permanently capped at four seeds")
    if (ROOT / TOY_PARITY_PATH).exists():
        raise FileExistsError("retired toy parity artifact already exists")
    require_deterministic_environment()
    verify_protected_boundary()
    ecology = generate_ecology_manifest()
    rows = [
        {
            "ordinal": ordinal,
            "genome_seed": derive_seed(
                BASELINE_COMMIT, ordinal, namespace="permanently-retired-toy"
            ),
        }
        for ordinal in range(toy_seed_count)
    ]
    serial = _toy_worker((list(map(dict, rows)), ecology))
    partitions = ([], [])
    for row in rows:
        partitions[int(row["ordinal"]) % 2].append(dict(row))
    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=2, mp_context=context) as executor:
        batches = list(executor.map(
            _toy_worker,
            ((partitions[0], ecology), (partitions[1], ecology)),
        ))
    parallel = [item for batch in batches for item in batch]
    parallel.sort(key=lambda item: int(item["ordinal"]))
    serial_bytes = _canonical_bytes(serial)
    parallel_bytes = _canonical_bytes(parallel)
    result = {
        "schema_version": "native_v2_science_retired_toy_parity.v1",
        "experiment_id": EXPERIMENT_ID,
        "permanently_retired": True,
        "toy_seed_count": toy_seed_count,
        "toy_seed_cap": 4,
        "seeds": rows,
        "serial_payload_sha256": hashlib.sha256(serial_bytes).hexdigest(),
        "two_process_payload_sha256": hashlib.sha256(parallel_bytes).hexdigest(),
        "byte_identical": serial_bytes == parallel_bytes,
        "per_seed": [
            {
                "ordinal": left["ordinal"],
                "serial_digest": left["scientific_payload_digest"],
                "parallel_digest": right["scientific_payload_digest"],
                "equal": left == right,
            }
            for left, right in zip(serial, parallel, strict=True)
        ],
        "serial_scientific_payloads": serial,
    }
    if not result["byte_identical"] or not all(
        row["equal"] for row in result["per_seed"]
    ):
        result["canonical_process_policy"] = "serial"
        result["passed"] = False
    else:
        result["canonical_process_policy"] = "two_process_spawn"
        result["passed"] = True
    result["toy_parity_digest"] = sha256_json(result)
    _atomic_json(ROOT / TOY_PARITY_PATH, result)
    if not result["passed"]:
        raise ScientificIntegrityError("retired toy serial/two-process parity failed")
    return result


def _print_summary(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    toy = commands.add_parser("toy-parity")
    toy.add_argument("--seeds", type=int, default=2)
    freeze = commands.add_parser("freeze-design")
    freeze.add_argument("--pre-science-commit", required=True)
    prefix = commands.add_parser("run-prefix")
    prefix.add_argument("--workers", type=int, choices=(1, 2), default=2)
    commands.add_parser("run-exposure")
    suffix = commands.add_parser("run-suffix")
    suffix.add_argument("--workers", type=int, choices=(1, 2), default=2)
    args = parser.parse_args(argv)
    if args.command == "toy-parity":
        result = run_retired_toy_parity(toy_seed_count=args.seeds)
    elif args.command == "freeze-design":
        result = freeze_design(args.pre_science_commit)
    elif args.command == "run-prefix":
        result = run_prefix_cohort(workers=args.workers)
    elif args.command == "run-exposure":
        result = run_preoutcome_exposure()
    elif args.command == "run-suffix":
        result = run_canonical_suffix(workers=args.workers)
    else:  # pragma: no cover
        raise AssertionError(args.command)
    _print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
