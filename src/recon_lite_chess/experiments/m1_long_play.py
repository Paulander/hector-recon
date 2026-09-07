"""Longer ordinary play from every saved larger-budget replication actor.

Only a declared continuation schedule and checkpoint/report orchestration. The
learner, scalar coach, feature terminals and all learning parameters are reused.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import json
import multiprocessing
from pathlib import Path
import time

from . import ordinary_m1 as prior


def restore_source(reference, private_source, seed):
    """Verify the published endpoint before loading its trusted private state."""
    original = reference['manifest']
    cap = str(max(original['caps']))
    expected = next(r for r in reference['results'] if r['seed'] == seed)['comparison']['arms'][cap]
    directory = Path(private_source) / f'seed-{seed}/cap-{cap}'
    pointer = prior.read(directory / 'latest.json')
    if pointer['sha256'] != expected['checkpoint_sha256']:
        raise ValueError('source is not the published final checkpoint')
    state = prior.load_checkpoint(directory, original, seed)
    actor = state['organism']
    snapshot = {k: v for k, v in expected['after'].items() if k != 'evaluation'}
    if (state['next_event'] != original['end_event'] or asdict(actor.config) != expected['config']
            or prior.snapshot(actor) != snapshot):
        raise ValueError('source endpoint or learned state differs')
    return actor, expected


def continue_actor(actor, fens, validation, *, seed, manifest, directory, output, deadline):
    """Fixed chronological milestones; scores never choose the next action/block."""
    directory, output = Path(directory), Path(output)
    state = {'seed': seed, 'role_index': 0, 'next_event': manifest['start_event'], 'organism': actor}
    config, history = asdict(actor.config), prior.digest(actor.shadow.report())
    initial = prior.snapshot(actor)
    blocks, milestones, pending = [], {}, None
    try:
        prior.save_checkpoint(directory, state, manifest)
        start = manifest['start_event']
        while start < manifest['end_event']:
            next_evaluation = next(e for e in manifest['evaluations'] if e > start)
            stop = min(start + manifest['block'], next_evaluation)
            pending = {'kind': 'training', 'start': start, 'end': stop, 'max_moves': stop-start}
            prior.atomic_json(output / f'pending-{seed}.json', pending)
            training = prior.train(state['organism'], fens, manifest['plans'][str(seed)][start:stop],
                                   start_event=start, deadline=deadline)
            state['next_event'] = stop
            blocks.append({'start': start, 'end': stop, 'training': training})
            prior.save_checkpoint(directory, state, manifest)
            pending = None
            actor = state['organism']
            if asdict(actor.config) != config or prior.digest(actor.shadow.report()) != history:
                raise RuntimeError('continuation changed fixed settings or completed shadow history')
            if stop in manifest['evaluations']:
                pending = {'kind': 'evaluation', 'event': stop, 'max_moves': len(validation)}
                prior.atomic_json(output / f'pending-{seed}.json', pending)
                evaluated = prior.evaluate(actor, validation, role='none', deadline=deadline)
                pointer = prior.save_checkpoint(directory, state, manifest)
                state = prior.load_checkpoint(directory, manifest, seed)
                if prior.actor_digest(state['organism']) != prior.actor_digest(actor):
                    raise RuntimeError('milestone reload changed learned state')
                milestones[str(stop)] = {'result': evaluated,
                    'checkpoint_sha256': pointer['sha256'], 'checkpoint_reloaded': True}
                prior.atomic_json(output / f'seed-{seed}-{stop}.json', milestones[str(stop)])
                pending = None
            prior.atomic_json(output / f'progress-{seed}.json', {
                'seed': seed, 'completed': stop, 'blocks': blocks, 'milestones': milestones})
            (output / f'pending-{seed}.json').unlink(missing_ok=True)
            print(json.dumps({'seed': seed, 'completed': stop,
                **({'mates': milestones[str(stop)]['result']['evaluation']['mates']}
                   if str(stop) in milestones else {})}), flush=True)
            start = stop
        if time.monotonic() >= deadline:
            raise TimeoutError('long-play seed time cap expired')
        return {'initial': initial, 'config': config, 'blocks': blocks, 'milestones': milestones,
                'settings_and_completed_history_unchanged': True}
    except BaseException as error:
        prior.atomic_json(output / f'failure-{seed}.json', {
            'status': 'incomplete', 'seed': seed, 'error': str(error),
            'completed_blocks': blocks, 'completed_milestones': milestones, 'unfinished_unit': pending,
            'note': 'One attempt only. An unfinished unit may contain additional actual moves; '
                    'preserve it and all private boundaries, with no silent replay or budget reset.'})
        raise


def run_seed(task):
    seed, reference, private_source, manifest, fens, validation, output, private = task
    started = time.monotonic()
    directory = Path(private) / f'seed-{seed}'
    directory.mkdir()
    actor, expected = restore_source(reference, private_source, seed)
    result = continue_actor(actor, fens, validation, seed=seed, manifest=manifest,
                            directory=directory, output=output,
                            deadline=started + manifest['wall_seconds_per_seed'])
    result.update(seed=seed, status='complete', source_checkpoint_sha256=expected['checkpoint_sha256'],
                  inherited_evaluation=expected['after']['evaluation'], wall_seconds=time.monotonic()-started)
    prior.atomic_json(Path(output) / f'seed-{seed}.json', result)
    return result


def make_manifest(reference, fens, validation, train_sha, validation_sha, *,
                  end_event, evaluations, block, workers, wall_seconds, reference_sha):
    old = reference['manifest']
    if reference['status'] != 'complete' or old['source'] != prior.sources():
        raise ValueError('complete source-matched replication required')
    if (train_sha, validation_sha) != (old['train_sha256'], old['validation_sha256']):
        raise ValueError('original training/development pools required')
    start = old['end_event']
    if (end_event <= start or not evaluations or evaluations != sorted(set(evaluations))
            or evaluations[0] <= start or evaluations[-1] != end_event
            or min(block, workers, wall_seconds) < 1):
        raise ValueError('positive budgets and ordered fixed milestones ending at the endpoint required')
    seeds = old['seeds']  # Every seed; no performance-based subset.
    if sorted(r['seed'] for r in reference['results']) != sorted(seeds):
        raise ValueError('complete results for every source seed required')
    plans = {str(seed): list(prior.prior.prior.schedule_indices(len(fens), end_event, seed)) for seed in seeds}
    if any(plans[str(seed)][:start] != old['plans'][str(seed)]['order'] for seed in seeds):
        raise ValueError('continued schedule changed the inherited prefix')
    return {'schema': 'm1_long_play.v1', 'source': prior.sources(), 'runner_sha256': prior.sha(__file__),
            'reference_sha256': reference_sha, 'seeds': seeds, 'source_cap': max(old['caps']),
            'start_event': start, 'end_event': end_event, 'evaluations': evaluations, 'block': block,
            'plans': plans, 'workers': min(workers, len(seeds)), 'wall_seconds_per_seed': wall_seconds,
            'train_sha256': train_sha, 'validation_sha256': validation_sha,
            'training_moves': len(seeds)*(end_event-start),
            'evaluation_moves': len(seeds)*len(evaluations)*len(validation),
            'final_test_opened': False, 'validation_is_development': True,
            'limits': ['All saved larger-budget endpoints continue with exactly the same configuration.',
                       'The inherited baseline evaluation is reused, not counted as new play.',
                       'No scores choose a seed, checkpoint, schedule, parameter or structure.',
                       'This measures ordinary continuation, not another causal budget/rate comparison.',
                       'One attempt with a fixed time cap; no automatic retry, resume or extension.']}


def run(args):
    reference = prior.read(args.reference)['run']
    fens, train_sha = prior.load_split(args.pool, 'train')
    validation, validation_sha = prior.load_split(args.pool, 'validation')
    manifest = make_manifest(reference, fens, validation, train_sha, validation_sha,
        end_event=args.episodes, evaluations=args.evaluate_at, block=args.block,
        workers=args.workers, wall_seconds=args.wall_seconds, reference_sha=prior.sha(args.reference))
    args.output.mkdir(parents=True, exist_ok=False)
    args.private.mkdir(parents=True, exist_ok=False, mode=0o700)
    prior.atomic_json(args.output / 'manifest.json', manifest)
    tasks = [(seed, reference, str(args.private_source), manifest, fens, validation,
              str(args.output), str(args.private)) for seed in manifest['seeds']]
    try:
        if manifest['workers'] == 1:
            results = [run_seed(task) for task in tasks]
        else:
            with ProcessPoolExecutor(max_workers=manifest['workers'],
                                     mp_context=multiprocessing.get_context('spawn')) as executor:
                results = list(executor.map(run_seed, tasks))
        training = sum(b['training']['real_moves'] for r in results for b in r['blocks'])
        evaluation = sum(m['result']['evaluation']['count'] for r in results for m in r['milestones'].values())
        if (training, evaluation) != (manifest['training_moves'], manifest['evaluation_moves']):
            raise RuntimeError('completed play differs from the declared move budget')
        result = {'status': 'complete', 'manifest': manifest, 'results': results,
                  'actual_training_moves': training, 'actual_evaluation_moves': evaluation}
        prior.atomic_json(args.output / 'summary.json', result)
        return result
    except BaseException as error:
        prior.atomic_json(args.output / 'failure.json', {'status': 'incomplete', 'error': str(error)})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('pool', 'reference', 'private-source', 'output', 'private'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--episodes', type=int, default=4096)
    parser.add_argument('--evaluate-at', type=int, nargs='+', default=[1536, 2048, 3072, 4096])
    parser.add_argument('--block', type=int, default=128)
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--wall-seconds', type=int, default=4800)
    print(json.dumps({'status': run(parser.parse_args())['status']}))


if __name__ == '__main__':
    main()
