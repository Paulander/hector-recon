"""Nomination sees actual outcomes; no fixture label or alternate reward is read."""
from dataclasses import replace
import copy
import pickle

import pytest

from recon_lite_chess.coach.interface import Feedback
from recon_lite_hector.learning.owner_development import AdaptiveOwnerDevelopment, OwnerDevelopmentConfig
from recon_lite_hector.learning.context_decision import OwnershipLimits
from recon_lite_hector.learning.recursive_context import Expression
from test_context_decision import Port, ROWS, planted, owned, scores, weight_snapshot


def adaptive(*, config=None, source=None, limits=None):
    return AdaptiveOwnerDevelopment.from_actor(
        source or planted(), state_coordinates=(0, 1, 2),
        development=config or OwnerDevelopmentConfig(), limits=limits)


def step(actor, event, row):
    port = Port(row)
    action = actor.act(port, event_id=event, learn=True)
    prediction = actor.pending[-1][2]
    observations = actor.candidate_pending
    reward = port.outcome()
    actor.observe(Feedback(event, action, reward))
    return action, prediction, observations, reward


def test_candidate_probing_changes_neither_choices_nor_the_original_weight_update():
    source = planted()
    source.config = replace(source.config, exploration=.25)
    control = owned(source)
    learner = adaptive(source=source, config=OwnerDevelopmentConfig(develop_every=1000))
    assert learner.owner_candidates
    for expression in learner.owner_candidates:
        learner._check_route(expression)
    for event in range(24):
        actions = []
        for actor in (control, learner):
            port = Port(ROWS[event % len(ROWS)])
            action = actor.act(port, event_id=event, learn=True)
            actions.append(action)
            actor.observe(Feedback(event, action, port.outcome()))
        assert actions[0] == actions[1]
        assert control.conditions == learner.conditions
        assert control.rng.getstate() == learner.rng.getstate()
    assert all(e.n0 + e.n1 == 24 for e in learner.owner_evidence[0].values())
    assert not learner.development_history


def test_residual_statistics_bind_to_actual_preupdate_prediction_and_invalid_feedback_is_neutral():
    actor = adaptive(config=OwnerDevelopmentConfig(develop_every=1000))
    port = Port(ROWS[1])
    action = actor.act(port, event_id=3, learn=True)
    before = copy.deepcopy(actor.conditions)
    pending = actor.candidate_pending
    for feedback in (Feedback(4, action, 1), Feedback(3, 'wrong', 1), Feedback(3, action, float('nan'))):
        with pytest.raises(ValueError):
            actor.observe(feedback)
        assert actor.conditions == before and actor.owner_evidence == {0: {}}
        assert actor.candidate_pending == pending
    with pytest.raises(RuntimeError, match='feedback'):
        pickle.dumps(actor)
    actor.observe(Feedback(3, action, port.outcome()))
    residual = port.outcome() - pending[3]
    for index, enabled in enumerate(pending[4]):
        evidence = actor.owner_evidence[0][index]
        assert (evidence.n0, evidence.n1) == ((0, 1) if enabled else (1, 0))
        assert evidence.sum0 + evidence.sum1 == residual


def test_experience_nominates_a_split_and_keeps_parent_evidence_as_ancestry():
    # The owner learns only from the ordinary port + actual outcome interface.
    actor = adaptive(config=OwnerDevelopmentConfig(develop_every=8, min_support=2))
    for event in range(8):
        step(actor, event, ROWS[event])
    event = actor.development_history[0]
    assert event['split'] is not None and len(actor.leaves) == 2
    selected = event['split']
    evidence = selected['evidence']
    assert min(evidence.n0, evidence.n1) >= 2 and evidence.score(2) == selected['score']
    assert actor.owner_candidates[selected['candidate']] == selected['route']
    assert actor.owner_evidence[0][selected['candidate']] == evidence
    for owner in selected['children']:
        assert actor.owner_evidence[owner] == {} and actor.owner_visits[owner] == 0
    assert all(e.n0 + e.n1 == 8 for e in actor.owner_evidence[0].values())
    actor.validate_ownership()


def test_only_the_visited_owner_develops_and_receives_candidate_history():
    actor = adaptive(config=OwnerDevelopmentConfig(split_enabled=False, develop_every=2))
    left, right = actor.split_decision(0, Expression('read', atom=(0, True)))
    inactive = weight_snapshot(actor, left)
    initial_scores = [scores(actor, row) for row in ROWS if not row[0]]
    for event in range(8):
        step(actor, event, (True, bool(event % 2), bool(event % 3)))
    assert weight_snapshot(actor, left) == inactive
    assert [scores(actor, row) for row in ROWS if not row[0]] == initial_scores
    assert actor.owner_visits[left] == 0 and actor.owner_evidence[left] == {}
    assert all(e['owner'] == right for e in actor.development_history)


def test_local_retirement_preserves_records_and_other_owner_scores():
    actor = adaptive(config=OwnerDevelopmentConfig(split_enabled=False, develop_every=2))
    left, right = actor.split_decision(0, Expression('read', atom=(0, True)))
    actor.config = replace(actor.config, grace_episodes=2)
    doomed = next(cid for cid in actor.leaves[right].contributions
                  if actor.base_expressions[cid] == Expression('read', atom=(3, True)))
    actor.conditions[doomed].weight.fast = actor.conditions[doomed].weight.slow = 0.0
    remembered = actor.base_expressions[doomed]
    inactive = weight_snapshot(actor, left)
    # Chosen a stays a across these two unsuccessful moves; b cue remains weak.
    step(actor, 0, (True, False, False))
    step(actor, 1, (True, False, False))
    assert doomed not in actor.conditions
    assert any(record['condition'].identity == doomed for record in actor.retirement_history)
    assert remembered in actor.owner_seen[right]
    assert weight_snapshot(actor, left) == inactive
    assert actor.leaves[right].bias_id in actor.conditions


def test_budget_exhaustion_keeps_weight_learning_and_records_rejected_nominees():
    actor = adaptive(config=OwnerDevelopmentConfig(develop_every=8, min_support=2),
                     limits=OwnershipLimits(max_parameters=4))
    before = copy.deepcopy(actor.conditions)
    for event in range(16):
        step(actor, event, ROWS[event % 8])
    assert len(actor.leaves) == 1 and actor.conditions != before
    assert actor.development_history[0]['budget_rejections']
    assert all(e['birth'] is None for e in actor.development_history)
    assert all(e.n0 + e.n1 == 16 for e in actor.owner_evidence[0].values())


def test_checkpoint_restores_nomination_lifecycle_and_branch_choices():
    actor = adaptive(config=OwnerDevelopmentConfig(develop_every=8, min_support=2))
    for event in range(8):
        step(actor, event, ROWS[event])
    restored = pickle.loads(pickle.dumps(actor))
    for event in range(8, 32):
        assert step(actor, event, ROWS[event % 8]) == step(restored, event, ROWS[event % 8])
        for name in ('conditions', 'leaves', 'owner_visits', 'owner_evidence',
                     'owner_seen', 'development_history', 'retirement_history'):
            assert getattr(actor, name) == getattr(restored, name)
        assert actor.proposal_rng.getstate() == restored.proposal_rng.getstate()
    restored.validate_ownership()
    assert [scores(actor, row) for row in ROWS] == [scores(restored, row) for row in ROWS]
