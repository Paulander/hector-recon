# Generic-Core Multi-State Key-Door: Failed Retention Package

Date: 2026-07-12. Track: generic-core development. Verdict: hypothesis
falsified on retention. Confirmation claim: none. No repair or rerun authorized.

## Frozen execution

The contract was committed at `59bd5bf`. Legal-action filtering,
multi-decision responsibility tests, and runner were committed at `f5d56d2`;
the full generic suite passed 45/45 before the frozen 20-task range ran once.

## Raw gates

| Measurement | Frozen requirement | Observed |
|---|---:|---:|
| Persistent beats reset, regime 0 | at least 16/20 | 0/20 |
| Persistent beats reset, regime 1 | at least 16/20 | 20/20 |
| Persistent median regime-0 joint success | at least 0.85 | 0.0 |
| Persistent median regime-1 joint success | at least 0.85 | 1.0 |
| Persistent median key accuracy, both regimes | at least 0.90 | 1.0 / 1.0 |
| Median joint composite-ablation drop | at least 0.15 | 0.206055 |
| Mature hidden key and door/regime pair | at least 16/20 | 20/20 |
| Graph/update mismatch and trial leakage | zero | zero |
| Matched configured budgets | 20/20 | 20/20 |

The retention gates failed decisively.

## Behavioral decomposition

Persistent arm after both phases:

- regime 0: key accuracy 1.0, door accuracy 0.0, joint success 0.0 on every
  task;
- regime 1: key accuracy 1.0, door accuracy 1.0, joint success 1.0 on every
  task.

Transition-reset control:

- regime 0 mean key 0.5033, door 0.0159, joint 0.0084;
- regime 1 mean key 0.5041, door 1.0, joint 0.5041.

Every persistent episode credited two selected graph decisions (16,384 decision
credits per task). Every reset episode credited only the door decision (8,192).
The early key was therefore learned perfectly only when its responsibility
survived the actual action-dependent transition.

## Structural diagnosis

The failure is door-policy interference, not missing temporal credit:

- every persistent door channel reached the lifetime four-candidate limit;
- every door candidate was born at observation 128, 256, 384, or 512, entirely
  inside regime-0 training;
- all 20 tasks matured a cue/regime-0 pair;
- zero tasks formed a cue/regime-1 pair;
- regime-1 training reached 100% by flipping shared primitive door weights;
- those shared changes made the old mapping exactly wrong, overwhelming the
  still-present regime-0 topology.

`max_candidates=4` is a lifetime proposal cap. Pruned candidates still consume
the budget, so the ecology had no structural birth capacity when the new regime
arrived. Mature local structure was also unprotected from shared fast-weight
interference; there was no replay or local consolidation.

This directly supports two earlier project concerns: structural capacity must
renew after pruning, and mature context-specific competence needs slower/local
consolidation or exception replay when shared weights change.

## Artifact

`reports/autogrowth/generic_core/multistate_key_door_20260712.json`

- artifact SHA-256:
  `92f9f534b9e9e8c6b9d2fcc7bcf39643003335a351732cfff72364b26949ecdc`;
- source commit:
  `f5d56d2d5c0c2a5698d29a9ebbe808e3c1d74f38`;
- task-row SHA-256:
  `7f7b5aca4e293c65be1670e923cf49188c8edc62e40604d4009b8bb82fa627cf`;
- episodic implementation SHA-256:
  `f7adc17f8d4c764274df916a4866b915ecdc8fc5526dd6fa2f8aa00edba72c6c`;
- composition implementation SHA-256:
  `0b647e16fc2173535d1d01bdfd076947a5dd2d0fc304a9372f805f8161941f2d`;
- runner SHA-256:
  `c79e4f5579af1acb3eadb17dc9fd5c746fe826cb36a7ba4bf031439ab98a0c5e`.

## Supported and falsified statements

Supported:

- graph responsibility spans a real action-dependent transition and credits an
  early decision from terminal-only valence;
- grown topology causally changes behavior in a two-decision environment;
- the learner acquires the new observable regime perfectly;
- legal-action filtering remains an environment interface and graph parity is
  exact.

Falsified or unshown:

- the current law does not retain old door competence while learning the new
  regime without replay;
- continual learning, local consolidation, renewable ecology,
  robust-composition integration, options, self-curriculum, KRK transfer,
  imagination, and dreaming remain unshown;
- perfect new-regime performance is not key-door completion because old-regime
  behavior is exactly inverted.

## Required PI decision

This package is closed. Do not automatically add replay, freeze weights, renew
candidate slots, or rerun.

The cleanest next single factor is renewable structural capacity: make
`max_candidates` a maximum live trial/mature count, let pruned candidates
release their slot, and freeze a separate lifetime proposal/compute budget.
Test whether regime-1 cue composites can then form without replay or learning
rate changes. If new topology forms but retention still fails, isolate local
consolidation/replay next.
