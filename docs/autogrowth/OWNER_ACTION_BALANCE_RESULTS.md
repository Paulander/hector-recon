# Owner-local action coverage: bounded result

Completed 2026-09-16 on `codex/context-owned-decisions`. This is a two-action
Boolean mechanism test, not chess. The source-pinned raw directory is
`snapshots/autogrowth/owner-action-balance-20260916-seeds33-35`.
The complete raw ZIP is
`reports/autogrowth/development/HECTOR_OWNER_ACTION_BALANCE_20260916.zip`;
its CRC check passes and SHA-256 is
`2c6fe1c376b76459df1a827cb2de37eaf57bed8d0c58518500a4fa43ab9c4214`.

## Result and decision

The local exploration intervention worked mechanically: it sampled the rare
action more often and made task-relevant x routes eligible earlier. Its final
greedy score beat action-contrast in two paired seeds, but tied the current
reference in aggregate and used more stored structure. Only one owner-balanced
seed accepted any structural split. This meets the narrow preregistered
condition for a separate replication, not promotion, a chess claim, or an
automatic longer run. Preserve the current owner learner as reference.

| Seed | Current | Action-contrast | Owner-balance | Final physical nodes (same order) | Final parameters (same order) |
| --- | ---: | ---: | ---: | --- | --- |
| 33 | 14/16 | 13/16 | 12/16 | 329 / 411 / 391 | 28 / 47 / 43 |
| 34 | 14/16 | 12/16 | 14/16 | 325 / 341 / 711 | 28 / 39 / 64 |
| 35 | 12/16 | 12/16 | 14/16 | 329 / 357 / 391 | 28 / 40 / 43 |
| Total | 40/48 | 37/48 | 40/48 | | |

All arms began at 8/16. Every endpoint was 8/8 on context A; all remaining
errors were in context B. Owner-balance seed 34 briefly reached 14/16 and
retained it to the endpoint, but its 711 nodes and 64 parameters were over
twice the current arm's node allocation and hit the parameter cap. This is a
costly candidate, not a demonstrated efficiency improvement.

## What the mechanism did—and did not do

The intervention changes only which action receives the existing bounded
stochastic exploration boost. The boost is directed toward a least-sampled
action of the formally active owner; the graph still chooses and executes.
The exploration rate, rewards, split nominee/acceptance laws and budgets are
unchanged. Per-owner action counts reconstructed exactly from submitted real
actions at every checkpoint. In the first 64 actions, executed `act-a` counts
were 8 vs 15 (seed 33), 4 vs 14 (34), and 7 vs 18 (35), action-contrast versus
owner-balance. This is direct evidence of improved rare-action coverage, not
evidence that the organism learned a better action value.

The first owner-balance nomination occurred at episode 64 in all seeds and
selected an x-coordinate route, with action-contrast scores 47.574, 49.452,
and 56.549 respectively. The comparator selected x at episode 64 in seed 33
but waited until 128 in seeds 34/35. No noise route was promoted at the root.
Thus the prior noise-only eligibility failure was absent in this sample.

However, every first x split in both trial arms was prospectively **PRUNED**
after two assessment windows. A high action-conditional residual contrast
correctly identifies a local policy distinction but does not establish that
separate child scorers improve actual reward beyond an already plastic parent.
Owner-balance seed 34 later accepted one y split at episode 1371 with +0.2085
access gain; two later candidates remained provisional. Seeds 33 and 35 had
zero mature splits. Seed 35's 14/16 endpoint therefore cannot be credited to
accepted structural growth; it arose along a different ordinary
exploration/weight-learning trajectory. Its final third root candidate was a
noise-coordinate trial, not mature. All three owner-balanced endpoints remained
below 16/16.

The active owner branch still receives the actual action's scalar reward
through its active condition weights, and conditions record local outcome
correlations. Parent SCRIPT nodes do not have independent learned local
rewards that compound into higher-level goals. The experiment did not add
such a hierarchy. Whether a parent/child credit contract would improve
structural usefulness is a separate architectural hypothesis; rewarding
activation alone would risk self-serving but externally useless subgoals.

## Integrity and scope

21 focused tests passed before play. The study completed in 709.33 seconds,
within the one-worker 3,600-second and 2 GiB Mac RSS guard. The process
`ru_maxrss` was 62,537,728 bytes (59.64 MiB); the JSON key `max_rss_kib`
is inherited from the Linux runner and misnames Darwin's byte unit. All
17,280 actual training actions, 4,464 scheduled evaluations, 4,464 frozen
evaluation reproductions, 270 sealed blocks and 279 checkpoints verified.
Source hashes, trial histories and every per-owner action count were checked;
no unchosen action outcome was credited. The three paired seeds are
descriptive, not a reliability estimate. No continuation has been run.

The result shifts the next question away from mere nomination coverage:
does an apparently relevant route need independent scorer copies at all,
and if so what locally observable, externally grounded credit allows those
copies to become useful without rewarding arbitrary activation? Investigate
that from saved evidence before another learner change or a longer run.
