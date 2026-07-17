"""Preregistered deterministic touched-data competence-envelope V3."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
import hashlib
from itertools import combinations
import json
from pathlib import Path
import random
import struct
from time import perf_counter
from typing import Any, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.nodes import StemCellState

from .native_authority_handover import native_authority_tripwires
from .native_authority_lab import NativeAuthorityLabConfig, load_retired_r0_build
from .native_competence_envelope import (
    AvailabilityState,
    CompetenceContextGrowthGenome,
    CompetenceEvidenceRecord,
    GraphNativeCompetenceEnvelope,
    NativeR0CompetenceOrganism,
)
from .native_competence_envelope_experiment import EXPECTED, _hash_json, _hash_list
from .native_competence_envelope_v2_training import (
    GLOBAL_EVIDENCE_RATE,
    OUTCOME_SHUFFLE_SEED,
    _arm_report,
    _artifact_observation,
    _global_evidence_control,
    _observe,
)


OUTPUT = (
    "reports/autogrowth/native_authority/"
    "touched_r0_competence_envelope_v3_training_only.json"
)
V2_MODULE = (
    "src/recon_lite_chess/autogrowth/"
    "native_competence_envelope_v2_training.py"
)
V2_MODULE_SHA256 = "b2f499131b7628faa1211273c298070c693e94f767a59c9ae7510019e67e9341"
LEARNER_MODULE = (
    "src/recon_lite_chess/autogrowth/native_competence_envelope.py"
)
LEARNER_MODULE_SHA256 = "65dda4f09bc1181a6fe3780c27b56da4fc888a377ae3cfffe3c728e9d11d2a7b"
DETERMINISTIC_CLOSURE = (
    "reports/autogrowth/native_authority/"
    "deterministic_native_activation_closure.json"
)
DETERMINISTIC_CLOSURE_SHA256 = (
    "d0940d7375aacd647b0d390c93d2c37f0308636569236740e7a1497ce32445b7"
)
TAPE_SEED = 2026071601
EXAMPLE_CAP_PER_ARITY = 8
ACTUATION_FIELDS = (
    "actuator_identity", "move_uci", "option_identity", "activation",
    "candidate_count", "formal_ticks", "graph_owned", "host_fallback",
)


@dataclass(frozen=True)
class V3TrainingConfig:
    output: str = OUTPUT
    source_artifact: str = (
        "reports/autogrowth/native_from_scratch/"
        "r0_r1_balanced96_240_seed_20260719_compact.json"
    )
    source_organism: str = (
        "snapshots/autogrowth/native_authority/r0_organism.pkl"
    )
    build_report: str = (
        "reports/autogrowth/native_authority/r0_organism_build.json"
    )


def run_touched_competence_envelope_v3_training(
    config: V3TrainingConfig | None = None,
) -> Mapping[str, Any]:
    cfg = config or V3TrainingConfig()
    started = perf_counter()
    source_hashes = {
        V2_MODULE: _file_sha256(V2_MODULE),
        LEARNER_MODULE: _file_sha256(LEARNER_MODULE),
        DETERMINISTIC_CLOSURE: _file_sha256(DETERMINISTIC_CLOSURE),
    }
    expected_hashes = {
        V2_MODULE: V2_MODULE_SHA256,
        LEARNER_MODULE: LEARNER_MODULE_SHA256,
        DETERMINISTIC_CLOSURE: DETERMINISTIC_CLOSURE_SHA256,
    }
    if source_hashes != expected_hashes:
        raise RuntimeError("a frozen V3 source or prerequisite changed")

    build = load_retired_r0_build(NativeAuthorityLabConfig(
        source_artifact=cfg.source_artifact,
        organism_path=cfg.source_organism,
        build_report_path=cfg.build_report,
    ))
    organism = build.organism
    tape = [
        {"historical_pool_name": "r0_train", "fen": fen}
        for fen in build.pools.r0_train
    ] + [
        {"historical_pool_name": "train_decoy", "fen": fen}
        for fen in build.pools.gate_train_decoys
    ]
    random.Random(TAPE_SEED).shuffle(tape)
    legacy_tape = [{
        "class": (
            "positive"
            if row["historical_pool_name"] == "r0_train"
            else "failure"
        ),
        "fen": row["fen"],
    } for row in tape]
    if _hash_json(legacy_tape) != EXPECTED["tape"]:
        raise RuntimeError("V3 touched tape changed")

    result: dict[str, Any] = {
        "schema_version": "touched_r0_competence_envelope_v3_training_only.v1",
        "preregistered_training_only": True,
        "source_deterministic_closure_commit": "133ba03",
        "frozen_source_hashes": source_hashes,
        "historical_pool_names_are_provenance_only": True,
        "architectural_debt": {
            "mechanism": "extract_active_competence_signals",
            "current_authority": (
                "generic label-blind reconstruction from board, selected move, "
                "and graph maps"
            ),
            "missing_authority": "actual frame-local terminal trace provenance",
            "invalidates_v3": False,
            "blocks_fully_self_contained_native_claim": True,
            "changed_in_v3": False,
        },
        "validation_touched": False,
        "regression_touched": False,
        "retired_successors_touched": False,
        "r1_touched": False,
        "fresh_data_touched": False,
        "global_evidence_rate": GLOBAL_EVIDENCE_RATE,
        "stage": "admission",
    }
    r0_before = organism.persistent_state_audit()
    with native_authority_tripwires() as tripwires:
        reference_rows, reference_state = _deterministic_reference_rows(
            organism, tape
        )
        observations = [
            _observe(
                organism,
                row["fen"],
                row["historical_pool_name"],
                index,
            )
            for index, row in enumerate(tape)
        ]
        r0_after_admission = organism.persistent_state_audit()
        admission = _admission_v3(
            observations,
            reference_rows,
            direct_persistent_identity=r0_before == r0_after_admission,
            wrapper_persistent_identity=reference_state["before"]
            == reference_state["after"],
        )
        result.update({
            "deterministic_reference": {
                "count": len(reference_rows),
                "sha256": _hash_json(reference_rows),
                "rows": reference_rows,
                "persistent_state": reference_state,
            },
            "admission": admission,
            "authority_tripwires": dict(tripwires),
        })
        # Persist exact admission evidence before any possible early stop.
        _write_result(cfg.output, result)
        if not admission["passed"] or any(tripwires.values()):
            result.update({
                "stage": "closed_before_learning",
                "binding_boundary": "evidence_admission",
                "passed": False,
                "duration_seconds": perf_counter() - started,
                "next_action": "preserve_v3_admission_failure",
            })
            return _write_result(cfg.output, result)

        records = tuple(row["evidence"] for row in observations)
        connected = GraphNativeCompetenceEnvelope()
        connected.grow(
            records,
            genome=CompetenceContextGrowthGenome(
                connected.config.selection_seed
            ),
        )
        permutation = list(range(64))
        random.Random(OUTCOME_SHUFFLE_SEED).shuffle(permutation)
        if _hash_list(permutation) != EXPECTED["outcome_perm"]:
            raise RuntimeError("V3 outcome permutation changed")
        outcomes = [record.observed_completion for record in records]
        shuffled_records = tuple(
            replace(
                record,
                observed_completion=outcomes[permutation[index]],
            )
            for index, record in enumerate(records)
        )
        shuffled = GraphNativeCompetenceEnvelope()
        shuffled.grow(
            shuffled_records,
            genome=CompetenceContextGrowthGenome(
                shuffled.config.selection_seed
            ),
        )
        r0_final = organism.persistent_state_audit()
        diagnostic = enumerate_bounded_pure_base_patterns(
            records, connected
        )
        verdict = diagnostic["verdict"]
        connected_report = _arm_report(connected, records)
        shuffled_report = _arm_report(shuffled, records)
        arm_comparison = _arm_comparison(
            records, connected, shuffled,
            connected_report, shuffled_report,
        )
        result.update({
            "stage": "closed_after_lifecycle",
            "binding_boundary": verdict,
            "training_rows": [
                _artifact_observation(row) for row in observations
            ],
            "frozen_config": asdict(connected.config),
            "outcome_shuffle": {
                "seed": OUTCOME_SHUFFLE_SEED,
                "permutation_sha256": _hash_list(permutation),
                "permutation": permutation,
            },
            "arms": {
                "connected": connected_report,
                "outcome_shuffled": shuffled_report,
            },
            "connected_vs_outcome_shuffled": arm_comparison,
            "global_evidence_control": _global_evidence_control(records),
            "post_run_laboratory_diagnostic": diagnostic,
            "r0_persistent_state": {
                "before": r0_before,
                "after_admission": r0_after_admission,
                "final": r0_final,
            },
            "authority_tripwires": dict(tripwires),
        })

    integrity = {
        "frozen_sources_exact": source_hashes == expected_hashes,
        "admission_passed": admission["passed"],
        "connected_three_rounds": (
            len(connected.audit.lifecycle_reviews)
            == connected.config.structural_rounds == 3
        ),
        "shuffled_three_rounds": (
            len(shuffled.audit.lifecycle_reviews)
            == shuffled.config.structural_rounds == 3
        ),
        "same_frozen_config": connected.config == shuffled.config,
        "global_evidence_exact_0_625": GLOBAL_EVIDENCE_RATE == 40 / 64,
        "zero_r0_mutation": r0_before == r0_after_admission == r0_final,
        "zero_authority_tripwires": all(
            value == 0 for value in result["authority_tripwires"].values()
        ),
        "stopped_after_lifecycle": True,
        "diagnostic_read_only_and_bounded": (
            diagnostic["read_only_no_learning_feedback"]
            and diagnostic["full_pattern_records_persisted"] is False
        ),
        "no_downstream_data": True,
    }
    result.update({
        "integrity": integrity,
        "passed": all(integrity.values()),
        "duration_seconds": perf_counter() - started,
        "next_action": "stop_for_external_review",
    })
    return _write_result(cfg.output, result)


def _deterministic_reference_rows(
    organism: Any,
    tape: Sequence[Mapping[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, Mapping[str, str]]]:
    wrapper = NativeR0CompetenceOrganism.loads(
        NativeR0CompetenceOrganism(
            organism, GraphNativeCompetenceEnvelope()
        ).dumps()
    )
    before = wrapper.persistent_state_audit()
    session = wrapper.dream_session()
    rows: list[dict[str, Any]] = []
    try:
        for index, item in enumerate(tape):
            query = session.request(FrameContext(
                frame_id=f"v3-reference:{index}",
                kind=FrameKind.VIRTUAL,
                values={"board": chess.Board(item["fen"])},
            ))
            if query.actuation is None:
                raise RuntimeError("V3 deterministic reference emitted no action")
            rows.append({
                "index": index,
                "historical_pool_name": item["historical_pool_name"],
                "fen": item["fen"],
                "actuation": asdict(query.actuation),
                "activation_ieee754": _float_bits(
                    query.actuation.activation
                ),
                "active_competence_signal_ids": list(
                    query.active_competence_signal_ids
                ),
            })
    finally:
        session.close()
    after = wrapper.persistent_state_audit()
    return rows, {"before": before, "after": after}


def _admission_v3(
    rows: Sequence[Mapping[str, Any]],
    reference_rows: Sequence[Mapping[str, Any]],
    *,
    direct_persistent_identity: bool,
    wrapper_persistent_identity: bool,
) -> dict[str, Any]:
    successes = sum(bool(row["completion"]) for row in rows)
    failures = len(rows) - successes
    mismatch_rows = parity_mismatch_rows(rows, reference_rows)
    gates = {
        "count_64": len(rows) == len(reference_rows) == 64,
        "exact_40_successes": successes == 40,
        "exact_24_failures": failures == 24,
        "policy_responses_64": all(
            row["evidence"].policy_response for row in rows
        ),
        "unique_evidence_64": (
            len({row["evidence"].evidence_key for row in rows}) == 64
        ),
        "zero_fabricated_reward": all(
            not row["fabricated_reward"] for row in rows
        ),
        "direct_persistent_identity": direct_persistent_identity,
        "wrapper_persistent_identity": wrapper_persistent_identity,
        "bit_exact_deterministic_path_parity": not mismatch_rows,
    }
    failed_gate_rows = [
        {"field": f"admission.gates.{name}", "real_value": value,
         "reference_value": True}
        for name, value in gates.items() if not value
    ]
    return {
        "counts_before_gates": {
            "total": len(rows),
            "success": successes,
            "failure": failures,
            "policy_response": sum(
                bool(row["evidence"].policy_response) for row in rows
            ),
            "response_present_failure": sum(
                row["evidence"].policy_response and not row["completion"]
                for row in rows
            ),
        },
        "parity_mismatch_count": len(mismatch_rows),
        "parity_mismatch_rows": mismatch_rows,
        "failed_gate_rows": failed_gate_rows,
        "gates": gates,
        "passed": all(gates.values()),
    }


def parity_mismatch_rows(
    rows: Sequence[Mapping[str, Any]],
    reference_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    for index in range(max(len(rows), len(reference_rows))):
        real = rows[index] if index < len(rows) else None
        reference = reference_rows[index] if index < len(reference_rows) else None
        frame = real or reference or {}
        if real is None or reference is None:
            mismatches.append({
                "index": index,
                "fen": frame.get("fen"),
                "historical_pool_name": frame.get("historical_pool_name"),
                "field": "frame_presence",
                "real_value": real is not None,
                "reference_value": reference is not None,
            })
            continue
        for field in ACTUATION_FIELDS:
            real_value = real["actuation"][field]
            reference_value = reference["actuation"][field]
            if field == "activation":
                equal = _float_bits(real_value) == _float_bits(reference_value)
            else:
                equal = real_value == reference_value
            if not equal:
                row = {
                    "index": index,
                    "fen": real["fen"],
                    "historical_pool_name": real["historical_pool_name"],
                    "field": f"GraphActuation.{field}",
                    "real_value": real_value,
                    "reference_value": reference_value,
                }
                if field == "activation":
                    row.update({
                        "real_ieee754": _float_bits(real_value),
                        "reference_ieee754": _float_bits(reference_value),
                    })
                mismatches.append(row)
        real_signals = real["active_competence_signal_ids"]
        reference_signals = reference["active_competence_signal_ids"]
        if real_signals != reference_signals:
            mismatches.append({
                "index": index,
                "fen": real["fen"],
                "historical_pool_name": real["historical_pool_name"],
                "field": "active_competence_signal_ids",
                "real_value": real_signals,
                "reference_value": reference_signals,
            })
    return mismatches


def enumerate_bounded_pure_base_patterns(
    records: Sequence[CompetenceEvidenceRecord],
    connected: GraphNativeCompetenceEnvelope,
) -> dict[str, Any]:
    signal_masks: dict[str, int] = {}
    success_mask = 0
    full_mask = (1 << len(records)) - 1
    for index, record in enumerate(records):
        bit = 1 << index
        if record.observed_completion:
            success_mask |= bit
        for signal in record.active_signal_ids:
            signal_masks[signal] = signal_masks.get(signal, 0) | bit
    failure_mask = full_mask ^ success_mask
    eligible = tuple(sorted(
        signal for signal, mask in signal_masks.items()
        if mask.bit_count() >= 4
    ))
    proposals: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for proposal in connected.audit.proposal_rows:
        members = tuple(sorted(map(str, proposal.get("members", ()))))
        if members and not any(member.startswith("context:") for member in members):
            proposals[members].append(proposal)
    mature_specs = {
        tuple(sorted(cell.members))
        for cell in connected.cells.values()
        if cell.state == StemCellState.MATURE
        and not any(member.startswith("context:") for member in cell.members)
    }

    digest = hashlib.sha256()
    counts: dict[str, dict[str, int]] = {}
    histograms: dict[str, dict[str, dict[str, int]]] = {}
    examples: dict[str, list[dict[str, Any]]] = {}
    totals = Counter({
        "tested": 0,
        "support_qualified": 0,
        "pure": 0,
        "attempted": 0,
        "admitted": 0,
        "matured": 0,
    })
    rejection_reasons = Counter()
    for arity in (1, 2, 3):
        arity_key = str(arity)
        arity_counts = Counter({
            "tested": 0,
            "support_qualified": 0,
            "pure": 0,
        })
        support_hist = Counter()
        pure_support_hist = Counter()
        polarity_hist = Counter()
        mixture_hist = Counter()
        status_hist = Counter({
            "not_attempted": 0,
            "attempted_rejected": 0,
            "admitted_not_matured": 0,
            "matured": 0,
        })
        arity_examples: list[dict[str, Any]] = []
        for members in combinations(eligible, arity):
            arity_counts["tested"] += 1
            mask = full_mask
            for member in members:
                mask &= signal_masks[member]
            support = mask.bit_count()
            if support < 4:
                continue
            arity_counts["support_qualified"] += 1
            support_hist[str(support)] += 1
            successes = (mask & success_mask).bit_count()
            failures = (mask & failure_mask).bit_count()
            if successes and failures:
                continue
            arity_counts["pure"] += 1
            pure_support_hist[str(support)] += 1
            polarity = (
                AvailabilityState.AVAILABLE.value
                if successes else AvailabilityState.REFUTED.value
            )
            polarity_hist[polarity] += 1
            mixture_hist[f"{successes}:{failures}"] += 1
            proposal_rows = proposals.get(tuple(members), ())
            attempted = bool(proposal_rows)
            admitted = any(bool(row.get("admitted")) for row in proposal_rows)
            mature = tuple(members) in mature_specs
            if mature:
                status = "matured"
            elif admitted:
                status = "admitted_not_matured"
            elif attempted:
                status = "attempted_rejected"
            else:
                status = "not_attempted"
            status_hist[status] += 1
            reasons = sorted(
                str(row.get("reason") or "admitted")
                for row in proposal_rows
            )
            for reason in reasons:
                if reason != "admitted":
                    rejection_reasons[reason] += 1
            pattern = {
                "members": list(members),
                "arity": arity,
                "support": support,
                "successes": successes,
                "failures": failures,
                "polarity": polarity,
                "attempted": attempted,
                "admitted": admitted,
                "mature": mature,
                "proposal_reasons": reasons,
            }
            encoded = json.dumps(
                pattern, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)
            if len(arity_examples) < EXAMPLE_CAP_PER_ARITY:
                arity_examples.append(pattern)
        counts[arity_key] = dict(sorted(arity_counts.items()))
        histograms[arity_key] = {
            "support_qualified_support": dict(sorted(support_hist.items())),
            "pure_support": dict(sorted(pure_support_hist.items())),
            "pure_polarity": dict(sorted(polarity_hist.items())),
            "pure_mixture": dict(sorted(mixture_hist.items())),
            "pure_proposal_status": dict(sorted(status_hist.items())),
        }
        examples[arity_key] = arity_examples
        totals.update({
            "tested": arity_counts["tested"],
            "support_qualified": arity_counts["support_qualified"],
            "pure": arity_counts["pure"],
            "attempted": sum(
                count for status, count in status_hist.items()
                if status != "not_attempted"
            ),
            "admitted": (
                status_hist["admitted_not_matured"] + status_hist["matured"]
            ),
            "matured": status_hist["matured"],
        })
    verdict = _diagnostic_verdict(totals)
    return {
        "laboratory_only": True,
        "read_only_no_learning_feedback": True,
        "full_pattern_records_persisted": False,
        "example_cap_per_arity": EXAMPLE_CAP_PER_ARITY,
        "record_count": len(records),
        "signal_identity_count": len(signal_masks),
        "base_signals_with_support_at_least_4": len(eligible),
        "exact_counts_by_arity": counts,
        "exact_histograms_by_arity": histograms,
        "exact_total_counts": dict(sorted(totals.items())),
        "proposal_rejection_reason_histogram": dict(
            sorted(rejection_reasons.items())
        ),
        "pure_pattern_digest": {
            "algorithm": "sha256_length_prefixed_canonical_json",
            "value": digest.hexdigest(),
        },
        "bounded_examples_by_arity": examples,
        "verdict": verdict,
        "verdict_explanation": _verdict_explanation(verdict),
    }


def _diagnostic_verdict(totals: Mapping[str, int]) -> str:
    if int(totals.get("pure", 0)) == 0:
        return "current_representation_or_selectivity_insufficient"
    if int(totals.get("attempted", 0)) == 0:
        return "nomination_or_responsibility_failure"
    if int(totals.get("admitted", 0)) == 0:
        return "proposal_admission_or_capacity_failure"
    if int(totals.get("matured", 0)) == 0:
        return "lifecycle_or_evidence_accounting_defect"
    return "native_competence_learning_engaged_compare_outcome_shuffled"


def _verdict_explanation(verdict: str) -> str:
    return {
        "current_representation_or_selectivity_insufficient": (
            "No pure support-qualified singleton, pair, or triple exists."
        ),
        "nomination_or_responsibility_failure": (
            "Pure patterns exist, but the frozen genome attempted none."
        ),
        "proposal_admission_or_capacity_failure": (
            "Pure patterns were attempted, but none were admitted."
        ),
        "lifecycle_or_evidence_accounting_defect": (
            "A pure pattern was admitted, but no selective cell matured."
        ),
        "native_competence_learning_engaged_compare_outcome_shuffled": (
            "At least one pure selective cell matured; compare the frozen arms."
        ),
    }[verdict]


def _arm_comparison(
    records: Sequence[CompetenceEvidenceRecord],
    connected: GraphNativeCompetenceEnvelope,
    shuffled: GraphNativeCompetenceEnvelope,
    connected_report: Mapping[str, Any],
    shuffled_report: Mapping[str, Any],
) -> dict[str, Any]:
    def mature_count(envelope: GraphNativeCompetenceEnvelope) -> int:
        return sum(
            cell.state == StemCellState.MATURE
            for cell in envelope.cells.values()
        )

    def actual_pure_mature_count(envelope: GraphNativeCompetenceEnvelope) -> int:
        count = 0
        for cell in envelope.cells.values():
            if cell.state != StemCellState.MATURE:
                continue
            if any(member.startswith("context:") for member in cell.members):
                continue
            matched = [
                record for record in records
                if set(cell.members).issubset(record.active_signal_ids)
            ]
            successes = sum(record.observed_completion for record in matched)
            failures = len(matched) - successes
            count += int(len(matched) >= 4 and not (successes and failures))
        return count

    return {
        "descriptive_training_only": True,
        "connected_mature_cell_count": mature_count(connected),
        "outcome_shuffled_mature_cell_count": mature_count(shuffled),
        "connected_actual_outcome_pure_mature_count": (
            actual_pure_mature_count(connected)
        ),
        "outcome_shuffled_actual_outcome_pure_mature_count": (
            actual_pure_mature_count(shuffled)
        ),
        "connected_training_descriptive_metrics": (
            connected_report["training_descriptive_metrics"]
        ),
        "outcome_shuffled_on_actual_outcomes_descriptive_metrics": (
            shuffled_report["training_descriptive_metrics"]
        ),
    }


def _float_bits(value: float) -> str:
    return struct.pack("!d", float(value)).hex()


def _file_sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_result(path: str, result: Mapping[str, Any]) -> Mapping[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result
