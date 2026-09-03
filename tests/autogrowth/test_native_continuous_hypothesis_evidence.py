"""Data-free exact contracts for semantic birth before graph allocation.

The source and tiny synthetic interactions are built in code; no experiment
artifacts, chess curriculum pools, solution oracle, or protected data is read.
"""
from dataclasses import replace

import pytest

from recon_lite_chess.autogrowth import native_prospective_evidence_authority_v2 as module
from recon_lite_chess.autogrowth.native_competence_envelope import AvailabilityState, PROVENANCE_COMMITMENT_V4
from recon_lite_chess.autogrowth.native_prospective_boundary_candidate_ecology import boundary_candidate_semantic_identity
from tests.autogrowth.test_native_mixed_evidence_specialization import (
    _mixed_authority, _consume, _open_mint, ADVERSARIAL,
)


def _event(authority, number, outcome=True):
    return _consume(authority, outcome=outcome, fullmove=700 + number,
                    frame_id=f"continuous-contract:{number}")[0][2]


def _birth(authority, receipt, *, candidate_id="continuous-clean", broad=False):
    reference = authority.accepted_real_references[receipt.receipt_id]
    negatives = [item for item in authority.accepted_real_references.values() if not item.observed_outcome]
    roles = dict(reference.typed_signal_roles)
    members = sorted(item for item in reference.ordered_signal_identities
                     if roles.get(item) in {"BASE_TERMINAL", "MATURE_COMPOSITE"}
                     and (any(item in row.ordered_signal_identities for row in negatives) if broad
                          else all(item not in row.ordered_signal_identities for row in negatives)))
    assert members
    member = members[0]
    source = authority.source_policy_identity_for_receipt(receipt.receipt_id)
    kwargs = dict(candidate_id=candidate_id, members=(member,), member_signal_roles=((member, roles[member]),),
                  source_identity=source, semantic_identity=boundary_candidate_semantic_identity((member,), ((member, roles[member]),), source),
                  birth_frontier_ordinal=authority.next_expected_ordinal - 1,
                  triggering_receipt_id=receipt.receipt_id)
    digest = authority.register_boundary_hypothesis_birth(**kwargs)
    return digest, kwargs


def _request(authority, candidate_id="continuous-clean"):
    birth = authority.boundary_hypothesis_births[candidate_id]
    frontier = authority.next_expected_ordinal
    inspected, support, _negatives = authority._continuous_evidence_ids(birth, frontier - 1)
    inspected_commitment = module._compact_set_commitment(inspected, exclusive_frontier=frontier)
    support_commitment = module._compact_set_commitment(support, exclusive_frontier=frontier)
    return module.BoundaryPromotionRequest(
        candidate_id=candidate_id, members=birth.members, fixed_polarity=True,
        triggering_receipt_id=birth.triggering_receipt_id,
        supporting_receipt_ids=support_commitment.witness_ids,
        inspected_receipt_ids=inspected_commitment.witness_ids,
        source_generation=authority.current_generation,
        provenance_schema_version=PROVENANCE_COMMITMENT_V4,
        supporting_receipt_commitment=support_commitment,
        inspected_receipt_commitment=inspected_commitment,
        hypothesis_birth_digest=birth.birth_digest,
    )


@pytest.fixture
def authority():
    return _mixed_authority(AvailabilityState.AVAILABLE, structural_mode=module.StructuralMode.EVENT_DRIVEN)


def test_continuous_transfer_certifies_once_without_rewriting_past_emissions(authority):
    discovery = _event(authority, 0)
    _, kwargs = _birth(authority, discovery)
    for index in range(1, 5):
        _event(authority, index)
    old_emissions = dict(authority.emissions)
    request = _request(authority)
    authority.settle_pending_structural_requests((request,))
    child_id = authority._adaptive_boundary_child_id(request)
    child = authority.states[child_id]
    assert child.prospectively_certified and child.successes == child.support == 4
    assert discovery.receipt_id not in child.certification_receipt_ids
    assert child.hypothesis.birth_frontier == kwargs["birth_frontier_ordinal"]
    assert child.hypothesis.materialization_frontier == authority.next_expected_ordinal - 1
    assert authority.emissions == old_emissions
    assert all(child_id not in emission.matching_cell_ids for emission in old_emissions.values())
    authority.verify_full_history_boundary("continuous physical activation")
    restored = module.NativeProspectiveAuthorityV2.loads(authority.dumps())
    assert restored.continuation_manifest() == authority.continuation_manifest()
    _event(restored, 5)
    assert restored.states[child_id].successes == 5
    restored.verify_full_history_boundary("continuous first subsequent REAL")


def test_three_postbirth_receipts_cannot_count_the_discovery_trigger(authority):
    discovery = _event(authority, 0)
    _birth(authority, discovery)
    for index in range(1, 4):
        _event(authority, index)
    before = authority.continuation_manifest()
    with pytest.raises(module.ProspectiveV2IntegrityError, match="four strictly postbirth"):
        authority.settle_pending_structural_requests((_request(authority),))
    assert authority.continuation_manifest() == before
    restored = module.NativeProspectiveAuthorityV2.loads(authority.dumps())
    assert restored.continuation_manifest() == before


def test_backdated_birth_and_source_substitution_are_atomic(authority):
    discovery = _event(authority, 0)
    _, kwargs = _birth(authority, discovery)
    _event(authority, 1)
    before = authority.continuation_manifest()
    # Re-reporting an existing immutable residual is a read-only no-op, not
    # a new old-dated birth.  A different ID with that date is forbidden.
    assert authority.register_boundary_hypothesis_birth(**kwargs) == authority.boundary_hypothesis_births[kwargs["candidate_id"]].birth_digest
    assert authority.continuation_manifest() == before
    with pytest.raises(module.ProspectiveV2IntegrityError, match="backdated"):
        authority.register_boundary_hypothesis_birth(**{**kwargs, "candidate_id": "backdated"})
    changed = {**kwargs, "candidate_id": "wrong-source", "birth_frontier_ordinal": authority.next_expected_ordinal - 1,
               "source_identity": "wrong-source"}
    changed["semantic_identity"] = boundary_candidate_semantic_identity(changed["members"], changed["member_signal_roles"], changed["source_identity"])
    with pytest.raises(module.ProspectiveV2IntegrityError, match="source"):
        authority.register_boundary_hypothesis_birth(**changed)
    assert authority.continuation_manifest() == before


def test_prebirth_negative_survives_a_new_positive_incarnation(authority):
    discovery = _event(authority, 0)
    _birth(authority, discovery, broad=True)
    for index in range(1, 5):
        _event(authority, index)
    before = authority.continuation_manifest()
    with pytest.raises(module.ProspectiveV2IntegrityError, match="known negative"):
        authority.settle_pending_structural_requests((_request(authority),))
    assert authority.continuation_manifest() == before


def test_transfer_failure_rolls_back_allocation_not_semantic_birth(authority, monkeypatch):
    discovery = _event(authority, 0)
    _birth(authority, discovery)
    for index in range(1, 5):
        _event(authority, index)
    request = _request(authority)
    before = authority.continuation_manifest()
    original = authority._record_boundary_candidate
    def fail(operation, payload):
        original(operation, payload)
        if operation == "boundary_promotion_materialize":
            raise RuntimeError("test late transfer failure")
    monkeypatch.setattr(authority, "_record_boundary_candidate", fail)
    with pytest.raises(RuntimeError, match="late transfer failure"):
        authority.settle_pending_structural_requests((request,))
    assert authority.continuation_manifest() == before
    assert request.candidate_id in authority.boundary_hypothesis_births


def test_birth_link_and_postbirth_support_cannot_be_forged(authority):
    discovery = _event(authority, 0)
    _birth(authority, discovery)
    for index in range(1, 5):
        _event(authority, index)
    request = _request(authority)
    before = authority.continuation_manifest()
    forged = replace(request, hypothesis_birth_digest="a" * 64, promotion_gate_digest="")
    with pytest.raises(module.ProspectiveV2IntegrityError, match="precommitted"):
        authority.settle_pending_structural_requests((forged,))
    assert authority.continuation_manifest() == before


def test_source_and_exact_role_changes_abstain_before_dispatch(authority):
    discovery = _event(authority, 0)
    _birth(authority, discovery)
    for index in range(1, 5):
        latest = _event(authority, index)
    request = _request(authority)
    authority.settle_pending_structural_requests((request,))
    child_id = authority._adaptive_boundary_child_id(request)
    assert child_id in authority._graph_measure(latest.trace)["available"]
    changed_source = replace(latest.trace, source_state_identity="different-frozen-policy")
    changed_role = replace(latest.trace, terminal_signals=tuple(
        replace(signal, role="DIFFERENT_TYPED_ROLE") if signal.identity in request.members else signal
        for signal in latest.trace.terminal_signals))
    before = authority.continuation_manifest()
    for trace in (changed_source, changed_role):
        measured = authority._graph_measure(trace)
        assert child_id not in measured["commitment"]
        assert child_id not in measured["available"]
    assert authority.continuation_manifest() == before


def test_semantic_birth_is_committed_in_the_next_predecessor(authority):
    discovery = _event(authority, 0)
    _birth(authority, discovery)
    _event(authority, 1)
    authority.boundary_hypothesis_births.clear()
    authority._boundary_hypothesis_birth_digest = ""
    with pytest.raises(module.ProspectiveV2IntegrityError, match="predecessor"):
        authority.verify_full_history_boundary("deleted precommitment")


def test_birth_registration_itself_rolls_back_on_commit_failure(authority, monkeypatch):
    discovery = _event(authority, 0)
    before = authority.continuation_manifest()
    original = authority._advance_boundary_commitment
    def fail(operation, payload):
        original(operation, payload)
        if operation == "boundary_hypothesis_birth":
            raise RuntimeError("test registration failure")
    monkeypatch.setattr(authority, "_advance_boundary_commitment", fail)
    with pytest.raises(RuntimeError, match="registration failure"):
        _birth(authority, discovery)
    assert authority.continuation_manifest() == before


def test_pending_postbirth_event_restores_with_exact_precommitment(authority):
    discovery = _event(authority, 0)
    _birth(authority, discovery)
    pending, _trace, receipt = _open_mint(authority, outcome=True, fullmove=701,
                                        frame_id="continuous-contract:pending")
    before = authority.continuation_manifest()
    restored = module.NativeProspectiveAuthorityV2.loads(authority.dumps())
    assert restored.continuation_manifest() == before
    assert restored.pending_event.pending_token == pending.pending_token
    authority.consume(receipt)
    restored.consume(receipt)
    assert restored.continuation_manifest() == authority.continuation_manifest()


def _continuous_legacy_parent_request(authority):
    first = _event(authority, 0)
    _birth(authority, first)
    _event(authority, 1, outcome=False)
    for index in range(2, 5):
        _event(authority, index)
    assert len(authority._pending_request_ids()) == 1
    return authority.deferred_requests[authority._pending_request_ids()[0]]


def test_late_second_counterexample_rejects_residual_before_allocation(authority):
    request = _continuous_legacy_parent_request(authority)
    proposed = authority._deferred_request_plan(
        request.request_id, attempt_ordinal=0, target_generation=1,
        reserved_members=set(authority._reserved_member_pairs),
    ).consumption
    assert proposed.child_cell_id is not None
    rejected_members = proposed.selected_members
    _consume(authority, outcome=False, fullmove=710, frame_id="continuous:late-C2",
             fen_template=ADVERSARIAL[AvailabilityState.AVAILABLE])
    assert rejected_members[1] not in authority._continuous_deferred_eligible_ids(
        request, frontier=authority.next_expected_ordinal - 1)
    authority.settle_pending_structural_requests()
    assert all(state.hypothesis.members != rejected_members for state in authority.states.values())
    for index in range(11, 15):
        _event(authority, index)
    assert not any(state.hypothesis.members == rejected_members and state.prospectively_certified
                   for state in authority.states.values())
    authority.verify_full_history_boundary("late-C2 rejection and later positives")
    restored = module.NativeProspectiveAuthorityV2.loads(authority.dumps())
    assert restored.continuation_manifest() == authority.continuation_manifest()


def test_deferred_child_and_grandchild_freeze_all_typed_roles_and_source(authority):
    request = _continuous_legacy_parent_request(authority)
    authority.settle_pending_structural_requests()
    child_id = authority.request_consumptions[request.request_id].child_cell_id
    assert child_id is not None
    child = authority.states[child_id]
    assert child.hypothesis.semantic_source_identity
    assert child.support == child.contradictions == 0 and not child.prospectively_certified
    assert child.hypothesis.hypothesis_birth_digest is None
    _consume(authority, outcome=False, fullmove=720, frame_id="continuous:child-C1",
             fen_template=ADVERSARIAL[AvailabilityState.AVAILABLE])
    for index in range(21, 25):
        latest = _event(authority, index)
    authority.settle_pending_structural_requests()
    grandchildren = [state for state in authority.states.values()
                     if state.hypothesis.lineage_parent_id == child_id]
    assert grandchildren
    grandchild = grandchildren[0]
    assert grandchild.support == 0 and not grandchild.prospectively_certified
    assert grandchild.hypothesis.semantic_source_identity == child.hypothesis.semantic_source_identity
    assert set(child.hypothesis.semantic_member_roles).issubset(grandchild.hypothesis.semantic_member_roles)
    added = grandchild.hypothesis.members[1]
    assert added not in dict(child.hypothesis.semantic_member_roles)
    changed_role = replace(latest.trace, terminal_signals=tuple(
        replace(signal, role="DIFFERENT_TYPED_ROLE") if signal.identity == added else signal
        for signal in latest.trace.terminal_signals))
    assert grandchild.hypothesis.cell_id in authority._graph_measure(latest.trace)["commitment"]
    assert grandchild.hypothesis.cell_id not in authority._graph_measure(changed_role)["commitment"]
    changed_source = replace(latest.trace, source_state_identity="another-policy")
    assert child_id not in authority._graph_measure(changed_source)["commitment"]
    assert grandchild.hypothesis.cell_id not in authority._graph_measure(changed_source)["commitment"]
    authority.verify_full_history_boundary("typed recursive residuals")
    restored = module.NativeProspectiveAuthorityV2.loads(authority.dumps())
    assert restored.continuation_manifest() == authority.continuation_manifest()


def test_all_refuted_residuals_use_normal_empty_consumption(authority, monkeypatch):
    """The native gate's all-refuted input is ordinary learner rejection.

    The preceding late-C2 test supplies a real accepted counterexample.  This
    unit case supplies that terminal fact for every residual to exercise the
    empty-set plumbing without inventing additional chess positions.
    """
    request = _continuous_legacy_parent_request(authority)
    original = authority._continuous_deferred_contract
    def all_refuted(*args, **kwargs):
        source, roles, support, contradictions = original(*args, **kwargs)
        return source, roles, support, max(1, contradictions)
    monkeypatch.setattr(authority, "_continuous_deferred_contract", all_refuted)
    before_ids = set(authority.states)
    authority.settle_pending_structural_requests()
    consumption = authority.request_consumptions[request.request_id]
    assert consumption.disposition == "REJECTED_EMPTY_ELIGIBILITY"
    assert consumption.child_cell_id is None
    assert consumption.selected_members == ()
    assert consumption.genome_call_count == 1
    assert set(authority.states) == before_ids
