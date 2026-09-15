# Owner nomination pilot: development operates, benefit not demonstrated

2026-09-14, `codex/context-owned-decisions`, implementation `e39d332a`.
The [fixed protocol](OWNER_NOMINATION_PILOT.md) was declared before pilot play.
All assigned play finished. The original final verifier failed on shortened
progress copies; retain its `incomplete` result. A separate read-only audit
verified the sealed records and every saved evaluation without repeating training.

## Results

Correct decisions out of all 16 supplied Boolean rows:

| Seed | Arm | Prefix 128 | 192 | 256 | 320 | Final 384 | Final owners | Effective parameters | Physical nodes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | Splitting disabled | 8 | 8 | 8 | 8 | 8 | 1 | 13 | 87 |
| 10 | Splitting enabled | 8 | 8 | 8 | 8 | 8 | 4 | 36 | 377 |
| 11 | Splitting disabled | 8 | 8 | 8 | 8 | 8 | 1 | 12 | 77 |
| 11 | Splitting enabled | 8 | 8 | 8 | 8 | 8 | 4 | 36 | 367 |

Each source had eight scoring conditions plus bias. Both enabled actors nominated
three splits from their own actual residuals, reaching expression depth three.
Neither enabled actor added a new scoring condition after conversion. Disabled
seed 10 added four and seed 11 three. No contribution was pruned in any arm.
Splitting produced more structure with no final-score advantage in this pilot.

Totals conceal changes. Seed 10 always chose action-b in frozen evaluation, with
exactly the same eight successes. Seed 11 in both arms gained A row 4 and lost A
row 12 at 192; those changes remain at the endpoint. Its enabled arm also gained A
row 0 and lost A row 8 at 320, then reversed that pair at 384. Thus there is still
within-context behavioral replacement, even though every measured total is8.
Both arms received 128 A and 128 B continuation actions. Seed 10 received 61/69
positive A/B outcomes in either arm; seed 11 received 64/60 in either arm.

These prefixes had not acquired a competent initial policy: each solved 4/8 of A
and 4/8 of B. The declared 128-action prefix was too short for this realized source
vocabulary to make a convincing learned-skill retention benchmark. Seeds were not
selected or discarded by outcome, and the schedule was not extended after seeing
this. The result is a development-mechanics pilot, not a verdict on ownership's
retention value relative to the stronger earlier recursive learners.

## What actually grew

Coordinate names below are offline interpretations; the learner used numbered
terminal coordinates and never received the environment's target formula.

| Seed | Event | Visited owner | Nominated route | Actual samples false/true | Score |
| --- | --- | --- | --- | --- | --- |
| 10 | 192 | 0 | y=true | 32/32 | 9.691215 |
| 10 | 319 | 1 | noise=true | 32/32 | 1.197790 |
| 10 | 320 | 2 | z=false | 32/32 | 3.949977 |
| 11 | 192 | 0 | y=false | 32/32 | 5.927839 |
| 11 | 318 | 1 | z=true | 32/32 | 4.301594 |
| 11 | 320 | 2 | z=true | 32/32 | 4.656936 |

Seed 10 spent one split on the task's irrelevant fourth coordinate. Residual
separation can reflect sampling and changing predictions; it is not a certificate
of a useful decision boundary. No nominee was rejected by a graph budget here.
The final children received only 4–28 subsequent visits each, below the 64 visits
needed for their next development opportunity. Do not assume their eventual value.

## Exact representational limitation

For an action score, a state-only contribution gives both actions the same support:

    Q(b)-Q(a) = sum_j w_j [phi_j(s,b)-phi_j(s,a)].

If every bracket is zero, changing those weights cannot affect the choice. A
state-only route multiplying such a scorer cannot create an action difference.
This is mathematical accounting of frozen definitions, not a trained repair.

Seed 10's prefix contained no action-dependent condition at all. Its enabled arm
copied that limitation into four contexts; all 16 rows still have structurally
identical action features. Its disabled arm finally birthed an action-dependent
condition at 384, but that zero-weight newborn had no subsequent training. It
distinguishes only four rows, and other required action-a rows remain forced ties.

Seed 11's prefix and both endpoints can distinguish actions on 10/16 rows. Rows 1,
3 and11 require action-a but have equal action feature vectors for every scoring
parameter. Formal tie selection prefers action-b. Those exact witnesses prove
that no weight assignment in these endpoint structures can solve all 16 rows.
The raw terminal vocabulary does expose the action binding; it is the grown
compositions that fail to make sufficient use of it.

Two supplied development choices matter here: a successful split substitutes for
a local birth proposal, and children start their own 64-visit development clocks.
Both enabled arms used every realized opportunity for splitting, so neither
created new scoring features. This identifies a possible conflict between
partitioning and discovering useful action distinctions. It does not establish
that adding one particular feature or simply lengthening training will solve it.

## Verification and resource evidence

- 267 distinct tests passed:46 focused/new plus221 required compatibility tests.
  Four runner tests were repeated after the preflight schedule reduction; they
  are included in267, not counted twice. The original learners/formal core were
  unchanged. Test evidence is in `OWNER_NOMINATION_CHECKS_20260914.json`.
- 1280 rewarded training actions,288 scheduled evaluations,20 completed blocks
  and26 checkpoints have verified sealed records and ancestry. All 68 snapshotted
  authoritative sources still match. Actual candidate observations and local
  credit arithmetic verify against the completed journals.
- Worker elapsed 73.284 s, peak RSS 37,688 KiB, one CPU;2GiB address-space ceiling,
  540s worker/570s independent wall caps. No resource limit was approached.
- The original verifier reproduced 64 frozen actions before failing on a progress
  manifest. The independent audit reproduced all 288 scheduled actions on disposable
  clones in 14.182 s, peak RSS 35,652 KiB. Total frozen verification executions are 352;
  no training was repeated. Pilot environment executions total 1,920 including this
  additional verification. The separate discarded calibration executed 32 training
  and 32 evaluation actions and supplied no actor to the pilot.

Six progress/submission copies in three blocks had become exact shortened prefixes
of their originally sealed contents: seed 10 unsplit320 retained 63/64 records,
seed 10 adaptive192 retained 62/64, and seed 11 unsplit128 retained 62/64. For every
copy, the complete corresponding sealed journal (or its submission-field projection)
matches the original manifest hash exactly. All other manifest files, including
the sealed 1,280 training records, checkpoints and evaluations, match directly.
No absent record was invented or regenerated through training. The shortened files
and failed original report are preserved unchanged. The cause of the copy changes
is not established; do not relabel the raw run as a clean verification pass.

The independent audit is `scripts/autogrowth/audit_owner_nomination.py`; its exact
source hash and findings are recorded in
`reports/autogrowth/development/OWNER_NOMINATION_20260914.json`. It never calls
`observe`, grows an actor, installs diagnostic weights or edits the raw evidence.

## Decision and next checkpoint

Keep whole-decision ownership experimental. It has tested score inheritance and
inactive-context credit isolation, and now actual-experience nomination, but no
demonstrated performance benefit here. It does not implement a common physical
trunk, safe shared trainable knowledge, merging, freezing/reopening or goal control.

Before another training comparison:

1. Make action-sensitive feature discovery and contextual partitioning coexist
   under a generic local rule. Evaluate nomination in relation to competing action
   scores, not just absolute selected-action reward errors. No task-label gate,
   fitted repair or forced action feature may enter as a claimed discovery.
2. Separate a cold-start acquisition test from a retention test using a fixed
   existing cohort with learned behavior; include all declared actors. Keep the
   original contributor-split learner as a necessary baseline. The present two-arm
   pilot is not the planned contributor/ownership/local-freezing comparison.
3. Use independently sealed immutable per-action evidence for future interrupted
   runs, and investigate the recurring progress-copy behavior before relying on
   streaming copies as the only evidence. Do not repeat this pilot automatically.

No process remains running. No follow-up training or publication was performed. Read
[the pedagogical explanation](OWNER_DEVELOPMENT_EXPLAINED.md) for the larger status.
