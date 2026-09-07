"""Offline chess-pattern and saved-graph attribution. No training/runtime import."""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
import gzip
import json
import math
from pathlib import Path
import pickle
import time

import chess
from . import m1_representation as d
from . import m1_ranking_certificate as ranking

prior = d.prior


def geometry(board):
    wk, bk = board.king(chess.WHITE), board.king(chess.BLACK)
    dx = abs(chess.square_file(wk)-chess.square_file(bk))
    dy = abs(chess.square_rank(wk)-chess.square_rank(bk))
    xf = chess.square_file(bk) in (0, 7)
    yr = chess.square_rank(bk) in (0, 7)
    return {'king_file_distance': dx, 'king_rank_distance': dy,
            'king_shape': f'{min(dx, dy)}x{max(dx, dy)}',
            'edge_orientation': 'corner' if xf and yr else 'file' if xf else 'rank' if yr else 'interior'}


def laboratory_rows(fens, *, deadline, counts):
    rows = []
    for fen in fens:
        d.expired(deadline)
        original = chess.Board(fen)
        bindings, vectors = d.terminal_vectors(d.ChessFeaturePort(original))
        after = []
        for binding in bindings:
            board = original.copy(stack=False)
            move = chess.Move.from_uci(binding)
            piece = 'rook' if board.piece_type_at(move.from_square) == chess.ROOK else 'king'
            board.push(move)
            counts['laboratory_transitions'] += 1
            mate = board.is_checkmate()
            stalemate = board.is_stalemate()
            rook = next(iter(board.pieces(chess.ROOK, chess.WHITE)))
            after.append({'mate': int(mate), 'piece': piece,
                'result': 'mate' if mate else 'stalemate' if stalemate else 'check' if board.is_check() else 'quiet',
                'black_legal_replies': board.legal_moves.count(),
                'rook_capturable': any(m.to_square == rook for m in board.legal_moves),
                'target_black_king_distance': chess.square_distance(move.to_square, board.king(chess.BLACK))})
        wins = [a['mate'] for a in after]
        if sum(wins) != 1:
            raise ValueError('this exact ranking study requires one winning action per row')
        rows.append({'fen': fen, 'bindings': bindings, 'vectors': vectors, 'wins': wins,
                     'after': after, 'geometry': geometry(original), 'orbit': prior.orbit_key(original)})
    return rows


def restore(reference, private, seed, event):
    run = reference['run']; manifest = run['manifest']
    if reference['status'] != 'complete' or run['status'] != 'complete' or manifest['source'] != prior.sources():
        raise ValueError('complete source-matched long-play reference required')
    record = next(r for r in run['results'] if r['seed'] == seed)
    if event == manifest['start_event']:
        entries = [e for e in reference['private_checkpoint_index']
                   if e['path'].startswith(f'seed-{seed}/checkpoint-0-{event:06d}-')]
        expected = record['initial']; evaluation = record['inherited_evaluation']
    elif event == manifest['end_event']:
        milestone = record['milestones'][str(event)]
        entries = [e for e in reference['private_checkpoint_index'] if e['sha256'] == milestone['checkpoint_sha256']]
        expected = {k: v for k, v in milestone['result'].items() if k != 'evaluation'}
        evaluation = milestone['result']['evaluation']
    else:
        raise ValueError('only declared initial/final endpoints are supported')
    if len(entries) != 1:
        raise ValueError('one exact indexed endpoint required')
    entry = entries[0]; path = (private / entry['path']).resolve()
    if not path.is_relative_to(private.resolve()) or prior.sha(path) != entry['sha256']:
        raise ValueError('checkpoint path/transport differs')
    with gzip.open(path, 'rb') as stream:
        payload = pickle.load(stream)
    state = payload['state']; actor = state['organism']
    if (payload['source'] != manifest['source'] or payload['manifest_digest'] != prior.digest(manifest)
            or state['seed'] != seed or state['role_index'] != 0
            or state['next_event'] != event or actor.completed != event or actor.pending or actor.hold_topology
            or asdict(actor.config) != record['config'] or prior.snapshot(actor) != expected):
        raise ValueError('checkpoint state/configuration differs from published endpoint')
    return actor, evaluation, entry['sha256']


def checked_certificate(rows, matrices, *, deadline):
    """Never turn an unresolved numerical check into a feasibility claim."""
    try:
        return {'status': 'resolved', **ranking.certificate(rows, matrices, deadline=deadline)}
    except RuntimeError as error:
        if str(error) not in ('numerical solution did not reproduce winning choices',
                              'inconclusive tie-aware feasibility result', 'invalid feasibility result'):
            raise
        return {'status': 'inconclusive', 'reason': str(error), 'fitted_weights_discarded': True}


def repair_room(rows, matrices, outcomes, *, deadline):
    """Can each failure be fixed while preserving this set's current successes?

    Separate feasible repairs need not be jointly feasible. No fitted policy is
    installed, returned or counted as an actor's performance.
    """
    successes = [i for i, won in enumerate(outcomes) if won]
    result = {}
    for i, won in enumerate(outcomes):
        if won:
            continue
        indices = successes + [i]
        proof = checked_certificate([rows[j] for j in indices], [matrices[j] for j in indices], deadline=deadline)
        result[str(i)] = {'can_add_without_losing_current_success': proof.get('perfect_fixed_weight_policy_exists'),
                         'preserved_successes': len(successes), 'proof': proof}
    return result


def grouped(rows, outcomes):
    result = {}
    for field in ('edge_orientation', 'king_shape', 'king_file_distance', 'king_rank_distance'):
        groups = defaultdict(list)
        for i, row in enumerate(rows):
            groups[str(row['geometry'][field])].append(i)
        result[field] = {key: {'rows': len(ids), 'mates': sum(outcomes[i] for i in ids),
            'orbits': len({rows[i]['orbit'] for i in ids}),
            'failed_orbits': len({rows[i]['orbit'] for i in ids if not outcomes[i]})}
            for key, ids in sorted(groups.items())}
    return result


def profile(actor, traces, initial_event):
    conditions = list(actor.conditions.values())
    masks = [[values[j] for t in traces for values in t['matrix']] for j in range(len(conditions))]
    invariant = [j for j in range(len(conditions)) if all(len({v[j] for v in t['matrix']}) == 1 for t in traces)]
    active = [j for j, mask in enumerate(masks) if any(mask)]
    discriminating = sorted(set(range(len(conditions))) - set(invariant))
    return {'live': len(conditions), 'arity': dict(Counter(len(c.atoms) for c in conditions)),
        'operators': dict(Counter(c.operator for c in conditions)),
        'distinct_atoms': len({a for c in conditions for a in c.atoms}),
        'action_invariant_on_examined_rows': len(invariant),
        'action_discriminating_on_examined_rows': len(discriminating),
        'never_active_on_examined_rows': len(conditions)-len(active),
        'invariant_abs_weight_mass': math.fsum(abs(float(conditions[j].weight)) for j in invariant),
        'discriminating_abs_weight_mass': math.fsum(abs(float(conditions[j].weight)) for j in discriminating),
        'post_initial_live': sum(c.born >= initial_event for c in conditions),
        'post_initial_discriminating': sum(conditions[j].born >= initial_event for j in discriminating),
        'mean_selected_active_conditions': sum(sum(t['matrix'][t['chosen']]) for t in traces)/len(traces),
        'discriminating_with_zero_training_participation': sum(conditions[j].stats.relevance_stats.activation_count == 0 for j in discriminating),
        'condition_activity': [{'id': c.identity, 'arity': len(c.atoms), 'operator': c.operator,
            'born': c.born, 'action_discriminating': j in discriminating,
            'active_alternatives': sum(masks[j]), 'training_activations': c.stats.relevance_stats.activation_count,
            'training_requests': c.stats.relevance_stats.request_exposures}
            for j, c in enumerate(conditions)]}


def inspect(actor, rows, *, deadline, counts):
    traces = []
    def observe(i, row, matrix, scores, chosen):
        traces.append({'matrix': matrix, 'scores': scores, 'chosen': chosen})
    result = d.inspect_actor(actor, rows, deadline=deadline, counts=counts, row_observer=observe)
    matrices = [t['matrix'] for t in traces]
    result['tie_aware_ranking'] = checked_certificate(rows, matrices, deadline=deadline)
    room = repair_room(rows, matrices, result['outcomes'], deadline=deadline)
    result['patterns'] = grouped(rows, result['outcomes'])
    result['failures'] = []
    for i, won in enumerate(result['outcomes']):
        if won:
            continue
        row, trace = rows[i], traces[i]
        win = row['wins'].index(1); chosen = trace['chosen']
        result['failures'].append({'row': i, 'orbit': row['orbit'], 'geometry': row['geometry'],
            'chosen_effect': row['after'][chosen], 'winning_effect': row['after'][win],
            'win_minus_chosen_support': trace['scores'][win]-trace['scores'][chosen],
            'winning_and_chosen_gate_signatures_equal': trace['matrix'][win] == trace['matrix'][chosen],
            **room[str(i)]})
    return result, traces


def margin_change(initial, final, row, old_trace, new_trace):
    """Accounting for one fixed win/loss pair, not a causal learner intervention."""
    win, loss = row['wins'].index(1), new_trace['chosen']
    old, new = initial.conditions, final.conditions
    old_d = {cid: d.gate_value(c, row['vectors'][win])-d.gate_value(c, row['vectors'][loss]) for cid, c in old.items()}
    new_d = {cid: d.gate_value(c, row['vectors'][win])-d.gate_value(c, row['vectors'][loss]) for cid, c in new.items()}
    common = old.keys() & new.keys()
    if any((old[i].operator, old[i].atoms) != (new[i].operator, new[i].atoms) for i in common):
        raise RuntimeError('persistent condition identity changed definition')
    start = math.fsum(float(c.weight)*old_d[i] for i, c in old.items())
    stop = math.fsum(float(c.weight)*new_d[i] for i, c in new.items())
    retained = math.fsum((float(new[i].weight)-float(old[i].weight))*old_d[i] for i in common)
    removed = -math.fsum(float(old[i].weight)*old_d[i] for i in old.keys()-new.keys())
    born = math.fsum(float(new[i].weight)*new_d[i] for i in new.keys()-old.keys())
    if (not math.isclose(start, old_trace['scores'][win]-old_trace['scores'][loss], abs_tol=1e-10)
            or not math.isclose(stop, new_trace['scores'][win]-new_trace['scores'][loss], abs_tol=1e-10)):
        raise RuntimeError('pair margin differs from checked formal scores')
    if not math.isclose(stop-start, retained+removed+born, abs_tol=1e-10):
        raise RuntimeError('margin accounting differs')
    return {'initial_margin_on_final_pair': start, 'final_margin_on_final_pair': stop,
            'retained_weight_change': retained, 'removed_contribution_change': removed,
            'new_contribution_change': born, 'accounting_matches': True}


def compare(seed, actors, reports, traces, data):
    old, new = actors
    result = {'seed': seed, 'retained_initial_conditions': len(old.conditions.keys() & new.conditions.keys()), 'splits': {}}
    for name, rows in data.items():
        before, after = reports[0][name]['outcomes'], reports[1][name]['outcomes']
        groups = {'gained': [], 'lost': [], 'persistent_failure': [], 'retained_success': []}
        for i, (a, b) in enumerate(zip(before, after)):
            key = 'gained' if b > a else 'lost' if a > b else 'retained_success' if b else 'persistent_failure'
            item = {'row': i, 'orbit': rows[i]['orbit'], 'geometry': rows[i]['geometry']}
            if not b:
                item['margin_change'] = margin_change(old, new, rows[i], traces[0][name][i], traces[1][name][i])
            groups[key].append(item)
        result['splits'][name] = {k: {'count': len(v), 'orbits': len({x['orbit'] for x in v}),
            'rows': v if k != 'retained_success' else [],
            'shapes': dict(Counter(x['geometry']['king_shape'] for x in v)),
            'edge_orientations': dict(Counter(x['geometry']['edge_orientation'] for x in v))}
            for k, v in groups.items()}
    return result


def run(args):
    if args.wall_seconds <= 0:
        raise ValueError('positive diagnostic budget required')
    reference = prior.read(args.reference); source = reference['run']['manifest']
    if reference['status'] != 'complete' or source['source'] != prior.sources():
        raise ValueError('complete source-matched reference required')
    splits, hashes = {}, {}
    for name in ('train', 'validation'):
        splits[name], hashes[name] = prior.load_split(args.pool, name)
        if hashes[name] != source[name+'_sha256']:
            raise ValueError('pool differs from saved experiment')
    events = (source['start_event'], source['end_event'])
    actors_plan = [(seed, event) for seed in (7, 9) for event in events]
    manifest = {'schema': 'm1_failure_patterns.v1', 'source': prior.sources(),
        'diagnostic_sha256': prior.sha(__file__), 'representation_sha256': prior.sha(d.__file__),
        'certificate_sha256': prior.sha(ranking.__file__), 'scipy': d.scipy.__version__,
        'reference_sha256': prior.sha(args.reference), 'actors': actors_plan,
        'pool_hashes': hashes, 'wall_seconds': args.wall_seconds,
        'laboratory_transitions': sum(chess.Board(f).legal_moves.count() for rows in splits.values() for f in rows),
        'actor_evaluation_moves': len(actors_plan)*sum(map(len, splits.values())), 'training_moves': 0,
        'final_test_opened': False, 'diagnostic_data_enters_actor': False,
        'limits': ['Post-hoc diagnosis of selected histories, not independent confirmation.',
            'Repair feasibility is per failed row with all current split successes retained; separate repairs need not combine.',
            'Numerically unresolved certificates remain inconclusive, never scored as success.',
            'Invariant/activity claims concern the examined pools, not all possible contexts.',
            'Support decomposition is arithmetic accounting, not a causal training intervention.']}
    args.output.mkdir(parents=True, exist_ok=False)
    prior.atomic_json(args.output/'manifest.json', manifest)
    started = time.monotonic(); deadline = started+args.wall_seconds
    counts = {'laboratory_transitions': 0, 'actor_actions_started': 0, 'actor_evaluation_moves': 0}
    results, comparisons = [], []
    try:
        data = {name: laboratory_rows(fens, deadline=deadline, counts=counts) for name, fens in splits.items()}
        print(json.dumps({'laboratory_complete': counts['laboratory_transitions']}), flush=True)
        for seed in (7, 9):
            actors, paired_reports, paired_traces = [], [], []
            for event in events:
                actor, expected, checkpoint = restore(reference, args.private, seed, event)
                before = prior.snapshot(actor)
                reports, traces = {}, {}
                for name, rows in data.items():
                    reports[name], traces[name] = inspect(actor, rows, deadline=deadline, counts=counts)
                    prior.atomic_json(args.output/f'seed-{seed}-{event}-{name}.json', reports[name])
                    print(json.dumps({'seed': seed, 'event': event, 'split': name, 'mates': reports[name]['mates']}), flush=True)
                if any(reports['validation'][k] != expected[k] for k in ('mates', 'outcomes', 'action_digest')):
                    raise RuntimeError('historical development behavior differs')
                # Physical slots may be allocated when examining the larger train
                # pool; learned state and all learning/control history must match.
                if prior.actor_digest(actor) != prior.digest((before['learned_digest'], before['control_digest'])):
                    raise RuntimeError('diagnosis changed learned state')
                result = {'seed': seed, 'event': event, 'checkpoint_sha256': checkpoint,
                    'historical_behavior_matches': True, 'learned_state_unchanged': True,
                    'reports': reports, 'profile': profile(actor, traces['train']+traces['validation'], events[0])}
                results.append(result)
                prior.atomic_json(args.output/f'seed-{seed}-{event}.json', result)
                actors.append(actor); paired_reports.append(reports); paired_traces.append(traces)
            comparisons.append(compare(seed, actors, paired_reports, paired_traces, data))
        assert counts['laboratory_transitions'] == manifest['laboratory_transitions']
        assert counts['actor_evaluation_moves'] == counts['actor_actions_started'] == manifest['actor_evaluation_moves']
        d.expired(deadline)
        result = {'status': 'complete', 'manifest': manifest, 'actual_counts': counts,
                  'wall_seconds': time.monotonic()-started, 'results': results, 'comparisons': comparisons}
        prior.atomic_json(args.output/'summary.json', result)
        return result
    except BaseException as error:
        prior.atomic_json(args.output/'failure.json', {'status': 'incomplete', 'error': str(error),
            'completed_counts': counts, 'possible_unreturned_actor_moves': counts['actor_actions_started']-counts['actor_evaluation_moves']})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('pool', 'reference', 'private', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--wall-seconds', type=int, default=1800)
    print(json.dumps({'status': run(parser.parse_args())['status']}))


if __name__ == '__main__':
    main()
