# Normal-access recovery: protocol before outcomes

Experimental branch: `codex/residual-shadow-nomination`, from `9268b1db`.
This follows the negative 50% probing result in [TRIAL_USEFULNESS.md](TRIAL_USEFULNESS.md).
It adds phase recording to the experiment runner; no learner, coach, formal engine,
credit rule, birth/pruning law or parameter is changed. Default `--recovery 0`
preserves the previous experiment's behavior and result format.

## Question and fixed design

Does the performance cost of a completed probing interval persist after another
128 ordinary training actions? This tests recovery of the complete learner,
including normal pruning/replacement and continued edge learning. It cannot
attribute any recovery solely to edge updates or establish a usefulness controller.

- Same seeds 1, 2, 3; five arms: none, ranked, random, probe_ranked, probe_random.
- Same 32-condition base budget, 64 shadow candidates, 64 discovery actions,
  minimum support 4, attachment after 128 actions, and 128-action comparison
  interval. Probe probability remains 0.5 for that interval only.
- Append exactly 128 normal-access training actions to EVERY arm, for 384 per
  arm. The existing internal mechanism ends its probing window; the coach never
  chooses access from a graph inspection or an offline score. No learner freeze.
- Record training outcomes by the three phases. Verify prefix/comparison digests
  and the episode-256 learned-state digest against the previous completed run.
  Probe assignments/history and its RNG must remain unchanged during recovery.
- Evaluate only after all 384 actions, on the same 128 development rows. Evaluate
  each of the four addition actors on an offline clone with only its final trial
  coefficient masked. No intermediate validation or score-selected removal.
- Observe lifecycle at phase boundaries: births, pruning, live/retired identities
  and trial survival. The current tombstones block identical rebirth; new random
  replacements are allowed. The trial reaches its age-256 grace at the final
  outcome; older base conditions may retire earlier. Keep all normal rules.
- Budget: **5,760 training + 1,920 normal validation + 1,536 ablation = 9,216
  actual moves**. Three seed workers; **1,800 seconds per seed**. No automatic
  extensions, additional seeds or outcome-based parameter changes.
- The training schedule, random definitions, source/runtime hashes, pool hashes
  and budgets are written before play. Failed/incomplete runs cannot be reported
  as complete. Do not open final-test rows or publish raw boards/actions/weights.

Train SHA256: `6007840a71af73552e78ca3a272ce0af1b4639258246b39fa578f842a5a2a8f2`.
Validation SHA256: `dd92f3740e916f89665f459f9165088bac563a465c8bd803404a241f48798c2e`.
Require disjoint training/validation symmetry orbits. This reused validation is
development data and cannot establish sealed mastery.

Primary comparison: probed-minus-always-enabled final mates within each seed and
role, compared with the previously recorded episode-256 gap. Also report all
arms against no addition, phase training mates, final ablations, lifecycle changes
and elapsed time. Improvement with more training in every arm is not a specific
benefit of probing. Distinct nominees can produce identical trajectories, and
identical ranked/random nominees are not independent confirmations.

## Reproduction

Use Python 3.12, chess 1.11.2 and numpy 2.3.5, with the existing pool:

```bash
PYTHONPATH=src:libs/recon-lite/src python scripts/autogrowth/run_trial_usefulness.py \
  --pool reports/autogrowth/runs/m1-coach-smoke-pool \
  --output reports/autogrowth/runs/trial-recovery-seeds123 \
  --seeds 1 2 3 --conditions 32 --candidates 64 --discovery 64 \
  --after-episode 128 --suffix 128 --window 128 --probability 0.5 \
  --recovery 128 --min-support 4 --workers 3 --wall-seconds 1800
```

Use a fresh output path. Run the focused suite in `AGENTS.md` plus
`tests/autogrowth/test_trial_recovery_experiment.py` before actual play. New tests
check exact moves/no intermediate evaluation, unchanged completed probe evidence,
phase split equivalence to uninterrupted learning, exact prior prefix, parallel
parity, invalid boundaries, and preservation of incomplete status on failure.

## Interpretation and continuation

This is a stability/experience experiment, not a new growth mechanism. Recovery
would show at least partly transient damage; persistent damage would motivate
inspection of ordinary credit and action opportunity before another controller.
Neither outcome authorizes promoting the probe or declaring autonomous useful
selection. Keep mechanism evidence, chess performance and handover claims distinct.

## Execution interruption and identical retry

The first attempt at implementation `cca08f8d` was interrupted by the execution
connection disappearing. Its session became unknown, and no training workers
remained. Ten completed-arm console entries survived, but no complete seed record
or aggregate summary did. It is **incomplete**, not a scientific result. Preserve
`reports/autogrowth/development/TRIAL_RECOVERY_INTERRUPTED_20260906.json`.
Those entries establish at least 6,016 actual moves; additional in-flight moves
are uncounted. Do not present the completed retry's budget as the total compute
used across attempts or cherry-pick the first attempt's favorable arms.

The runner now writes each completed arm's full aggregate record immediately.
This output-only fix changes no learner/input/schedule. A focused failure test
checks that a later failure preserves earlier arm evidence without producing a
complete summary. It does not add automatic resume or extend a timed-out run.

Repeat all 15 arms with exactly the declared parameters and the same 1,800-second
per-seed cap in a fresh directory:
`reports/autogrowth/runs/trial-recovery-seeds123-retry1`. This retry is due to an
execution interruption, with no scientific configuration change or score-based
extension. Record its source hashes before play and check its completed arms
against every available earlier log entry, excluding wall times.

## Implementation and verification

Initial phase runner/protocol: `cca08f8d34c635239b5d87e2241197f952105948`.
Output checkpoint fix and retry protocol:
`426b4e80b543f0d82c82461ca681d7ab412562a7`.

157 distinct focused tests passed across the checks: 146 unchanged mechanism/
regression tests and 11 experiment tests, including six new recovery/output
checks. The original ten experiment tests also passed before the interruption.
The output fix's eleven experiment tests were rerun successfully before the retry.
No learner or coach mechanism was modified.

## Completed retry: 2026-09-06

All 9,216 planned moves completed: 5,760 training, 1,920 normal validation and
1,536 offline ablation. Seed totals were 862.153, 971.213 and 965.109 seconds,
below the unchanged 1,800-second cap. The aggregate is
`reports/autogrowth/development/TRIAL_RECOVERY_20260906.json`.
The interrupted attempt is recorded separately; the retry's move count excludes
its at-least-6,016 completed-arm moves and unknown in-flight work.

Every arm reproduced the previous 256-action prefix/comparison records and exact
learned-state digest, including nomination and retained shadow history. All six
probe reports/history digests stayed identical to the previous completed probe
experiment: recovery did not generate new assignments or rewrite its evidence.
All ten surviving interrupted-arm console entries reproduced apart from timing.
Final-test rows stayed unopened. Validation remains 128 viewed development rows
in 25 training-disjoint symmetry orbits.

Development mates before → after the additional 128 training actions:

| Seed | No addition | Always ranked | Always random | Probed ranked | Probed random |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 126 → 126 | 126 → 128 | 128 → 128 | 122 → 124 | 126 → 128 |
| 2 | 93 → 115 | 101 → 101 | 101 → 101 | 94 → 98 | 94 → 98 |
| 3 | 66 → 66 | 66 → 66 | 66 → 66 | 66 → 66 |

Recovery is partial and nonuniform. Seed 1's random-probe deficit closes, while
its ranked-probe deficit stays four mates. Seed 2's deficits shrink from seven
to three mates. Seed 3 has no deficit to recover but remains at 66/128, with zero
of the 25 orbits entirely solved in every arm. No probed arm beats its matched
always-enabled reference after recovery. Perfect development scores in some seed
1 arms do not establish reliable M1 mastery, final-test success or superiority of
residual-ranked growth. Each actor has still had only 384 training decisions.

Recovery training mates (out of 128) in none/ranked/random/probe_ranked/probe_random
order were 98/95/101/95/101, 81/84/84/84/84 and 55/52/55/52/55. They are on a
different scheduled block from the earlier comparison interval; do not interpret
raw phase-rate changes as a matched before/after test.

Final offline ablations:

| Seed / arms | Normal → masked | Actions changed | Mates lost / gained when masked |
| --- | ---: | ---: | ---: |
| 1 always ranked | 128 → 128 | 0 | 0 / 0 |
| 1 probed ranked | 124 → 124 | 0 | 0 / 0 |
| 1 always/probed random, each | 128 → 124 | 4 | 4 / 0 |
| 2 always ranked/random, each | 101 → 94 | 51 | 29 / 22 |
| 2 probed ranked/random, each | 98 → 113 | 35 | 10 / 25 |
| 3 all four addition arms, each | 66 → 66 | 0 | 0 / 0 |

Seed 2 again selected the same AND for ranked/random. Within each always/probed
pair, its subsequent action/outcome digests, evaluations, ablations and lifecycle
matched. These are not independent confirmations. Its probed final-policy harm
shrinks from 23 to 15 mates, but remains material; 113 is an offline masked score,
not an autonomous removal or a learned achievement.

The same condition helps its always-enabled policy (101 → 94 when masked), yet
the independently trained no-addition actor reaches 115. Thus current-policy
dependence, the benefit of adding a condition during learning, and earlier
randomized access estimates remain distinct. A single lifetime score cannot be
treated as universal usefulness or child competence.

## Confirmed lifecycle behavior and limits

The longer real-play interval exercised ordinary pruning and replacement for
the first time on this track: 10–14 base conditions retired and 9–13 new random
conditions were born per arm. Tombstones persist and block identical rebirth.
All twelve added trial instances survived and remained TRIAL, including the
harmful seed 2 probed instances. Low absolute weight is not a causal usefulness
criterion, and this experiment provides no automatic retention/maturity policy.

Final populations contain 31–32 live definitions. Additions began recovery with
33, but replacement birth uses the unchanged base cap of 32; the extra lifetime
attachment does not reserve a permanent extra slot. Seed 2's always-enabled arms
end at 31 because finite random birth attempts need not immediately refill every
vacancy. These ordinary lifecycle effects are part of the measured trajectories.
Physical graph counts, including disconnected shadow structures, are recorded in
the aggregate; they are not independent learned concepts.

New evidence: partial recovery without a coach intervention, actual retirement
and new births while preserving history, and persistent dependence on the whole
learning trajectory. This establishes operation of the existing mechanisms under
longer chess play. It does not demonstrate causally useful adaptive growth,
strategic handover, consolidation benefit or general M1/KRK competence.

## Next bounded target

Before changing usefulness rates or adding a controller, separate ordinary edge
learning from the lifecycle changes that occurred during recovery. Add one
experimental **fixed-topology recovery control**: reproduce the same first 256
actions, then suppress birth/pruning only during the fixed 128-action recovery
interval. Keep all edge learning, normal action selection and outcome feedback
active. Compare against the completed ordinary-lifecycle recovery reference.

This is a laboratory control, not a proposed permanent frozen organism. Test
that topology stays fixed while weights and decisions can change, episode-256
history reproduces, probe evidence stays intact, and coach opacity is preserved.
Declare matched seeds, roles and resources before play. Use the result to choose
a credit or lifecycle correction instead of assuming either is the source of the
remaining deficit. Do not silently extend this completed run.

The tiny independently trained two-child competence/delegation task remains a
separate planned capability. It need not wait for perfect structural discovery,
but no result here establishes learned strategic handover.
