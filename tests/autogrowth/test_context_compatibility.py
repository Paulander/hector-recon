"""Logical proof, conservative bounds and unchanged actual-action learning."""
import copy
from dataclasses import replace
import itertools
import pickle
from pathlib import Path
import sys
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts/autogrowth'))

from recon_lite_hector.learning.compatible_owner import CompatibleOwnerDevelopment
from recon_lite_hector.learning.context_compatibility import CompatibilityConfig, check_compatibility
from recon_lite_hector.learning.owner_development import AdaptiveOwnerDevelopment, OwnerDevelopmentConfig
from recon_lite_hector.learning.recursive_context import Expression, TRUE, combine, negate
from recon_lite_hector.learning.terminal_development import Coordinate
from test_context_decision import Port, ROWS, planted, scores
from test_owner_development import step


def read(i, value=True):
    return Expression('read', atom=(i, value))


def learner(enabled=True, **kwargs):
    return CompatibleOwnerDevelopment.from_actor(planted(), state_coordinates=(0,1,2),
        compatibility=CompatibilityConfig(enabled=enabled, **kwargs),
        development=OwnerDevelopmentConfig(split_enabled=False, develop_every=8))


def test_contradiction_and_or_alternative_are_distinguished():
    context = read(0)
    assert check_compatibility(context, read(0, False), Port.schema).status == 'impossible'
    alternative = combine('or', (read(0, False), read(1)))
    assert check_compatibility(context, alternative, Port.schema).status == 'compatible'
    assert check_compatibility(context, combine('and', (read(0, False), read(1))), Port.schema).status == 'impossible'


def test_exactly_one_is_not_parity_and_nested_negation_keeps_semantics():
    context = combine('and', (read(0), read(1), read(2)))
    candidate = combine('xor', (read(0), read(1), read(2)))
    assert check_compatibility(context, candidate, Port.schema).status == 'impossible'
    assert check_compatibility(context, negate(candidate), Port.schema).status == 'compatible'
    assert check_compatibility(negate(read(0)), read(0), Port.schema).status == 'impossible'


def test_declared_integer_domains_and_reader_types_are_respected():
    schema = (Coordinate('distance', (2,4,6)),)
    assert check_compatibility(read(0,2), read(0,4), schema).status == 'impossible'
    assert check_compatibility(negate(read(0,2)), read(0,6), schema).status == 'compatible'
    assert check_compatibility(TRUE, read(0,True), (Coordinate('integer', (0,1)),)).status == 'unknown'


def test_bounded_inconclusive_checks_keep_possible_and_impossible_trials_eligible():
    for budget in (CompatibilityConfig(max_nodes=1), CompatibilityConfig(max_assignments=1),
                   CompatibilityConfig(max_operations=1)):
        assert check_compatibility(read(0), read(0,False), Port.schema, budget).status == 'unknown'
    # This witness requires no empirical observation, count or reward.
    rare = combine('and', tuple(read(i) for i in range(4)))
    assert check_compatibility(TRUE, rare, Port.schema).status == 'compatible'


def test_proofs_match_an_independent_truth_interpreter_over_composed_grammar():
    def truth(e, row):
        if e.operator == 'true': return True
        if e.operator == 'read': return row[e.atom[0]] == e.atom[1]
        children = [truth(c,row) for c in e.children]
        if e.operator == 'and': return all(children)
        if e.operator == 'or': return any(children)
        return children.count(True) == 1
    atoms = [read(0), read(0,False), read(1), TRUE]
    expressions = atoms + [combine(op, children) for op in ('and','or','xor')
                           for children in itertools.combinations(atoms, 3)]
    for context, candidate in itertools.product(expressions, repeat=2):
        possible = any(truth(context,row) and truth(candidate,row)
                       for row in itertools.product((False,True), repeat=2))
        assert check_compatibility(context,candidate,Port.schema).status == ('compatible' if possible else 'impossible')


def test_rejection_cache_is_bounded_scoped_and_checkpointed():
    actor = learner(cache_entries=1)
    left, right = actor.split_decision(0, read(0))
    assert actor._compatibility(right, read(0,False))[0].status == 'impossible'
    assert actor._compatibility(right, read(0,False))[1]
    assert actor._compatibility(left, read(0,False))[0].status == 'compatible'
    restored = pickle.loads(pickle.dumps(actor))
    assert restored._compatibility(right, read(0,False))[1]
    # Same owner identity with changed constraints must not reuse the proof.
    restored.leaves[right] = replace(restored.leaves[right], path=TRUE)
    assert restored._compatibility(right, read(0,False))[0].status == 'compatible'
    actor.schema = (Coordinate('revised-schema', (False,True)), *actor.schema[1:])
    assert not actor._compatibility(right, read(0,False))[1]
    assert len(actor.rejection_cache) == 1


def forced_reader(actor, value):
    actor.proposal_rng = Mock()
    actor.proposal_rng.randint.return_value = 1
    actor.proposal_rng.sample.return_value = [0]
    actor.proposal_rng.choice.return_value = value


def test_rejected_birth_consumes_one_proposal_without_allocating_or_retrying():
    actor = learner()
    _, owner = actor.split_decision(0, read(0))
    forced_reader(actor, False)
    before = copy.deepcopy((actor.conditions, actor.leaves, actor.base_expressions,
                            actor.owner_seen, actor.next_condition, vars(actor.graph)))
    assert actor._birth_local(owner) is None
    assert (actor.conditions, actor.leaves, actor.base_expressions,
            actor.owner_seen, actor.next_condition, vars(actor.graph)) == before
    assert actor.proposal_rng.sample.call_count == 1
    assert actor.proposal_rng.choice.call_count == 1
    assert actor.birth_proposals[-1]['outcome'] == 'contradiction'
    assert actor._birth_local(owner) is None
    assert actor.birth_proposals[-1]['cached']
    assert actor.proposal_rng.sample.call_count == 2


def test_unknown_and_state_only_births_are_installed_without_semantic_merging():
    actor = learner(max_nodes=1)
    _, owner = actor.split_decision(0, read(0))
    forced_reader(actor, False)
    cid = actor._birth_local(owner)
    assert cid in actor.conditions and actor.birth_proposals[-1]['verdict']['status'] == 'unknown'
    possible = learner()
    _, owner = possible.split_decision(0, read(0))
    forced_reader(possible, True)
    cid = possible._birth_local(owner)
    assert cid in possible.conditions  # Already entailed, but not contradictory.


def test_disabled_extension_matches_original_through_growth_and_actual_credit():
    # Full-state equality, including RNGs and physical graph; only new observer
    # metadata is removed. Tests the copied proposal law against its control.
    from run_owner_nomination_fivefold import same_state
    original = AdaptiveOwnerDevelopment.from_actor(planted(), state_coordinates=(0,1,2),
        development=OwnerDevelopmentConfig(split_enabled=False, develop_every=8))
    actor = learner(enabled=False)
    for event in range(32):
        assert step(actor,event,ROWS[event%8]) == step(original,event,ROWS[event%8])
    stripped = copy.deepcopy(actor)
    for name in ('compatibility_config', 'rejection_cache', 'birth_proposals'):
        delattr(stripped,name)
    stripped.__class__ = AdaptiveOwnerDevelopment
    same_state(stripped,original)


def test_active_checker_preserves_terminal_boundary_and_reload_trajectory():
    actor = learner()
    actor.split_decision(0,read(0))
    for event in range(8): step(actor,event,ROWS[event%8])
    restored = pickle.loads(pickle.dumps(actor))
    for event in range(8,32):
        assert step(actor,event,ROWS[event%8]) == step(restored,event,ROWS[event%8])
    assert actor.conditions == restored.conditions
    assert actor.rejection_cache == restored.rejection_cache
    assert actor.proposal_rng.getstate() == restored.proposal_rng.getstate()
    assert [scores(actor,row) for row in ROWS] == [scores(restored,row) for row in ROWS]
