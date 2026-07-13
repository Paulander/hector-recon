# Architecture Decision: Internal Proprioception and Virtual Frames

Date: 2026-07-13. Status: accepted architecture boundary.

## Decision

Internal terminals are first-class generic embodiment, not optional diagnostics.
They expose locally measurable state through ordinary ReCoN topology so graph
structure can use that state without a host-side decision function secretly
reading learner fields. A measurement backend may be implemented in Python, as
board sensors are, but Python must only measure and actuate a graph-emitted
request; it must not choose an exploration target from hidden candidate state.

`EVIDENCE_DEFICIT` is persistent, internal-real state. In the immediate generic
experiment it measures one candidate's anonymous adjudication evidence and is
consumed by a candidate-local request SCRIPT. The terminal and SCRIPT are
graph-native. The final content-blind actuator bus remains host-executed and may
only allocate an already-scheduled exploration event from emitted graph request
strengths. This package does not claim a full conversion to
`FormalReConEngine`.

Virtual frames and internal terminals are orthogonal mechanisms. A virtual frame
changes the state in which terminals are evaluated; it does not replace the
terminal vocabulary. Future `CHILD_RESPONSE` terminals are frame-local and will
expose a mature child's confirmation, grounded expected value, and uncertainty
for a real or hypothetical successor. `PREDICTION_SURPRISE` compares a prior
virtual child response with the observed real successor.

## Credit boundary

Internal measurements may route requests, but cannot create correctness,
reward, rent, maturity, consolidation, or outcome grounding. In particular:

- evidence deficit may request more ordinary experience but cannot make that
  experience positive;
- mature-child availability may route a parent action but cannot certify the
  child unless the child was grounded by observed outcomes;
- a dream can never confirm itself or supply its own learning credit;
- only observed environment outcomes, or consolidated value emitted by an
  externally grounded mature child, may supply learning credit.

This keeps internal proprioception local without creating a privileged overseer.
The candidate senses the same anonymous evidence currency that will adjudicate
it, while the laboratory retains only frozen protocol, audit, and post-hoc
interpretation authority.

## Immediate implementation consequence

The completed activation-count package is immutable negative evidence. Its host
function read `activation_count` and selected an action, so it was graph-backed
but not fully graph-internal. The next causal package must use the same terminal
and request-SCRIPT topology in both proxy and exact arms. Only the measurement
backend differs: raw trial activation count versus exact retained reservoir
support. Only live trials may request in this experiment. Mature candidates keep
the exact counter for audit but cannot replenish evidence or affect request
allocation.

## Next architectural layer

After the evidence-currency package is closed, the next engineering canary is a
side-effect-free `FrameContext` with frame-evaluable external and internal
terminals. The intended handover is:

```text
virtual action -> hypothetical successor -> request mature child
-> frame-local CHILD_RESPONSE -> parent selects leg -> real actuator
-> observed successor calibrates PREDICTION_SURPRISE
```

The canary must prove no persistent dream-time weight, lifecycle, reservoir,
maturity, reward, or actuator mutation and must include shuffled response,
disconnected terminal, no-frame, leakage, and self-credit controls. It is not
part of the immediate evidence-deficit experiment and cannot support a fresh KRK
claim by itself.
