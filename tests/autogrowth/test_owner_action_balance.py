"""Fixture-seed checks of graph-owned routing and actual-action coverage."""
from dataclasses import replace
import json
import pickle

import run_owner_action_contrast as previous
import run_owner_action_balance as pilot
from recon_lite_hector.learning.owner_action_balance import OwnerBalancedActionContrastDevelopment
from recon_lite_hector.learning.recursive_context import Expression
from test_owner_fresh_start import step


def create(seed=98, exploration=None):
    prior = previous.actor_for(seed, 'action-contrast')
    return OwnerBalancedActionContrastDevelopment.create(
        schema=previous.prior.BooleanEnvironment.schema,
        state_coordinates=(0, 1, 2, 3), seed=seed,
        config=prior.config if exploration is None else replace(prior.config, exploration=exploration),
        search=prior.birth_search_config, development=prior.development_config,
        limits=prior.ownership_limits)


def test_no_exploration_preserves_graph_choice_and_credit():
    ordinary = previous.actor_for(98, 'action-contrast')
    ordinary.config = replace(ordinary.config, exploration=0)
    balanced = create(exploration=0)
    for row in range(32):
        assert step(ordinary, row % 16) == step(balanced, row % 16)
    assert ordinary.conditions == balanced.conditions
    assert ordinary.leaves == balanced.leaves
    assert ordinary.owner_evidence == balanced.owner_evidence
    assert ordinary.action_contrast_evidence == balanced.action_contrast_evidence


def test_existing_stochastic_signal_targets_less_sampled_action():
    actor = create(exploration=1)
    actor.action_visits[0] = {'act-b': 10}
    action, _ = step(actor, 0)
    assert action == 'act-a'
    assert actor.exploration_owner is None
    assert actor.action_visits[0] == {'act-b': 10, 'act-a': 1}


def test_local_counts_follow_actual_owner_and_survive_checkpoint():
    actor = create(exploration=1)
    children = actor.nominate_split(0, Expression('read', atom=(0, True)))
    assert all(actor.action_visits[child] == {} for child in children)
    for row in range(16):
        step(actor, row)
    assert sum(sum(c.values()) for c in actor.action_visits.values()) == 16
    restored = pickle.loads(pickle.dumps(actor, protocol=5))
    assert restored.action_visits == actor.action_visits
    for row in range(16):
        assert step(actor, row) == step(restored, row)
    assert restored.action_visits == actor.action_visits


def test_sealed_block_and_report_assembly_for_all_arms(tmp_path):
    actors = [pilot.actor_for(98, role) for role in pilot.ROLES]
    previous.prior.verify_initial_pair(actors)
    order = previous.prior.schedule(98)[:64]
    for role, actor in zip(pilot.ROLES, actors):
        directory = tmp_path/role
        directory.mkdir()
        previous_hash = previous.save_actor(actor, directory/'start.pkl.gz')
        actor, _, evaluation = previous.prior.train_block(
            actor, order, directory/'block', previous_hash)
        records = [json.loads(line)
                   for line in (directory/'block/training.jsonl').read_text().splitlines()]
        previous.prior.verify_birth_evidence(actor, records, {})
        previous.prior.verify_trials(actor, records, {})
        previous.verify_action_contrast(actor, records, {})
        assert isinstance(previous.trial_history(actor), list)
        assert 0 <= evaluation['correct'] <= 16
        if role == 'owner-balance':
            expected = {}
            for row in records:
                cell = expected.setdefault(row['owner'], {})
                cell[row['action']] = cell.get(row['action'], 0) + 1
            assert all(actual == expected.get(owner, {})
                       for owner, actual in actor.action_visits.items())
