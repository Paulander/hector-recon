# M1 learning-rate comparison

Protocol fixed before new play, 2026-09-09. Explicitly authorized by the user to
run in the background and report completion. The preceding retention diagnosis
and `M1_CORNER_MECHANISM.md` establish actual shared-weight interference, available
ranking capacity, and a distinction between reward prediction and per-board
ordering. A smaller step is a hypothesis, not an established retention fix.

## Fixed treatment and schedule

- Source: the exact final **4,096**-decision long-play checkpoints from
  `a21473e7b818271fbd5424204ea83d49c2d550f8`, seeds **4, 7, 9**. Initial development
  scores **128, 126, 111 / 128**. The same sources were used in exploration.
- Restore and clone each into learning rates **.3 and .1**. Only that field changes.
  Keep exploration **.25**, cap **64**, normal births/pruning, scalar rewards,
  terminal features and all learner mechanisms. There is no added nominee.
- Continue each from **4,096 to 6,144**: **2,048** additional rewarded moves,
  original shuffled 256-row training schedule, eight appearances per row.
  Verify the complete inherited schedule and actor before play.
- Frozen development evaluation on all 128 rows at **4,608, 5,120, 5,632, 6,144**.
  Frozen training-set evaluation on all 256 rows at the final endpoint.
  Save each **128**-decision block and reload evaluated checkpoints. Evaluation
  never changes training decisions, source selection, settings or endpoint.
- **12,288 training + 3,072 development evaluation + 1,536 training evaluation =
  16,896 actual moves.** No final-test access or alternative-action grading in
  this training runner. Preserve action-bound post-feedback JSONL logs.
- The saved RecoveryTrial actors already separate exploration and birth RNGs.
  Both arms keep .25 exploration and the same positions, so exploration draws
  remain matched. Different weights may change pruning/birth and the separate
  birth stream; future topology need not match. Verify exploration RNG digests
  at corresponding milestones. Never use changed-policy fixed-log replay.

## Resource and background limits

Three worker processes, restricted to three available logical CPUs, single-thread
numerical libraries. Each arm has **3,000 seconds** with an interrupting timer and
ordinary transaction-boundary deadline checks. One attempt only; no automatic
retry, resume or extension. The supervisor kills the experiment process group on
an arm failure, **110-minute** total wall deadline, **6 GiB** aggregate resident
memory threshold, or its STOP file. Every process also inherits a **2.5 GiB**
address-space ceiling. Limits apply to this job, not unrelated user processes.

The supervisor writes PID, heartbeat, peak memory and explicit complete/incomplete
status in `reports/autogrowth/runs/m1-learning-rate-job-20260909/status.json`.
Completed blocks and partial logs remain after interruption. A termination inside
an action can leave an unfinished transaction; never silently replay it.
The completion notification checks this status and actual reports. It must report
an interruption honestly; a stopped or unavailable process is not a completed run.

## Interpretation and checks

Primary: every final seed's .1-minus-.3 development difference, with paired gained
and lost rows. Also report all milestones, acquisition of initially failed rows,
loss of initially solved rows, final training performance, actual training wins,
and resource costs. Row gains must not conceal regressions. Do not choose an
earlier best-scoring checkpoint as the final result.

The .3 control must reproduce the earlier .25 exploration action log and shared
milestone results. The extra frozen evaluation cannot alter its learning history.
Final saved actors, source identity, config, counts and logs must verify.
If a lower rate preserves an inferior starting policy or delays acquisition,
that is not improved learning. Any favorable result is evidence on three selected
histories, not a default change or fresh-seed confirmation. Feature/rule/growth
changes are separate interventions.

Run the required branch suite plus `tests/autogrowth/test_m1_learning_rate.py`
before launch. New tests verify the sole rate change, source/schedule checks,
terminal-only play, exact ordinary-trajectory equivalence, frozen evaluation,
checkpoint reloads, serial/parallel equivalence, retained partial logs and a hard
deadline interrupting a stuck call. Existing learner and experimental controls
remain unchanged.

Launcher: `python scripts/autogrowth/background_m1_learning_rate.py` with the
existing Python 3.12/chess 1.11.2 environment and hash seed 0. The launch is
one-time: directories are created exclusively, so a second invocation fails.
Post-run accounting writes `reports/autogrowth/development/M1_LEARNING_RATE_20260909.json`
and a checkpoint ZIP. Keep private payloads outside git and preserve the archive.

Preflight: 16 frozen development moves from seed 9 took 14.25 seconds on one
CPU, with no training or state change. This calibration is separate from the
16,896 planned experimental moves. The arm/job limits above were increased
before play to accommodate the measured runtime while keeping three CPU cores.

## Interruption observed 2026-09-09

This attempt is **incomplete**. The supervisor and runner host identities were
absent and execution session 5304 no longer existed. There is no normal exit or
recorded failure cause. The last measured aggregate RSS was 218,714,112 bytes;
this does not establish peak usage after that heartbeat or explain termination.

Seed 4 at both rates and seed 7 at .3 each logged 512 new rewarded moves and
saved step 4,608. There are 1,536 logged training moves and 15 checkpoint payloads
in total. Their first development evaluations have pending markers and no
completed reports; the number of evaluation moves actually executed is unknown,
bounded by 384 across these three units. The other three arms never started.
The older progress markers stop at 4,480; the payload pointers establish 4,608.

No final or intermediate learning-rate result is available. The status file was
marked incomplete and the scheduled notification disabled after reporting the
interruption directly. No restart, resume, replay or replacement run was made.
The private interrupted archive preserves payloads, action logs, pending markers,
manifest and status evidence, with SHA-256 hashes. The fixed protocol above has
not been retrospectively changed. Background persistence across replies was
overstated; any future launch needs a verified durable execution arrangement.
