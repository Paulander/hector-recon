"""A continuation must preserve its source and learn only from actual play."""
import argparse
import copy
from dataclasses import asdict
import inspect
from pathlib import Path
import time

import chess
import pytest

from recon_lite_chess.coach.pools import prepare
from recon_lite_chess.coach.terminal import ChessFeaturePort
from recon_lite_chess.experiments import m1_long_play as experiment
from recon_lite_hector.learning.terminal_development import _reader, DevelopmentConfig
from recon_lite_hector.learning.residual_shadow import ShadowConfig


def source(tmp_path):
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
    manifest = {'source': experiment.prior.sources(), 'seeds': [4], 'caps': [2, 4],
                'end_event': 12, 'plans': {'4': spec},
                'train_sha256': train_sha, 'validation_sha256': validation_sha}
    private = tmp_path / 'source'
    directory = private / 'seed-4/cap-4'
    directory.mkdir(parents=True)
    pointer = experiment.prior.save_checkpoint(directory, {
        'seed': 4, 'role_index': 0, 'next_event': 12, 'organism': actor}, manifest)
    reference = {'status': 'complete', 'manifest': manifest, 'results': [
        {'seed': 4, 'comparison': {'arms': {'4': {'config': asdict(actor.config),
         'after': evaluated, 'checkpoint_sha256': pointer['sha256']}}}}]}
    path = tmp_path / 'reference.json'
    experiment.prior.atomic_json(path, {'run': reference})
    return pool, private, path, actor


def args_for(tmp_path, pool, private, reference):
    return argparse.Namespace(pool=pool, private_source=private, reference=reference,
        output=tmp_path / 'output', private=tmp_path / 'saved', episodes=20,
        evaluate_at=[16, 20], block=4, workers=1, wall_seconds=90)


def test_continuation_counts_actual_moves_obeys_terminal_boundary_and_matches_continuous_play(tmp_path, monkeypatch):
    pool, private, reference, original = source(tmp_path)
    source_files = {p: p.read_bytes() for p in private.rglob('*') if p.is_file()}
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
    read = Path.read_bytes
    def read_bytes(path):
        assert path.name != 'test.txt'
        return read(path)
    monkeypatch.setattr(Path, 'read_bytes', read_bytes)
    def forbidden(*args, **kwargs):
        raise AssertionError('continuation must load its saved actor, not construct another')
    monkeypatch.setattr(experiment.prior, 'new_actor', forbidden)
    args = args_for(tmp_path, pool, private, reference)
    result = experiment.run(args)
    assert result['status'] == 'complete' and requests
    assert result['actual_training_moves'] == 8 and result['actual_evaluation_moves'] == 4
    assert len(pushes) == 12 and result['manifest']['seeds'] == [4]
    seed = result['results'][0]
    assert seed['config'] == asdict(original.config)
    assert seed['settings_and_completed_history_unchanged']
    assert list(seed['milestones']) == ['16', '20']
    assert all(m['checkpoint_reloaded'] and m['result']['evaluation']['learned_state_unchanged']
               for m in seed['milestones'].values())
    assert source_files == {p: p.read_bytes() for p in private.rglob('*') if p.is_file()}
    restored = experiment.prior.load_checkpoint(args.private / 'seed-4', result['manifest'], 4)['organism']
    fens, _ = experiment.prior.load_split(pool, 'train')
    uninterrupted = copy.deepcopy(original)
    experiment.prior.train(uninterrupted, fens, result['manifest']['plans']['4'][12:],
                           start_event=12, deadline=time.monotonic()+30)
    assert experiment.prior.actor_digest(restored) == experiment.prior.actor_digest(uninterrupted)
    with pytest.raises(FileExistsError):
        experiment.run(args)


def test_changed_source_or_schedule_rejected_instead_of_selecting_another_checkpoint(tmp_path):
    pool, private, reference_path, _ = source(tmp_path)
    reference = experiment.prior.read(reference_path)['run']
    changed = copy.deepcopy(reference)
    changed['results'][0]['comparison']['arms']['4']['checkpoint_sha256'] = '0'*64
    with pytest.raises(ValueError, match='published final checkpoint'):
        experiment.restore_source(changed, private, 4)
    changed = copy.deepcopy(reference)
    changed['results'][0]['comparison']['arms']['4']['config']['learning_rate'] = 0.1
    with pytest.raises(ValueError, match='learned state differs'):
        experiment.restore_source(changed, private, 4)
    fens, th = experiment.prior.load_split(pool, 'train')
    validation, vh = experiment.prior.load_split(pool, 'validation')
    changed = copy.deepcopy(reference)
    changed['manifest']['plans']['4']['order'][0] = -1
    with pytest.raises(ValueError, match='inherited prefix'):
        experiment.make_manifest(changed, fens, validation, th, vh, end_event=20,
            evaluations=[16,20], block=4, workers=1, wall_seconds=90, reference_sha='fixture')
    with pytest.raises(ValueError, match='ordered fixed milestones'):
        experiment.make_manifest(reference, fens, validation, th, vh, end_event=20,
            evaluations=[20,16], block=4, workers=1, wall_seconds=90, reference_sha='fixture')


def test_interrupted_actual_play_preserves_last_boundary_and_unfinished_move_budget(tmp_path, monkeypatch):
    pool, private, reference, _ = source(tmp_path)
    args = args_for(tmp_path, pool, private, reference)
    train = experiment.prior.train
    def interrupted(actor, fens, order, **kwargs):
        train(actor, fens, order[:1], **kwargs)
        raise RuntimeError('fixture interruption after an actual action')
    monkeypatch.setattr(experiment.prior, 'train', interrupted)
    with pytest.raises(RuntimeError, match='fixture interruption'):
        experiment.run(args)
    failure = experiment.prior.read(args.output / 'failure-4.json')
    assert failure['unfinished_unit'] == {'kind':'training','start':12,'end':16,'max_moves':4}
    assert not failure['completed_blocks'] and not (args.output / 'summary.json').exists()
    manifest = experiment.prior.read(args.output / 'manifest.json')
    state = experiment.prior.load_checkpoint(args.private / 'seed-4', manifest, 4)
    assert state['next_event'] == state['organism'].completed == 12
