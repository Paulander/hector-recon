"""Development-only benchmark for incremental REAL-history validation.

This module is deliberately additive.  It never opens the frozen deferred-
specialization experiment or any validation, regression, retired-successor,
or R1 artifact.  Its synthetic stream carries a fourth piece (a black knight),
which makes every board and D4 orbit materially disjoint from the protected
three-piece KRK corpora.

The output is descriptive software-performance evidence only.  It is not a
scientific ReCoN result and must never be used for model selection.

Phase 1 is deliberately staged.  Events 1--32 form the exhaustive per-event
legacy/incremental gate.  Later work is incremental-only and advances solely
through explicit 64/128/256 checkpoints, where accepted history is fully
reconstructed.  Each stage is bounded and atomically preserves continuation.
"""
from __future__ import annotations

import argparse
import base64
import copy
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import resource
import signal
import statistics
import subprocess
import sys
import time
from typing import Any, Iterator, Mapping, Sequence
import uuid

import chess

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.learning import (
    IntrinsicCreditConfig,
    IntrinsicCreditEngine,
)
from recon_lite_hector.nodes import StemCellState

from .foundation_curriculum import _generate_mate_in_one_positions
from .native_authority_handover import (
    FrozenCompetenceProvenance,
    NativeR0Organism,
)
from .native_competence_envelope import (
    AvailabilityState,
    CompetenceEnvelopeConfig,
    DormantOrigin,
    MixedOutcomeDisposition,
    SpecializationMode,
)
from . import native_deferred_specialization_fresh_discriminator as science
from . import native_deferred_specialization_performance_reclosure as cache_api
from . import native_prospective_evidence_authority_v2 as v2
from .native_intrinsic_curriculum import R0_COMPETENCE_ID
from .native_prospective_evidence_authority_v2 import (
    HISTORY_VALIDATION_INCREMENTAL,
    HISTORY_VALIDATION_LEGACY,
    NativeProspectiveAuthorityV2,
    V2Mode,
)
from .native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
)
from .native_trace_competence_authority import (
    TraceNativeCompetenceOrganism,
    TraceNativeLearningConfig,
)
from .positions import generate_krk_board


DEVELOPMENT_LABEL = "DEVELOPMENT_VIEWED_NOT_SCIENTIFIC"
SCHEMA_VERSION = "native_incremental_history_development_benchmark.v2"
SEED_RESULT_SCHEMA = (
    "native_incremental_history_development_benchmark.seed_result.v2"
)
SOURCE_COMMIT = "b6848ef4e3eb27d022ac6c67f3c903c962907737"
DOMAIN_KEY = (
    f"{DEVELOPMENT_LABEL}|{SOURCE_COMMIT}|"
    "incremental-history-bounded-v2"
)
DOMAIN_SHA256 = hashlib.sha256(DOMAIN_KEY.encode("utf-8")).hexdigest()
CONSTRUCTION_SEED = int(DOMAIN_SHA256[:16], 16)
assert CONSTRUCTION_SEED == 16591302007524402855

REGION_COUNTS = {
    "parent_discovery": 64,
    "parent_prospective_support_and_contradiction": 5,
    "child_prospective_certification": 251,
    "sealed_evaluation": 64,
}
STRUCTURAL_FRONTIER = 69
CHECKPOINTS = (32, 64, 128, 256)
EXHAUSTIVE_PARITY_GATE_EVENTS = CHECKPOINTS[0]
PHASE1_STRATEGIES = ("incremental", "legacy_full_replay")
PHASE1_CHECKPOINT_SCHEMA = (
    "native_incremental_history_development_benchmark.phase1_checkpoint.v2"
)
DEFAULT_PHASE1_WALL_CEILING_SECONDS = 2.0 * 60.0 * 60.0
DEFAULT_PHASE1_PEAK_RSS_CEILING_MIB = 8.0 * 1024.0
ARMS = science.ARMS
MAX_WORKERS = 4
DEFAULT_OUTPUT_DIR = Path(
    "reports/autogrowth/development/"
    "native_incremental_history_benchmark_v2"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
ALLOWED_OUTPUT_ROOT = (
    REPOSITORY_ROOT / "reports" / "autogrowth" / "development"
)
DEPENDENCY_PATHS = (
    Path("src/recon_lite_chess/autogrowth/foundation_curriculum.py"),
    Path("src/recon_lite_chess/autogrowth/positions.py"),
    Path(
        "src/recon_lite_chess/autogrowth/"
        "native_deferred_specialization_fresh_discriminator.py"
    ),
    Path(
        "src/recon_lite_chess/autogrowth/"
        "native_deferred_specialization_performance_reclosure.py"
    ),
    Path(
        "src/recon_lite_chess/autogrowth/"
        "native_prospective_evidence_authority_v2.py"
    ),
    Path(
        "src/recon_lite_chess/autogrowth/"
        "native_single_graph_curriculum.py"
    ),
    Path(
        "src/recon_lite_chess/autogrowth/"
        "native_trace_competence_authority.py"
    ),
    Path(
        "src/recon_lite_chess/autogrowth/"
        "native_competence_envelope.py"
    ),
    Path(
        "src/recon_lite_chess/autogrowth/native_authority_handover.py"
    ),
    Path(
        "src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py"
    ),
)


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _sha_json(value: Any) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True, cwd=REPOSITORY_ROOT
    ).strip()


def _guard_output_dir(output_dir: Path) -> Path:
    resolved = output_dir.resolve()
    allowed = ALLOWED_OUTPUT_ROOT.resolve()
    if not resolved.is_relative_to(allowed) or resolved == allowed:
        raise RuntimeError(
            "benchmark output must be a named directory below "
            f"{allowed}"
        )
    return resolved


def _dependency_hashes() -> dict[str, str]:
    result = {}
    for relative in DEPENDENCY_PATHS:
        path = REPOSITORY_ROOT / relative
        result[str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _verify_tracked_dependencies_clean() -> None:
    for cached in (False, True):
        command = ["git", "diff"]
        if cached:
            command.append("--cached")
        command.append("--quiet")
        result = subprocess.run(command, cwd=REPOSITORY_ROOT, check=False)
        if result.returncode == 1:
            raise RuntimeError("tracked benchmark dependency has local changes")
        if result.returncode not in {0, 1}:
            raise RuntimeError("could not verify tracked dependency cleanliness")


def _verify_audited_source_revision() -> str:
    """Bind core dependencies to SOURCE_COMMIT without self-referential Git.

    The benchmark module may be committed after the audited core commit.  Its
    own byte hash is included in input_identity; every tracked core dependency
    must remain byte-identical to SOURCE_COMMIT.
    """

    head = _git_head()
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", SOURCE_COMMIT, head],
        cwd=REPOSITORY_ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        raise RuntimeError(
            f"audited core commit {SOURCE_COMMIT} is not an ancestor of {head}"
        )
    unchanged = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            SOURCE_COMMIT,
            head,
            "--",
            *(str(path) for path in DEPENDENCY_PATHS),
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
    )
    if unchanged.returncode == 1:
        raise RuntimeError(
            "tracked benchmark dependencies differ from audited core commit "
            f"{SOURCE_COMMIT}"
        )
    if unchanged.returncode != 0:
        raise RuntimeError("could not verify audited source revision")
    return head


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(
        f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.partial"
    )
    with partial.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(partial, path)


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _atomic_write_bytes(path, _json_bytes(payload) + b"\n")


def _self_digest(payload: Mapping[str, Any]) -> dict[str, Any]:
    unsigned = dict(payload)
    unsigned.pop("payload_digest", None)
    return {**unsigned, "payload_digest": _sha_json(unsigned)}


def _load_self_digested(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = payload.pop("payload_digest", None)
    if not isinstance(expected, str) or _sha_json(payload) != expected:
        raise RuntimeError(f"self-digest mismatch: {path}")
    return {**payload, "payload_digest": expected}


class Phase1CeilingExceeded(RuntimeError):
    """Raised when a bounded Phase-1 invocation reaches a declared ceiling."""


@dataclass(frozen=True)
class _Phase1Budget:
    wall_started: float
    max_wall_seconds: float
    max_peak_rss_mib: float

    def check(self, operation: str) -> None:
        elapsed = time.perf_counter() - self.wall_started
        if elapsed >= self.max_wall_seconds:
            raise Phase1CeilingExceeded(
                "Phase 1 wall ceiling crossed at safe boundary "
                f"{operation}: {elapsed:.3f}s >= "
                f"{self.max_wall_seconds:.3f}s"
            )
        peak_rss_mib, basis = _rss_mib()
        if peak_rss_mib >= self.max_peak_rss_mib:
            raise Phase1CeilingExceeded(
                "Phase 1 peak-RSS ceiling crossed at safe boundary "
                f"{operation}: {peak_rss_mib:.3f} MiB >= "
                f"{self.max_peak_rss_mib:.3f} MiB ({basis})"
            )


@contextmanager
def _phase1_wall_budget(
    *, max_wall_seconds: float, max_peak_rss_mib: float
) -> Iterator[_Phase1Budget]:
    """Enforce a real-time alarm and safe-boundary peak-RSS checks.

    The alarm can interrupt an in-flight Python operation.  The caller never
    persists mutable in-memory state after such an interruption, so only the
    preceding atomic checkpoint remains resumable.
    """

    if not math.isfinite(max_wall_seconds) or max_wall_seconds <= 0.0:
        raise ValueError("Phase 1 wall ceiling must be finite and positive")
    if not math.isfinite(max_peak_rss_mib) or max_peak_rss_mib <= 0.0:
        raise ValueError("Phase 1 peak-RSS ceiling must be finite and positive")
    wall_started = time.perf_counter()
    budget = _Phase1Budget(
        wall_started=wall_started,
        max_wall_seconds=max_wall_seconds,
        max_peak_rss_mib=max_peak_rss_mib,
    )

    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_delay, previous_interval = signal.setitimer(
        signal.ITIMER_REAL, 0.0
    )

    def _expired(_signum: int, _frame: Any) -> None:
        raise Phase1CeilingExceeded(
            "Phase 1 hard wall ceiling crossed inside an operation: "
            f"{max_wall_seconds:.3f}s"
        )

    signal.signal(signal.SIGALRM, _expired)
    signal.setitimer(signal.ITIMER_REAL, max_wall_seconds)
    try:
        budget.check("invocation-start")
        yield budget
        budget.check("invocation-finish")
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_delay > 0.0:
            elapsed = time.perf_counter() - wall_started
            signal.setitimer(
                signal.ITIMER_REAL,
                max(1e-9, previous_delay - elapsed),
                previous_interval,
            )


def development_seed(ordinal: int) -> int:
    """Return a high-bit seed disjoint from every frozen 63-bit seed."""

    if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 0:
        raise ValueError("development seed ordinal must be nonnegative")
    raw = hashlib.sha256(
        f"{DOMAIN_KEY}|cohort-seed|{ordinal}".encode("utf-8")
    ).digest()
    return (1 << 63) | (int.from_bytes(raw[:8], "big") & ((1 << 63) - 1))


def _after(board: chess.Board, move: chess.Move) -> chess.Board:
    successor = board.copy(stack=False)
    successor.push(move)
    return successor


def _add_black_knight_marker(
    base: chess.Board, *, require_mate: bool
) -> tuple[chess.Board, chess.Move] | None:
    """Add the first safe marker under a fixed square/move ordering."""

    for square in chess.SQUARES:
        if base.piece_at(square) is not None:
            continue
        if base.is_attacked_by(chess.WHITE, square):
            continue
        board = base.copy(stack=False)
        board.set_piece_at(square, chess.Piece(chess.KNIGHT, chess.BLACK))
        if not board.is_valid() or board.turn is not chess.WHITE:
            continue
        moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
        mating = tuple(move for move in moves if _after(board, move).is_checkmate())
        if require_mate:
            candidates = mating
        elif mating:
            continue
        else:
            candidates = moves
        for move in candidates:
            successor = _after(board, move)
            marker = successor.pieces(chess.KNIGHT, chess.BLACK)
            if marker and (successor.is_checkmate() is require_mate):
                return board, move
    return None


def _construction_templates() -> dict[str, tuple[chess.Board, chess.Move]]:
    positive: tuple[chess.Board, chess.Move] | None = None
    for fen in _generate_mate_in_one_positions(
        count=64,
        seed=CONSTRUCTION_SEED,
        excluded=set(),
        max_attempts=1_000_000,
    ):
        candidate = _add_black_knight_marker(
            chess.Board(fen), require_mate=True
        )
        if candidate is not None:
            positive = candidate
            break
    if positive is None:
        raise RuntimeError("deterministic positive marker construction failed")

    rng = random.Random(CONSTRUCTION_SEED ^ 0x9E3779B97F4A7C15)
    negative: tuple[chess.Board, chess.Move] | None = None
    for _ in range(100_000):
        base = generate_krk_board(rng, excluded_fens=set())
        candidate = _add_black_knight_marker(base, require_mate=False)
        if candidate is not None:
            negative = candidate
            break
    if negative is None:
        raise RuntimeError("deterministic negative marker construction failed")
    return {"positive": positive, "negative": negative}


def _family_for(region: str, ordinal: int) -> str:
    if region in {"parent_discovery", "sealed_evaluation"}:
        return "positive" if ordinal % 2 == 0 else "negative"
    if region == "parent_prospective_support_and_contradiction":
        return "positive" if ordinal < 4 else "negative"
    if region == "child_prospective_certification":
        return "positive" if ordinal % 5 < 4 else "negative"
    raise ValueError(f"unknown region: {region}")


@dataclass(frozen=True)
class DevelopmentStream:
    rows: tuple[science.StreamRow, ...]
    families: tuple[str, ...]
    training_cases: tuple[tuple[str, str, str], ...]
    manifest: dict[str, Any]


def build_development_stream() -> DevelopmentStream:
    """Build and freeze the deterministic marked stream before learner use."""

    templates = _construction_templates()
    rows: list[science.StreamRow] = []
    families: list[str] = []
    global_ordinal = 0
    for region, count in REGION_COUNTS.items():
        for region_ordinal in range(count):
            family = _family_for(region, region_ordinal)
            template, _move = templates[family]
            board = template.copy(stack=False)
            board.halfmove_clock = 17
            board.fullmove_number = 100_000 + global_ordinal
            fen = board.fen()
            identity = {
                "label": DEVELOPMENT_LABEL,
                "source_commit": SOURCE_COMMIT,
                "construction_seed": CONSTRUCTION_SEED,
                "region": region,
                "region_ordinal": region_ordinal,
                "global_ordinal": global_ordinal,
                "predecessor_fen": fen,
            }
            digest = _sha_json(identity)
            rows.append(science.StreamRow(
                region=region,
                region_ordinal=region_ordinal,
                global_ordinal=global_ordinal,
                row_id=(
                    f"{DEVELOPMENT_LABEL}:{region}:{region_ordinal:04d}:"
                    f"{digest[:16]}"
                ),
                predecessor_fen=fen,
                d4_orbit_key=science.canonical_d4_orbit_key(fen),
                planned_physical_interaction_id=_sha_json({
                    **identity, "kind": "planned-physical-interaction"
                }),
            ))
            families.append(family)
            global_ordinal += 1

    if len({row.row_id for row in rows}) != len(rows):
        raise RuntimeError("development row IDs are not unique")
    if len({row.predecessor_fen for row in rows}) != len(rows):
        raise RuntimeError("development predecessor FENs are not unique")
    if len({row.planned_physical_interaction_id for row in rows}) != len(rows):
        raise RuntimeError("development physical IDs are not unique")
    for row in rows:
        board = chess.Board(row.predecessor_fen)
        signature = sorted(piece.symbol() for piece in board.piece_map().values())
        if (
            not board.is_valid()
            or signature != ["K", "R", "k", "n"]
            or board.turn is not chess.WHITE
            or len(board.pieces(chess.KNIGHT, chess.BLACK)) != 1
            or row.d4_orbit_key
            != science.canonical_d4_orbit_key(row.predecessor_fen)
        ):
            raise RuntimeError("development material-separation guard failed")

    training_cases = tuple(
        (family, board.fen(), move.uci())
        for family, (board, move) in sorted(templates.items())
    )
    unsigned = {
        "schema_version": SCHEMA_VERSION,
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "source_commit": SOURCE_COMMIT,
        "domain_key_sha256": DOMAIN_SHA256,
        "construction_seed": CONSTRUCTION_SEED,
        "region_counts": REGION_COUNTS,
        "row_count": len(rows),
        "rows": [row.manifest() for row in rows],
        "families": families,
        "training_cases": [list(item) for item in training_cases],
        "material_signature": ["K", "R", "k", "n"],
        "material_separator": "one persistent black knight",
        "protected_invariant": (
            "the protected pure-KRK source trajectories never contain a "
            "black knight, including any successors that lose the rook"
        ),
        "d4_separation_proof": (
            "canonical_d4_orbit_key includes every piece symbol; D4 cannot "
            "remove the black knight, while all protected corpora are pure KRK"
        ),
        "within_stream_geometry": {
            "unique_predecessor_fens": len({row.predecessor_fen for row in rows}),
            "unique_d4_orbits": len({row.d4_orbit_key for row in rows}),
            "repeated_geometry_intentional": True,
            "reason": "hold graph context fixed while REAL history grows",
        },
        "performance_scope_disclosure": {
            "d4_geometry_count": 2,
            "source_trained_on_exact_two_templates": True,
            "parent_and_child_family_schedule": (
                "fixed four-positive/one-negative development pattern"
            ),
            "engagement_is_constructed_not_naturalistic": True,
            "valid_use": (
                "history-length, whole-organism-copy, graph, validation, "
                "boundary, serialization, and sealed-evaluation scaling"
            ),
            "invalid_use": (
                "scientific mechanism frequency or workload-distribution "
                "generalization"
            ),
            "production_size_limit": (
                "the source graph has exactly two intrinsic updates, so any "
                "deepcopy conclusion is scoped to the resulting Stage-A-shaped "
                "organism and not an unmeasured production graph"
            ),
        },
        "cache_disclosure": {
            "explicit_outcome_field": False,
            "outcome_derivable_from_successor_fen": True,
            "cache_is_permanently_development_viewed": True,
        },
        "opened_protected_resources": [],
    }
    manifest = {**unsigned, "stream_sha256": _sha_json(unsigned)}
    return DevelopmentStream(
        rows=tuple(rows),
        families=tuple(families),
        training_cases=training_cases,
        manifest=manifest,
    )


def build_development_source(
    stream: DevelopmentStream,
) -> TraceNativeCompetenceOrganism:
    """Build the fixed synthetic R0 using the existing test configuration."""

    graph = NativeReConKRKGraph(config=NativeSingleGraphConfig(
        include_symmetries=False,
        max_ticks=80,
        indexed_scheduler=True,
        key_mode="canonical",
        shared_feature_atoms=True,
        shared_projection_atoms=True,
        include_grouped_cache_terminals=False,
        score_action_pattern_atoms=True,
        terminal_score_normalization="sqrt",
    ))
    for family, fen, move_uci in stream.training_cases:
        graph.apply_intrinsic_td(
            chess.Board(fen),
            chess.Move.from_uci(move_uci),
            td_error=1.0,
            stage_diagnostic=f"{DEVELOPMENT_LABEL}:{family}",
        )
    graph.mature_existing_graph()
    graph.freeze_existing_parameters(reason=DEVELOPMENT_LABEL)
    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(min_grounding_evidence=3)
    )
    credit.register(R0_COMPETENCE_ID, mature=True)
    state = credit.states[R0_COMPETENCE_ID]
    state.slow_value = state.fast_value = 0.8
    state.terminal_evidence = 3
    state.causal_confirmations = 1
    state.grounding_level = 0
    r0 = NativeR0Organism(
        graph=graph,
        credit=credit,
        provenance=FrozenCompetenceProvenance.from_credit(
            credit, R0_COMPETENCE_ID
        ),
        frozen_triplet_ids=frozenset(graph.triplet_ids),
        source_manifest={
            "kind": DEVELOPMENT_LABEL,
            "scientific_use_permitted": False,
            "source_commit": SOURCE_COMMIT,
            "stream_sha256": stream.manifest["stream_sha256"],
            "construction_seed": CONSTRUCTION_SEED,
            "training_case_count": len(stream.training_cases),
            "training_update_count_per_case": 1,
            "configuration_source": (
                "tests/autogrowth/test_native_incremental_history_validation.py"
            ),
        },
    )
    envelope_config = CompetenceEnvelopeConfig(selection_seed=development_seed(0))
    return TraceNativeCompetenceOrganism.empty(
        r0,
        envelope_config=envelope_config,
        learning_config=TraceNativeLearningConfig(
            lifecycle_connected=True,
            specialization_mode=SpecializationMode.LOCAL_CONTRAST,
            genome_seed=envelope_config.selection_seed,
        ),
    )


def build_and_validate_cache(
    source: TraceNativeCompetenceOrganism,
    stream: DevelopmentStream,
) -> dict[str, cache_api.CachedR0Observation]:
    observations = cache_api.build_observation_cache(
        source, stream.rows, frame_namespace=DEVELOPMENT_LABEL
    )
    if len(observations) != len(stream.rows):
        raise RuntimeError("development cache cardinality mismatch")
    expected_family = dict(zip(
        (row.row_id for row in stream.rows), stream.families
    ))
    for row, record in zip(stream.rows, observations):
        actual = chess.Board(record.successor_fen).is_checkmate()
        expected = expected_family[row.row_id] == "positive"
        if actual is not expected:
            raise RuntimeError(
                f"frozen development row outcome mismatch: {row.row_id}"
            )
        successor = chess.Board(record.successor_fen)
        if len(successor.pieces(chess.KNIGHT, chess.BLACK)) != 1:
            raise RuntimeError("development marker did not survive R0 transition")
    return {item.row_id: item for item in observations}


def _rows_by_region(
    stream: DevelopmentStream, region: str
) -> tuple[science.StreamRow, ...]:
    return tuple(row for row in stream.rows if row.region == region)


def _initialize_arms(
    *,
    source: TraceNativeCompetenceOrganism,
    stream: DevelopmentStream,
    cache: Mapping[str, cache_api.CachedR0Observation],
    seed: int,
) -> tuple[dict[SpecializationMode, NativeProspectiveAuthorityV2], dict[str, Any]]:
    source_r0_digest, source_continuation_digest = cache_api._source_bindings(
        source
    )
    envelope_config = replace(source.envelope.config, selection_seed=int(seed))
    learning_config = replace(
        source.learning_config,
        genome_seed=int(seed),
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
    )
    organism = TraceNativeCompetenceOrganism.empty(
        source.r0,
        envelope_config=envelope_config,
        learning_config=learning_config,
    )
    organism.open_prospective_discovery_epoch()
    discovery_rows = _rows_by_region(stream, "parent_discovery")
    receipts = cache_api._mint_discovery_receipts_cached(
        organism,
        discovery_rows,
        cache,
        source_r0_digest=source_r0_digest,
        source_continuation_digest=source_continuation_digest,
    )
    organism.grow_from_grounded_receipts(
        receipts,
        finalize=True,
        mixed_outcome_disposition=MixedOutcomeDisposition.RETAIN_SHADOW,
    )
    epoch = organism.envelope.nomination_epoch
    if epoch is None or epoch.nomination_closed:
        raise RuntimeError("grown development organism is not nomination-open")
    shadows = tuple(sorted(
        (
            cell for cell in organism.envelope.cells.values()
            if cell.state is StemCellState.DORMANT
            and cell.dormant_origin is DormantOrigin.MIXED_OUTCOME_SHADOW
            and cell.prune_reason == "mixed_outcomes"
            and cell.specialization_depth == 0
        ),
        key=lambda cell: (cell.born_request_ordinal, cell.cell_id),
    ))
    template = NativeProspectiveAuthorityV2.from_organism(
        organism,
        mode=V2Mode.PROSPECTIVE,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
        structural_epoch_schedule=(STRUCTURAL_FRONTIER,),
    )
    template.close_nomination()
    template._verify_invariants()
    arms = {mode: copy.deepcopy(template) for mode in ARMS}
    before = {_sha_json(authority.continuation_manifest()) for authority in arms.values()}
    if len(before) != 1:
        raise RuntimeError("candidate-identical development arms diverged")
    for mode, authority in arms.items():
        authority.specialization_mode = mode
        authority._verify_invariants()
    return arms, {
        "discovery_receipt_count": len(receipts),
        "candidate_count": len(template.states),
        "shadow_parent_count": len(shadows),
        "shadow_parent_ids": [cell.cell_id for cell in shadows],
        "candidate_template_digest": template.continuation_digest(),
        "source_r0_digest": source_r0_digest,
        "source_continuation_digest": source_continuation_digest,
    }


@dataclass
class _Attribution:
    graph_wall_seconds: float = 0.0
    graph_calls: int = 0
    live_graph_wall_seconds: float = 0.0
    live_graph_calls: int = 0
    replay_graph_wall_seconds: float = 0.0
    replay_graph_calls: int = 0
    full_invariant_inclusive_wall_seconds: float = 0.0
    full_invariant_calls: int = 0
    incremental_history_validator_inclusive_wall_seconds: float = 0.0
    incremental_history_validator_calls: int = 0
    ledger_replay_validator_inclusive_wall_seconds: float = 0.0
    ledger_replay_validator_calls: int = 0
    digest_wall_seconds: float = 0.0
    digest_calls: int = 0
    _replay_depth: int = 0

    def snapshot(self) -> dict[str, float | int]:
        return {
            key: value for key, value in asdict(self).items()
            if not key.startswith("_")
        }


def _delta(
    after: Mapping[str, float | int], before: Mapping[str, float | int]
) -> dict[str, float | int]:
    return {key: after[key] - before[key] for key in before}


@contextmanager
def _runtime_attribution() -> Iterator[_Attribution]:
    """Collect inclusive call time inside one isolated benchmark process."""

    ledger = _Attribution()
    original_graph = v2._run_authority_graph
    original_verify = NativeProspectiveAuthorityV2._verify_invariants
    original_incremental = (
        NativeProspectiveAuthorityV2._verify_incremental_history_state
    )
    original_ledger = NativeProspectiveAuthorityV2._verify_ledger_derived_state
    original_digest = NativeProspectiveAuthorityV2.continuation_digest

    def graph_wrapper(*args: Any, **kwargs: Any) -> Any:
        started = time.perf_counter()
        try:
            return original_graph(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - started
            ledger.graph_wall_seconds += elapsed
            ledger.graph_calls += 1
            if ledger._replay_depth:
                ledger.replay_graph_wall_seconds += elapsed
                ledger.replay_graph_calls += 1
            else:
                ledger.live_graph_wall_seconds += elapsed
                ledger.live_graph_calls += 1

    def verify_wrapper(self: NativeProspectiveAuthorityV2, *args: Any, **kwargs: Any) -> Any:
        started = time.perf_counter()
        try:
            return original_verify(self, *args, **kwargs)
        finally:
            ledger.full_invariant_inclusive_wall_seconds += (
                time.perf_counter() - started
            )
            ledger.full_invariant_calls += 1

    def incremental_wrapper(
        self: NativeProspectiveAuthorityV2, *args: Any, **kwargs: Any
    ) -> Any:
        started = time.perf_counter()
        try:
            return original_incremental(self, *args, **kwargs)
        finally:
            ledger.incremental_history_validator_inclusive_wall_seconds += (
                time.perf_counter() - started
            )
            ledger.incremental_history_validator_calls += 1

    def ledger_wrapper(
        self: NativeProspectiveAuthorityV2, *args: Any, **kwargs: Any
    ) -> Any:
        started = time.perf_counter()
        ledger._replay_depth += 1
        try:
            return original_ledger(self, *args, **kwargs)
        finally:
            ledger._replay_depth -= 1
            ledger.ledger_replay_validator_inclusive_wall_seconds += (
                time.perf_counter() - started
            )
            ledger.ledger_replay_validator_calls += 1

    def digest_wrapper(self: NativeProspectiveAuthorityV2) -> str:
        started = time.perf_counter()
        try:
            return original_digest(self)
        finally:
            ledger.digest_wall_seconds += time.perf_counter() - started
            ledger.digest_calls += 1

    v2._run_authority_graph = graph_wrapper
    NativeProspectiveAuthorityV2._verify_invariants = verify_wrapper
    NativeProspectiveAuthorityV2._verify_incremental_history_state = (
        incremental_wrapper
    )
    NativeProspectiveAuthorityV2._verify_ledger_derived_state = ledger_wrapper
    NativeProspectiveAuthorityV2.continuation_digest = digest_wrapper
    try:
        yield ledger
    finally:
        v2._run_authority_graph = original_graph
        NativeProspectiveAuthorityV2._verify_invariants = original_verify
        NativeProspectiveAuthorityV2._verify_incremental_history_state = (
            original_incremental
        )
        NativeProspectiveAuthorityV2._verify_ledger_derived_state = (
            original_ledger
        )
        NativeProspectiveAuthorityV2.continuation_digest = original_digest


def _topology_size(authority: NativeProspectiveAuthorityV2) -> dict[str, int]:
    topology = authority.authority_topology
    snapshot = topology.get("graph_snapshot", topology)
    nodes = snapshot.get("nodes", ()) if isinstance(snapshot, Mapping) else ()
    edges = snapshot.get("edges", ()) if isinstance(snapshot, Mapping) else ()
    return {
        "candidate_count": len(authority.states),
        "graph_node_count": len(nodes),
        "graph_edge_count": len(edges),
    }


def _history_event_count(authority: NativeProspectiveAuthorityV2) -> int:
    state = authority.incremental_history_state
    return 0 if state is None else int(state.event_count)


def _plain_event(
    authority: NativeProspectiveAuthorityV2,
    row: science.StreamRow,
    record: cache_api.CachedR0Observation,
    *,
    source_r0_digest: str,
    source_continuation_digest: str,
) -> dict[str, Any]:
    pending, trace = cache_api.open_cached_real_event(
        authority,
        row,
        record,
        source_r0_digest=source_r0_digest,
        source_continuation_digest=source_continuation_digest,
    )
    predecessor = chess.Board(row.predecessor_fen)
    successor = science._execute_transition(predecessor, trace)
    receipt = authority.mint_environment_receipt(
        pending_token=pending.pending_token,
        trace=trace,
        predecessor=predecessor,
        successor=successor,
    )
    emission = authority.consume(receipt)
    return {
        "pending": pending,
        "trace": trace,
        "receipt": receipt,
        "emission": emission,
        "actual": successor.is_checkmate(),
    }


def _profiled_event(
    authority: NativeProspectiveAuthorityV2,
    row: science.StreamRow,
    record: cache_api.CachedR0Observation,
    *,
    source_r0_digest: str,
    source_continuation_digest: str,
    attribution: _Attribution,
) -> dict[str, Any]:
    """Execute the public consume transaction with its deepcopy split out."""

    operation_before = attribution.snapshot()
    cpu_started = time.process_time()
    event_started = time.perf_counter()
    open_started = time.perf_counter()
    pending, trace = cache_api.open_cached_real_event(
        authority,
        row,
        record,
        source_r0_digest=source_r0_digest,
        source_continuation_digest=source_continuation_digest,
    )
    open_seconds = time.perf_counter() - open_started
    predecessor = chess.Board(row.predecessor_fen)
    successor = science._execute_transition(predecessor, trace)
    mint_started = time.perf_counter()
    receipt = authority.mint_environment_receipt(
        pending_token=pending.pending_token,
        trace=trace,
        predecessor=predecessor,
        successor=successor,
    )
    mint_seconds = time.perf_counter() - mint_started
    copy_started = time.perf_counter()
    candidate = copy.deepcopy(authority)
    deepcopy_seconds = time.perf_counter() - copy_started
    in_place_started = time.perf_counter()
    emission = candidate._consume_in_place(receipt)
    in_place_seconds = time.perf_counter() - in_place_started
    commit_started = time.perf_counter()
    authority.__dict__.clear()
    authority.__dict__.update(candidate.__dict__)
    commit_seconds = time.perf_counter() - commit_started
    event_seconds = time.perf_counter() - event_started
    cpu_seconds = time.process_time() - cpu_started
    attribution_delta = _delta(attribution.snapshot(), operation_before)
    return {
        "pending": pending,
        "trace": trace,
        "receipt": receipt,
        "emission": emission,
        "actual": successor.is_checkmate(),
        "timing": {
            "event_wall_seconds": event_seconds,
            "event_cpu_seconds": cpu_seconds,
            "open_wall_seconds": open_seconds,
            "mint_wall_seconds": mint_seconds,
            "deepcopy_wall_seconds": deepcopy_seconds,
            "consume_in_place_wall_seconds": in_place_seconds,
            "commit_wall_seconds": commit_seconds,
            "attribution_inclusive": attribution_delta,
            "categories_overlap": True,
            "instrumented": True,
            "attribution_semantics": (
                "full-invariant, history-validator, digest, and graph timers "
                "are inclusive; replay graph is the subset executed inside "
                "ledger-derived history reconstruction and must not be summed "
                "with its enclosing validator"
            ),
        },
    }


def _profiled_consume_differential(
    authority: NativeProspectiveAuthorityV2,
    row: science.StreamRow,
    record: cache_api.CachedR0Observation,
    *,
    source_r0_digest: str,
    source_continuation_digest: str,
) -> dict[str, Any]:
    public = copy.deepcopy(authority)
    split = copy.deepcopy(authority)
    plain = _plain_event(
        public,
        row,
        record,
        source_r0_digest=source_r0_digest,
        source_continuation_digest=source_continuation_digest,
    )
    with _runtime_attribution() as attribution:
        profiled = _profiled_event(
            split,
            row,
            record,
            source_r0_digest=source_r0_digest,
            source_continuation_digest=source_continuation_digest,
            attribution=attribution,
        )
    exact = (
        plain["pending"] == profiled["pending"]
        and plain["trace"] == profiled["trace"]
        and plain["receipt"] == profiled["receipt"]
        and plain["emission"] == profiled["emission"]
        and public.continuation_manifest() == split.continuation_manifest()
    )
    if not exact:
        raise RuntimeError("profiled consume differs from public consume")
    return {
        "exact": True,
        "public_continuation_digest": public.continuation_digest(),
        "split_continuation_digest": split.continuation_digest(),
    }


def _structural_successor(
    authority: NativeProspectiveAuthorityV2,
) -> dict[str, Any]:
    started = time.perf_counter()
    sealed = authority.seal_prospective_generation()
    opened = authority.open_structural_successor()
    consumptions = []
    child_ids = []
    while any(
        request_id not in authority.request_consumptions
        for request_id in authority.sealed_request_ids
    ):
        consumption = authority.consume_next_structural_request()
        manifest = consumption.manifest()
        if consumption.child_cell_id is not None:
            child_id = authority.materialize_deferred_child(
                consumption.request_id
            )
            child_ids.append(child_id)
            manifest = {
                **manifest,
                "materialized_child_id": child_id,
            }
        consumptions.append(manifest)
    prospective = authority.open_prospective_successor()
    return {
        "sealed_boundary": sealed.manifest(),
        "structural_boundary": opened.manifest(),
        "prospective_boundary": prospective.manifest(),
        "sealed_request_count": len(authority.sealed_request_ids),
        "consumptions": consumptions,
        "child_ids": child_ids,
        "wall_seconds": time.perf_counter() - started,
    }


def _structural_parity(
    incremental: NativeProspectiveAuthorityV2,
    legacy: NativeProspectiveAuthorityV2,
) -> dict[str, Any]:
    left = _structural_successor(incremental)
    right = _structural_successor(legacy)
    comparable_left = {key: value for key, value in left.items() if key != "wall_seconds"}
    comparable_right = {key: value for key, value in right.items() if key != "wall_seconds"}
    if (
        comparable_left != comparable_right
        or incremental.continuation_manifest() != legacy.continuation_manifest()
    ):
        raise RuntimeError("legacy/incremental structural parity mismatch")
    return {
        "exact": True,
        "request_count": left["sealed_request_count"],
        "child_count": len(left["child_ids"]),
        "incremental_wall_seconds": left["wall_seconds"],
        "legacy_wall_seconds": right["wall_seconds"],
    }


def _checkpoint_projection(
    authority: NativeProspectiveAuthorityV2,
) -> dict[str, Any]:
    manifest = authority.continuation_manifest()
    rebuilt = authority._new_incremental_history_state()
    ordered_receipts = sorted(
        authority.consumed_receipts.values(),
        key=lambda item: (item.ordinal, item.receipt_id),
    )
    for receipt in ordered_receipts:
        rebuilt = authority._next_incremental_history_state(
            rebuilt,
            receipt=receipt,
            transaction=authority.event_transactions[receipt.pending_token],
            reference=authority.accepted_real_references[receipt.receipt_id],
            emission=authority.emissions[receipt.receipt_id],
        )
    live_history = (
        None
        if authority.incremental_history_state is None
        else authority.incremental_history_state.manifest()
    )
    rebuilt_history = rebuilt.manifest()
    if live_history != rebuilt_history:
        raise RuntimeError("additive history-chain rebuild differs from live state")
    groups = {
        "ordering_and_history": {
            "next_expected_ordinal": manifest["next_expected_ordinal"],
            "accepted_real_references": manifest["accepted_real_references"],
            "consumed_receipts": manifest["consumed_receipts"],
            "consumed_tokens": manifest["consumed_tokens"],
            "physical_fingerprints": manifest[
                "prospective_physical_fingerprints"
            ],
            "emissions": manifest["emissions"],
            "event_transactions": manifest["event_transactions"],
        },
        "incremental_chain": manifest["incremental_history_state"],
        "candidates_and_graphs": {
            "states": manifest["states"],
            "structural_invariants": manifest["structural_invariants"],
            "authority_topology": manifest["authority_topology"],
            "base_v3": manifest["base_v3"],
        },
        "protocol_and_specialization": {
            key: manifest[key] for key in (
                "structural_epoch_schedule",
                "current_generation",
                "generation_phase",
                "deferred_requests",
                "request_queue",
                "lifetime_requested_parent_ids",
                "request_consumptions",
                "deferred_child_births",
                "deferred_child_escrows",
                "generation_boundaries",
                "sealed_request_ids",
                "sealed_request_queue_digest",
            )
        },
        "r0_persistent_state": authority.base.r0.persistent_state_audit(),
    }
    return {
        "full_manifest_sha256": _sha_json(manifest),
        "live_history_manifest": live_history,
        "rebuilt_history_manifest": rebuilt_history,
        "live_history_sha256": _sha_json(live_history),
        "rebuilt_history_sha256": _sha_json(rebuilt_history),
        "additive_history_chain_rebuild_exact": True,
        "group_sha256": {
            key: _sha_json(value) for key, value in groups.items()
        },
        "event_count": _history_event_count(authority),
        **_topology_size(authority),
    }


def _run_phase1_stage(
    *,
    source: TraceNativeCompetenceOrganism,
    stream: DevelopmentStream,
    cache: Mapping[str, cache_api.CachedR0Observation],
    maximum_events: int,
    starting_event: int = 0,
    starting_strategies: Mapping[
        SpecializationMode, Mapping[str, NativeProspectiveAuthorityV2]
    ] | None = None,
    starting_discovery: Mapping[str, Any] | None = None,
    budget: _Phase1Budget | None = None,
) -> tuple[
    dict[str, Any],
    dict[SpecializationMode, dict[str, NativeProspectiveAuthorityV2]],
]:
    """Run one exact per-event parity stage and return resumable state."""

    if maximum_events not in {32, 64, 128, 256}:
        raise ValueError("Phase 1 maximum must be 32, 64, 128, or 256")
    if starting_event not in {0, 32, 64, 128}:
        raise ValueError("Phase 1 start must be 0, 32, 64, or 128")
    if maximum_events <= starting_event:
        raise ValueError("Phase 1 target must be after its starting event")
    expected_target = (
        EXHAUSTIVE_PARITY_GATE_EVENTS
        if starting_event == 0
        else CHECKPOINTS[CHECKPOINTS.index(starting_event) + 1]
    )
    if maximum_events != expected_target:
        raise ValueError(
            "Phase 1 stages must advance exactly one persisted checkpoint"
        )
    started = _utc_now()
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    seed = development_seed(0)
    if budget is not None:
        budget.check("stage-initialization-before")
    if starting_event == 0:
        if starting_strategies is not None or starting_discovery is not None:
            raise ValueError("initial Phase 1 stage cannot receive resumed state")
        initialization_started = time.perf_counter()
        initial_arms, discovered = _initialize_arms(
            source=source, stream=stream, cache=cache, seed=seed
        )
        discovery = dict(discovered)
        initialization_seconds = time.perf_counter() - initialization_started
        strategies: dict[
            SpecializationMode, dict[str, NativeProspectiveAuthorityV2]
        ] = {}
        for mode, authority in initial_arms.items():
            incremental = copy.deepcopy(authority)
            legacy = copy.deepcopy(authority)
            incremental.set_history_validation_mode_for_development(
                HISTORY_VALIDATION_INCREMENTAL
            )
            legacy.set_history_validation_mode_for_development(
                HISTORY_VALIDATION_LEGACY
            )
            if (
                incremental.continuation_manifest()
                != legacy.continuation_manifest()
            ):
                raise RuntimeError(
                    "validation strategies differ before Phase 1"
                )
            strategies[mode] = {
                "incremental": incremental,
                "legacy_full_replay": legacy,
            }
    else:
        if starting_strategies is None or starting_discovery is None:
            raise ValueError("continued Phase 1 stage requires persisted state")
        initialization_seconds = 0.0
        discovery = dict(starting_discovery)
        strategies = {
            mode: {
                "incremental": starting_strategies[mode]["incremental"]
            }
            for mode in ARMS
        }
        counts = {
            _history_event_count(authority)
            for pair in strategies.values()
            for authority in pair.values()
        }
        if counts != {starting_event}:
            raise RuntimeError(
                "resumed Phase 1 authorities do not match the checkpoint"
            )
    if budget is not None:
        budget.check("stage-initialization-after")

    source_r0_digest = discovery["source_r0_digest"]
    source_continuation_digest = discovery["source_continuation_digest"]
    parent_rows = _rows_by_region(
        stream, "parent_prospective_support_and_contradiction"
    )
    certification_rows = _rows_by_region(
        stream, "child_prospective_certification"
    )
    all_event_rows = (*parent_rows, *certification_rows)
    event_rows = all_event_rows[starting_event:maximum_events]
    exhaustive_per_event_parity = starting_event == 0
    timings: dict[str, dict[str, list[dict[str, Any]]]] = {
        mode.value: {"incremental": [], "legacy_full_replay": []}
        for mode in ARMS
    }
    checkpoints: dict[str, dict[str, Any]] = {}
    midpoint_roundtrip: dict[str, Any] = {}
    structural: dict[str, Any] = {}
    long_history_differential: dict[str, Any] | None = None

    differential = None
    if starting_event == 0:
        differential = _profiled_consume_differential(
            initial_arms[ARMS[0]],
            parent_rows[0],
            cache[parent_rows[0].row_id],
            source_r0_digest=source_r0_digest,
            source_continuation_digest=source_continuation_digest,
        )

    for event_index, row in enumerate(event_rows, start=starting_event + 1):
        if budget is not None:
            budget.check(f"event-{event_index}-before")
        order = (
            (
                ("incremental", "legacy_full_replay")
                if event_index % 2
                else ("legacy_full_replay", "incremental")
            )
            if exhaustive_per_event_parity
            else ("incremental",)
        )
        trace_manifests: dict[str, list[dict[str, Any]]] = {
            key: [] for key in order
        }
        for mode in ARMS:
            results: dict[str, dict[str, Any]] = {}
            for strategy in order:
                authority = strategies[mode][strategy]
                before_count = _history_event_count(authority)
                op_started = time.perf_counter()
                op_cpu_started = time.process_time()
                with _runtime_attribution() as event_attribution:
                    result = _profiled_event(
                        authority,
                        row,
                        cache[row.row_id],
                        source_r0_digest=source_r0_digest,
                        source_continuation_digest=(
                            source_continuation_digest
                        ),
                        attribution=event_attribution,
                    )
                elapsed = time.perf_counter() - op_started
                cpu_elapsed = time.process_time() - op_cpu_started
                timings[mode.value][strategy].append({
                    "event_count_before": before_count,
                    "event_count_after": (
                        _history_event_count(authority)
                    ),
                    "row_id": row.row_id,
                    "wall_seconds": elapsed,
                    "cpu_seconds": cpu_elapsed,
                    "component_timing": result["timing"],
                    **_topology_size(authority),
                })
                results[strategy] = result
                trace_manifests[strategy].append(
                    science._semantic_trace_manifest(result["trace"])
                )
            if exhaustive_per_event_parity:
                left = results["incremental"]
                right = results["legacy_full_replay"]
                exact = (
                    left["pending"] == right["pending"]
                    and science._semantic_trace_manifest(left["trace"])
                    == science._semantic_trace_manifest(right["trace"])
                    and left["receipt"] == right["receipt"]
                    and left["emission"] == right["emission"]
                    and left["actual"] == right["actual"]
                    and strategies[mode][
                        "incremental"
                    ].continuation_manifest()
                    == strategies[mode][
                        "legacy_full_replay"
                    ].continuation_manifest()
                )
                if not exact:
                    raise RuntimeError(
                        f"Phase 1 parity mismatch at {row.row_id} / "
                        f"{mode.value}"
                    )
            if budget is not None:
                budget.check(
                    f"event-{event_index}-{mode.value}-after"
                )
        if trace_manifests["incremental"][1:] != trace_manifests[
            "incremental"
        ][:-1]:
            raise RuntimeError(f"Phase 1 arm trace divergence at {row.row_id}")

        if event_index == len(parent_rows):
            for mode in ARMS:
                structural[mode.value] = _structural_parity(
                    strategies[mode]["incremental"],
                    strategies[mode]["legacy_full_replay"],
                )

        if event_index in CHECKPOINTS and event_index <= maximum_events:
            checkpoint: dict[str, Any] = {}
            for mode in ARMS:
                incremental = strategies[mode]["incremental"]
                incremental_boundary_started = time.perf_counter()
                incremental.verify_full_history_boundary(
                    f"phase1-{event_index}-incremental-{mode.value}"
                )
                incremental_boundary = (
                    time.perf_counter() - incremental_boundary_started
                )
                left_projection = _checkpoint_projection(incremental)
                if exhaustive_per_event_parity:
                    legacy = strategies[mode]["legacy_full_replay"]
                    legacy_boundary_started = time.perf_counter()
                    legacy.verify_full_history_boundary(
                        f"phase1-{event_index}-legacy-{mode.value}"
                    )
                    legacy_boundary = (
                        time.perf_counter() - legacy_boundary_started
                    )
                    right_projection = _checkpoint_projection(legacy)
                    if left_projection != right_projection:
                        raise RuntimeError(
                            f"Phase 1 checkpoint mismatch at {event_index} / "
                            f"{mode.value}"
                        )
                else:
                    legacy_reference = NativeProspectiveAuthorityV2.loads(
                        incremental.dumps()
                    )
                    legacy_reference.set_history_validation_mode_for_development(
                        HISTORY_VALIDATION_LEGACY
                    )
                    legacy_boundary_started = time.perf_counter()
                    legacy_reference.verify_full_history_boundary(
                        f"phase1-{event_index}-boundary-replay-{mode.value}"
                    )
                    legacy_boundary = (
                        time.perf_counter() - legacy_boundary_started
                    )
                    right_projection = _checkpoint_projection(legacy_reference)
                    if left_projection != right_projection:
                        raise RuntimeError(
                            f"Phase 1 reconstructed checkpoint mismatch at "
                            f"{event_index} / {mode.value}"
                        )
                checkpoint[mode.value] = {
                    **left_projection,
                    "exact": True,
                    "full_history_boundary_exact": True,
                    "evidence_scope": (
                        "per_event_strategy_parity_plus_full_boundary"
                        if exhaustive_per_event_parity
                        else "checkpoint_full_history_reconstruction_only"
                    ),
                    "per_event_legacy_incremental_parity_covered_here": (
                        exhaustive_per_event_parity
                    ),
                    "incremental_boundary_wall_seconds": incremental_boundary,
                    "legacy_boundary_wall_seconds": legacy_boundary,
                }
            checkpoints[str(event_index)] = checkpoint
            if budget is not None:
                budget.check(f"checkpoint-{event_index}-after")

        if event_index == 128 and maximum_events >= 128:
            for mode in ARMS:
                item: dict[str, Any] = {}
                restored: dict[str, NativeProspectiveAuthorityV2] = {}
                for strategy in tuple(strategies[mode]):
                    authority = strategies[mode][strategy]
                    before = authority.continuation_manifest()
                    dump_started = time.perf_counter()
                    payload = authority.dumps()
                    dump_seconds = time.perf_counter() - dump_started
                    load_started = time.perf_counter()
                    candidate = NativeProspectiveAuthorityV2.loads(payload)
                    load_seconds = time.perf_counter() - load_started
                    if candidate.continuation_manifest() != before:
                        raise RuntimeError("Phase 1 midpoint roundtrip mismatch")
                    expected_validation_mode = (
                        HISTORY_VALIDATION_INCREMENTAL
                        if strategy == "incremental"
                        else HISTORY_VALIDATION_LEGACY
                    )
                    if candidate._history_validation_mode != expected_validation_mode:
                        raise RuntimeError(
                            "Phase 1 midpoint validation strategy changed"
                        )
                    restored[strategy] = candidate
                    item[strategy] = {
                        "payload_bytes": len(payload),
                        "serialization_wall_seconds": dump_seconds,
                        "restoration_wall_seconds": load_seconds,
                    }
                if (
                    "legacy_full_replay" in restored
                    and restored["incremental"].continuation_manifest()
                    != restored[
                        "legacy_full_replay"
                    ].continuation_manifest()
                ):
                    raise RuntimeError("Phase 1 cross-strategy restore mismatch")
                strategies[mode] = restored
                midpoint_roundtrip[mode.value] = {
                    **item,
                    "exact": True,
                    "evidence_scope": (
                        "incremental_continuation_roundtrip_only"
                        if "legacy_full_replay" not in restored
                        else "cross_strategy_roundtrip_parity"
                    ),
                }
            if maximum_events > event_index:
                next_row = all_event_rows[event_index]
                long_history_differential = _profiled_consume_differential(
                    strategies[ARMS[0]]["incremental"],
                    next_row,
                    cache[next_row.row_id],
                    source_r0_digest=source_r0_digest,
                    source_continuation_digest=source_continuation_digest,
                )

    if (
        long_history_differential is None
        and starting_event < 128 <= maximum_events
    ):
        next_row = all_event_rows[128]
        long_history_differential = _profiled_consume_differential(
            strategies[ARMS[0]]["incremental"],
            next_row,
            cache[next_row.row_id],
            source_r0_digest=source_r0_digest,
            source_continuation_digest=source_continuation_digest,
        )

    evaluation_rows = _rows_by_region(stream, "sealed_evaluation")
    sealed_evaluation: dict[str, Any] = {}
    for mode in ARMS:
        if budget is not None:
            budget.check(f"sealed-evaluation-{mode.value}-before")
        live_pair = strategies[mode]
        pair = {
            strategy: NativeProspectiveAuthorityV2.loads(authority.dumps())
            for strategy, authority in live_pair.items()
        }
        for authority in pair.values():
            authority.seal_read_only_evaluation()
        if (
            exhaustive_per_event_parity
            and pair["incremental"].continuation_manifest()
            != pair["legacy_full_replay"].continuation_manifest()
        ):
            raise RuntimeError("Phase 1 evaluation-seal parity mismatch")
        decisions = []
        evaluation_started = time.perf_counter()
        strategy_evaluation_seconds = {
            "incremental": 0.0,
            "legacy_full_replay": 0.0,
        }
        for row_index, row in enumerate(evaluation_rows):
            result = {}
            evaluation_order = (
                (
                    ("incremental", "legacy_full_replay")
                    if row_index % 2 == 0
                    else ("legacy_full_replay", "incremental")
                )
                if exhaustive_per_event_parity
                else ("incremental",)
            )
            for strategy in evaluation_order:
                authority = pair[strategy]
                strategy_started = time.perf_counter()
                opened = cache_api.evaluate_cached_observation(
                    authority,
                    row,
                    cache[row.row_id],
                    source_r0_digest=source_r0_digest,
                    source_continuation_digest=source_continuation_digest,
                )
                strategy_evaluation_seconds[strategy] += (
                    time.perf_counter() - strategy_started
                )
                result[strategy] = {
                    "trace": science._semantic_trace_manifest(opened["trace"]),
                    "classification": opened["classification"].to_manifest(),
                    "graph": opened["graph"],
                }
            if (
                exhaustive_per_event_parity
                and result["incremental"] != result["legacy_full_replay"]
            ):
                raise RuntimeError(
                    f"Phase 1 sealed-evaluation mismatch at {row.row_id}"
                )
            decisions.append({
                "row_id": row.row_id,
                "projection_sha256": _sha_json(result["incremental"]),
            })
        sealed_evaluation[mode.value] = {
            "exact": True,
            "evidence_scope": (
                "incremental_legacy_exact_parity"
                if exhaustive_per_event_parity
                else "incremental_after_exact_full_history_boundary"
            ),
            "per_event_strategy_parity_claimed": exhaustive_per_event_parity,
            "row_count": len(decisions),
            "decision_projection_sha256": _sha_json(decisions),
            "pair_wall_seconds": time.perf_counter() - evaluation_started,
            "strategy_wall_seconds": strategy_evaluation_seconds,
        }
        if budget is not None:
            budget.check(f"sealed-evaluation-{mode.value}-after")

    peak_rss_mib, peak_rss_basis = _rss_mib()
    return {
        "schema_version": SCHEMA_VERSION,
        "phase": "phase1_exact_parity",
        "status": "PASSED",
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "source_commit": SOURCE_COMMIT,
        "stream_sha256": stream.manifest["stream_sha256"],
        "genome_seed": seed,
        "stage_start_event_exclusive": starting_event,
        "stage_end_event_inclusive": maximum_events,
        "maximum_events": maximum_events,
        "checkpoint_event_counts": [
            item
            for item in CHECKPOINTS
            if starting_event < item <= maximum_events
        ],
        "claim_scope": {
            "per_event_legacy_incremental_exact_parity": {
                "covered_event_range_inclusive": (
                    [1, EXHAUSTIVE_PARITY_GATE_EVENTS]
                    if exhaustive_per_event_parity
                    else None
                ),
                "basis": (
                    "literal transaction, semantic trace, receipt, emission, "
                    "actual outcome, and complete continuation-manifest "
                    "equality after every covered event"
                ),
                "not_extended_by_this_stage": (
                    not exhaustive_per_event_parity
                ),
            },
            "incremental_execution": {
                "covered_event_range_inclusive": [
                    starting_event + 1,
                    maximum_events,
                ],
                "per_event_legacy_comparator_run": exhaustive_per_event_parity,
            },
            "full_history_boundary_reconstruction": {
                "covered_event_counts": [
                    item
                    for item in CHECKPOINTS
                    if starting_event < item <= maximum_events
                ],
                "basis": (
                    "incremental state passed exact ledger reconstruction; "
                    "a legacy-validation clone passed the same reconstruction "
                    "and had an identical checkpoint projection"
                ),
                "independently_evolved_legacy_state_compared": (
                    exhaustive_per_event_parity
                ),
            },
            "unexecuted_events_not_claimed": (
                []
                if maximum_events == CHECKPOINTS[-1]
                else [maximum_events + 1, CHECKPOINTS[-1]]
            ),
            "scientific_claim_permitted": False,
        },
        "both_authorities_remained_prospective": True,
        "only_validation_strategy_varied": exhaustive_per_event_parity,
        "post_gate_incremental_only": not exhaustive_per_event_parity,
        "profiled_consume_public_differential": {
            "history_zero": differential,
            "history_128_after_structural_growth": long_history_differential,
        },
        "discovery": discovery,
        "initialization_wall_seconds": initialization_seconds,
        "structural": structural,
        "checkpoints": checkpoints,
        "midpoint_serialization_restoration": midpoint_roundtrip,
        "sealed_evaluation": sealed_evaluation,
        "event_timings": timings,
        "timing_order_alternated": True,
        "timings_exclude_manifest_comparisons": True,
        "event_component_timings_instrumented": True,
        "started_at": started,
        "finished_at": _utc_now(),
        "wall_seconds": time.perf_counter() - wall_started,
        "cpu_seconds": time.process_time() - cpu_started,
        "peak_rss_mib": peak_rss_mib,
        "peak_rss_basis": peak_rss_basis,
    }, strategies


def run_phase1_parity(
    *,
    source: TraceNativeCompetenceOrganism,
    stream: DevelopmentStream,
    cache: Mapping[str, cache_api.CachedR0Observation],
    maximum_events: int = 32,
) -> dict[str, Any]:
    """Run a fresh bounded exact-parity stage without persisting continuation."""

    result, _strategies = _run_phase1_stage(
        source=source,
        stream=stream,
        cache=cache,
        maximum_events=maximum_events,
    )
    return result


def _event_record(
    *,
    row: science.StreamRow,
    result: Mapping[str, Any],
    history_before: int,
    authority: NativeProspectiveAuthorityV2,
) -> dict[str, Any]:
    pending = result["pending"]
    emission = result["emission"]
    return {
        "row_id": row.row_id,
        "region": row.region,
        "global_ordinal": row.global_ordinal,
        "history_event_count_before": history_before,
        "history_event_count_after": (
            _history_event_count(authority)
        ),
        "selected_action": result["trace"].actuation.move_uci,
        "observed_outcome": result["actual"],
        "classification_before": pending.pre_outcome_classification.to_manifest(),
        "matching_cell_ids_before": list(pending.matching_cell_ids),
        "receipt_id": result["receipt"].receipt_id,
        "interaction_fingerprint": result["receipt"].interaction_fingerprint,
        "prequential_false_authority_ids": list(
            emission.prequential_false_authority_ids
        ),
        "graph_maturity_ids": list(emission.graph_maturity_ids),
        "graph_revocation_ids": list(emission.graph_revocation_ids),
        "graph_specialization_request_ids": list(
            emission.graph_specialization_request_ids
        ),
        "request_queue_appended_ids": list(
            emission.request_queue_appended_ids
        ),
        "timing": result["timing"],
        **_topology_size(authority),
    }


def _consume_profiled_all_arms(
    *,
    arms: Mapping[SpecializationMode, NativeProspectiveAuthorityV2],
    row: science.StreamRow,
    cache: Mapping[str, cache_api.CachedR0Observation],
    source_r0_digest: str,
    source_continuation_digest: str,
    attribution: _Attribution,
    ledgers: dict[str, list[dict[str, Any]]],
) -> None:
    results: dict[SpecializationMode, dict[str, Any]] = {}
    for mode, authority in arms.items():
        history_before = _history_event_count(authority)
        result = _profiled_event(
            authority,
            row,
            cache[row.row_id],
            source_r0_digest=source_r0_digest,
            source_continuation_digest=source_continuation_digest,
            attribution=attribution,
        )
        results[mode] = result
        ledgers[mode.value].append(_event_record(
            row=row,
            result=result,
            history_before=history_before,
            authority=authority,
        ))
    semantic = [
        science._semantic_trace_manifest(results[mode]["trace"])
        for mode in ARMS
    ]
    fingerprints = [
        results[mode]["receipt"].interaction_fingerprint for mode in ARMS
    ]
    outcomes = [bool(results[mode]["actual"]) for mode in ARMS]
    if semantic[1:] != semantic[:-1]:
        raise RuntimeError(f"cohort arm semantic divergence at {row.row_id}")
    if len(set(fingerprints)) != 1 or len(set(outcomes)) != 1:
        raise RuntimeError(f"cohort physical divergence at {row.row_id}")


def _timing_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    keys = (
        "event_wall_seconds",
        "event_cpu_seconds",
        "open_wall_seconds",
        "mint_wall_seconds",
        "deepcopy_wall_seconds",
        "consume_in_place_wall_seconds",
        "commit_wall_seconds",
    )
    totals = {
        key: sum(float(row["timing"][key]) for row in rows) for key in keys
    }
    event_total = totals["event_wall_seconds"]
    return {
        "event_count": len(rows),
        "totals": totals,
        "deepcopy_fraction_of_event_wall": (
            0.0 if not event_total
            else totals["deepcopy_wall_seconds"] / event_total
        ),
        "consume_in_place_fraction_of_event_wall": (
            0.0 if not event_total
            else totals["consume_in_place_wall_seconds"] / event_total
        ),
        "checkpoint_curve": [
            {
                "event_count": int(row["history_event_count_after"]),
                "event_wall_seconds": row["timing"]["event_wall_seconds"],
                "deepcopy_wall_seconds": row["timing"][
                    "deepcopy_wall_seconds"
                ],
                "consume_in_place_wall_seconds": row["timing"][
                    "consume_in_place_wall_seconds"
                ],
                "candidate_count": row["candidate_count"],
                "graph_node_count": row["graph_node_count"],
                "graph_edge_count": row["graph_edge_count"],
            }
            for row in rows
            if int(row["history_event_count_after"]) in CHECKPOINTS
        ],
    }


def _mechanism_summary(
    authority: NativeProspectiveAuthorityV2,
    *,
    discovery: Mapping[str, Any],
    structural: Mapping[str, Any],
    ledger: Sequence[Mapping[str, Any]],
    initial_ids: set[str],
    evaluation_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    child_ids = sorted(
        birth.child_cell_id
        for birth in authority.deferred_child_births.values()
        if birth.disposition == "MATERIALIZED"
    )
    child_transitions = {
        child_id: list(authority.states[child_id].transition_rows)
        for child_id in child_ids
    }
    certified_ids = sorted(
        cell_id for cell_id, state in authority.states.items()
        if state.prospectively_certified
    )
    safe_ids = sorted(
        cell_id for cell_id in certified_ids
        if authority.states[cell_id].hypothesis.polarity
        is AvailabilityState.AVAILABLE
    )
    selective_ids = sorted(
        cell_id for cell_id in certified_ids
        if authority.states[cell_id].hypothesis.polarity
        is AvailabilityState.REFUTED
    )
    parent_contradiction_rows = []
    parent_contradiction_incidences = 0
    for row in ledger:
        if row["region"] != "parent_prospective_support_and_contradiction":
            continue
        affected = sorted(initial_ids.intersection(
            set(row["prequential_false_authority_ids"])
            | set(row["graph_revocation_ids"])
        ))
        if affected:
            parent_contradiction_rows.append({
                "row_id": row["row_id"], "parent_cell_ids": affected
            })
            parent_contradiction_incidences += len(affected)
    certifications = [
        {
            "row_id": row["row_id"],
            "cell_ids": row["graph_maturity_ids"],
        }
        for row in ledger if row["graph_maturity_ids"]
    ]
    revocations = [
        {
            "row_id": row["row_id"],
            "cell_ids": row["graph_revocation_ids"],
        }
        for row in ledger if row["graph_revocation_ids"]
    ]
    return {
        "candidate_count_after_discovery": discovery["candidate_count"],
        "dormant_mixed_shadow_count": discovery["shadow_parent_count"],
        "parent_contradiction_event_count": len(parent_contradiction_rows),
        "parent_contradiction_cell_incidences": (
            parent_contradiction_incidences
        ),
        "parent_contradiction_rows": parent_contradiction_rows,
        "specialization_request_count": len(authority.deferred_requests),
        "sealed_request_count": structural["sealed_request_count"],
        "request_consumptions": structural["consumptions"],
        "children_born_count": len(child_ids),
        "children_born_ids": child_ids,
        "child_transition_rows": child_transitions,
        "certification_events": certifications,
        "revocation_events": revocations,
        "final_prospectively_certified_cell_ids": certified_ids,
        "final_safe_cell_ids": safe_ids,
        "final_selective_cell_ids": selective_ids,
        "sealed_metrics": science.sealed_metrics(evaluation_rows),
        "candidate_graph_size_over_time": [
            {
                key: row[key] for key in (
                    "history_event_count_after",
                    "candidate_count",
                    "graph_node_count",
                    "graph_edge_count",
                )
            }
            for row in ledger
        ],
        "non_engagement_retained_without_seed_replacement": True,
    }


def _rss_mib() -> tuple[float, str]:
    raw = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if sys.platform == "darwin":
        return raw / (1024.0 * 1024.0), "ru_maxrss bytes (macOS)"
    return raw / 1024.0, "ru_maxrss KiB (non-macOS)"


def _run_seed_core(
    *,
    ordinal: int,
    seed: int,
    source: TraceNativeCompetenceOrganism,
    stream: DevelopmentStream,
    cache: Mapping[str, cache_api.CachedR0Observation],
    seed_identity: str,
    run_plan_sha256: str,
    invocation_id: str,
    resumed_from_invocation_ids: Sequence[str],
) -> dict[str, Any]:
    started_at = _utc_now()
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    initialization_started = time.perf_counter()
    arms, discovery = _initialize_arms(
        source=source, stream=stream, cache=cache, seed=seed
    )
    initialization_seconds = time.perf_counter() - initialization_started
    initial_ids = {mode: set(authority.states) for mode, authority in arms.items()}
    ledgers = {mode.value: [] for mode in ARMS}
    structural: dict[str, Any] = {}
    boundaries: dict[str, Any] = {}
    serialization: dict[str, Any] = {}
    evaluations: dict[str, list[dict[str, Any]]] = {}
    source_audit = source.r0.persistent_state_audit()

    with _runtime_attribution() as attribution:
        for row in _rows_by_region(
            stream, "parent_prospective_support_and_contradiction"
        ):
            _consume_profiled_all_arms(
                arms=arms,
                row=row,
                cache=cache,
                source_r0_digest=discovery["source_r0_digest"],
                source_continuation_digest=discovery[
                    "source_continuation_digest"
                ],
                attribution=attribution,
                ledgers=ledgers,
            )
        for mode, authority in arms.items():
            structural[mode.value] = _structural_successor(authority)
        for row in _rows_by_region(
            stream, "child_prospective_certification"
        ):
            _consume_profiled_all_arms(
                arms=arms,
                row=row,
                cache=cache,
                source_r0_digest=discovery["source_r0_digest"],
                source_continuation_digest=discovery[
                    "source_continuation_digest"
                ],
                attribution=attribution,
                ledgers=ledgers,
            )

        for mode, authority in arms.items():
            boundary_started = time.perf_counter()
            authority.verify_full_history_boundary(
                f"cohort-seed-{ordinal}-{mode.value}"
            )
            boundaries[mode.value] = {
                "exact": True,
                "wall_seconds": time.perf_counter() - boundary_started,
                "event_count": _history_event_count(authority),
            }
            before = authority.continuation_manifest()
            dump_started = time.perf_counter()
            payload = authority.dumps()
            dump_seconds = time.perf_counter() - dump_started
            load_started = time.perf_counter()
            restored = NativeProspectiveAuthorityV2.loads(payload)
            load_seconds = time.perf_counter() - load_started
            if restored.continuation_manifest() != before:
                raise RuntimeError("cohort serialization/restoration mismatch")
            seal_started = time.perf_counter()
            restored.seal_read_only_evaluation()
            seal_seconds = time.perf_counter() - seal_started
            frozen_manifest = restored.continuation_manifest()
            decisions = []
            evaluation_started = time.perf_counter()
            for row in _rows_by_region(stream, "sealed_evaluation"):
                opened = cache_api.evaluate_cached_observation(
                    restored,
                    row,
                    cache[row.row_id],
                    source_r0_digest=discovery["source_r0_digest"],
                    source_continuation_digest=discovery[
                        "source_continuation_digest"
                    ],
                )
                classification = opened["classification"]
                decisions.append({
                    "row_id": row.row_id,
                    "available": (
                        classification.state is AvailabilityState.AVAILABLE
                    ),
                    "actual": chess.Board(
                        cache[row.row_id].successor_fen
                    ).is_checkmate(),
                    "available_cell_ids": list(
                        classification.available_cell_ids
                    ),
                    "refuted_cell_ids": list(
                        classification.refuted_cell_ids
                    ),
                    "matching_cell_ids": list(opened["graph"]["commitment"]),
                    "semantic_trace_digest": science._trace_digest(
                        opened["trace"]
                    ),
                })
            evaluation_seconds = time.perf_counter() - evaluation_started
            if restored.continuation_manifest() != frozen_manifest:
                raise RuntimeError("cohort sealed evaluation mutated authority")
            if restored.base.r0.persistent_state_audit() != source_audit:
                raise RuntimeError("cohort R0 persistent state changed")
            arms[mode] = restored
            evaluations[mode.value] = decisions
            serialization[mode.value] = {
                "payload_bytes": len(payload),
                "payload_sha256": hashlib.sha256(payload).hexdigest(),
                "serialization_wall_seconds": dump_seconds,
                "restoration_wall_seconds": load_seconds,
                "evaluation_seal_wall_seconds": seal_seconds,
                "sealed_evaluation_wall_seconds": evaluation_seconds,
                "sealed_evaluation_row_count": len(decisions),
                "serialization_includes_full_boundary": True,
                "restoration_includes_full_boundary": True,
            }
        attribution_totals = attribution.snapshot()

    arm_results = {}
    for mode, authority in arms.items():
        ledger = ledgers[mode.value]
        arm_results[mode.value] = {
            "event_ledger": ledger,
            "timing_summary": _timing_summary(ledger),
            "structural_successor": structural[mode.value],
            "full_history_boundary": boundaries[mode.value],
            "serialization_restoration_evaluation": serialization[mode.value],
            "sealed_evaluation_rows": evaluations[mode.value],
            "mechanisms": _mechanism_summary(
                authority,
                discovery=discovery,
                structural=structural[mode.value],
                ledger=ledger,
                initial_ids=initial_ids[mode],
                evaluation_rows=evaluations[mode.value],
            ),
            "final_continuation_sha256": _sha_json(
                authority.continuation_manifest()
            ),
        }
    rss_mib, rss_basis = _rss_mib()
    return {
        "schema_version": SEED_RESULT_SCHEMA,
        "status": "COMPLETED",
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "source_commit": SOURCE_COMMIT,
        "stream_sha256": stream.manifest["stream_sha256"],
        "ordinal": ordinal,
        "genome_seed": seed,
        "seed_identity": seed_identity,
        "run_plan_sha256": run_plan_sha256,
        "completion_invocation_id": invocation_id,
        "resumed_from_invocation_ids": list(resumed_from_invocation_ids),
        "initialization": discovery,
        "initialization_wall_seconds": initialization_seconds,
        "arms": arm_results,
        "attribution_inclusive_totals": attribution_totals,
        "attribution_categories_overlap": True,
        "started_at": started_at,
        "finished_at": _utc_now(),
        "wall_seconds": time.perf_counter() - wall_started,
        "cpu_seconds": time.process_time() - cpu_started,
        "peak_rss_mib": rss_mib,
        "peak_rss_basis": rss_basis,
        "worker_pid": os.getpid(),
    }


def _validate_cached_outcomes(
    stream: DevelopmentStream,
    cache: Mapping[str, cache_api.CachedR0Observation],
) -> None:
    expected_family = dict(zip(
        (row.row_id for row in stream.rows), stream.families
    ))
    if set(cache) != {row.row_id for row in stream.rows}:
        raise RuntimeError("development cache row set mismatch")
    for row in stream.rows:
        record = cache[row.row_id]
        expected = expected_family[row.row_id] == "positive"
        actual = chess.Board(record.successor_fen).is_checkmate()
        if actual is not expected:
            raise RuntimeError(
                f"frozen development cache outcome mismatch: {row.row_id}"
            )
        if len(chess.Board(record.successor_fen).pieces(
            chess.KNIGHT, chess.BLACK
        )) != 1:
            raise RuntimeError("cached transition lost development marker")


def prepare_development_inputs(
    output_dir: Path,
) -> tuple[
    TraceNativeCompetenceOrganism,
    DevelopmentStream,
    dict[str, cache_api.CachedR0Observation],
    dict[str, Any],
]:
    """Persist the frozen dev stream before any learner/cache operation."""

    output_dir = _guard_output_dir(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stream = build_development_stream()
    stream_path = output_dir / "development_stream.json"
    if stream_path.exists():
        if json.loads(stream_path.read_text(encoding="utf-8")) != stream.manifest:
            raise RuntimeError("persisted development stream identity changed")
    else:
        _atomic_write_json(stream_path, stream.manifest)

    source = build_development_source(stream)
    source_r0_digest, source_continuation_digest = cache_api._source_bindings(
        source
    )
    r0_audit = source.r0.persistent_state_audit()
    stable_r0_audit = {
        key: r0_audit[key] for key in (
            "topology_sha256",
            "weights_sha256",
            "credit_sha256",
            "lifecycle_sha256",
        )
    }
    source_manifest = {
        "schema_version": SCHEMA_VERSION,
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "source_commit": SOURCE_COMMIT,
        "stream_sha256": stream.manifest["stream_sha256"],
        "construction_seed": CONSTRUCTION_SEED,
        "source_r0_persistent_digest": source_r0_digest,
        "source_organism_continuation_digest": source_continuation_digest,
        "stable_source_r0_audit": stable_r0_audit,
        "stable_source_r0_audit_sha256": _sha_json(stable_r0_audit),
        "process_local_audit_fields_excluded_from_cross_process_identity": [
            "exact_state_sha256", "serialized_state_sha256"
        ],
        "cross_process_exclusion_reason": (
            "those two pickle/set-order-sensitive diagnostic hashes vary "
            "across fresh Python processes while topology, weights, credit, "
            "lifecycle, source binding, and continuation remain exact"
        ),
        "training_cases": [list(item) for item in stream.training_cases],
        "configuration_provenance": {
            "graph_and_credit_values": (
                "copied field-for-field from the existing incremental-history "
                "synthetic test"
            ),
            "lifecycle_and_specialization_modes": (
                "copied from the existing deferred-specialization Stage-A path"
            ),
        },
        "learner_parameter_tuning_performed": False,
    }
    source_manifest["source_manifest_sha256"] = _sha_json(source_manifest)
    source_path = output_dir / "development_source_manifest.json"
    if source_path.exists():
        if json.loads(source_path.read_text(encoding="utf-8")) != source_manifest:
            raise RuntimeError("persisted development source identity changed")
    else:
        _atomic_write_json(source_path, source_manifest)

    cache_path = output_dir / "development_r0_observation_cache.json"
    if cache_path.exists():
        cache = cache_api.load_and_verify_cache(
            cache_path, source, stream.rows
        )
    else:
        cache = build_and_validate_cache(source, stream)
        cache_payload = cache_api.cache_payload(
            source, stream.rows, tuple(cache[row.row_id] for row in stream.rows)
        )
        cache_payload.pop("payload_digest")
        cache_payload.update({
            "development_label": DEVELOPMENT_LABEL,
            "scientific_use_permitted": False,
            "outcome_derivable_from_successor_fen": True,
            "interpretation": (
                "permanently viewed development cache; contains no explicit "
                "outcome field but is not outcome-blind as an artifact"
            ),
        })
        cache_payload["payload_digest"] = _sha_json(cache_payload)
        _atomic_write_json(cache_path, cache_payload)
    _validate_cached_outcomes(stream, cache)

    module_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    identity_unsigned = {
        "schema_version": SCHEMA_VERSION,
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "source_commit": SOURCE_COMMIT,
        "benchmark_git_head": _git_head(),
        "module_sha256": module_sha256,
        "tracked_dependency_sha256": _dependency_hashes(),
        "all_tracked_repository_files_verified_clean": True,
        "stream_sha256": stream.manifest["stream_sha256"],
        "source_manifest_sha256": source_manifest[
            "source_manifest_sha256"
        ],
        "source_r0_persistent_digest": source_r0_digest,
        "source_organism_continuation_digest": source_continuation_digest,
        "cache_payload_digest": json.loads(
            cache_path.read_text(encoding="utf-8")
        )["payload_digest"],
        "arms": [mode.value for mode in ARMS],
        "checkpoints": list(CHECKPOINTS),
        "region_counts": REGION_COUNTS,
        "cache_outcome_derivable_and_development_viewed": True,
    }
    input_identity = {
        **identity_unsigned,
        "input_identity_sha256": _sha_json(identity_unsigned),
    }
    identity_path = output_dir / "input_identity.json"
    if identity_path.exists():
        if json.loads(identity_path.read_text(encoding="utf-8")) != input_identity:
            raise RuntimeError("persisted benchmark input identity changed")
    else:
        _atomic_write_json(identity_path, input_identity)
    return source, stream, cache, input_identity


def _seed_identity(
    input_identity: Mapping[str, Any],
    *,
    ordinal: int,
    seed: int,
    run_plan_sha256: str,
) -> str:
    return _sha_json({
        "input_identity_sha256": input_identity["input_identity_sha256"],
        "seed_result_schema": SEED_RESULT_SCHEMA,
        "run_plan_sha256": run_plan_sha256,
        "ordinal": ordinal,
        "genome_seed": seed,
        "arms": [mode.value for mode in ARMS],
    })


def _seed_result_path(output_dir: Path, ordinal: int) -> Path:
    return output_dir / "seed_results" / f"{ordinal:03d}.json"


def _seed_start_path(
    output_dir: Path, ordinal: int, invocation_id: str
) -> Path:
    return (
        output_dir / "seed_state"
        / f"{ordinal:03d}.{invocation_id}.started.json"
    )


def _load_or_create_run_plan(
    *,
    output_dir: Path,
    input_identity: Mapping[str, Any],
    cohort_size: int,
    workers: int,
    calibration_decision_sha256: str,
) -> dict[str, Any]:
    path = output_dir / "run_plan.json"
    fixed = {
        "schema_version": SCHEMA_VERSION,
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "input_identity_sha256": input_identity["input_identity_sha256"],
        "calibration_decision_sha256": calibration_decision_sha256,
        "cohort_size": cohort_size,
        "workers": workers,
        "cohort_ordinals": list(range(1, cohort_size + 1)),
        "cohort_genome_seeds": [
            development_seed(item) for item in range(1, cohort_size + 1)
        ],
        "seed_replacement_permitted": False,
        "maximum_workers": MAX_WORKERS,
    }
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        for key, value in fixed.items():
            if existing.get(key) != value:
                raise RuntimeError(
                    "cohort run plan is immutable across resumes"
                )
        expected = existing.pop("run_plan_sha256", None)
        if expected != _sha_json(existing):
            raise RuntimeError("cohort run plan digest mismatch")
        return {**existing, "run_plan_sha256": expected}
    unsigned = {**fixed, "created_at": _utc_now()}
    plan = {**unsigned, "run_plan_sha256": _sha_json(unsigned)}
    _atomic_write_json(path, plan)
    return plan


def _invocation_path(output_dir: Path, invocation_id: str) -> Path:
    return output_dir / "invocations" / f"{invocation_id}.json"


def _write_invocation(
    *,
    output_dir: Path,
    invocation_id: str,
    run_plan_sha256: str,
    status: str,
    started_at: str,
    elapsed_wall_seconds: float,
    scheduled_ordinals: Sequence[int],
    interrupted_ordinals: Sequence[int],
    completed_this_invocation: Sequence[int],
    failed_this_invocation: Sequence[int],
) -> dict[str, Any]:
    payload = _self_digest({
        "schema_version": SCHEMA_VERSION,
        "label": DEVELOPMENT_LABEL,
        "invocation_id": invocation_id,
        "run_plan_sha256": run_plan_sha256,
        "status": status,
        "started_at": started_at,
        "updated_at": _utc_now(),
        "elapsed_wall_seconds": elapsed_wall_seconds,
        "scheduled_ordinals": list(scheduled_ordinals),
        "interrupted_ordinals_before_invocation": list(interrupted_ordinals),
        "completed_this_invocation": sorted(completed_this_invocation),
        "failed_this_invocation": sorted(failed_this_invocation),
    })
    _atomic_write_json(_invocation_path(output_dir, invocation_id), payload)
    return payload


def _prior_start_invocations(output_dir: Path, ordinal: int) -> tuple[str, ...]:
    result = []
    directory = output_dir / "seed_state"
    if not directory.exists():
        return ()
    for path in sorted(directory.glob(f"{ordinal:03d}.*.started.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        invocation_id = payload.get("invocation_id")
        if isinstance(invocation_id, str):
            result.append(invocation_id)
    return tuple(result)


def _run_seed_worker(payload: Mapping[str, Any]) -> dict[str, Any]:
    output_dir = Path(payload["output_dir"])
    ordinal = int(payload["ordinal"])
    seed = int(payload["seed"])
    seed_identity = str(payload["seed_identity"])
    run_plan_sha256 = str(payload["run_plan_sha256"])
    invocation_id = str(payload["invocation_id"])
    resumed_from = tuple(payload["resumed_from_invocation_ids"])
    start_payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "STARTED",
        "label": DEVELOPMENT_LABEL,
        "ordinal": ordinal,
        "genome_seed": seed,
        "seed_identity": seed_identity,
        "run_plan_sha256": run_plan_sha256,
        "invocation_id": invocation_id,
        "resumed_from_invocation_ids": list(resumed_from),
        "worker_pid": os.getpid(),
        "started_at": _utc_now(),
    }
    _atomic_write_json(
        _seed_start_path(output_dir, ordinal, invocation_id), start_payload
    )
    try:
        result = _run_seed_core(
            ordinal=ordinal,
            seed=seed,
            source=payload["source"],
            stream=payload["stream"],
            cache=payload["cache"],
            seed_identity=seed_identity,
            run_plan_sha256=run_plan_sha256,
            invocation_id=invocation_id,
            resumed_from_invocation_ids=resumed_from,
        )
    except Exception as exc:
        result = {
            "schema_version": SEED_RESULT_SCHEMA,
            "status": "FAILED",
            "label": DEVELOPMENT_LABEL,
            "scientific_use_permitted": False,
            "source_commit": SOURCE_COMMIT,
            "stream_sha256": payload["stream"].manifest["stream_sha256"],
            "ordinal": ordinal,
            "genome_seed": seed,
            "seed_identity": seed_identity,
            "run_plan_sha256": run_plan_sha256,
            "completion_invocation_id": invocation_id,
            "resumed_from_invocation_ids": list(resumed_from),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "failed_at": _utc_now(),
            "worker_pid": os.getpid(),
        }
    final = _self_digest(result)
    path = _seed_result_path(output_dir, ordinal)
    _atomic_write_json(path, final)
    return {
        "ordinal": ordinal,
        "status": final["status"],
        "path": str(path),
        "payload_digest": final["payload_digest"],
        "error": final.get("error"),
    }


def _worker_transport_smoke(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Exercise spawn, input pickling, bindings, and atomic worker output."""

    source = payload["source"]
    stream = payload["stream"]
    cache = payload["cache"]
    source_r0_digest, source_continuation_digest = cache_api._source_bindings(
        source
    )
    if set(cache) != {row.row_id for row in stream.rows}:
        raise RuntimeError("worker transport smoke cache identity mismatch")
    result = _self_digest({
        "schema_version": SCHEMA_VERSION,
        "status": "PASSED",
        "label": DEVELOPMENT_LABEL,
        "source_r0_digest": source_r0_digest,
        "source_continuation_digest": source_continuation_digest,
        "stream_sha256": stream.manifest["stream_sha256"],
        "cache_row_count": len(cache),
        "worker_pid": os.getpid(),
    })
    path = Path(payload["path"])
    _atomic_write_json(path, result)
    return {"path": str(path), "payload_digest": result["payload_digest"]}


def run_process_pool_transport_smoke(
    *,
    source: TraceNativeCompetenceOrganism,
    stream: DevelopmentStream,
    cache: Mapping[str, cache_api.CachedR0Observation],
    path: Path,
) -> dict[str, Any]:
    with ProcessPoolExecutor(max_workers=1, max_tasks_per_child=1) as executor:
        returned = executor.submit(_worker_transport_smoke, {
            "source": source,
            "stream": stream,
            "cache": dict(cache),
            "path": str(path),
        }).result()
    persisted = _load_self_digested(path)
    if returned["payload_digest"] != persisted["payload_digest"]:
        raise RuntimeError("worker transport smoke persistence mismatch")
    return persisted


def _valid_existing_seed(
    path: Path, *, expected_identity: str, expected_run_plan_sha256: str
) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = _load_self_digested(path)
    if payload.get("seed_identity") != expected_identity:
        raise RuntimeError(f"seed result identity mismatch: {path}")
    if payload.get("run_plan_sha256") != expected_run_plan_sha256:
        raise RuntimeError(f"seed result run-plan mismatch: {path}")
    return payload


def _hardware_manifest() -> dict[str, Any]:
    if sys.platform != "darwin":
        return {
            "mac_model": None,
            "mac_machine_name": None,
            "mac_chip": None,
            "physical_memory_label": None,
            "total_memory_bytes": None,
            "total_memory_gib": None,
        }
    try:
        payload = json.loads(subprocess.check_output(
            ["system_profiler", "SPHardwareDataType", "-json"],
            text=True,
            stderr=subprocess.DEVNULL,
        ))
        item = payload["SPHardwareDataType"][0]
        memory_label = item.get("physical_memory")
        total_memory = None
        if isinstance(memory_label, str):
            parts = memory_label.split()
            if len(parts) == 2 and parts[1].upper() == "GB":
                total_memory = int(float(parts[0]) * 1024 ** 3)
        return {
            "mac_model": item.get("machine_model"),
            "mac_machine_name": item.get("machine_name"),
            "mac_chip": item.get("chip_type"),
            "physical_memory_label": memory_label,
            "total_memory_bytes": total_memory,
            "total_memory_gib": (
                None if total_memory is None
                else total_memory / (1024.0 ** 3)
            ),
        }
    except (OSError, subprocess.CalledProcessError, KeyError, ValueError):
        return {
            "mac_model": None,
            "mac_machine_name": None,
            "mac_chip": None,
            "physical_memory_label": None,
            "total_memory_bytes": None,
            "total_memory_gib": None,
        }


def _environment_manifest(workers: int) -> dict[str, Any]:
    return {
        "machine": platform.machine(),
        "platform": platform.platform(),
        "macos_version": platform.mac_ver()[0],
        "python": sys.version,
        "python_executable": sys.executable,
        "logical_cpu_count": os.cpu_count(),
        **_hardware_manifest(),
        "workers": workers,
    }


def _phase1_performance_summary(
    phase1: Mapping[str, Any]
) -> dict[str, Any]:
    totals = {}
    curves = {}
    for mode in ARMS:
        rows_by_strategy = phase1["event_timings"][mode.value]
        totals[mode.value] = {}
        curves[mode.value] = {}
        for strategy, rows in rows_by_strategy.items():
            total = sum(float(row["wall_seconds"]) for row in rows)
            component_totals = {
                key: sum(
                    float(row["component_timing"][key]) for row in rows
                )
                for key in (
                    "event_wall_seconds",
                    "event_cpu_seconds",
                    "open_wall_seconds",
                    "mint_wall_seconds",
                    "deepcopy_wall_seconds",
                    "consume_in_place_wall_seconds",
                    "commit_wall_seconds",
                )
            }
            inclusive_attribution = {
                key: sum(
                    float(row["component_timing"][
                        "attribution_inclusive"
                    ][key])
                    for row in rows
                )
                for key in (
                    "graph_wall_seconds",
                    "graph_calls",
                    "live_graph_wall_seconds",
                    "live_graph_calls",
                    "replay_graph_wall_seconds",
                    "replay_graph_calls",
                    "full_invariant_inclusive_wall_seconds",
                    "full_invariant_calls",
                    "incremental_history_validator_inclusive_wall_seconds",
                    "incremental_history_validator_calls",
                    "ledger_replay_validator_inclusive_wall_seconds",
                    "ledger_replay_validator_calls",
                    "digest_wall_seconds",
                    "digest_calls",
                )
            }
            totals[mode.value][strategy] = {
                "outer_event_wall_seconds": total,
                "component_totals": component_totals,
                "inclusive_attribution_totals": inclusive_attribution,
                "categories_overlap": True,
            }
            curve = []
            for checkpoint in phase1["checkpoint_event_counts"]:
                window = [
                    float(row["wall_seconds"])
                    for row in rows
                    if checkpoint - 7
                    <= int(row["event_count_after"])
                    <= checkpoint
                ]
                curve.append({
                    "event_count": checkpoint,
                    "window_median_wall_seconds": (
                        statistics.median(window) if window else None
                    ),
                    "window_size": len(window),
                })
            curves[mode.value][strategy] = curve
        incremental_rows = rows_by_strategy["incremental"]
        legacy_rows = rows_by_strategy["legacy_full_replay"]
        compared_counts = {
            int(row["event_count_after"]) for row in legacy_rows
        }
        incremental_gate = sum(
            float(row["wall_seconds"])
            for row in incremental_rows
            if int(row["event_count_after"]) in compared_counts
        )
        legacy_gate = sum(float(row["wall_seconds"]) for row in legacy_rows)
        totals[mode.value]["exhaustive_gate_legacy_over_incremental_speedup"] = (
            legacy_gate / incremental_gate if incremental_gate else None
        )
        totals[mode.value]["speedup_comparison_event_counts"] = sorted(
            compared_counts
        )
    return {
        "event_wall_totals": totals,
        "checkpoint_window_curves": curves,
        "measured_not_remaining_time_estimates": True,
    }


def write_calibration_decision(
    *,
    output_dir: Path,
    input_identity: Mapping[str, Any],
    phase1: Mapping[str, Any],
) -> dict[str, Any]:
    path = output_dir / "calibration_decision.json"
    if path.exists():
        existing = _load_self_digested(path)
        if existing.get("input_identity_sha256") != input_identity[
            "input_identity_sha256"
        ]:
            raise RuntimeError("calibration decision identity mismatch")
        return existing
    if (
        phase1.get("status") != "PASSED"
        or int(phase1.get("maximum_events", -1)) != 256
    ):
        raise RuntimeError("calibration requires passing 256-event Phase 1")
    event_seconds = sum(
        float(row["component_timing"]["event_wall_seconds"])
        for mode in ARMS
        for row in phase1["event_timings"][mode.value]["incremental"]
    )
    structural_seconds = sum(
        float(phase1["structural"][mode.value][
            "incremental_wall_seconds"
        ])
        for mode in ARMS
    )
    final_boundary_seconds = sum(
        float(phase1["checkpoints"]["256"][mode.value][
            "incremental_boundary_wall_seconds"
        ])
        for mode in ARMS
    )
    serialization_seconds = sum(
        float(phase1["midpoint_serialization_restoration"][mode.value][
            "incremental"
        ]["serialization_wall_seconds"])
        + float(phase1["midpoint_serialization_restoration"][mode.value][
            "incremental"
        ]["restoration_wall_seconds"])
        for mode in ARMS
    )
    evaluation_seconds = sum(
        float(phase1["sealed_evaluation"][mode.value][
            "strategy_wall_seconds"
        ]["incremental"])
        for mode in ARMS
    )
    component_seconds = {
        "initialization": float(phase1["initialization_wall_seconds"]),
        "incremental_events_all_arms": event_seconds,
        "incremental_structural_successor_all_arms": structural_seconds,
        "final_full_boundaries_all_arms": final_boundary_seconds,
        "midpoint_serialization_restoration_proxy_all_arms": (
            serialization_seconds
        ),
        "sealed_evaluation_all_arms": evaluation_seconds,
    }
    per_seed_seconds = sum(component_seconds.values())
    headroom_factor = 1.25
    forecasts = [
        {
            "cohort_size": cohort_size,
            "workers": 1,
            "projected_hours_without_headroom": (
                per_seed_seconds * cohort_size / 3600.0
            ),
            "projected_hours_with_headroom": (
                per_seed_seconds * cohort_size * headroom_factor / 3600.0
            ),
        }
        for cohort_size in (2, 4, 8)
    ]
    eligible = [
        item for item in forecasts
        if item["projected_hours_with_headroom"] <= 10.0
    ]
    if not eligible:
        raise RuntimeError(
            "one-worker Phase 1 projection cannot bound even two seeds to "
            "10 hours; explicit 1/2/4 worker calibration is required"
        )
    selected = max(eligible, key=lambda item: item["cohort_size"])
    decision = _self_digest({
        "schema_version": SCHEMA_VERSION,
        "status": "CALIBRATED",
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "input_identity_sha256": input_identity["input_identity_sha256"],
        "phase1_payload_digest": phase1["payload_digest"],
        "phase1_component_seconds": component_seconds,
        "phase1_incremental_seed_proxy_seconds": per_seed_seconds,
        "headroom_factor": headroom_factor,
        "forecasts": forecasts,
        "selected_cohort_size": selected["cohort_size"],
        "selected_workers": 1,
        "projected_hours_without_headroom": selected[
            "projected_hours_without_headroom"
        ],
        "projected_hours_with_headroom": selected[
            "projected_hours_with_headroom"
        ],
        "worker_selection_basis": (
            "one worker already yields the largest admissible cohort under "
            "the 10-hour headroom bound, so a contention-producing 1/2/4 "
            "worker calibration was unnecessary"
        ),
        "projection_limitations": (
            "midpoint serialization/restoration proxies final history, and "
            "the 25% headroom covers that difference plus process startup, "
            "payload transfer, scheduling, and instrumentation overhead"
        ),
        "created_at": _utc_now(),
    })
    _atomic_write_json(path, decision)
    return decision


def _invocation_history(output_dir: Path) -> list[dict[str, Any]]:
    directory = output_dir / "invocations"
    if not directory.exists():
        return []
    return sorted(
        (_load_self_digested(path) for path in directory.glob("*.json")),
        key=lambda item: (item["started_at"], item["invocation_id"]),
    )


def _compact_seed_aggregates(
    seeds: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    completed = [row for row in seeds if row["status"] == "COMPLETED"]
    seed_runtime = [
        {
            "ordinal": row["ordinal"],
            "wall_seconds": row["wall_seconds"],
            "cpu_seconds": row["cpu_seconds"],
            "peak_rss_mib": row["peak_rss_mib"],
            "completion_invocation_id": row["completion_invocation_id"],
            "resumed_from_invocation_ids": row[
                "resumed_from_invocation_ids"
            ],
        }
        for row in completed
    ]
    arms: dict[str, Any] = {}
    for mode in ARMS:
        exclusive_keys = {
            "open": "open_wall_seconds",
            "mint": "mint_wall_seconds",
            "whole_organism_deepcopy": "deepcopy_wall_seconds",
            "consume_in_place": "consume_in_place_wall_seconds",
            "commit": "commit_wall_seconds",
        }
        totals = {key: 0.0 for key in exclusive_keys}
        mechanism_rows = []
        checkpoint_values = {item: [] for item in CHECKPOINTS}
        for seed in completed:
            arm = seed["arms"][mode.value]
            component = arm["timing_summary"]["totals"]
            for label, key in exclusive_keys.items():
                totals[label] += float(component[key])
            mechanisms = arm["mechanisms"]
            mechanism_rows.append({
                "ordinal": seed["ordinal"],
                "candidates": mechanisms["candidate_count_after_discovery"],
                "shadows": mechanisms["dormant_mixed_shadow_count"],
                "parent_contradiction_events": mechanisms[
                    "parent_contradiction_event_count"
                ],
                "requests": mechanisms["specialization_request_count"],
                "children": mechanisms["children_born_count"],
                "certification_events": len(
                    mechanisms["certification_events"]
                ),
                "revocation_events": len(mechanisms["revocation_events"]),
                "true_positives": mechanisms["sealed_metrics"][
                    "raw_true_positives"
                ],
                "false_positives": mechanisms["sealed_metrics"][
                    "raw_false_positives"
                ],
                "abstentions": mechanisms["sealed_metrics"]["abstentions"],
                "positive_coverage": mechanisms["sealed_metrics"][
                    "safe_positive_coverage"
                ],
                "final_safe_cells": len(mechanisms["final_safe_cell_ids"]),
                "final_selective_cells": len(
                    mechanisms["final_selective_cell_ids"]
                ),
            })
            for point in arm["timing_summary"]["checkpoint_curve"]:
                checkpoint_values[int(point["event_count"])].append(
                    float(point["event_wall_seconds"])
                )
        ranking = sorted(
            (
                {"component": key, "wall_seconds": value}
                for key, value in totals.items()
            ),
            key=lambda item: (-item["wall_seconds"], item["component"]),
        )
        curve = [
            {
                "event_count": checkpoint,
                "median_event_wall_seconds": (
                    statistics.median(values) if values else None
                ),
                "seed_count": len(values),
            }
            for checkpoint, values in checkpoint_values.items()
        ]
        first = next(
            (row["median_event_wall_seconds"] for row in curve
             if row["event_count"] == 32),
            None,
        )
        last = next(
            (row["median_event_wall_seconds"] for row in curve
             if row["event_count"] == 256),
            None,
        )
        exponent = (
            None
            if first in {None, 0.0} or last in {None, 0.0}
            else math.log(last / first) / math.log(8.0)
        )
        arms[mode.value] = {
            "exclusive_component_totals": totals,
            "exclusive_component_ranking": ranking,
            "dominant_exclusive_component": (
                None if not ranking else ranking[0]["component"]
            ),
            "per_event_checkpoint_curve": curve,
            "per_event_power_exponent_32_to_256": exponent,
            "growth_interpretation": (
                "insufficient"
                if exponent is None
                else (
                    "per_event_cost_increases_materially_with_history"
                    if exponent > 0.25
                    else "per_event_cost_approximately_flat_or_weakly_growing"
                )
            ),
            "mechanism_rows": mechanism_rows,
        }
    return {"seed_runtime": seed_runtime, "arms": arms}


def _cohort_summary(
    *,
    output_dir: Path,
    input_identity: Mapping[str, Any],
    run_plan: Mapping[str, Any],
    phase1: Mapping[str, Any],
) -> dict[str, Any]:
    cohort_size = int(run_plan["cohort_size"])
    workers = int(run_plan["workers"])
    seeds = []
    for ordinal in range(1, cohort_size + 1):
        seed = development_seed(ordinal)
        path = _seed_result_path(output_dir, ordinal)
        payload = _valid_existing_seed(
            path,
            expected_identity=_seed_identity(
                input_identity,
                ordinal=ordinal,
                seed=seed,
                run_plan_sha256=run_plan["run_plan_sha256"],
            ),
            expected_run_plan_sha256=run_plan["run_plan_sha256"],
        )
        if payload is not None:
            seeds.append(payload)
    completed = [row for row in seeds if row["status"] == "COMPLETED"]
    mean_wall = (
        statistics.fmean(float(row["wall_seconds"]) for row in completed)
        if completed else None
    )
    invocations = _invocation_history(output_dir)
    cohort_elapsed = sum(
        float(item["elapsed_wall_seconds"]) for item in invocations
    )
    estimated_32 = (
        None
        if not completed or not cohort_elapsed
        else cohort_elapsed / len(completed) * 32 / 3600.0
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": (
            "COMPLETED"
            if len(completed) == cohort_size
            else "IN_PROGRESS_OR_FAILED"
        ),
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "source_commit": SOURCE_COMMIT,
        "input_identity_sha256": input_identity["input_identity_sha256"],
        "run_plan": dict(run_plan),
        "invocation_history": invocations,
        "cohort_ordinals": run_plan["cohort_ordinals"],
        "cohort_genome_seeds": run_plan["cohort_genome_seeds"],
        "cohort_size": cohort_size,
        "workers": workers,
        "completed_ordinals": sorted(int(row["ordinal"]) for row in completed),
        "failed_ordinals": sorted(
            int(row["ordinal"]) for row in seeds if row["status"] == "FAILED"
        ),
        "seed_result_digests": {
            str(row["ordinal"]): row["payload_digest"] for row in seeds
        },
        "environment": _environment_manifest(workers),
        "phase1_performance": _phase1_performance_summary(phase1),
        "mean_completed_seed_wall_seconds": mean_wall,
        "observed_cohort_invocation_wall_seconds": cohort_elapsed,
        "software_estimate_32_seed_wall_hours_at_same_throughput": estimated_32,
        "software_estimate_basis": (
            "sum of observed cohort invocation wall divided by completed "
            "seeds, multiplied by 32; includes startup, payload transfer, "
            "scheduling, and the frozen worker plan; not a scientific or "
            "remaining-time estimate"
        ),
        "compact_aggregates": _compact_seed_aggregates(seeds),
        "updated_at": _utc_now(),
    }
    return _self_digest(summary)


def run_cohort(
    *,
    output_dir: Path,
    source: TraceNativeCompetenceOrganism,
    stream: DevelopmentStream,
    cache: Mapping[str, cache_api.CachedR0Observation],
    input_identity: Mapping[str, Any],
    phase1: Mapping[str, Any],
    calibration_decision: Mapping[str, Any],
    cohort_size: int,
    workers: int,
) -> dict[str, Any]:
    if phase1.get("status") != "PASSED":
        raise RuntimeError("cohort forbidden before a passing Phase 1 gate")
    if phase1.get("input_identity_sha256") != input_identity[
        "input_identity_sha256"
    ]:
        raise RuntimeError("Phase 1 input identity mismatch")
    if (
        int(phase1.get("maximum_events", -1)) != 256
        or not phase1.get("midpoint_serialization_restoration")
    ):
        raise RuntimeError("cohort requires complete 256-event Phase 1 parity")
    if (
        calibration_decision.get("status") != "CALIBRATED"
        or calibration_decision.get("input_identity_sha256")
        != input_identity["input_identity_sha256"]
    ):
        raise RuntimeError("cohort requires a bound calibration decision")
    if cohort_size not in {2, 4, 8}:
        raise ValueError("cohort size must be 2, 4, or 8")
    if workers not in {1, 2, 4} or workers > cohort_size:
        raise ValueError("workers must be 1, 2, or 4 and no larger than cohort")
    if (
        int(calibration_decision["selected_cohort_size"]) != cohort_size
        or int(calibration_decision["selected_workers"]) != workers
    ):
        raise RuntimeError("requested cohort differs from calibration decision")
    if float(calibration_decision["projected_hours_with_headroom"]) > 10.0:
        raise RuntimeError("calibrated cohort projection exceeds 10 hours")
    run_plan = _load_or_create_run_plan(
        output_dir=output_dir,
        input_identity=input_identity,
        cohort_size=cohort_size,
        workers=workers,
        calibration_decision_sha256=calibration_decision["payload_digest"],
    )
    invocation_id = uuid.uuid4().hex
    invocation_started_at = _utc_now()
    invocation_wall_started = time.perf_counter()
    pending = []
    interrupted = []
    for ordinal in range(1, cohort_size + 1):
        seed = development_seed(ordinal)
        identity = _seed_identity(
            input_identity,
            ordinal=ordinal,
            seed=seed,
            run_plan_sha256=run_plan["run_plan_sha256"],
        )
        result_path = _seed_result_path(output_dir, ordinal)
        existing = _valid_existing_seed(
            result_path,
            expected_identity=identity,
            expected_run_plan_sha256=run_plan["run_plan_sha256"],
        )
        if existing is not None:
            if existing["status"] == "FAILED":
                raise RuntimeError(
                    f"retained seed {ordinal} has terminal failure: "
                    f"{existing.get('error')}"
                )
            if existing["status"] == "COMPLETED":
                continue
        prior_invocations = _prior_start_invocations(output_dir, ordinal)
        if prior_invocations:
            interrupted.append(ordinal)
        pending.append({
            "output_dir": str(output_dir),
            "ordinal": ordinal,
            "seed": seed,
            "seed_identity": identity,
            "run_plan_sha256": run_plan["run_plan_sha256"],
            "invocation_id": invocation_id,
            "resumed_from_invocation_ids": list(prior_invocations),
            "source": source,
            "stream": stream,
            "cache": dict(cache),
        })

    summary_path = output_dir / "benchmark.json"
    scheduled_ordinals = [int(item["ordinal"]) for item in pending]
    completed_this_invocation: list[int] = []
    failed_this_invocation: list[int] = []
    _write_invocation(
        output_dir=output_dir,
        invocation_id=invocation_id,
        run_plan_sha256=run_plan["run_plan_sha256"],
        status="STARTED" if pending else "NOOP_ALREADY_COMPLETED",
        started_at=invocation_started_at,
        elapsed_wall_seconds=0.0,
        scheduled_ordinals=scheduled_ordinals,
        interrupted_ordinals=interrupted,
        completed_this_invocation=completed_this_invocation,
        failed_this_invocation=failed_this_invocation,
    )
    initial = _cohort_summary(
        output_dir=output_dir,
        input_identity=input_identity,
        run_plan=run_plan,
        phase1=phase1,
    )
    _atomic_write_json(summary_path, initial)
    failures = []
    if pending:
        with ProcessPoolExecutor(
            max_workers=workers, max_tasks_per_child=1
        ) as executor:
            futures = [executor.submit(_run_seed_worker, item) for item in pending]
            for future in as_completed(futures):
                outcome = future.result()
                if outcome["status"] != "COMPLETED":
                    failures.append(outcome)
                    failed_this_invocation.append(int(outcome["ordinal"]))
                else:
                    completed_this_invocation.append(int(outcome["ordinal"]))
                _write_invocation(
                    output_dir=output_dir,
                    invocation_id=invocation_id,
                    run_plan_sha256=run_plan["run_plan_sha256"],
                    status="RUNNING",
                    started_at=invocation_started_at,
                    elapsed_wall_seconds=(
                        time.perf_counter() - invocation_wall_started
                    ),
                    scheduled_ordinals=scheduled_ordinals,
                    interrupted_ordinals=interrupted,
                    completed_this_invocation=completed_this_invocation,
                    failed_this_invocation=failed_this_invocation,
                )
                summary = _cohort_summary(
                    output_dir=output_dir,
                    input_identity=input_identity,
                    run_plan=run_plan,
                    phase1=phase1,
                )
                _atomic_write_json(summary_path, summary)
    _write_invocation(
        output_dir=output_dir,
        invocation_id=invocation_id,
        run_plan_sha256=run_plan["run_plan_sha256"],
        status="FAILED" if failures else "COMPLETED",
        started_at=invocation_started_at,
        elapsed_wall_seconds=time.perf_counter() - invocation_wall_started,
        scheduled_ordinals=scheduled_ordinals,
        interrupted_ordinals=interrupted,
        completed_this_invocation=completed_this_invocation,
        failed_this_invocation=failed_this_invocation,
    )
    _atomic_write_json(
        summary_path,
        _cohort_summary(
            output_dir=output_dir,
            input_identity=input_identity,
            run_plan=run_plan,
            phase1=phase1,
        ),
    )
    final = _load_self_digested(summary_path)
    if failures or final["status"] != "COMPLETED":
        raise RuntimeError(f"development cohort did not complete: {failures}")
    return final


def _phase1_checkpoint_path(output_dir: Path, event_count: int) -> Path:
    if event_count not in CHECKPOINTS:
        raise ValueError("unknown Phase 1 checkpoint")
    return output_dir / "phase1_checkpoints" / f"{event_count:03d}.json"


def _serialize_phase1_strategies(
    strategies: Mapping[
        SpecializationMode, Mapping[str, NativeProspectiveAuthorityV2]
    ],
    *,
    expected_event_count: int,
    budget: _Phase1Budget | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    encoded: dict[str, Any] = {}
    timings: dict[str, Any] = {}
    for mode in ARMS:
        encoded[mode.value] = {}
        timings[mode.value] = {}
        pair_manifests = []
        for strategy in PHASE1_STRATEGIES:
            if strategy not in strategies[mode]:
                continue
            if budget is not None:
                budget.check(
                    f"checkpoint-state-{mode.value}-{strategy}-before"
                )
            authority = strategies[mode][strategy]
            if _history_event_count(authority) != expected_event_count:
                raise RuntimeError(
                    "checkpoint state has the wrong history length"
                )
            manifest = authority.continuation_manifest()
            pair_manifests.append(manifest)
            dump_started = time.perf_counter()
            payload = authority.dumps()
            dump_seconds = time.perf_counter() - dump_started
            load_started = time.perf_counter()
            restored = NativeProspectiveAuthorityV2.loads(payload)
            load_seconds = time.perf_counter() - load_started
            if restored.continuation_manifest() != manifest:
                raise RuntimeError(
                    "persisted Phase 1 checkpoint failed roundtrip parity"
                )
            expected_mode = (
                HISTORY_VALIDATION_INCREMENTAL
                if strategy == "incremental"
                else HISTORY_VALIDATION_LEGACY
            )
            if restored._history_validation_mode != expected_mode:
                raise RuntimeError(
                    "persisted Phase 1 checkpoint changed validation mode"
                )
            encoded[mode.value][strategy] = {
                "encoding": "base64",
                "payload_bytes": len(payload),
                "payload_sha256": hashlib.sha256(payload).hexdigest(),
                "payload_base64": base64.b64encode(payload).decode("ascii"),
            }
            timings[mode.value][strategy] = {
                "payload_bytes": len(payload),
                "serialization_wall_seconds": dump_seconds,
                "restoration_wall_seconds": load_seconds,
                "roundtrip_exact": True,
            }
            if budget is not None:
                budget.check(
                    f"checkpoint-state-{mode.value}-{strategy}-after"
                )
        if len(pair_manifests) == 2 and pair_manifests[0] != pair_manifests[1]:
            raise RuntimeError(
                "incremental and legacy checkpoint states differ"
            )
        if "incremental" not in encoded[mode.value]:
            raise RuntimeError("checkpoint omitted incremental continuation")
    return encoded, timings


def _restore_phase1_strategies(
    checkpoint: Mapping[str, Any],
    *,
    expected_event_count: int,
) -> dict[SpecializationMode, dict[str, NativeProspectiveAuthorityV2]]:
    restored: dict[
        SpecializationMode, dict[str, NativeProspectiveAuthorityV2]
    ] = {}
    for mode in ARMS:
        pair: dict[str, NativeProspectiveAuthorityV2] = {}
        manifests = []
        for strategy in PHASE1_STRATEGIES:
            if strategy not in checkpoint["authority_states"][mode.value]:
                continue
            item = checkpoint["authority_states"][mode.value][strategy]
            if item.get("encoding") != "base64":
                raise RuntimeError("unsupported Phase 1 checkpoint encoding")
            try:
                payload = base64.b64decode(
                    item["payload_base64"], validate=True
                )
            except (TypeError, ValueError) as exc:
                raise RuntimeError(
                    "invalid Phase 1 checkpoint payload encoding"
                ) from exc
            if (
                len(payload) != int(item["payload_bytes"])
                or hashlib.sha256(payload).hexdigest()
                != item["payload_sha256"]
            ):
                raise RuntimeError("Phase 1 checkpoint payload mismatch")
            authority = NativeProspectiveAuthorityV2.loads(payload)
            if _history_event_count(authority) != expected_event_count:
                raise RuntimeError("Phase 1 checkpoint history mismatch")
            expected_mode = (
                HISTORY_VALIDATION_INCREMENTAL
                if strategy == "incremental"
                else HISTORY_VALIDATION_LEGACY
            )
            if authority._history_validation_mode != expected_mode:
                raise RuntimeError(
                    "Phase 1 checkpoint validation mode mismatch"
                )
            pair[strategy] = authority
            manifests.append(authority.continuation_manifest())
        if len(manifests) == 2 and manifests[0] != manifests[1]:
            raise RuntimeError(
                "restored incremental and legacy checkpoint states differ"
            )
        if "incremental" not in pair:
            raise RuntimeError("checkpoint has no incremental continuation")
        restored[mode] = pair
    return restored


def _load_phase1_checkpoint(
    output_dir: Path,
    *,
    event_count: int,
    input_identity_sha256: str,
) -> dict[str, Any]:
    path = _phase1_checkpoint_path(output_dir, event_count)
    if not path.exists():
        raise RuntimeError(
            f"Phase 1 checkpoint {event_count} is absent; run its explicit "
            "preceding stage first"
        )
    checkpoint = _load_self_digested(path)
    if checkpoint.get("schema_version") != PHASE1_CHECKPOINT_SCHEMA:
        raise RuntimeError("Phase 1 checkpoint schema mismatch")
    if checkpoint.get("status") != "PASSED":
        raise RuntimeError("Phase 1 checkpoint is not passing")
    if checkpoint.get("input_identity_sha256") != input_identity_sha256:
        raise RuntimeError("Phase 1 checkpoint input identity mismatch")
    if int(checkpoint.get("checkpoint_event_count", -1)) != event_count:
        raise RuntimeError("Phase 1 checkpoint event-count mismatch")
    return checkpoint


def _phase1_claim_scope(completed: Sequence[int]) -> dict[str, Any]:
    ordered = sorted(int(item) for item in completed)
    maximum = ordered[-1]
    return {
        "per_event_legacy_incremental_exact_parity": {
            "covered_event_range_inclusive": [
                1,
                EXHAUSTIVE_PARITY_GATE_EVENTS,
            ],
            "basis": (
                "literal transaction, semantic trace, receipt, emission, "
                "actual outcome, and complete continuation-manifest equality "
                "after every covered event"
            ),
            "not_claimed_after_event": EXHAUSTIVE_PARITY_GATE_EVENTS,
        },
        "incremental_execution": {
            "covered_event_range_inclusive": [1, maximum],
            "post_gate_per_event_legacy_comparator_run": False,
        },
        "full_history_boundary_reconstruction": {
            "covered_event_counts": ordered,
            "basis": (
                "each persisted incremental state passed exact accepted-ledger "
                "reconstruction; a legacy-validation clone produced an "
                "identical checkpoint projection"
            ),
            "independently_evolved_legacy_state_compared_at": [
                EXHAUSTIVE_PARITY_GATE_EVENTS
            ],
        },
        "unexecuted_events_not_claimed": (
            [] if maximum == CHECKPOINTS[-1]
            else [maximum + 1, CHECKPOINTS[-1]]
        ),
        "checkpoint_success_does_not_imply_per_event_strategy_parity": True,
        "scientific_claim_permitted": False,
    }


def _build_phase1_index(
    *,
    output_dir: Path,
    input_identity_sha256: str,
    maximum_events: int,
) -> dict[str, Any]:
    completed = [item for item in CHECKPOINTS if item <= maximum_events]
    checkpoints = [
        _load_phase1_checkpoint(
            output_dir,
            event_count=item,
            input_identity_sha256=input_identity_sha256,
        )
        for item in completed
    ]
    previous_digest = None
    for expected_previous, checkpoint in zip((0, *completed[:-1]), checkpoints):
        if int(checkpoint["previous_checkpoint_event_count"]) != expected_previous:
            raise RuntimeError("Phase 1 checkpoint chain is not contiguous")
        if checkpoint.get("previous_checkpoint_payload_digest") != previous_digest:
            raise RuntimeError("Phase 1 checkpoint predecessor digest mismatch")
        previous_digest = checkpoint["payload_digest"]

    stage_results = [item["stage_result"] for item in checkpoints]
    timings = {
        mode.value: {strategy: [] for strategy in PHASE1_STRATEGIES}
        for mode in ARMS
    }
    boundary_evidence: dict[str, Any] = {}
    structural: dict[str, Any] = {}
    midpoint: dict[str, Any] = {}
    history_zero = None
    history_128 = None
    for result in stage_results:
        for mode in ARMS:
            for strategy in PHASE1_STRATEGIES:
                timings[mode.value][strategy].extend(
                    result["event_timings"][mode.value][strategy]
                )
        boundary_evidence.update(result["checkpoints"])
        structural.update(result["structural"])
        midpoint.update(result["midpoint_serialization_restoration"])
        differential = result["profiled_consume_public_differential"]
        history_zero = differential["history_zero"] or history_zero
        history_128 = (
            differential["history_128_after_structural_growth"]
            or history_128
        )
    latest = stage_results[-1]
    peak_index = max(
        range(len(stage_results)),
        key=lambda index: float(stage_results[index]["peak_rss_mib"]),
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "phase": "phase1_staged_exact_parity",
        "status": "PASSED",
        "coverage_status": (
            "COMPLETE_256_EVENT_WITH_32_EVENT_EXHAUSTIVE_GATE"
            if maximum_events == CHECKPOINTS[-1]
            else "BOUNDED_32_EVENT_GATE_WITH_EXPLICIT_BOUNDARIES"
        ),
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "source_commit": SOURCE_COMMIT,
        "input_identity_sha256": input_identity_sha256,
        "stream_sha256": latest["stream_sha256"],
        "genome_seed": latest["genome_seed"],
        "maximum_events": maximum_events,
        "checkpoint_event_counts": completed,
        "explicit_continuation_required_for_next_checkpoint": (
            maximum_events != CHECKPOINTS[-1]
        ),
        "next_checkpoint_event_count": (
            None
            if maximum_events == CHECKPOINTS[-1]
            else CHECKPOINTS[CHECKPOINTS.index(maximum_events) + 1]
        ),
        "claim_scope": _phase1_claim_scope(completed),
        "both_authorities_remained_prospective_through_exhaustive_gate": True,
        "exhaustive_gate_only_validation_strategy_varied": True,
        "post_gate_single_incremental_path": maximum_events > 32,
        "profiled_consume_public_differential": {
            "history_zero": history_zero,
            "history_128_after_structural_growth": history_128,
        },
        "discovery": checkpoints[0]["discovery"],
        "initialization_wall_seconds": sum(
            float(item["initialization_wall_seconds"])
            for item in stage_results
        ),
        "structural": structural,
        "checkpoints": boundary_evidence,
        "midpoint_serialization_restoration": midpoint,
        "sealed_evaluation": latest["sealed_evaluation"],
        "sealed_evaluation_claim": (
            (
                "exact incremental/legacy evaluation parity"
                if maximum_events == EXHAUSTIVE_PARITY_GATE_EVENTS
                else "incremental evaluation after exact boundary reconstruction"
            )
            + f" at the {maximum_events}-event persisted boundary only"
        ),
        "event_timings": timings,
        "timing_order_alternated": True,
        "timings_exclude_manifest_comparisons": True,
        "event_component_timings_instrumented": True,
        "started_at": stage_results[0]["started_at"],
        "finished_at": latest["finished_at"],
        "wall_seconds": sum(float(item["wall_seconds"]) for item in stage_results),
        "cpu_seconds": sum(float(item["cpu_seconds"]) for item in stage_results),
        "peak_rss_mib": stage_results[peak_index]["peak_rss_mib"],
        "peak_rss_basis": stage_results[peak_index]["peak_rss_basis"],
        "stage_checkpoint_files": [
            str(_phase1_checkpoint_path(output_dir, item))
            for item in completed
        ],
        "stage_checkpoint_payload_digests": {
            str(item["checkpoint_event_count"]): item["payload_digest"]
            for item in checkpoints
        },
        "latest_checkpoint_payload_digest": checkpoints[-1]["payload_digest"],
        "updated_at": _utc_now(),
    }
    return _self_digest(result)


def _write_phase1_attempt_failure(
    *,
    output_dir: Path,
    invocation_id: str,
    input_identity_sha256: str,
    previous_event_count: int,
    target_event_count: int,
    max_wall_seconds: float,
    max_peak_rss_mib: float,
    exc: Exception,
) -> None:
    status = (
        "CEILING_EXCEEDED"
        if isinstance(exc, Phase1CeilingExceeded)
        else "FAILED"
    )
    payload = _self_digest({
        "schema_version": SCHEMA_VERSION,
        "phase": "phase1_stage_attempt",
        "status": status,
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "source_commit": SOURCE_COMMIT,
        "input_identity_sha256": input_identity_sha256,
        "invocation_id": invocation_id,
        "previous_checkpoint_event_count": previous_event_count,
        "target_checkpoint_event_count": target_event_count,
        "max_wall_seconds": max_wall_seconds,
        "max_peak_rss_mib": max_peak_rss_mib,
        "prior_atomic_checkpoint_preserved": True,
        "partial_in_memory_state_resumable": False,
        "error_type": type(exc).__name__,
        "error": str(exc),
        "failed_at": _utc_now(),
    })
    _atomic_write_json(
        output_dir / "phase1_attempts" / f"{invocation_id}.json",
        payload,
    )


def _write_phase1_stage(
    *,
    output_dir: Path,
    source: TraceNativeCompetenceOrganism,
    stream: DevelopmentStream,
    cache: Mapping[str, cache_api.CachedR0Observation],
    input_identity: Mapping[str, Any],
    target_event_count: int,
    continuing: bool,
    max_wall_seconds: float,
    max_peak_rss_mib: float,
) -> dict[str, Any]:
    if target_event_count not in CHECKPOINTS:
        raise ValueError("unknown Phase 1 target checkpoint")
    target_index = CHECKPOINTS.index(target_event_count)
    previous_event_count = 0 if target_index == 0 else CHECKPOINTS[target_index - 1]
    if continuing != (previous_event_count != 0):
        raise ValueError(
            "use --phase1 only for the 32-event gate and "
            "--continue-phase1-to for every later stage"
        )
    identity_sha256 = str(input_identity["input_identity_sha256"])
    target_path = _phase1_checkpoint_path(output_dir, target_event_count)
    if target_path.exists():
        _load_phase1_checkpoint(
            output_dir,
            event_count=target_event_count,
            input_identity_sha256=identity_sha256,
        )
        latest_event_count = max(
            item
            for item in CHECKPOINTS
            if _phase1_checkpoint_path(output_dir, item).exists()
        )
        index = _build_phase1_index(
            output_dir=output_dir,
            input_identity_sha256=identity_sha256,
            maximum_events=latest_event_count,
        )
        _atomic_write_json(output_dir / "phase1_parity.json", index)
        return index

    previous_checkpoint = None
    previous_digest = None
    starting_strategies = None
    starting_discovery = None
    if previous_event_count:
        previous_checkpoint = _load_phase1_checkpoint(
            output_dir,
            event_count=previous_event_count,
            input_identity_sha256=identity_sha256,
        )
        previous_digest = previous_checkpoint["payload_digest"]
        starting_discovery = previous_checkpoint["discovery"]

    invocation_id = uuid.uuid4().hex
    try:
        with _phase1_wall_budget(
            max_wall_seconds=max_wall_seconds,
            max_peak_rss_mib=max_peak_rss_mib,
        ) as budget:
            if previous_checkpoint is not None:
                budget.check("checkpoint-restoration-before")
                starting_strategies = _restore_phase1_strategies(
                    previous_checkpoint,
                    expected_event_count=previous_event_count,
                )
                budget.check("checkpoint-restoration-after")
            result, strategies = _run_phase1_stage(
                source=source,
                stream=stream,
                cache=cache,
                maximum_events=target_event_count,
                starting_event=previous_event_count,
                starting_strategies=starting_strategies,
                starting_discovery=starting_discovery,
                budget=budget,
            )
            authority_states, state_roundtrip = (
                _serialize_phase1_strategies(
                    {
                        mode: {
                            "incremental": strategies[mode]["incremental"]
                        }
                        for mode in ARMS
                    },
                    expected_event_count=target_event_count,
                    budget=budget,
                )
            )
            result["persisted_state_roundtrip"] = state_roundtrip
            checkpoint = _self_digest({
                "schema_version": PHASE1_CHECKPOINT_SCHEMA,
                "phase": "phase1_atomic_checkpoint",
                "status": "PASSED",
                "label": DEVELOPMENT_LABEL,
                "scientific_use_permitted": False,
                "source_commit": SOURCE_COMMIT,
                "input_identity_sha256": identity_sha256,
                "stream_sha256": stream.manifest["stream_sha256"],
                "checkpoint_event_count": target_event_count,
                "previous_checkpoint_event_count": previous_event_count,
                "previous_checkpoint_payload_digest": previous_digest,
                "continuation_is_explicit": True,
                "claim_scope": result["claim_scope"],
                "discovery": result["discovery"],
                "stage_result": result,
                "authority_states": authority_states,
                "created_at": _utc_now(),
            })
            budget.check(f"checkpoint-{target_event_count}-persist-before")
            _atomic_write_json(target_path, checkpoint)
    except Exception as exc:
        _write_phase1_attempt_failure(
            output_dir=output_dir,
            invocation_id=invocation_id,
            input_identity_sha256=identity_sha256,
            previous_event_count=previous_event_count,
            target_event_count=target_event_count,
            max_wall_seconds=max_wall_seconds,
            max_peak_rss_mib=max_peak_rss_mib,
            exc=exc,
        )
        raise
    index = _build_phase1_index(
        output_dir=output_dir,
        input_identity_sha256=identity_sha256,
        maximum_events=target_event_count,
    )
    _atomic_write_json(output_dir / "phase1_parity.json", index)
    return index


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare-only", action="store_true")
    action.add_argument(
        "--phase1",
        action="store_true",
        help="run or reuse only the exhaustive 32-event parity gate",
    )
    action.add_argument(
        "--continue-phase1-to",
        type=int,
        choices=CHECKPOINTS[1:],
        metavar="{64,128,256}",
        help=(
            "continue from the immediately preceding atomic Phase-1 "
            "checkpoint"
        ),
    )
    action.add_argument("--calibrate", action="store_true")
    action.add_argument("--run-cohort", action="store_true")
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR
    )
    parser.add_argument(
        "--max-wall-seconds",
        type=float,
        default=DEFAULT_PHASE1_WALL_CEILING_SECONDS,
        help="hard wall ceiling for one Phase-1 stage (default: 7200)",
    )
    parser.add_argument(
        "--max-peak-rss-mib",
        type=float,
        default=DEFAULT_PHASE1_PEAK_RSS_CEILING_MIB,
        help=(
            "peak-RSS ceiling checked at safe operation boundaries "
            "(default: 8192)"
        ),
    )
    parser.add_argument("--cohort-size", type=int, choices=(2, 4, 8))
    parser.add_argument("--workers", type=int, choices=(1, 2, 4))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    args.output_dir = _guard_output_dir(args.output_dir)
    _verify_audited_source_revision()
    _verify_tracked_dependencies_clean()
    source, stream, cache, input_identity = prepare_development_inputs(
        args.output_dir
    )
    if args.prepare_only:
        print(json.dumps({
            "status": "PREPARED",
            "label": DEVELOPMENT_LABEL,
            "input_identity_sha256": input_identity[
                "input_identity_sha256"
            ],
            "stream_sha256": stream.manifest["stream_sha256"],
            "row_count": len(stream.rows),
            "output_dir": str(args.output_dir),
        }, sort_keys=True))
        return 0
    if args.phase1 or args.continue_phase1_to is not None:
        target_event_count = (
            CHECKPOINTS[0]
            if args.phase1
            else int(args.continue_phase1_to)
        )
        phase1 = _write_phase1_stage(
            output_dir=args.output_dir,
            source=source,
            stream=stream,
            cache=cache,
            input_identity=input_identity,
            target_event_count=target_event_count,
            continuing=not args.phase1,
            max_wall_seconds=args.max_wall_seconds,
            max_peak_rss_mib=args.max_peak_rss_mib,
        )
        print(json.dumps({
            "status": phase1["status"],
            "coverage_status": phase1["coverage_status"],
            "phase1_path": str(args.output_dir / "phase1_parity.json"),
            "wall_seconds": phase1["wall_seconds"],
            "maximum_events": phase1["maximum_events"],
            "next_checkpoint_event_count": phase1[
                "next_checkpoint_event_count"
            ],
        }, sort_keys=True))
        return 0
    phase1_path = args.output_dir / "phase1_parity.json"
    if not phase1_path.exists():
        raise RuntimeError("Phase 1 result is absent")
    phase1 = _load_self_digested(phase1_path)
    if args.calibrate:
        decision = write_calibration_decision(
            output_dir=args.output_dir,
            input_identity=input_identity,
            phase1=phase1,
        )
        print(json.dumps({
            "status": decision["status"],
            "calibration_path": str(
                args.output_dir / "calibration_decision.json"
            ),
            "selected_cohort_size": decision["selected_cohort_size"],
            "selected_workers": decision["selected_workers"],
            "projected_hours_with_headroom": decision[
                "projected_hours_with_headroom"
            ],
        }, sort_keys=True))
        return 0
    if args.cohort_size is None or args.workers is None:
        raise ValueError("--run-cohort requires --cohort-size and --workers")
    calibration_path = args.output_dir / "calibration_decision.json"
    if not calibration_path.exists():
        raise RuntimeError("calibration decision is absent")
    calibration_decision = _load_self_digested(calibration_path)
    result = run_cohort(
        output_dir=args.output_dir,
        source=source,
        stream=stream,
        cache=cache,
        input_identity=input_identity,
        phase1=phase1,
        calibration_decision=calibration_decision,
        cohort_size=args.cohort_size,
        workers=args.workers,
    )
    print(json.dumps({
        "status": result["status"],
        "benchmark_path": str(args.output_dir / "benchmark.json"),
        "completed_ordinals": result["completed_ordinals"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
