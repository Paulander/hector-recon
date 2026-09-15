# HECTOR operations and crash recovery

## Inspect before doing anything

The user authorized handover preparation followed by the specific checkpoint
retry. Read START_HERE.md and the retry protocol. All paths below were correct
at preparation; if the environment was replaced, restore verified files first.
Do not confuse tool-session disappearance with a verified worker exit. Do not
reuse a PID without checking process identity and its start time. Never terminate
an unrelated process just because an old numeric PID matches.

The authoritative local checkout was:
`/workspace/scratch/42ed9c9c2a4a/hector-recursive`.
The current conversational scratch path was `/workspace/scratch/2d2531e3ef96`.
The work branch is `codex/context-owned-decisions` in private
`https://github.com/Paulander/hector-recon`.

First use `git status --short`, `git rev-parse HEAD HEAD^{tree}` and inspect the
latest entries of AGENTS.md. Check the retry's `retry-control/status.json`, its
unit intents/receipts and real block manifests. Use `rg --files` to find named
files. Do not run old experiment launchers just to learn where they stopped.

## Runtime

Python3.12.14 was used. Runtime dependencies include numpy2.3.5,
python-chess1.999/chess1.11.2, pytest8.4.2 and scipy; inspect the archive's
`environment.json` for exact installed versions. The checkout has a vendored
`libs/recon-lite/src`. Additional preinstalled dependencies were located at
`/workspace/scratch/63cf1a75c465/audit-deps`. That path is environment-specific;
restore equivalent packages if it no longer exists. Do not install/change learner
source to make a pickle load. Pickles are trusted project artifacts, not arbitrary
untrusted uploads.

Run project Python from the repository with:

```bash
env PYTHONPATH=/workspace/scratch/63cf1a75c465/audit-deps:src:libs/recon-lite/src:scripts/autogrowth \
  PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 python YOUR_SCRIPT.py
```

The thread environment matters for audit/LP runtime even though the learner is
CPU-bound and small. Use the declared one-CPU worker affinity and memory limits.
Do not inject scipy/LP outputs into actors. No GPU is required.

## Main source map

| File under `src/recon_lite_hector/learning/` | Responsibility |
| --- | --- |
| `context_decision.py` | Whole-scorer ownership, cloning, routes/compiler, live budgets |
| `owner_development.py` | Owner-local actual-residual nomination and local birth/pruning |
| `owner_compatibility.py` | Proven-impossible new-birth rejection; unknown remains eligible |
| `owner_birth_search.py` | Shared candidate pool and random/residual proposal selection |
| `fresh_owner.py` | Zero-training construction with separated exploration/birth RNGs |
| `owner_trial.py` | Original provisional parent/children law, permission gates, real-use outcomes |
| `owner_trial_learning.py` | Readiness clock, PROBATION reviews, bounded retained reconsideration |
| `trial_usefulness.py` | Existing internal permission primitive and UseOutcome records |
| `terminal_development.py`, `recursive_context.py` | Existing condition, expression, credit and recursive machinery |

Check actual imports for exact class inheritance. The revised class inherits the
original trial class, which inherits the fresh learner. Transactional development
uses deep copies, so do not keep stale references to a trial/weight across an
observe call. Checkpoint serialization refuses pending actual feedback.

Original study runner: `scripts/autogrowth/run_owner_trial_learning.py`.
It exports the three unchanged actor factories, exact schedule, training block
recorder, same-state checks and trial/readiness verifier. Do not edit this pinned
runner merely to get a recovery script working. The retry wrapper is separate:
`scripts/autogrowth/retry_owner_trial_learning.py` (implemented and verified by three recovery fixtures before play).

Useful tests: `tests/autogrowth/test_owner_trial_learning.py`,
`test_owner_split_trial.py`, `test_owner_fresh_start.py`, `test_context_decision.py`,
and `libs/recon-lite/tests/test_formal_choice.py`. The35 distinct focused checks
passed before the interrupted study; five new checks were repeated on final
source. New recovery tests must use fixture seeds98/99, never exploratory tuning
on21/22/23. Existing original runtime sources stay byte-identical.

## Recorder layout and immutable boundaries

Within `snapshots/autogrowth/owner-trial-learning-20260915/`:

- `source.json` maps86 runtime files to SHA-256; `source-snapshot/` contains their
  exact bytes. Match both to the pinned git tree.
- `intent.json` declares seeds/arms/planned counts. The original attempt has no
  worker `result.json`; preserve that absence.
- `seed-21/schedule.json` is the seeded1,920-row order.
- Each arm has `start.pkl.gz`, `initial-evaluation.json`, then `block-NNNNNN/`.
- A block's `intent.json` contains start/stop/order/parent checkpoint hash.
  `submitted/EVENT.json` is written after an actual action and before feedback;
  `credited/EVENT.json` adds actual updated weights after matching feedback.
  `training.jsonl` seals the same records, then `checkpoint.pkl.gz`,
  `evaluation.json`, and `complete.json` seal the block and every payload hash.
- `complete.json` is the authority for a completed block. A populated directory
  or progress line is insufficient. Validate paths, hashes, chain and exact credit.
- `interruption.json` is an explicitly labeled observer record, not a worker result.

Original seed21 current/trial have30 sealed blocks each. Revised has24; its last
checkpoint is `seed-21/learning-trial/block-001472/checkpoint.pkl.gz` at episode1536.
The unsealed tail is `seed-21/learning-trial/block-001536/`,39 submissions and39
credits for1536–1574. Do not overwrite or move it into an apparently complete run.

The retry directory is
`snapshots/autogrowth/owner-trial-learning-retry-20260915/`.
It reuses sealed evidence by copying and recording provenance, adds new units,
and has separate `retry-control/` metadata. Locks are operational protection;
learner decisions do not read them. Reused blocks remain byte-identical to their
source. Newly generated logs must stand on their own actual executions.

## Known durable raw archives

These are private user files, not public artifacts. Source/report files backed by
git are intentionally kept in the repository; raw run archives are separate.

| Archive | Identity / verification |
| --- | --- |
| `HECTOR_OWNER_TRIAL_LEARNING_PARTIAL_20260915.zip` | Library `libfile_1f179c97dea081918faac4def83827cb`; file `file_000000003d1c81f4a8d7cfdb3cc4c029`; version0;10,631,144 bytes |
| Its SHA-256 | `a4e0b2f9dbc66661f3b11239e7943891385c9ef1efea79f4dcbe37554b92c676` |
| Original combined-trial archive `HECTOR_OWNER_SPLIT_TRIAL_20260915.zip` | Library `libfile_9b72e7cb40108191ae9638f6b5575d60`; file `file_00000000ca988210ac53d3f0962d1e23`; version0;25,111,467 bytes |
| Its SHA-256 | `07a5e36d01dbd91d9e294925b9461c2fe03797fb011ecb732296299f0099d274` |

Both local ZIPs were in `/workspace/scratch/2d2531e3ef96/`. The partial archive has
11,269 members; every11,268 payload hash and ZIP CRC was verified. It includes
`run/`, test XML, worker log, environment/source pins and SHA256SUMS.json. It omits
git-backed source-snapshot files. Restore those from remote source commit
`5277b06cc527cadaef20d818d70fb2d66db5409b`, verifying every source.json hash, then
copy the verified files under the run's source-snapshot/ directory as required by
the original verifier. Do not pretend omission is a damaged experiment.

If an exact Library identity is known, use the Library skill's materialization
route for that identity; do not search unrelated files or invent IDs. Follow its
current tool schemas. If Library access is unavailable, the user can attach the
named archive. If the repository alone survives, its reports are sufficient to
understand the state, but not to restore missing mutable learner checkpoints.

## GitHub access and publication

The authenticated GitHub plugin has access to the user's private repository.
Native git transport previously lacked credentials. Use ordinary git if working
credentials now exist; otherwise exact-tree snapshot publication remains valid.
Never print credential-bearing remote URLs or tokens. Read only the parsed host
and path when verifying the local destination.

Available connector operations were `github_fetch`, `github_create_tree`,
`github_create_commit` and `github_update_ref`. Discover their current schemas.
Fetch the branch collection and repository metadata to verify the current branch,
private ownership and push permission. Encoded branch-slash resource URLs can fail;
the branches collection worked reliably. Do not overwrite another instance's work.

For snapshot publication: retain local commits; read changed UTF-8 files in
10,000-character chunks (larger tool outputs may truncate), assemble exact tree
entries with mode100644/typeblob/content against the remote parent tree. Check
created tree SHA equals `git rev-parse HEAD^{tree}`. Only then create the remote
commit with its real parent, and update the work branch with force=false. Verify
branch and main afterward. Record the local/remote IDs and common tree.

A previous automatic approval review initially rejected a private payload over
unverified destination/ownership. New read-only repository/permission and exact
origin/parent-tree evidence resolved it; do not blindly retry a rejection or
switch transports to bypass review. If blocked, finish concrete local work and
explain the actual review reason. Earlier user authorization to publish this
private branch persists. It does not authorize main changes or messages to others.

## Recovery commands and success criteria

After wrapper preflight and source publication, intended commands are:

```bash
python scripts/autogrowth/retry_owner_trial_learning.py init --output snapshots/autogrowth/owner-trial-learning-retry-20260915
python scripts/autogrowth/retry_owner_trial_learning.py status --output snapshots/autogrowth/owner-trial-learning-retry-20260915
python scripts/autogrowth/retry_owner_trial_learning.py step --output snapshots/autogrowth/owner-trial-learning-retry-20260915
python scripts/autogrowth/retry_owner_trial_learning.py verify --output snapshots/autogrowth/owner-trial-learning-retry-20260915
python scripts/autogrowth/retry_owner_trial_learning.py finalize --output snapshots/autogrowth/owner-trial-learning-retry-20260915
```

Use the full runtime environment prefix above and independent timeout. `step`
advances one bounded start/training unit; `verify` advances one arm's frozen
verification; `finalize` only closes an already verified experiment. Read actual
CLI help if implementation changed since this preparation document. A status
call must not execute environment actions. Do not call the original run() on the
recovery directory: it requires a new directory and would start from zero.

The final assembled cohort must still contain270 blocks/279 checkpoints and the
original17,280/4,464/4,464 logical action counts. New retry execution is11,904
training+3,072 scheduled+4,464 frozen=19,440. Preserve39 known repeated actions
separately in physical accounting; see protocol. Count every extra diagnostic
execution explicitly. Offline arithmetic/capacity inspection uses no environment.

After the wrapper completes:

- `summarize_owner_trial_learning.py RUN --output REPORT` computes acquisition,
  retained/lost/recovered rows, trial histories and storage counts.
- `audit_owner_trial_learning.py RUN --output AUDIT` checks all formal raw flags,
  assignment RNG draws, owner-local evidence and trial outcomes/readiness.
- `analyze_owner_split_trial.py RUN --output CAPACITY` checks all saved choices
  arithmetically and produces exact committed-graph capacity certificates.
- The original `run_owner_trial_learning.verify_run` executes another4,464 frozen
  actions if called: do not accidentally run it in addition to the allocated
  per-arm verification and omit the extra action count.

Use fresh output filenames; do not overwrite original records to make assertions
pass. Package ignored raw data with source pins, runtime dependencies, observer
and unit records. Validate hashes/ZIP CRC and save it durably. Update the final
handover and branch. If interrupted again, state exactly what survives, whether
any unit lacks an exit record, and which actions are uncheckpointed. Do not claim
retention across unmeasured intervals or finish a summary by inventing results.
