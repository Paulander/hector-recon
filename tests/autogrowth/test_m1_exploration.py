"""Exploration alone changes, with truthful actual-action logs and frozen evaluation."""
import argparse
import copy
from dataclasses import asdict, replace
import inspect
import json
from pathlib import Path
import time

import chess
import pytest

from recon_lite_chess.coach.pools import prepare
from recon_lite_chess.coach.terminal import ChessFeaturePort
from recon_lite_chess.experiments import m1_exploration as experiment
from recon_lite_hector.learning.terminal_development import _reader, DevelopmentConfig
from recon_lite_hector.learning.residual_shadow import ShadowConfig


def fixture(tmp_path):
    pool = tmp_path / 'pool'
    prepare(pool, seed=43, train=4, validation=2, test=2)
    fens, train_sha = experiment.prior.load_split(pool, 'train')
    validation, validation_sha = experiment.prior.load_split(pool, 'validation')
    order = list(experiment.prior.prior.prior.schedule_indices(4, 12, 4))
    spec = {'actor_config': asdict(DevelopmentConfig(max_conditions=4, grace_episodes=4)),
            'shadow_config': asdict(ShadowConfig(candidates=4, discovery_episodes=2, min_support=1)),
            'after_episode': 3, 'recovery_after': 4, 'order': order}
    actor = experiment.prior.new_actor(4, 'none', spec)
    experiment.prior.train(actor, fens, order, start_event=0, deadline=time.monotonic()+60)
    evaluated = experiment.prior.evaluate(actor, validation, role='none', deadline=time.monotonic()+60)
    manifest = {'source': experiment.prior.sources(), 'seeds': [4], 'end_event': 12,
                'plans': {'4': order}, 'train_sha256': train_sha, 'validation_sha256': validation_sha}
    private = tmp_path / 'source'
    directory = private / 'seed-4'
    directory.mkdir(parents=True)
    pointer = experiment.prior.save_checkpoint(directory, {
        'seed': 4, 'role_index': 0, 'next_event': 12, 'organism': actor}, manifest)
    reference = {'status': 'complete', 'manifest': manifest, 'results': [
        {'seed': 4, 'config': asdict(actor.config), 'milestones': {'12': {
            'result': evaluated, 'checkpoint_sha256': pointer['sha256']}}}]}
    path = tmp_path / 'reference.json'
    experiment.prior.atomic_json(path, {'run': reference})
    args = argparse.Namespace(pool=pool, private_source=private, reference=path, seeds=[4],
        output=tmp_path/'output', private=tmp_path/'saved', episodes=20,
        evaluate_at=[16,20], block=4, workers=1, wall_seconds=90)
    return args, actor, fens, validation


def test_paired_run_only_changes_exploration_logs_real_feedback_and_keeps_boundary(tmp_path, monkeypatch):
    args, original, fens, _ = fixture(tmp_path)
    inherited = experiment.prior.actor_digest(original)
    source_files = {p: p.read_bytes() for p in args.private_source.rglob('*') if p.is_file()}
    requests, measure = [], ChessFeaturePort.measure
    def measured(port, coordinate, binding):
        assert inspect.currentframe().f_back.f_code is _reader.__code__
        requests.append(coordinate)
        return measure(port, coordinate, binding)
    monkeypatch.setattr(ChessFeaturePort, 'measure', measured)
    pushes, push = [], chess.Board.push
    def pushed(board, move):
        pushes.append(move)
        return push(board, move)
    monkeypatch.setattr(chess.Board, 'push', pushed)
    read_bytes = Path.read_bytes
    def reading(path):
        assert path.name != 'test.txt'
        return read_bytes(path)
    monkeypatch.setattr(Path, 'read_bytes', reading)
    def forbidden(*args, **kwargs):
        raise AssertionError('must restore source; no replacement learner')
    monkeypatch.setattr(experiment.prior, 'new_actor', forbidden)
    result = experiment.run(args)
    assert requests and result['actual_training_moves'] == 16 and result['actual_evaluation_moves'] == 8
    assert len(pushes) == 24
    assert source_files == {p: p.read_bytes() for p in args.private_source.rglob('*') if p.is_file()}
    assert experiment.prior.actor_digest(original) == inherited
    assert {r['inherited_actor_digest'] for r in result['results']} == {inherited}
    for arm in result['results']:
        rate = arm['exploration']
        directory = args.private / f'seed-4/exploration-{rate:.2f}'
        rows = [json.loads(s) for s in (directory/'training-actions.jsonl').read_text().splitlines()]
        assert [r['event'] for r in rows] == list(range(12,20))
        assert [r['pool_index'] for r in rows] == result['manifest']['plans']['4'][12:]
        assert sum(r['reward'] > 0 for r in rows) == sum(b['training']['mates'] for b in arm['blocks'])
        assert all(r['action'] and r['real_moves'] == 1 and r['reward'] in (-1,1) for r in rows)
        assert arm['config'] == asdict(original.config) | {'exploration': rate}
        assert arm['sole_config_treatment_verified'] and arm['inherited_state_unchanged']
        assert all(m['checkpoint_reloaded'] and m['result']['evaluation']['learned_state_unchanged']
                   for m in arm['milestones'].values())
        clone = copy.deepcopy(original)
        clone.config = replace(clone.config, exploration=rate)
        ordinary = experiment.prior.train(clone, fens, result['manifest']['plans']['4'][12:],
            start_event=12, deadline=time.monotonic()+30)
        restored = experiment.prior.load_checkpoint(directory, result['manifest'], 4)['organism']
        assert ordinary['mates'] == sum(r['reward'] > 0 for r in rows)
        assert experiment.prior.actor_digest(clone) == experiment.prior.actor_digest(restored)
    with pytest.raises(FileExistsError):
        experiment.run(args)


@pytest.mark.parametrize('rate', [0.25, 0.5])
def test_logging_matches_existing_coach_transcript_and_learning_exactly(tmp_path, rate):
    _, original, fens, _ = fixture(tmp_path)
    original.config = replace(original.config, exploration=rate)
    logged, ordinary = copy.deepcopy(original), copy.deepcopy(original)
    order = [0,1,2,3,2,1,0,3]
    with (tmp_path/'actions.jsonl').open('x') as stream:
        report = experiment.train_logged(logged, fens, order, start_event=12,
            deadline=time.monotonic()+30, stream=stream)
    control = experiment.prior.train(ordinary, fens, order, start_event=12, deadline=time.monotonic()+30)
    assert report == control
    assert experiment.prior.actor_digest(logged) == experiment.prior.actor_digest(ordinary)


def test_wrong_source_or_schedule_rejected(tmp_path):
    args, _, fens, validation = fixture(tmp_path)
    reference = experiment.prior.read(args.reference)['run']
    bad = copy.deepcopy(reference)
    bad['results'][0]['milestones']['12']['checkpoint_sha256'] = '0'*64
    with pytest.raises(ValueError, match='published final checkpoint'):
        experiment.restore_source(bad, args.private_source, 4)
    bad = copy.deepcopy(reference)
    bad['results'][0]['config']['learning_rate'] = .1
    with pytest.raises(ValueError, match='learned state'):
        experiment.restore_source(bad, args.private_source, 4)
    bad = copy.deepcopy(reference)
    bad['manifest']['plans']['4'][0] = -1
    kwargs = dict(seeds=[4], end_event=20, evaluations=[16,20], block=4,
                  workers=1, wall_seconds=90, reference_sha='fixture')
    old = reference['manifest']
    with pytest.raises(ValueError, match='inherited prefix'):
        experiment.make_manifest(bad, fens, validation, old['train_sha256'], old['validation_sha256'], **kwargs)
    for changes in ({'seeds':[4,4]}, {'evaluations':[20,16]}, {'end_event':12}):
        with pytest.raises(ValueError):
            experiment.make_manifest(reference, fens, validation, old['train_sha256'],
                                     old['validation_sha256'], **(kwargs | changes))


def test_partial_block_preserves_submitted_behavior_and_prior_boundary(tmp_path, monkeypatch):
    args, _, _, _ = fixture(tmp_path)
    train = experiment.train_logged
    def interrupted(actor, fens, order, **kwargs):
        train(actor, fens, order[:1], **kwargs)
        raise RuntimeError('fixture stops after completed reward')
    monkeypatch.setattr(experiment, 'train_logged', interrupted)
    with pytest.raises(RuntimeError, match='fixture stops'):
        experiment.run(args)
    out = args.output / 'seed-4/exploration-0.25'
    failure = experiment.prior.read(out/'failure-4.json')
    assert failure['unfinished_unit'] == {'kind':'training','start':12,'end':16,'max_moves':4}
    directory = args.private / 'seed-4/exploration-0.25'
    rows = [json.loads(s) for s in (directory/'training-actions.jsonl').read_text().splitlines()]
    assert len(rows) == 1 and rows[0]['event'] == 12 and rows[0]['real_moves'] == 1
    manifest = experiment.prior.read(args.output/'manifest.json')
    assert experiment.prior.load_checkpoint(directory, manifest, 4)['next_event'] == 12
    assert not (args.output/'summary.json').exists()


def test_parallel_results_match_serial_history_and_evaluation(tmp_path):
    args, _, _, _ = fixture(tmp_path)
    serial = experiment.run(args)
    args.output, args.private, args.workers = tmp_path/'parallel', tmp_path/'parallel-private', 2
    parallel = experiment.run(args)
    for a,b in zip(serial['results'], parallel['results']):
        assert a['config'] == b['config'] and a['blocks'] == b['blocks']
        assert a['transcript_sha256'] == b['transcript_sha256']
        assert {k:v['result'] for k,v in a['milestones'].items()} == {
            k:v['result'] for k,v in b['milestones'].items()}
