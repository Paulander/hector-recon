# Recursive retention results: acquisition, loss and recovery

Completed 2026-09-12 on `codex/recursive-context-specialization`. The fixed
[protocol](RECURSIVE_RETENTION.md) compares flat growth, random recursive splits
and reward-error-guided recursive splits on fresh seeds 4/5/6. It uses the same
learner as the earlier pilot, without new features, rewards or learning rules.
The laboratory shifts experience from A to mostly B, then back to mostly A;
the environment's reward rule stays unchanged. These are Boolean development
results, not chess mastery or autonomous curriculum/delegation.

## Measured behavior

Final correct actions out of all sixteen rows:

| Seed | Common prefix | Flat | Random splits | Guided splits |
| --- | ---: | ---: | ---: | ---: |
| 4 | 12 | 12 | 12 | **15** |
| 5 | 8 | 8 | 12 | **16** |
| 6 | 12 | 12 | 12 | **14** |
| Total | 32/48 | 32/48 | 36/48 | **45/48** |

Each cell below gives **A correct / B correct**, each out of eight. All arms
receive the same scheduled examples within a seed and matched exploration draws.

| Seed | Arm | Prefix256 | After mostly B:640 | After return to mostly A:1024 |
| --- | --- | --- | --- | --- |
| 4 | Flat | 7 / 5 | 4 / 8 | 4 / 8 |
| 4 | Random | 7 / 5 | 4 / 8 | 6 / 6 |
| 4 | Guided | 7 / 5 | 4 / 8 | 7 / 8 |
| 5 | Flat | 4 / 4 | 4 / 4 | 4 / 4 |
| 5 | Random | 4 / 4 | 4 / 8 | 4 / 8 |
| 5 | Guided | 4 / 4 | 4 / 8 | 8 / 8 |
| 6 | Flat | 8 / 4 | 4 / 8 | 8 / 4 |
| 6 | Random | 8 / 4 | 4 / 8 | 8 / 4 |
| 6 | Guided | 8 / 4 | 5 / 8 | 8 / 6 |

Guided and random actors both learn all B rows at episode 640. Of the **eleven
new B successes**, guided retains **nine** at the final return measurement;
random retains **five**. Flat learns seven new B rows and retains three. Guided
therefore shows better final B retention than the random control in this run,
alongside better final A performance (23/24 versus 18/24).

However, guided splits do not prevent forgetting during acquisition. During the
first shift they lose **eleven of nineteen original A successes**, versus ten
for random and eight for flat. Guided also gains five different A successes,
which hides some turnover in the aggregate count. Seed 5 is a particularly clear
example: its guided A total stays 4/8, but **all four originally solved A rows
are replaced by four different successes**. Initial A proficiency also varies
substantially; this is not a comparison of three mastered initial skills.

Relative to the complete prefix policies, final guided actors gain14 rows and
lose 1; random gains 6 and loses 2; flat gains 4 and loses 4. Guided seed 4's final A
total matches its prefix 7/8, but it gains row 13 and loses row 5. Guided seed 6 loses
newly acquired B rows 6/7 after returning to mostly A. Seed 5 temporarily loses two
B successes at episode 896 before recovering to 16/16. Final totals do not imply
uninterrupted preservation of the same decisions.

## Structure and interpretation

Every recursive arm performs six splits and reaches generation 2: an already
refined descendant is refined again. Guided maximum expression depth is 3 in all
seeds; random reaches 4/3/3. This is actual nested growth during learning. It
does not establish a hierarchy of goals or a learned growth policy.

| Seed | Flat contributions / physical nodes | Random | Guided |
| --- | --- | --- | --- |
| 4 | 11 / 85 | 15 / 153 | 14 / 139 |
| 5 | 11 / 81 | 13 / 147 | 12 / 123 |
| 6 | 13 / 89 | 12 / 133 | 11 / 121 |

Guided outperforms random with fewer final contributions and physical nodes in
these three seeds. Still, matched caps and opportunities are not matched total
computation, proposal histories or realized graph sizes. This small contextual
toy supports further work on guided specialization, with better recovery and
endpoint retention here. It does not show global consolidation or a universal
advantage. The shared credit law, other plastic contributors and action-dependent
candidate contexts remain relevant possible sources of interference.

The next focused investigation should use these complete journals to attribute
guided seed 6's lost B rows and seed 4's exchanged A row to actual credit and
structural events. Check whether active contributions span both contexts and
whether residual-selected distinctions separate the behaviors that interfere.
Do this before adding another retention law or migrating chess actors. No new
training run has been started after this comparison.

## Verification, limits and the stopped attempt

The successful corrected run at **`2170daab`** took **161.568 seconds**, one CPU
core, peak RSS **34628KiB (33.82MiB)**, under its ten-minute/2-GiB limits. All
**7680 training + 912 scheduled evaluation actions** completed. All **60 blocks,
72 checkpoints and 7680 scheduled training records** pass hash, order, reward,
participating-weight-update and checkpoint checks. Initial arm states and paired
exploration states match. A separate frozen verification reproduces all 57
evaluations: **912 additional evaluation actions**, zero training updates.
There are no missing records or unresolved completion markers in this run.

**33 distinct focused tests** passed: the eight recorder tests, seven recursive
mechanism tests, and eighteen existing terminal/choice tests. The runtime learner,
formal engine and chess adapter were not edited. Synthetic journal probe records
are file-system checks, not learner actions or experimental experience.

The initial attempt at `4afc34a4` remains separately closed and incomplete. It
stopped after 30.514 seconds when deleted partial-log paths reappeared as shorter
exact prefixes of sealed journals. The cause is undetermined; it was not a
resource exhaustion. Its **1536 training records, 176 scheduled evaluation
actions and fifteen checkpoints** are intact, with all 176 evaluation actions
reproduced offline. It is not counted as another independent seed or complete arm
comparison. Its overlapping 1536 training records match the corrected attempt
byte-for-byte, supporting that the recorder repair preserved that trajectory.

The [documented correction](RECURSIVE_RETENTION_RECORDER_CORRECTION.md) retains a
bounded progress log and writes completed evidence to a separate exclusive file;
it never relies on deleting or renaming progress files. No actor was resumed from
the stopped attempt. Both attempts, their exact source snapshots, and the earlier
unexpected duplicate files are preserved in the checkpoint archive.

Machine-readable results:
[complete run and row analysis](../../reports/autogrowth/development/RECURSIVE_RETENTION_20260912.json).
No training or background task remains active. Results are committed locally;
no GitHub publication was performed.
