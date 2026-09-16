"""Synthetic nomination checks; fixture seeds are outside the study cohort."""
import copy
import json
import pickle

import run_owner_trial_learning as control
import run_owner_action_contrast as pilot
from recon_lite_hector.learning.owner_action_contrast import (
    ActionContrastEvidence, ActionContrastLearningTrialOwnerDevelopment,
)
from test_owner_fresh_start import step


def create(seed=98):
    prior = control.create_actor(seed, 'learning-trial')
    return ActionContrastLearningTrialOwnerDevelopment.create(
        schema=control.BooleanEnvironment.schema, state_coordinates=(0, 1, 2, 3),
        seed=seed, config=prior.config, search=prior.birth_search_config,
        development=prior.development_config, limits=prior.ownership_limits)


def fill(values):
    evidence = ActionContrastEvidence()
    for side, action, residual in values:
        for _ in range(4):
            evidence.add(side, action, residual)
    return evidence


def test_common_residual_shift_does_not_nominate_a_route():
    evidence = fill([(False, 'act-a', -1), (True, 'act-a', 1),
                     (False, 'act-b', -1), (True, 'act-b', 1)])
    assert evidence.score(4) == 0
    assert evidence.score(5) is None


def test_changed_action_advantage_scores_but_sparse_cells_abstain():
    evidence = fill([(False, 'act-a', 1), (True, 'act-a', -1),
                     (False, 'act-b', -1), (True, 'act-b', 1)])
    assert evidence.score(4) == 16
    evidence.counts[True, 'act-b'] = 3
    assert evidence.score(4) is None


def test_actual_action_only_and_checkpoint_roundtrip():
    actor = create()
    control.verify_initial_pair([control.create_actor(98, 'learning-trial'), actor])
    for row in range(16):
        step(actor, row)
    counts = sum(sum(stat.counts.values()) for stat in actor.action_contrast_evidence[0].values())
    assert counts == len(actor.owner_candidates) * 16
    clone = pickle.loads(pickle.dumps(actor, protocol=5))
    assert actor.action_contrast_evidence == clone.action_contrast_evidence
    for row in range(16):
        assert step(actor, row) == step(clone, row)
    assert actor.action_contrast_evidence == clone.action_contrast_evidence


def test_original_learning_trial_remains_exactly_unchanged():
    actor = control.create_actor(99, 'learning-trial')
    twin = copy.deepcopy(actor)
    for row in range(32):
        assert step(actor, row % 16) == step(twin, row % 16)
    control.verify_same_state(actor, twin)


def test_one_sealed_block_and_report_assembly_for_each_arm(tmp_path):
    actors = [pilot.actor_for(98, role) for role in pilot.ROLES]
    control.verify_initial_pair(actors)
    order = control.schedule(98)[:64]
    for role, actor in zip(pilot.ROLES, actors):
        directory = tmp_path / role
        directory.mkdir()
        previous = control.save_actor(actor, directory/'start.pkl.gz')
        actor, _, evaluation = control.train_block(actor, order, directory/'block', previous)
        records = [json.loads(line)
                   for line in (directory/'block/training.jsonl').read_text().splitlines()]
        control.verify_birth_evidence(actor, records, {})
        control.verify_trials(actor, records, {})
        pilot.verify_action_contrast(actor, records, {})
        assert 0 <= evaluation['correct'] <= 16
        history = pilot.trial_history(actor)
        if role == 'current':
            assert history == []
        else:
            assert isinstance(history, list)
