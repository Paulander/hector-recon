# Native terminal-trace historical regression result

Date: 2026-07-20
Branch: `codex/native-krk-resume-composition`
Pre-data freeze commit: `70b2706672a3dcd4ff9e3aeadff4b3393ed798cb`
Scope: single inference-only opening of the sealed historical regression split; not fresh evidence.

## Verdict

FAIL: `specialized_contexts_overgeneralize`.

The trace-native local-contrast organisms transferred more safe deployable
coverage than both controls and passed both paired superiority tests, but they
emitted 28 false-positive AVAILABLE decisions across the 512 negative
decisions. Only 11/32 were safe-narrow, below the frozen 24/32 gate. The
specialization mechanism therefore transferred causally, but its learned
contexts are not selective enough for deployment.

This is a scientific negative, not an instrument abort. Every authority,
serialization, trace-parity, session, and no-mutation invariant passed.

## Canonical artifact

- artifact: `reports/autogrowth/native_authority/native_terminal_trace_historical_regression.json.gz`
- compressed SHA-256: `eb60826db7269b1fb69cd2abe21d137bb1853503cd8177e69aeb36050a77ecf4`
- uncompressed SHA-256: `a5f5184175297aa16cff2c533a687ab71f04b35574c8c2b4bf0926b39855cc95`
- size: 5.3 MiB compressed; 112 MiB uncompressed
- runtime: 11,157.745 seconds (3h05m58s)
- organisms: all 96 frozen artifacts (32 ordinals x 3 arms)
- regression opening: exactly once
- fresh, retired-65, and R1 access: zero

## Frozen cohort result

| Arm | TP | FP | safe-narrow | strict | deployable TP |
|---|---:|---:|---:|---:|---:|
| local contrast | 184 | 28 | 11/32 | 0/32 | 58 |
| demotion only | 103 | 16 | 5/32 | 0/32 | 22 |
| counterexample blind | 141 | 21 | 7/32 | 0/32 | 36 |

Thirty of 32 local organisms had nonzero TP on both the viewed development and
historical regression splits. Local deployable TP exceeded demotion in 8 paired
ordinals versus 1 loss and 23 ties (one-sided p=0.01953125), and exceeded blind
in 6 versus 0 losses and 26 ties (p=0.015625). Both Holm-adjusted p-values were
0.03125. Eighty-one held-out TP advantages over demotion were supported by a
mature depth-one child.

The 28 local false positives were concentrated on five decoy rows: row 20 (5),
23 (1), 24 (16), 27 (4), and 31 (2). This is descriptive localization only; no
threshold, organism, row, or mechanism was selected or changed after viewing
regression.

## Gate adjudication

Passed:

- local deployable TP exceeds demotion-only;
- local deployable TP exceeds counterexample-blind;
- paired superiority over both controls after Holm correction;
- 30/32 have nonzero viewed-development and regression TP;
- a mature depth-one child supplies held-out advantage;
- all integrity, authority, exact trace/actuation parity, complete-session, and
  no-mutation gates.

Failed:

- zero local false positives: 28/512 negative decisions were false positives;
- local safe-narrow at least 24/32: observed 11/32.

## Validation

- pre-data synthetic-focused suite: 3 passed in 3.72 seconds
- post-closure full repository suite: 979 passed in 3,473.68 seconds (57m53s)

## Interpretation and stop

Graph-selected terminal traces and outcome-grounded one-level specialization
survive serialization and transfer to historical regression better than both
frozen controls. The same organisms nevertheless overgeneralize on unseen
historical decoys. This closes the package as a selectivity/generalization
failure, not as evidence against trace-native authority or against causal
specialization.

Regression is now viewed development data permanently. No tuning, retraining,
selected organism, ensemble, new mechanism, R1, retired-65 access, or fresh data
is authorized by this result. The package stops after documentation, full-suite
validation, commit, and push.
