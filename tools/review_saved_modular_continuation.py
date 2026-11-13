"""Read authenticated fixed512 JSON; never load checkpoints or execute a learner.

This is a scoped opportunity/count reconciliation, not replacement semantic V.
Run from the chess worktree with --workspace and --output explicit.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, description):
    if not condition:
        raise ValueError(description)


def read_checked(path, expected):
    raw = path.read_bytes()
    require(sha(raw) == expected, f"changed evidence: {path}")
    return json.loads(raw)


def typed_fields(value):
    pairs = value['dict']
    require(len({k for k, _ in pairs}) == len(pairs), 'duplicate typed dictionary key')
    return dict(pairs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    packet = args.workspace / 'm2-modular-512-verification-recovery-20261021-saved-closure'
    checks_path = packet / 'CHECKSUMS.json'
    checks = read_checked(checks_path, 'a614d14ebec3f540ece5760fcf4f76efa59421d7bdcabd7eb38a0d3d6843873d')
    inputs = {}

    def saved(relative):
        expected = checks['entries'][relative]['sha256']
        inputs[str(packet / relative)] = expected
        return read_checked(packet / relative, expected)

    ledger = saved('FINAL_PARTIAL_LEDGER.json')
    require(ledger['scientific_verdict'] == 'NOT_VERIFIED_V_NOT_ENTERED', 'unexpected prior verdict')
    scientific = Path(ledger['external_dependencies_remain'][0])
    mat_path = scientific / 'PRODUCER_MATERIALIZATION.json'
    mat_hash = 'ff0a4a745e19eeb135e259f286ecd3dba91c5ceecd9cbca099a7ce0a885d8e1d'
    materialization = read_checked(mat_path, mat_hash)
    inputs[str(mat_path)] = mat_hash
    result = {}
    byte_count = file_count = 0
    for arm in ('frozen', 'plastic'):
        c = saved(f'receipts/{arm}/C_COMPLETE.json')
        r = saved(f'receipts/{arm}/R_PENDING.json')
        require(c['identity'] == r['identity'] ==
                f'm2-modular-setup-512-continuation-20261010-v1:001:{arm}', 'actor identity')
        require(c['schedule_sha256'] == r['schedule_sha256'], 'schedule binding')
        for phase, status in (('R', 'PASS'), ('C', 'PASS'), ('V', 'FAIL')):
            guard = saved(f'receipts/recovery_{phase}_{arm}_v1/guard.json')
            require(guard['status'] == status, f'{phase} actual guard')
        require(r['replayed_episodes'] == 512 and r['recorded_actions_forced'] is False,
                'own-choice replay scope')
        require(r['completed_full_checkpoint_comparison_count'] == 5, 'checkpoint count')
        replay = {x['episode']: x for x in r['exact_event_comparisons']}
        require(set(replay) == set(range(1, 513)), 'replay identity coverage')
        root = scientific / 'scientific' / arm / f'fixed512_P_{arm}_v1' / 'p'
        manifest = materialization['arms'][arm]['files']
        episodes = {}
        for name, entry in manifest.items():
            path = root / name
            raw = path.read_bytes()
            require(len(raw) == entry['bytes'] and sha(raw) == entry['sha256'],
                    f'producer file changed: {path}')
            byte_count += len(raw)
            file_count += 1
            if name.startswith('EPISODE-'):
                event = json.loads(raw)
                i = event['relative_episode']
                require(name == f'EPISODE-{i:03d}.json' and i not in episodes,
                        'episode identity/uniqueness')
                require(event['global_episode'] == 256 + i, 'global episode origin')
                require(replay[i]['comparison']['producer_episode_sha256'] == sha(raw),
                        'replay to producer binding')
                episodes[i] = event
        require(set(episodes) == set(range(1, 513)), 'complete fixed episode set')
        counts = Counter()
        successes = Counter()
        births, per_term = [], {}
        first_contrast = first_weighted_contrast = first_nonbias_update = None
        first_setup_completed = last_setup_completed = None
        all_actions = 0
        for i, event in sorted(episodes.items()):
            contract = 'm2' if event['white_action_budget'] == 2 else 'm1'
            counts[f'{contract}_episodes'] += 1
            native = typed_fields(event['result_exact'])
            traces = native['traces']['list']
            sequence = [typed_fields(typed_fields(t)['request'])['selected_module'] for t in traces]
            all_actions += len(traces)
            require(len(traces) == event['physical_white_actions'] == replay[i]['physical_white_actions'],
                    'physical action count')
            if native['eventual_mate']:
                successes[contract + ':' + '->'.join(sequence)] += 1
            require(event['learning_evidence']['positive_m2_receipt'] ==
                    (contract == 'm2' and native['eventual_mate']), 'positive receipt definition')
            counts[f'{contract}_setup_first'] += bool(sequence and sequence[0] == 'setup')
            passive = event['continuation_passive']
            clock = passive['local_clock']['modules']['setup']
            if first_setup_completed is None:
                first_setup_completed = clock['completed_before']
            else:
                require(clock['completed_before'] == last_setup_completed, 'Setup clock continuity')
            last_setup_completed = clock['completed_after']
            require(clock['completed_after'] - clock['completed_before'] == clock['applied_frames'],
                    'Setup applied observations')
            counts['setup_applied_observations'] += clock['applied_frames']
            require(sequence.count('setup') == clock['selected_frames'] == len(passive['setup_menus']),
                    'Setup selection/menu correspondence')
            counts[f'{contract}_setup_selections'] += sequence.count('setup')
            for menu in passive['setup_menus']:
                truth = any(x['truth_varies_across_actual_bindings']
                            for x in menu['contrasts']['conditions'] if not x['bias'])
                weighted = menu['contrasts']['derived_unboosted_score_contrast']
                counts['setup_menus_with_feature_contrast'] += truth
                counts['setup_menus_with_score_contrast'] += weighted
                if truth and first_contrast is None:
                    first_contrast = i
                if weighted and first_weighted_contrast is None:
                    first_weighted_contrast = i
            for birth in event['learning_evidence']['structural_commits']:
                if birth['module'] != 'setup':
                    continue
                births.append(birth)
                per_term[str(birth['condition'])] = {'birth_episode': i, 'updates': 0,
                    'positive_target_updates': 0, 'negative_target_updates': 0,
                    'first_update_episode': None, 'last_update_episode': None}
            updates = passive['lean_ordered_event_evidence']['ordered_credit_math']
            setup_updates = [x for x in updates if x['module'] == 'setup' and x['updated']]
            require(len(setup_updates) == clock['applied_frames'], 'ordered credit/clock agreement')
            for frame in setup_updates:
                require(sequence[frame['white_ordinal'] - 1] == 'setup', 'selected credit owner')
                target_positive = float.fromhex(frame['target_hex']) > 0
                counts['setup_positive_target_frames'] += target_positive
                counts['setup_negative_target_frames'] += not target_positive
                active_nonbias = [x for x in frame['ordered_increments']
                                  if x['condition'] != 0 and float.fromhex(x['applied_increment_hex']) != 0]
                counts['setup_nonbias_nonzero_frames'] += bool(active_nonbias)
                counts['setup_nonbias_nonzero_contributor_updates'] += len(active_nonbias)
                counts['setup_nonbias_positive_target_frames'] += bool(active_nonbias) and target_positive
                if active_nonbias and first_nonbias_update is None:
                    first_nonbias_update = i
                for term in active_nonbias:
                    row = per_term[str(term['condition'])]
                    require(i > row['birth_episode'], 'credit must follow admitted birth episode')
                    row['updates'] += 1
                    row['positive_target_updates' if target_positive else 'negative_target_updates'] += 1
                    row['first_update_episode'] = row['first_update_episode'] or i
                    row['last_update_episode'] = i
        require(all_actions == r['replayed_white_actions'], 'replay action total')
        expected = c['learning_evidence']
        require(counts['setup_nonbias_nonzero_contributor_updates'] ==
                expected['setup_all_post_birth_nonzero_credit'], 'independent Setup credit count')
        require({str(b['condition']): b for b in births} == expected['structural_commits']['setup'],
                'independent structural commit aggregation')
        require(sum(n for k, n in successes.items() if k.startswith('m2:')) ==
                expected['positive_m2_receipts'], 'independent positive M2 receipt count')
        result[arm] = {'counts': dict(counts), 'successful_training_sequences': dict(successes),
            'white_actions': all_actions, 'setup_completed_before': first_setup_completed,
            'setup_completed_after': last_setup_completed, 'setup_births': births,
            'setup_term_exposure': per_term, 'first_feature_contrast_episode': first_contrast,
            'first_score_contrast_episode': first_weighted_contrast,
            'first_nonbias_nonzero_credit_episode': first_nonbias_update,
            'census_status': 'PROVISIONAL_NOT_REVERIFIED',
            'original_V_status': 'FAIL_BEFORE_ENTRY_UNCHANGED'}
    require(file_count == materialization['files'] == 1052, 'complete producer manifest count')
    require(byte_count == materialization['bytes'] == 61529391, 'complete producer manifest bytes')
    output = {'schema': 'chess.saved-continuation-opportunity-review.v1',
        'status': 'SCOPED_SAVED_RECORD_RECONCILIATION_PASS',
        'not_final_scientific_acceptance': True, 'new_native_calls': 0, 'new_training': 0,
        'checkpoint_deserializations': 0, 'inputs': inputs, 'producer_files_checked': file_count,
        'producer_bytes_checked': byte_count, 'replayed_episode_records_joined': 1024,
        'source_sha256': sha(Path(__file__).read_bytes()), 'arms': result}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as file:
        json.dump(output, file, indent=2, sort_keys=True, allow_nan=False)
        file.write('\n')
    print(json.dumps({'status': output['status'], 'arms': result}, indent=2))


if __name__ == '__main__':
    main()
