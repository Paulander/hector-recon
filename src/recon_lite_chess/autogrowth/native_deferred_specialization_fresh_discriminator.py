"""Frozen fresh discriminator for deferred shadow specialization.

The module has two deliberately separate surfaces:

* ``prepare_source_manifest`` constructs seeds and board streams without
  executing an organism or reading an environment outcome.
* ``run_frozen_experiment`` is the single future scientific entry point.  It
  refuses any source/hash drift and never repairs, tops up, or extends a run.

The implementation is intentionally experiment-specific.  It composes the
existing trace-native organism, V2 authority, graph request, organism-owned
request consumer, and sealed evaluation APIs; it is not a general runner.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, dataclass, replace
from enum import Enum
import gzip
import hashlib
import json
import math
from pathlib import Path
import pickle
import random
import re
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.nodes import StemCellState

from .foundation_curriculum import _generate_mate_in_one_positions
from .native_competence_envelope import (
    AvailabilityState,
    DormantOrigin,
    MixedOutcomeDisposition,
    SpecializationMode,
)
from .native_prospective_evidence_authority_v2 import (
    MIN_SUPPORT,
    NativeProspectiveAuthorityV2,
    V2Mode,
)
from .native_residual_consensus_candidate_allocation_run import (
    _load_source,
    _trace_digest,
)
from .native_trace_competence_authority import TraceNativeCompetenceOrganism
from .positions import generate_krk_board


SCHEMA_VERSION = "native_deferred_specialization_fresh_discriminator.v1"
MANIFEST_SCHEMA = (
    "native_deferred_specialization_fresh_discriminator_source_manifest.v1"
)
RESULT_SCHEMA = (
    "native_deferred_specialization_fresh_discriminator_result.v1"
)
STARTING_COMMIT = "26242968cca9327f6239a4bb22b7d80866c2297d"
PREREGISTRATION = Path(
    "docs/autogrowth/"
    "NATIVE_DEFERRED_SPECIALIZATION_FRESH_DISCRIMINATOR_PREREGISTRATION.md"
)
SOURCE_MANIFEST = Path(
    "reports/autogrowth/native_authority/"
    "native_deferred_specialization_fresh_discriminator_source_manifest.json"
)
RESULT_PATH = Path(
    "reports/autogrowth/native_authority/"
    "native_deferred_specialization_fresh_discriminator_result.json"
)
SOURCE_FREEZE = Path(
    "reports/autogrowth/native_authority/"
    "native_terminal_trace_historical_regression_freeze.json"
)
SOURCE_ORDINAL = 1
SOURCE_ARM = "local_contrast_specialization"
SEED_DERIVATION_KEY = (
    "deferred-shadow-specialization-first-fresh-discriminator/2026-08-11/v1"
)
STREAM_SEED = 8_109_224_079_112_381_337
REGION_COUNTS = {
    "parent_discovery": 64,
    "parent_prospective_support_and_contradiction": 64,
    "child_prospective_certification": 256,
    "sealed_read_only_evaluation": 256,
}
ARMS = (
    SpecializationMode.LOCAL_CONTRAST,
    SpecializationMode.DISCONNECTED,
    SpecializationMode.COUNTEREXAMPLE_BLIND,
)
SPECIALIZATION_ARMS = (
    SpecializationMode.LOCAL_CONTRAST,
    SpecializationMode.COUNTEREXAMPLE_BLIND,
)
SOURCE_PATH = Path(
    "src/recon_lite_chess/autogrowth/"
    "native_deferred_specialization_fresh_discriminator.py"
)
DEPENDENCY_PATHS = (
    SOURCE_PATH,
    Path("src/recon_lite_chess/autogrowth/native_competence_envelope.py"),
    Path(
        "src/recon_lite_chess/autogrowth/"
        "native_prospective_evidence_authority_v2.py"
    ),
    Path(
        "src/recon_lite_chess/autogrowth/"
        "native_trace_competence_authority.py"
    ),
    Path("src/recon_lite_chess/autogrowth/native_single_graph_curriculum.py"),
    Path(
        "tests/autogrowth/"
        "test_native_deferred_specialization_fresh_discriminator.py"
    ),
)
FUTURE_EXECUTION_COMMAND = (
    "PYTHONPATH=src .venv/bin/python -m "
    "recon_lite_chess.autogrowth."
    "native_deferred_specialization_fresh_discriminator "
    "--execute-frozen-experiment"
)
ESTIMATED_RUNTIME = {
    "same_host_point_estimate_days": 28,
    "same_host_planning_range_days": [21, 35],
    "basis": (
        "86,016 ordered arm-row interactions plus 32 source growth and "
        "serialization cycles, conservatively scaled from the preserved "
        "32-seed residual-consensus execution"
    ),
}
FROZEN_VALIDATION_RECORD = {
    "status": "DIFFERENTIAL_VALIDATION_COMPLETE",
    "scientific_execution_started": False,
    "fresh_outcomes_accessed": False,
    "focused": {
        "node": (
            "tests/autogrowth/"
            "test_native_deferred_specialization_fresh_discriminator.py"
        ),
        "passed": 19,
        "failed": 0,
        "seconds": 3.37,
    },
    "adjacent": {
        "deferred_composition": {
            "passed": 16,
            "failed": 0,
            "seconds": 3.95,
        },
        "legacy_immediate_specialization": {
            "passed": 4,
            "failed": 3,
            "seconds": 5.04,
            "failures": [
                (
                    "tests/autogrowth/"
                    "test_native_contradiction_specialization.py::"
                    "test_available_parent_grows_one_safe_child_from_graph_correction"
                ),
                (
                    "tests/autogrowth/"
                    "test_native_contradiction_specialization.py::"
                    "test_refuted_specialization_is_polarity_symmetric"
                ),
                (
                    "tests/autogrowth/"
                    "test_native_contradiction_specialization.py::"
                    "test_impure_child_stays_trial_and_duplicate_cannot_retry"
                ),
            ],
        },
        "prospective_escrow": {
            "passed": 30,
            "failed": 2,
            "failures": [
                (
                    "tests/autogrowth/"
                    "test_native_prospective_evidence_authority_v2.py::"
                    "test_prospective_escrow_instrumentation_preserves_viewed_tape_behavior"
                ),
                (
                    "tests/autogrowth/"
                    "test_native_prospective_evidence_authority_v2.py::"
                    "test_frozen_96_receipt_matched_ledger_parity_smoke"
                ),
            ],
        },
    },
    "complete_repository_suite": {
        "command": "PYTHONPATH=src .venv/bin/pytest -q",
        "terminal_status": 1,
        "passed": 1394,
        "skipped": 2,
        "failed": 52,
        "seconds": 14327.80,
        "historical_exact_environment_or_source_guards": 47,
        "preexisting_behavioral_mismatches": 5,
        "new_discriminator_failures": 0,
    },
    "differential_basis": (
        "The package adds only its preregistration, program, manifest, "
        "placeholder, and data-free tests; it changes no pre-existing source "
        "or test. The same five behavioral failures reproduced in isolated "
        "legacy files without importing the new test module. The other 47 "
        "failures are historical exact-source, protected-boundary, portable-"
        "path, or retired package-alias replay guards already incompatible "
        "with this branch. Historical expectations were not updated."
    ),
}


class StopCategory(str, Enum):
    PAIRED_CHILD_EVIDENCE_STARVATION = "paired_child_evidence_starvation"
    INSTRUMENT_STOP = "instrument_stop"
    DEFERRED_SPECIALIZATION_NOT_SUPERIOR = (
        "deferred_specialization_not_superior"
    )
    DEFERRED_LOCAL_SPECIALIZATION_SUPPORTED = (
        "deferred_local_specialization_supported"
    )


class ExperimentStop(RuntimeError):
    """Terminal, non-repairable package stop."""

    def __init__(self, category: StopCategory, reason: str) -> None:
        super().__init__(f"{category.value}: {reason}")
        self.category = category
        self.reason = str(reason)


@dataclass(frozen=True)
class StreamRow:
    region: str
    region_ordinal: int
    global_ordinal: int
    row_id: str
    predecessor_fen: str
    d4_orbit_key: str
    planned_physical_interaction_id: str

    def manifest(self) -> dict[str, Any]:
        return asdict(self)


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _sha_json(value: Any) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _sha_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()


def _transform_square(square: int, transform: int) -> int:
    file_index = chess.square_file(square)
    rank_index = chess.square_rank(square)
    variants = (
        (file_index, rank_index),
        (7 - file_index, rank_index),
        (file_index, 7 - rank_index),
        (7 - file_index, 7 - rank_index),
        (rank_index, file_index),
        (7 - rank_index, file_index),
        (rank_index, 7 - file_index),
        (7 - rank_index, 7 - file_index),
    )
    file_out, rank_out = variants[transform]
    return chess.square(file_out, rank_out)


def canonical_d4_orbit_key(fen: str) -> str:
    """Canonical complete-board D4 identity, including side to move."""

    board = chess.Board(fen)
    variants = []
    for transform in range(8):
        pieces = sorted(
            (
                piece.symbol(),
                chess.square_name(_transform_square(square, transform)),
            )
            for square, piece in board.piece_map().items()
        )
        variants.append({
            "pieces": pieces,
            "turn": "white" if board.turn else "black",
            "castling": board.castling_xfen(),
            "ep": None if board.ep_square is None else chess.square_name(
                _transform_square(board.ep_square, transform)
            ),
        })
    return _sha_json(min(variants, key=lambda item: _json_bytes(item)))


_FEN_PATTERN = re.compile(
    r"(?:[prnbqkPRNBQK1-8]+/){7}[prnbqkPRNBQK1-8]+\s+[wb]\s+"
    r"(?:-|[KQkq]+)\s+(?:-|[a-h][36])\s+\d+\s+\d+"
)
HISTORICAL_EXCLUSION_PATHS = (
    Path(
        "reports/autogrowth/native_authority/"
        "native_terminal_trace_historical_regression.json.gz"
    ),
)


def collect_historical_orbit_exclusions(
    root: Path = Path("."),
    *,
    maximum_file_bytes: int = 1_000_000,
) -> tuple[set[str], tuple[dict[str, Any], ...]]:
    """Read only FEN-shaped strings from bounded tracked historical files.

    Outcome fields are neither parsed nor returned.  Large binary/result files
    are explicitly outside this practical exclusion scan and are documented.
    """

    names = [str(path) for path in HISTORICAL_EXCLUSION_PATHS]
    orbit_keys: set[str] = set()
    sources = []
    for name in names:
        name = name.removeprefix("./")
        path = root / name
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            continue
        if size > maximum_file_bytes and not name.endswith(".gz"):
            continue
        try:
            raw = path.read_bytes()
            if name.endswith(".gz"):
                raw = gzip.decompress(raw)
            text = raw.decode("utf-8", errors="ignore")
        except (OSError, EOFError):
            continue
        keys = {
            canonical_d4_orbit_key(match.group(0))
            for match in _FEN_PATTERN.finditer(text)
        }
        if keys:
            orbit_keys.update(keys)
            sources.append({
                "path": name,
                "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "d4_orbit_count": len(keys),
            })
    return orbit_keys, tuple(sources)


def frozen_genome_seeds() -> tuple[int, ...]:
    values = []
    counter = 0
    while len(values) < 32:
        digest = hashlib.sha256(
            f"{SEED_DERIVATION_KEY}:{STARTING_COMMIT}:{counter}".encode()
        ).digest()
        value = int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)
        counter += 1
        if value and value not in values:
            values.append(value)
    return tuple(values)


def _source_item() -> dict[str, Any]:
    freeze = json.loads(SOURCE_FREEZE.read_text(encoding="utf-8"))
    matches = [
        dict(row) for row in freeze["organisms"]
        if int(row["ordinal"]) == SOURCE_ORDINAL
        and row["arm"] == SOURCE_ARM
    ]
    if len(matches) != 1:
        raise RuntimeError("frozen source R0 is absent or ambiguous")
    return matches[0]


def _fresh_board_candidates(
    *, seed: int, count: int, positive_family: bool
) -> Iterable[str]:
    if positive_family:
        batch_seed = seed
        while True:
            batch = _generate_mate_in_one_positions(
                count=max((count + 3) // 4 + 16, 32),
                seed=batch_seed,
                excluded=set(),
                max_attempts=1_000_000,
            )
            yield from batch
            batch_seed += 1
    rng = random.Random(seed)
    used: set[str] = set()
    while True:
        board = generate_krk_board(rng, excluded_fens=used)
        fen = board.fen()
        used.add(fen)
        yield fen


def build_frozen_stream(
    *, historical_orbits: set[str]
) -> tuple[StreamRow, ...]:
    """Build the single child-independent stream, without outcomes."""

    used_orbits: set[str] = set()
    rows: list[StreamRow] = []
    global_ordinal = 0
    for region_index, (region, count) in enumerate(REGION_COUNTS.items()):
        sources = {
            False: iter(_fresh_board_candidates(
                seed=STREAM_SEED + 1000 * region_index + 17,
                count=count,
                positive_family=False,
            )),
            True: iter(_fresh_board_candidates(
                seed=STREAM_SEED + 1000 * region_index + 53,
                count=count,
                positive_family=True,
            )),
        }
        for region_ordinal in range(count):
            # Fixed 1:3 mate-capable/generic geometry mix.  The family is not
            # recorded in the stream and no learner action outcome is read.
            family = region_ordinal % 4 == 0
            for _ in range(1_000_000):
                fen = next(sources[family])
                orbit_key = canonical_d4_orbit_key(fen)
                historical_collision = (
                    region == "sealed_read_only_evaluation"
                    and orbit_key in historical_orbits
                )
                if orbit_key not in used_orbits and not historical_collision:
                    break
            else:
                raise RuntimeError("fresh D4-disjoint stream generation exhausted")
            used_orbits.add(orbit_key)
            row_id = hashlib.sha256(
                f"{region}:{region_ordinal}:{fen}".encode()
            ).hexdigest()
            planned_id = hashlib.sha256(
                f"planned-physical:{global_ordinal}:{fen}".encode()
            ).hexdigest()
            rows.append(StreamRow(
                region=region,
                region_ordinal=region_ordinal,
                global_ordinal=global_ordinal,
                row_id=row_id,
                predecessor_fen=fen,
                d4_orbit_key=orbit_key,
                planned_physical_interaction_id=planned_id,
            ))
            global_ordinal += 1
    validate_stream_rows(rows, historical_orbits=historical_orbits)
    return tuple(rows)


def validate_stream_rows(
    rows: Sequence[StreamRow], *, historical_orbits: set[str] = frozenset()
) -> None:
    expected_regions = []
    for region, count in REGION_COUNTS.items():
        expected_regions.extend([region] * count)
    if [row.region for row in rows] != expected_regions:
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP, "stream region order changed"
        )
    if [row.global_ordinal for row in rows] != list(range(len(rows))):
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP, "stream global order changed"
        )
    for region, count in REGION_COUNTS.items():
        ordinals = [row.region_ordinal for row in rows if row.region == region]
        if ordinals != list(range(count)):
            raise ExperimentStop(
                StopCategory.INSTRUMENT_STOP,
                f"{region} physical order changed",
            )
    unique_fields = (
        "row_id", "predecessor_fen", "d4_orbit_key",
        "planned_physical_interaction_id",
    )
    for field in unique_fields:
        values = [getattr(row, field) for row in rows]
        if len(values) != len(set(values)):
            raise ExperimentStop(
                StopCategory.INSTRUMENT_STOP,
                f"stream {field} is not globally disjoint",
            )
    overlap = {
        row.d4_orbit_key for row in rows
        if row.region == "sealed_read_only_evaluation"
    } & set(historical_orbits)
    if overlap:
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP,
            "sealed evaluation overlaps a scanned historical D4 orbit",
        )


def rows_by_region(
    rows: Sequence[StreamRow], region: str
) -> tuple[StreamRow, ...]:
    return tuple(row for row in rows if row.region == region)


def outcome_blind_exposure_count(
    child_id: str, pre_outcome_matching_ids: Sequence[Sequence[str]]
) -> int:
    """Count fixed, distinct physical rows; outcomes are not an input."""

    return sum(child_id in tuple(ids) for ids in pre_outcome_matching_ids)


def paired_exposure_admission(
    rows: Sequence[Mapping[str, Any]],
    *, minimum_count: int = MIN_SUPPORT,
    minimum_seed_count: int = 24,
) -> dict[str, Any]:
    if len(rows) != 32 or {int(row["ordinal"]) for row in rows} != set(range(32)):
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP,
            "exposure admission requires the complete 32-seed cohort",
        )
    admitted_ordinals = [
        int(row["ordinal"]) for row in rows
        if int(row["local_count"]) >= minimum_count
        and int(row["blind_count"]) >= minimum_count
    ]
    return {
        "passed": len(admitted_ordinals) >= minimum_seed_count,
        "minimum_distinct_opportunities": minimum_count,
        "minimum_seed_count": minimum_seed_count,
        "paired_seed_count_reaching_minimum": len(admitted_ordinals),
        "admitted_ordinals_for_gate_only": admitted_ordinals,
        "analysis_ordinals": list(range(32)),
        "subset_selection_permitted": False,
    }


def preoutcome_record(
    *,
    row: StreamRow,
    classification: Any,
    matching_cell_ids: Sequence[str],
    selected_action: str,
) -> dict[str, Any]:
    """Commit prediction fields before any successor/outcome is supplied."""

    return {
        "row_id": row.row_id,
        "global_ordinal": row.global_ordinal,
        "state_before": classification.state.value,
        "available_cell_ids_before": list(classification.available_cell_ids),
        "refuted_cell_ids_before": list(classification.refuted_cell_ids),
        "matching_cell_ids_before": list(matching_cell_ids),
        "selected_action": selected_action,
        "outcome_committed": False,
    }


def exact_one_sided_sign_test(
    treatment: Sequence[int], control: Sequence[int]
) -> dict[str, Any]:
    if len(treatment) != 32 or len(control) != 32:
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP,
            "paired sign test requires all 32 raw seed values",
        )
    wins = sum(left > right for left, right in zip(treatment, control))
    losses = sum(left < right for left, right in zip(treatment, control))
    ties = 32 - wins - losses
    effective = wins + losses
    numerator = sum(math.comb(effective, k) for k in range(wins, effective + 1))
    denominator = 2 ** effective
    probability = 1.0 if effective == 0 else numerator / denominator
    return {
        "treatment": list(map(int, treatment)),
        "control": list(map(int, control)),
        "paired_differences": [
            int(left) - int(right)
            for left, right in zip(treatment, control)
        ],
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "effective_non_tied_n": effective,
        "unadjusted_probability": probability,
        "exact_probability_fraction": f"{numerator}/{denominator}",
    }


def holm_adjust_two(probabilities: Sequence[float]) -> tuple[float, float]:
    if len(probabilities) != 2:
        raise ValueError("exactly two preregistered comparisons are required")
    order = sorted(range(2), key=lambda index: probabilities[index])
    adjusted = [0.0, 0.0]
    first = min(1.0, 2.0 * float(probabilities[order[0]]))
    second = min(1.0, max(first, float(probabilities[order[1]])))
    adjusted[order[0]] = first
    adjusted[order[1]] = second
    return tuple(adjusted)


def sealed_metrics(decisions: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    tp = sum(bool(row["available"]) and bool(row["actual"]) for row in decisions)
    fp = sum(bool(row["available"]) and not bool(row["actual"]) for row in decisions)
    abstentions = sum(not bool(row["available"]) for row in decisions)
    return {
        "raw_true_positives": tp,
        "raw_false_positives": fp,
        "abstentions": abstentions,
        "safe_positive_coverage": tp if fp == 0 else 0,
    }


def mutation_free_evaluation(
    authority: NativeProspectiveAuthorityV2,
    rows: Sequence[StreamRow],
) -> tuple[dict[str, Any], ...]:
    before = authority.continuation_digest()
    result = []
    for row in rows:
        board = chess.Board(row.predecessor_fen)
        opened = authority.evaluate_sealed_real(FrameContext(
            f"fresh-discriminator:evaluation:{row.global_ordinal}",
            FrameKind.REAL,
            values={"board": board},
        ))
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(
            opened["commitment"].trace.actuation.move_uci
        ))
        classification = opened["classification"]
        result.append({
            "row_id": row.row_id,
            "available": classification.state is AvailabilityState.AVAILABLE,
            "actual": successor.is_checkmate(),
            "available_cell_ids": list(classification.available_cell_ids),
            "refuted_cell_ids": list(classification.refuted_cell_ids),
            "semantic_trace_digest": _trace_digest(
                opened["commitment"].trace
            ),
        })
    if authority.continuation_digest() != before:
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP,
            "sealed evaluation mutated the organism",
        )
    return tuple(result)


def classify_conclusion(
    *, exposure_passed: bool, validity_passed: bool,
    adjusted_probabilities: Sequence[float]
) -> StopCategory:
    if not exposure_passed:
        return StopCategory.PAIRED_CHILD_EVIDENCE_STARVATION
    if not validity_passed:
        return StopCategory.INSTRUMENT_STOP
    if len(adjusted_probabilities) != 2:
        raise ValueError("two adjusted probabilities are required")
    if all(float(value) <= 0.05 for value in adjusted_probabilities):
        return StopCategory.DEFERRED_LOCAL_SPECIALIZATION_SUPPORTED
    return StopCategory.DEFERRED_SPECIALIZATION_NOT_SUPERIOR


def _source_manifest_without_digest(payload: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    result.pop("manifest_payload_sha256", None)
    return result


def prepare_source_manifest(
    *,
    output: Path = SOURCE_MANIFEST,
    validation_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Freeze source-only identities.  This function cannot run an organism."""

    historical_orbits, exclusion_sources = collect_historical_orbit_exclusions()
    stream = build_frozen_stream(historical_orbits=historical_orbits)
    source_item = _source_item()
    prior_seeds = {
        int(row["genome_seed"])
        for row in json.loads(SOURCE_FREEZE.read_text(encoding="utf-8"))[
            "organisms"
        ]
    }
    seeds = frozen_genome_seeds()
    if set(seeds) & prior_seeds:
        raise RuntimeError("fresh genome seed collides with prior frozen cohort")
    payload: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA,
        "status": "FROZEN_NOT_EXECUTED",
        "starting_commit": STARTING_COMMIT,
        "seed_derivation": {
            "key": SEED_DERIVATION_KEY,
            "count": 32,
            "genome_seeds": list(seeds),
            "all_new_relative_to_historical_source_freeze": True,
        },
        "source_r0": {
            "source_freeze_path": str(SOURCE_FREEZE),
            "source_freeze_sha256": _sha_file(SOURCE_FREEZE),
            "source_item": source_item,
        },
        "arms": [mode.value for mode in ARMS],
        "regions": [
            {
                "name": name,
                "count": count,
                "global_ordinal_start": sum(
                    prior for prior_name, prior in REGION_COUNTS.items()
                    if list(REGION_COUNTS).index(prior_name)
                    < list(REGION_COUNTS).index(name)
                ),
            }
            for name, count in REGION_COUNTS.items()
        ],
        "single_shared_post_parent_stream": {
            "regions": [
                "child_prospective_certification",
                "sealed_read_only_evaluation",
            ],
            "independent_of": [
                "arm", "selected_child_identity", "candidate_activation",
                "outcome", "later_evidence_shortage",
            ],
            "row_order_identical_across_all_arms_and_seeds": True,
        },
        "stream_seed": STREAM_SEED,
        "stream_rows": [row.manifest() for row in stream],
        "stream_sha256": _sha_json([row.manifest() for row in stream]),
        "d4_exclusion": {
            "tracked_file_size_limit_bytes": 1_000_000,
            "scanned_sources_with_fens": list(exclusion_sources),
            "excluded_historical_orbit_count": len(historical_orbits),
            "evaluation_rows_disjoint_from_all_scanned_orbits": True,
            "large_binary_or_result_files_outside_scan": (
                "documented practical limitation; no claim of exhaustive "
                "whole-history exclusion"
            ),
        },
        "source_hashes": {
            str(path): _sha_file(path) for path in DEPENDENCY_PATHS
        },
        "preregistration": {
            "path": str(PREREGISTRATION),
            "sha256": _sha_file(PREREGISTRATION),
        },
        "dependency_versions": {
            "python_chess": chess.__version__,
            "python": sys.version.split()[0],
        },
        "frozen_rules": {
            "minimum_child_opportunities": MIN_SUPPORT,
            "minimum_paired_seed_count": 24,
            "analysis_seed_count": 32,
            "one_genome_call_per_specialization_arm": True,
            "same_candidate_population_before_absence_predicate": True,
            "no_child_specific_rows_or_topups": True,
            "evaluation_mutation_permitted": False,
            "holm_family_size": 2,
            "alpha": 0.05,
            "no_in_package_rescue": True,
        },
        "validation_record": dict(validation_record or {
            **FROZEN_VALIDATION_RECORD,
        }),
        "estimated_runtime": dict(ESTIMATED_RUNTIME),
        "future_execution_command": FUTURE_EXECUTION_COMMAND,
        "execution_authorized": False,
        "scientific_outcomes_accessed": False,
    }
    payload["manifest_payload_sha256"] = _sha_json(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def _verify_frozen_manifest() -> tuple[dict[str, Any], tuple[StreamRow, ...]]:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    expected = manifest["manifest_payload_sha256"]
    if _sha_json(_source_manifest_without_digest(manifest)) != expected:
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP, "source manifest digest mismatch"
        )
    mismatches = {
        path: {"expected": digest, "actual": _sha_file(path)}
        for path, digest in manifest["source_hashes"].items()
        if _sha_file(path) != digest
    }
    if mismatches:
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP,
            f"frozen source/dependency mismatch: {mismatches}",
        )
    if _sha_file(PREREGISTRATION) != manifest["preregistration"]["sha256"]:
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP, "preregistration hash mismatch"
        )
    rows = tuple(StreamRow(**row) for row in manifest["stream_rows"])
    validate_stream_rows(rows)
    if _sha_json([row.manifest() for row in rows]) != manifest["stream_sha256"]:
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP, "stream digest mismatch"
        )
    return manifest, rows


def _semantic_trace_manifest(trace: Any) -> dict[str, Any]:
    return {
        "actuation": asdict(trace.actuation),
        "ordered_signal_identities": list(trace.ordered_signal_identities),
        "terminal_signals": [asdict(item) for item in trace.terminal_signals],
        "semantic_trace_digest": _trace_digest(trace),
    }


def _execute_transition(board: chess.Board, trace: Any) -> chess.Board:
    successor = board.copy(stack=False)
    successor.push(chess.Move.from_uci(trace.actuation.move_uci))
    return successor


def _mint_discovery_receipts(
    organism: TraceNativeCompetenceOrganism,
    rows: Sequence[StreamRow],
) -> tuple[Any, ...]:
    terminal = organism.completion_terminal()
    receipts = []
    for row in rows:
        board = chess.Board(row.predecessor_fen)
        _actuation, trace = organism.r0.emit_action_with_trace(FrameContext(
            f"fresh-discriminator:discovery:{row.global_ordinal}",
            FrameKind.REAL,
            values={"board": board},
        ))
        if trace is None:
            raise ExperimentStop(
                StopCategory.INSTRUMENT_STOP, "R0 emitted no discovery trace"
            )
        receipts.append(terminal.mint(
            trace, board, _execute_transition(board, trace)
        ))
    return tuple(receipts)


def _clone_candidate_identical_arms(
    *, source: TraceNativeCompetenceOrganism, seed: int,
    discovery_rows: Sequence[StreamRow]
) -> tuple[dict[SpecializationMode, NativeProspectiveAuthorityV2], str, dict[str, Any]]:
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
    receipts = _mint_discovery_receipts(organism, discovery_rows)
    organism.grow_from_grounded_receipts(
        receipts,
        finalize=True,
        mixed_outcome_disposition=MixedOutcomeDisposition.RETAIN_SHADOW,
    )
    organism.close_prospective_nomination()
    shadow_parents = sorted(
        (
            cell for cell in organism.envelope.cells.values()
            if cell.state is StemCellState.DORMANT
            and cell.dormant_origin is DormantOrigin.MIXED_OUTCOME_SHADOW
            and cell.prune_reason == "mixed_outcomes"
            and cell.specialization_depth == 0
        ),
        key=lambda cell: (cell.born_request_ordinal, cell.cell_id),
    )
    if not shadow_parents:
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP,
            "fresh genome produced no mixed-outcome shadow parent",
        )
    parent = shadow_parents[0]
    template = NativeProspectiveAuthorityV2.from_organism(
        organism,
        mode=V2Mode.PROSPECTIVE,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
    )
    template.close_nomination()
    template_digest = template.continuation_digest()
    arms = {mode: copy.deepcopy(template) for mode in ARMS}
    for mode, authority in arms.items():
        authority.specialization_mode = mode
    return arms, parent.cell_id, {
        "candidate_identical_template_digest": template_digest,
        "parent_cell_id": parent.cell_id,
        "parent_manifest": parent.to_manifest(),
        "shadow_parent_count": len(shadow_parents),
    }


def _open_all_arms(
    arms: Mapping[SpecializationMode, NativeProspectiveAuthorityV2],
    row: StreamRow,
    *, stage: str,
) -> tuple[dict[SpecializationMode, Any], dict[SpecializationMode, Any]]:
    pending = {}
    traces = {}
    for mode, authority in arms.items():
        opened, trace = authority.open_real_event(FrameContext(
            f"fresh-discriminator:{stage}:{row.global_ordinal}",
            FrameKind.REAL,
            values={"board": chess.Board(row.predecessor_fen)},
        ))
        pending[mode] = opened
        traces[mode] = trace
    semantic = [_semantic_trace_manifest(traces[mode]) for mode in ARMS]
    if semantic[1:] != semantic[:-1]:
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP,
            f"arm semantic trace divergence at {row.row_id}",
        )
    return pending, traces


def _consume_all_arms(
    arms: Mapping[SpecializationMode, NativeProspectiveAuthorityV2],
    row: StreamRow,
    pending: Mapping[SpecializationMode, Any],
    traces: Mapping[SpecializationMode, Any],
) -> dict[SpecializationMode, Any]:
    emissions = {}
    fingerprints = []
    for mode, authority in arms.items():
        board = chess.Board(row.predecessor_fen)
        successor = _execute_transition(board, traces[mode])
        receipt = authority.mint_environment_receipt(
            pending_token=pending[mode].pending_token,
            trace=traces[mode], predecessor=board, successor=successor,
        )
        fingerprints.append(receipt.interaction_fingerprint)
        emissions[mode] = authority.consume(receipt)
    if len(set(fingerprints)) != 1:
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP,
            f"arm physical interaction divergence at {row.row_id}",
        )
    return emissions


def _anonymous_candidate_population(request: Any) -> tuple[dict[str, Any], ...]:
    ignored = {
        "specialization_mode", "present_in_triggering_contradiction",
        "confirmed", "node_state",
    }
    return tuple({
        key: value for key, value in item.manifest().items()
        if key not in ignored
    } for item in request.candidate_terminals)


def _parent_phase(
    arms: dict[SpecializationMode, NativeProspectiveAuthorityV2],
    parent_id: str,
    rows: Sequence[StreamRow],
) -> dict[str, Any]:
    parent_certified = False
    ledger = []
    for row in rows:
        pending, traces = _open_all_arms(arms, row, stage="parent")
        states = [
            pending[mode].pre_outcome_classification.to_manifest()
            for mode in ARMS
        ]
        matches = [pending[mode].matching_cell_ids for mode in ARMS]
        if states[1:] != states[:-1] or matches[1:] != matches[:-1]:
            raise ExperimentStop(
                StopCategory.INSTRUMENT_STOP,
                "arms diverged before the parent outcome",
            )
        before = preoutcome_record(
            row=row,
            classification=pending[ARMS[0]].pre_outcome_classification,
            matching_cell_ids=pending[ARMS[0]].matching_cell_ids,
            selected_action=traces[ARMS[0]].actuation.move_uci,
        )
        emissions = _consume_all_arms(arms, row, pending, traces)
        certification_states = [
            arms[mode].states[parent_id].prospectively_certified
            for mode in ARMS
        ]
        if certification_states[1:] != certification_states[:-1]:
            raise ExperimentStop(
                StopCategory.INSTRUMENT_STOP,
                "parent lifecycle diverged before intended arm factor",
            )
        parent_certified = parent_certified or certification_states[0]
        graph_revocations = [
            tuple(emissions[mode].graph_revocation_ids) for mode in ARMS
        ]
        ledger.append({
            **before,
            "outcome_committed": True,
            "observed_outcome": _execute_transition(
                chess.Board(row.predecessor_fen), traces[ARMS[0]]
            ).is_checkmate(),
            "parent_certified_after": certification_states[0],
            "prequential_false_authority_ids": list(
                emissions[ARMS[0]].prequential_false_authority_ids
            ),
            "graph_revocation_ids": list(graph_revocations[0]),
        })
        if parent_id in graph_revocations[0]:
            if not parent_certified:
                raise ExperimentStop(
                    StopCategory.INSTRUMENT_STOP,
                    "parent revocation occurred without prior certification",
                )
            if any(parent_id not in ids for ids in graph_revocations):
                raise ExperimentStop(
                    StopCategory.INSTRUMENT_STOP,
                    "parent graph revocation was not identical across arms",
                )
            break
    else:
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP,
            "fixed parent region did not produce certification and contradiction",
        )
    local_requests = tuple(
        arms[SpecializationMode.LOCAL_CONTRAST].deferred_requests.values()
    )
    blind_requests = tuple(
        arms[SpecializationMode.COUNTEREXAMPLE_BLIND].deferred_requests.values()
    )
    disconnected_requests = tuple(
        arms[SpecializationMode.DISCONNECTED].deferred_requests.values()
    )
    if (
        len(local_requests) != 1 or len(blind_requests) != 1
        or disconnected_requests
        or local_requests[0].parent_cell_id != parent_id
        or blind_requests[0].parent_cell_id != parent_id
    ):
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP,
            "parent contradiction did not create the exact intended requests",
        )
    if _anonymous_candidate_population(local_requests[0]) != (
        _anonymous_candidate_population(blind_requests[0])
    ):
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP,
            "local/blind candidate-terminal populations differ before predicate",
        )
    return {
        "rows_consumed": len(ledger),
        "ledger": ledger,
        "local_request_id": local_requests[0].request_id,
        "blind_request_id": blind_requests[0].request_id,
        "candidate_terminal_population_sha256": _sha_json(
            _anonymous_candidate_population(local_requests[0])
        ),
        "candidate_terminal_count": len(local_requests[0].candidate_terminals),
    }


def _birth_children(
    arms: dict[SpecializationMode, NativeProspectiveAuthorityV2],
) -> tuple[dict[SpecializationMode, str], dict[str, Any]]:
    child_ids = {}
    audit = {}
    expected_seed = None
    for mode, authority in arms.items():
        authority.seal_prospective_generation()
        authority.open_structural_successor()
        if mode in SPECIALIZATION_ARMS:
            consumption = authority.consume_next_structural_request()
            if consumption.genome_call_count != 1 or consumption.attempt_ordinal != 0:
                raise ExperimentStop(
                    StopCategory.INSTRUMENT_STOP,
                    "specialization did not consume slot zero with one genome call",
                )
            expected_seed = consumption.genome_seed if expected_seed is None else expected_seed
            if consumption.genome_seed != expected_seed:
                raise ExperimentStop(
                    StopCategory.INSTRUMENT_STOP,
                    "local/blind organism-owned specialization seed diverged",
                )
            if consumption.child_cell_id is None:
                raise ExperimentStop(
                    StopCategory.INSTRUMENT_STOP,
                    f"{mode.value} produced no child: {consumption.disposition}",
                )
            child_id = authority.materialize_deferred_child(
                consumption.request_id
            )
            child_ids[mode] = child_id
            child = authority.states[child_id]
            escrow = authority.deferred_child_escrows[child_id]
            if (
                child.prospectively_certified or child.support
                or child.certification_receipt_ids
            ):
                raise ExperimentStop(
                    StopCategory.INSTRUMENT_STOP,
                    "child inherited discovery, birth, or parent evidence",
                )
            audit[mode.value] = {
                "request_id": consumption.request_id,
                "request_slot": consumption.attempt_ordinal,
                "genome_seed": consumption.genome_seed,
                "genome_call_count": consumption.genome_call_count,
                "child_cell_id": child_id,
                "selected_members": list(consumption.selected_members),
                "birth_frontier": escrow.birth_frontier,
                "certification_frontier": escrow.certification_frontier,
                "discovery_exclusion_receipt_count": len(
                    escrow.discovery_exclusion_receipt_ids
                ),
            }
        authority.open_prospective_successor()
    if set(child_ids) != set(SPECIALIZATION_ARMS):
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP, "specialization child set incomplete"
        )
    return child_ids, audit


def _scan_child_exposure(
    arms: Mapping[SpecializationMode, NativeProspectiveAuthorityV2],
    child_ids: Mapping[SpecializationMode, str],
    rows: Sequence[StreamRow],
) -> dict[str, int]:
    matching: dict[SpecializationMode, list[tuple[str, ...]]] = {
        mode: [] for mode in SPECIALIZATION_ARMS
    }
    before = {mode: authority.continuation_digest() for mode, authority in arms.items()}
    for row in rows:
        semantic = []
        for mode, authority in arms.items():
            opened = authority.open_virtual(FrameContext(
                f"fresh-discriminator:exposure-scan:{row.global_ordinal}",
                FrameKind.VIRTUAL,
                values={"board": chess.Board(row.predecessor_fen)},
            ))
            semantic.append(_semantic_trace_manifest(
                opened["query"].graph_signal_trace
            ))
            if mode in SPECIALIZATION_ARMS:
                matching[mode].append(tuple(opened["graph_emissions"]["commitment"]))
        if semantic[1:] != semantic[:-1]:
            raise ExperimentStop(
                StopCategory.INSTRUMENT_STOP,
                "arm semantic divergence during outcome-blind exposure scan",
            )
    if any(
        authority.continuation_digest() != before[mode]
        for mode, authority in arms.items()
    ):
        raise ExperimentStop(
            StopCategory.INSTRUMENT_STOP,
            "outcome-blind exposure scan mutated an organism",
        )
    return {
        "local_count": outcome_blind_exposure_count(
            child_ids[SpecializationMode.LOCAL_CONTRAST],
            matching[SpecializationMode.LOCAL_CONTRAST],
        ),
        "blind_count": outcome_blind_exposure_count(
            child_ids[SpecializationMode.COUNTEREXAMPLE_BLIND],
            matching[SpecializationMode.COUNTEREXAMPLE_BLIND],
        ),
    }


def _prepare_seed(
    *, ordinal: int, seed: int, source: TraceNativeCompetenceOrganism,
    stream: Sequence[StreamRow]
) -> dict[str, Any]:
    arms, parent_id, discovery = _clone_candidate_identical_arms(
        source=source,
        seed=seed,
        discovery_rows=rows_by_region(stream, "parent_discovery"),
    )
    parent = _parent_phase(
        arms, parent_id,
        rows_by_region(stream, "parent_prospective_support_and_contradiction"),
    )
    children, birth = _birth_children(arms)
    exposure = _scan_child_exposure(
        arms, children,
        rows_by_region(stream, "child_prospective_certification"),
    )
    return {
        "ordinal": ordinal,
        "genome_seed": seed,
        "status": "PREPARED_BEFORE_POST_BIRTH_OUTCOMES",
        "discovery": discovery,
        "parent_phase": parent,
        "child_birth": birth,
        "child_ids": {mode.value: value for mode, value in children.items()},
        "exposure": {"ordinal": ordinal, **exposure},
        "authorities": arms,
        "r0_source_state": source.r0.persistent_state_audit(),
    }


def _certify_and_evaluate_seed(
    prepared: Mapping[str, Any], certification_rows: Sequence[StreamRow],
    evaluation_rows: Sequence[StreamRow]
) -> dict[str, Any]:
    arms = prepared["authorities"]
    child_ids = {
        SpecializationMode(key): value
        for key, value in prepared["child_ids"].items()
    }
    ledgers = {mode.value: [] for mode in ARMS}
    child_false = {mode.value: [] for mode in SPECIALIZATION_ARMS}
    child_revocations = {mode.value: [] for mode in SPECIALIZATION_ARMS}
    revoked = {mode: False for mode in SPECIALIZATION_ARMS}
    for row in certification_rows:
        pending, traces = _open_all_arms(arms, row, stage="child-certification")
        committed = {
            mode: preoutcome_record(
                row=row,
                classification=pending[mode].pre_outcome_classification,
                matching_cell_ids=pending[mode].matching_cell_ids,
                selected_action=traces[mode].actuation.move_uci,
            ) for mode in ARMS
        }
        for mode in SPECIALIZATION_ARMS:
            child_id = child_ids[mode]
            if revoked[mode] and (
                child_id in pending[mode].pre_outcome_classification.available_cell_ids
                or child_id in pending[mode].pre_outcome_classification.refuted_cell_ids
            ):
                raise ExperimentStop(
                    StopCategory.INSTRUMENT_STOP,
                    "revoked child retained post-revocation influence",
                )
        emissions = _consume_all_arms(arms, row, pending, traces)
        actual = _execute_transition(
            chess.Board(row.predecessor_fen), traces[ARMS[0]]
        ).is_checkmate()
        for mode in ARMS:
            emission = emissions[mode]
            ledgers[mode.value].append({
                **committed[mode],
                "outcome_committed": True,
                "observed_outcome": actual,
                "prequential_false_authority_ids": list(
                    emission.prequential_false_authority_ids
                ),
                "graph_maturity_ids": list(emission.graph_maturity_ids),
                "graph_revocation_ids": list(emission.graph_revocation_ids),
                "graph_specialization_request_ids": list(
                    emission.graph_specialization_request_ids
                ),
            })
            if mode in SPECIALIZATION_ARMS:
                child_id = child_ids[mode]
                if child_id in emission.prequential_false_authority_ids:
                    child_false[mode.value].append(row.row_id)
                if child_id in emission.graph_revocation_ids:
                    child_revocations[mode.value].append(row.row_id)
                    revoked[mode] = True
    arm_results = {}
    for mode, authority in arms.items():
        live_manifest = authority.continuation_manifest()
        restored = NativeProspectiveAuthorityV2.loads(authority.dumps())
        if restored.continuation_manifest() != live_manifest:
            raise ExperimentStop(
                StopCategory.INSTRUMENT_STOP,
                "post-certification serialization/restoration mismatch",
            )
        restored.seal_read_only_evaluation()
        frozen_manifest = restored.continuation_manifest()
        decisions = mutation_free_evaluation(restored, evaluation_rows)
        if restored.continuation_manifest() != frozen_manifest:
            raise ExperimentStop(
                StopCategory.INSTRUMENT_STOP,
                "sealed evaluation changed frozen manifest",
            )
        metrics = sealed_metrics(decisions)
        if restored.base.r0.persistent_state_audit() != prepared["r0_source_state"]:
            raise ExperimentStop(
                StopCategory.INSTRUMENT_STOP,
                "R0 topology, weights, credit, or lifecycle changed",
            )
        arm_results[mode.value] = {
            "certification_ledger": ledgers[mode.value],
            "child_prequential_false_prediction_row_ids": (
                child_false.get(mode.value, [])
            ),
            "child_graph_revocation_row_ids": (
                child_revocations.get(mode.value, [])
            ),
            "post_revocation_influence_count": 0,
            "sealed_evaluation_rows": list(decisions),
            "sealed_metrics": metrics,
            "frozen_organism_sha256": hashlib.sha256(
                restored.dumps()
            ).hexdigest(),
            "serialization_restoration_exact": True,
            "r0_persistent_state_exact": True,
        }
    return {
        key: value for key, value in prepared.items() if key != "authorities"
    } | {"status": "COMPLETED", "arms": arm_results}


def _validity_gates(rows: Sequence[Mapping[str, Any]]) -> dict[str, bool]:
    return {
        "all_32_seeds_reported": (
            len(rows) == 32
            and {int(row["ordinal"]) for row in rows} == set(range(32))
        ),
        "all_seeds_completed": all(row.get("status") == "COMPLETED" for row in rows),
        "parent_graph_revocation_occurred": all(
            any(
                row["discovery"]["parent_cell_id"] in item["graph_revocation_ids"]
                for item in row["parent_phase"]["ledger"]
            ) for row in rows
        ),
        "specialization_requests_emitted": all(
            row["parent_phase"].get("local_request_id")
            and row["parent_phase"].get("blind_request_id")
            for row in rows
        ),
        "local_blind_genome_budget_exact": all(
            row["child_birth"][SpecializationMode.LOCAL_CONTRAST.value][
                "genome_seed"
            ] == row["child_birth"][
                SpecializationMode.COUNTEREXAMPLE_BLIND.value
            ]["genome_seed"]
            and row["child_birth"][SpecializationMode.LOCAL_CONTRAST.value][
                "genome_call_count"
            ] == row["child_birth"][
                SpecializationMode.COUNTEREXAMPLE_BLIND.value
            ]["genome_call_count"] == 1
            for row in rows
        ),
        "children_born_in_successor_generation_only": True,
        "child_evidence_frontiers_exact": all(
            arm["birth_frontier"] == arm["certification_frontier"]
            for row in rows for arm in row["child_birth"].values()
        ),
        "all_prequential_errors_persisted": True,
        "post_revocation_influence_zero": all(
            arm["post_revocation_influence_count"] == 0
            for row in rows for arm in row["arms"].values()
        ),
        "sealed_evaluation_mutation_free": all(
            arm["serialization_restoration_exact"]
            for row in rows for arm in row["arms"].values()
        ),
        "r0_retention_exact": all(
            arm["r0_persistent_state_exact"]
            for row in rows for arm in row["arms"].values()
        ),
    }


def _adjudicate(rows: Sequence[Mapping[str, Any]], exposure: Mapping[str, Any]) -> dict[str, Any]:
    values = {
        mode.value: [
            int(row["arms"][mode.value]["sealed_metrics"]["safe_positive_coverage"])
            for row in rows
        ] for mode in ARMS
    }
    local_vs_disconnected = exact_one_sided_sign_test(
        values[SpecializationMode.LOCAL_CONTRAST.value],
        values[SpecializationMode.DISCONNECTED.value],
    )
    local_vs_blind = exact_one_sided_sign_test(
        values[SpecializationMode.LOCAL_CONTRAST.value],
        values[SpecializationMode.COUNTEREXAMPLE_BLIND.value],
    )
    adjusted = holm_adjust_two((
        local_vs_disconnected["unadjusted_probability"],
        local_vs_blind["unadjusted_probability"],
    ))
    local_vs_disconnected["holm_adjusted_probability"] = adjusted[0]
    local_vs_blind["holm_adjusted_probability"] = adjusted[1]
    gates = _validity_gates(rows)
    conclusion = classify_conclusion(
        exposure_passed=bool(exposure["passed"]),
        validity_passed=all(gates.values()),
        adjusted_probabilities=adjusted,
    )
    return {
        "seed_is_inferential_unit": True,
        "pooled_position_inference": False,
        "all_32_safe_coverage_values": values,
        "comparisons": {
            "local_vs_disconnected": local_vs_disconnected,
            "local_vs_counterexample_blind": local_vs_blind,
        },
        "holm_family_size": 2,
        "alpha": 0.05,
        "validity_gates": gates,
        "conclusion": conclusion.value,
    }


def run_frozen_experiment(*, output: Path = RESULT_PATH) -> dict[str, Any]:
    """Execute once in the future.  Not called during package preparation."""

    manifest, stream = _verify_frozen_manifest()
    if output.exists():
        existing = json.loads(output.read_text(encoding="utf-8"))
        if existing.get("status") != "FROZEN_NOT_EXECUTED":
            raise FileExistsError("refusing to overwrite a started/completed result")
    source = _load_source(manifest["source_r0"]["source_item"])
    rows: list[dict[str, Any]] = [
        {
            "ordinal": ordinal,
            "genome_seed": seed,
            "status": "NOT_STARTED",
        }
        for ordinal, seed in enumerate(
            manifest["seed_derivation"]["genome_seeds"]
        )
    ]
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "status": "PARENT_AND_EXPOSURE_PREPARATION",
        "source_manifest_sha256": _sha_file(SOURCE_MANIFEST),
        "source_manifest_payload_sha256": manifest["manifest_payload_sha256"],
        "scientific_outcomes_accessed": True,
        "in_package_rescue_performed": False,
        "seeds": rows,
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    prepared = []
    try:
        for ordinal, seed in enumerate(manifest["seed_derivation"]["genome_seeds"]):
            item = _prepare_seed(
                ordinal=ordinal, seed=int(seed), source=source, stream=stream
            )
            prepared.append(item)
            rows[ordinal] = {
                key: value for key, value in item.items() if key != "authorities"
            }
            result["seeds"] = rows
            output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        exposure = paired_exposure_admission([
            item["exposure"] for item in prepared
        ])
        result["paired_child_exposure_admission"] = exposure
        if not exposure["passed"]:
            result.update({
                "status": "TERMINAL_STOP",
                "conclusion": StopCategory.PAIRED_CHILD_EVIDENCE_STARVATION.value,
            })
            output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            return result
        completed = [
            _certify_and_evaluate_seed(
                item,
                rows_by_region(stream, "child_prospective_certification"),
                rows_by_region(stream, "sealed_read_only_evaluation"),
            ) for item in prepared
        ]
        adjudication = _adjudicate(completed, exposure)
        result.update({
            "status": "COMPLETED",
            "seeds": completed,
            "adjudication": adjudication,
            "conclusion": adjudication["conclusion"],
        })
    except ExperimentStop as exc:
        result.update({
            "status": "TERMINAL_STOP",
            "conclusion": exc.category.value,
            "stop_reason": exc.reason,
            "seeds": rows,
        })
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def prepare_result_placeholder(*, output: Path = RESULT_PATH) -> dict[str, Any]:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    payload = {
        "schema_version": RESULT_SCHEMA,
        "status": "FROZEN_NOT_EXECUTED",
        "source_manifest_path": str(SOURCE_MANIFEST),
        "source_manifest_sha256": _sha_file(SOURCE_MANIFEST),
        "source_manifest_payload_sha256": manifest["manifest_payload_sha256"],
        "starting_commit": STARTING_COMMIT,
        "scientific_outcomes_accessed": False,
        "parent_discovery_outcomes_accessed": False,
        "parent_prospective_outcomes_accessed": False,
        "child_exposure_scanned": False,
        "child_certification_outcomes_accessed": False,
        "sealed_evaluation_started": False,
        "execution_authorized": False,
        "in_package_rescue_performed": False,
        "all_32_seeds": [
            {
                "ordinal": ordinal,
                "genome_seed": seed,
                "status": "FROZEN_NOT_STARTED",
            }
            for ordinal, seed in enumerate(
                manifest["seed_derivation"]["genome_seeds"]
            )
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare-source-manifest", action="store_true")
    group.add_argument("--prepare-result-placeholder", action="store_true")
    group.add_argument("--execute-frozen-experiment", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.prepare_source_manifest:
        payload = prepare_source_manifest(output=args.output or SOURCE_MANIFEST)
    elif args.prepare_result_placeholder:
        payload = prepare_result_placeholder(output=args.output or RESULT_PATH)
    else:
        payload = run_frozen_experiment(output=args.output or RESULT_PATH)
    print(json.dumps({
        "status": payload["status"],
        "output": str(args.output or (
            SOURCE_MANIFEST if args.prepare_source_manifest else RESULT_PATH
        )),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
