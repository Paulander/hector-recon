# Four versus eight owners: completed fresh comparison

Completed 2026-09-15 under the predeclared [protocol](OWNER_HEADROOM.md).
Only the maximum live owner count differed. All six actors started untrained,
used residual/current birth selection and received1920 actual training actions.
No learner, operator grammar, maturation rule, split clock or pruning setting
was changed. This is a16-row Boolean development task, not chess.

## Outcome

| Seed | Four owners | Eight owners | Eight minus four |
| --- | ---: | ---: | ---: |
| 15 | 14/16 | 13/16 | -1 |
| 16 | 13/16 | 16/16 | +3 |
| 17 | 15/16 | 14/16 | -1 |
| Total | 42/48 | 43/48 | +1 |

More owner slots win one pair and lose two. The small aggregate improvement
does not establish a reliable acquisition or retention fix. Eight-owner seed16
reaches16/16 at1536 and holds it at every subsequent measured checkpoint through
1920. Four-owner seed17 reaches16 at1408, later loses/relearns decisions several
times and finishes15. Neither eight-owner seed15 nor17 ever exceeds its final
13 or14. Four-owner seed16 peaks15 and ends13; seed15 peaks14.

## Growth cost and exposure

| Seed / owners | First scoring birth | Scoring births | Final parameters | Final physical nodes | Final live-owner visits |
| --- | ---: | ---: | ---: | ---: | --- |
| 15 / 4 | 436 | 24 | 28 | 339 | 429–434 |
| 15 / 8 | 920 | 16 | 24 | 365 | 180–187 |
| 16 / 4 | 444 | 24 | 28 | 325 | 430–434 |
| 16 / 8 | 917 | 16 | 24 | 351 | 182–188 |
| 17 / 4 | 445 | 24 | 28 | 333 | 429–436 |
| 17 / 8 | 911 | 16 | 24 | 363 | 180–188 |

The four-owner actors exhaust their three splits by192. All eight-owner actors
exhaust their seven splits by448, before the B-heavy phase begins at640. The
extra split opportunities replace scoring births, and each child starts its own
64-visit development clock. Eight-owner actors therefore create fewer scoring
conditions within the fixed global experience budget. They also have more
physical nodes despite fewer effective parameters: execution instances replicate
the deeper routes. Final expression depths are3 versus4; retained definition
counts are66/64/65 versus74/73/74. No condition is pruned in any arm, and no
additional definition/parameter/node allocation rejection is recorded.

At640, all eight-owner greedy policies are still the initial8/16 all-act-b
baseline. Their four correct A rows must not be treated as learned A mastery.
Four-owner actors have8/8,8/8 and6/8 A correctness at that boundary. A comparison
of raw subsequent A-retention percentages would therefore use unequal reference
skills. Equal global actions also do not imply equal exposure per child scorer.

Offline inspection finds the eight owners partition by x, y and the distractor
bit; each final owner still contains the two possible switch-bit states. This
is understandable from the timing: all splits occurred during A-only exposure,
when the switch bit could not provide both sides of the required support.
The learner was never supplied this task-level explanation or a desired route.
The result exposes early allocation and scoring-discovery competition as well
as residual interference; it does not isolate their individual causal effects.

## Retention and final failures

| Seed / owners | Final A / B | B rows solved at1280 | Those lost by1920 | Final failed rows |
| --- | --- | ---: | --- | --- |
| 15 / 4 | 8 / 6 | 7 | 7 | 6,7 |
| 15 / 8 | 7 / 6 | 5 | 7 | 4,7,10 |
| 16 / 4 | 8 / 5 | 7 | 6,10 | 6,10,11 |
| 16 / 8 | 8 / 8 | 7 | none | none |
| 17 / 4 | 8 / 7 | 8 | 11 | 11 |
| 17 / 8 | 6 / 8 | 7 | none | 4,5 |

Eight-owner seeds16 and17 retain all their1280 B successes at every later
measured checkpoint. Seed17 still never solves A rows4/5 anywhere in its saved
trajectory. Seed15's eight-owner arm never solves rows4/10 and loses row7 at1600.
Four-owner seed16 never solves row11, while rows6/10 are learned and then lost.
Four-owner seed17's final loss of row11 follows several recoveries, with its last
correct checkpoint at1792 and failure from1856. Full per-row histories, phase
boundaries and worst measured retention are in the machine-readable reports.

## Represented capacity versus learned weights

| Seed | Four-owner final graph admits16/16 | Eight-owner final graph admits16/16 |
| --- | --- | --- |
| 15 | No | No |
| 16 | Yes, but learned score13 | Yes, learned score16 |
| 17 | Yes, but learned score15 | No |

All three feasible cases have exactly checked rational feasibility witnesses.
For all three infeasible cases, separate nonnegative rational combinations of
the ranking inequalities give an exact contradiction. These certify the saved
graphs, not the future growing process. No fitted weights were installed or
executed, and no new environment actions were used by this offline analysis.
The missing distinctions and within-owner weight-learning problem both remain.

All final live conditions are TRIAL:28 per four-owner actor and24 per eight-owner
actor. There is no active promotion mechanism in this path. Read
[CURRENT_COMPOSITION_AND_LIFECYCLE.md](CURRENT_COMPOSITION_AND_LIFECYCLE.md) for
the distinction between engine k-of-n/nested Boolean support and current bounded
discovery, along with the precise lifecycle correction.

## Verification and disposition

All11520 training actions,2976 scheduled evaluation actions and2976 frozen
reproduction actions verify:17472 environment actions in total,180 blocks and
186 checkpoints. Initial actors differ only in the declared limit; limits remain
fixed, candidate evidence and actual scalar credit reconstruct, paired final
exploration streams match, and frozen evaluations reproduce. All81 runtime
source hashes match; all79 previous runtime sources remain unchanged.
The23 focused checks pass:3 new headroom checks,6 existing fresh-start checks
and14 existing formal-engine cases. The original52-check ownership/fresh cohort
evidence remains applicable to its unchanged source; it is not counted as a new
test invocation here. No broadened legacy rerun was required for this runner-only
setting comparison.

Runtime982.986s, peak41576 KiB RSS, one CPU, under the2-GiB and3600/3630-second
limits. No retry or extension; no training process remains running. The source
was committed before cohort play: local4f779c0a, remote1ecb5a00, identical tree.
The private run archive contains all sealed evidence and the preflight test
record, with CRC and every member SHA256 verified. Its exact archive hash and
size are in OWNER_HEADROOM_VERIFICATION_20260915.json.

Machine-readable files in reports/autogrowth/development:
OWNER_HEADROOM_20260915.json, OWNER_HEADROOM_ANALYSIS_20260915.json,
OWNER_HEADROOM_CAPACITY_CERTIFICATES_20260915.json and
OWNER_HEADROOM_VERIFICATION_20260915.json. The reporting tools are read-only.

Keep four owners as the current experimental reference; eight is not a reliable
replacement on this evidence. Further work should distinguish improving local
composition/discovery from balancing scoring development and recursive splits.
Maturation remains an explicit unimplemented mechanism, not a hidden fix already
in use. Do not launch another experiment or add those mechanisms automatically.
The private work branch is published as exact-tree snapshots; local commit
history is preserved. Main remains unchanged.
