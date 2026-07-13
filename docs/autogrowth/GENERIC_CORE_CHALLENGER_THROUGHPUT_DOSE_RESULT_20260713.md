# Generic-Core Challenger-Throughput Dose Result

Date: 2026-07-13. Track: generic-core development. Status: complete negative.
No confirmation or KRK claim.

## Frozen provenance

- Preregistration commit: 'e5e397c'.
- Frozen implementation/source commit: 'de8f683baed2c4b8388e1680ae1830ecba026a98'.
- Fresh seeds: 20262001--20262020, executed exactly once after both commits
  were pushed.
- Compressed artifact:
  'reports/autogrowth/generic_core/challenger_throughput_dose_20260713.json.gz'.
- Compressed SHA-256:
  '0ecbf95c8e444142c3cdcb28bd688973ec0ed135e5ab98ba3811e1368d47ab6f'.
- Raw JSON SHA-256:
  '94a6d4066d98bdccfbd9115070c4f01fc40949b09411cd289218060054bfe1e0'.
  The 64 MB raw file is retained outside Git at
  '/tmp/challenger_throughput_dose_20260713.json'.
- Focused validation: 16 passed. Full repository validation: 787 passed in
  2,412.81 seconds. A retired-seed full-path smoke also completed with every
  invariant true.

All 20 phase-0 checkpoints passed the frozen >=0.85 development boundary;
median development success was 1.0. Quiescence removed 3--9 unfinished trials
per checkpoint (median 5.5) without changing behavior.

## Primary arm table

Values are median old success / median new success, number of seeds with both
>=0.85, and median final mature occupancy.

| demand | arm | old | new | both | mature |
|---:|---|---:|---:|---:|---:|
| 0 | fixed-8 ranked | 1.000 | 1.000 | 20/20 | 12.0 |
| 0 | rent batch-1 ranked | 1.000 | 1.000 | 19/20 | 7.5 |
| 0 | rent batch-2 ranked | 1.000 | 1.000 | 19/20 | 7.5 |
| 0 | rent batch-4 ranked | 1.000 | 1.000 | 19/20 | 8.0 |
| 0 | rent batch-4 shuffled | 1.000 | 1.000 | 20/20 | 8.0 |
| 1 | fixed-8 ranked | 1.000 | 1.000 | 19/20 | 19.0 |
| 1 | rent batch-1 ranked | 1.000 | 1.000 | 17/20 | 11.0 |
| 1 | rent batch-2 ranked | 1.000 | 1.000 | 19/20 | 12.0 |
| 1 | rent batch-4 ranked | 1.000 | 1.000 | 19/20 | 13.0 |
| 1 | rent batch-4 shuffled | 0.978 | 0.715 | 3/20 | 9.5 |
| 2 | fixed-8 ranked | 1.000 | 1.000 | 19/20 | 21.0 |
| 2 | rent batch-1 ranked | 0.882 | 0.658 | 1/20 | 9.5 |
| 2 | rent batch-2 ranked | 0.895 | 0.681 | 2/20 | 11.0 |
| 2 | rent batch-4 ranked | 0.990 | 0.709 | 1/20 | 12.0 |
| 2 | rent batch-4 shuffled | 0.825 | 0.147 | 0/20 | 8.5 |

## Preregistered gate verdicts

| gate | verdict | decisive measurement |
|---|---|---|
| fixed-8 ceiling replication | PASS | medians 1.0/1.0; 19/20 joint |
| batch-1 manipulation check | PASS | occupancy 9.5; only 1/20 joint |
| topology dose | FAIL | medians 9.5/11/12; strict 10/20; batch-4 minus batch-1 2 |
| performance dose | FAIL | batch-4 minus batch-1 median 0; positive 9/20 |
| fixed-capacity noninferiority | FAIL | batch-4 minus fixed median -0.249 |
| nomination selectivity | PASS | closed-loop and shadow each ranked wins 20/20 |
| demand allocation | FAIL | batch-4 occupancies 8/13/12; monotonic 9/20; m2-m0 4 |
| low-demand compression | PASS | fixed minus batch-4 occupancy 4.5; medians 1.0/1.0 |
| safety and identity | PASS | all 60 cells; zero safety binds |

Overall 'development_support' is false.

## Manipulation and causal attribution

The intended throughput manipulation succeeded:

| m=2 ranked dose | proposals | promotions | retirements | final mature |
|---|---:|---:|---:|---:|
| batch-1 | 8.0 | 6.0 | 4.0 | 9.5 |
| batch-2 | 15.0 | 8.0 | 4.0 | 11.0 |
| batch-4 | 25.0 | 8.5 | 4.0 | 12.0 |

Batch-4 therefore removed the hard proposal ceiling, but the extra seventeen
median proposals beyond batch-1 produced only 2.5 additional promotions and
2.5 additional final mature candidates. Across batch-4 'm=2' runs, extra
challengers were primarily rejected (median 7), left uncertain then pruned
(median 4), or lacked adequate support then were pruned (median 3).

The weak topology increase did not become a performance dose. Batch-4 beat
batch-1 on minimum old/new success in 9 seeds, tied in 7 and lost in 4; its
median difference was zero. It beat batch-2 in 7, tied in 7 and lost in 6,
again with median zero. Fixed-8 beat batch-4 in 19/20 seeds. Batch-4 preserved
the old mapping much better than it learned the new mapping (0.990 versus
0.709 median), so catastrophic retention loss is not the dominant endpoint
failure.

Nomination remains strongly supported. At 'm=2', batch-4 ranked beat batch-4
shuffled in 20/20 tasks with median minimum-success advantage 0.467. On the
identical fixed-ranked experience stream, ranked counterfactual rent beat
shuffled in 20/20 with median advantage 0.0833. Thus the negative result is not
evidence that residual-ranked proposals lack compositional signal.

Final changed-cue ablations in 'm=2' counted 87 positive, 4 negative and 149
zero effects for batch-4 ranked. Extra throughput exposed some additional
useful candidates, but most additional topology was absent, redundant or too
weakly trained to control the changed decisions.

## Interpretation and closure

The hypothesis that one-challenger throughput was the sufficient missing
metabolic rate is falsified. The hard proposal ceiling was real, and relaxing
it modestly increased occupancy, but proposal availability was not the main
remaining cause of the fixed-versus-rent gap.

The supported next scientific distinction is between:

1. **candidate equilibration/plasticity failure** -- concurrent challengers do
   not acquire stable individual causal value before rent review; and
2. **rent eligibility/credit failure** -- useful distributed or cooperative
   candidates have weak individual counterfactual rent and are therefore
   rejected even when nomination is informative.

This result does not select between those explanations and does not authorize
an automatic change to review cadence, learning rate, rent threshold,
cooperative credit, topology capacity or KRK transfer. Any next package must
change exactly one of those factors on fresh generic-core data.

The package is closed as a negative completion. The robust achievements carried
forward are role-blind nomination selectivity, low-demand topology compression,
shared-state preservation, trial isolation, and bounded global metabolism.
