"""Viewed-data V2 competence development and native R0->R1 handover.

This package ports the prospective-evidence mechanism, not the synthetic V2
organism.  It intentionally adds no learner, transport, registry, or launcher.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import gzip
import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Sequence

import chess

from recon_lite import ChildResponse, FrameContext, FrameKind

from .native_authority_handover import ChildQuery, NativeHandoverGenome
from .native_authority_lab import NativeAuthorityLabConfig, load_retired_r0_build
from .native_child_availability import (
    FailClosedNativeHandoverGenome,
    observe_query_completion,
    observe_real_child,
    response_with_availability,
)
from .native_competence_envelope import AvailabilityState, EnvelopeClassification
from .native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    V2Mode,
)
from .native_trace_competence_authority import TraceNativeCompetenceOrganism


BASE_COMMIT = "00c1330dc096f977738bebeb041a6fab8146e572"
RESULT_TAG = "tg26m-v2-portable-outcome-result"
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
EXPECTED_HASHES = {
    str(REGRESSION_ARTIFACT): (
        "eb60826db7269b1fb69cd2abe21d137bb1853503cd8177e69aeb36050a77ecf4"
    ),
    str(RETIRED_DIAGNOSTIC): (
        "e946abccb4e846ca260f034174c6f440683155ebf17b617c0de8b2ae3a5baf2b"
    ),
    "reports/autogrowth/native_authority/retired_r1_handover_development.json": (
        "efc63749f2f99b0e8b3a729b3bdf99b416639e40f682d730a5a709f7de79db4d"
    ),
    "snapshots/autogrowth/native_authority/r0_organism.pkl": (
        "bb58b7d64bd3ab5b696713a7253555e051bd0e9fdef4637db7c27e7517495eaf"
    ),
    "reports/autogrowth/native_from_scratch/"
    "r0_r1_balanced96_240_seed_20260719_compact.json": (
        "c55a4097547713edb5d9ef27a250bbfac62fb9886d86afae87b387b72869c792"
    ),
    "src/recon_lite_chess/autogrowth/"
    "native_prospective_evidence_authority_v2.py": (
        "25945864fd998caf22ae12cbcb9bcb4779447337c0079f705640c63d2356f029"
    ),
    "src/recon_lite_chess/autogrowth/native_authority_handover.py": (
        "b65fc61f05f1ecda992e44e5baa1e98daeec53495573c0a5b6ec24b3fc68f445"
    ),
    "src/recon_lite_chess/autogrowth/native_child_availability.py": (
        "c3739bdd5d9cc1b4f8bf1774027d9501dc0f68b234214f30a66a9478ec26936a"
    ),
}


PREREGISTRATION = {
    "hypothesis": (
        "later REAL completion evidence makes native R0 competence selective "
        "enough to improve viewed Mate-in-2 conversion"
    ),
    "null": "no selective availability or no conversion gain over both controls",
    "single_factor": (
        "child availability source: V2-certified versus disconnected versus "
        "legacy any-policy-response"
    ),
    "information_boundary": (
        "board, legal actions, graph trace, and observed REAL checkmate only; "
        "labels are post-hoc metrics and VIRTUAL frames cannot certify"
    ),
    "selectivity_gate": {
        "safe_narrow_seed_count_min": 1,
        "aggregate_tp_strictly_exceeds_fp": True,
        "all_positive_seed_count_max": 0,
    },
    "success_gate": {
        "exact_r0_retention": True,
        "zero_host_fallback": True,
        "zero_virtual_mutation": True,
        "non_all_positive": True,
        "causal_connected_action_difference_min": 1,
        "connected_conversion_strictly_exceeds_each_control": True,
        "unchanged_v2_core": True,
    },
    "compute_change_budget": {
        "sources": 32,
        "later_real_certification_rows_per_source": 32,
        "selectivity_rows_per_source": 65,
        "handover_rows": 16,
        "shared_runtime_changes": 0,
        "fresh_rows": 0,
    },
    "kill_rule": (
        "preserve the first failed gate; do not tune thresholds, add a mechanism, "
        "extend evidence lifetime, or open fresh rows"
    ),
}


@dataclass(frozen=True)
class DevelopmentConfig:
    output: str = str(DEFAULT_OUTPUT)
    sources: int = 32
    certification_rows: int = 32
    handover_train_rows: int = 8
    handover_evaluation_rows: int = 8


class NativeV2R0CompetenceOrganism:
    """Serializable V2 authority with the existing child dream interface."""

    def __init__(self, authority: NativeProspectiveAuthorityV2) -> None:
        if authority.mode is not V2Mode.PROSPECTIVE:
            raise ValueError("handover requires the prospective V2 arm")
        if authority.pending_event is not None:
            raise ValueError("handover cannot open with a pending REAL event")
        authority._verify_invariants()
        self.authority = authority

    @property
    def r0(self):
        return self.authority.base.r0

    def dream_session(self) -> "NativeV2R0DreamSession":
        return NativeV2R0DreamSession(self)

    def dumps(self) -> bytes:
        return self.authority.dumps()

    @classmethod
    def loads(cls, payload: bytes) -> "NativeV2R0CompetenceOrganism":
        return cls(NativeProspectiveAuthorityV2.loads(payload))


class NativeV2R0DreamSession:
    """Read V2 graph availability from isolated native VIRTUAL traces."""

    def __init__(self, organism: NativeV2R0CompetenceOrganism) -> None:
        self.organism = organism
        self.before = organism.authority.continuation_digest()
        self.closed = False

    def request(self, frame: FrameContext) -> ChildQuery:
        if self.closed:
            raise RuntimeError("V2 R0 dream session is closed")
        opened = self.organism.authority.open_virtual(frame)
        query = opened["query"]
        if opened["certification_commitment"] is not None:
            raise RuntimeError("VIRTUAL request created certification evidence")
        trace = query.graph_signal_trace
        classification = (
            EnvelopeClassification(
                AvailabilityState.UNKNOWN, 0.5, 1.0, (), (), False, False, False
            )
            if trace is None
            else self.organism.authority._classification_from_emissions(
                self.organism.authority.states,
                self.organism.authority._graph_measure(trace),
            )
        )
        available = classification.state is AvailabilityState.AVAILABLE
        r0 = self.organism.r0
        result = ChildQuery(
            response=ChildResponse(
                child_id=r0.provenance.child_id,
                confirmed=available,
                policy_response=query.actuation is not None,
                available=available,
                expected_value=(
                    r0.provenance.consolidated_value if available else 0.0
                ),
                uncertainty=classification.uncertainty,
                grounded=r0.provenance.grounded,
                grounding_source=r0.provenance.grounding_source,
            ),
            actuation=query.actuation,
            frame_id=query.frame_id,
            persistent_mutation_count=query.persistent_mutation_count,
            effect_attempts=query.effect_attempts,
            active_competence_signal_ids=(
                () if trace is None else trace.ordered_signal_identities
            ),
            availability_provenance={
                "authority": "NativeProspectiveAuthorityV2_graph_emission",
                "classification": classification.to_manifest(),
                "certification_evidence_added": 0,
            },
            graph_signal_trace=trace,
        )
        if self.organism.authority.continuation_digest() != self.before:
            raise RuntimeError("VIRTUAL handover query mutated V2 authority")
        return result

    def close(self) -> None:
        if self.organism.authority.continuation_digest() != self.before:
            raise RuntimeError("V2 R0 dream session leaked persistent state")
        self.closed = True


def _sha_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _sha_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")).hexdigest()


def _verify_sources() -> dict[str, str]:
    actual = {path: _sha_file(path) for path in EXPECTED_HASHES}
    changed = {
        path: {"expected": EXPECTED_HASHES[path], "actual": digest}
        for path, digest in actual.items()
        if digest != EXPECTED_HASHES[path]
    }
    if changed:
        raise RuntimeError(f"frozen source changed: {changed}")
    return actual


def _load_regression() -> dict[str, Any]:
    with gzip.open(REGRESSION_ARTIFACT, "rt", encoding="utf-8") as stream:
        result = json.load(stream)
    if (
        not result["gates"]["integrity"]
        or len(result["reference_rows"]) != 32
        or len(result["organisms"]) != 96
        or result["interpretation"] != "specialized_contexts_overgeneralize"
    ):
        raise RuntimeError("historical regression authority is incomplete")
    return result


def _load_source(item: Mapping[str, Any]) -> TraceNativeCompetenceOrganism:
    path = Path(str(item["path"]))
    compressed = path.read_bytes()
    if hashlib.sha256(compressed).hexdigest() != item["compressed_sha256"]:
        raise RuntimeError("source organism compressed hash mismatch")
    raw = gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest() != item["uncompressed_sha256"]:
        raise RuntimeError("source organism raw hash mismatch")
    source = TraceNativeCompetenceOrganism.loads(raw)
    if source.continuation_digest_v3() != item["continuation_v3_sha256"]:
        raise RuntimeError("source organism continuation mismatch")
    return source


def _local_sources(regression: Mapping[str, Any], count: int) -> list[dict[str, Any]]:
    rows = sorted(
        (item["source_artifact"] for item in regression["organisms"]
         if item["arm"] == "local_contrast_specialization"),
        key=lambda item: int(item["ordinal"]),
    )
    if len(rows) != 32 or count != 32:
        raise RuntimeError("this frozen package requires all 32 source organisms")
    return rows


def _certify(
    source_item: Mapping[str, Any],
    reference_rows: Sequence[Mapping[str, Any]],
) -> tuple[NativeV2R0CompetenceOrganism, dict[str, Any]]:
    source = _load_source(source_item)
    authority = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    frozen = authority.close_nomination()
    identity_before = authority.experimental_identity
    candidate_digest = _sha_json(list(frozen))
    parity_failures: list[dict[str, Any]] = []
    matured = revoked = 0
    for reference in reference_rows:
        row_index = int(reference["row_index"])
        predecessor = chess.Board(str(reference["fen"]))
        pending, trace = authority.open_real_event(FrameContext(
            frame_id=f"trace-regression-real:{row_index}",
            kind=FrameKind.REAL,
            values={"board": predecessor},
        ))
        if asdict(trace.actuation) != reference["actuation"]:
            parity_failures.append({"row": row_index, "field": "actuation"})
        if trace.digest() != reference["trace_digest"]:
            parity_failures.append({"row": row_index, "field": "trace_digest"})
        successor = predecessor.copy(stack=False)
        successor.push(chess.Move.from_uci(trace.actuation.move_uci))
        if successor.is_checkmate() != bool(reference["actual_completion"]):
            parity_failures.append({"row": row_index, "field": "completion"})
        receipt = authority.mint_environment_receipt(
            pending_token=pending.pending_token,
            trace=trace,
            predecessor=predecessor,
            successor=successor,
        )
        emission = authority.consume(receipt)
        matured += len(emission.graph_maturity_ids)
        revoked += len(emission.graph_revocation_ids)
    if parity_failures:
        raise RuntimeError(f"viewed REAL replay mismatch: {parity_failures}")
    if authority.experimental_identity != identity_before:
        raise RuntimeError("candidate identity changed during certification")
    payload = NativeV2R0CompetenceOrganism(authority).dumps()
    restored = NativeV2R0CompetenceOrganism.loads(payload)
    if restored.authority.continuation_digest() != authority.continuation_digest():
        raise RuntimeError("serialized V2 R0 authority changed on restore")
    clearings = sum(
        row["transition"] == "GRAPH_LOCAL_REVOCATION"
        for state in restored.authority.states.values()
        for row in state.transition_rows
    )
    return restored, {
        "ordinal": int(source_item["ordinal"]),
        "genome_seed": int(source_item["genome_seed"]),
        "candidate_count": len(frozen),
        "candidate_digest": candidate_digest,
        "later_real_interactions": len(reference_rows),
        "graph_maturity_emissions": matured,
        "graph_revocation_emissions": revoked,
        "contradiction_driven_clearings": clearings,
        "final_certified_cell_count": sum(
            state.prospectively_certified
            for state in restored.authority.states.values()
        ),
        "serialization": {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "roundtrip_exact": True,
        },
    }


def _state(query: ChildQuery) -> str:
    provenance = query.availability_provenance or {}
    classification = provenance.get("classification", {})
    return str(classification.get("state", AvailabilityState.UNKNOWN.value))


def _selectivity_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "abstentions": 0}
    positive_abstentions = negative_abstentions = 0
    for row in rows:
        state = row["state"]
        actual = bool(row["actual_completion"])
        if state == AvailabilityState.AVAILABLE.value:
            counts["tp" if actual else "fp"] += 1
        elif state == AvailabilityState.REFUTED.value:
            counts["fn" if actual else "tn"] += 1
        else:
            counts["abstentions"] += 1
            if actual:
                positive_abstentions += 1
            else:
                negative_abstentions += 1
    available = counts["tp"] + counts["fp"]
    resolved = sum(counts[key] for key in ("tp", "fp", "tn", "fn"))
    return {
        **counts,
        "positive_abstentions": positive_abstentions,
        "negative_abstentions": negative_abstentions,
        "available_count": available,
        "availability_coverage": available / max(1, len(rows)),
        "resolved_coverage": resolved / max(1, len(rows)),
        "precision": None if available == 0 else counts["tp"] / available,
        "safe_narrow": counts["tp"] > 0 and counts["fp"] == 0,
        "all_positive": available == len(rows),
    }


def _measure_retired_selectivity(
    organism: NativeV2R0CompetenceOrganism,
    prior: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, tuple[ChildQuery, ...]], dict[Any, Any]]:
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
            actual = {
                "parent_action": action,
                "black_reply": reply.uci(),
                "reply_index": index,
                "successor_fen": successor.fen(),
                "policy_response": bool(query.response.policy_response),
                "policy_action": None if query.actuation is None else query.actuation.move_uci,
                "policy_success": observed.completion_confirmed,
            }
            for key, value in actual.items():
                if reference[key] != value:
                    raise RuntimeError(f"retired successor parity mismatch: {cursor}:{key}")
            rows.append({
                "slot": cursor,
                "parent_action": action,
                "black_reply": reply.uci(),
                "actual_completion": observed.completion_confirmed,
                "state": _state(query),
                "available": query.response.available,
            })
            cursor += 1
    if cursor != 65 or cursor != len(expected):
        raise RuntimeError("retired 65-successor cardinality changed")
    if organism.authority.continuation_digest() != before:
        raise RuntimeError("retired VIRTUAL evaluation mutated authority")
    return _selectivity_metrics(rows), slots, frames


def _retention(
    organism: NativeV2R0CompetenceOrganism,
    reference_r0: Any,
    fens: Sequence[str],
) -> dict[str, Any]:
    rows = []
    for fen in fens:
        expected = reference_r0.emit_action(chess.Board(fen))
        actual = organism.r0.emit_action(chess.Board(fen))
        rows.append({
            "fen": fen,
            "expected": None if expected is None else expected.move_uci,
            "actual": None if actual is None else actual.move_uci,
            "exact": expected == actual,
        })
    return {
        "count": len(rows),
        "exact_count": sum(row["exact"] for row in rows),
        "exact": all(row["exact"] for row in rows),
    }


def _control_slots(
    r0: Any,
    slots: Mapping[str, tuple[ChildQuery, ...]],
) -> dict[str, tuple[ChildQuery, ...]]:
    return {
        action: tuple(
            response_with_availability(
                r0, query, available=bool(query.response.policy_response)
            )
            for query in queries
        )
        for action, queries in slots.items()
    }


def _evaluate_selected_action(r0: Any, parent: chess.Board, decision: Any) -> dict[str, Any]:
    selected = decision.actuation.move_uci
    after = parent.copy(stack=False)
    after.push(chess.Move.from_uci(selected))
    replies = []
    for reply in sorted(after.legal_moves, key=lambda move: move.uci()):
        successor = after.copy(stack=False)
        successor.push(reply)
        observed = observe_real_child(r0, successor)
        replies.append({
            "reply": reply.uci(),
            "child_action": None if observed.actuation is None else observed.actuation.move_uci,
            "completed": observed.completion_confirmed,
        })
    return {
        "selected_first": selected,
        "converted": bool(replies and all(row["completed"] for row in replies)),
        "selection_mode": decision.selection_mode,
        "host_fallback_count": decision.host_fallback_count,
        "actuator_multiplicity": decision.actuator_multiplicity,
        "all_reply_available_action_count": sum(
            bool(queries) and all(query.response.available for query in queries)
            for queries in decision.response_slots.values()
        ),
        "replies": replies,
    }


def _handover_rows(
    organism: NativeV2R0CompetenceOrganism,
    fens: Sequence[tuple[str, str]],
) -> dict[str, Any]:
    genome = NativeHandoverGenome()
    chooser = FailClosedNativeHandoverGenome()
    before = organism.authority.continuation_digest()
    rows = []
    for split, fen in fens:
        parent = chess.Board(fen)
        connected_slots, frames = genome.query_child_slots(parent, organism)
        any_slots = _control_slots(organism.r0, connected_slots)
        decisions = {
            "connected": chooser.decide_from_available_slots(
                parent, connected_slots, frames
            ),
            "disconnected": chooser.decide_from_available_slots(
                parent, connected_slots, frames, disconnected=True
            ),
            "any_policy_response": chooser.decide_from_available_slots(
                parent, any_slots, frames
            ),
        }
        arms = {
            name: _evaluate_selected_action(organism.r0, parent, decision)
            for name, decision in decisions.items()
        }
        rows.append({
            "split": split,
            "fen": fen,
            "arms": arms,
            "connected_differs_from_disconnected": (
                arms["connected"]["selected_first"]
                != arms["disconnected"]["selected_first"]
            ),
            "connected_differs_from_any": (
                arms["connected"]["selected_first"]
                != arms["any_policy_response"]["selected_first"]
            ),
            "causal_connected_win": (
                arms["connected"]["converted"]
                and not arms["disconnected"]["converted"]
                and not arms["any_policy_response"]["converted"]
                and arms["connected"]["selected_first"]
                != arms["disconnected"]["selected_first"]
                and arms["connected"]["selected_first"]
                != arms["any_policy_response"]["selected_first"]
            ),
            "virtual_mutation_count": sum(
                query.persistent_mutation_count
                for queries in connected_slots.values() for query in queries
            ),
        })
    if organism.authority.continuation_digest() != before:
        raise RuntimeError("handover VIRTUAL evaluation mutated authority")
    summary = {}
    for arm in ("connected", "disconnected", "any_policy_response"):
        summary[arm] = {
            "conversion_count": sum(row["arms"][arm]["converted"] for row in rows),
            "position_count": len(rows),
            "host_fallback_count": sum(
                row["arms"][arm]["host_fallback_count"] for row in rows
            ),
            "multiplicity_failures": sum(
                row["arms"][arm]["actuator_multiplicity"] != 1 for row in rows
            ),
        }
    return {"summary": summary, "rows": rows}


def run(config: DevelopmentConfig | None = None) -> dict[str, Any]:
    cfg = config or DevelopmentConfig()
    started = perf_counter()
    hashes = _verify_sources()
    regression = _load_regression()
    prior = json.loads(RETIRED_DIAGNOSTIC.read_text(encoding="utf-8"))
    build = load_retired_r0_build(NativeAuthorityLabConfig())
    sources = _local_sources(regression, cfg.sources)
    references = tuple(regression["reference_rows"][: cfg.certification_rows])
    if len(references) != 32:
        raise RuntimeError("the frozen certification tape requires 32 rows")
    result: dict[str, Any] = {
        "schema_version": "native_v2_r0_handover_development.v1",
        "development_only": True,
        "fresh_data_touched": False,
        "base_commit": BASE_COMMIT,
        "result_tag": RESULT_TAG,
        "implementation_map": [
            "TraceNativeCompetenceOrganism viewed REAL ledgers nominate fixed-polarity candidates",
            "NativeProspectiveAuthorityV2 consumes 32 later distinct viewed REAL interactions",
            "NativeV2R0CompetenceOrganism serializes and emits read-only V2 graph availability",
            "NativeHandoverGenome.query_child_slots enumerates legal first actions and Black replies",
            "FailClosedNativeHandoverGenome performs existing all-replies graph choice",
        ],
        "preregistration": PREREGISTRATION,
        "source_hashes": hashes,
        "rows": {
            "certification": len(references),
            "retired_selectivity": 65,
            "fresh": 0,
        },
        "seeds": [],
    }
    learned: list[NativeV2R0CompetenceOrganism] = []
    for source_item in sources:
        organism, certification = _certify(source_item, references)
        selectivity, _slots, _frames = _measure_retired_selectivity(organism, prior)
        learned.append(organism)
        result["seeds"].append({
            "ordinal": certification["ordinal"],
            "genome_seed": certification["genome_seed"],
            "certification": certification,
            "selectivity": selectivity,
        })
    aggregate = {
        key: sum(row["selectivity"][key] for row in result["seeds"])
        for key in ("tp", "fp", "tn", "fn", "abstentions")
    }
    safe_narrow = sum(row["selectivity"]["safe_narrow"] for row in result["seeds"])
    all_positive = sum(row["selectivity"]["all_positive"] for row in result["seeds"])
    selectivity_gate = {
        "safe_narrow_seed_count_at_least_one": safe_narrow >= 1,
        "aggregate_tp_strictly_exceeds_fp": aggregate["tp"] > aggregate["fp"],
        "zero_all_positive_seeds": all_positive == 0,
    }
    result["selectivity"] = {
        "aggregate": aggregate,
        "safe_narrow_seed_count": safe_narrow,
        "all_positive_seed_count": all_positive,
        "gate": selectivity_gate,
        "passed": all(selectivity_gate.values()),
    }
    if not result["selectivity"]["passed"]:
        result.update({
            "passed": False,
            "stage": "closed_before_handover",
            "behavioral_boundary": "real_r0_competence_not_nontrivially_selective",
            "duration_seconds": perf_counter() - started,
        })
        return _write_result(cfg.output, result)

    retention_fens = tuple((*build.pools.r0_validation, *build.pools.r0_regression))
    retention = [
        _retention(organism, build.organism, retention_fens)
        for organism in learned
    ]
    result["r0_retention"] = {
        "per_seed": retention,
        "exact_seed_count": sum(row["exact"] for row in retention),
        "passed": all(row["exact"] and row["count"] == 32 for row in retention),
    }
    if not result["r0_retention"]["passed"]:
        result.update({
            "passed": False,
            "stage": "closed_before_handover",
            "behavioral_boundary": "r0_retention",
            "duration_seconds": perf_counter() - started,
        })
        return _write_result(cfg.output, result)

    train = tuple(build.pools.r1_train[: cfg.handover_train_rows])
    evaluation = tuple(
        (*build.pools.r1_validation, *build.pools.r1_regression)
    )[: cfg.handover_evaluation_rows]
    handover_fens = tuple(
        [("train", fen) for fen in train]
        + [("evaluation", fen) for fen in evaluation]
    )
    if len(handover_fens) != 16:
        raise RuntimeError("the frozen handover development tape requires 16 rows")
    handover = []
    for seed_row, organism in zip(result["seeds"], learned, strict=True):
        measured = _handover_rows(organism, handover_fens)
        handover.append({
            "ordinal": seed_row["ordinal"],
            "genome_seed": seed_row["genome_seed"],
            **measured,
        })
    totals = {
        arm: sum(row["summary"][arm]["conversion_count"] for row in handover)
        for arm in ("connected", "disconnected", "any_policy_response")
    }
    causal = sum(
        row["causal_connected_win"]
        for seed in handover for row in seed["rows"]
    )
    action_differences = {
        "versus_disconnected": sum(
            row["connected_differs_from_disconnected"]
            for seed in handover for row in seed["rows"]
        ),
        "versus_any_policy_response": sum(
            row["connected_differs_from_any"]
            for seed in handover for row in seed["rows"]
        ),
    }
    gates = {
        "exact_r0_retention": result["r0_retention"]["passed"],
        "zero_host_fallback": all(
            seed["summary"][arm]["host_fallback_count"] == 0
            for seed in handover
            for arm in ("connected", "disconnected", "any_policy_response")
        ),
        "exactly_one_actuator": all(
            seed["summary"][arm]["multiplicity_failures"] == 0
            for seed in handover
            for arm in ("connected", "disconnected", "any_policy_response")
        ),
        "zero_persistent_virtual_learning": all(
            row["virtual_mutation_count"] == 0
            for seed in handover for row in seed["rows"]
        ),
        "selective_not_all_positive": all_positive == 0,
        "causal_first_action_difference": causal >= 1,
        "connected_improves_over_disconnected": (
            totals["connected"] > totals["disconnected"]
        ),
        "connected_improves_over_any_policy_response": (
            totals["connected"] > totals["any_policy_response"]
        ),
        "unchanged_v2_core_semantics": (
            _sha_file(
                "src/recon_lite_chess/autogrowth/"
                "native_prospective_evidence_authority_v2.py"
            )
            == EXPECTED_HASHES[
                "src/recon_lite_chess/autogrowth/"
                "native_prospective_evidence_authority_v2.py"
            ]
        ),
    }
    result["handover"] = {
        "row_order": [dict(split=split, fen=fen) for split, fen in handover_fens],
        "row_order_digest": _sha_json(handover_fens),
        "per_seed": handover,
        "conversion_totals": totals,
        "position_seed_count": len(handover) * len(handover_fens),
        "causal_connected_win_count": causal,
        "action_differences": action_differences,
    }
    result["gates"] = gates
    result["passed"] = all(gates.values())
    result["stage"] = "complete_touched_r0_r1_development"
    result["behavioral_boundary"] = None if result["passed"] else next(
        key for key, value in gates.items() if not value
    )
    result["duration_seconds"] = perf_counter() - started
    return _write_result(cfg.output, result)


def _write_result(path: str | Path, result: Mapping[str, Any]) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite result: {target}")
    payload = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    target.write_text(payload, encoding="utf-8")
    return dict(result)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    result = run(DevelopmentConfig(output=args.output))
    print(json.dumps({
        "output": args.output,
        "passed": result["passed"],
        "stage": result["stage"],
        "behavioral_boundary": result["behavioral_boundary"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
