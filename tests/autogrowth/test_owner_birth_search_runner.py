"""Exercise real action recording/restoration and reject damaged evidence."""
import json

import pytest

import run_owner_birth_search as runner
from recon_lite_hector.learning.recursive_context import RecursiveDevelopment, RecursiveConfig
from recon_lite_hector.learning.terminal_development import DevelopmentConfig


def test_real_block_preserves_candidate_observations_and_detects_tampering(tmp_path):
    source = RecursiveDevelopment(seed=21,
        config=DevelopmentConfig(max_conditions=4, grace_episodes=10000),
        recursive_config=RecursiveConfig(prefix=1000))
    port=runner.BooleanEnvironment(runner.ROWS[0])
    action=source.act(port,event_id=0,learn=True)
    source.observe(runner.Feedback(0,action,port.outcome()))
    actor=runner.BirthSearchOwnerDevelopment.from_actor(source,
        state_coordinates=(0,1,2,3),search_seed=21,
        limits=runner.OwnershipLimits(max_parameters=64,max_definitions=256,max_physical_nodes=2048))
    previous=runner.save_actor(actor,tmp_path/'start.pkl.gz')
    order=[0,1,2,3]
    actor,checkpoint,result=runner.train_block(actor,order,tmp_path/'block',previous)
    assert actor.completed==5 and len(result['rows'])==16
    records=[json.loads(s) for s in (tmp_path/'block/training.jsonl').read_text().splitlines()]
    assert all(len(r['birth_candidate_values'])==24 for r in records)
    assert all(e.n0+e.n1==4 for e in actor.birth_evidence[0])
    assert runner.evaluate(actor)==result
    target=tmp_path/'block/credited/000001.json'
    target.write_bytes(target.read_bytes()+b' ')
    with pytest.raises(AssertionError): runner.prior.verify_block(tmp_path/'block',order,1,previous)
