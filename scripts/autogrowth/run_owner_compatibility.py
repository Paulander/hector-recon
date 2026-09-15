"""Fixed compatibility comparison; source reuse, immutable action evidence, no retries."""
import argparse
import copy
from dataclasses import asdict
import json
import os
from pathlib import Path
import resource
import signal
import time

import run_owner_nomination_fivefold as prior
from run_owner_nomination import (ROOT, SEEDS, AdaptiveOwnerDevelopment, OwnershipLimits,
    OwnerDevelopmentConfig, digest, write_once, json_once, save_actor, load_actor,
    evaluate, structure, verify_conversion)
from recon_lite_hector.learning.compatible_owner import CompatibleOwnerDevelopment
from recon_lite_hector.learning.context_compatibility import CompatibilityConfig

SOURCE = ROOT/'snapshots/autogrowth/owner-nomination-fivefold-20260914'
PROTOCOL = ROOT/'docs/autogrowth/OWNER_COMPATIBILITY.md'
ROLES = ('control', 'compatible')
COUNTS = {'training': 5120, 'evaluation': 1280, 'verification_actions': 1280,
          'blocks': 80, 'checkpoints': 84}


def original_state(actor):
    """Read-only observer audit; never supplied back to an acting learner."""
    stripped = copy.deepcopy(actor)
    for name in ('compatibility_config', 'rejection_cache', 'birth_proposals'):
        delattr(stripped, name)
    stripped.__class__ = AdaptiveOwnerDevelopment
    return stripped


def same_control(actor, historical):
    assert not actor.compatibility_config.enabled
    prior.same_state(original_state(actor), historical)


def source_hashes():
    result = prior.source_hashes()
    result[PROTOCOL.relative_to(ROOT).as_posix()] = digest(PROTOCOL.read_bytes())
    return result


def verify_run(out):
    for name, expected in json.loads((out/'source.json').read_text()).items():
        assert digest((ROOT/name).read_bytes()) == digest((out/'source-snapshot'/name).read_bytes()) == expected
    counts = dict.fromkeys(COUNTS, 0)
    for seed in SEEDS:
        directory = out/f'seed-{seed}'
        _, order = prior.schedule(seed)
        assert json.loads((directory/'schedule.json').read_text()) == order
        source_info = json.loads((directory/'source-checkpoint.json').read_text())
        assert digest((directory/'source.pkl.gz').read_bytes()) == source_info['sha256']
        for role in ROLES:
            role_dir = directory/role
            actor = load_actor(role_dir/'start.pkl.gz')
            assert actor.completed == 640
            previous = digest((role_dir/'start.pkl.gz').read_bytes())
            counts['checkpoints'] += 1
            for offset in range(0, 1280, 64):
                block = role_dir/f'block-{640+offset:06d}'
                actor = prior.verify_block(block, order[offset:offset+64], 640+offset, previous)
                previous = digest((block/'checkpoint.pkl.gz').read_bytes())
                assert evaluate(actor) == json.loads((block/'evaluation.json').read_text())
                counts['training'] += 64
                counts['evaluation'] += 16
                counts['verification_actions'] += 16
                counts['blocks'] += 1
                counts['checkpoints'] += 1
    assert counts == COUNTS, counts
    return counts


def run(output):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (2*1024**3, 2*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (64*1024**2, 64*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (1800, 1805))
    def expired(_signal, _frame):
        raise TimeoutError('fixed 1800-second worker limit reached')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(1800)
    started = time.monotonic()
    report = {'status': 'running', 'seeds': SEEDS, 'roles': ROLES, 'planned': COUNTS,
              'source_payloads': 2, 'arms': [], 'historical_control_reproduction': []}
    try:
        json_once(out/'unchanged-original-learner.json', prior.verify_unchanged_learner())
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
            _, order = prior.schedule(seed)
            json_once(directory/'schedule.json', order)
            source_block = SOURCE/f'seed-{seed}/prefix/block-000576'
            expected = json.loads((source_block/'complete.json').read_text())['files']['checkpoint.pkl.gz']
            payload = (source_block/'checkpoint.pkl.gz').read_bytes()
            assert digest(payload) == expected
            write_once(directory/'source.pkl.gz', payload)
            json_once(directory/'source-checkpoint.json', {'sha256': expected,
                      'path': source_block.relative_to(ROOT).as_posix(), 'completed': 640})
            source_actor = load_actor(directory/'source.pkl.gz')
            assert source_actor.completed == 640
            initial = json.loads((source_block/'evaluation.json').read_text())
            pair = []
            for role in ROLES:
                actor = CompatibleOwnerDevelopment.from_actor(source_actor,
                    state_coordinates=(0,1,2,3), development=OwnerDevelopmentConfig(),
                    limits=OwnershipLimits(max_parameters=64, max_definitions=256, max_physical_nodes=2048),
                    compatibility=CompatibilityConfig(enabled=role=='compatible'))
                verify_conversion(source_actor, actor)
                prior.same_state(original_state(actor), load_actor(SOURCE/f'seed-{seed}/adaptive/start.pkl.gz'))
                role_dir = directory/role
                role_dir.mkdir()
                previous = save_actor(actor, role_dir/'start.pkl.gz')
                arm_started = time.monotonic()
                arm = {'seed': seed, 'role': role, 'initial': initial,
                       'evaluations': [], 'structures': [], 'block_seconds': [],
                       'limits': asdict(actor.ownership_limits),
                       'development_config': asdict(actor.development_config),
                       'compatibility_config': asdict(actor.compatibility_config)}
                report['arms'].append(arm)
                for offset in range(0, 1280, 64):
                    tick = time.monotonic()
                    block = role_dir/f'block-{640+offset:06d}'
                    actor, previous, result = prior.train_block(actor, order[offset:offset+64],
                        block, previous, do_evaluate=True)
                    arm['block_seconds'].append(time.monotonic()-tick)
                    if role == 'control':
                        old = SOURCE/f'seed-{seed}/adaptive'/block.name
                        same_control(actor, load_actor(old/'checkpoint.pkl.gz'))
                        assert (block/'training.jsonl').read_bytes() == (old/'training.jsonl').read_bytes()
                        assert result == json.loads((old/'evaluation.json').read_text())
                    arm['evaluations'].append(result)
                    arm['structures'].append(structure(actor))
                    print(json.dumps({'seed': seed, 'role': role, 'event': actor.completed,
                        'correct': result['correct'], 'nodes': len(actor.graph.nodes),
                        'rejections': sum(p['outcome']=='contradiction' for p in actor.birth_proposals),
                        'elapsed_seconds': round(time.monotonic()-started,2)}), flush=True)
                arm['elapsed_seconds'] = time.monotonic()-arm_started
                arm['birth_proposals'] = actor.birth_proposals
                arm['development_history'] = actor.development_history
                json_once(role_dir/'results.json', arm)
                if role == 'control':
                    report['historical_control_reproduction'].append({'seed': seed, 'blocks': 20,
                                                                    'full_original_state_and_logs': True})
                pair.append(actor.exploration_rng.getstate())
            assert pair[0] == pair[1]
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
