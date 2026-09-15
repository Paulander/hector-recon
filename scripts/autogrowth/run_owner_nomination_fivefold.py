"""User-authorized fivefold rerun; unchanged learner, individually sealed actions."""
import argparse
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import resource
import signal
import time

import run_owner_nomination as original
from run_owner_nomination import (
    ROOT, ROWS, SEEDS, ROLES, BooleanEnvironment, Feedback, RecursiveDevelopment,
    RecursiveConfig, DevelopmentConfig, AdaptiveOwnerDevelopment, OwnershipLimits,
    OwnerDevelopmentConfig, encoded, digest, write_once, json_once, save_actor,
    load_actor, evaluate, structure, verify_conversion, verify_pair,
)

PRIOR = ROOT/'snapshots/autogrowth/owner-nomination-20260914'
PROTOCOL = ROOT/'docs/autogrowth/OWNER_NOMINATION_FIVEFOLD.md'
COUNTS = {'training': 6400, 'evaluation': 1344, 'verification_actions': 1344,
          'blocks': 100, 'checkpoints': 106}


def schedule(seed):
    prefix, continuation = original.schedule(seed)
    return prefix*5, continuation[:128]*5 + continuation[128:]*5


def same_state(left, right):
    assert type(left) is type(right)
    excluded = {'graph', 'rng', 'proposal_rng', 'exploration_rng'}
    assert vars(left).keys() == vars(right).keys()
    for name in vars(left).keys()-excluded:
        assert getattr(left, name) == getattr(right, name), name
    for name in ('rng', 'proposal_rng', 'exploration_rng'):
        assert getattr(left, name).getstate() == getattr(right, name).getstate()
    assert vars(left.graph) == vars(right.graph)


def train_block(actor, order, directory, previous, *, do_evaluate):
    start = actor.completed
    directory.mkdir()
    (directory/'submitted').mkdir()
    (directory/'credited').mkdir()
    json_once(directory/'intent.json', {'start': start, 'stop': start+len(order),
              'order': list(order), 'previous': previous, 'evaluate': do_evaluate})
    records = []
    for row in order:
        event = actor.completed
        env = BooleanEnvironment(ROWS[row])
        action = actor.act(env, event_id=event, learn=True)
        reward = env.outcome()
        _, _, prediction, active = actor.pending[-1]
        weights = [actor.conditions[cid].weight for cid in active]
        adaptive = isinstance(actor, AdaptiveOwnerDevelopment)
        pending = actor.candidate_pending if adaptive else None
        record = {'event': event, 'row': row, 'action': action, 'reward': reward,
                  'prediction': prediction, 'active': active,
                  'denominator': len(active) if adaptive else 1+len(active),
                  'owner': pending[2] if pending else None,
                  'candidate_values': pending[4] if pending else None,
                  'weights_before': [float(w) for w in weights]}
        json_once(directory/'submitted'/f'{event:06d}.json', record)
        actor.observe(Feedback(event, action, reward))
        record['weights_after'] = [float(w) for w in weights]
        data = encoded(record)
        write_once(directory/'credited'/f'{event:06d}.json', data)
        records.append(data)
    write_once(directory/'training.jsonl', b''.join(records))
    checkpoint_hash = save_actor(actor, directory/'checkpoint.pkl.gz')
    restored = load_actor(directory/'checkpoint.pkl.gz')
    if isinstance(restored, AdaptiveOwnerDevelopment):
        restored.validate_ownership()
    result = evaluate(restored) if do_evaluate else None
    if result is not None:
        json_once(directory/'evaluation.json', result)
    json_once(directory/'complete.json', {'start': start, 'stop': restored.completed,
        'files': {p.relative_to(directory).as_posix(): digest(p.read_bytes())
                  for p in sorted(directory.rglob('*')) if p.is_file()}})
    verify_block(directory, order, start, previous)
    return restored, checkpoint_hash, result


def verify_block(directory, order, start, previous):
    manifest = json.loads((directory/'complete.json').read_text())
    actual_paths = {p.relative_to(directory).as_posix() for p in directory.rglob('*')
                    if p.is_file() and p != directory/'complete.json'}
    assert actual_paths == set(manifest['files'])
    for name, expected in manifest['files'].items():
        assert digest((directory/name).read_bytes()) == expected, str(directory/name)
    intent = json.loads((directory/'intent.json').read_text())
    assert intent == {'start': start, 'stop': start+len(order), 'order': list(order),
                      'previous': previous, 'evaluate': intent['evaluate']}
    assert manifest['start'] == start and manifest['stop'] == start+len(order)
    records = [json.loads(line) for line in (directory/'training.jsonl').read_text().splitlines()]
    assert len(records) == len(order)
    for event, row, record in zip(range(start, start+len(order)), order, records):
        assert (record['event'], record['row']) == (event, row)
        assert json.loads((directory/'credited'/f'{event:06d}.json').read_text()) == record
        assert json.loads((directory/'submitted'/f'{event:06d}.json').read_text()) == {
            k:v for k,v in record.items() if k != 'weights_after'}
        x, y, z, _ = ROWS[row]
        assert record['action'] in ('act-a', 'act-b')
        assert record['reward'] == (1 if (record['action']=='act-b') == (y if z else x) else -1)
        n = len(record['active']) + int(record['owner'] is None)
        assert record['denominator'] == n > 0
        assert len(record['weights_before']) == len(record['weights_after']) == len(record['active'])
        delta = .3*(record['reward']-record['prediction'])/n
        assert all(math.isclose(after-before, delta, abs_tol=2e-12)
                   for before, after in zip(record['weights_before'], record['weights_after']))
    actor = load_actor(directory/'checkpoint.pkl.gz')
    assert actor.completed == start+len(order)
    if isinstance(actor, AdaptiveOwnerDevelopment):
        actor.validate_ownership()
        assert actor.candidate_pending is None and actor.owner_pending is None
    return actor


def source_hashes():
    result = original.sources()
    result[PROTOCOL.relative_to(ROOT).as_posix()] = digest(PROTOCOL.read_bytes())
    return result


def verify_unchanged_learner():
    prior = json.loads((PRIOR/'source.json').read_text())
    unchanged = {name: expected for name, expected in prior.items()
                 if name.startswith(('src/', 'libs/'))}
    assert unchanged
    for name, expected in unchanged.items():
        assert digest((ROOT/name).read_bytes()) == expected
    return unchanged


def verify_run(out):
    source = json.loads((out/'source.json').read_text())
    for name, expected in source.items():
        assert digest((ROOT/name).read_bytes()) == digest((out/'source-snapshot'/name).read_bytes()) == expected
    counts = dict.fromkeys(COUNTS, 0)
    for seed in SEEDS:
        directory = out/f'seed-{seed}'
        prefix, continuation = schedule(seed)
        assert json.loads((directory/'schedule.json').read_text()) == {'prefix': prefix, 'continuation': continuation}
        same_state(load_actor(directory/'prefix/block-000064/checkpoint.pkl.gz'),
                   load_actor(PRIOR/f'seed-{seed}/prefix/block-000064/checkpoint.pkl.gz'))
        for role in ('prefix', *ROLES):
            role_dir = directory/role
            actor = load_actor(role_dir/'start.pkl.gz')
            previous = digest((role_dir/'start.pkl.gz').read_bytes())
            counts['checkpoints'] += 1
            start = actor.completed
            order = prefix if role=='prefix' else continuation
            for offset in range(0, len(order), 64):
                block = role_dir/f'block-{start+offset:06d}'
                actor = verify_block(block, order[offset:offset+64], start+offset, previous)
                previous = digest((block/'checkpoint.pkl.gz').read_bytes())
                counts['training'] += 64
                counts['blocks'] += 1
                counts['checkpoints'] += 1
                path = block/'evaluation.json'
                if path.exists():
                    assert evaluate(actor) == json.loads(path.read_text())
                    counts['evaluation'] += 16
                    counts['verification_actions'] += 16
    assert counts == COUNTS, counts
    return counts


def run(output):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (2*1024**3, 2*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (64*1024**2, 64*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (1200, 1205))
    def expired(_signal, _frame):
        raise TimeoutError('fixed 1200-second worker limit reached')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(1200)
    started = time.monotonic()
    report = {'status': 'running', 'seeds': SEEDS, 'roles': ROLES,
              'planned': COUNTS, 'arms': [], 'prefix_evaluations': {}}
    try:
        unchanged = verify_unchanged_learner()
        json_once(out/'unchanged-learner.json', unchanged)
        source = source_hashes()
        json_once(out/'source.json', source)
        for name in source:
            path = out/'source-snapshot'/name
            path.parent.mkdir(parents=True, exist_ok=True)
            write_once(path, (ROOT/name).read_bytes())
        json_once(out/'intent.json', report)
        for seed in SEEDS:
            directory = out/f'seed-{seed}'
            directory.mkdir()
            prefix, continuation = schedule(seed)
            json_once(directory/'schedule.json', {'prefix': prefix, 'continuation': continuation})
            # All learner parameters, including RecursiveConfig.prefix, stay unchanged.
            source_actor = RecursiveDevelopment(seed=seed, config=DevelopmentConfig(max_conditions=8),
                            recursive_config=RecursiveConfig(role='flat', prefix=128))
            prefix_dir = directory/'prefix'
            prefix_dir.mkdir()
            previous = save_actor(source_actor, prefix_dir/'start.pkl.gz')
            report['prefix_evaluations'][seed] = []
            for offset in range(0, 640, 64):
                source_actor, previous, initial = train_block(source_actor, prefix[offset:offset+64],
                    prefix_dir/f'block-{offset:06d}', previous, do_evaluate=offset in (64, 576))
                if initial is not None:
                    report['prefix_evaluations'][seed].append(initial)
                    print(json.dumps({'seed': seed, 'role': 'prefix', 'event': source_actor.completed,
                                      'correct': initial['correct']}), flush=True)
                if offset == 64:
                    same_state(source_actor, load_actor(PRIOR/f'seed-{seed}/prefix/block-000064/checkpoint.pkl.gz'))
            actors = {role: AdaptiveOwnerDevelopment.from_actor(source_actor, state_coordinates=(0,1,2,3),
                limits=OwnershipLimits(max_parameters=64, max_definitions=256, max_physical_nodes=2048),
                development=OwnerDevelopmentConfig(split_enabled=role=='adaptive')) for role in ROLES}
            for actor in actors.values():
                verify_conversion(source_actor, actor)
            verify_pair(actors['unsplit'], actors['adaptive'])
            pair = []
            for role, actor in actors.items():
                role_dir = directory/role
                role_dir.mkdir()
                previous = save_actor(actor, role_dir/'start.pkl.gz')
                arm = {'seed': seed, 'role': role, 'initial': initial, 'evaluations': [],
                       'structures': [], 'limits': asdict(actor.ownership_limits),
                       'development_config': asdict(actor.development_config)}
                report['arms'].append(arm)
                for offset in range(0, 1280, 64):
                    actor, previous, result = train_block(actor, continuation[offset:offset+64],
                        role_dir/f'block-{640+offset:06d}', previous, do_evaluate=True)
                    state = structure(actor)
                    arm['evaluations'].append(result)
                    arm['structures'].append(state)
                    print(json.dumps({'seed': seed, 'role': role, 'event': actor.completed,
                        'correct': result['correct'], 'owners': state['owners'],
                        'births': state['births_after_conversion'],
                        'elapsed_seconds': round(time.monotonic()-started, 2)}), flush=True)
                arm['development_history'] = actor.development_history
                arm['leaves'] = [{'owner': owner, 'path': repr(leaf.path), 'born': leaf.born,
                                 'visits': actor.owner_visits[owner]} for owner, leaf in actor.leaves.items()]
                json_once(role_dir/'results.json', arm)
                pair.append(structure(actor)['exploration_rng_digest'])
            assert len(set(pair)) == 1
        report['verification'] = verify_run(out)
        report['status'] = 'complete'
    except BaseException as error:
        report.update(status='incomplete', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        signal.alarm(0)
        report['elapsed_seconds'] = time.monotonic()-started
        report['max_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        json_once(out/'result.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    run(parser.parse_args().output)
