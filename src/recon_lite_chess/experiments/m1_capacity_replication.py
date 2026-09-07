"""Fresh-seed replication of the existing late condition-budget intervention.

Fixed schedules and ordinary scalar-outcome play only. This runner adds no
learner mechanism and never imports diagnostic answers into an actor.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import json
import multiprocessing
from pathlib import Path
import time

import chess

from recon_lite_hector.learning.terminal_development import DevelopmentConfig
from recon_lite_hector.learning.residual_shadow import ShadowConfig
from . import m1_capacity as capacity

prior = capacity.prior


def run_seed(task):
    seed, manifest, fens, validation, output, private = task
    output, directory = Path(output), Path(private) / f'seed-{seed}'
    directory.mkdir()
    prefix_dir = directory / 'prefix'
    prefix_dir.mkdir()
    started = time.monotonic()
    deadline = started + manifest['wall_seconds_per_seed']
    spec = manifest['plans'][str(seed)]
    blocks, milestones = [], {}
    state = {'seed': seed, 'role_index': 0, 'next_event': 0,
             'organism': prior.new_actor(seed, 'none', spec)}
    frozen_history = None
    try:
        prior.save_checkpoint(prefix_dir, state, manifest)
        for start in range(0, manifest['split_event'], manifest['block']):
            stop = min(start + manifest['block'], manifest['split_event'])
            actor = state['organism']
            training = prior.train(actor, fens, spec['order'][start:stop],
                                   start_event=start, deadline=deadline)
            blocks.append({'start': start, 'end': stop, 'training': training})
            state['next_event'] = stop
            if stop >= spec['after_episode']:
                history = prior.digest(actor.shadow.report())
                if frozen_history is not None and history != frozen_history:
                    raise RuntimeError('completed shadow history changed')
                frozen_history = history
            prior.save_checkpoint(prefix_dir, state, manifest)
            if stop in manifest['prefix_evaluations']:
                evaluated = prior.evaluate(actor, validation, role='none', deadline=deadline)
                pointer = prior.save_checkpoint(prefix_dir, state, manifest)
                state = prior.load_checkpoint(prefix_dir, manifest, seed)
                if prior.actor_digest(state['organism']) != prior.actor_digest(actor):
                    raise RuntimeError('prefix reload changed the actor')
                milestones[str(stop)] = {'result': evaluated,
                    'checkpoint_sha256': pointer['sha256'], 'checkpoint_reloaded': True}
            progress = {'seed': seed, 'status': 'prefix', 'completed': stop,
                        'blocks': blocks, 'milestones': milestones}
            prior.atomic_json(output / f'progress-{seed}.json', progress)
            print(json.dumps({'seed': seed, 'completed': stop, 'phase': 'prefix',
                **({'mates': milestones[str(stop)]['result']['evaluation']['mates']}
                   if str(stop) in milestones else {})}), flush=True)
        paired = capacity.compare(state['organism'], fens, validation,
            spec['order'][manifest['split_event']:], event=manifest['split_event'],
            caps=manifest['caps'], deadline=deadline, private=directory,
            manifest=manifest, seed=seed)
        if time.monotonic() >= deadline:
            raise TimeoutError('replication seed time cap expired')
        result = {'seed': seed, 'status': 'complete', 'prefix_blocks': blocks,
                  'milestones': milestones, 'comparison': paired,
                  'wall_seconds': time.monotonic() - started}
        prior.atomic_json(output / f'seed-{seed}.json', result)
        print(json.dumps({'seed': seed, 'phase': 'complete', 'mates': {
            cap: arm['after']['evaluation']['mates'] for cap, arm in paired['arms'].items()}}), flush=True)
        return result
    except BaseException as error:
        prior.atomic_json(output / f'failure-{seed}.json', {
            'seed': seed, 'status': 'incomplete', 'error': str(error),
            'prefix_blocks': blocks, 'milestones': milestones,
            'note': 'No retry. Private checkpoints preserve completed boundaries; '
                    'unreported partial blocks or evaluations are additional uncertain work.'})
        raise


def build_manifest(seeds, fens, validation, train_sha, validation_sha, *, workers, wall_seconds):
    if (not seeds or len(set(seeds)) != len(seeds) or set(seeds) & {1, 2, 3}
            or min(workers, wall_seconds) < 1):
        raise ValueError('unique fresh seeds and positive budgets required')
    if not fens or not validation:
        raise ValueError('nonempty training and development pools required')
    train_orbits = {prior.orbit_key(chess.Board(fen)) for fen in fens}
    validation_orbits = {prior.orbit_key(chess.Board(fen)) for fen in validation}
    if train_orbits & validation_orbits:
        raise ValueError('training and development symmetry orbits overlap')
    spec = {'actor_config': asdict(DevelopmentConfig(max_conditions=32)),
            'shadow_config': asdict(ShadowConfig(candidates=64, discovery_episodes=64, min_support=4)),
            'after_episode': 128, 'recovery_after': 256}
    plans = {str(seed): spec | {'order': list(prior.prior.prior.schedule_indices(len(fens), 1280, seed))}
             for seed in seeds}
    return {'schema': 'm1_capacity_replication.v1', 'source': prior.sources(),
            'runner_sha256': prior.sha(__file__), 'comparison_runner_sha256': prior.sha(capacity.__file__),
            'seeds': seeds, 'plans': plans, 'role': 'none', 'caps': [32, 64],
            'split_event': 1024, 'end_event': 1280, 'block': 128,
            'prefix_evaluations': [384, 1024], 'workers': min(workers, len(seeds)),
            'wall_seconds_per_seed': wall_seconds,
            'train_sha256': train_sha, 'validation_sha256': validation_sha,
            'train_count': len(fens), 'validation_count': len(validation),
            'train_orbits': len(train_orbits), 'validation_orbits': len(validation_orbits),
            'training_moves': len(seeds) * (1024 + 2 * 256),
            'evaluation_moves': len(seeds) * 4 * len(validation),
            'final_test_opened': False, 'validation_is_development': True,
            'limits': ['Fresh random seeds on the same viewed development positions.',
                       'The budget changes at 1024, not from birth; this tests late expansion.',
                       'Copied prefix experience is counted once, not as additional play.',
                       'Learning rate, exploration, credit, random birth and pruning are unchanged.',
                       'No score selects a seed, checkpoint, schedule, condition or learning rate.',
                       'No diagnostic grading, fitted weights or action labels enter training.',
                       'One attempt, no automatic retry or extension; partial work is retained.']}


def run(args):
    fens, train_sha = prior.load_split(args.pool, 'train')
    validation, validation_sha = prior.load_split(args.pool, 'validation')
    manifest = build_manifest(args.seeds, fens, validation, train_sha, validation_sha,
                              workers=args.workers, wall_seconds=args.wall_seconds)
    args.output.mkdir(parents=True, exist_ok=False)
    args.private.mkdir(parents=True, exist_ok=False, mode=0o700)
    prior.atomic_json(args.output / 'manifest.json', manifest)
    tasks = [(seed, manifest, fens, validation, str(args.output), str(args.private)) for seed in args.seeds]
    try:
        if manifest['workers'] == 1:
            results = [run_seed(task) for task in tasks]
        else:
            with ProcessPoolExecutor(max_workers=manifest['workers'],
                                     mp_context=multiprocessing.get_context('spawn')) as executor:
                results = list(executor.map(run_seed, tasks))
        training_moves = sum(b['training']['real_moves'] for r in results for b in r['prefix_blocks'])
        training_moves += sum(b['real_moves'] for r in results
                              for a in r['comparison']['arms'].values() for b in a['blocks'])
        evaluation_moves = sum(m['result']['evaluation']['count'] for r in results
                               for m in r['milestones'].values())
        evaluation_moves += sum(a['after']['evaluation']['count'] for r in results
                                for a in r['comparison']['arms'].values())
        if (training_moves, evaluation_moves) != (manifest['training_moves'], manifest['evaluation_moves']):
            raise RuntimeError('completed move accounting differs from the declared budget')
        result = {'status': 'complete', 'manifest': manifest, 'results': results,
                  'actual_training_moves': training_moves, 'actual_evaluation_moves': evaluation_moves}
        prior.atomic_json(args.output / 'summary.json', result)
        return result
    except BaseException as error:
        prior.atomic_json(args.output / 'failure.json', {'status': 'incomplete', 'error': str(error)})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('pool', 'output', 'private'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--seeds', type=int, nargs='+', default=[4, 5, 6, 7, 8, 9])
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--wall-seconds', type=int, default=2400)
    print(json.dumps({'status': run(parser.parse_args())['status']}))


if __name__ == '__main__':
    main()
