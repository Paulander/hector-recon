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
