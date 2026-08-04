"""Fixed-seed viewed-data V2 R0 competence-to-handover canary."""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, dataclass, replace
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter
import traceback
from typing import Any, Mapping, Sequence

import chess

from recon_lite import ChildResponse, FrameContext, FrameKind

from .native_authority_handover import ChildQuery, NativeHandoverGenome
from .native_authority_lab import NativeAuthorityLabConfig, load_retired_r0_build
from .native_child_availability import (
    FailClosedNativeHandoverGenome,
    observe_query_completion,
)
from .native_competence_envelope import AvailabilityState
from .native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    V2Mode,
    VIRTUAL_AVAILABLE_VALUE,
    VIRTUAL_RESPONSE_UNCERTAINTY,
)
from .native_trace_competence_authority import TraceNativeCompetenceOrganism


BASE_COMMIT = "00c1330dc096f977738bebeb041a6fab8146e572"
RESULT_TAG = "tg26m-v2-portable-outcome-result"
FIXED_SOURCE_ORDINAL = 0
FIXED_GENOME_SEED = 927199493097905893
REGRESSION_ARTIFACT = Path(
    "reports/autogrowth/native_authority/"
    "native_terminal_trace_historical_regression.json.gz"
)
RETIRED_DIAGNOSTIC = Path(
    "reports/autogrowth/native_authority/"
    "retired_r0_child_availability_diagnostic.json"
)
DEFAULT_OUTPUT = Path(
    "reports/autogrowth/native_authority/"
    "native_v2_r0_handover_development.json"
)

# Immutable viewed inputs remain hash-bound; package code is bound by clean HEAD.
IMMUTABLE_SOURCE_HASHES = {
    str(REGRESSION_ARTIFACT): (
        "eb60826db7269b1fb69cd2abe21d137bb1853503cd8177e69aeb36050a77ecf4"
    ),
    str(RETIRED_DIAGNOSTIC): (
        "e946abccb4e846ca260f034174c6f440683155ebf17b617c0de8b2ae3a5baf2b"
    ),
    "snapshots/autogrowth/native_authority/r0_organism.pkl": (
        "bb58b7d64bd3ab5b696713a7253555e051bd0e9fdef4637db7c27e7517495eaf"
    ),
    "reports/autogrowth/native_from_scratch/"
    "r0_r1_balanced96_240_seed_20260719_compact.json": (
        "c55a4097547713edb5d9ef27a250bbfac62fb9886d86afae87b387b72869c792"
    ),
}
PACKAGE_SOURCE_PATHS = (
    "src/recon_lite_chess/autogrowth/native_v2_r0_handover_development.py",
    "src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2.py",
    "src/recon_lite_chess/autogrowth/native_child_availability.py",
)


PREREGISTRATION = {
    "hypothesis": (
        "one predeclared R0 genome earns exact binary V2 availability from later "
        "REAL competence interactions and causally changes the touched Mate-in-2 "
        "first action"
    ),
    "null": (
        "the fixed organism misses a touched-data competence gate, fails exact "
        "retired selectivity, or does not causally outperform both controls"
    ),
    "fixed_genome_seed": FIXED_GENOME_SEED,
    "single_factor": "binary prospectively certified child availability",
    "information_boundary": (
        "R0 board, graph-selected action, complete typed graph trace and observed "
        "REAL completion only; VIRTUAL frames and handover rows cannot learn"
    ),
    "response_contract": {
        "available_value": VIRTUAL_AVAILABLE_VALUE,
        "available_uncertainty": VIRTUAL_RESPONSE_UNCERTAINTY,
        "confidence_fields": "telemetry_only",
    },
    "controls": ["equal-reply-count availability derangement", "disconnected"],
    "touched_gate": {
        "validation_positive_min": 14,
        "validation_decoy_fp_max": 0,
        "regression_positive_min": 14,
        "regression_decoy_fp_max": 0,
        "combined_positive_min": 29,
        "retired_65": "1 TP, 0 FP, 64 unavailable",
    },
    "kill_rule": (
        "stop at the first failed gate without tuning, another seed, another "
        "mechanism, R1 learning, or fresh data"
    ),
}


@dataclass(frozen=True)
class DevelopmentConfig:
    output: str = str(DEFAULT_OUTPUT)


class NativeV2R0CompetenceOrganism:
    """The existing child interface backed only by frozen V2 certification."""

    def __init__(
        self,
        authority: NativeProspectiveAuthorityV2,
        *,
        cleared_certification_ids: frozenset[str] = frozenset(),
    ) -> None:
        if authority.mode is not V2Mode.PROSPECTIVE:
            raise ValueError("handover requires the prospective V2 mode")
        if authority.pending_event is not None:
            raise ValueError("handover cannot open with a pending REAL event")
        authority._verify_invariants()
        unknown = set(cleared_certification_ids).difference(authority.states)
        if unknown:
            raise ValueError(f"unknown cleared certification IDs: {sorted(unknown)}")
        self.authority = authority
        self.cleared_certification_ids = cleared_certification_ids

    @property
    def r0(self):
        return self.authority.base.r0

    def dream_session(self) -> "NativeV2R0DreamSession":
        return NativeV2R0DreamSession(self)

    def dumps(self) -> bytes:
        if self.cleared_certification_ids:
            raise ValueError("intervention clones are not deployable artifacts")
        return self.authority.dumps()

    @classmethod
    def loads(cls, payload: bytes) -> "NativeV2R0CompetenceOrganism":
        return cls(NativeProspectiveAuthorityV2.loads(payload))

    def isolated_clearing_clone(
        self, cell_ids: Sequence[str]
    ) -> "NativeV2R0CompetenceOrganism":
        return NativeV2R0CompetenceOrganism(
            NativeProspectiveAuthorityV2.loads(self.authority.dumps()),
            cleared_certification_ids=frozenset(cell_ids),
        )


class NativeV2R0DreamSession:
    def __init__(self, organism: NativeV2R0CompetenceOrganism) -> None:
        self.organism = organism
        self.before = organism.authority.continuation_digest()
        self.closed = False

    def request(self, frame: FrameContext) -> ChildQuery:
        if self.closed:
            raise RuntimeError("V2 R0 dream session is closed")
        opened = self.organism.authority.open_virtual(frame)
        if opened["certification_commitment"] is not None:
            raise RuntimeError("VIRTUAL query created certification evidence")
        query = opened["query"]
        provenance = dict(query.availability_provenance or {})
        if provenance.get("authority") != (
            "NativeProspectiveAuthorityV2_graph_emission"
        ):
            raise RuntimeError("child query bypassed V2 graph authority")
        if self.organism.cleared_certification_ids and query.response.available:
            available_ids = set(provenance.get("available_cell_ids", ()))
            survivors = available_ids.difference(
                self.organism.cleared_certification_ids
            )
            provenance["intervention_cleared_certification_ids"] = sorted(
                self.organism.cleared_certification_ids
            )
            provenance["intervention_surviving_available_cell_ids"] = sorted(
                survivors
            )
            if not survivors:
                query = replace(
                    query,
                    response=_binary_response(query, available=False),
                    availability_provenance=provenance,
                )
        expected_strength = (
            VIRTUAL_AVAILABLE_VALUE * (1.0 - VIRTUAL_RESPONSE_UNCERTAINTY)
            if query.response.available else 0.0
        )
        if query.response.selection_strength != expected_strength:
            raise RuntimeError("availability response used confidence ranking")
        if self.organism.authority.continuation_digest() != self.before:
            raise RuntimeError("VIRTUAL handover query mutated V2 authority")
        return query

    def close(self) -> None:
        if self.organism.authority.continuation_digest() != self.before:
            raise RuntimeError("V2 R0 dream session leaked persistent state")
        self.closed = True


def _binary_response(query: ChildQuery, *, available: bool) -> ChildResponse:
    source = query.response
    return ChildResponse(
        child_id=source.child_id,
        confirmed=available,
        policy_response=source.policy_response,
        available=available,
        expected_value=VIRTUAL_AVAILABLE_VALUE if available else 0.0,
        uncertainty=VIRTUAL_RESPONSE_UNCERTAINTY,
        grounded=source.grounded,
        grounding_source=source.grounding_source,
    )


def _sha_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _sha_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")).hexdigest()


def _verify_sources() -> dict[str, str]:
    actual = {
        path: _sha_file(path)
        for path in (*IMMUTABLE_SOURCE_HASHES, *PACKAGE_SOURCE_PATHS)
    }
    changed = {
        path: {"expected": expected, "actual": actual[path]}
        for path, expected in IMMUTABLE_SOURCE_HASHES.items()
        if actual[path] != expected
    }
    if changed:
        raise RuntimeError(f"immutable source changed: {changed}")
    return actual


def _git_source_freeze() -> dict[str, Any]:
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if status:
        raise RuntimeError(f"package must run from a clean source freeze: {status}")
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {"commit": commit, "clean_before_execution": True}


def _load_regression() -> dict[str, Any]:
    with gzip.open(REGRESSION_ARTIFACT, "rt", encoding="utf-8") as stream:
        result = json.load(stream)
    if (
        not result["gates"]["integrity"]
        or len(result["reference_rows"]) != 32
        or len(result["organisms"]) != 96
    ):
        raise RuntimeError("historical regression authority is incomplete")
    return result


def _fixed_source_item(regression: Mapping[str, Any]) -> dict[str, Any]:
    rows = sorted(
        (item["source_artifact"] for item in regression["organisms"]
         if item["arm"] == "local_contrast_specialization"),
        key=lambda item: int(item["ordinal"]),
    )
    if len(rows) != 32:
        raise RuntimeError("expected all 32 historical source records")
    selected = dict(rows[FIXED_SOURCE_ORDINAL])
    if (
        int(selected["ordinal"]) != FIXED_SOURCE_ORDINAL
        or int(selected["genome_seed"]) != FIXED_GENOME_SEED
    ):
        raise RuntimeError("fixed source identity changed")
    return selected


def _load_source(item: Mapping[str, Any]) -> TraceNativeCompetenceOrganism:
    compressed = Path(str(item["path"])).read_bytes()
    if hashlib.sha256(compressed).hexdigest() != item["compressed_sha256"]:
        raise RuntimeError("source organism compressed hash mismatch")
    raw = gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest() != item["uncompressed_sha256"]:
        raise RuntimeError("source organism raw hash mismatch")
    source = TraceNativeCompetenceOrganism.loads(raw)
    if source.continuation_digest_v3() != item["continuation_v3_sha256"]:
        raise RuntimeError("source organism continuation mismatch")
    return source


def _certify_fixed_source(
    source_item: Mapping[str, Any],
    references: Sequence[Mapping[str, Any]],
) -> tuple[
    NativeV2R0CompetenceOrganism,
    NativeV2R0CompetenceOrganism,
    dict[str, Any],
]:
    source = _load_source(source_item)
    authority = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    frozen = authority.close_nomination()
    identity_before = copy.deepcopy(authority.experimental_identity)
    matured = revoked = 0
    for reference in references:
        row_index = int(reference["row_index"])
        predecessor = chess.Board(str(reference["fen"]))
        pending, trace = authority.open_real_event(FrameContext(
            f"trace-regression-real:{row_index}",
            FrameKind.REAL,
            values={"board": predecessor},
        ))
        successor = predecessor.copy(stack=False)
        successor.push(chess.Move.from_uci(trace.actuation.move_uci))
        parity = {
            "actuation": asdict(trace.actuation) == reference["actuation"],
            "trace": trace.digest() == reference["trace_digest"],
            "completion": successor.is_checkmate()
            == bool(reference["actual_completion"]),
        }
        if not all(parity.values()):
            raise RuntimeError(f"viewed REAL replay mismatch {row_index}: {parity}")
        receipt = authority.mint_environment_receipt(
            pending_token=pending.pending_token,
            trace=trace,
            predecessor=predecessor,
            successor=successor,
        )
        emission = authority.consume(receipt)
        matured += len(emission.graph_maturity_ids)
        revoked += len(emission.graph_revocation_ids)
    if authority.experimental_identity != identity_before:
        raise RuntimeError("candidate identity changed during certification")
    live = NativeV2R0CompetenceOrganism(authority)
    payload = live.dumps()
    restored = NativeV2R0CompetenceOrganism.loads(payload)
    if restored.authority.continuation_digest() != authority.continuation_digest():
        raise RuntimeError("serialization changed V2 authority")
    clearings = sum(
        row["transition"] == "GRAPH_LOCAL_REVOCATION"
        for state in authority.states.values() for row in state.transition_rows
    )
    return live, restored, {
        "ordinal": int(source_item["ordinal"]),
        "genome_seed": int(source_item["genome_seed"]),
        "candidate_count": len(frozen),
        "candidate_digest": _sha_json(list(frozen)),
        "later_distinct_real_interactions": len(references),
        "graph_maturity_emissions": matured,
        "graph_revocation_emissions": revoked,
        "contradiction_driven_clearings": clearings,
        "final_certified_cell_count": sum(
            state.prospectively_certified for state in authority.states.values()
        ),
        "serialization": {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "roundtrip_continuation_exact": True,
        },
    }


def _trace_projection(trace: Any) -> dict[str, Any] | None:
    if trace is None:
        return None
    value = trace.canonical_manifest()
    value.pop("frame_id", None)
    value.pop("frame_kind", None)
    return value


def _query_projection(query: ChildQuery) -> dict[str, Any]:
    provenance = query.availability_provenance or {}
    return {
        "action": None if query.actuation is None else asdict(query.actuation),
        "trace": _trace_projection(query.graph_signal_trace),
        "policy_response": query.response.policy_response,
        "available": query.response.available,
        "selection_strength": query.response.selection_strength,
        "classification": provenance.get("classification"),
        "matching_certified_cell_ids": provenance.get(
            "matching_certified_cell_ids", []
        ),
        "available_cell_ids": provenance.get("available_cell_ids", []),
    }


def _measure_competence_rows(
    organism: NativeV2R0CompetenceOrganism,
    rows: Sequence[tuple[str, str, bool]],
) -> dict[str, Any]:
    before = organism.authority.continuation_digest()
    measured = []
    session = organism.dream_session()
    try:
        for index, (split, fen, expected) in enumerate(rows):
            board = chess.Board(fen)
            frame_id = f"competence-gate:{split}:{index}"
            query = session.request(FrameContext(
                frame_id, FrameKind.VIRTUAL, values={"board": board}
            ))
            real_action, real_trace = organism.r0.emit_action_with_trace(
                FrameContext(frame_id, FrameKind.REAL, values={"board": board})
            )
            if query.actuation != real_action:
                raise RuntimeError("REAL/VIRTUAL action parity failure")
            if _trace_projection(query.graph_signal_trace) != _trace_projection(
                real_trace
            ):
                raise RuntimeError("REAL/VIRTUAL trace parity failure")
            observed = observe_query_completion(
                organism.r0, board.copy(stack=False), query
            )
            if observed.completion_confirmed != expected:
                raise RuntimeError(f"competence outcome changed: {split}:{index}")
            provenance = query.availability_provenance or {}
            signals = [] if query.graph_signal_trace is None else [
                asdict(item) for item in query.graph_signal_trace.terminal_signals
            ]
            measured.append({
                "split": split,
                "fen": fen,
                "actual_completion": expected,
                "state": provenance["classification"]["state"],
                "available": query.response.available,
                "typed_trace_digest": _sha_json(signals),
                "projection": _query_projection(query),
            })
    finally:
        session.close()
    if organism.authority.continuation_digest() != before:
        raise RuntimeError("competence gate caused persistent learning")
    return {"rows": measured, "metrics": _metrics(measured)}


def _metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    result = {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "abstentions": 0}
    for row in rows:
        actual = bool(row["actual_completion"])
        state = row["state"]
        if state == AvailabilityState.AVAILABLE.value:
            result["tp" if actual else "fp"] += 1
        elif state == AvailabilityState.REFUTED.value:
            result["fn" if actual else "tn"] += 1
        else:
            result["abstentions"] += 1
    available = result["tp"] + result["fp"]
    result["available_count"] = available
    result["availability_coverage"] = available / max(1, len(rows))
    return result


def _mixed_trace_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["typed_trace_digest"]), []).append(row)
    mixed = [
        values for values in grouped.values()
        if {bool(row["actual_completion"]) for row in values} == {False, True}
    ]
    violations = [
        [row["fen"] for row in values]
        for values in mixed
        if any(row["state"] != AvailabilityState.UNKNOWN.value for row in values)
    ]
    return {
        "mixed_typed_trace_group_count": len(mixed),
        "violations": violations,
        "passed": bool(mixed) and not violations,
    }


def _canonical_position(fen: str) -> str:
    return " ".join(chess.Board(fen).fen().split()[:4])


def _symmetry_orbit_key(fen: str) -> str:
    """Canonical D4 key for any board inventory, including captured rooks."""

    board = chess.Board(fen)

    def transform(square: int, variant: int) -> int:
        file_index = chess.square_file(square)
        rank_index = chess.square_rank(square)
        coordinates = (
            (file_index, rank_index),
            (7 - file_index, rank_index),
            (file_index, 7 - rank_index),
            (7 - file_index, 7 - rank_index),
            (rank_index, file_index),
            (7 - rank_index, file_index),
            (rank_index, 7 - file_index),
            (7 - rank_index, 7 - file_index),
        )
        return chess.square(*coordinates[variant])

    variants = []
    for variant in range(8):
        pieces = tuple(sorted(
            (piece.symbol(), transform(square, variant))
            for square, piece in board.piece_map().items()
        ))
        castling = tuple(sorted(
            transform(square, variant)
            for square in chess.SquareSet(board.castling_rights)
        ))
        ep_square = (
            -1 if board.ep_square is None
            else transform(board.ep_square, variant)
        )
        variants.append((pieces, int(board.turn), castling, ep_square))
    return _sha_json(min(variants))


def _handover_boards(parent_fen: str) -> tuple[str, ...]:
    parent = chess.Board(parent_fen)
    rows = [parent.fen()]
    for first in sorted(parent.legal_moves, key=lambda move: move.uci()):
        after = parent.copy(stack=False)
        after.push(first)
        for reply in sorted(after.legal_moves, key=lambda move: move.uci()):
            successor = after.copy(stack=False)
            successor.push(reply)
            rows.append(successor.fen())
    return tuple(rows)


def _disjointness(
    organism: NativeV2R0CompetenceOrganism,
    certification_fens: Sequence[str],
    parent_fen: str,
) -> dict[str, Any]:
    evidence = tuple(
        [receipt.predecessor_fen for receipt in organism.authority.base.receipts.values()]
        + list(certification_fens)
    )
    handover = _handover_boards(parent_fen)
    evidence_positions = {_canonical_position(fen) for fen in evidence}
    handover_positions = {_canonical_position(fen) for fen in handover}
    evidence_orbits = {_symmetry_orbit_key(fen) for fen in evidence}
    handover_orbits = {_symmetry_orbit_key(fen) for fen in handover}
    exact_overlap = sorted(evidence_positions & handover_positions)
    orbit_overlap = sorted(evidence_orbits & handover_orbits)
    return {
        "evidence_board_count": len(evidence_positions),
        "handover_board_count": len(handover_positions),
        "exact_overlap": exact_overlap,
        "symmetry_orbit_overlap": orbit_overlap,
        "passed": not exact_overlap and not orbit_overlap,
    }


def _measure_handover_queries(
    organism: NativeV2R0CompetenceOrganism,
    prior: Mapping[str, Any],
) -> tuple[dict[str, tuple[ChildQuery, ...]], dict[Any, Any], dict[str, Any]]:
    parent = chess.Board(str(prior["retired_r1_fen"]))
    before = organism.authority.continuation_digest()
    slots, frames = NativeHandoverGenome().query_child_slots(parent, organism)
    expected = list(prior["successor_decomposition"])
    rows = []
    cursor = 0
    for action in sorted(slots):
        after = parent.copy(stack=False)
        after.push(chess.Move.from_uci(action))
        replies = sorted(after.legal_moves, key=lambda move: move.uci())
        for index, (reply, query) in enumerate(zip(replies, slots[action], strict=True)):
            successor = after.copy(stack=False)
            successor.push(reply)
            observed = observe_query_completion(
                organism.r0, successor.copy(stack=False), query
            )
            reference = expected[cursor]
            parity = {
                "parent_action": action == reference["parent_action"],
                "black_reply": reply.uci() == reference["black_reply"],
                "successor": successor.fen() == reference["successor_fen"],
                "policy_action": (
                    None if query.actuation is None else query.actuation.move_uci
                ) == reference["policy_action"],
                "completion": observed.completion_confirmed
                == reference["policy_success"],
            }
            if not all(parity.values()):
                raise RuntimeError(f"retired successor parity failure {cursor}: {parity}")
            provenance = query.availability_provenance or {}
            rows.append({
                "slot": cursor,
                "parent_action": action,
                "black_reply": reply.uci(),
                "virtual_board": successor.fen(),
                "actual_completion": observed.completion_confirmed,
                "state": provenance["classification"]["state"],
                "available": query.response.available,
                "r0_action": None if query.actuation is None else query.actuation.move_uci,
                "trace": (
                    None if query.graph_signal_trace is None
                    else query.graph_signal_trace.canonical_manifest()
                ),
                "policy_response": query.response.policy_response,
                "availability_provenance": provenance,
            })
            cursor += 1
    if cursor != 65 or cursor != len(expected):
        raise RuntimeError("retired successor cardinality changed")
    if organism.authority.continuation_digest() != before:
        raise RuntimeError("handover measurement caused persistent learning")
    return slots, frames, {"rows": rows, "metrics": _metrics(rows)}


def _deranged_slots(
    slots: Mapping[str, tuple[ChildQuery, ...]],
) -> tuple[dict[str, tuple[ChildQuery, ...]], dict[str, str]]:
    strata: dict[int, list[str]] = {}
    for action, queries in sorted(slots.items()):
        strata.setdefault(len(queries), []).append(action)
    mapping: dict[str, str] = {}
    for actions in strata.values():
        if len(actions) == 1:
            mapping[actions[0]] = actions[0]
        else:
            for index, action in enumerate(actions):
                mapping[action] = actions[(index + 1) % len(actions)]
    result = {}
    for action, queries in slots.items():
        donor = slots[mapping[action]]
        if len(queries) != len(donor):
            raise RuntimeError("derangement crossed reply-count stratum")
        rows = []
        for query, donor_query in zip(queries, donor, strict=True):
            provenance = dict(query.availability_provenance or {})
            provenance.update({
                "control": "equal_reply_count_availability_derangement",
                "availability_donor_action": mapping[action],
            })
            rows.append(replace(
                query,
                response=_binary_response(
                    query, available=bool(donor_query.response.available)
                ),
                availability_provenance=provenance,
            ))
        result[action] = tuple(rows)
    if sum(q.response.available for qs in result.values() for q in qs) != sum(
        q.response.available for qs in slots.values() for q in qs
    ):
        raise RuntimeError("derangement changed available-slot count")
    return result, mapping


def _evaluate_decision(
    parent: chess.Board,
    decision: Any,
    measured_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    selected = decision.actuation.move_uci
    after = parent.copy(stack=False)
    after.push(chess.Move.from_uci(selected))
    if after.is_checkmate():
        replies = []
        converted = True
    else:
        replies = [
            {
                "reply": row["black_reply"],
                "child_action": row["r0_action"],
                "completed": row["actual_completion"],
                "measurement_slot": row["slot"],
            }
            for row in measured_rows
            if row["parent_action"] == selected
        ]
        expected_replies = [
            move.uci()
            for move in sorted(after.legal_moves, key=lambda move: move.uci())
        ]
        if [row["reply"] for row in replies] != expected_replies:
            raise RuntimeError("control did not reuse the exact measured reply set")
        converted = bool(replies and all(row["completed"] for row in replies))
    return {
        "selected_first": selected,
        "converted": converted,
        "selection_mode": decision.selection_mode,
        "host_fallback_count": decision.host_fallback_count,
        "causal_graph_audit": decision.causal_graph_audit,
        "replies": replies,
    }


def _causal_canary(
    organism: NativeV2R0CompetenceOrganism,
    parent_fen: str,
    slots: Mapping[str, tuple[ChildQuery, ...]],
    frames: Mapping[Any, Any],
    measured_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    parent = chess.Board(parent_fen)
    chooser = FailClosedNativeHandoverGenome()
    deranged, mapping = _deranged_slots(slots)
    decisions = {
        "connected": chooser.decide_from_available_slots(parent, slots, frames),
        "deranged": chooser.decide_from_available_slots(parent, deranged, frames),
        "disconnected": chooser.decide_from_available_slots(
            parent, slots, frames, disconnected=True
        ),
    }
    arms = {
        name: _evaluate_decision(parent, decision, measured_rows)
        for name, decision in decisions.items()
    }
    selected = arms["connected"]["selected_first"]
    selected_queries = slots[selected]
    cleared_ids = sorted({
        cell_id
        for query in selected_queries
        for cell_id in (query.availability_provenance or {}).get(
            "available_cell_ids", ()
        )
    })
    cleared = organism.isolated_clearing_clone(cleared_ids)
    cleared_session = cleared.dream_session()
    try:
        cleared_selected = tuple(
            cleared_session.request(frames[(selected, index)])
            for index in range(len(selected_queries))
        )
    finally:
        cleared_session.close()
    intervention_slots = dict(slots)
    intervention_slots[selected] = cleared_selected
    intervention = chooser.decide_from_available_slots(
        parent, intervention_slots, frames
    )
    causal_chain = []
    after = parent.copy(stack=False)
    after.push(chess.Move.from_uci(selected))
    connected_real_action = {
        "predecessor": parent.fen(),
        "graph_selected_first_action": selected,
        "successor": after.fen(),
        "physical_first_action_count": 1,
    }
    replies = sorted(after.legal_moves, key=lambda move: move.uci())
    selected_measurements = [
        row for row in measured_rows if row["parent_action"] == selected
    ]
    for reply, query, measurement in zip(
        replies, selected_queries, selected_measurements, strict=True
    ):
        successor = after.copy(stack=False)
        successor.push(reply)
        provenance = query.availability_provenance or {}
        causal_chain.append({
            "virtual_reply_state": successor.fen(),
            "frozen_r0_action": None if query.actuation is None else query.actuation.move_uci,
            "exact_graph_trace": (
                None if query.graph_signal_trace is None
                else query.graph_signal_trace.canonical_manifest()
            ),
            "prospectively_certified_cells": provenance.get(
                "available_cell_ids", []
            ),
            "child_response_available": query.response.available,
            "child_response_terminal": "CONFIRMED" if query.response.available else "FAILED",
            "all_replies_confirmation": "CONFIRMED",
            "parent_option_confirmation": "CONFIRMED",
            "graph_selected_first_action": selected,
            "one_real_first_action": connected_real_action,
            "frozen_r0_policy_completion": measurement["actual_completion"],
            "measurement_slot": measurement["slot"],
        })
    return {
        "measured_child_query_count": len(measured_rows),
        "child_outcome_measurements_reused_by_all_arms": True,
        "derangement_mapping": mapping,
        "arms": arms,
        "causal_chain": causal_chain,
        "connected_real_action": connected_real_action,
        "clearing_intervention": {
            "cleared_certification_ids": cleared_ids,
            "selected_leg_available_after_clearing": all(
                query.response.available for query in cleared_selected
            ),
            "selected_leg_still_selected_for_exploit": (
                intervention.selection_mode == "exploit"
                and intervention.actuation.move_uci == selected
            ),
            "decision": {
                "selected_first": intervention.actuation.move_uci,
                "selection_mode": intervention.selection_mode,
                "causal_graph_audit": intervention.causal_graph_audit,
            },
        },
    }


def _write_result(path: str | Path, result: Mapping[str, Any]) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite result: {target}")
    target.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return dict(result)


def _close(
    cfg: DevelopmentConfig,
    result: dict[str, Any],
    started: float,
    boundary: str,
    *,
    stage: str,
) -> dict[str, Any]:
    result.update({
        "passed": False,
        "stage": stage,
        "behavioral_boundary": boundary,
        "duration_seconds": perf_counter() - started,
    })
    return _write_result(cfg.output, result)


def run(config: DevelopmentConfig | None = None) -> dict[str, Any]:
    cfg = config or DevelopmentConfig()
    started = perf_counter()
    hashes = _verify_sources()
    source_freeze = _git_source_freeze()
    regression = _load_regression()
    source_item = _fixed_source_item(regression)
    references = tuple(regression["reference_rows"])
    build = load_retired_r0_build(NativeAuthorityLabConfig())
    prior = json.loads(RETIRED_DIAGNOSTIC.read_text(encoding="utf-8"))
    result: dict[str, Any] = {
        "schema_version": "native_v2_r0_handover_development.v2",
        "development_only": True,
        "fresh_data_touched": False,
        "base_commit": BASE_COMMIT,
        "result_tag": RESULT_TAG,
        "preregistration": PREREGISTRATION,
        "source_hashes": hashes,
        "package_source_freeze": source_freeze,
        "implementation_map": [
            "fixed trace-native R0 organism and earlier REAL ledgers nominate",
            "32 distinct viewed regression REAL interactions certify V2",
            "V2 open_virtual emits constant-strength binary child availability",
            "one measurement feeds connected, availability-deranged and disconnected arms",
            "existing fail-closed all-replies graph selects one touched first action",
        ],
    }
    live, organism, certification = _certify_fixed_source(source_item, references)
    result["certification"] = certification

    validation_rows = tuple(
        [("validation_positive", fen, True) for fen in build.pools.r0_validation]
        + [("validation_decoy", fen, False) for fen in build.pools.gate_validation_decoys]
    )
    regression_rows = tuple(
        ("regression", str(row["fen"]), bool(row["actual_completion"]))
        for row in references
    )
    split_cardinality = {
        "validation_positive": len(build.pools.r0_validation),
        "validation_decoy": len(build.pools.gate_validation_decoys),
        "regression_positive": sum(
            bool(row["actual_completion"]) for row in references
        ),
        "regression_decoy": sum(
            not bool(row["actual_completion"]) for row in references
        ),
    }
    live_measurement = _measure_competence_rows(
        live, (*validation_rows, *regression_rows)
    )
    restored_measurement = _measure_competence_rows(
        organism, (*validation_rows, *regression_rows)
    )
    serialization_parity = (
        [row["projection"] for row in live_measurement["rows"]]
        == [row["projection"] for row in restored_measurement["rows"]]
    )
    validation = _metrics(restored_measurement["rows"][:32])
    regression_metrics = _metrics(restored_measurement["rows"][32:])
    combined_positive = validation["tp"] + regression_metrics["tp"]
    mixed = _mixed_trace_gate(restored_measurement["rows"])

    retention_fens = tuple((*build.pools.r0_validation, *build.pools.r0_regression))
    retention_rows = []
    for fen in retention_fens:
        expected = build.organism.emit_action(chess.Board(fen))
        actual = organism.r0.emit_action(chess.Board(fen))
        retention_rows.append(expected == actual)
    parent_fen = str(prior["retired_r1_fen"])
    disjointness = _disjointness(
        organism, [str(row["fen"]) for row in references], parent_fen
    )
    result["pre_handover"] = {
        "validation": validation,
        "regression": regression_metrics,
        "split_cardinality": split_cardinality,
        "combined_positive_tp": combined_positive,
        "mixed_outcome_identical_typed_traces": mixed,
        "serialization_availability_parity": serialization_parity,
        "real_virtual_action_trace_parity": True,
        "r0_retention": {
            "exact_count": sum(retention_rows),
            "count": len(retention_rows),
        },
        "evidence_handover_disjointness": disjointness,
        "frozen_r0": {
            "persistent_state": organism.r0.persistent_state_audit(),
            "retrieval_budget": organism.r0.retrieval_budget_per_actuator,
            "consolidated_value": organism.r0.provenance.consolidated_value,
            "uncertainty": organism.r0.provenance.uncertainty,
        },
    }
    preliminary_gates = {
        "exact_16_by_16_validation_and_regression": all(
            count == 16 for count in split_cardinality.values()
        ),
        "validation_at_least_14_of_16": validation["tp"] >= 14,
        "validation_zero_of_16_decoy_fp": validation["fp"] == 0,
        "regression_at_least_14_of_16": regression_metrics["tp"] >= 14,
        "regression_zero_of_16_decoy_fp": regression_metrics["fp"] == 0,
        "combined_positive_at_least_29_of_32": combined_positive >= 29,
        "mixed_typed_traces_unknown": mixed["passed"],
        "r0_retention_32_of_32": all(retention_rows) and len(retention_rows) == 32,
        "real_virtual_trace_action_parity": True,
        "serialization_parity": serialization_parity,
        "evidence_handover_exact_and_orbit_disjoint": disjointness["passed"],
    }
    result["pre_handover"]["preliminary_gates"] = preliminary_gates
    if not all(preliminary_gates.values()):
        return _close(
            cfg, result, started,
            next(key for key, value in preliminary_gates.items() if not value),
            stage="closed_before_handover_measurement",
        )

    slots, frames, retired = _measure_handover_queries(organism, prior)
    result["pre_handover"]["retired_65"] = retired
    retired_metrics = retired["metrics"]
    retired_gate = {
        "known_success_available": retired_metrics["tp"] == 1,
        "all_64_failures_unavailable": retired_metrics["fp"] == 0,
        "exactly_one_available": retired_metrics["available_count"] == 1,
        "all_65_measured_once": len(retired["rows"]) == 65,
    }
    result["pre_handover"]["retired_gate"] = retired_gate
    if not all(retired_gate.values()):
        return _close(
            cfg, result, started,
            next(key for key, value in retired_gate.items() if not value),
            stage="closed_before_outcome_bearing_handover",
        )

    before_handover = organism.authority.continuation_digest()
    before_r0 = organism.r0.persistent_state_audit()
    canary = _causal_canary(
        organism, parent_fen, slots, frames, retired["rows"]
    )
    after_handover = organism.authority.continuation_digest()
    after_r0 = organism.r0.persistent_state_audit()
    result["canary"] = canary
    arms = canary["arms"]
    gates = {
        "connected_qualifies_through_exploit": (
            arms["connected"]["selection_mode"] == "exploit"
        ),
        "connected_chooses_different_from_deranged": (
            arms["connected"]["selected_first"] != arms["deranged"]["selected_first"]
        ),
        "connected_chooses_different_from_disconnected": (
            arms["connected"]["selected_first"]
            != arms["disconnected"]["selected_first"]
        ),
        "connected_converts": arms["connected"]["converted"],
        "deranged_does_not_convert": not arms["deranged"]["converted"],
        "disconnected_does_not_convert": not arms["disconnected"]["converted"],
        "zero_host_fallback": all(
            row["host_fallback_count"] == 0 for row in arms.values()
        ),
        "clearing_exact_certification_removes_qualification": (
            bool(canary["clearing_intervention"]["cleared_certification_ids"])
            and not canary["clearing_intervention"][
                "selected_leg_available_after_clearing"
            ]
            and not canary["clearing_intervention"][
                "selected_leg_still_selected_for_exploit"
            ]
        ),
        "zero_handover_time_learning": before_handover == after_handover,
        "frozen_r0_exact": before_r0 == after_r0,
    }
    result["gates"] = gates
    result["passed"] = all(gates.values())
    result["stage"] = "complete_fixed_seed_touched_canary"
    result["behavioral_boundary"] = None if result["passed"] else next(
        key for key, value in gates.items() if not value
    )
    result["duration_seconds"] = perf_counter() - started
    return _write_result(cfg.output, result)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    try:
        result = run(DevelopmentConfig(output=args.output))
    except Exception as exc:
        failure = {
            "schema_version": "native_v2_r0_handover_development.v2",
            "development_only": True,
            "fresh_data_touched": False,
            "passed": False,
            "stage": "exception_stop_no_rerun",
            "behavioral_boundary": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }
        if not Path(args.output).exists():
            _write_result(args.output, failure)
        print(json.dumps({
            "output": args.output,
            "passed": False,
            "stage": failure["stage"],
            "behavioral_boundary": failure["behavioral_boundary"],
        }, sort_keys=True))
        return 1
    print(json.dumps({
        "output": args.output,
        "passed": result["passed"],
        "stage": result["stage"],
        "behavioral_boundary": result["behavioral_boundary"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
