"""Preregistered touched-data, training-only competence-envelope V2."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, replace
import hashlib
from itertools import combinations
import json
from pathlib import Path
import random
from time import perf_counter
from typing import Any, Mapping, Sequence

import chess

from recon_lite import ChildResponse
from recon_lite_hector.nodes import StemCellState

from .native_authority_handover import (
    ChildQuery,
    native_authority_tripwires,
)
from .native_authority_lab import NativeAuthorityLabConfig, load_retired_r0_build
from .native_child_availability import (
    observe_query_completion,
)
from .native_competence_envelope import (
    AvailabilityState,
    CompetenceContextGrowthGenome,
    CompetenceEvidenceRecord,
    GraphNativeCompetenceEnvelope,
    evidence_key,
    extract_active_competence_signals,
)
from .native_competence_envelope_experiment import (
    EXPECTED,
    _hash_json,
    _hash_list,
)


ADDENDUM_ARTIFACT = (
    "reports/autogrowth/native_authority/"
    "native_mature_envelope_authority_addendum.json"
)
ADDENDUM_SHA256 = (
    "4edca9472129a855fe7ec539f655da141b59e0b9d5136668ed5294095f4b3c46"
)
OUTPUT = (
    "reports/autogrowth/native_authority/"
    "touched_r0_competence_envelope_v2_training_only.json"
)
TAPE_SEED = 2026071601
OUTCOME_SHUFFLE_SEED = 2026071602
GLOBAL_EVIDENCE_RATE = 0.625


@dataclass(frozen=True)
class V2TrainingConfig:
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


def run_touched_competence_envelope_v2_training(
    config: V2TrainingConfig | None = None,
) -> Mapping[str, Any]:
    cfg = config or V2TrainingConfig()
    started = perf_counter()
    if _file_sha256(ADDENDUM_ARTIFACT) != ADDENDUM_SHA256:
        raise RuntimeError("mature-envelope authority addendum changed")

    addendum = json.loads(Path(ADDENDUM_ARTIFACT).read_text())
    if not addendum.get("passed"):
        raise RuntimeError("mature-envelope authority addendum did not pass")
    build = load_retired_r0_build(NativeAuthorityLabConfig(
        source_artifact=cfg.source_artifact,
        organism_path=cfg.source_organism,
        build_report_path=cfg.build_report,
    ))
    tape = [
        {"historical_pool_name": "r0_train", "fen": fen}
        for fen in build.pools.r0_train
    ] + [
        {"historical_pool_name": "train_decoy", "fen": fen}
        for fen in build.pools.gate_train_decoys
    ]
    random.Random(TAPE_SEED).shuffle(tape)
    legacy_tape = [
        {
            "class": (
                "positive"
                if row["historical_pool_name"] == "r0_train"
                else "failure"
            ),
            "fen": row["fen"],
        }
        for row in tape
    ]
    if _hash_json(legacy_tape) != EXPECTED["tape"]:
        raise RuntimeError("V2 touched tape changed")

    result: dict[str, Any] = {
        "schema_version": "touched_r0_competence_envelope_v2_training_only.v1",
        "preregistered_training_only": True,
        "source_addendum_commit": "84e423f",
        "source_addendum_artifact": {
            "path": ADDENDUM_ARTIFACT,
            "sha256": ADDENDUM_SHA256,
        },
        "historical_pool_names_are_provenance_only": True,
        "validation_touched": False,
        "regression_touched": False,
        "retired_successors_touched": False,
        "r1_touched": False,
        "fresh_data_touched": False,
        "global_evidence_rate": GLOBAL_EVIDENCE_RATE,
        "stage": "admission",
    }
    r0_before = build.organism.persistent_state_audit()
    with native_authority_tripwires() as tripwires:
        observations = [
            _observe(
                build.organism,
                row["fen"],
                row["historical_pool_name"],
                index,
            )
            for index, row in enumerate(tape)
        ]
        r0_after_admission = build.organism.persistent_state_audit()
        admission = _admission(
            observations,
            addendum["full_frame_input_parity"]["rows"],
            r0_before == r0_after_admission,
        )
        result["admission"] = admission
        result["authority_tripwires"] = dict(tripwires)
        if not admission["passed"]:
            result.update({
                "stage": "closed_before_learning",
                "binding_boundary": "evidence_admission",
                "passed": False,
                "duration_seconds": perf_counter() - started,
                "next_action": "preserve_admission_failure",
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
            raise RuntimeError("V2 outcome permutation changed")
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
        r0_final = build.organism.persistent_state_audit()
        diagnostic = enumerate_pure_base_patterns(records)
        interpretation = _interpret_diagnostic(diagnostic, connected)
        result.update({
            "stage": "closed_after_lifecycle",
            "binding_boundary": interpretation,
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
                "connected": _arm_report(connected, records),
                "outcome_shuffled": _arm_report(shuffled, records),
            },
            "global_evidence_control": _global_evidence_control(records),
            "post_run_laboratory_diagnostic": diagnostic,
            "diagnostic_interpretation": interpretation,
            "r0_persistent_state": {
                "before": r0_before,
                "after_admission": r0_after_admission,
                "final": r0_final,
            },
            "authority_tripwires": dict(tripwires),
        })

    integrity = {
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
        "diagnostic_read_only": True,
        "no_downstream_data": True,
    }
    result.update({
        "integrity": integrity,
        "passed": all(integrity.values()),
        "duration_seconds": perf_counter() - started,
        "next_action": "stop_for_external_review",
    })
    return _write_result(cfg.output, result)


def _observe(
    organism: Any,
    fen: str,
    historical_pool_name: str,
    index: int,
) -> dict[str, Any]:
    board = chess.Board(fen)
    actuation = organism.emit_action(board)
    if actuation is None:
        raise RuntimeError("purity-corrected R0 emitted no policy response")
    signals = extract_active_competence_signals(
        organism, board, actuation
    )
    raw = ChildQuery(
        response=ChildResponse(
            child_id=organism.provenance.child_id,
            confirmed=False,
            expected_value=0.0,
            uncertainty=organism.provenance.uncertainty,
            grounded=organism.provenance.grounded,
            grounding_source=organism.provenance.grounding_source,
            policy_response=True,
            available=False,
        ),
        actuation=actuation,
        frame_id=f"v2-training:{index}",
        persistent_mutation_count=0,
        effect_attempts=(),
        active_competence_signal_ids=signals,
    )
    observed = observe_query_completion(
        organism, board.copy(stack=False), raw
    )
    record = CompetenceEvidenceRecord(
        evidence_key=evidence_key(
            board,
            actuation,
            organism.provenance.completion_terminal_kind,
        ),
        active_signal_ids=signals,
        policy_response=True,
        observed_completion=observed.completion_confirmed,
        actuator_identity=actuation.actuator_identity,
        completion_terminal_identity=(
            organism.provenance.completion_terminal_kind
        ),
    )
    return {
        "index": index,
        "historical_pool_name": historical_pool_name,
        "fen": fen,
        "actuation": asdict(actuation),
        "active_competence_signal_ids": list(signals),
        "completion": observed.completion_confirmed,
        "observed_terminal": observed.observed_terminal,
        "local_competence_failure": observed.local_competence_failure,
        "fabricated_reward": observed.fabricated_terminal_reward,
        "evidence": record,
    }


def _admission(
    rows: Sequence[Mapping[str, Any]],
    addendum_rows: Sequence[Mapping[str, Any]],
    persistent_identity: bool,
) -> dict[str, Any]:
    successes = sum(bool(row["completion"]) for row in rows)
    failures = len(rows) - successes
    parity = all(
        row["actuation"] == addendum_rows[index]["actuation"]
        and row["active_competence_signal_ids"]
        == addendum_rows[index]["active_competence_signal_ids"]
        for index, row in enumerate(rows)
    )
    gates = {
        "count_64": len(rows) == 64,
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
        "exact_persistent_identity": persistent_identity,
        "purity_corrected_path_parity": parity,
    }
    return {
        "counts_before_gates": {
            "total": len(rows),
            "success": successes,
            "failure": failures,
            "policy_response": sum(
                bool(row["evidence"].policy_response) for row in rows
            ),
            "response_present_failure": sum(
                row["evidence"].policy_response
                and not row["completion"]
                for row in rows
            ),
        },
        "gates": gates,
        "passed": all(gates.values()),
    }


def _arm_report(
    envelope: GraphNativeCompetenceEnvelope,
    evaluation_records: Sequence[CompetenceEvidenceRecord],
) -> dict[str, Any]:
    return {
        "manifest": envelope.to_manifest(),
        "round_histograms": round_histograms(envelope),
        "final_state_histogram": dict(sorted(Counter(
            cell.state.name for cell in envelope.cells.values()
        ).items())),
        "final_polarity_histogram": dict(sorted(Counter(
            "none" if cell.polarity is None else cell.polarity.value
            for cell in envelope.cells.values()
        ).items())),
        "training_descriptive_metrics": _classification_metrics(
            envelope, evaluation_records
        ),
    }


def round_histograms(
    envelope: GraphNativeCompetenceEnvelope,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    proposals_by_round: dict[int, list[Mapping[str, Any]]] = {
        index: [] for index in range(envelope.config.structural_rounds)
    }
    for proposal in envelope.audit.proposal_rows:
        proposals_by_round[int(proposal["round_index"])].append(proposal)
    for round_index, review in enumerate(envelope.audit.lifecycle_reviews):
        proposals = proposals_by_round[round_index]
        cells = list(review["cells"])
        purity = Counter()
        mixture = Counter()
        for cell in cells:
            successes = int(cell["successes"])
            failures = int(cell["failures"])
            support = int(cell["support"])
            if support == 0:
                purity["no_support"] += 1
            elif successes and failures:
                purity["impure"] += 1
            else:
                purity["pure"] += 1
            mixture[f"{successes}:{failures}"] += 1
        rows.append({
            "round_index": round_index,
            "review_index": review["review_index"],
            "final_review": review["final"],
            "proposal_histogram": {
                "recorded": len(proposals),
                "admitted": sum(
                    bool(proposal["admitted"]) for proposal in proposals
                ),
                "rejected": sum(
                    not bool(proposal["admitted"]) for proposal in proposals
                ),
                "reason": dict(sorted(Counter(
                    proposal["reason"] or "admitted"
                    for proposal in proposals
                ).items())),
            },
            "duplication_histogram": {
                "duplicate": sum(
                    proposal["reason"] == "duplicate"
                    for proposal in proposals
                ),
                "non_duplicate": sum(
                    proposal["reason"] != "duplicate"
                    for proposal in proposals
                ),
            },
            "support_histogram": dict(sorted(Counter(
                str(cell["support"]) for cell in cells
            ).items())),
            "purity_histogram": dict(sorted(purity.items())),
            "mixture_histogram": dict(sorted(mixture.items())),
            "arity_histogram": dict(sorted(Counter(
                str(len(proposal["members"])) for proposal in proposals
            ).items())),
            "prune_histogram": dict(sorted(Counter(
                cell["prune_reason"] or "not_pruned" for cell in cells
            ).items())),
            "positive_mature": review["positive_mature"],
            "refuted_mature": review["refuted_mature"],
        })
    return rows


def enumerate_pure_base_patterns(
    records: Sequence[CompetenceEvidenceRecord],
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
        signal
        for signal, mask in signal_masks.items()
        if mask.bit_count() >= 4
    ))
    patterns: list[dict[str, Any]] = []
    tested: dict[str, int] = {}
    support_eligible: dict[str, int] = {}
    pure_counts: dict[str, int] = {}
    for arity in (1, 2, 3):
        tested_count = 0
        support_count = 0
        pure_count = 0
        for members in combinations(eligible, arity):
            tested_count += 1
            mask = full_mask
            for member in members:
                mask &= signal_masks[member]
            support = mask.bit_count()
            if support < 4:
                continue
            support_count += 1
            successes = (mask & success_mask).bit_count()
            failures = (mask & failure_mask).bit_count()
            if successes and failures:
                continue
            pure_count += 1
            patterns.append({
                "members": list(members),
                "arity": arity,
                "support": support,
                "successes": successes,
                "failures": failures,
                "polarity": (
                    AvailabilityState.AVAILABLE.value
                    if successes
                    else AvailabilityState.REFUTED.value
                ),
            })
        tested[str(arity)] = tested_count
        support_eligible[str(arity)] = support_count
        pure_counts[str(arity)] = pure_count
    return {
        "laboratory_only": True,
        "read_only_no_learning_feedback": True,
        "record_count": len(records),
        "signal_identity_count": len(signal_masks),
        "base_signals_with_support_at_least_4": len(eligible),
        "tested_combination_count_by_arity": tested,
        "support_eligible_count_by_arity": support_eligible,
        "pure_pattern_count_by_arity": pure_counts,
        "pure_pattern_count": len(patterns),
        "patterns": patterns,
    }


def _interpret_diagnostic(
    diagnostic: Mapping[str, Any],
    connected: GraphNativeCompetenceEnvelope,
) -> str:
    pure_specs = {
        tuple(sorted(pattern["members"]))
        for pattern in diagnostic["patterns"]
    }
    proposed_specs = {
        tuple(sorted(proposal["members"]))
        for proposal in connected.audit.proposal_rows
        if proposal["members"]
        and not any(
            str(member).startswith("context:")
            for member in proposal["members"]
        )
    }
    mature_specs = {
        tuple(sorted(cell.members))
        for cell in connected.cells.values()
        if cell.state == StemCellState.MATURE
        and not any(member.startswith("context:") for member in cell.members)
    }
    proposed_pure = pure_specs & proposed_specs
    matured_pure = pure_specs & mature_specs
    diagnostic["proposed_pure_pattern_count"] = len(proposed_pure)
    diagnostic["matured_pure_pattern_count"] = len(matured_pure)
    diagnostic["proposed_pure_patterns"] = [
        list(members) for members in sorted(proposed_pure)
    ]
    diagnostic["matured_pure_patterns"] = [
        list(members) for members in sorted(matured_pure)
    ]
    if not pure_specs:
        return "current_internal_representation_insufficient"
    if not proposed_pure:
        return "nomination_or_responsibility_failure"
    if not matured_pure:
        return "lifecycle_defect"
    return "pure_pattern_maturation_observed"


def _classification_metrics(
    envelope: GraphNativeCompetenceEnvelope,
    records: Sequence[CompetenceEvidenceRecord],
) -> dict[str, Any]:
    rows = []
    for record in records:
        classification = envelope.classify(
            record.active_signal_ids,
            policy_response=record.policy_response,
        )
        rows.append({
            "evidence_key": record.evidence_key,
            "observed_completion": record.observed_completion,
            "classification": classification.to_manifest(),
        })
    available = [
        row["classification"]["state"] == AvailabilityState.AVAILABLE.value
        for row in rows
    ]
    true = [bool(row["observed_completion"]) for row in rows]
    return {
        "descriptive_only_no_handover_gate": True,
        "available_count": sum(available),
        "true_positive": sum(a and y for a, y in zip(available, true, strict=True)),
        "false_positive": sum(a and not y for a, y in zip(available, true, strict=True)),
        "true_negative": sum(not a and not y for a, y in zip(available, true, strict=True)),
        "false_negative": sum(not a and y for a, y in zip(available, true, strict=True)),
        "rows": rows,
    }


def _global_evidence_control(
    records: Sequence[CompetenceEvidenceRecord],
) -> dict[str, Any]:
    labels = [float(record.observed_completion) for record in records]
    positive = [label for label in labels if label == 1.0]
    negative = [label for label in labels if label == 0.0]
    squared = [
        (GLOBAL_EVIDENCE_RATE - label) ** 2 for label in labels
    ]
    return {
        "constant_probability": GLOBAL_EVIDENCE_RATE,
        "source": "actual_training_prevalence_40_of_64",
        "overall_brier": sum(squared) / len(squared),
        "positive_brier": sum(
            (GLOBAL_EVIDENCE_RATE - label) ** 2 for label in positive
        ) / len(positive),
        "negative_brier": sum(
            (GLOBAL_EVIDENCE_RATE - label) ** 2 for label in negative
        ) / len(negative),
        "handover_mask_used": False,
    }


def _artifact_observation(row: Mapping[str, Any]) -> dict[str, Any]:
    record = row["evidence"]
    return {
        key: value for key, value in row.items() if key != "evidence"
    } | {
        "evidence_key": record.evidence_key,
        "policy_response": record.policy_response,
    }


def _write_result(path: str, result: Mapping[str, Any]) -> Mapping[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def _file_sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
