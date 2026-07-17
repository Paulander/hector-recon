from __future__ import annotations

from pathlib import Path

from recon_lite_hector.nodes import StemCellState, StemCellTerminal

from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState,
    CompetenceContextCell,
    CompetenceEvidenceRecord,
    GraphNativeCompetenceEnvelope,
)
from recon_lite_chess.autogrowth.native_competence_envelope_v3b_seed_robustness import (
    EXCLUDED_SEED_MAX,
    LEARNER_MODULE,
    LEARNER_SHA256,
    SEED_COUNT,
    SOURCE_ROWS_SHA256,
    SOURCE_V3_ARTIFACT,
    SOURCE_V3_SHA256,
    _composition_minimality,
    _duplicate_audit,
    _file_sha256,
    _hash_json,
    _load_json,
    _state_digests,
    _persist_organism,
    adjudicate_cohort,
    audit_envelope,
    derive_seed,
    generate_seed_manifest,
    validate_seed_manifest,
)


def _records() -> tuple[CompetenceEvidenceRecord, ...]:
    return tuple(
        CompetenceEvidenceRecord(
            evidence_key=f"evidence-{index}",
            active_signal_ids=(
                "shared",
                "success" if index < 4 else "failure",
                f"row-{index}",
            ),
            policy_response=True,
            observed_completion=index < 4,
            actuator_identity=f"chess_move:a{index + 1}a1",
            completion_terminal_identity="mate",
        )
        for index in range(8)
    )


def _cell(
    cell_id: str,
    members: tuple[str, ...],
    *,
    state: StemCellState = StemCellState.MATURE,
) -> CompetenceContextCell:
    stem = StemCellTerminal(cell_id)
    stem.state = state
    return CompetenceContextCell(
        cell_id=cell_id,
        members=members,
        born_round=0,
        born_request_ordinal=0,
        stem_cell=stem,
        polarity=AvailabilityState.AVAILABLE,
        support=4,
        successes=4,
        failures=0,
        maturity_review=1,
    )


def _paired_row(connected: bool, shuffled: bool) -> dict[str, object]:
    if connected and not shuffled:
        paired = "connected_only"
    elif shuffled and not connected:
        paired = "shuffled_only"
    elif connected:
        paired = "both"
    else:
        paired = "neither"
    return {
        "connected": {"engaged": connected},
        "outcome_shuffled": {"engaged": shuffled},
        "paired_outcome": paired,
    }


def test_v3b_locks_v3_artifact_rows_and_learner() -> None:
    source = _load_json(SOURCE_V3_ARTIFACT)
    assert _file_sha256(SOURCE_V3_ARTIFACT) == SOURCE_V3_SHA256
    assert _hash_json(source["training_rows"]) == SOURCE_ROWS_SHA256
    assert _file_sha256(LEARNER_MODULE) == LEARNER_SHA256


def test_seed_derivation_is_deterministic_unique_and_excludes_audited_range(
    tmp_path: Path,
) -> None:
    commit = "a" * 40
    expected = [derive_seed(commit, ordinal) for ordinal in range(SEED_COUNT)]
    repeated = [derive_seed(commit, ordinal) for ordinal in range(SEED_COUNT)]
    assert repeated == expected
    assert len({row["seed"] for row in expected}) == SEED_COUNT
    assert min(row["seed"] for row in expected) > EXCLUDED_SEED_MAX

    path = tmp_path / "manifest.json"
    manifest = generate_seed_manifest(commit, output=str(path))
    validate_seed_manifest(manifest, verify_files=False)
    assert [row["ordinal"] for row in manifest["seeds"]] == list(
        range(SEED_COUNT)
    )


def test_adjudication_reports_discrimination_and_reliability_independently() -> None:
    capable_but_stochastic = (
        [_paired_row(True, False) for _ in range(24)]
        + [_paired_row(False, False) for _ in range(8)]
    )
    result = adjudicate_cohort(capable_but_stochastic)
    assert result["mechanism_discrimination"]["passed"] is True
    assert result["reliability"]["passed"] is False
    assert result["interpretation"] == "capable_but_too_stochastic"

    robust = (
        [_paired_row(True, False) for _ in range(28)]
        + [_paired_row(False, False) for _ in range(4)]
    )
    robust_result = adjudicate_cohort(robust)
    assert robust_result["mechanism_discrimination"]["passed"] is True
    assert robust_result["reliability"]["passed"] is True


def test_member_order_duplicate_is_audited_without_changing_frozen_learner() -> None:
    envelope = GraphNativeCompetenceEnvelope()
    envelope.audit.proposal_rows.extend([
        {
            "members": ["a", "b"],
            "admitted": True,
            "reason": None,
        },
        {
            "members": ["b", "a"],
            "admitted": True,
            "reason": None,
        },
        {
            "members": ["a", "b"],
            "admitted": False,
            "reason": "duplicate",
        },
    ])
    audit = _duplicate_audit(envelope.audit.proposal_rows, envelope)
    assert audit["member_order_canonical_duplicate_group_count"] == 1
    assert audit["order_variant_group_count"] == 1
    assert audit["order_sensitive_missed_duplicate_admissions"] == 1
    assert audit["learner_unchanged"] is True


def test_minimality_uses_exact_mask_and_strict_canonical_member_subset() -> None:
    audit = _composition_minimality([
        {
            "cell_id": "minimal",
            "raw_arity": 2,
            "canonical_members": ["a", "b"],
            "activation_mask_hex": "000000000000000f",
        },
        {
            "cell_id": "redundant",
            "raw_arity": 3,
            "canonical_members": ["a", "b", "c"],
            "activation_mask_hex": "000000000000000f",
        },
    ])
    classes = {row["cell_id"]: row for row in audit["rows"]}
    assert classes["minimal"]["classification"] == "minimal"
    assert classes["redundant"]["classification"] == (
        "redundant_strict_superset"
    )
    assert classes["redundant"]["strict_subset_same_mask_cell_ids"] == [
        "minimal"
    ]


def test_diagnostic_uses_actual_before_after_digests_and_exact_masks() -> None:
    envelope = GraphNativeCompetenceEnvelope(cells={
        "positive": _cell("positive", ("success",)),
        "redundant": _cell("redundant", ("shared", "success")),
    })
    for record in _records():
        envelope.add_unique_evidence(record)
    before = _state_digests(envelope)
    audit = audit_envelope(envelope, _records())
    after = _state_digests(envelope)
    assert before == after
    masks = {
        row["cell_id"]: row["activation_mask_hex"]
        for row in audit["patterns_and_activation_masks"]
    }
    assert masks == {
        "positive": "000000000000000f",
        "redundant": "000000000000000f",
    }
    assert audit["unique_activation_masks"]["count"] == 1
    assert audit["composition_minimality"]["histogram"] == {
        "redundant_strict_superset": 1
    }


def test_every_organism_format_restores_even_when_envelope_is_empty(
    tmp_path: Path,
) -> None:
    artifact = _persist_organism(
        GraphNativeCompetenceEnvelope(), str(tmp_path), 0, 1001, "connected"
    )
    assert artifact["persisted"] is True
    assert artifact["empty_envelope"] is True
    assert artifact["restore_parity"] is True
    assert artifact["source_manifest_sha256"] == artifact[
        "restored_manifest_sha256"
    ]
