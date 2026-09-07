from dataclasses import asdict
import inspect
import time

from recon_lite_chess.coach.terminal import ChessFeaturePort
from recon_lite_chess.experiments import m1_capacity as experiment
from recon_lite_chess.experiments.fixed_topology_recovery import RecoveryTrial
from recon_lite_hector.learning.terminal_development import DevelopmentConfig
from recon_lite_hector.learning.live_trial import TrialConfig
from recon_lite_hector.learning.residual_shadow import ShadowConfig


def test_capacity_is_the_only_treatment_with_opaque_play_matched_exploration_and_checkpoints(tmp_path, monkeypatch):
    import recon_lite_chess.experiments.m1_representation as diagnosis
    def forbidden(*args, **kwargs):
        raise AssertionError('diagnostic answers must not enter this experiment')
    for name in ('laboratory_rows', 'inspect_actor', 'ranking_feasibility'):
        monkeypatch.setattr(diagnosis, name, forbidden)
    original = ChessFeaturePort.measure
    def measure(port, coordinate, binding):
        assert inspect.currentframe().f_back.f_code is diagnosis._reader.__code__
        return original(port, coordinate, binding)
    monkeypatch.setattr(ChessFeaturePort, 'measure', measure)
    actor = RecoveryTrial(seed=3, recovery_after=3,
        config=DevelopmentConfig(max_conditions=2, births_per_episode=1, grace_episodes=4),
        trial_config=TrialConfig('none', 3),
        shadow_config=ShadowConfig(candidates=4, discovery_episodes=2, min_support=1))
    fens = ['7k/5K2/8/8/8/8/8/R7 w - - 0 1', 'k7/2K5/8/8/8/8/8/7R w - - 0 1']
    deadline = time.monotonic()+30
    experiment.prior.train(actor, fens, [0, 1]*3, start_event=0, deadline=deadline)
    config = asdict(actor.config)
    manifest = {'source': experiment.prior.sources(), 'fixture': True}
    result = experiment.compare(actor, fens, fens, [0, 1]*4, event=6, caps=(2, 4),
                                deadline=deadline, private=tmp_path, manifest=manifest, seed=3)
    assert result['inherited_state_unchanged'] and result['exploration_streams_match']
    for cap, arm in result['arms'].items():
        assert arm['config'] == config | {'max_conditions': int(cap)}
        assert sum(b['real_moves'] for b in arm['blocks']) == 8
        assert arm['after']['lifecycle']['completed'] == 14
        assert arm['after']['evaluation']['count'] == 2
        assert arm['after']['evaluation']['learned_state_unchanged']
        restored = experiment.prior.load_checkpoint(tmp_path/f'cap-{cap}', manifest, 3)['organism']
        assert restored.completed == 14 and restored.config.max_conditions == int(cap)
    assert result['arms']['4']['after']['lifecycle']['births'] > result['arms']['2']['after']['lifecycle']['births']
