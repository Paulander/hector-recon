# V2 frozen-cohort package-alias compatibility reclosure — preregistration

Date: 2026-07-27

Starting commit: `b9e3b9392d91da4db495e79fc97f3820e31654af`

## Purpose and boundary

This is a data-free compatibility package. It preserves the terminal
`run-exposure` stop at `b9e3b939`, its failure artifact, the stopped execution
adapter, the protected V2.1 learner and laboratory registry, the frozen driver,
and every retained cohort artifact.

The package corrects only the naming boundary between:

- the frozen experiment's complete `runtime:<full path>` package map; and
- the laboratory registry's stable alias keys declared by
  `POLICY_CRITICAL_SOURCE_PATHS`.

It does not alter organisms, candidates, graph state, seeds, targets, ecology,
thresholds, exposure rules, outcomes, endpoints, statistics or stop labels.
It uses no temporary module-global replacement.

Only compatibility readiness is authorized here. The stopped exposure command,
the new exposure command and the new science command must not be run.

## Frozen diagnosis

Before implementation, programmatic diagnosis must establish:

- the registry declares exactly 13 aliases;
- none of those alias keys exists in the original experiment map;
- every `runtime:<declared path>` entry exists;
- for every alias, the runtime-path digest, current file SHA-256 and registry
  expected digest are identical.

Any mismatch stops the package without correction.

## Expanded-map law

The production expanded map is deterministic:

1. Begin with every original path-keyed entry and value.
2. Read the exact alias-to-path mapping from
   `POLICY_CRITICAL_SOURCE_PATHS`.
3. For each declared alias, copy the digest from its exact
   `runtime:<declared path>` entry.
4. Require that digest to equal the current file SHA-256 and the registry's
   expected alias digest.
5. Permit no missing original entry, changed original entry, missing alias,
   changed alias or additional manually authored key.

The one validated expanded map must be used for registry construction,
registry scan, cohort aggregation, execution-manifest identity and later
admission reconstruction.

## Bounded reconstruction seam

The frozen driver has no package-map injection point. This package contains one
bounded outer copy of only `_reconstruct_exposure_value`, with the expanded map
provided explicitly.

An AST comparison must prove that, after:

- removing the frozen internal package-map acquisition;
- removing the bounded explicit-map validation acquisition;
- removing the bounded function's extra `package_hashes` argument; and
- normalizing the function name,

the complete remaining function tree is identical. A difference anywhere else
stops the package.

The complete driver is not copied or versioned.

## Focused checks

Before source freeze, focused tests must prove:

- exact 13-alias diagnosis and three-way hash equality;
- complete original-map retention;
- removal or alteration of any one of the 13 aliases fails;
- a wrong declared path fails;
- an extra manually authored alias fails;
- the production expanded map creates a real registry;
- a small synthetic create/scan/cohort canary uses one identical map
  throughout and reads no outcomes;
- the old path-only map reproduces the preserved alias failure;
- the bounded reconstruction ASTs differ only in map acquisition;
- no module global is replaced;
- all package paths are separate from the stopped adapter;
- readiness contains no exposure probe, registry scan or cohort aggregation;
- the stopped failure and adapter package remain exact.

Run the new focused file and the adjacent V2 authority, frozen-driver and
stopped-adapter test files. Do not run the full repository suite unless a
change escapes the new package.

## Source and artifact freeze

Commit and push the compatibility source, tests and this preregistration before
creating manifests. Then commit and push:

- a source manifest binding the new files, exact diagnosis, expanded-map
  identity, AST comparison, environment and literal public commands; and
- an artifact-binding manifest binding the stopped package, old failure,
  cohort transports, all new output paths, frozen scientific constants and
  readiness-only stop boundary.

The real readiness process may begin only from those committed manifests.

## Real readiness gate

The one real readiness process must:

- restore and verify 32/32 candidate contracts;
- restore and verify 96/96 A/B/C organisms;
- reproduce accepted cohort digest
  `a144fe94f4479c819756dfc44b22a2594e2b9df09367d571d39ab54007560bb8`;
- construct exactly three registries, one per arm;
- register all 96 stored payloads using the exact frozen outcome-blind row
  definitions and one expanded map;
- record each complete registry manifest and package-map digest;
- preserve exact candidate/graph semantic state;
- preserve all watched module bindings and stopped-adapter artifacts;
- execute zero registry scans, zero cohort aggregations, zero organism exposure
  probes and zero outcome reads;
- stop before the first organism exposure probe.

Failure is preserved in the new readiness-failure path and ends the package
without repair or rerun.

## Delivery

If readiness passes, commit and push the readiness artifact, result note and
authoritative ledger update. Leave a clean worktree at a matching remote HEAD
and stop for independent review.

No exposure, science, R1, retired-65, historical regression or other unopened
data is authorized.
