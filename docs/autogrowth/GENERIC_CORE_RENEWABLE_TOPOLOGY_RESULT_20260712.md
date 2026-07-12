# Generic-Core Renewable Topology: Failed Retention Package

Date: 2026-07-12. Track: generic-core development. Verdict: structural
mechanism works; retention hypothesis falsified. No repair or rerun authorized.

## Frozen execution

The contract was committed at `d393ad6`. Renewable slot semantics, legacy
compatibility tests, bounded audit counters, and runner were committed at
`336ebe7`; the full generic suite passed 47/47 before 20 fresh tasks ran once.

## Raw gates

| Measurement | Frozen requirement | Observed |
|---|---:|---:|
| Mature cue/regime-1 pair | at least 16/20 | 20/20 |
| Median regime-0 joint success | at least 0.70 | 0.0 |
| Median regime-1 joint success | at least 0.85 | 1.0 |
| Median key accuracy, both regimes | at least 0.90 | 1.0 / 1.0 |
| Persistent beats reset, regime 0 | at least 16/20 | 4/20 |
| Persistent beats reset, regime 1 | at least 16/20 | 20/20 |
| Median composite-ablation drop | at least 0.15 | 0.260742 |
| Maximum total/live candidates | at most 64 / 4 | 32 / 4 |
| Graph/update mismatch and trial leakage | zero | zero |
| Matched configured budgets | 20/20 | 20/20 |

The structural gate passed, but behavioral retention remained decisively below
the frozen threshold.

## Isolation result

Renewable capacity did exactly what it was intended to do:

- every task formed at least one mature door cue/regime-1 composite;
- persistent tasks retained one or two mature regime-0 pairs and one to four
  mature regime-1 pairs;
- no action exceeded four concurrently live candidates;
- no action used more than 32 of 64 lifetime proposals;
- the median causal topology-ablation effect increased from 0.2061 to 0.2607.

Yet old-regime performance remained poor:

- persistent regime-0 key accuracy: 1.0;
- persistent regime-0 door/joint mean: 0.0945, median 0.0, range 0–0.65625;
- persistent regime-1 key/door/joint: 1.0 on every task;
- only four tasks beat the reset control on old-regime joint success.

Therefore missing structural birth was a real blocker, but not the final one.
Even when both old and new context-specific composites exist, phase-1 updates to
shared bias/primitive weights alter the baseline beneath the mature phase-0
subgraphs. Old composite weights are still present but no longer compensate for
the shifted shared score.

## Interpretation

This falsifies the idea that additional self-grown topology alone solves
continual retention. The remaining problem is now specifically stability versus
plasticity:

- shared fast weights remain globally plastic;
- mature local structure has no consolidated baseline contract;
- inactive old contexts receive no corrective experience;
- there is no learner-local replay or interference-triggered reactivation.

This is the generic analogue of the user's earlier concern that topology and
optimal weight configuration co-depend, and that structural epochs need
equilibration/consolidation. The result also supports slower or frozen shared
weights after local competence matures, while leaving new context-specific
candidate weights plastic.

## Artifact

`reports/autogrowth/generic_core/renewable_topology_key_door_20260712.json`

- artifact SHA-256:
  `6b65b0101d76dda7bd75e0a7e58f5d26e59448d44fb96a660e8624331bd5c7e7`;
- source commit:
  `336ebe7bd7fb3b87076aa8e7a5a692358a5f0c02`;
- task-row SHA-256:
  `5221d0cfcba044e92be6d3fec993ffd230344c8c64903ad8b456c92f5e8a303a`;
- composition implementation SHA-256:
  `f2896fdba954761535268df5b506c6ccbb8cd48132a207f31b5a9b9b709cdb2e`;
- episodic implementation SHA-256:
  `f7adc17f8d4c764274df916a4866b915ecdc8fc5526dd6fa2f8aa00edba72c6c`;
- predecessor runner SHA-256:
  `c79e4f5579af1acb3eadb17dc9fd5c746fe826cb36a7ba4bf031439ab98a0c5e`;
- runner SHA-256:
  `afe7ce532df4506e4e85e6ce3b88b6cef1d87c8691983e67560bbddde78bd1e8`.

## Required PI decision

The package is closed. Do not automatically add replay or change learning rates.

The cleanest next factor is learner-local consolidation: after a candidate
becomes mature through future causal benefit, freeze or strongly slow that
action channel's shared primitive/bias weights while leaving trial and
context-specific candidate weights plastic. No phase signal or replay is needed.
Compare this against the unchanged renewable-capacity policy on fresh tasks.

If that fails, separately test learner-local interference replay. KRK transfer
remains unauthorized.
