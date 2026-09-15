# HECTOR handover: start here

Prepared 2026-09-15 at Oskar Paulander's explicit request, before retrying an
interrupted experiment. These documents are intended to let a new instance work
without the previous conversation. Read this file, RESEARCH_AND_ARCHITECTURE.md,
OPERATIONS_AND_RECOVERY.md and ../OWNER_TRIAL_LEARNING_RETRY.md, then check live
files/status rather than assuming the preparation-time state is current.

The separate recovery wrapper is now implemented and its three fixtures passed;
all86 original runtime files are unchanged. Handover publication preceded retry
implementation/play at remote48e184e33df7307b5abc9926636b93b8456a75d1.
For live progress inspect the retry-control files; the status below describes
the interrupted first attempt, not an assertion that recovery has not advanced.

See [live recovery checkpoint](LIVE_RECOVERY.md) for the retry archive identity
and latest published progress; raw status can be newer.

## Current instruction and authority

The latest user instruction is: **“First: prepare documents to hand over to a
new instance (as much information as possible) in case it crashes again. Then
retry the previous step.”** This explicitly authorizes the retry below and
supersedes the older no-automatic-retry restriction for this specific recovery.
Do not ask again whether to do this already-authorized work. It does not authorize
changing the scientific hypothesis, retuning thresholds, merging main, opening
an unrelated study or silently deleting interrupted evidence.

The user wants a self-contained, locally learning ReCoN/Hector. No environment
labels, external oracles, macro/network coach, fitted weights or analyst-selected
repairs may enter its decisions or growth. Favor direct explanation, actual
measurements and reproducible evidence. Point out errors and uncertainties.
Do not tell the user that full task accuracy proves general convergence or that
one accepted trial is permanent knowledge. Do not send emails/messages to others.

## Repository and source identity

- Private GitHub repository: `Paulander/hector-recon`.
- Active work branch: `codex/context-owned-decisions`.
- Main is intentionally unchanged at `2aa1ce47a6a93e2571aaa0b02101e9543fe94955`.
- Local checkout at preparation: `/workspace/scratch/42ed9c9c2a4a/hector-recursive`.
- Conversation scratch directory: `/workspace/scratch/2d2531e3ef96`.
- Last published status: remote `af7ed03fa76990e7bf67593f912dcd2e82aa1a06`,
  local `101027614baa6b62013522317a19273d6fee1a9f`, exact common tree
  `ac8c520158ccfb1c8717d21d5287ddc113895304`.
- Scientific source pin: remote `5277b06cc527cadaef20d818d70fb2d66db5409b`,
  local `51140753e256e8cbd9d50651cc3413aa14355810`, exact common tree
  `5f1cfbbcf1a5e865a4c81d2adf9e4661817710f7`.
- Remote/local commit IDs differ because native git transport had no credentials;
  exact source trees were published through the authenticated GitHub connector.
  Local history was retained. Tree equality, not commit-ID equality, is required.
- More recent handover/retry commits may now exist. Check the branch and its docs.

## State before the newly authorized retry

The three-arm experiment compares `current`, `trial`, and `learning-trial`,
fresh seeds 21/22/23, 1,920 training actions each. All are Boolean learners, not
chess players. The complete intended experiment is 17,280 training actions,
4,464 scheduled evaluation actions, 4,464 frozen reproduction actions,
270 training blocks and 279 checkpoints.

The first execution session disappeared without a worker result or exit record.
No worker was visible afterward. Cause unknown; no evidence identifies an
assertion failure, memory limit, timeout or frontend-only problem. The final
worker progress line records 368.87 elapsed seconds, not total runtime.

| Surviving seed-21 learner | At action 1,536 | Last checkpoint | Last score |
| --- | ---: | ---: | ---: |
| Current | 15/16 | 1,920 | 16/16 |
| Original trial | 11/16 | 1,920 | 11/16 |
| Learning-trial | 13/16 | 1,536 | 13/16 |

The revised learner additionally has 39 actual submitted/credited records for
events 1,536–1,574 with no checkpoint or evaluation. A further unrecorded
in-flight execution cannot be excluded. Seeds 22/23 never started. Totals:
5,415 recorded training, 1,392 scheduled evaluation actions, 84 sealed blocks,
87 checkpoints. Zero frozen reproduction actions. All saved evaluation choices
were checked arithmetically without new environment actions.

The two trial learners had identical first 320 actual records. Their first root
x split was born at 64. The old rule rejected it at 320 (gain -0.3124). The new
rule retained it, reached child readiness at 339, and accepted at 595 after
256 prospective requests (gain +0.8265). This supports allowing learning time;
it is not a completed final-performance comparison. At checkpoint 1,536 two
deeper trials remain PROBATION, with 147/114 prospective requests; neither has
reached its first review. The second-review rule has been exercised in a
mechanical fixture, not yet in this partial study.

The user-authorized retry will preserve all these original files and recover
from sealed checkpoints, with explicit accounting for repeated real actions.
It must keep all 86 original runtime source hashes unchanged. Retry changes are
recording/orchestration only. See the separate retry protocol for exact counts.

## Read these next

1. [Research and architecture](RESEARCH_AND_ARCHITECTURE.md): user goals,
   mechanism boundaries, exact meaning of owner/TRIAL/MATURE, history of results,
   unresolved hypotheses and interpretation traps.
2. [Operations and recovery](OPERATIONS_AND_RECOVERY.md): commands, dependencies,
   archive identities, source restoration, GitHub publication, recorder layout,
   crash checks and final audits.
3. [Retry protocol](../OWNER_TRIAL_LEARNING_RETRY.md): newly authorized recovery,
   immutable source/evidence boundaries, action accounting and execution plan.
4. [Original lifecycle protocol](../OWNER_TRIAL_LEARNING.md) and
   [interruption report](../OWNER_TRIAL_LEARNING_STATUS.md).
5. Root `AGENTS.md`, especially its latest entries; older entries are historical
   and often contain restrictions superseded by later explicit user instructions.

## Immediate continuation checklist

- Read `retry-control/status.json` and immutable unit intents/results in the retry
  directory if it exists. Never assume an old tool session still exists or that
  a process ID alone identifies the original worker.
- Inspect real processes and completed block manifests. Do not launch a competing
  worker; the retry command uses an exclusive process lock.
- If documents/source are prepared but retry initialization has not happened,
  finish the listed preflight and source publication first, then initialize once.
- If a retry unit is sealed, reuse it. A block without `complete.json` is unsealed,
  even if every action record is present. Preserve it and account for any repeated
  actual executions; never replay its feedback into a changed actor or fabricate
  a checkpoint/result.
- Continue only the declared remaining logical schedule. No performance-driven
  extra play. Retain the original attempt and its 39-record tail permanently.
- At completion, run the independent no-play audit, exact capacity/choice audit,
  retention summary, verify action accounting, archive raw evidence and publish
  the private branch. Update this handover with the resulting state.

A clean restart of the whole cohort is unnecessary when valid checkpoints
survive. Conversely, copying logs is not proof that the new actor reached their
post-action state. Recovery must actually restore a checkpoint and either use
its next action or perform explicitly counted, identical-policy real reexecution.
