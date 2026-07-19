from __future__ import annotations

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.nodes import StemCellState, StemCellTerminal

from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState,
    CompetenceContextCell,
    CompetenceEvidenceRecord,
    GraphNativeCompetenceEnvelope,
)
from recon_lite_chess.autogrowth.native_mature_cell_falsification import (
    _apply_shuffled_control,
    _cohort_metrics,
    _data_firewall,
)


def _envelope() -> GraphNativeCompetenceEnvelope:
    envelope = GraphNativeCompetenceEnvelope()
    for cell_id, member in (("first", "atom:a"), ("second", "atom:b")):
        stem = StemCellTerminal(cell_id)
        stem.state = StemCellState.MATURE
        cell = CompetenceContextCell(
            cell_id=cell_id,
            members=(member,),
            born_round=0,
            born_request_ordinal=0,
            stem_cell=stem,
            polarity=AvailabilityState.AVAILABLE,
            support=4,
            successes=4,
        )
        envelope.cells[cell_id] = cell
    envelope.rebuild_graph()
    return envelope


def _failure() -> CompetenceEvidenceRecord:
    return CompetenceEvidenceRecord(
        evidence_key="unique",
        active_signal_ids=("atom:a",),
        policy_response=True,
        observed_completion=False,
        actuator_identity="actuator:a",
        completion_terminal_identity="completion",
    )


def test_shuffled_control_consumes_graph_emission_with_transition_parity() -> None:
    envelope = _envelope()
    emission = envelope.observe_real_outcome(
        FrameContext("real", FrameKind.REAL, values={}),
        _failure(),
        lifecycle_connected=False,
    )
    transitioned = _apply_shuffled_control(
        envelope, emission, {"first": "second", "second": "first"}
    )
    assert emission.contradiction_cell_ids == ("first",)
    assert transitioned == ("second",)
    assert envelope.cells["first"].state == StemCellState.MATURE
    assert envelope.cells["second"].state == StemCellState.PROBATION


def test_cohort_metrics_preserves_empty_and_safe_organisms() -> None:
    rows = [
        {"metrics": {"tp": 0, "fp": 0, "safe_narrow_pass": False, "strict_pass": False}},
        {"metrics": {"tp": 14, "fp": 0, "safe_narrow_pass": True, "strict_pass": True}},
    ]
    result = _cohort_metrics(rows)
    assert result["organism_count"] == 2
    assert result["total_tp"] == 14
    assert result["total_fp"] == 0
    assert result["safe_narrow_passes"] == 1
    assert result["strict_passes"] == 1


def test_package_firewall_excludes_every_forbidden_extension() -> None:
    assert not any(_data_firewall().values())
