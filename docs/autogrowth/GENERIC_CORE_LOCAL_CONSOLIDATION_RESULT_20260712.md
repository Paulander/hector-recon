# Generic-Core Local Consolidation: Failed Coexistence Package

Date: 2026-07-12. Track: generic-core development. Verdict: consolidation is
causal but hard freeze falsified. No repair or rerun authorized.

## Frozen execution

The contract was committed at `0ee12c9`. Maturity-triggered consolidation,
legacy-default tests, audit counters, and runner were committed at `f121f51`;
the full generic suite passed 50/50 before 20 fresh tasks ran once.

## Raw gates

| Measurement | Frozen requirement | Observed |
|---|---:|---:|
| Consolidated median regime-0 joint | at least 0.85 | 0.803711 |
| Consolidated median regime-1 joint | at least 0.85 | 0.645508 |
| Consolidated median key, both regimes | at least 0.90 | 0.923828 / 0.926758 |
| Consolidated old joint exceeds control | at least 16/20 | 20/20 |
| New-regime median loss versus control | at most 0.05 | 0.354492 |
| Mature regime-1 pair | at least 16/20 | 20/20 |
| Median composite-ablation effect | at least 0.15 | 0.390625 |
| Shared updates after maturity | zero | zero |
| Candidate updates after maturity | nonzero | nonzero on 20/20 |
| Resource, parity, leakage, budget gates | pass | pass |

The coexistence hypothesis failed because both regime thresholds and the
new-regime non-inferiority gate failed.

## Stability–plasticity result

Compared with the renewable control on identical fresh tasks:

- control regime 0 joint median/mean: 0.0 / 0.0335;
- consolidated regime 0 joint median/mean: 0.8037 / 0.7188;
- control regime 1 joint median/mean: 1.0 / 0.9963;
- consolidated regime 1 joint median/mean: 0.6455 / 0.6881.

Hard consolidation therefore caused a large, universal old-regime improvement
and a large new-regime loss. It is not neutral machinery: it directly controls
the stability–plasticity balance.

Key competence stayed relatively strong in both regimes, while door behavior
split the difference rather than preserving both mappings. Disabling mature
topology caused a median 0.3906 joint loss, so context-specific candidates
carried more behavioral responsibility than in predecessor packages.

## Timing diagnosis

- all 20 tasks had candidate updates after consolidation;
- all matured channels had exactly zero shared updates afterward;
- first maturity occurred at median observation 484, range 173–3,248;
- phase 0 lasts 4,096 observations per action population;
- most channels therefore froze shared weights long before phase-0
  equilibration was complete.

The learner-local trigger was valid, but scale 0.0 was too strong and often too
early. The frozen baseline was stable but underfit; later context-specific
candidates could not fully compensate. This directly supports the user's
earlier proposal that hierarchy/age/activation-sensitive learning speeds are
likely a tunable or adaptive mechanism rather than a binary freeze.

## Artifact

`reports/autogrowth/generic_core/local_consolidation_key_door_20260712.json`

- artifact SHA-256:
  `ca356c3734dd4d46db99f1bb8605e3c421fe130228581103ca44904bb3fb9e49`;
- source commit:
  `f121f51f4d56444f0721962150c1a0d4298a06b2`;
- task-row SHA-256:
  `abffe8c901450c00a8b8dcca755a8553fc0bebf538738bfa4153f4981b0f19ca`;
- composition implementation SHA-256:
  `28e6ff6dfc69a839dee820d1770208b94847132287fa19511eac194d47b3f1b8`;
- episodic implementation SHA-256:
  `f7adc17f8d4c764274df916a4866b915ecdc8fc5526dd6fa2f8aa00edba72c6c`;
- runner SHA-256:
  `ca9871ebee68cc21d0c63245bdb119fd022c4480361e589e7c8ff669b023aa8b`.

## Supported and falsified statements

Supported:

- learner-local maturity can control shared plasticity without a phase signal;
- consolidation greatly improves retention;
- renewable contextual candidates continue learning after consolidation;
- graph topology remains causally responsible.

Falsified:

- immediate hard freeze at first maturity does not achieve old/new coexistence;
- binary freezing is not a sufficient consolidation law.

Unshown:

- an intermediate or confidence-driven consolidation rate;
- replay, local interference detection, option packaging, robust contextual
  choice, self-curriculum, and KRK transfer.

## Required PI decision

This package is closed. Do not choose a better scale after viewing these rows.

The cleanest next package is a preregistered consolidation-dose experiment on
fresh tasks, treating the post-maturity shared-learning scale as the sole
factor. A conservative ladder such as {0.10, 0.25, 0.50, 1.00 control} should
be frozen with one coexistence criterion and no post-result rescue. An
alternative is a new confidence-driven gradual consolidation law, but it should
not be mixed with the fixed-dose question.
