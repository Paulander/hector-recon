# Native V2 Frozen-Cohort Package-Alias Compatibility Reclosure Result

Date: 2026-07-27

## Verdict

PASS — data-free readiness only.

The outer compatibility package repairs the package-map naming mismatch without
changing the protected V2.1 learner, laboratory registry, frozen driver,
stopped execution adapter, cohort organisms, candidates, graph state, seeds,
targets, ecology, or thresholds.

The retained cohort is ready for independent review. No real exposure probe,
registry scan, cohort exposure adjudication, environment outcome read, or
science execution occurred.

## Frozen commits

- Starting clean HEAD:
  `b9e3b9392d91da4db495e79fc97f3820e31654af`
- Source, tests, and preregistration:
  `3a8dc372a1503c828538704c5d8b3f4a46e46a05`
- Source and artifact manifests:
  `7d2b64ac8aa5f6ad6302959fe530388d369b8e79`

Both freeze commits were pushed before the real readiness command.

## Diagnosis

The original frozen map contains 296 path-keyed entries and none of the 13
stable aliases declared by `POLICY_CRITICAL_SOURCE_PATHS`.

For every declared alias, the following three values were equal:

1. the original map's `runtime:<declared path>` digest;
2. the SHA-256 of the current file bytes;
3. the digest expected by the laboratory registry under the alias.

The expanded map retains all 296 original entries and mechanically adds exactly
the 13 declared aliases, for 309 entries total.

- Original map digest:
  `837da27658bb691490fc771f5eec445c28870888ff6bb7b3f8140f527bb38da4`
- Expanded map digest:
  `2334cce42845479e8d1a642876d088b96ad18c5d1b55c9b31e7cfaa0549f048d`
- Expanded-map manifest digest:
  `b150ac2ad6368343411285d8afdea2593d54f6b0babe61f0419e6c8bd4929d71`

The bounded reconstruction function differs from the frozen reconstruction
only in acquiring and validating the explicit expanded map. Its normalized AST
comparison passed, with comparison digest
`5e02d0fce1e812ff4264fe79abac29686cc91d24505886f62244fcd47dc6ef3f`.
No module global was replaced.

## Validation

- New focused/adversarial package tests:
  39 passed in 342.65 seconds.
- Adjacent execution-adapter and review-repair tests:
  48 passed, 1 skipped in 45.65 seconds.
- Adjacent native V2 authority tests:
  29 passed in 15,134.31 seconds.

The full repository suite was not repeated because all changes are confined to
the new outer compatibility package, its tests, preregistration, manifests,
readiness artifact, and documentation. Protected runtime sources remain
byte-identical.

## Frozen manifests

- Source manifest SHA-256:
  `d1736b3ca31f975c295bf5524879de28bd591d6c0ef2fcc6c9f7a3ac644dbe8b`
- Source manifest canonical digest:
  `f6251ca38731c3b22b277f3f47c60b546630c18ec69787fcc0bfec6f96381fd2`
- Artifact binding SHA-256:
  `334880f320cecc55c180792d70ff2382e74ca1779d2fa6a3c09ea9c4cf571af5`
- Artifact binding canonical digest:
  `136c63f0ab35ecfc2422a5a4bdf6f758ab9091828e09f4f49e10b0550d2e4be7`

## One real-cohort readiness execution

The one authorized `verify-readiness` command completed successfully.

- Artifact-reported runtime: 5,061.60 seconds.
- Process wall time: 4,972.17 seconds.
- Candidate contracts: 32/32 canonically verified.
- Stored A/B/C organisms: 96/96 verified.
- Cohort digest:
  `a144fe94f4479c819756dfc44b22a2594e2b9df09367d571d39ab54007560bb8`
- Registries constructed: 3.
- Registry payloads: 96.
- Stored row definitions bound into the registries: 1,536.
- Registry scans: 0.
- Cohort exposure adjudications: 0.
- Organism exposure probes: 0.
- Outcome reads: 0.
- Candidate or graph mutations: 0.
- Module-global replacements: 0.

The registry-closure digest is
`a55c0c698681177b0bb2f78811bb01d6aa993781174f80d83f446b381387300e`.
All three registries use expanded package-map digest
`2334cce42845479e8d1a642876d088b96ad18c5d1b55c9b31e7cfaa0549f048d`.

The semantic state digest was byte-identical before and after:
`130842160194a59ee06df577165209374ebcf663b7db19aa806958219afb9737`.
The 732,563,064-byte canonical runtime view was also identical before and after,
with SHA-256
`0ae7e3696619d76056a33099a45c3c4b3f157e3f1847dac69e3b790c03e24ddb`.

The stopped adapter's source manifest, artifact binding, readiness artifact,
and preserved exposure failure remained unchanged as a set, with identity
digest
`f435a867ef8a86d3ee6effbcef54cbdabde0f49521ec2abc817b26c52639c936`.
The preserved failure artifact SHA-256 remains
`1e7713a5ef3b33e46d61fa7525e95f430126996b48477f96bbc5ee871886ab9f`.

## Readiness artifact

- Path:
  `reports/autogrowth/native_authority/v2_frozen_cohort_package_alias_compatibility_reclosure/readiness.json`
- SHA-256:
  `1eb1fb814593341f96766e9fad6696b595803055b5a8b85b2c7a20be97037bed`
- Canonical readiness digest:
  `e7e37b53b2a251e65a7e4214b74eae11f98c6b8ea7a6f6001d7dfa9a7598d02a`

No readiness failure, exposure artifact, exposure failure, execution manifest,
science journal, science carrier, canonical result, or science failure exists
in the new package.

## Frozen later commands

These commands are frozen for a later independent decision and were not run:

```text
.venv/bin/python3 -m recon_lite_chess.autogrowth.native_v2_frozen_cohort_package_alias_compatibility_reclosure run-exposure
.venv/bin/python3 -m recon_lite_chess.autogrowth.native_v2_frozen_cohort_package_alias_compatibility_reclosure run-science
```

This result closes only the alias-to-path compatibility and real-cohort
readiness boundary. It is not exposure, causal, scientific, or KRK R1
evidence.
