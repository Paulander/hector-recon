# Fivefold owner-nomination experiment

Declared 2026-09-14 before training, on `codex/context-owned-decisions` after
`471fd3bd`. The user explicitly requested repeating the last experiment with
five times the training. This authorizes this separate run; the original raw
pilot and its incomplete verification status remain untouched.

## Fixed intervention

Use the same seeds 10/11, original environment, learner source, rates, exploration,
candidate law, pruning grace, local 64-visit interval and all graph budgets.
Only the experience schedule and evidence recorder change. No feature, nominee,
correct action or fitted weight is supplied to training.

Multiply every training phase by five: the original 128-action prefix becomes
640; each original 128-action mostly-B and mostly-A phase becomes 640. Repeat
each original phase's exact order five times. Thus the first 128 source actions
must reproduce the prior source actors exactly, including random state. Conversion
to owner runtime now occurs at 640. The recursive learner's own prefix parameter
stays at 128; no learner configuration is changed to match the harness duration.
The longer source learning can change inherited conditions/candidate vocabulary;
this is not a continuation from the previous four-owner endpoints and does not
isolate child exposure from the effect of the longer initial learning phase.

Each seed forks once into splitting enabled/disabled, with identical copied state
and the same schedule. Final endpoint is 1,920 decisions. Use all assigned actors
and report every scheduled measurement irrespective of scores.

- Exactly 6,400 training actions: two 640-action prefixes, four 1,280-action arms.
- Save every 64 actions. Evaluate both prefixes at 128 and 640; evaluate all
  continuation blocks: 1,344 scheduled frozen actions in total.
- Verify each recorded evaluation once more on disposable clones: 1,344 separate
  verification actions. No training replay is used to fill missing evidence.
- Exactly 100 training blocks and 106 checkpoints, counting six initial states.
- One CPU, one worker, numerical libraries one thread, 2 GiB address space,
  64 MiB individual-file ceiling, 1,200-second worker wall/CPU budget, independent
  GNU timeout at 1,230 seconds with a five-second kill grace. These are hard caps,
  not expected durations. About 29 GiB was free at preflight; individual action
  records are expected to remain well below 100 MiB overall.
- Preserve any partial attempt. No automatic second attempt or extension.

The earlier 73-second run supports a minutes-scale estimate, but bigger graphs and
more births can increase per-action cost. The generous bounded cap covers that
uncertainty without risking an unbounded process. No new calibration actor is
required or injected. Monitor progress while it runs.

## Evidence recorder change

After each actual selected action/outcome, write one exclusive immutable submitted
record before feedback. After feedback, write a separate exclusive credited record.
Completed blocks also receive a sealed training journal, checkpoint, evaluation and
recursive hash manifest. There are no growing progress files. Verify every action,
actual reward and normalized credit increment; verify all per-action records agree
with the sealed block. Tests must establish trajectory equivalence to the previous
recorder and preservation of an executed action if feedback processing fails.

Hash every previously snapshotted learner/core source before play and bind this
runner/protocol to a new source snapshot. Reuse the prior full 267-test compatibility
evidence for unchanged source; run focused recorder and owner tests for this change.

## Interpretation and next decision

Report gains/losses by row, local context visits since birth, development opportunities,
new scoring conditions and their action sensitivity, pruning and realized cost.
Equal total samples do not imply equal context exposure or equal computation.
Neither the fourfold context cap nor fivefold training guarantees sufficient visits
to rare contexts. Newly installed conditions have only subsequent visits to learn.

If increased experience changes the observed learning benefit, revise the earlier
conclusion before changing the mechanism. Otherwise proceed with the planned local
investigation of action-sensitive discovery and competition between splitting and
ordinary births. In either case, retain the original contributor-split learner as
the future baseline. This two-arm toy study does not establish chess transfer,
compact common-trunk sharing or reliable retention.
