# Action-conditional owner nomination: bounded result

Completed 2026-09-16 on branch `codex/context-owned-decisions`. This is a
two-action Boolean mechanism test, not chess or a mate-in-2 result. The raw
directory is `snapshots/autogrowth/owner-action-contrast-20260916-seeds30-32`.
The completed seeds 21–23 cohort was not resumed or modified.
The ZIP archive `reports/autogrowth/development/HECTOR_OWNER_ACTION_CONTRAST_20260916.zip`
includes this completed raw run and both preserved preliminary failures. Its ZIP
CRC check passes; SHA-256 is
`22c18fbdc6f21bcad2096d027b4ad5e0866132b61f40fa208cc7ea5e741a0ef2`.

## Decision

Do not promote or extend the action-contrast nominee. It improved against the
existing learning-trial in only one of three fresh paired seeds, tied one and
lost one. It remained below the current reference in two seeds, tied one, and
accepted an irrelevant noise-bit root split in seed 32. The predeclared
continuation gate failed. Keep the current owner learner as reference.

| Seed | Current | Learning-trial | Action-contrast | Final physical nodes (same order) | Final parameters (same order) |
| --- | ---: | ---: | ---: | --- | --- |
| 30 | 15/16 | 14/16 | 12/16 | 321 / 403 / 561 | 27 / 34 / 49 |
| 31 | 14/16 | 12/16 | 12/16 | 321 / 623 / 339 | 28 / 56 / 38 |
| 32 | 14/16 | 12/16 | 14/16 | 333 / 523 / 361 | 27 / 44 / 30 |
| Total | 43/48 | 38/48 | 38/48 | | |

All arms started at 8/16 and finished with 8/8 in context A. Remaining errors
were in context B. Action-contrast mature split counts were 1/0/3 across seeds;
the existing learning-trial had 2/1/1. Pending counts were 2/1/0 versus
1/1/2 respectively. These are finite-run structural observations, not proof
that any mature partition is semantically correct or beneficial long-term.

## Mechanistic failure exposed

The new nomination score measures a difference-in-differences of actual-action
residuals across route sides, with four observations required per action/side
cell. Synthetic tests show it rejects an exact common residual shift and
recognizes an exact action-preference reversal. In live play, that four-cell
support rule creates a selection bias when the policy strongly favors one
action. At seed 32 episode 128, only 8 of 128 actions had been `act-a`.
The root route for noise coordinate 3 had four `act-a` observations on each
side, so it was eligible with score 1.3700. An x route had 1 versus 7
`act-a` observations across its sides, y routes had a zero cell, and the
context-z route had no opposite-side observations. Thus noise was the only
eligible route; it was not selected over fully supported task-relevant routes.
That noise root was prospectively accepted at episode 631 with +0.2357 access
gain. Later x/y descendants helped the policy reach 14/16, but the irrelevant
root and lack of perfect ranking remain. This directly falsifies the hope that
the four-cell score alone would prevent such partitions. The exact reason for
the prospective noise access gain (sampling, time-varying weights, or copied
scorer dynamics) is not isolated by this experiment.

Seed 30 shows the opposite cost: the first action-contrast root nomination
waited until episode 128 versus episode 64 under learning-trial. Its x root
accepted, but two deeper trials stayed in probation; the endpoint was 12/16
with 561 nodes, against learning-trial's 14/16 with 403 nodes. Seed 31 had
two pruned action-contrast roots and no mature split, ending at 12/16. The
criterion can therefore both delay useful specialization and admit noise.

## Integrity and limits

The final attempt ran one worker with numerical-library threads fixed to one,
an independent 2 GiB Mac RSS guard and 3,600-second wall bound. It finished in
853.19 worker seconds. The Python process `ru_maxrss` was 61,997,056 bytes
(59.13 MiB); the JSON field is historically named `max_rss_kib`, but Darwin
reports bytes. All 17,280 training actions, 4,464 scheduled evaluations,
4,464 independent frozen evaluation reproductions, 270 sealed blocks and 279
checkpoints passed source-hash and actual-record verification. Action-contrast
four-cell counts/sums were reconstructed from immutable executed-action records.
No unchosen action outcome was fed to a learner.

Two preliminary harness failures are retained separately: an empty directory
from macOS rejecting `RLIMIT_AS` before any action, and an incomplete seeds
27–29 attempt after only seed 27's current arm completed 1,920 actions. A
report-assembly field assumption caused the latter stop. Neither contributed
learning input or a paired comparison. The learner law and parameters were
unchanged through the portability/report fixes. These attempts mean the final
cohort should be read as a bounded exploratory test, not a pristine registered
confirmatory study.

An optional no-play exact capacity analysis was attempted but could not run:
the available Python environment lacks SciPy. No weights were fitted or
installed. The endpoint score and route evidence above do not rely on it.

The narrow next scientific question is how to obtain action coverage for
candidate partitions without making whichever route happens to have rare-action
coverage win by default, and how to distinguish transient child-scorer benefit
from a useful route. That requires a new explicit hypothesis and bounded test;
this result does not authorize extending the current pilot or moving to M2.
