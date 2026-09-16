"""One-shot, three-arm action-conditional nomination pilot on fresh Boolean seeds."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import resource
import signal
import sys
import time

import run_owner_trial_learning as prior
from run_owner_nomination import ROOT, digest, json_once, save_actor, load_actor, evaluate
from recon_lite_hector.learning.owner_action_contrast import (
    ActionContrastLearningTrialOwnerDevelopment,
)
from recon_lite_hector.learning.owner_trial_learning import LearningTrialOwnerDevelopment


SEEDS = (30, 31, 32)
ROLES = ('current', 'learning-trial', 'action-contrast')
PROTOCOL = ROOT / 'docs/autogrowth/OWNER_ACTION_CONTRAST_PILOT.md'
COUNTS = {'training': 17280, 'evaluation': 4464, 'verification_actions': 4464,
          'blocks': 270, 'checkpoints': 279}


def actor_for(seed, role):
    if role == 'action-contrast':
        baseline = prior.create_actor(seed, 'learning-trial')
        return ActionContrastLearningTrialOwnerDevelopment.create(
            schema=prior.BooleanEnvironment.schema, state_coordinates=(0, 1, 2, 3),
            seed=seed, config=baseline.config, search=baseline.birth_search_config,
            development=baseline.development_config, limits=baseline.ownership_limits)
    return prior.create_actor(seed, role)


def source_hashes():
    hashes = prior.source_hashes()
    for path in (Path(__file__).resolve(), PROTOCOL,
                 ROOT / 'src/recon_lite_hector/learning/owner_action_contrast.py'):
        hashes[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
    return hashes


def verify_action_contrast(actor, records, evidence):
    if not isinstance(actor, ActionContrastLearningTrialOwnerDevelopment):
        return
    for row in records:
        owner = row['owner']
        for index, side in enumerate(row['candidate_values']):
            key = (bool(side), row['action'])
            cell = evidence.setdefault(owner, {}).setdefault(index, {}).setdefault(key, [0, 0.0])
            cell[0] += 1
            cell[1] += row['reward'] - row['prediction']
    assert set(evidence) <= set(actor.action_contrast_evidence)
    for owner, candidates in actor.action_contrast_evidence.items():
        expected = evidence.get(owner, {})
        assert set(candidates) == set(expected)
        for index, statistic in candidates.items():
            assert statistic.counts == {key: cell[0] for key, cell in expected[index].items()}
            assert statistic.sums == {key: cell[1] for key, cell in expected[index].items()}


def trial_history(actor):
    if not isinstance(actor, LearningTrialOwnerDevelopment):
        return []
    return [dict(parent=t.parent, children=t.children,
                 route=t.route, born=t.born, state=t.state.name,
                 resolution=t.resolution, summary=actor.trial_summary(t),
                 assessment_clock=asdict(actor.assessment_clocks[(t.parent, t.born)]))
            for t in [*actor.split_trial_history, *actor.split_trials.values()]]


def verify(output, hashes):
    for name, expected in hashes.items():
        assert digest((ROOT/name).read_bytes()) == digest((output/'source-snapshot'/name).read_bytes()) == expected
    counts = dict.fromkeys(COUNTS, 0)
    for seed in SEEDS:
        order = prior.schedule(seed)
        assert json.loads((output/f'seed-{seed}/schedule.json').read_text()) == order
        starts = [load_actor(output/f'seed-{seed}'/role/'start.pkl.gz') for role in ROLES]
        prior.verify_initial_pair(starts)
        final_rngs = []
        for role, actor in zip(ROLES, starts):
            prior.verify_same_state(actor, actor_for(seed, role))
            directory = output/f'seed-{seed}'/role
            assert evaluate(actor) == json.loads((directory/'initial-evaluation.json').read_text())
            counts['evaluation'] += 16
            counts['verification_actions'] += 16
            counts['checkpoints'] += 1
            previous = digest((directory/'start.pkl.gz').read_bytes())
            births, trials, action_evidence = {}, {}, {}
            for offset in range(0, 1920, 64):
                block = directory/f'block-{offset:06d}'
                actor = prior.recording.prior.verify_block(block, order[offset:offset+64], offset, previous)
                previous = digest((block/'checkpoint.pkl.gz').read_bytes())
                records = [json.loads(line) for line in (block/'training.jsonl').read_text().splitlines()]
                prior.verify_birth_evidence(actor, records, births)
                prior.verify_trials(actor, records, trials)
                verify_action_contrast(actor, records, action_evidence)
                assert evaluate(actor) == json.loads((block/'evaluation.json').read_text())
                counts['training'] += 64
                counts['evaluation'] += 16
                counts['verification_actions'] += 16
                counts['blocks'] += 1
                counts['checkpoints'] += 1
            final_rngs.append(actor.exploration_rng.getstate())
        assert all(state == final_rngs[0] for state in final_rngs)
    assert counts == COUNTS, counts
    return counts


def run(path):
    output = Path(path)
    output.mkdir(parents=True, exist_ok=False)
    # Darwin rejects RLIMIT_AS; the existing independent guard enforces 2 GiB
    # resident memory there. Linux retains the hard address-space limit.
    if sys.platform != 'darwin':
        resource.setrlimit(resource.RLIMIT_AS, (2*1024**3, 2*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (64*1024**2, 64*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (3600, 3605))
    def expired(_signal, _frame):
        raise TimeoutError('declared 3600-second worker wall limit reached')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(3600)
    started = time.monotonic()
    report = {'status': 'running', 'seeds': SEEDS, 'roles': ROLES,
              'planned': COUNTS, 'source_payloads': 0, 'arms': []}
    try:
        hashes = source_hashes()
        json_once(output/'source.json', hashes)
        for name in hashes:
            p = output/'source-snapshot'/name
            p.parent.mkdir(parents=True, exist_ok=True)
            prior.write_once(p, (ROOT/name).read_bytes())
        json_once(output/'intent.json', report)
        for seed in SEEDS:
            directory = output/f'seed-{seed}'
            directory.mkdir()
            order = prior.schedule(seed)
            json_once(directory/'schedule.json', order)
            actors = [actor_for(seed, role) for role in ROLES]
            prior.verify_initial_pair(actors)
            final_rngs = []
            for role, actor in zip(ROLES, actors):
                arm_dir = directory/role
                arm_dir.mkdir()
                previous = save_actor(actor, arm_dir/'start.pkl.gz')
                initial = evaluate(actor)
                json_once(arm_dir/'initial-evaluation.json', initial)
                arm = {'seed': seed, 'role': role, 'initial': initial,
                       'evaluations': [], 'structures': [],
                       'search': asdict(actor.birth_search_config),
                       'limits': asdict(actor.ownership_limits),
                       'candidate_pool': actor.birth_definitions,
                       'initial_structure': prior.structure(actor)}
                report['arms'].append(arm)
                for offset in range(0, 1920, 64):
                    actor, previous, result = prior.train_block(
                        actor, order[offset:offset+64], arm_dir/f'block-{offset:06d}', previous)
                    arm['evaluations'].append(result)
                    arm['structures'].append(prior.structure(actor))
                    print(json.dumps({'seed': seed, 'role': role, 'event': actor.completed,
                                      'correct': result['correct'],
                                      'owners': len(actor.leaves),
                                      'nodes': len(actor.graph.nodes),
                                      'elapsed_seconds': round(time.monotonic()-started, 2)}),
                          flush=True)
                arm['trial_history'] = trial_history(actor)
                arm['birth_nominations'] = actor.birth_nominations
                arm['development_history'] = actor.development_history
                json_once(arm_dir/'results.json', arm)
                final_rngs.append(actor.exploration_rng.getstate())
            assert all(state == final_rngs[0] for state in final_rngs)
        report['verification'] = verify(output, hashes)
        report['status'] = 'complete'
    except BaseException as error:
        report.update(status='incomplete', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        signal.alarm(0)
        report['elapsed_seconds'] = time.monotonic()-started
        report['max_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        json_once(output/'result.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    run(parser.parse_args().output)
