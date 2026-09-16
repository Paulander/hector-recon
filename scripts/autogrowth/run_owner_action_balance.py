"""Thin fresh-seed configuration of the sealed owner-action pilot runner."""
import argparse
import json
from pathlib import Path

import run_owner_action_contrast as base
from run_owner_nomination import ROOT, digest, load_actor
from recon_lite_hector.learning.owner_action_balance import OwnerBalancedActionContrastDevelopment


SEEDS = (33, 34, 35)
ROLES = ('current', 'action-contrast', 'owner-balance')
PROTOCOL = ROOT/'docs/autogrowth/OWNER_ACTION_BALANCE_PILOT.md'
old_actor_for = base.actor_for
old_source_hashes = base.source_hashes


def actor_for(seed, role):
    if role != 'owner-balance':
        return old_actor_for(seed, role)
    prior = old_actor_for(seed, 'action-contrast')
    return OwnerBalancedActionContrastDevelopment.create(
        schema=base.prior.BooleanEnvironment.schema,
        state_coordinates=(0, 1, 2, 3), seed=seed, config=prior.config,
        search=prior.birth_search_config, development=prior.development_config,
        limits=prior.ownership_limits)


def source_hashes():
    hashes = old_source_hashes()
    for path in (Path(__file__).resolve(),
                 ROOT/'src/recon_lite_hector/learning/owner_action_balance.py'):
        hashes[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
    return hashes


def verify_extra(output):
    result = {}
    for seed in SEEDS:
        directory = output/f'seed-{seed}'/'owner-balance'
        counts = {}
        for offset in range(0, 1920, 64):
            block = directory/f'block-{offset:06d}'
            for row in (json.loads(line) for line in (block/'training.jsonl').read_text().splitlines()):
                owner_counts = counts.setdefault(row['owner'], {})
                action = row['action']
                owner_counts[action] = owner_counts.get(action, 0) + 1
            actor = load_actor(block/'checkpoint.pkl.gz')
            assert actor.exploration_owner is None
            assert set(counts) <= set(actor.action_visits)
            assert all(actual == counts.get(owner, {})
                       for owner, actual in actor.action_visits.items())
        result[str(seed)] = {'actual_action_counts_verified': 1920,
                             'owners': len(counts), 'counts': counts}
    return result


def configure():
    base.SEEDS = SEEDS
    base.ROLES = ROLES
    base.PROTOCOL = PROTOCOL
    base.actor_for = actor_for
    base.source_hashes = source_hashes
    base.verify_extra = verify_extra


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    configure()
    base.run(parser.parse_args().output)
