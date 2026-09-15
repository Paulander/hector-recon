"""Small runner checks; no full pilot is executed by the test suite."""
from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts/autogrowth'))
import run_owner_nomination as lab


def small_source():
    actor=lab.RecursiveDevelopment(seed=31,config=lab.DevelopmentConfig(max_conditions=4),
                                 recursive_config=lab.RecursiveConfig(role='flat',prefix=8))
    for event in range(8):
        env=lab.BooleanEnvironment(lab.ROWS[event])
        action=actor.act(env,event_id=event,learn=True)
        actor.observe(lab.Feedback(event,action,env.outcome()))
    return actor


def test_both_roles_inherit_one_source_and_differ_only_in_permission_to_split():
    source=small_source()
    actors=[lab.AdaptiveOwnerDevelopment.from_actor(source,state_coordinates=(0,1,2,3),
                 development=lab.OwnerDevelopmentConfig(split_enabled=flag)) for flag in (False,True)]
    for actor in actors: lab.verify_conversion(source,actor)
    lab.verify_pair(*actors)
    assert lab.evaluate(actors[0])==lab.evaluate(source)==lab.evaluate(actors[1])


def test_one_completed_block_seals_actions_updates_and_restored_evaluation(tmp_path):
    source=small_source()
    actor=lab.AdaptiveOwnerDevelopment.from_actor(source,state_coordinates=(0,1,2,3),
             development=lab.OwnerDevelopmentConfig(develop_every=8,min_support=2))
    previous=lab.save_actor(actor,tmp_path/'start.pkl.gz')
    order=list(range(16))
    restored,checkpoint,result=lab.train_block(actor,order,tmp_path/'block',previous,do_evaluate=True)
    assert restored.completed==24 and checkpoint and result==lab.evaluate(restored)
    lab.verify_block(tmp_path/'block',order,8,previous)
    with pytest.raises(FileExistsError):
        lab.train_block(restored,order,tmp_path/'block',checkpoint,do_evaluate=True)
    path=tmp_path/'block'/'training.jsonl'
    path.write_bytes(path.read_bytes()+b'{}\n')
    with pytest.raises(AssertionError): lab.verify_block(tmp_path/'block',order,8,previous)


def test_submitted_action_survives_a_failure_while_applying_feedback(tmp_path,monkeypatch):
    actor=small_source()
    def stop(_feedback):
        raise RuntimeError('fixture interrupts after actual action and reward')
    monkeypatch.setattr(actor,'observe',stop)
    with pytest.raises(RuntimeError,match='fixture interrupts'):
        lab.train_block(actor,[0,1],tmp_path/'partial','prior',do_evaluate=True)
    submitted=[json.loads(s) for s in (tmp_path/'partial'/'submissions.jsonl').read_text().splitlines()]
    assert len(submitted)==1 and submitted[0]['event']==8 and submitted[0]['action']
    assert not (tmp_path/'partial'/'complete.json').exists()
    assert (tmp_path/'partial'/'progress.jsonl').read_bytes()==b''


def test_fixed_schedule_has_exact_counts_and_no_phase_label_sent_to_actor():
    for seed in lab.SEEDS:
        prefix,continuation=lab.schedule(seed)
        assert len(prefix)==128 and len(continuation)==256
        assert all(not lab.ROWS[index][2] for index in prefix)
        for offset in range(0,256,64):
            unit=continuation[offset:offset+64]
            assert sum(lab.ROWS[index][2] for index in unit)==(56 if offset<128 else 8)
