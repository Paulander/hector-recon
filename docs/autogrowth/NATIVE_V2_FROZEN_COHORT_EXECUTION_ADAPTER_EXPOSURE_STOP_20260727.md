# V2 frozen-cohort execution adapter — exposure terminal stop

Date: 2026-07-27

Reviewed starting commit:
`8d69599ddacaf8d5ce134de5afa4ec75ac641da9`

## Verdict

**TERMINAL PROGRAM STOP BEFORE EXPOSURE ADMISSION AND BEFORE OUTCOMES.**

The one authorized frozen `run-exposure` command ended with a fail-fast
`ProspectiveV2IntegrityError`. Per the frozen execution rule, it was not
repaired, repeated or advanced. `run-science` was not started.

This is an execution-package source-binding stop. It is not an exposure
admission result, a causal result, or evidence for or against the scientific
hypothesis.

## Exact execution

Preflight began from a clean worktree with local and remote HEAD both equal to
the reviewed commit. All frozen adapter, test, source-manifest,
artifact-binding and readiness hashes matched the reviewed readiness closure,
and every exposure/science output path was absent.

The command executed exactly once:

```text
.venv/bin/python3 -m recon_lite_chess.autogrowth.native_v2_frozen_cohort_execution_adapter_freeze run-exposure
```

The deterministic environment used the frozen single-thread settings,
`PYTHONHASHSEED=0`, `TZ=UTC` and `C.UTF-8`.

The enclosing timer recorded:

- real: `2086.17` seconds;
- user: `2042.70` seconds;
- system: `11.22` seconds.

There was no restart or second exposure process.

## Failure

The terminal exception was:

```text
ProspectiveV2IntegrityError:
laboratory package omits or alters policy-critical source:
hector_m5_structure
```

The frozen call sequence reached
`V2LaboratoryRegistry.freeze(...)`, whose first operation validates the
supplied package-hash mapping. It stopped there, before the first
`probe_real_exposure(...)` call.

Read-only localization after the stop established:

- the supplied frozen map contains
  `runtime:src/recon_lite_hector/learning/m5_structure.py`;
- its value is the correct current file SHA-256
  `0d6d4a28d950f5c5caea5484bd2a7c44b7585d6b2e6f79be3631ca735426af05`;
- the registry validation contract instead performs lookup by the alias
  `hector_m5_structure`;
- that alias is absent from the supplied map, so validation fails before the
  registry or scan is created.

No source or manifest was changed to reconcile the two naming schemes.

## Preserved terminal artifact

Failure artifact:

- path:
  `reports/autogrowth/native_authority/v2_frozen_cohort_execution_adapter_freeze/exposure_failure.json`;
- SHA-256:
  `1e7713a5ef3b33e46d61fa7525e95f430126996b48477f96bbc5ee871886ab9f`;
- internal failure digest:
  `e76be5210359e1dc5a3aed02d18bd081a1f2e6555a64af519af3763d8936a110`.

The artifact records:

- command: `run-exposure`;
- exception type: `ProspectiveV2IntegrityError`;
- exact process ID: `1133585`;
- outcome accesses: `0`;
- outcome event IDs: empty.

The generic failure schema records `exposure_rows_read` as `null`; it does not
claim a completed exposure count. Source-order inspection shows the stop
preceded the first organism exposure probe.

## Stop boundary and unevaluated quantities

The following paths remain absent:

- admitted exposure artifact;
- execution manifest;
- science journal;
- science carrier;
- canonical result;
- science failure artifact.

Accordingly, there are no 32-seed outcome results, paired comparisons,
effective sample sizes, corrected probabilities, engagement counts, revocation
counts, or scientific gate verdicts to reconstruct. None is reported as zero;
they are **not evaluated**.

The frozen adapter source, tests, manifests, readiness artifact, 32 seeds,
organisms, candidates, graphs, ecology and thresholds remain byte-identical.
No R1, retired-65, historical-regression or other unopened data was accessed.

The package stops here for review. Any future naming-contract correction must
be a separately authorized package; it must not be treated as a continuation
or rerun of this terminal execution.
