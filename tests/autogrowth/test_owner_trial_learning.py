"""Actual-action lifecycle fixtures; seeds98/99, never the study cohort."""
import copy
from dataclasses import replace
import json
import pickle

import pytest

import run_owner_trial_learning as runner
import run_owner_split_trial as old
from recon_lite_hector.learning.owner_trial_learning import LearningTrialOwnerDevelopment
from recon_lite_hector.learning.recursive_context import Expression
from test_owner_fresh_start import step
from test_owner_split_trial import add_action_feature


def fixed_actor(monkeypatch, exploration=0):
    # Isolate trial timing from random feature growth, leaving the normal64
    # exposure clock intact. Study actors never receive this fixture patch.
    monkeypatch.setattr(LearningTrialOwnerDevelopment,'_run_development',lambda self,owner:None)
    a = runner.create_actor(99,'learning-trial')
    a.config = replace(a.config,exploration=exploration)
    return a


def test_unvisited_child_cannot_skip_readiness_or_survive_lifetime(monkeypatch):
    a = fixed_actor(monkeypatch)
    children = a.nominate_split(0,Expression('read',atom=(0,True)))
    for i in range(1535):
        step(a,0)
        if i in (255,511):
            assert a.split_trials[0].state.name=='TRIAL'
            assert not a.assessment_clocks[(0,0)].reviews
    assert min(a.split_trials[0].child_exposures.values())==0
    step(a,0)
    t = a.split_trial_history[0]
    assert t.state.name=='PRUNED' and len(t.outcomes)==1536
    assert t.resolution['reason']=='unproven at lifetime budget'
    assert t.resolution['assessment_assigned']==0
    assert set(a.leaves)=={0} and len(t.retired)==2
    assert set(t.child_exposures)==set(children)


def test_assessment_is_prospective_and_real_learning_can_earn_acceptance(monkeypatch):
    a = fixed_actor(monkeypatch,exploration=.25); add_action_feature(a)
    children = a.nominate_split(0,Expression('read',atom=(0,True)))
    while a.split_trials and a.completed<1536:
        step(a,0 if a.completed%2==0 else 12)
    t = a.split_trial_history[0]; clock = a.assessment_clocks[(0,0)]
    assert clock.start>256 and min(clock.learning_counts.values())==64
    assert any(r.reward<0 for r in t.outcomes[:clock.start])
    assert t.state.name=='MATURE',t.resolution
    assert t.resolution['assessment_assigned'] in (256,512)
    assert len(t.outcomes)==clock.start+t.resolution['assessment_assigned']
    assessed = t.outcomes[clock.start:]
    groups = [[r.reward for r in assessed if r.enabled==flag] for flag in (False,True)]
    assert t.resolution['mean_reward_gain']==sum(groups[1])/len(groups[1])-sum(groups[0])/len(groups[0])
    assert set(a.leaves)==set(children)


def test_first_unproven_review_retains_candidate_history_then_second_retires(monkeypatch):
    a = fixed_actor(monkeypatch)
    children = a.nominate_split(0,Expression('read',atom=(3,True)))
    while not a.assessment_clocks[(0,0)].reviews:
        assert a.completed<1536
        step(a,a.completed%2)
    t = a.split_trials[0]; prefix = copy.deepcopy(t.outcomes)
    inherited = copy.deepcopy(t.inherited)
    assert t.state.name=='PROBATION' and not a.split_trial_history
    assert not a.assessment_clocks[(0,0)].reviews[0]['accepted']
    assert t.children==children and t.born==0
    restored = pickle.loads(pickle.dumps(a,protocol=5))
    frozen = pickle.dumps(restored,protocol=5)
    runner.evaluate(restored)
    assert pickle.dumps(restored,protocol=5)==frozen
    while a.split_trials:
        assert a.completed<1536
        row = a.completed%2
        assert step(a,row)==step(restored,row)
    runner.verify_same_state(a,restored)
    t = a.split_trial_history[0]; clock = a.assessment_clocks[(0,0)]
    assert t.outcomes[:len(prefix)]==prefix and t.inherited==inherited
    assert t.state.name=='PRUNED' and len(clock.reviews)==2
    assert t.resolution['assessment_assigned']==512
    assert t.resolution['mean_reward_gain']==0
    assert t.resolution['reason']=='unproven after two assessments'


def test_existing_controls_are_identical_from_fresh_state():
    actors = [runner.create_actor(98,role) for role in runner.ROLES]
    runner.verify_initial_pair(actors)
    for role,a in zip(runner.ROLES,actors):
        if role=='learning-trial': continue
        b = old.create_actor(98,role)
        runner.verify_same_state(a,b)
        for row in range(16): assert step(a,row)==step(b,row)
        runner.verify_same_state(a,b)


def test_immutable_actual_records_reconstruct_readiness_and_detect_clock_tampering(tmp_path,monkeypatch):
    a = fixed_actor(monkeypatch)
    a.nominate_split(0,Expression('read',atom=(3,True)))
    previous = runner.save_actor(a,tmp_path/'start.pkl.gz')
    evidence = {}
    for offset in range(0,640,64):
        block = tmp_path/f'block-{offset}'
        a,previous,result = runner.train_block(a,[0,1]*32,block,previous)
        records = [json.loads(s) for s in (block/'training.jsonl').read_text().splitlines()]
        runner.verify_trials(a,records,evidence)
    assert a.assessment_clocks[(0,0)].reviews
    a.assessment_clocks[(0,0)].start += 1
    with pytest.raises(AssertionError): runner.verify_trials(a,[],evidence)
