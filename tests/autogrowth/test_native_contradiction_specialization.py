from __future__ import annotations

import copy
import inspect
import pickle

import pytest

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.nodes import StemCellState, StemCellTerminal
from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState, CompetenceContextCell, CompetenceContextGrowthGenome,
    CompetenceEvidenceRecord, GraphNativeCompetenceEnvelope, SpecializationMode,
)

def _real(key="real"):
    return FrameContext(key, FrameKind.REAL, values={})

def _record(key, signals, completion):
    return CompetenceEvidenceRecord(
        evidence_key=key, active_signal_ids=signals, policy_response=True,
        observed_completion=completion, actuator_identity=f"actuator:{key}",
        completion_terminal_identity="terminal:goal",
    )

def _parent(polarity=AvailabilityState.AVAILABLE):
    envelope = GraphNativeCompetenceEnvelope()
    stem = StemCellTerminal("parent")
    stem.state = StemCellState.TRIAL
    cell = CompetenceContextCell(
        cell_id="parent", members=("atom:A",), born_round=0,
        born_request_ordinal=0, stem_cell=stem,
    )
    envelope.cells[cell.cell_id] = cell
    envelope._member_specs.add(cell.members)
    outcome = polarity == AvailabilityState.AVAILABLE
    for index in range(4):
        envelope.add_unique_evidence(
            _record(f"support:{index}", ("atom:A", "atom:B"), outcome)
        )
    envelope._review_lifecycle(final=False)
    envelope.rebuild_graph()
    assert cell.state == StemCellState.MATURE and cell.polarity == polarity
    return envelope

def _specialize(envelope, key="contradiction", completion=False):
    return envelope.observe_real_outcome(
        _real(key), _record(key, ("atom:A",), completion),
        lifecycle_connected=True,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
    )

def test_available_parent_grows_one_safe_child_from_graph_correction():
    envelope = _parent()
    emission = _specialize(envelope)
    assert emission.transitioned_cell_ids == ("parent",)
    assert emission.specialization_request_parent_ids == ("parent",)
    child = envelope.cells[emission.specialization_child_ids[0]]
    assert child.members == ("context:parent", "atom:B")
    assert child.lineage_parent_id == "parent" and child.specialization_depth == 1
    assert child.state == StemCellState.MATURE
    assert child.evidence_keys == tuple(f"support:{i}" for i in range(4))
    assert envelope.cells["parent"].state == StemCellState.PROBATION
    assert envelope.classify(("atom:A", "atom:B"), policy_response=True).state == AvailabilityState.AVAILABLE
    result = envelope.classify(("atom:A",), policy_response=True)
    assert result.state == AvailabilityState.UNKNOWN and "parent" not in result.available_cell_ids

def test_refuted_specialization_is_polarity_symmetric():
    envelope = _parent(AvailabilityState.REFUTED)
    emission = _specialize(envelope, completion=True)
    child = envelope.cells[emission.specialization_child_ids[0]]
    assert child.state == StemCellState.MATURE
    assert child.polarity == AvailabilityState.REFUTED
    assert envelope.classify(("atom:A", "atom:B"), policy_response=True).state == AvailabilityState.REFUTED
    assert envelope.classify(("atom:A",), policy_response=True).state == AvailabilityState.UNKNOWN

def test_impure_child_stays_trial_and_duplicate_cannot_retry():
    envelope = _parent()
    envelope.observe_real_outcome(
        _real("impurity"), _record("impurity", ("atom:A", "atom:B"), False),
        lifecycle_connected=False,
    )
    emission = _specialize(envelope)
    child = envelope.cells[emission.specialization_child_ids[0]]
    assert child.state == StemCellState.TRIAL
    assert (child.successes, child.failures) == (4, 1)
    duplicate = _specialize(envelope)
    assert not duplicate.evidence_inserted and not duplicate.specialization_child_ids
    assert envelope.specialization_audit.request_opportunities == 1

def test_virtual_observation_cannot_mutate_specialization_state():
    envelope = _parent()
    before = envelope.continuation_digest_v2()
    with pytest.raises(ValueError, match="REAL"):
        envelope.observe_real_outcome(
            FrameContext("dream", FrameKind.VIRTUAL, values={}),
            _record("dream", ("atom:A",), False), lifecycle_connected=True,
            specialization_mode=SpecializationMode.LOCAL_CONTRAST,
        )
    assert envelope.continuation_digest_v2() == before

def test_continuation_v2_detects_required_mutations():
    envelope = _parent()
    child_id = _specialize(envelope).specialization_child_ids[0]
    baseline = envelope.continuation_digest_v2()
    evidence_changed = copy.deepcopy(envelope)
    old = evidence_changed.evidence["support:0"]
    evidence_changed.evidence["support:0"] = CompetenceEvidenceRecord(
        old.evidence_key, old.active_signal_ids, old.policy_response,
        old.observed_completion, "actuator:mutated",
        old.completion_terminal_identity,
    )
    counter_changed = copy.deepcopy(envelope)
    counter_changed._review_count += 1
    members_changed = copy.deepcopy(envelope)
    members_changed._member_specs.add(("atom:mutated",))
    lineage_changed = copy.deepcopy(envelope)
    lineage_changed.cells[child_id].lineage_parent_id = "mutated"
    for changed in (evidence_changed, counter_changed, members_changed, lineage_changed):
        assert changed.continuation_digest_v2() != baseline

def test_serialized_continuation_nominates_same_child_and_lifecycle():
    source = _parent()
    restored = pickle.loads(pickle.dumps(source, protocol=pickle.HIGHEST_PROTOCOL))
    assert _specialize(source) == _specialize(restored)
    assert source.continuation_manifest_v2() == restored.continuation_manifest_v2()

def test_runner_api_cannot_supply_parent_or_candidate_identity():
    observe = inspect.signature(GraphNativeCompetenceEnvelope.observe_real_outcome).parameters
    genome = inspect.signature(CompetenceContextGrowthGenome.propose_specialization).parameters
    assert "parent_id" not in observe and "candidate_id" not in observe
    assert tuple(genome) == ("self", "request")

