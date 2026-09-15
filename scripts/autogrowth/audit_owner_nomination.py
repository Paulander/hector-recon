"""Read-only audit of sealed owner pilot evidence; never trains or repairs files."""
import argparse
import json
import math
import os
from pathlib import Path
import resource
import signal
import time

from run_owner_nomination import SEEDS, ROLES, schedule, structure, verify_conversion, verify_pair
from run_recursive_retention import ROOT, ROWS, digest, encoded, load_actor, evaluate, json_once


def value(expression, row, action):
    if expression.operator == 'true':
        return True
    if expression.operator == 'read':
        index, expected = expression.atom
        return (*ROWS[row], bool(action))[index] == expected
    children = [value(c, row, action) for c in expression.children]
    return {'and': all(children), 'or': any(children), 'xor': sum(children) == 1}[expression.operator]


def target(row):
    x, y, z, _ = ROWS[row]
    return int(y if z else x)


def discrimination(actor):
    identities = list(actor.conditions)
    differences = [[int(value(actor.expressions[c], row, 1)) -
                    int(value(actor.expressions[c], row, 0)) for c in identities]
                   for row in range(16)]
    tied = [row for row, vector in enumerate(differences) if not any(vector)]
    forced_losses = [row for row in tied if target(row) == 0]
    return {'identities': identities, 'action_difference_vectors': differences,
            'structurally_tied_rows': tied, 'forced_tie_losses': forced_losses,
            'action_distinguishing_rows': 16-len(tied),
            'perfect_ranking_impossible_by_exact_tie': bool(forced_losses)}


def audit(root):
    started = time.monotonic()
    raw = json.loads((root/'result.json').read_text())
    source = json.loads((root/'source.json').read_text())
    for name, expected in source.items():
        assert digest((ROOT/name).read_bytes()) == expected
        assert digest((root/'source-snapshot'/name).read_bytes()) == expected
    report = {'raw_status': raw['status'], 'raw_error': raw.get('error'),
              'raw_elapsed_seconds': raw['elapsed_seconds'], 'raw_max_rss_kib': raw['max_rss_kib'],
              'sources_verified': len(source), 'changed_progress_copies': [], 'arms': [],
              'counts': {'training': 0, 'scheduled_evaluation': 0,
                         'independent_frozen_reproductions': 0, 'blocks': 0, 'checkpoints': 0},
              'training_repeated': 0, 'raw_evidence_modified': False}
    original_verification_open = True
    original_verification_actions = 0
    for seed in SEEDS:
        directory = root/f'seed-{seed}'
        prefix, continuation = schedule(seed)
        assert json.loads((directory/'schedule.json').read_text()) == {'prefix': prefix, 'continuation': continuation}
        parent = load_actor(directory/'prefix/block-000064/checkpoint.pkl.gz')
        left, right = [load_actor(directory/role/'start.pkl.gz') for role in ROLES]
        for actor in (left, right):
            verify_conversion(parent, actor)
        verify_pair(left, right)
        for role in ('prefix', *ROLES):
            role_dir = directory/role
            actor = load_actor(role_dir/'start.pkl.gz')
            previous = digest((role_dir/'start.pkl.gz').read_bytes())
            start_event = actor.completed
            report['counts']['checkpoints'] += 1
            assigned = prefix if role == 'prefix' else continuation
            original = {r['row'] for r in json.loads((directory/'prefix/block-000064/evaluation.json').read_text())['rows'] if r['reward'] > 0}
            previous_solved = set(original)
            arm = {'seed': seed, 'role': role, 'initial_discrimination': discrimination(actor) if role != 'prefix' else None,
                   'measurements': [], 'training_successes': [0, 0], 'training_exposure': [0, 0]}
            for offset in range(0, len(assigned), 64):
                block = role_dir/f'block-{start_event+offset:06d}'
                manifest = json.loads((block/'complete.json').read_text())
                intent = json.loads((block/'intent.json').read_text())
                order = assigned[offset:offset+64]
                assert intent == {'start': start_event+offset, 'stop': start_event+offset+64,
                                  'order': order, 'previous': previous, 'evaluate': role!='prefix' or offset==64}
                assert manifest['start'] == intent['start'] and manifest['stop'] == intent['stop']
                sealed = (block/'training.jsonl').read_bytes()
                records = [json.loads(line) for line in sealed.splitlines()]
                assert len(records) == 64
                derived_submissions = b''.join(encoded({k:v for k,v in record.items() if k!='weights_after'}) for record in records)
                for name, expected in manifest['files'].items():
                    actual = (block/name).read_bytes()
                    if digest(actual) != expected:
                        assert name in ('progress.jsonl', 'submissions.jsonl')
                        canonical = sealed if name == 'progress.jsonl' else derived_submissions
                        assert canonical.startswith(actual) and digest(canonical) == expected
                        report['changed_progress_copies'].append({'path': (block/name).relative_to(root).as_posix(),
                            'observed_lines': len(actual.splitlines()), 'sealed_lines': 64,
                            'observed_sha256': digest(actual), 'declared_sha256': expected,
                            'prefix_matches_sealed_records': True})
                        original_verification_open = False
                for record, row, event in zip(records, order, range(intent['start'], intent['stop'])):
                    assert (record['row'], record['event']) == (row, event)
                    assert record['action'] in ('act-a', 'act-b')
                    assert record['reward'] == (1 if (record['action']=='act-b') == bool(target(row)) else -1)
                    n = len(record['active']) + int(role=='prefix')
                    assert record['denominator'] == n > 0
                    assert len(record['weights_before']) == len(record['weights_after']) == len(record['active'])
                    delta = .3*(record['reward']-record['prediction'])/n
                    assert all(math.isclose(after-before, delta, abs_tol=2e-12)
                               for before, after in zip(record['weights_before'], record['weights_after']))
                    if role != 'prefix':
                        assert record['candidate_values'] == [value(c, row, record['action']=='act-b') for c in actor.owner_candidates]
                    context = int(ROWS[row][2])
                    arm['training_exposure'][context] += 1
                    arm['training_successes'][context] += int(record['reward'] > 0)
                actor = load_actor(block/'checkpoint.pkl.gz')
                assert actor.completed == intent['stop']
                previous = digest((block/'checkpoint.pkl.gz').read_bytes())
                report['counts']['training'] += 64
                report['counts']['blocks'] += 1
                report['counts']['checkpoints'] += 1
                if intent['evaluate']:
                    saved = json.loads((block/'evaluation.json').read_text())
                    assert evaluate(actor) == saved
                    report['counts']['scheduled_evaluation'] += 16
                    report['counts']['independent_frozen_reproductions'] += 16
                    if original_verification_open:
                        original_verification_actions += 16
                    solved = {r['row'] for r in saved['rows'] if r['reward'] > 0}
                    arm['measurements'].append({'episode': actor.completed, 'correct': saved['correct'],
                        'context_correct': saved['context_correct'], 'solved_rows': sorted(solved),
                        'gained_since_previous': sorted(solved-previous_solved),
                        'lost_since_previous': sorted(previous_solved-solved),
                        'gained_since_prefix': sorted(solved-original), 'lost_since_prefix': sorted(original-solved),
                        'structure': structure(actor), 'discrimination': discrimination(actor)})
                    previous_solved = solved
            if role != 'prefix':
                arm['development_history'] = actor.development_history
                arm['leaf_details'] = [{'owner': owner, 'path': repr(leaf.path), 'born': leaf.born,
                                       'subsequent_visits': actor.owner_visits[owner],
                                       'parameters': len(leaf.contributions)} for owner, leaf in actor.leaves.items()]
                assert not actor.candidate_pending and not actor.owner_pending
                actor.validate_ownership()
            report['arms'].append(arm)
    assert report['counts'] == {'training': 1280, 'scheduled_evaluation': 288,
        'independent_frozen_reproductions': 288, 'blocks': 20, 'checkpoints': 26}
    report['original_frozen_reproductions_before_failed_manifest'] = original_verification_actions
    report['status'] = 'sealed_records_and_checkpoints_verified_with_retained_progress_copy_failure'
    report['audit_elapsed_seconds'] = time.monotonic()-started
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (2*1024**3, 2*1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (110, 115))
    signal.alarm(110)
    result = audit(args.input)
    result['audit_max_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result['audit_source_sha256'] = digest(Path(__file__).read_bytes())
    json_once(args.output, result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('arms','changed_progress_copies')}))
