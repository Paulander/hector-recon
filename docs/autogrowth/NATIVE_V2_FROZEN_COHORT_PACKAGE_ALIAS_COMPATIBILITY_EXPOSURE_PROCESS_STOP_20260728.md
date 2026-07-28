# Native V2 Frozen-Cohort Package-Alias Compatibility Exposure Process Stop

Date: 2026-07-28

## Verdict

TERMINAL EXTERNAL PROCESS STOP — exposure admission not evaluated.

The one authorized exposure invocation ended with process exit code 143 and no
stdout or stderr. The program did not catch the termination and wrote no
failure artifact, exposure artifact, or execution manifest.

Per the binding Stage 1 rule, the exposure command was not repaired, resumed,
or repeated. `run-science` was not started.

## Exact starting state

- Branch: `codex/native-krk-resume-composition`
- Local and remote HEAD:
  `07ba8ab4fe2f215f17be306300241abb9a4aa954`
- Worktree: clean
- Frozen cohort digest:
  `a144fe94f4479c819756dfc44b22a2594e2b9df09367d571d39ab54007560bb8`
- Frozen expanded-map digest:
  `2334cce42845479e8d1a642876d088b96ad18c5d1b55c9b31e7cfaa0549f048d`
- Source manifest SHA-256:
  `d1736b3ca31f975c295bf5524879de28bd591d6c0ef2fcc6c9f7a3ac644dbe8b`
- Artifact binding SHA-256:
  `334880f320cecc55c180792d70ff2382e74ca1779d2fa6a3c09ea9c4cf571af5`
- Readiness artifact SHA-256:
  `1eb1fb814593341f96766e9fad6696b595803055b5a8b85b2c7a20be97037bed`

No package process was active before launch.

## Invocation

The following literal command was invoked once:

```text
.venv/bin/python3 -m recon_lite_chess.autogrowth.native_v2_frozen_cohort_package_alias_compatibility_reclosure run-exposure
```

The managed process ran for approximately 17 minutes before returning:

```text
exit code: 143
stdout: empty
stderr: empty
```

Exit 143 indicates termination by signal 15 at the process-control boundary.
There is no caught program exception or frozen program failure record from
which an exposure result can be reconstructed.

## Durable post-stop state

No package child process survives. The worktree remained clean immediately
after the stop. The new package directory still contained exactly the same
three files as before invocation:

1. `source_manifest.json`
2. `artifact_binding_manifest.json`
3. `readiness.json`

Their hashes remained exact. In particular, no
`preoutcome_exposure.json`, `exposure_failure.json`,
`execution_manifest.json`, science journal, science carrier,
`canonical_result.json.gz`, or science failure artifact exists.

Tracked cohort and graph files were not persistently changed. The interrupted
process did not produce a durable in-run mutation audit, so the exposure-run
mutation count itself is not evaluated.

## Quantities not evaluated

Because there is no admitted exposure artifact, the following are all **not
evaluated**, not zero:

- exposure qualification;
- qualifying-seed count and the 24/32 admission gate;
- complete 32/96 A/B/C exposure parity;
- row-level target exposure;
- planted-target support;
- C contradiction dose;
- graph clearing;
- exposure-run mutation count;
- exposure-run outcome-read count;
- engagement and revocation;
- all per-arm endpoints;
- all 32 `D_safe` and `D_signal` values;
- wins, losses, ties, and effective sample sizes;
- exact and Holm-corrected probabilities;
- favorable-seed count;
- pooled totals;
- every scientific pass/fail gate;
- exposure, execution, journal, and canonical-result digests.

The outcome stage was never invoked, so no science journal exists from which to
derive an outcome count. The outcome suffix remains unconsumed by
`run-science`, but this exposure attempt is terminal and must not be reused or
repeated.

This stop is not evidence for or against the scientific hypothesis and is not
KRK R1 evidence.
