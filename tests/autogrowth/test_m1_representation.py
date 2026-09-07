"""Laboratory checks; planted structures are never a chess training input."""
import copy
import inspect
import time
from types import SimpleNamespace

import pytest

from recon_lite_chess.coach.terminal import ChessFeaturePort
from recon_lite_chess.experiments import m1_representation as diagnosis
from recon_lite_chess.experiments.fixed_topology_recovery import RecoveryTrial
from recon_lite_hector.learning.terminal_development import Condition, DevelopmentConfig
from recon_lite_hector.learning.live_trial import TrialConfig
from recon_lite_hector.learning.residual_shadow import ShadowConfig


@pytest.mark.parametrize('operator,expected', [('and', 1), ('or', 1), ('xor', 0)])
def test_three_reader_boolean_semantics(operator, expected):
    c = SimpleNamespace(operator=operator, atoms=((0, True), (1, True), (2, True)))
    assert diagnosis.gate_value(c, (True, True, True)) == expected


def test_alias_bound_respects_runtime_slot_tie_and_is_not_a_global_attainability_claim():
    row = {'wins': [1, 0]}
    assert diagnosis.alias_summary([row], [[(0,), (0,)]])['unavoidable_failures_with_existing_tie'] == 1
    assert diagnosis.alias_summary([row], [[(0,), (1,)]])['unavoidable_failures_with_existing_tie'] == 0
    # Reversing the labels permits a favorable tie even without information.
    assert diagnosis.alias_summary([{'wins': [0, 1]}], [[(0,), (0,)]])['unavoidable_failures_with_existing_tie'] == 0
    wins = [0]*11; wins[9] = 1
    assert diagnosis.alias_summary([{'wins': wins}], [[(0,)]*11])['local_signature_upper_bound_mates'] == 1


def test_offline_feasibility_detects_joint_boolean_need_without_returning_coefficients():
    # XOR is indistinguishable to a linear sum of two raw Boolean readers.
    rows = [{'wins': [0, 1, 1, 0]}]
    atoms = [[(0, 0), (0, 1), (1, 0), (1, 1)]]
    composed = [[(0,), (1,), (1,), (0,)]]
    deadline = time.monotonic()+10
    a = diagnosis.ranking_feasibility(rows, atoms, deadline=deadline)
    b = diagnosis.ranking_feasibility(rows, composed, deadline=deadline)
    assert not a['strict_all_winners_rankable'] and b['strict_all_winners_rankable']
    assert b['fitted_weights_discarded'] and 'weights' not in b and 'x' not in b


def test_lab_replay_reads_through_terminals_counts_moves_and_never_learns(monkeypatch):
    original = ChessFeaturePort.measure
    def measure(port, coordinate, binding):
        assert inspect.currentframe().f_back.f_code is diagnosis._reader.__code__
        return original(port, coordinate, binding)
    monkeypatch.setattr(ChessFeaturePort, 'measure', measure)
    fens = ['7k/5K2/8/8/8/8/8/R7 w - - 0 1', 'k7/2K5/8/8/8/8/8/7R w - - 0 1']
    counts = {'laboratory_transitions': 0, 'actor_evaluation_moves': 0, 'actor_actions_started': 0}
    deadline = time.monotonic()+30
    rows = diagnosis.laboratory_rows(fens, deadline=deadline, counts=counts)
    assert counts['laboratory_transitions'] == sum(len(r['bindings']) for r in rows)
    actor = RecoveryTrial(seed=3, recovery_after=256, config=DevelopmentConfig(max_conditions=4),
                          trial_config=TrialConfig('none', 128), shadow_config=ShadowConfig())
    actor.schema = ChessFeaturePort.schema
    for cid, (operator, atoms, weight) in enumerate([
            ('and', ((1, True),), -.4), ('or', ((0, False), (1, True)), .2),
            ('xor', ((10, True), (11, True), (1, False)), -.3)]):
        c = Condition(cid, atoms, operator, 0); c.weight.fast = weight
        actor.conditions[cid] = c; actor.next_condition += 1
    def forbidden(*args, **kwargs):
        raise AssertionError('diagnostic must not call observe or change topology')
    monkeypatch.setattr(actor, 'observe', forbidden)
    monkeypatch.setattr(actor, '_birth', forbidden)
    monkeypatch.setattr(actor, '_prune', forbidden)
    before = diagnosis.prior.actor_digest(actor)
    result = diagnosis.inspect_actor(actor, rows, deadline=deadline, counts=counts)
    assert result['formal_support_and_choice_match'] and result['learned_state_unchanged']
    assert diagnosis.prior.actor_digest(actor) == before
    assert counts['actor_evaluation_moves'] == counts['actor_actions_started'] == 2


def test_checkpoint_source_rejected_before_unpickling(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('must reject before reading pickle')
    monkeypatch.setattr(diagnosis.pickle, 'load', forbidden)
    source = copy.deepcopy(diagnosis.prior.sources()); source['runner_sha256'] = 'different'
    with pytest.raises(ValueError, match='runtime/source'):
        diagnosis.restore_actor({'manifest': {'source': source}}, tmp_path, tmp_path, 3, 'none', 1024)


def test_expired_diagnostic_budget_stops_before_grading():
    with pytest.raises(TimeoutError):
        diagnosis.laboratory_rows(['not-read'], deadline=time.monotonic()-1)
