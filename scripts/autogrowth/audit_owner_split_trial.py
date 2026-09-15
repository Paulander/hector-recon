"""Offline terminal-flag, assignment-RNG and owner-evidence audit; no play."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random

from run_owner_split_trial import load_actor, digest, ROLES, SEEDS, verify_trials
from run_recursive_retention import ROWS


def truth(expression, values):
    if expression.operator == 'true': return True
    if expression.operator == 'read': return values[expression.atom[0]] == expression.atom[1]
    flags = [truth(c,values) for c in expression.children]
    if expression.operator == 'and': return all(flags)
    if expression.operator == 'or': return any(flags)
    if expression.operator == 'xor': return sum(flags) == 1
    raise ValueError(expression.operator)


def audit(path):
    root = Path(path)
    result = json.loads((root/'result.json').read_text())
    assert result['status']=='complete'
    sources = json.loads((root/'source.json').read_text())
    from run_owner_split_trial import ROOT
    for name,expected in sources.items():
        assert digest((ROOT/name).read_bytes()) == digest((root/'source-snapshot'/name).read_bytes()) == expected
    report = {'status':'verified','source_files':len(sources),'training_actions':0,
              'new_environment_actions':0,'arms':[]}
    for seed in SEEDS:
        for role in ROLES:
            directory = root/f'seed-{seed}'/role
            actor = load_actor(directory/'block-001856/checkpoint.pkl.gz')
            records = [json.loads(s) for block in sorted(directory.glob('block-*'))
                       for s in (block/'training.jsonl').read_text().splitlines()]
            rng = random.Random(f'owner-split-use:{seed}')
            counts, evidence, trials = Counter(), {}, {}
            for row in records:
                values = (*ROWS[row['row']],row['action']=='act-b')
                assert row['candidate_values'] == [truth(e,values) for e in actor.owner_candidates]
                assert row['birth_candidate_values'] == [truth(e,values) for e in actor.birth_expressions]
                flags = row['split_assignments']
                assert flags == {str(k):rng.random()<.5 for k in sorted(map(int,flags))}
                owner = row['owner']; counts[owner] += 1
                ev = evidence.setdefault(owner,[[0,0,0.,0.] for _ in actor.owner_candidates])
                for e,flag in zip(ev,row['candidate_values']):
                    e[int(flag)] += 1
                    e[2+int(flag)] += row['reward']-row['prediction']
            for owner,count in actor.owner_visits.items(): assert count == counts[owner]
            for owner,observed in actor.owner_evidence.items():
                for i,e in observed.items():
                    assert [e.n0,e.n1,e.sum0,e.sum1] == evidence[owner][i]
            verify_trials(actor,records,trials)
            if role=='trial': assert actor.split_use_rng.getstate() == rng.getstate()
            report['training_actions'] += len(records)
            report['arms'].append({'seed':seed,'role':role,'actions':len(records),
                'all_formal_probe_flags_match_declared_measurements':True,
                'all_assignment_draws_match_independent_rng':True,
                'all_owner_exposure_and_residual_histories_match':True,
                'all_trial_outcomes_and_child_exposures_match':True})
    assert report['training_actions'] == 11520
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run'); parser.add_argument('--output',required=True)
    args=parser.parse_args()
    with Path(args.output).open('x') as stream:
        json.dump(audit(args.run),stream,indent=2,sort_keys=True); stream.write('\n')
