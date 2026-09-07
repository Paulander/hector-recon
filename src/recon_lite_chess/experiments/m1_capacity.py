"""Paired capacity-budget probe using the unchanged ordinary M1 learner.

The sole treatment is max_conditions. No diagnostic labels or fitted weights
are inputs. The loader below verifies trusted historical checkpoints only.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import copy
from dataclasses import asdict, replace
import json
import multiprocessing
from pathlib import Path
import time

from . import ordinary_m1 as prior
from .m1_representation import restore_actor


def compare(actor, fens, validation, order, *, event, caps, deadline, private, manifest, seed):
    inherited = prior.actor_digest(actor)
    shadow = prior.digest(actor.shadow.report())
    arms = {}
    for cap in caps:
        clone = copy.deepcopy(actor)
        clone.config = replace(clone.config, max_conditions=cap)
        directory = private/f'cap-{cap}'
        directory.mkdir()
        state = {'seed': seed, 'role_index': 0, 'next_event': event, 'organism': clone}
        before = prior.snapshot(clone)
        prior.save_checkpoint(directory, state, manifest)
        blocks = []
        for offset in range(0, len(order), 128):
            block = order[offset:offset+128]
            training = prior.train(clone, fens, block, start_event=event+offset, deadline=deadline)
            blocks.append(training)
            state['next_event'] = event+offset+len(block)
            prior.save_checkpoint(directory, state, manifest)
        evaluated = prior.evaluate(clone, validation, role='none', deadline=deadline)
        if prior.digest(clone.shadow.report()) != shadow:
            raise RuntimeError('frozen nomination history changed')
        pointer = prior.save_checkpoint(directory, state, manifest)
        restored = prior.load_checkpoint(directory, manifest, seed)['organism']
        if prior.actor_digest(restored) != prior.actor_digest(clone):
            raise RuntimeError('capacity checkpoint changed actor')
        arms[str(cap)] = {'config': asdict(clone.config), 'before': before, 'blocks': blocks,
                          'after': evaluated, 'checkpoint_sha256': pointer['sha256']}
    if prior.actor_digest(actor) != inherited:
        raise RuntimeError('comparison changed the inherited actor')
    if len({a['after']['exploration_rng_digest'] for a in arms.values()}) != 1:
        raise RuntimeError('exploration streams diverged')
    return {'inherited_actor_digest': inherited, 'inherited_state_unchanged': True,
            'exploration_streams_match': True, 'arms': arms}


def run_seed(task):
    seed, reference, previous, private_source, output, private, manifest, fens, validation = task
    started = time.monotonic(); deadline = started+manifest['wall_seconds_per_seed']
    directory = Path(private)/f'seed-{seed}'; directory.mkdir()
    try:
        actor, sha = restore_actor(reference, Path(previous), Path(private_source), seed, 'none', 1024)
        if actor.config.max_conditions != 32:
            raise ValueError('expected original 32-condition actor')
        result = compare(actor, fens, validation, manifest['plans'][str(seed)], event=1024,
                         caps=(32, 64), deadline=deadline, private=directory, manifest=manifest, seed=seed)
        if time.monotonic() >= deadline:
            raise TimeoutError('capacity probe time cap expired')
        result.update(seed=seed, status='complete', source_checkpoint_sha256=sha,
                      wall_seconds=time.monotonic()-started)
        prior.atomic_json(Path(output)/f'seed-{seed}.json', result)
        print(json.dumps({'seed': seed, 'mates': {cap: a['after']['evaluation']['mates'] for cap, a in result['arms'].items()}}), flush=True)
        return result
    except BaseException as error:
        # No silent retry. Checkpoints retain completed training boundaries;
        # uncommitted work must be accounted separately if this attempt fails.
        prior.atomic_json(Path(output)/f'failure-{seed}.json', {'status': 'incomplete', 'error': str(error),
            'note': 'Completed training checkpoints retained; any uncommitted block/evaluation is additional uncertain work.'})
        raise


def run(args):
    reference = prior.read(args.reference)
    if reference['status'] != 'complete' or reference['manifest']['source'] != prior.sources():
        raise ValueError('complete source-matched reference required')
    fens, train_sha = prior.load_split(args.pool, 'train')
    validation, val_sha = prior.load_split(args.pool, 'validation')
    if (train_sha, val_sha) != (reference['manifest']['train_sha256'], reference['manifest']['validation_sha256']):
        raise ValueError('original pools required')
    plans = {str(seed): list(prior.prior.prior.schedule_indices(len(fens), 1280, seed))[1024:]
             for seed in (2, 3)}
    manifest = {'schema': 'm1_capacity.v1', 'source': prior.sources(), 'runner_sha256': prior.sha(__file__),
                'checkpoint_loader_sha256': prior.sha(Path(__file__).with_name('m1_representation.py')),
                'reference_sha256': prior.sha(args.reference), 'seeds': [2, 3], 'role': 'none',
                'caps': [32, 64], 'start_event': 1024, 'end_event': 1280, 'plans': plans,
                'train_sha256': train_sha, 'validation_sha256': val_sha,
                'training_moves': 1024, 'evaluation_moves': 4*len(validation), 'workers': 2,
                'wall_seconds_per_seed': 900, 'final_test_opened': False,
                'limits': ['Two development-selected seeds; exploratory capacity test, not independent confirmation.',
                           'Only max_conditions changes; birth, pruning, credit, features and rewards are unchanged.',
                           'No diagnostic answers or fitted weights enter the learner.',
                           'More random capacity is not adaptive structural selection.']}
    args.output.mkdir(parents=True, exist_ok=False)
    args.private.mkdir(parents=True, exist_ok=False, mode=0o700)
    prior.atomic_json(args.output/'manifest.json', manifest)
    tasks = [(seed, reference, str(args.previous), str(args.private_source), str(args.output),
              str(args.private), manifest, fens, validation) for seed in (2, 3)]
    with ProcessPoolExecutor(max_workers=2, mp_context=multiprocessing.get_context('spawn')) as executor:
        results = list(executor.map(run_seed, tasks))
    assert sum(b['real_moves'] for r in results for a in r['arms'].values() for b in a['blocks']) == 1024
    result = {'status': 'complete', 'manifest': manifest, 'actual_training_moves': 1024,
              'actual_evaluation_moves': 4*len(validation), 'results': results}
    prior.atomic_json(args.output/'summary.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('pool', 'reference', 'previous', 'private-source', 'output', 'private'):
        parser.add_argument('--'+name, type=Path, required=True)
    print(json.dumps({'status': run(parser.parse_args())['status']}))
