# Learning before split assessment: implemented; comparison interrupted

The revised local lifecycle is implemented and published on the private work
branch. **The fixed comparison is incomplete.** The execution session disappeared
without a worker result or exit record. No worker was visible afterward, and the
surviving files stayed unchanged during audit. The cause is unknown; this is not
evidence of a learner assertion failure, a resource-limit exit or a frontend-only
problem. No retry, extension or main merge was performed.

The [predeclared protocol](OWNER_TRIAL_LEARNING.md) gives each continuing parent
and each child 64 actual controlled actions before assessment. It then assesses
256 prospective requests, retains an unproven live candidate for one second
assessment at 512, and imposes a 1,536-request lifetime. The existing gain and
support thresholds stay unchanged. Weight learning and ordinary local growth
continue throughout. No labels, offline fitted weights or external network coach
enter the learner. This is a combined readiness/timing/review change; its parts
are not isolated causal interventions. Final same-owner exclusion still exists.

## What actually ran

The source was pinned before play at local
`51140753e256e8cbd9d50651cc3413aa14355810`, published as remote
`5277b06cc527cadaef20d818d70fb2d66db5409b`, with identical tree
`5f1cfbbcf1a5e865a4c81d2adf9e4661817710f7`.
All 86 runtime source hashes match. All 83 files shared with the previous trial
run are unchanged; the old protocol remains in git but is outside this run's
runtime snapshot. Current and original-trial learner implementations are unchanged.

| Seed 21 learner | Score at common action 1,536 | Saved endpoint | Endpoint score |
| --- | ---: | ---: | ---: |
| Current ownership | 15/16 | 1,920 | 16/16 |
| Original trial rule | 11/16 | 1,920 | 11/16 |
| Learning-before-assessment | 13/16 | 1,536 | 13/16; interrupted |

The revised learner has 39 additional submitted and credited actions, through
local event 1,574, but no checkpoint or evaluation for that partial block. They
remain preserved as an unsealed tail. Do not treat its 1,536 checkpoint as a
1,920-action result or discard/replay those 39 actions silently. An unrecorded
in-flight execution cannot be excluded. Seeds 22 and 23 never started.

Recorded totals are **5,415 training actions**: 5,376 in 84 sealed blocks plus
39 in the tail; **1,392 scheduled evaluation actions**, **87 checkpoints**.
The planned frozen reproduction phase never began. No environment actions were
executed during the interruption audit. Total worker duration and peak memory
are unavailable; the last progress line records 368.87 elapsed seconds. The
initial limits were one CPU, 2 GiB, 3,600 worker seconds and a 3,630-second
independent timeout; no surviving exit record identifies which event stopped it.

## What this does establish

The two trial learners have **identical first 320 complete action records**.
Their first candidate is the same root x split, born at action 64. The original
rule retires it at 320 with split-minus-parent mean reward of -0.3124. The revised
learner preserves that candidate and its weights/history. Its children reach
64 actual actions each at episode 339; parent/child learning exposures are
140/71/64. Over the next 256 prospective requests, reward gain becomes +0.8265,
with 123 parent outcomes and 133 child outcomes (65/68 per child). It accepts at
595, before the A-to-mostly-B schedule change at 640.

Thus one early-negative candidate really did become useful under continued
learning in the observed A exposure. This supports the timing concern. It does
not show that all later structure is useful, that full-time training would have
had the same effect, or that the revised learner wins the final comparison.
The comparison uses an adaptive policy and a finite experimental acceptance rule,
not a calibrated guarantee of causal usefulness.

At interruption, the revised learner has two committed owners and two further
PROBATION trials, both testing y inside a different x owner. They started at
708/713 and became ready only at 1,242/1,301. Their prospective windows contain
147/114 region requests at checkpoint 1,536, below the required 256. Neither has
had its first assessment; neither has earned acceptance. Their partial reward
gains are -0.1407/-0.0298, diagnostic observations only. The second-review rule
has passed a mechanical fixture but has not yet been exercised in this cohort.

The revised learner preserves all eight A successes from 640 and all five B
successes from 1,280 through every later *available* checkpoint. It still fails
rows 2, 3 and 15. Its committed graph at 1,536 lacks joint 16/16 ranking capacity,
proved by an exact nonnegative contradiction. This certificate concerns the saved
committed graph, not the capacity of pending candidates or continued growth.
The original trial endpoint also lacks joint capacity. Current ownership has a
verified rational witness and actually holds 16/16 from 1,792 through 1,920;
it had temporary A losses earlier, so this is not loss-free learning from zero.

At their respective saved endpoints, nodes/parameters are current 335/28,
original trial 143/21, revised 463/39. The revised allocation includes six stored
scorers for two committed owners plus two parent/children comparisons. All four
reserved-owner slots are occupied. These are unequal-duration endpoints; they
illustrate storage costs, not a fair final efficiency ranking. Ordinary scoring
births started at 64 in both trial arms versus 442 in current ownership.

## Verification and recovery boundary

35 distinct focused checks passed, including five new actual-action lifecycle
fixtures. Those five passed again on final source. They cover exposure readiness,
prospective evidence, live reconsideration without resetting history, rejection
at finite lifetime, exact checkpoint continuation and unchanged controls.
The previous 58-check control evidence is retained for unchanged source.

The no-play audit verifies all 84 block manifests, checkpoint chains, actual
scalar updates, owner-local residual/birth histories, trial readiness/reviews,
formal raw-coordinate probe flags, and independent assignment RNG draws.
All **1,392 saved evaluation choices** also match direct score arithmetic.
The 39 tail records match their submissions, declared rows, actual reward law,
credit arithmetic and probe/RNG flags; no saved post-tail actor exists to verify.
The first audit is preserved in `OWNER_TRIAL_LEARNING_PARTIAL_20260915.json`;
the expanded audit adds owner residual reconstruction and the matched 320-record
prefix in `OWNER_TRIAL_LEARNING_AUDIT_20260915.json`, under
`reports/autogrowth/development/`. Both executed zero environment actions.

The raw run remains in `snapshots/autogrowth/owner-trial-learning-20260915/`.
Its `interruption.json` is explicitly an observer record, not a fabricated
worker `result.json`. Raw evidence, checkpoints, unsealed tail, test XML and log
are saved in `HECTOR_OWNER_TRIAL_LEARNING_PARTIAL_20260915.zip`:
10,631,144 bytes; 11,269 members; all 11,268 payload hashes and ZIP CRCs verify.
SHA-256: `a4e0b2f9dbc66661f3b11239e7943891385c9ef1efea79f4dcbe37554b92c676`.
Git-backed code/reports remain in the private repository and are referenced by
source commit/hash rather than duplicated in the raw archive.

Keep current ownership as the reference. Do not merge this into main based on
partial evidence or retune the lifecycle from these scores. Before another play
attempt, explicitly specify recovery accounting for the 39 uncheckpointed actions
and execution-session loss. The predeclared one-attempt/no-retry protocol does not
authorize silently restarting or extending this interrupted cohort. Preserve
all surviving evidence and keep any future attempt separately identified.
