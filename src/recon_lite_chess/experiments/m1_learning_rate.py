"""Fixed learning-rate comparison; unchanged learner and scalar-outcome coach.

Behavior is recorded only after an actual action and its feedback. Recorded
actions are never replayed into learning; analysis happens after every arm ends.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import copy
from dataclasses import asdict, replace
import json
import multiprocessing
from pathlib import Path
import signal
import time

from . import m1_long_play as continuation

from .m1_exploration import train_logged

prior = continuation.prior
RATES = (0.30, 0.10)


def restore_source(reference, private_source, seed):
    old = reference['manifest']
    row = next(r for r in reference['results'] if r['seed'] == seed)
    expected = row['milestones'][str(old['end_event'])]
    directory = Path(private_source) / f'seed-{seed}'
    pointer = prior.read(directory / 'latest.json')
    if pointer['sha256'] != expected['checkpoint_sha256']:
        raise ValueError('source is not the published final checkpoint')
    state = prior.load_checkpoint(directory, old, seed)
    actor = state['organism']
    snapshot = {k: v for k, v in expected['result'].items() if k != 'evaluation'}
    if (state['next_event'] != old['end_event'] or asdict(actor.config) != row['config']
            or prior.snapshot(actor) != snapshot or actor.config.learning_rate != RATES[0]):
        raise ValueError('source endpoint, learned state or base learning_rate differs')
    return actor, expected



def run_arm(task):
    """Enforce a wall deadline even inside one expensive action or solver call."""
    def expired(signum, frame):
        raise TimeoutError('hard arm wall limit expired')
    old_handler = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, task[4]['wall_seconds_per_arm'])
    try:
        return _run_arm(task)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


def _run_arm(task):
    seed, rate, reference, private_source, manifest, fens, validation, output, private = task
    started = time.monotonic()
    label = f'{rate:.2f}'
    directory = Path(private) / f'seed-{seed}/learning_rate-{label}'
    out = Path(output) / f'seed-{seed}/learning_rate-{label}'
    directory.mkdir(parents=True)
    out.mkdir(parents=True)
    try:
        original, expected = restore_source(reference, private_source, seed)
        inherited_digest = prior.actor_digest(original)
        actor = copy.deepcopy(original)
        actor.config = replace(actor.config, learning_rate=rate)
        config = asdict(original.config) | {'learning_rate': rate}
        if asdict(actor.config) != config:
            raise RuntimeError('treatment changed more than learning_rate')
        # Verify the complete inherited learned/control state with the sole
        # permitted config field normalized, before any further interaction.
        actor.config = original.config
        if prior.actor_digest(actor) != inherited_digest:
            raise RuntimeError('clone changed inherited learned/control state')
        actor.config = replace(actor.config, learning_rate=rate)
        log = directory / 'training-actions.jsonl'
        with log.open('x') as stream:
            def step(o, positions, order, **kwargs):
                return train_logged(o, positions, order, stream=stream, **kwargs)
            result = continuation.continue_actor(actor, fens, validation, seed=seed,
                manifest=manifest, directory=directory, output=out,
                deadline=started + manifest['wall_seconds_per_arm'], train_step=step)
        if prior.actor_digest(original) != inherited_digest:
            raise RuntimeError('comparison mutated original actor')
        final_actor = prior.load_checkpoint(directory, manifest, seed)['organism']
        result['final_train_evaluation'] = prior.evaluate(final_actor, fens, role='none',
            deadline=started + manifest['wall_seconds_per_arm'])
        if not result['final_train_evaluation']['evaluation']['learned_state_unchanged']:
            raise RuntimeError('final training-set evaluation changed the learned state')
        if prior.actor_digest(original) != inherited_digest:
            raise RuntimeError('final evaluation mutated original actor')
        result.update(seed=seed, learning_rate=rate, status='complete',
            source_checkpoint_sha256=expected['checkpoint_sha256'],
            inherited_evaluation=expected['result']['evaluation'],
            inherited_actor_digest=inherited_digest, inherited_state_unchanged=True,
            sole_config_treatment_verified=True,
            transcript_sha256=prior.sha(log), transcript_bytes=log.stat().st_size,
            wall_seconds=time.monotonic()-started)
        prior.atomic_json(out / 'result.json', result)
        return result
    except BaseException as error:
        prior.atomic_json(out / 'arm-failure.json', {'status': 'incomplete', 'seed': seed,
            'learning_rate': rate, 'error': str(error),
            'note': 'One attempt. Preserve action log, completed checkpoints and pending-unit records.'})
        raise


def make_manifest(reference, fens, validation, train_sha, validation_sha, *, seeds,
                  end_event, evaluations, block, workers, wall_seconds, reference_sha):
    old = reference['manifest']
    if reference['status'] != 'complete' or old['source'] != prior.sources():
        raise ValueError('complete source-matched long-play reference required')
    if (train_sha, validation_sha) != (old['train_sha256'], old['validation_sha256']):
        raise ValueError('original training/development pools required')
    if not seeds or len(set(seeds)) != len(seeds) or not set(seeds) <= set(old['seeds']):
        raise ValueError('unique seeds from the declared source required')
    start = old['end_event']
    if (end_event <= start or not evaluations or evaluations != sorted(set(evaluations))
            or evaluations[0] <= start or evaluations[-1] != end_event
            or min(block, workers, wall_seconds) < 1):
        raise ValueError('positive budgets and ordered fixed milestones ending at endpoint required')
    plans = {str(s): list(prior.prior.prior.schedule_indices(len(fens), end_event, s)) for s in seeds}
    if any(plans[str(s)][:start] != old['plans'][str(s)] for s in seeds):
        raise ValueError('continued schedule changed the inherited prefix')
    return {'schema': 'm1_learning_rate.v1', 'source': prior.sources(),
            'runner_sha256': prior.sha(__file__), 'continuation_runner_sha256': prior.sha(continuation.__file__),
            'reference_sha256': reference_sha, 'seeds': seeds, 'rates': list(RATES),
            'start_event': start, 'end_event': end_event, 'evaluations': evaluations, 'block': block,
            'plans': plans, 'workers': min(workers, len(seeds)*len(RATES)),
            'wall_seconds_per_arm': wall_seconds, 'train_sha256': train_sha,
            'validation_sha256': validation_sha, 'train_count': len(fens), 'validation_count': len(validation),
            'training_moves': len(seeds)*len(RATES)*(end_event-start),
            'development_evaluation_moves': len(seeds)*len(RATES)*len(evaluations)*len(validation),
            'training_evaluation_moves': len(seeds)*len(RATES)*len(fens),
            'evaluation_moves': len(seeds)*len(RATES)*(len(evaluations)*len(validation)+len(fens)),
            'final_test_opened': False, 'validation_is_development': True,
            'limits': ['Selected saved histories, not fresh-seed confirmation.',
                'Only learning_rate differs; exploration stays .25 and normal growth/credit continue.',
                'Matched exploration RNG and exercises; rate-dependent pruning/birth may shift the separate birth stream.',
                'Action/outcome log is written after feedback and never read by training.',
                'No alternate-action grading, diagnostic answers, family steering or score-selected endpoint.',
                'One attempt and fixed time cap per arm; no automatic retry, resume or extension.']}


def run(args):
    reference = prior.read(args.reference)['run']
    fens, train_sha = prior.load_split(args.pool, 'train')
    validation, validation_sha = prior.load_split(args.pool, 'validation')
    manifest = make_manifest(reference, fens, validation, train_sha, validation_sha, seeds=args.seeds,
        end_event=args.episodes, evaluations=args.evaluate_at, block=args.block,
        workers=args.workers, wall_seconds=args.wall_seconds, reference_sha=prior.sha(args.reference))
    args.output.mkdir(parents=True, exist_ok=False)
    args.private.mkdir(parents=True, exist_ok=False, mode=0o700)
    prior.atomic_json(args.output / 'manifest.json', manifest)
    tasks = [(s, rate, reference, str(args.private_source), manifest, fens, validation,
              str(args.output), str(args.private)) for s in manifest['seeds'] for rate in RATES]
    try:
        if manifest['workers'] == 1:
            results = [run_arm(task) for task in tasks]
        else:
            with ProcessPoolExecutor(max_workers=manifest['workers'],
                                     mp_context=multiprocessing.get_context('spawn')) as executor:
                results = list(executor.map(run_arm, tasks))
        training = sum(b['training']['real_moves'] for r in results for b in r['blocks'])
        evaluation = sum(m['result']['evaluation']['count'] for r in results for m in r['milestones'].values())
        evaluation += sum(r['final_train_evaluation']['evaluation']['count'] for r in results)
        if (training, evaluation) != (manifest['training_moves'], manifest['evaluation_moves']):
            raise RuntimeError('completed play differs from declared moves')
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
    parser.add_argument('--seeds', type=int, nargs='+', default=[4, 7, 9])
    parser.add_argument('--episodes', type=int, default=6144)
    parser.add_argument('--evaluate-at', type=int, nargs='+', default=[4608, 5120, 5632, 6144])
    parser.add_argument('--block', type=int, default=128)
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--wall-seconds', type=int, default=3000)
    print(json.dumps({'status': run(parser.parse_args())['status']}))


if __name__ == '__main__':
    main()
