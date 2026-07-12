# Generic-Core Self-Grown Coverage: Behavioral Success, Coverage Gate Miss

Date: 2026-07-12. Track: generic-core development. Verdict: formal package
negative because median coverage reached 5/8 rather than the frozen 6/8 gate.
Behavioral coexistence and ranked-versus-random selectivity are strongly
positive. No gate is relaxed post hoc.

## Execution and integrity

The contract and runner were committed at `e8331bb` and `7e5266c`. Focused
tests and a retired-seed smoke passed; the complete relevant suite passed 69/69
before fresh tasks. The once-only run completed on seeds 20261801--20261820.

All 20 tasks mastered phase 0. Clone parity, equal standard budgets,
byte-identical shared weights, graph parity, trial isolation and resource bounds
all passed. No pair was injected, no gain bound changed, and no semantic label
entered nomination.

## Results

| Arm | Median old | Median new | Both >=0.85 | Median coverage | Median proposals |
|---|---:|---:|---:|---:|---:|
| Four-live ranked | 1.000000 | 0.667969 | 2/20 | 3/8 | 54.5 |
| Eight-live ranked | 1.000000 | 1.000000 | 18/20 | 5/8 | 72.0 |
| Eight-live random | 0.813477 | 0.702148 | 1/20 | 2/8 | 69.5 |

Eight-ranked also had median old/new topology effects 0.3125/1.0 and zero median
old drop.

Paired selectivity:

- eight-ranked minimum(old,new) exceeded four-ranked on 19/20 tasks;
- eight-ranked exceeded capacity-matched random on 20/20;
- median paired advantage over random: 0.234375.

The random arm had nearly the same realized proposal count, so extra candidate
quantity alone does not explain the result.

## Frozen gate verdict

Eight-ranked passed every behavioral, causal, selectivity and integrity gate.
It failed only:

- required median contextual coverage: at least 6/8;
- observed median: 5/8.

Coverage counts were:

- four-ranked: range 2--6, median 3;
- eight-ranked: range 4--6, median 5;
- eight-random: range 1--5, median 2.

Therefore `development_support` remains false in the artifact.

## Interpretation

The result demonstrates that expanding local ecology lets ordinary anonymous
residual ranking self-grow a much more useful topology than matched-random
nomination. It achieves coexistence on 18/20 tasks without exhaustive injection
or higher gain.

The preregistered 6/8 coverage threshold was stronger than behavioral
sufficiency required on these tasks: a selective 5/8 subset often sufficed
because the mastered shared baseline already carried part of the policy.
That is a post-result interpretation, not permission to rewrite the gate.

Supported as development evidence:

- capacity four was a real structural bottleneck;
- residual nomination contains strong signal beyond capacity;
- self-grown contextual topology can preserve old mastery and acquire the new
  regime under frozen shared weights;
- full Cartesian coverage is not necessary for most tasks.

Not yet claimed:

- formal package success or independent confirmation;
- an autonomous rule for choosing capacity eight;
- removal of the laboratory phase-boundary freeze;
- native predecessor-child transfer or KRK.

## Artifact

`reports/autogrowth/generic_core/self_grown_contextual_coverage_20260712.json`

- artifact SHA-256:
  `5d8811f14f8797712a232e06087e5336d57e91fd59a1c6be28cff6253264a9d3`;
- source commit:
  `7e5266c5b3660dea95abbf2a24b2a47c3a5b2111`;
- task-row SHA-256:
  `4d90c9ecfccf15da0c991938091bd49cae7ae6a17a22cece9cad3410d421b7c2`;
- runner hash matches frozen source.

## Required decision

This package is closed. Do not lower the coverage gate on these rows.

The next decision should be externally reviewed: either preregister fresh
confirmation with coexistence/selectivity as primary gates and coverage as a
measured mediator, or first replace the externally chosen eight-live capacity
with a learner-local capacity-pressure rule. Direct KRK integration remains
premature because shared freezing is still laboratory scheduled and this generic
task exposes an explicit regime atom.
