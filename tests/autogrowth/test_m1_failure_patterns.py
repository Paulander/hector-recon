"""Offline attribution fixtures, never supplied to chess training."""
import copy
from dataclasses import asdict
import inspect
import json
import time
from types import SimpleNamespace

import chess
import pytest

from recon_lite_chess.experiments import m1_failure_patterns as e
from recon_lite_chess.experiments.fixed_topology_recovery import RecoveryTrial
from recon_lite_hector.learning.terminal_development import Condition, DevelopmentConfig
from recon_lite_hector.learning.live_trial import TrialConfig
from recon_lite_hector.learning.residual_shadow import ShadowConfig

FENS = ('7k/5K2/8/8/8/8/8/R7 w - - 0 1', 'k7/2K5/8/8/8/8/8/7R w - - 0 1')


def actor():
    result = RecoveryTrial(seed=7, recovery_after=256, config=DevelopmentConfig(max_conditions=4),
        trial_config=TrialConfig('none', 128), shadow_config=ShadowConfig(candidates=4))
    result.schema = e.d.ChessFeaturePort.schema
    for cid, (atoms, weight) in enumerate([(((0, True),), .3), (((1, True),), -.2),
                                          (((10, True), (12, True)), .7)]):
        c = Condition(cid, atoms, 'and', 0); c.weight.fast = weight
        result.conditions[cid] = c; result.next_condition += 1
    result._ensure_slots(1)
    result._init_shadow()
    return result


def test_preserved_success_repair_distinguishes_ordering_room_from_composition_conflict():
    rows = [{'wins': [1, 0]}, {'wins': [0, 1]}, {'wins': [1, 0]}]
    # Row 1 contradicts the retained row 0. Row 2 has an independent coordinate.
    matrices = [[(1, 0), (0, 0)], [(1, 0), (0, 0)], [(0, 1), (0, 0)]]
    r = e.repair_room(rows, matrices, [1, 0, 0], deadline=time.monotonic()+20)
    assert r['1']['can_add_without_losing_current_success'] is False
    assert r['1']['proof']['solver_independent_impossibility_witness']
    assert r['2']['can_add_without_losing_current_success'] is True
    assert all(x['proof']['fitted_weights_discarded'] for x in r.values())
    assert all('x' not in x['proof'] and 'weights' not in x['proof'] for x in r.values())


def test_profile_separates_action_invariance_from_inactivity():
    a = actor()
    # Coordinate 0 true on both alternatives, coordinate 1 varies, third inactive.
    traces = [{'matrix': [(1, 0, 0), (1, 1, 0)], 'chosen': 1}]
    result = e.profile(a, traces, 1280)
    assert result['action_invariant_on_examined_rows'] == 2
    assert result['never_active_on_examined_rows'] == 1
    assert result['action_discriminating_on_examined_rows'] == 1
    assert result['mean_selected_active_conditions'] == 2


def test_margin_decomposition_includes_lost_and_born_conditions():
    old = actor(); new = copy.deepcopy(old)
    new.conditions[1].weight.fast += .4
    del new.conditions[2]
    born = Condition(3, ((1, True),), 'and', 3); born.weight.fast = .6
    new.conditions[3] = born
    row = {'wins': [1, 0], 'vectors': [(True, True, False, False, False, False, False, False, False, False, True, False, True),
                                    (True, False, False, False, False, False, False, False, False, False, True, False, False)]}
    def trace(a):
        return {'chosen': 1, 'scores': [sum(float(c.weight)*e.d.gate_value(c, v) for c in a.conditions.values()) for v in row['vectors']]}
    r = e.margin_change(old, new, row, trace(old), trace(new))
    assert r['retained_weight_change'] == pytest.approx(.4)
    assert r['removed_contribution_change'] == pytest.approx(-.7)
    assert r['new_contribution_change'] == pytest.approx(.6)
    assert r['accounting_matches']


def test_new_diagnostic_counts_every_push_uses_terminals_and_never_learns(monkeypatch):
    pushes = []
    original_push, original_measure = chess.Board.push, e.d.ChessFeaturePort.measure
    def push(board, move):
        pushes.append(move)
        return original_push(board, move)
    def measure(port, coordinate, binding):
        assert inspect.currentframe().f_back.f_code is e.d._reader.__code__
        return original_measure(port, coordinate, binding)
    monkeypatch.setattr(chess.Board, 'push', push)
    monkeypatch.setattr(e.d.ChessFeaturePort, 'measure', measure)
    counts = {'laboratory_transitions': 0, 'actor_evaluation_moves': 0, 'actor_actions_started': 0}
    deadline = time.monotonic()+30
    rows = e.laboratory_rows(FENS, deadline=deadline, counts=counts)
    a = actor(); before = e.prior.actor_digest(a)
    def forbidden(*args, **kwargs):
        raise AssertionError('offline diagnosis attempted learner update')
    for name in ('observe', '_birth', '_prune'):
        monkeypatch.setattr(a, name, forbidden)
    report, traces = e.inspect(a, rows, deadline=deadline, counts=counts)
    assert report['formal_support_and_choice_match'] and len(traces) == 2
    assert e.prior.actor_digest(a) == before
    assert counts['actor_evaluation_moves'] == counts['actor_actions_started'] == 2
    assert len(pushes) == counts['laboratory_transitions']+2
    assert report['patterns']['edge_orientation']['corner']['rows'] == 2
    assert all(row['after'][row['wins'].index(1)]['result'] == 'mate' for row in rows)


def checkpoint_fixture(tmp_path):
    a = actor(); a.completed = 1280
    a.trial_decision = {'role': 'none', 'status': 'no_addition', 'after_episode': 128}
    private = tmp_path/'private'; directory = private/'seed-7'; directory.mkdir(parents=True)
    manifest = {'source': e.prior.sources(), 'start_event': 1280, 'end_event': 4096}
    state = {'seed': 7, 'role_index': 0, 'next_event': 1280, 'organism': a}
    pointer = e.prior.save_checkpoint(directory, state, manifest)
    path = directory/pointer['file']
    reference = {'status': 'complete', 'run': {'status': 'complete', 'manifest': manifest,
        'results': [{'seed': 7, 'initial': e.prior.snapshot(a), 'config': asdict(a.config),
                     'inherited_evaluation': {'mates': 0}}]},
        'private_checkpoint_index': [{'path': str(path.relative_to(private)), 'sha256': pointer['sha256']}]}
    return reference, private, path


def test_exact_checkpoint_restored_without_rewriting_source(tmp_path, monkeypatch):
    ref, private, path = checkpoint_fixture(tmp_path)
    before = path.read_bytes()
    a, _, sha = e.restore(ref, private, 7, 1280)
    assert e.prior.snapshot(a) == ref['run']['results'][0]['initial'] and e.prior.sha(path) == sha
    assert path.read_bytes() == before
    ref['run']['results'][0]['config']['max_conditions'] = 5
    with pytest.raises(ValueError, match='state/configuration'):
        e.restore(ref, private, 7, 1280)


@pytest.mark.parametrize('damage', ['source', 'hash', 'path'])
def test_bad_checkpoint_identity_rejected_before_unpickling(tmp_path, monkeypatch, damage):
    ref, private, path = checkpoint_fixture(tmp_path)
    if damage == 'source':
        ref['run']['manifest']['source']['runner_sha256'] = 'different'
    elif damage == 'hash':
        ref['private_checkpoint_index'][0]['sha256'] = 'different'
    else:
        ref['run']['manifest']['start_event'] = 1
        ref['run']['manifest']['end_event'] = 1280
        sha = ref['private_checkpoint_index'][0]['sha256']
        ref['run']['results'][0]['milestones'] = {'1280': {'result': {'evaluation': {}}, 'checkpoint_sha256': sha}}
        ref['private_checkpoint_index'][0]['path'] = '../../outside.pkl.gz'
    def forbidden(*args, **kwargs):
        raise AssertionError('must reject before unpickling')
    monkeypatch.setattr(e.pickle, 'load', forbidden)
    with pytest.raises(ValueError):
        e.restore(ref, private, 7, 1280)


def test_unresolved_solver_result_remains_unknown_and_timeout_propagates(monkeypatch):
    def unknown(*args, **kwargs):
        raise RuntimeError('numerical solution did not reproduce winning choices')
    monkeypatch.setattr(e.ranking, 'certificate', unknown)
    result = e.repair_room([{'wins': [1, 0]}], [[(1,), (0,)]], [0], deadline=time.monotonic()+1)
    assert result['0']['can_add_without_losing_current_success'] is None
    assert result['0']['proof']['status'] == 'inconclusive'
    def expired(*args, **kwargs):
        raise TimeoutError('expired')
    monkeypatch.setattr(e.ranking, 'certificate', expired)
    with pytest.raises(TimeoutError):
        e.checked_certificate([], [], deadline=0)


def test_complete_runner_reproduces_endpoints_and_preserves_every_private_file(tmp_path):
    pool = tmp_path/'pool'; pool.mkdir()
    pools = {'schema': 'mate_one_pool.v1', 'splits': {}}
    for name in ('train', 'validation'):
        path = pool/f'{name}.txt'; path.write_text('\n'.join(FENS)+'\n')
        pools['splits'][name] = {'count': len(FENS), 'sha256': e.prior.sha(path)}
    e.prior.atomic_json(pool/'manifest.json', pools)
    manifest = {'source': e.prior.sources(), 'start_event': 1280, 'end_event': 4096,
                **{name+'_sha256': item['sha256'] for name, item in pools['splits'].items()}}
    reference = {'status': 'complete', 'run': {'status': 'complete', 'manifest': manifest, 'results': []},
                 'private_checkpoint_index': []}
    private = tmp_path/'private'; private.mkdir()
    for seed in (7, 9):
        directory = private/f'seed-{seed}'; directory.mkdir()
        a = actor(); a.trial_decision = {'role': 'none', 'status': 'no_addition', 'after_episode': 128}
        record = {'seed': seed, 'config': asdict(a.config), 'milestones': {}}
        for event in (1280, 4096):
            a.completed = event
            evaluated = e.prior.evaluate(a, FENS, role='none', deadline=time.monotonic()+20)
            state = {'seed': seed, 'role_index': 0, 'next_event': event, 'organism': a}
            pointer = e.prior.save_checkpoint(directory, state, manifest)
            reference['private_checkpoint_index'].append({'path': str((directory/pointer['file']).relative_to(private)), 'sha256': pointer['sha256']})
            if event == 1280:
                record.update(initial=e.prior.snapshot(a), inherited_evaluation=evaluated['evaluation'])
            else:
                record['milestones'][str(event)] = {'result': evaluated, 'checkpoint_sha256': pointer['sha256']}
        reference['run']['results'].append(record)
    path = tmp_path/'reference.json'; e.prior.atomic_json(path, reference)
    before = {str(p): e.prior.sha(p) for p in private.rglob('*') if p.is_file()}
    args = SimpleNamespace(pool=pool, private=private, reference=path, output=tmp_path/'out', wall_seconds=60)
    result = e.run(args)
    assert result['status'] == 'complete' and len(result['results']) == 4
    assert result['actual_counts']['actor_evaluation_moves'] == 16
    assert result['manifest']['training_moves'] == 0
    assert all(r['historical_behavior_matches'] and r['learned_state_unchanged'] for r in result['results'])
    assert before == {str(p): e.prior.sha(p) for p in private.rglob('*') if p.is_file()}
    assert not (args.output/'failure.json').exists()
    # The declared deadline is honored and a failed run is never a complete one.
    args.output = tmp_path/'expired'; args.wall_seconds = 1e-12
    with pytest.raises(TimeoutError):
        e.run(args)
    failure = json.loads((args.output/'failure.json').read_text())
    assert failure['completed_counts']['laboratory_transitions'] == 0
    assert not (args.output/'summary.json').exists()
