# Generic-Core Adaptive Consolidation: Activation Decay Falsified

Date: 2026-07-12. Track: generic-core development. Verdict: valid negative
result. No automatic schedule repair, new mechanism, confirmation, integration,
or KRK transfer authorized.

## Frozen execution

The contract was committed at `bb13ec4`. The opt-in learner-local schedule,
audit instrumentation, lifecycle tests, budget tests, and frozen runner were
committed at `923d5ec`. Before fresh task generation, the complete core and
new runner suites passed 60/60.

The runner then completed one execution on 20 fresh seeds 20261501--20261520 and
preserved the full artifact.

## Arm results

| Arm | Median old joint | Median new joint | Old mean | Median key old/new | Mature new pair | Median topology ablation |
|---|---:|---:|---:|---:|---:|---:|
| Adaptive activation decay | 0.148438 | 1.000000 | 0.243457 | 1.0 / 1.0 | 20/20 | 0.250000 |
| Fixed-low 0.10 | 0.700195 | 1.000000 | 0.678027 | 1.0 / 1.0 | 20/20 | 0.520996 |
| Fixed-full 1.00 | 0.000000 | 1.000000 | 0.146777 | 1.0 / 1.0 | 20/20 | 0.249023 |

The adaptive arm:

- missed the 0.85 old-regime gate by 0.701562;
- beat fixed-full old performance on 10/20 tasks, versus required 16/20;
- beat fixed-low old performance on 2/20 tasks, versus required 14/20;
- passed the new-regime, key, contextual-pair, and topology-ablation gates.

The combined verdict is `gates_pass: false`.

## Mechanism exposure and integrity

The adaptive law did execute materially:

- median mature-evidence activations: 7,678;
- scale at most 0.20: 20/20 tasks;
- median minimum applied scale: 0.10;
- median mean channel scale after maturity: 0.450906;
- every task had mature structure, mature evidence, post-maturity shared
  updates, and post-maturity candidate updates.

All invariant gates passed:

- equal episode/evaluation/total-action/RNG budgets: 20/20;
- maximum live candidates: four;
- maximum total proposals: 32, under the limit of 64;
- graph/update mismatch count: zero;
- trial-root leakage: zero.

The failure is therefore behavioral, not absent treatment, unequal compute,
resource overflow, or runtime leakage.

## Interpretation

Repeated mature-child activation is a valid local clock for gradual plasticity
decay, but it is not a sufficient consolidation law. The adaptive arm lies much
closer to fixed-full than fixed-low retention. It allows shared weights to
remain substantially plastic while evidence accumulates; once those weights
have been overwritten by the later regime, subsequently reaching the 0.10 floor
does not reconstruct the earlier shared baseline.

The fixed-low control independently reproduced the previous ordered effect
(old median approximately 0.70, new median 1.0), strengthening the finding that
shared plasticity controls retention. What failed is the proposed
activation-only timing solution.

Do not tune the 1,024-activation horizon or floor on these rows. The stronger
architectural implication is that mature contextual structure needs control
over where residual updates are stored. New-context adaptation must not rewrite
the shared substrate on which old mature structure still depends.

## Artifact and provenance

`reports/autogrowth/generic_core/adaptive_consolidation_key_door_20260712.json`

- artifact SHA-256:
  `01c5bedaed69a9e1cc0541f442eb036f965da4ad1a426e4581b4b98c68fb39f0`;
- source commit:
  `923d5ec0b851dcd1e7e691ef25373ca87e3d34c1`;
- task-row SHA-256:
  `e637122c6ac3ffb6ff2d50cd72275d95351a4fe300cb901df8dd279b4891ff7d`;
- runner hash matches the frozen source;
- all 20 task rows and helper hashes are present.

## Supported, falsified, and unshown

Supported:

- learner-local mature activation can drive an auditable gradual schedule;
- the fixed stability-plasticity effect replicates on fresh tasks;
- graph-grown contextual topology remains bounded and causally relevant;
- positive shared plasticity preserves new-regime acquisition.

Falsified:

- the frozen mature-activation decay law does not achieve coexistence;
- delaying reduction until mature activations accumulate does not outperform an
  immediate fixed-low scale.

Unshown:

- responsibility-weighted residual allocation between shared and contextual
  weights;
- context-gated fast/slow weight stores or option packaging;
- interference-triggered protection/restoration;
- replay/consolidation during virtual frames;
- generic-core confirmation, curriculum integration, and KRK transfer.

## Required PI decision

This package is closed. The next mechanism should not be another fixed horizon
or floor sweep.

The strongest bounded next question is **contextual responsibility allocation**:
when a mature composite is active, route most of its residual update to that
contextual structure and protect shared primitives; when no mature composite
yet explains a novel context, allow a task-generic shadow adapter to learn
without immediately rewriting consolidated shared weights. This is closer to
the intended parent/child credit system than a global learning-rate schedule.

That mechanism needs its own information-boundary analysis, expressivity
control, preregistration, fresh randomized tasks, and explicit PI authorization.
