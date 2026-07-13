# Generic-Core Support-Directed Exploration Work Package

Date: 2026-07-13. Track: generic-core development. Status: PI-authorized and
frozen before implementation or fresh execution.

## Basis, hypothesis and strongest null

Independent reconstruction of the closed challenger-throughput artifact found
all four target cue-by-regime-by-action structures proposed in every hardest
task. All adequately supported target candidates matured (60/60), but one
correct-action activator per task was always pruned unsupported. Its median
reservoir support was 8.5 against the required 32. Only the selected action
channel is currently trained and stored, so the old policy can suppress the
action whose challenger needs evidence.

Hypothesis: allowing an active trial composite to direct an exploration event
that would already occur will break this self-confirming loop, supply adequate
action-conditioned evidence, mature all four target structures, and recover the
changed mapping without changing exploitation or total exploration.

Strongest null: support-directed probes do not increase minimum target support,
reduce unsupported target deaths, or improve mastered behavior relative to a
matched shuffled-responsibility control; alternatively they damage retention or
consume unequal exploration/resources.

## Learner and laboratory boundary

Use fresh seeds 20262101--20262120 and only the hardest anonymous demand m=2.
Each seed builds the same 4,096-episode regime-0 checkpoint and quiescence
boundary as the closed packages. Require development success >=0.85, prune
unfinished trials without another observation, prove behavior unchanged, and
clone the complete checkpoint into every arm. Freeze shared biases and primitive
weights byte-identically.

Generate 4,096 matched regime-1 experience rows and 512 old/512 new evaluation
rows per seed. The learner receives anonymous active terminals, legal action
IDs, graph/candidate state, selected scores, terminal return and its own
learner-local counters. It never receives cue meaning, action role, regime
meaning, changed-mapping flags, correct actions, target-candidate identity,
evaluation verdicts, cohort names or demand.

The laboratory may reconstruct the four relevant
cue-by-regime-1-by-door-action candidate identities only after execution for
measurement. Those identities may not affect proposals, exploration, learning,
rent, promotion, retirement or action scores.

## Exactly one changed scientific factor

The factor is allocation of already scheduled exploration actions. Exploration
rate, event timing and event count remain fixed. On non-exploration decisions,
all arms use the unchanged greedy policy. Trial candidates remain absent from
exploitative action scores and deployed graph roots.

Arms:

1. **fixed-8 ranked** -- the successful positive reference.
2. **rent batch-4 ranked** -- exact negative-mechanism replication with ordinary
   random exploration.
3. **rent batch-4 support-directed** -- on an ordinary exploration event, choose
   the legal action requested by the most under-supported active trial.
4. **rent batch-4 support-shuffled** -- same exploration-event schedule and
   request set, but choose a uniformly shuffled active request without using its
   support deficit.

Every rent arm keeps batch allowance 4, mature capacity 32, temporary ceiling
36, proposal interval 128, review interval 512, reservoir 2,048, minimum rent
support 32, all rent thresholds, retirement, nomination, candidate family,
learning rates, clipping, shared freezing and lifetime proposal budgets
unchanged.

## Frozen request mechanism

The request emitter is the existing shadow trial composite SCRIPT with its two
anonymous terminal-member legs. No new node family or semantic terminal is
introduced.

At every decision, the ordinary policy draws exploration exactly as before. If
the decision is exploitative, the request mechanism cannot act. At an
exploration event:

1. Enumerate trial candidates whose associated action is legal and whose two
   member terminals are active.
2. Candidate-local post-birth support is its activation count: the number of
   selected-action observations on which that shadow predicate was active.
3. Its support deficit is max(0, 32 minus post-birth support). Candidates with
   zero deficit do not request more evidence.
4. In the directed arm, choose among maximum-deficit requests; ties use one
   learner-local support RNG draw and stable anonymous candidate ordering.
5. In the shuffled arm, use the same one-draw budget to choose uniformly among
   all active positive-deficit requests, ignoring deficit magnitude.
6. If no request exists, retain the ordinary pre-drawn random action.

Choosing a requested action supplies ordinary world experience to every active
trial on that action. It does not grant reward, confirmation, rent, maturity or
score influence. The outcome can still reject the hypothesis.

Use a separate support RNG so the standing exploration/tie RNG stream remains
identical to the predecessor. Directed and shuffled arms make exactly one
support-RNG call per exploration event, even when no request exists. Record
every exploration event, request opportunity, selected requester, selected
action, beneficiaries, pre-probe support/deficit, fallback and cumulative
terminal return using anonymous IDs only.

The existing quantity named margin utility remains frozen as a lifecycle input.
Record, but do not use, absolute selected-action margin with and without each
candidate and whether the candidate changes the action-over-alternative sign.

## Measurements

Record phase-0 mastery/quiescence, clone parity, old/new success, cumulative
training return, evaluation checkpoints at 512/1024/2048/4096 for both old and
new pools, action/observation/exploration-event digests, ordinary exploration
count, support-RNG count, request opportunities, probe actions, fallbacks,
beneficiary counts, candidate activation/confirmation counts, reservoir support,
all proposal/review/rent/lifecycle events, occupancy, shared hashes, clipping,
trial-root isolation, graph/update parity and all resource ceilings.

Post hoc, identify the four target candidates per task and report their proposal
time, action selection count, activation/confirmation trajectory, maximum and
final review support, rent availability, lifecycle fate, probe count and
candidate-on/off effects. Separately report all non-target candidates so the
target analysis cannot hide global harm.

## Frozen gates

Development support requires every gate:

1. **Fixed reference.** Fixed-8 ranked has median old and new success each
   >=0.85 and at least 16/20 tasks master both.
2. **Negative replication.** Ordinary rent batch-4 fails the same joint mastery
   criterion: either a median endpoint is <0.85 or fewer than 16/20 master both.
3. **Evidence manipulation.** In the directed arm, at least 16/20 tasks have all
   four target candidates reach reservoir support >=32. Its per-task minimum
   target support exceeds shuffled in at least 14/20 tasks with median paired
   advantage >=12.
4. **Unsupported death.** At least 16/20 directed tasks mature all four target
   candidates, and no more than 4/80 directed target candidates die unsupported.
5. **Behavior.** Directed median old and new success are each >=0.85 and at
   least 16/20 tasks master both.
6. **Fixed noninferiority.** Median paired minimum old/new difference for
   directed versus fixed-8 is >=-0.05.
7. **Responsibility selectivity.** Directed exceeds shuffled on minimum old/new
   success in at least 14/20 tasks with median paired advantage >=0.10.
8. **Matched exploration.** Directed and shuffled have identical per-seed
   exploration-event counts and timing digests, identical support-RNG call
   counts, equal episode/reservoir budgets, and unchanged exploration rate.
9. **Safety and identity.** Shared hashes remain fixed; clone/manifests match;
   cumulative probe accounting balances; no lifecycle/allocation record contains
   semantic fields; trials never affect exploitative scores or deployed roots;
   no ceiling binds; and graph/update/resource invariants pass in all 80 arms.

## Predictions, kill criterion, budget and transfer

Prediction: ordinary batch-4 reproduces the missing fourth target structure.
Directed exploration raises its support above 32, matures all four targets in at
least 16 tasks, recovers old/new mastery near fixed-8, and beats shuffled
responsibility without increasing exploration count. Shuffled remains closer to
ordinary batch-4 because it does not consistently spend probes on the largest
local evidence deficit.

Any failed gate is a negative completion. Do not tune support target, exploration
rate, request eligibility, shuffling, rent, review cadence, topology capacity,
task distribution or gates after fresh rows are viewed. If target support rises
but adequately supported targets fail rent, individual versus cooperative rent
becomes the next separately authorized question. If targets mature but behavior
does not improve, action competition/plasticity becomes the next question. If
support does not rise, the request-allocation mechanism itself is falsified.

Compute/change budget: one generic exploration-request configuration and event
ledger, diagnostic action margins, one runner derived from the frozen
predecessor, focused tests, one retired-seed smoke, full repository validation,
then exactly 20 fresh seeds x four m=2 arms. Commit and push this contract before
mechanism code; commit and push validated implementation before fresh execution.

Frozen transfer: none. This package is generic-core development, not KRK
evidence. A supported mechanism requires a separately preregistered native KRK
R1 bridge before any R2 curriculum advance.
