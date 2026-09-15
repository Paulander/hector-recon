# Split budgets: cloud evidence and the reported Mac replication

Recorded 2026-09-14 from the user's pasted Mac result. The cloud run and attribution
were verified here. The Mac summary reports successful execution and exact frozen
verification; its archives are not attached to this workspace. Treat Mac numbers
as reported results pending archive inspection, not as independently reverified here.
The supplied `/Users/banquo/...` paths refer to the Mac, not the cloud filesystem.

## Results by cohort

The cloud continued deliberately selected saved guided seeds 4/5/6. The Mac built
fresh seeds 7/8/9 through the same earlier training protocol, then ran the fixed
six/twelve split-budget continuation. Each continuation arm received 768 actions.
Keep these cohorts distinct; do not treat paired arms as independent seeds or pool
them into an unbiased population estimate.

| Cohort | Seed | At continuation start | Final cap6 | Final cap12 | Measured losses |
| --- | ---: | ---: | ---: | ---: | --- |
| Cloud, verified here | 4 | 15/16 | 14/16 | 14/16 | A row4 recovered; B rows6/7 lost at endpoint. Cap12 temporarily reaches 16/16. |
| Cloud, verified here | 5 | 16/16 | 16/16 | 16/16 | None at scheduled measurements. |
| Cloud, verified here | 6 | 14/16 | 16/16 | 16/16 | None at new scheduled measurements; both recover B rows6/7. |
| Mac, user-reported | 7 | 12/16 | 16/16 | 16/16 | A row4 temporarily lost, then recovered in both. |
| Mac, user-reported | 8 | 12/16 | 16/16 | 16/16 | A rows8/9 temporarily lost; cap12 recovers one block earlier. |
| Mac, user-reported | 9 | 13/16 | 16/16 | 16/16 | None reported at scheduled measurements. |

Cloud totals are 45→46/48 under either cap; reported Mac totals are 37→48/48
under either cap. Descriptively, five of six actors finish 16/16 under each cap,
with six final-score ties. This does not prove the budgets are equivalent: the
endpoint has a ceiling, transient trajectories differ, and the last added split
receives no subsequent training under the declared schedule.

Reported Mac gains are B rows2/3/10/11 (seed7), B rows6/7/10/11 (seed8), and B
rows6/10/11 (seed9). All are retained at the endpoint. The temporary losses mean
this is evidence of acquisition and recovery, not uninterrupted retention.

| Mac seed | Cap6 splits/depth/generation/nodes | Cap12 splits/depth/generation/nodes |
| --- | --- | --- |
| 7 | 6 / 3 / 1 / 161 | 12 / 4 / 2 / 219 |
| 8 | 6 / 3 / 2 / 135 | 12 / 3 / 2 / 205 |
| 9 | 6 / 3 / 2 / 129 | 12 / 3 / 2 / 159 |

All three larger Mac actors reportedly use all six additional splits and finish
with larger physical graphs. The reported advantage is earlier recovery in seed8,
not a better endpoint. Physical node count is not the number of independent concepts.

## Interpretation for the next mechanism test

The original learner remains a credible control: all three fresh Mac actors
reportedly reach 16/16 without another learning mechanism. Do not claim these
results establish that freezing is necessary or that the learner cannot converge.
The new design target is reducing interference during learning while preserving
acquisition, rather than increasing an already saturated endpoint score.

Cloud seed4's loss was causally attributed to credit on coexisting broad competitors;
the specific B contribution survived and improved. Mac temporary losses do not
by themselves demonstrate that same cause. Their action journals are needed to
check whether duplicate functions or incomplete context separation recur.

The proposed next prototype remains context-specific ownership of local scoring
parameters: reuse immutable definitions, inherit current scores at a split, and
keep the competing-action weights private to each context. First check the
isolation property with fixed mechanical fixtures, without presenting that as
learned context discovery. A later training comparison must nominate contexts from
the learner's actual experience, preserve the outcome boundary, account for total
parameter/compute budgets, and compare acquisition plus row-level losses at fixed
milestones. Include sufficient post-split learning in a separately declared protocol.

Adaptive freezing, duplicate-credit handling and context ownership are different
interventions. Do not combine them in one first comparison or treat semantic
factoring as automatically preserving the present learning dynamics. No new
mechanism or training run is implemented/started by this consolidation.

## Mac execution report and outstanding verification

The user reports: 20 focused tests passed; 7680 training records, 60 blocks and
75 checkpoints; 124.96 seconds elapsed; peak 47040 KiB RSS; one worker and single
numeric-library threads; all 73 authoritative files unchanged before/after;
frozen verification matched; complete archive integrity check passed and contains
463 evidence files excluding the virtual environment. The protocol expects 912
scheduled evaluation actions and 912 additional frozen-verification actions; those
counts were not separately printed in the pasted result and remain to be checked.

This is a practical demonstration that the Mac can handle the bounded workload,
assuming the report is accurate. It is not a controlled hardware speed comparison:
the cohorts, initialization work and grown graph histories differ.

The completed output is called `mac-fresh-789-attempt2`. An earlier archive is
described as an initial preflight failure. Preserve both attempts. The failure's
cause, stopping point and whether any training action occurred are not established
by the summary; do not infer a protocol violation or zero earlier training without
examining its records.

Expected archives, as supplied by the user:

- `HECTOR_SPLIT_BUDGET_MAC_20260914_seed789_COMPLETE_NO_VENV.zip`
  SHA-256 `bd27b87f70c98f30446b408388d485af6e814a0e91d9e708daa808c2079ac1cb`.
- `HECTOR_SPLIT_BUDGET_MAC_20260914_seed789_INCOMPLETE.zip`
  SHA-256 `2e708607aa9c7e070f358c62dda600c50c8ae7ebbdd8d7957303beac16fa1212`.

When the archives are attached, verify hashes, source identity, schedules, block
ancestry, actual record counts and frozen results before promoting the Mac record
to independently verified. Do not retrain or repeat either attempt. Then inspect
the two transient-regression seeds at their measured loss/recovery boundaries.

Sources: user's pasted Mac report; local `RECURSIVE_SPLIT_BUDGET_RESULTS.md` and
`RECURSIVE_BUDGET_LOSS.md`. Machine-readable transcription:
`reports/autogrowth/development/RECURSIVE_MAC_REPORTED_20260914.json`.
