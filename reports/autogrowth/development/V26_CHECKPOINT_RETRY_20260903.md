# V26 checkpoint-recovery retry — live development record

Frozen source: `48dd21a68f283a9c5da87c99f8a9b943af1aa2aa`.
Code-only clean checkout:
`/Users/banquo/Documents/ChatGPT/Hector-Recon/v26-checkpoint-gate-48dd21a6`.
Branch: `codex/v26-pre-evaluation-checkpoint`.
Protocol: `docs/autogrowth/V26_CONTINUOUS_EVIDENCE_GATE.md` in that checkout.

## Conditions

- Seed2026090110, same development comparison as the interrupted10dc4c54 pair.
  Both arms include the new durability fix; continuous-hypothesis evidence is
  the only behavioral difference between them. Config comparison verified this.
- Repair first, then baseline, sequentially. Follow-through: R0 96×48; R1 at
  most32×8; validation4/final-regression4. Scores are not learner-visible.
- Per arm: 7,200-s and4,096-MiB complete-epoch ceilings, not hard deadlines.
  One process per arm; Python3.12.13, NumPy2.2.6, python-chess1.999, hash seed0,
  numerical-library threads1. No parameter/curriculum/selection changes.
- Preflight: 248-test eight-module suite plus one additional off-cadence test
  passed; exact training/evaluation-call AST comparison passed. New checkpoints
  survive interruption during any of the three checkpoint evaluation steps,
  with resumed graph/credit/evidence parity. This is not chess-generalization
  evidence. More than60 GiB disk free at preparation.
- Stop only the verified retry worker at the1.5-GiB disk floor, on integrity or
  memory failure, or if a scheduled check finds elapsed time over3h. No automatic
  extension/resumption/retry or additional seed. Starting the baseline once is
  authorized after normal repair completion or an intended R1 wall-budget stop,
  not after R0-incomplete, integrity, memory/disk or unexplained failure.

Outputs under
`/Users/banquo/Documents/ChatGPT/Hector-Recon/source/reports/autogrowth/development/`:

- `native_continuous_v26_seed_2026090110_48dd21a6_retry_repair`
- `native_continuous_v26_seed_2026090110_48dd21a6_retry_baseline`

The old interrupted outputs and all five retained gzip networks remain intact.
No protected fresh outcomes, frozen experiment or old-PC worker are in scope.

## Execution record

- Repair launched **2026-09-03 14:01:02 UTC** (16:01 Stockholm), Python
  worker **46997**, caffeinate helper47004, tool session **61172**. Process
  command/output identity verified after launch. Baseline not started.
- Clean frozen-checkout smoke check: off-cadence resume plus atomic write
  preservation, **2 passed in21.70s** (a repeat subset, not additional test cases).
- Last pre-launch available disk: **64,806,568 KiB (~61.8 GiB)**. No new
  learning result yet. App follow-up handles the bounded sequential comparison.
- Follow-up `v26-checkpoint-retry-follow-up` is active every five minutes in
  this task. At the post-launch check the worker was alive at97.6% CPU, with no
  logged exception. This establishes liveness, not completed learning progress.

## Exact command for the authorized baseline (once repair is finished)

**Already launched once at 16:06:41 UTC on 2026-09-03; do not run again.**

Verify no retry trainer is active, the source checkout is still clean at the
commit above, and the baseline output directory does not already exist. Do not
run this command a second time or reuse a completed/failed output directory.

```sh
cd /Users/banquo/Documents/ChatGPT/Hector-Recon/v26-checkpoint-gate-48dd21a6
mkdir /Users/banquo/Documents/ChatGPT/Hector-Recon/source/reports/autogrowth/development/native_continuous_v26_seed_2026090110_48dd21a6_retry_baseline
env PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONHASHSEED=0 \
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  PYTHONPATH=.:src:libs/recon-lite/src \
  /usr/bin/caffeinate -i /private/tmp/hector-recon-v25-py31213/bin/python -u \
  -m recon_lite_chess.autogrowth.native_adaptive_boundary_development \
  --profile follow-through --seed 2026090110 \
  --no-continuous-hypothesis-evidence \
  --max-wall-seconds 7200 --max-peak-rss-mib 4096 \
  --output-dir /Users/banquo/Documents/ChatGPT/Hector-Recon/source/reports/autogrowth/development/native_continuous_v26_seed_2026090110_48dd21a6_retry_baseline \
  > /Users/banquo/Documents/ChatGPT/Hector-Recon/source/reports/autogrowth/development/native_continuous_v26_seed_2026090110_48dd21a6_retry_baseline/run.log 2>&1
```

Repair uses the same command with the positive evidence flag and repair output
directory. Keep this record updated with each process identity, start/stop time,
exit status and observed results. Never substitute missing counters with zeros.

## Repair result and baseline handover — 2026-09-03

- Repair stopped at exact R1 epoch **18**, with an intended wall-budget stop:
  `CEILING_REACHED_AT_EXACT_EPOCH_SNAPSHOT`, reason
  `wall_seconds=7206.617>=7200.000`. Runner duration **7225.500555 s**;
  attempt file written **16:01:29 UTC**. No trainer remained at the handover
  check. Numeric process exit status was not captured after the original
  tool session detached; the actual attempt/log establish the stop reason.
- Latest snapshot loaded successfully: **65,702,098 bytes**, SHA256
  `f7c900558e128cbf3c4ee131c1b85503b8f0123ea722190eaed41bd997a65ee9`.
  This is transport integrity, not semantic organism identity. Snapshot epoch18,
  no pending evaluation; epoch18 explicitly skipped held-out evaluation at the
  wall ceiling. R1 snapshot duration **5698.350394 s** is a different scope from
  the overall runner duration above. No resume or extension was launched.
- Saved R1 counters: **144 episodes**, **139 unique REAL observations**, seven
  handoffs, **8 AVAILABLE /132 UNKNOWN /4 REFUTED** reply envelopes, successor
  value sum **4.771100415597943**, two structural transitions, seven surprise
  successes, five post-contact exact-Q choices and two positive-credit revisits.
  Handoff provider provenance and certification/structure details await the
  paired checkpoint audit; do not label these seven as continuous/new-shell
  handoffs from the aggregate count alone.
- R0 completed epoch96 with48 providers and initial frozen-policy validation
  **15/16**. Last evaluated R1 checkpoint epoch16 retained **15/16** frozen-core
  accuracy; V2 shell coverage was **12/16**, not frozen-core forgetting.
  Checkpoint M2 validation did not pass. Its zero rate uses short-circuit
  evaluation; no complete four-position/final regression result was produced.
  Missing epoch18/final evaluation is not zero performance.
- Baseline launched **16:06:41 UTC /18:06:41 Stockholm**, Python worker **51502**,
  caffeinate helper **51510**, tool session **53102**. Command/output/start identity
  verified. Same clean frozen48dd21a6 checkout, seed2026090110, follow-through,
  evidence flag off, numerical threads1,7200s/4096MiB. New independent baseline
  directory was absent before launch. No duplicate or other trainer was running.
- Baseline is the last authorized attempt. Safety check cutoff is elapsed
  **over3h**, i.e. after **19:06:41 UTC**; runner wall ceiling remains7200s at
  complete epochs. No further arm, restart, resume, extension or seed is allowed.
