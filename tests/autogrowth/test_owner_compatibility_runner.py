"""Paired conversion, accounting and sealed evidence for the compatibility run."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts/autogrowth'))

import run_owner_compatibility as lab
from test_owner_nomination_runner import small_source


def test_only_compatibility_flag_differs_at_conversion_and_control_matches():
    source = small_source()
    control = lab.CompatibleOwnerDevelopment.from_actor(source, state_coordinates=(0,1,2,3),
                                                       compatibility=lab.CompatibilityConfig(enabled=False))
    candidate = lab.CompatibleOwnerDevelopment.from_actor(source, state_coordinates=(0,1,2,3))
    candidate.compatibility_config = replace(candidate.compatibility_config, enabled=False)
    lab.prior.same_state(control,candidate)
    original = lab.AdaptiveOwnerDevelopment.from_actor(source,state_coordinates=(0,1,2,3))
    lab.same_control(control,original)


def test_comparison_retains_longer_schedule_without_repeating_the_prefix():
    for seed in lab.SEEDS:
        prefix, order = lab.prior.schedule(seed)
        assert len(prefix)==640 and len(order)==1280
        assert len(lab.ROLES)==2
    assert lab.COUNTS == dict(training=5120,evaluation=1280,verification_actions=1280,blocks=80,checkpoints=84)


def test_new_metadata_survives_the_original_immutable_recorder(tmp_path):
    actor = lab.CompatibleOwnerDevelopment.from_actor(small_source(),state_coordinates=(0,1,2,3),
                       development=lab.OwnerDevelopmentConfig(split_enabled=False,develop_every=8))
    restored, _, evaluation = lab.prior.train_block(actor,list(range(16)),tmp_path/'block',
                                                    'start',do_evaluate=True)
    assert restored.birth_proposals and evaluation==lab.evaluate(restored)
    original = copy.deepcopy(restored)
    lab.prior.verify_block(tmp_path/'block',list(range(16)),8,'start')
    lab.prior.same_state(restored,original)
    manifest=json.loads((tmp_path/'block/complete.json').read_text())
    assert len([p for p in manifest['files'] if p.startswith('submitted/')])==16
