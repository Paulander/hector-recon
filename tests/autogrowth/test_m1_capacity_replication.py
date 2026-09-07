"""The replication changes schedules/budgets, never the learner's information."""
import argparse
import inspect
from pathlib import Path
import time

import chess
import pytest

from recon_lite_chess.coach.pools import prepare
from recon_lite_chess.coach.terminal import ChessFeaturePort
from recon_lite_chess.experiments import m1_capacity_replication as experiment
from recon_lite_hector.learning.terminal_development import _reader


def small_manifest(original, *args, **kwargs):
    manifest = original(*args, **kwargs)
    for spec in manifest['plans'].values():
        spec['actor_config'].update(max_conditions=2, births_per_episode=1, grace_episodes=4)
        spec['shadow_config'].update(candidates=4, discovery_episodes=2, min_support=1)
        spec.update(after_episode=3, recovery_after=4, order=spec['order'][:12])
    manifest.update(split_event=8, end_event=12, block=4, prefix_evaluations=[4, 8],
                    caps=[2, 4], training_moves=16, evaluation_moves=8)
    return manifest


def test_fresh_replication_opaque_actual_play_fixed_schedule_and_restore(tmp_path, monkeypatch):
    import recon_lite_chess.experiments.m1_representation as diagnosis
    pool = tmp_path / 'pool'
    prepare(pool, seed=43, train=4, validation=2, test=2)
    original_manifest = experiment.build_manifest
    monkeypatch.setattr(experiment, 'build_manifest',
        lambda *a, **kw: small_manifest(original_manifest, *a, **kw))
    def forbidden(*args, **kwargs):
        raise AssertionError('diagnostic answers must not enter this experiment')
    for name in ('laboratory_rows', 'inspect_actor', 'ranking_feasibility', 'restore_actor'):
        monkeypatch.setattr(diagnosis, name, forbidden)
    original_measure = ChessFeaturePort.measure
    def measure(port, coordinate, binding):
        assert inspect.currentframe().f_back.f_code is _reader.__code__
        return original_measure(port, coordinate, binding)
    monkeypatch.setattr(ChessFeaturePort, 'measure', measure)
    pushes, original_push = [], chess.Board.push
    def push(board, move):
        pushes.append(move)
        return original_push(board, move)
    monkeypatch.setattr(chess.Board, 'push', push)
    original_read = Path.read_bytes
    def read(path):
        assert path.name != 'test.txt'
        return original_read(path)
    monkeypatch.setattr(Path, 'read_bytes', read)
    args = argparse.Namespace(pool=pool, output=tmp_path / 'public', private=tmp_path / 'private',
                              seeds=[4], workers=1, wall_seconds=90)
    result = experiment.run(args)
    assert result['status'] == 'complete'
    assert result['actual_training_moves'] == 16
    assert result['actual_evaluation_moves'] == 8
    assert len(pushes) == 24
    assert result['manifest']['final_test_opened'] is False
    seed = result['results'][0]
    assert set(seed['milestones']) == {'4', '8'}
    assert all(m['checkpoint_reloaded'] for m in seed['milestones'].values())
    paired = seed['comparison']
    assert paired['inherited_state_unchanged'] and paired['exploration_streams_match']
    assert paired['arms']['2']['config'] | {'max_conditions': 4} == paired['arms']['4']['config']
    for cap, arm in paired['arms'].items():
        assert arm['after']['evaluation']['learned_state_unchanged']
        state = experiment.prior.load_checkpoint(args.private / f'seed-4/cap-{cap}', result['manifest'], 4)
        assert state['next_event'] == state['organism'].completed == 12
        assert not state['organism'].hold_topology
        assert state['organism'].trial_condition is None
    # Evaluation and actual checkpoint reloads cannot teach the 2-budget control.
    fens, _ = experiment.prior.load_split(pool, 'train')
    spec = result['manifest']['plans']['4']
    continuous = experiment.prior.new_actor(4, 'none', spec)
    experiment.prior.train(continuous, fens, spec['order'], start_event=0, deadline=time.monotonic()+30)
    saved = experiment.prior.load_checkpoint(args.private / 'seed-4/cap-2', result['manifest'], 4)['organism']
    assert experiment.prior.actor_digest(continuous) == experiment.prior.actor_digest(saved)
    with pytest.raises(FileExistsError):
        experiment.run(args)


def test_manifest_fixes_late_intervention_counts_and_rejects_reused_seeds(tmp_path):
    pool = tmp_path / 'pool'
    prepare(pool, seed=43, train=4, validation=2, test=2)
    fens, train_sha = experiment.prior.load_split(pool, 'train')
    validation, validation_sha = experiment.prior.load_split(pool, 'validation')
    args = (fens, validation, train_sha, validation_sha)
    manifest = experiment.build_manifest([4, 5, 6, 7, 8, 9], *args, workers=6, wall_seconds=2400)
    assert manifest['training_moves'] == 9216
    assert manifest['evaluation_moves'] == 48  # Tiny two-row development fixture.
    assert manifest['caps'] == [32, 64] and manifest['prefix_evaluations'] == [384, 1024]
    assert all(len(spec['order']) == 1280 and spec['actor_config']['learning_rate'] == 0.3
               and spec['actor_config']['max_conditions'] == 32 for spec in manifest['plans'].values())
    for seeds in ([1, 4], [4, 4], []):
        with pytest.raises(ValueError, match='fresh seeds'):
            experiment.build_manifest(seeds, *args, workers=6, wall_seconds=2400)
    with pytest.raises(ValueError, match='orbits overlap'):
        experiment.build_manifest([4], fens, fens, train_sha, train_sha, workers=1, wall_seconds=90)
