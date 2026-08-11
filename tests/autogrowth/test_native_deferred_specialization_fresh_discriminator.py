from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import chess
import pytest

from recon_lite_chess.autogrowth.native_deferred_specialization_fresh_discriminator import (
    ARMS,
    RESULT_PATH,
    SOURCE_MANIFEST,
    ExperimentStop,
    StopCategory,
    StreamRow,
    _sha_json,
    canonical_d4_orbit_key,
    classify_conclusion,
    exact_one_sided_sign_test,
    frozen_genome_seeds,
    holm_adjust_two,
    mutation_free_evaluation,
    outcome_blind_exposure_count,
    paired_exposure_admission,
    preoutcome_record,
    rows_by_region,
    sealed_metrics,
    validate_stream_rows,
)


def _row(ordinal: int, region: str = "child_prospective_certification") -> StreamRow:
    board = chess.Board(None)
    board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.B2, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(chess.H8 - ordinal, chess.Piece(chess.KING, chess.BLACK))
    board.turn = chess.WHITE
    fen = board.fen()
    return StreamRow(
        region=region,
        region_ordinal=ordinal,
        global_ordinal=ordinal,
        row_id=f"row-{ordinal}",
        predecessor_fen=fen,
        d4_orbit_key=canonical_d4_orbit_key(fen),
        planned_physical_interaction_id=f"physical-{ordinal}",
    )


def test_manifest_freezes_one_identical_ordered_stream_for_every_arm():
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    rows = tuple(StreamRow(**row) for row in manifest["stream_rows"])
    orders = {
        mode.value: tuple(row.row_id for row in rows) for mode in ARMS
    }
    assert len(set(orders.values())) == 1
    assert manifest["single_shared_post_parent_stream"][
        "row_order_identical_across_all_arms_and_seeds"
    ] is True
    assert manifest["scientific_outcomes_accessed"] is False


def test_stream_construction_has_no_child_identity_or_outcome_parameter():
    from recon_lite_chess.autogrowth import (
        native_deferred_specialization_fresh_discriminator as module,
    )

    signature = inspect.signature(module.build_frozen_stream)
    assert tuple(signature.parameters) == ("historical_orbits",)
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    forbidden = {"child_id", "selected_child_identity", "outcome", "actual"}
    assert not forbidden.intersection(manifest["stream_rows"][0])


def test_complete_d4_orbit_equivalence_and_distinct_position_separation():
    base = "8/8/8/8/8/2K5/3R4/7k w - - 0 1"
    reflected = "8/8/8/8/8/5K2/4R3/k7 w - - 0 1"
    distinct = "8/8/8/8/8/2K5/4R3/7k w - - 0 1"
    assert canonical_d4_orbit_key(base) == canonical_d4_orbit_key(reflected)
    assert canonical_d4_orbit_key(base) != canonical_d4_orbit_key(distinct)


def test_frozen_stream_is_globally_d4_and_physical_id_disjoint():
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    rows = tuple(StreamRow(**row) for row in manifest["stream_rows"])
    validate_stream_rows(rows)
    assert len({row.d4_orbit_key for row in rows}) == len(rows)
    assert len({row.planned_physical_interaction_id for row in rows}) == len(rows)


def test_outcome_blind_exposure_count_reads_only_preoutcome_matches():
    matches = (("child",), (), ("other", "child"), ("other",))
    assert outcome_blind_exposure_count("child", matches) == 2
    assert "outcome" not in inspect.signature(
        outcome_blind_exposure_count
    ).parameters


def test_24_of_32_gate_does_not_select_a_24_seed_analysis_subset():
    rows = [
        {
            "ordinal": ordinal,
            "local_count": 4 if ordinal < 24 else 0,
            "blind_count": 4 if ordinal < 24 else 0,
        }
        for ordinal in range(32)
    ]
    result = paired_exposure_admission(rows)
    assert result["passed"] is True
    assert result["paired_seed_count_reaching_minimum"] == 24
    assert result["admitted_ordinals_for_gate_only"] == list(range(24))
    assert result["analysis_ordinals"] == list(range(32))
    assert result["subset_selection_permitted"] is False


def test_exposure_starvation_keeps_all_32_and_is_terminal():
    rows = [
        {"ordinal": ordinal, "local_count": 4, "blind_count": 3}
        for ordinal in range(32)
    ]
    admission = paired_exposure_admission(rows)
    assert admission["passed"] is False
    assert classify_conclusion(
        exposure_passed=False,
        validity_passed=True,
        adjusted_probabilities=(0.0, 0.0),
    ) is StopCategory.PAIRED_CHILD_EVIDENCE_STARVATION


def test_sequential_record_is_committed_before_outcome_exists():
    classification = SimpleNamespace(
        state=SimpleNamespace(value="UNKNOWN"),
        available_cell_ids=(),
        refuted_cell_ids=(),
    )
    result = preoutcome_record(
        row=_row(0), classification=classification,
        matching_cell_ids=("shadow",), selected_action="b2b8",
    )
    assert result["outcome_committed"] is False
    assert "observed_outcome" not in result
    assert result["matching_cell_ids_before"] == ["shadow"]


class _FakeTrace:
    actuation = SimpleNamespace(move_uci="b2b8")


class _FakeCommitment:
    trace = _FakeTrace()


class _FakeAuthority:
    def __init__(self, *, mutate: bool = False) -> None:
        self.value = 0
        self.mutate = mutate

    def continuation_digest(self):
        return str(self.value)

    def evaluate_sealed_real(self, _frame):
        if self.mutate:
            self.value += 1
        return {
            "commitment": _FakeCommitment(),
            "classification": SimpleNamespace(
                state=SimpleNamespace(name="UNKNOWN"),
                available_cell_ids=(), refuted_cell_ids=(),
            ),
        }


def test_read_only_evaluation_detects_any_mutation(monkeypatch):
    monkeypatch.setattr(
        "recon_lite_chess.autogrowth."
        "native_deferred_specialization_fresh_discriminator._trace_digest",
        lambda _trace: "semantic",
    )
    safe = _FakeAuthority()
    rows = (_row(0),)
    result = mutation_free_evaluation(safe, rows)
    assert len(result) == 1
    with pytest.raises(ExperimentStop) as exc:
        mutation_free_evaluation(_FakeAuthority(mutate=True), rows)
    assert exc.value.category is StopCategory.INSTRUMENT_STOP


def test_safe_coverage_never_suppresses_unsafe_organism():
    metrics = sealed_metrics((
        {"available": True, "actual": True},
        {"available": True, "actual": False},
        {"available": False, "actual": True},
    ))
    assert metrics == {
        "raw_true_positives": 1,
        "raw_false_positives": 1,
        "abstentions": 1,
        "safe_positive_coverage": 0,
    }


def test_exact_sign_test_uses_seed_pairs_and_retains_ties():
    treatment = [2] * 20 + [0] * 4 + [1] * 8
    control = [1] * 20 + [1] * 4 + [1] * 8
    result = exact_one_sided_sign_test(treatment, control)
    assert result["wins"] == 20
    assert result["losses"] == 4
    assert result["ties"] == 8
    assert result["effective_non_tied_n"] == 24
    assert len(result["paired_differences"]) == 32


def test_holm_correction_is_monotone_in_the_ordered_family():
    assert holm_adjust_two((0.01, 0.03)) == pytest.approx((0.02, 0.03))
    assert holm_adjust_two((0.04, 0.01)) == pytest.approx((0.04, 0.02))


def test_complete_reporting_and_new_seed_freeze():
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    seeds = frozen_genome_seeds()
    assert len(seeds) == len(set(seeds)) == 32
    assert manifest["seed_derivation"]["genome_seeds"] == list(seeds)
    assert [row["ordinal"] for row in result["all_32_seeds"]] == list(range(32))
    assert all(row["status"] == "FROZEN_NOT_STARTED" for row in result["all_32_seeds"])
    assert result["scientific_outcomes_accessed"] is False


@pytest.mark.parametrize(
    ("exposure", "validity", "probabilities", "expected"),
    [
        (False, True, (0.01, 0.01), StopCategory.PAIRED_CHILD_EVIDENCE_STARVATION),
        (True, False, (0.01, 0.01), StopCategory.INSTRUMENT_STOP),
        (True, True, (0.01, 0.06), StopCategory.DEFERRED_SPECIALIZATION_NOT_SUPERIOR),
        (True, True, (0.01, 0.02), StopCategory.DEFERRED_LOCAL_SPECIALIZATION_SUPPORTED),
    ],
)
def test_every_stop_category_is_fail_fast(exposure, validity, probabilities, expected):
    assert classify_conclusion(
        exposure_passed=exposure,
        validity_passed=validity,
        adjusted_probabilities=probabilities,
    ) is expected


def test_manifest_payload_digest_and_unexecuted_result_binding():
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    payload = dict(manifest)
    expected = payload.pop("manifest_payload_sha256")
    assert _sha_json(payload) == expected
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    assert result["source_manifest_sha256"] == __import__("hashlib").sha256(
        SOURCE_MANIFEST.read_bytes()
    ).hexdigest()
    assert result["status"] == "FROZEN_NOT_EXECUTED"


def test_region_filter_never_reorders_or_selects_by_child():
    rows = tuple(_row(index, "child_prospective_certification") for index in range(4))
    assert rows_by_region(rows, "child_prospective_certification") == rows
    assert "child" not in inspect.signature(rows_by_region).parameters
