"""Preregistered content-blind genome-seed robustness adjudication for V3."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
import gzip
import hashlib
import json
from pathlib import Path
import pickle
from typing import Any, Iterable, Mapping, Sequence

from recon_lite_hector.nodes import StemCellState

from .native_competence_envelope import (
    AvailabilityState,
    CompetenceContextGrowthGenome,
    CompetenceEnvelopeConfig,
    CompetenceEvidenceRecord,
    GraphNativeCompetenceEnvelope,
)
from .native_competence_envelope_experiment import _hash_json, _hash_list
from .native_competence_envelope_v2_training import round_histograms


SOURCE_V3_ARTIFACT = (
    "reports/autogrowth/native_authority/"
    "touched_r0_competence_envelope_v3_training_only.json"
)
SOURCE_V3_SHA256 = "91b3ae80773f2c2dd20cd00b82f5a1fde8190deef670623ea9ba39db9d514d94"
SOURCE_ROWS_SHA256 = "f70b28153ba01ab7d6549de36b670fd5f356906f7514fbbbfcef2b3457ced34d"
LEARNER_MODULE = "src/recon_lite_chess/autogrowth/native_competence_envelope.py"
LEARNER_SHA256 = "65dda4f09bc1181a6fe3780c27b56da4fc888a377ae3cfffe3c728e9d11d2a7b"
SHUFFLE_SHA256 = "501f16f2cce5cfff487152ed5a444ecadb7ebc76e29fdc032c9b6f016df90d0e"
PREREGISTRATION_DOCUMENT = (
    "docs/autogrowth/"
    "NATIVE_R0_COMPETENCE_ENVELOPE_V3B_SEED_ROBUSTNESS_PREREGISTRATION.md"
)
RUNNER_MODULE = (
    "src/recon_lite_chess/autogrowth/"
    "native_competence_envelope_v3b_seed_robustness.py"
)
SEED_MANIFEST = (
    "reports/autogrowth/native_authority/"
    "native_competence_envelope_v3b_seed_manifest.json"
)
OUTPUT = (
    "reports/autogrowth/native_authority/"
    "native_competence_envelope_v3b_seed_robustness.json"
)
ORGANISM_DIRECTORY = (
    "reports/autogrowth/native_authority/"
    "native_competence_envelope_v3b_organisms"
)
SEED_COUNT = 32
EXCLUDED_SEED_MAX = 1000
DERIVATION_DOMAIN = "hector-recon-v3b-content-blind-genome-seed-v1"


@dataclass(frozen=True)
class V3BConfig:
    source_v3_artifact: str = SOURCE_V3_ARTIFACT
    seed_manifest: str = SEED_MANIFEST
    output: str = OUTPUT
    organism_directory: str = ORGANISM_DIRECTORY


def derive_seed(
    preregistration_commit: str,
    ordinal: int,
    *,
    used: Iterable[int] = (),
) -> dict[str, Any]:
    if len(preregistration_commit) != 40:
        raise ValueError("preregistration commit must be a 40-character SHA-1")
    bytes.fromhex(preregistration_commit)
    used_set = set(map(int, used))
    counter = 0
    while True:
        payload = (
            f"{DERIVATION_DOMAIN}|{preregistration_commit}|"
            f"{int(ordinal)}|{counter}"
        ).encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        seed = int.from_bytes(bytes.fromhex(digest)[:8], "big") & ((1 << 63) - 1)
        if seed > EXCLUDED_SEED_MAX and seed not in used_set:
            return {
                "ordinal": int(ordinal),
                "counter": counter,
                "sha256": digest,
                "seed": seed,
            }
        counter += 1


def generate_seed_manifest(
    preregistration_commit: str,
    *,
    output: str = SEED_MANIFEST,
) -> Mapping[str, Any]:
    target = Path(output)
    if target.exists():
        raise FileExistsError("V3B seed manifest already exists")
    seeds: list[dict[str, Any]] = []
    used: set[int] = set()
    for ordinal in range(SEED_COUNT):
        row = derive_seed(preregistration_commit, ordinal, used=used)
        seeds.append(row)
        used.add(int(row["seed"]))
    runner_path = Path(RUNNER_MODULE)
    manifest = {
        "schema_version": "native_competence_envelope_v3b_seed_manifest.v1",
        "generated_before_any_arm": True,
        "preregistration_commit": preregistration_commit,
        "derivation": {
            "algorithm": "sha256",
            "domain": DERIVATION_DOMAIN,
            "input": "domain|preregistration_commit|ordinal|counter",
            "integer_mapping": "first_64_bits_unsigned_masked_to_63_bits",
            "excluded_seed_range_inclusive": [1, EXCLUDED_SEED_MAX],
            "collision_policy": "increment_counter_and_rederive",
        },
        "runner": {
            "path": str(runner_path),
            "sha256": _file_sha256(runner_path),
        },
        "preregistration": {
            "path": PREREGISTRATION_DOCUMENT,
            "sha256": _file_sha256(PREREGISTRATION_DOCUMENT),
        },
        "seed_count": len(seeds),
        "seeds": seeds,
        "seed_list_sha256": _hash_json([row["seed"] for row in seeds]),
    }
    _write_json(target, manifest)
    return manifest


def validate_seed_manifest(
    manifest: Mapping[str, Any],
    *,
    verify_files: bool = True,
) -> None:
    if manifest.get("schema_version") != (
        "native_competence_envelope_v3b_seed_manifest.v1"
    ):
        raise RuntimeError("V3B seed-manifest schema changed")
    if manifest.get("generated_before_any_arm") is not True:
        raise RuntimeError("V3B manifest does not attest pre-arm generation")
    if manifest.get("seed_count") != SEED_COUNT:
        raise RuntimeError("V3B seed count changed")
    commit = str(manifest.get("preregistration_commit", ""))
    rows = list(manifest.get("seeds", ()))
    if len(rows) != SEED_COUNT:
        raise RuntimeError("V3B seed rows changed")
    used: set[int] = set()
    for ordinal, row in enumerate(rows):
        expected = derive_seed(commit, ordinal, used=used)
        if dict(row) != expected:
            raise RuntimeError(f"V3B seed derivation mismatch at ordinal {ordinal}")
        seed = int(row["seed"])
        if seed <= EXCLUDED_SEED_MAX or seed in used:
            raise RuntimeError("V3B seed exclusion or uniqueness failure")
        used.add(seed)
    if manifest.get("seed_list_sha256") != _hash_json(
        [row["seed"] for row in rows]
    ):
        raise RuntimeError("V3B seed-list digest mismatch")
    if verify_files:
        runner = manifest["runner"]
        prereg = manifest["preregistration"]
        if _file_sha256(runner["path"]) != runner["sha256"]:
            raise RuntimeError("V3B runner changed after seed freeze")
        if _file_sha256(prereg["path"]) != prereg["sha256"]:
            raise RuntimeError("V3B preregistration changed after seed freeze")


def run_v3b_seed_robustness(
    config: V3BConfig | None = None,
) -> Mapping[str, Any]:
    cfg = config or V3BConfig()
    if _file_sha256(cfg.source_v3_artifact) != SOURCE_V3_SHA256:
        raise RuntimeError("canonical V3 artifact changed")
    if _file_sha256(LEARNER_MODULE) != LEARNER_SHA256:
        raise RuntimeError("frozen competence learner changed")
    source = _load_json(cfg.source_v3_artifact)
    if _hash_json(source["training_rows"]) != SOURCE_ROWS_SHA256:
        raise RuntimeError("canonical V3 signal rows changed")
    permutation = tuple(map(int, source["outcome_shuffle"]["permutation"]))
    if _hash_list(permutation) != SHUFFLE_SHA256:
        raise RuntimeError("canonical V3 outcome shuffle changed")
    manifest = _load_json(cfg.seed_manifest)
    validate_seed_manifest(manifest)
    manifest_sha256 = _file_sha256(cfg.seed_manifest)

    records = _records_from_v3(source["training_rows"])
    outcomes = tuple(record.observed_completion for record in records)
    shuffled_records = tuple(
        replace(record, observed_completion=outcomes[permutation[index]])
        for index, record in enumerate(records)
    )
    base_config = CompetenceEnvelopeConfig(**source["frozen_config"])
    result = _load_or_initialize_result(
        cfg, manifest, manifest_sha256, records, permutation
    )
    completed = list(result["seed_results"])
    _validate_contiguous_prefix(completed, manifest["seeds"])
    _validate_persisted_prefix(completed)
    for seed_row in manifest["seeds"][len(completed):]:
        ordinal = int(seed_row["ordinal"])
        seed = int(seed_row["seed"])
        connected = _run_arm(
            records, seed, "connected", base_config, cfg, ordinal
        )
        shuffled = _run_arm(
            shuffled_records, seed, "outcome_shuffled", base_config, cfg, ordinal
        )
        connected_engaged = bool(connected["engaged"])
        shuffled_engaged = bool(shuffled["engaged"])
        if connected_engaged and not shuffled_engaged:
            paired = "connected_only"
        elif shuffled_engaged and not connected_engaged:
            paired = "shuffled_only"
        elif connected_engaged:
            paired = "both"
        else:
            paired = "neither"
        completed.append({
            "ordinal": ordinal,
            "seed": seed,
            "connected": connected,
            "outcome_shuffled": shuffled,
            "paired_outcome": paired,
        })
        result["seed_results"] = completed
        result["stage"] = "running"
        result["completed_seed_count"] = len(completed)
        result["running_summary"] = _cohort_counts(completed)
        _write_json(cfg.output, result)

    adjudication = adjudicate_cohort(completed)
    state_identity = all(
        arm["diagnostic_state_digests"]["identical"]
        for row in completed
        for arm in (row["connected"], row["outcome_shuffled"])
    )
    result.update({
        "stage": "closed_after_adjudication",
        "completed_seed_count": len(completed),
        "cohort_counts": _cohort_counts(completed),
        "adjudication": adjudication,
        "integrity": {
            "all_32_seeds_present": len(completed) == SEED_COUNT,
            "all_64_organisms_persisted": all(
                arm["organism_artifact"]["persisted"]
                for row in completed
                for arm in (row["connected"], row["outcome_shuffled"])
            ),
            "all_64_organisms_restore_exactly": all(
                arm["organism_artifact"]["restore_parity"]
                for row in completed
                for arm in (row["connected"], row["outcome_shuffled"])
            ),
            "actual_diagnostic_state_identity_all_arms": state_identity,
            "all_arm_frozen_factor_checks": all(
                arm["frozen_factor_check"][
                    "selection_seed_equals_manifest_seed"
                ]
                and arm["frozen_factor_check"][
                    "all_other_config_fields_equal_v3"
                ]
                and arm["frozen_factor_check"]["request_order"]
                == "canonical_v3_order"
                and arm["frozen_factor_check"]["structural_round_count"] == 3
                for row in completed
                for arm in (row["connected"], row["outcome_shuffled"])
            ),
            "frozen_v3_artifact": _file_sha256(cfg.source_v3_artifact)
            == SOURCE_V3_SHA256,
            "frozen_learner": _file_sha256(LEARNER_MODULE) == LEARNER_SHA256,
            "fixed_signal_rows": _hash_json(source["training_rows"])
            == SOURCE_ROWS_SHA256,
            "fixed_outcome_shuffle": _hash_list(permutation) == SHUFFLE_SHA256,
            "no_seed_selection": [row["ordinal"] for row in completed]
            == list(range(SEED_COUNT)),
            "order_sensitive_deduplication_unchanged": True,
            "no_downstream_data": True,
        },
        "validation_touched": False,
        "regression_touched": False,
        "retired_successors_touched": False,
        "r1_touched": False,
        "fresh_data_touched": False,
        "next_action": "stop_after_v3b_adjudication",
    })
    result["passed_integrity"] = all(result["integrity"].values())
    _write_json(cfg.output, result)
    return result


def _records_from_v3(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[CompetenceEvidenceRecord, ...]:
    return tuple(CompetenceEvidenceRecord(
        evidence_key=str(row["evidence_key"]),
        active_signal_ids=tuple(map(str, row["active_competence_signal_ids"])),
        policy_response=bool(row["policy_response"]),
        observed_completion=bool(row["completion"]),
        actuator_identity=str(row["actuation"]["actuator_identity"]),
        completion_terminal_identity="mate",
    ) for row in rows)


def _run_arm(
    records: Sequence[CompetenceEvidenceRecord],
    seed: int,
    arm_name: str,
    base_config: CompetenceEnvelopeConfig,
    cfg: V3BConfig,
    ordinal: int,
) -> dict[str, Any]:
    arm_config = replace(base_config, selection_seed=int(seed))
    envelope = GraphNativeCompetenceEnvelope(config=arm_config)
    envelope.grow(
        records,
        genome=CompetenceContextGrowthGenome(int(seed)),
    )
    before = _state_digests(envelope)
    audit = audit_envelope(envelope, records)
    after = _state_digests(envelope)
    organism_artifact = _persist_organism(
        envelope, cfg.organism_directory, ordinal, seed, arm_name
    )
    mature_cells = [
        cell for cell in envelope.cells.values()
        if cell.state == StemCellState.MATURE
    ]
    first_maturity = min(
        (cell.maturity_review for cell in mature_cells
         if cell.maturity_review is not None),
        default=None,
    )
    return {
        "arm": arm_name,
        "genome_seed": int(seed),
        "engaged": bool(mature_cells),
        "first_maturity_round": first_maturity,
        "mature_cell_count": len(mature_cells),
        "mature_cells": [{
            "cell_id": cell.cell_id,
            "raw_members": list(cell.members),
            "canonical_members": sorted(cell.members),
            "polarity": (
                None if cell.polarity is None else cell.polarity.value
            ),
            "support": cell.support,
            "failures": cell.failures,
            "successes": cell.successes,
            "maturity_round": cell.maturity_review,
        } for cell in sorted(mature_cells, key=lambda item: item.cell_id)],
        "nomination_counts": audit["nomination_counts"],
        "training_coverage": audit["training_coverage"],
        "patterns_and_activation_masks": audit[
            "patterns_and_activation_masks"
        ],
        "unique_activation_masks": audit["unique_activation_masks"],
        "composition_minimality": audit["composition_minimality"],
        "duplicate_audit": audit["duplicate_audit"],
        "round_histograms": round_histograms(envelope),
        "diagnostic_state_digests": {
            "before": before,
            "after": after,
            "identical": before == after,
        },
        "organism_artifact": organism_artifact,
        "frozen_factor_check": {
            "selection_seed_equals_manifest_seed": (
                envelope.config.selection_seed == int(seed)
            ),
            "all_other_config_fields_equal_v3": all(
                getattr(envelope.config, field_name)
                == getattr(base_config, field_name)
                for field_name in base_config.__dataclass_fields__
                if field_name != "selection_seed"
            ),
            "request_order": "canonical_v3_order",
            "structural_round_count": len(envelope.audit.lifecycle_reviews),
        },
    }


def audit_envelope(
    envelope: GraphNativeCompetenceEnvelope,
    records: Sequence[CompetenceEvidenceRecord],
) -> dict[str, Any]:
    patterns = _pattern_rows(envelope, records)
    mask_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in patterns:
        mask_groups[row["activation_mask_hex"]].append({
            "cell_id": row["cell_id"],
            "raw_members": row["raw_members"],
            "canonical_members": row["canonical_members"],
        })
    unique_masks = [{
        "activation_mask_hex": mask,
        "support": int(mask, 16).bit_count(),
        "patterns": sorted(items, key=lambda item: item["cell_id"]),
    } for mask, items in sorted(mask_groups.items())]
    proposals = list(envelope.audit.proposal_rows)
    nomination_counts = {
        "recorded": len(proposals),
        "raw_arity": dict(sorted(Counter(
            str(len(row.get("members", ()))) for row in proposals
        ).items())),
        "admitted_raw_arity": dict(sorted(Counter(
            str(len(row.get("members", ())))
            for row in proposals if row.get("admitted")
        ).items())),
        "pair_nominations": sum(len(row.get("members", ())) == 2 for row in proposals),
        "triple_nominations": sum(len(row.get("members", ())) == 3 for row in proposals),
        "contextual_nominations": sum(
            any(str(member).startswith("context:")
                for member in row.get("members", ()))
            for row in proposals
        ),
    }
    coverage = _training_coverage(envelope, records)
    duplicate_audit = _duplicate_audit(proposals, envelope)
    minimality = _composition_minimality(patterns)
    return {
        "nomination_counts": nomination_counts,
        "training_coverage": coverage,
        "patterns_and_activation_masks": patterns,
        "unique_activation_masks": {
            "count": len(unique_masks),
            "groups": unique_masks,
            "digest": _hash_json(unique_masks),
        },
        "composition_minimality": minimality,
        "duplicate_audit": duplicate_audit,
    }


def _pattern_rows(
    envelope: GraphNativeCompetenceEnvelope,
    records: Sequence[CompetenceEvidenceRecord],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cell in sorted(envelope.cells.values(), key=lambda item: item.cell_id):
        mask = 0
        for index, record in enumerate(records):
            if envelope._cell_matches(cell, record, set()):
                mask |= 1 << index
        rows.append({
            "cell_id": cell.cell_id,
            "raw_members": list(cell.members),
            "canonical_members": sorted(cell.members),
            "raw_arity": len(cell.members),
            "context_member_count": sum(
                member.startswith("context:") for member in cell.members
            ),
            "activation_mask_hex": f"{mask:016x}",
            "activation_support": mask.bit_count(),
            "state": cell.state.name,
            "polarity": None if cell.polarity is None else cell.polarity.value,
            "support": cell.support,
            "successes": cell.successes,
            "failures": cell.failures,
        })
    return rows


def _composition_minimality(
    patterns: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    compositions = [row for row in patterns if int(row["raw_arity"]) > 1]
    classified: list[dict[str, Any]] = []
    for row in compositions:
        members = set(map(str, row["canonical_members"]))
        mask = row["activation_mask_hex"]
        strict_subset_ids = sorted(
            str(other["cell_id"])
            for other in patterns
            if other["activation_mask_hex"] == mask
            and set(map(str, other["canonical_members"])) < members
        )
        same_mask_peers = sorted(
            str(other["cell_id"])
            for other in patterns
            if other["activation_mask_hex"] == mask
            and other["cell_id"] != row["cell_id"]
        )
        classified.append({
            "cell_id": row["cell_id"],
            "classification": (
                "redundant_strict_superset" if strict_subset_ids else "minimal"
            ),
            "strict_subset_same_mask_cell_ids": strict_subset_ids,
            "same_mask_peer_cell_ids": same_mask_peers,
        })
    histogram = Counter(row["classification"] for row in classified)
    return {
        "definition": (
            "redundant iff a strict canonical-member subset has the same "
            "64-event activation mask"
        ),
        "histogram": dict(sorted(histogram.items())),
        "rows": classified,
    }


def _duplicate_audit(
    proposals: Sequence[Mapping[str, Any]],
    envelope: GraphNativeCompetenceEnvelope,
) -> dict[str, Any]:
    groups: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in proposals:
        groups[tuple(sorted(map(str, row.get("members", ()))))].append(row)
    canonical_duplicate_groups = []
    missed = 0
    for canonical, rows in sorted(groups.items()):
        if len(rows) < 2:
            continue
        raw_orders = sorted({tuple(map(str, row.get("members", ()))) for row in rows})
        admitted = [row for row in rows if row.get("admitted")]
        missed_here = max(0, len(admitted) - 1) if len(raw_orders) > 1 else 0
        missed += missed_here
        canonical_duplicate_groups.append({
            "canonical_members": list(canonical),
            "proposal_count": len(rows),
            "raw_orders": [list(item) for item in raw_orders],
            "admitted_count": len(admitted),
            "learner_duplicate_rejection_count": sum(
                row.get("reason") == "duplicate" for row in rows
            ),
            "order_sensitive_missed_duplicate_admissions": missed_here,
        })
    return {
        "learner_unchanged": True,
        "canonical_v3_unaffected": True,
        "raw_learner_duplicate_rejections": envelope.audit.duplicate_rejections,
        "member_order_canonical_duplicate_group_count": len(
            canonical_duplicate_groups
        ),
        "member_order_canonical_duplicate_occurrence_count": sum(
            row["proposal_count"] - 1 for row in canonical_duplicate_groups
        ),
        "order_variant_group_count": sum(
            len(row["raw_orders"]) > 1 for row in canonical_duplicate_groups
        ),
        "order_sensitive_missed_duplicate_admissions": missed,
        "groups": canonical_duplicate_groups,
    }


def _training_coverage(
    envelope: GraphNativeCompetenceEnvelope,
    records: Sequence[CompetenceEvidenceRecord],
) -> dict[str, Any]:
    states = []
    for record in records:
        state = envelope.classify(
            record.active_signal_ids,
            policy_response=record.policy_response,
        ).state
        states.append(state)
    available = [state == AvailabilityState.AVAILABLE for state in states]
    refuted = [state == AvailabilityState.REFUTED for state in states]
    true = [record.observed_completion for record in records]
    covered = [a or r for a, r in zip(available, refuted, strict=True)]
    return {
        "total": len(records),
        "available": sum(available),
        "refuted": sum(refuted),
        "unknown": len(records) - sum(covered),
        "covered": sum(covered),
        "coverage_fraction": sum(covered) / len(records),
        "available_true_positive": sum(
            a and y for a, y in zip(available, true, strict=True)
        ),
        "available_false_positive": sum(
            a and not y for a, y in zip(available, true, strict=True)
        ),
        "refuted_true_negative": sum(
            r and not y for r, y in zip(refuted, true, strict=True)
        ),
        "refuted_false_negative": sum(
            r and y for r, y in zip(refuted, true, strict=True)
        ),
    }


def _persist_organism(
    envelope: GraphNativeCompetenceEnvelope,
    directory: str,
    ordinal: int,
    seed: int,
    arm_name: str,
) -> dict[str, Any]:
    raw = pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL)
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    path = Path(directory) / f"{ordinal:02d}_{seed}_{arm_name}.pkl.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(compressed)
    restored = pickle.loads(gzip.decompress(path.read_bytes()))
    if not isinstance(restored, GraphNativeCompetenceEnvelope):
        raise RuntimeError("persisted V3B organism restored with wrong type")
    if restored.to_manifest() != envelope.to_manifest():
        raise RuntimeError("persisted V3B organism failed manifest parity")
    return {
        "persisted": True,
        "format": "gzip_pickle_graph_native_competence_envelope",
        "path": str(path),
        "empty_envelope": len(envelope.cells) == 0,
        "cell_count": len(envelope.cells),
        "uncompressed_bytes": len(raw),
        "compressed_bytes": len(compressed),
        "uncompressed_sha256": hashlib.sha256(raw).hexdigest(),
        "compressed_sha256": hashlib.sha256(compressed).hexdigest(),
        "restored_manifest_sha256": _hash_json(restored.to_manifest()),
        "source_manifest_sha256": _hash_json(envelope.to_manifest()),
        "restore_parity": True,
    }


def _state_digests(envelope: GraphNativeCompetenceEnvelope) -> dict[str, str]:
    exact = pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL)
    manifest = json.dumps(
        envelope.to_manifest(), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {
        "pickle_sha256": hashlib.sha256(exact).hexdigest(),
        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
    }


def adjudicate_cohort(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = _cohort_counts(rows)
    discrimination_gates = {
        "connected_engagement_at_least_24_of_32": counts[
            "connected_engaged"
        ] >= 24,
        "shuffled_engagement_at_most_6_of_32": counts[
            "shuffled_engaged"
        ] <= 6,
        "connected_only_minus_shuffled_only_at_least_20": counts[
            "connected_only_minus_shuffled_only"
        ] >= 20,
    }
    mechanism_discrimination_passed = all(discrimination_gates.values())
    reliability_gate = counts["connected_engaged"] >= 28
    if mechanism_discrimination_passed and reliability_gate:
        interpretation = "content_blind_seed_robust_and_discriminative"
    elif mechanism_discrimination_passed:
        interpretation = "capable_but_too_stochastic"
    elif reliability_gate:
        interpretation = "reliable_engagement_without_control_discrimination"
    else:
        interpretation = "content_blind_seed_robustness_not_established"
    return {
        "mechanism_discrimination": {
            "gates": discrimination_gates,
            "passed": mechanism_discrimination_passed,
        },
        "reliability": {
            "gate": {
                "connected_engagement_at_least_28_of_32": reliability_gate
            },
            "passed": reliability_gate,
        },
        "interpretation": interpretation,
        "does_not_prove_residual_responsibility_necessary": True,
    }


def _cohort_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    paired = Counter(str(row["paired_outcome"]) for row in rows)
    connected = sum(bool(row["connected"]["engaged"]) for row in rows)
    shuffled = sum(bool(row["outcome_shuffled"]["engaged"]) for row in rows)
    return {
        "total": len(rows),
        "connected_engaged": connected,
        "shuffled_engaged": shuffled,
        "connected_only": paired["connected_only"],
        "shuffled_only": paired["shuffled_only"],
        "both": paired["both"],
        "neither": paired["neither"],
        "connected_only_minus_shuffled_only": (
            paired["connected_only"] - paired["shuffled_only"]
        ),
    }


def _load_or_initialize_result(
    cfg: V3BConfig,
    manifest: Mapping[str, Any],
    manifest_sha256: str,
    records: Sequence[CompetenceEvidenceRecord],
    permutation: Sequence[int],
) -> dict[str, Any]:
    target = Path(cfg.output)
    if target.exists():
        result = dict(_load_json(target))
        if result.get("seed_manifest", {}).get("sha256") != manifest_sha256:
            raise RuntimeError("V3B checkpoint seed manifest mismatch")
        if result.get("source_rows_sha256") != SOURCE_ROWS_SHA256:
            raise RuntimeError("V3B checkpoint source-row mismatch")
        return result
    return {
        "schema_version": "native_competence_envelope_v3b_seed_robustness.v1",
        "preregistered": True,
        "source_v3_artifact": {
            "path": cfg.source_v3_artifact,
            "sha256": SOURCE_V3_SHA256,
        },
        "source_rows_sha256": SOURCE_ROWS_SHA256,
        "seed_manifest": {
            "path": cfg.seed_manifest,
            "sha256": manifest_sha256,
            "preregistration_commit": manifest["preregistration_commit"],
            "seed_list_sha256": manifest["seed_list_sha256"],
        },
        "frozen_factor_law": {
            "only_factor": "content_blind_member_choice_genome_seed",
            "signal_row_count": len(records),
            "request_order": "canonical_v3_order",
            "outcome_shuffle_sha256": _hash_list(permutation),
            "capacity_lifecycle_thresholds_unchanged": True,
            "order_sensitive_conjunction_deduplication_unchanged": True,
            "source_v3_artifact_sha256": SOURCE_V3_SHA256,
            "source_learner_sha256": LEARNER_SHA256,
        },
        "completed_seed_count": 0,
        "seed_results": [],
        "stage": "running",
    }


def _validate_contiguous_prefix(
    completed: Sequence[Mapping[str, Any]],
    seed_rows: Sequence[Mapping[str, Any]],
) -> None:
    for ordinal, row in enumerate(completed):
        if int(row["ordinal"]) != ordinal:
            raise RuntimeError("V3B checkpoint is not a contiguous prefix")
        if int(row["seed"]) != int(seed_rows[ordinal]["seed"]):
            raise RuntimeError("V3B checkpoint seed identity mismatch")


def _validate_persisted_prefix(
    completed: Sequence[Mapping[str, Any]],
) -> None:
    for row in completed:
        for arm_name in ("connected", "outcome_shuffled"):
            artifact = row[arm_name]["organism_artifact"]
            path = Path(str(artifact["path"]))
            if not path.exists():
                raise RuntimeError("V3B checkpoint organism is missing")
            compressed = path.read_bytes()
            if hashlib.sha256(compressed).hexdigest() != artifact[
                "compressed_sha256"
            ]:
                raise RuntimeError("V3B checkpoint organism hash mismatch")
            raw = gzip.decompress(compressed)
            if hashlib.sha256(raw).hexdigest() != artifact[
                "uncompressed_sha256"
            ]:
                raise RuntimeError("V3B checkpoint raw organism hash mismatch")
            restored = pickle.loads(raw)
            if not isinstance(restored, GraphNativeCompetenceEnvelope):
                raise RuntimeError("V3B checkpoint organism type mismatch")
            if _hash_json(restored.to_manifest()) != artifact[
                "source_manifest_sha256"
            ]:
                raise RuntimeError("V3B checkpoint organism parity mismatch")


def _file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_json(path: str | Path) -> Mapping[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, value: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
