# Virtual-Frame Mature-Child Handover Canary

Date: 2026-07-13. Status: deterministic engineering pass. This is not a fresh
scientific experiment, a KRK behavioral result, or authorization to open native
R1 or support-conditioned lifecycle grace.

## Architectural decision

The branch already had useful virtual-frame fragments: `FormalReConEngine`
could overlay per-node dictionaries, and the native curriculum could ask whether
a frozen Mate-in-1 policy succeeded on a hypothetical board. Those mechanisms
remain intact. They were not yet a reusable handover layer because frame identity
was untyped, the child response was shaped by a KRK host function, and persistent
dream-time effects had no generic firewall.

The core now defines:

- immutable `FrameContext` identity (`real` or `virtual`), lineage, hypothetical
  action, and terminal-visible values;
- frame-local, outcome-grounded `ChildResponse` with confirmation, expected
  value, uncertainty, and an anonymous nonnegative routing strength;
- graph-native `CHILD_RESPONSE` and `PREDICTION_SURPRISE` terminal backends;
- clone-based `VirtualFrameExecutor`, which evaluates ordinary external and
  internal terminals without changing the persistent graph;
- `FrameEffectFirewall`, which rejects real actuation, reward, weight, lifecycle,
  reservoir, and maturity changes from a virtual frame; and
- protected-state leak detection that restores hidden mutations and fails hard.

A dream never grounds or matures a child. `CHILD_RESPONSE` routes only when the
child response is already grounded and confirmed. `PREDICTION_SURPRISE` is
measured on the observed real successor and is a calibration signal, not
self-confirmation or reward.

## Deterministic canary

The canary constructs one parent SCRIPT with two virtual action-leg SCRIPTs.
Each leg requests an external successor terminal and an internal
`CHILD_RESPONSE` terminal. The final generic actuator bus reads only emitted
terminal strength and action identity; it does not inspect child fields or
successor semantics. This accurately preserves the present architectural
boundary: terminal evaluation and request topology are graph-native, while the
last cross-leg allocation/actuation remains host-executed.

The intended chain executes end to end:

```text
virtual action -> hypothetical successor -> grounded mature-child response
-> frame-local CHILD_RESPONSE -> parent action-leg allocation
-> exactly one real actuator -> observed real successor
-> frame-local PREDICTION_SURPRISE
```

All ten deterministic checks pass:

1. grounded mature-child value selects the `advance` leg;
2. shuffling only child responses changes selection to `stall`;
3. only the selected `advance` leg actuates the real environment;
4. the observed successor emits nonzero prediction surprise;
5. a disconnected internal terminal cannot alter selection;
6. omitting a virtual frame blocks dream evaluation;
7. persistent graph state is unchanged;
8. weights, lifecycle, reservoir, maturity, and reward state are unchanged;
9. a hidden closure mutation fails hard and is rolled back; and
10. attempted dream self-maturation is blocked by the effect firewall.

Artifact:
`reports/autogrowth/virtual_frame_child_response_canary_20260713.json`.
File SHA-256:
`d614ab1ae7a56f337e4de46eb06194ac319a02a77e24bae2344046e438913a46`.
Canonical payload content SHA-256:
`23bad0398d536c4a7152c2c477e12048954874f9d1da5b3b6b11f98eb01d6776`.
The focused frame/canary suite passes 14 tests. Full repository validation passes
842 tests in 2,201.96 seconds.

## What this does and does not establish

This establishes a reusable mechanism boundary: graph terminals can inspect a
hypothetical successor, consume a mature child's grounded competence, influence
which action leg reaches the real actuator, and later quantify prediction error
without dream-time learning leakage. The shuffled control makes the child
response causally relevant in the deterministic canary.

It does not establish autonomous discovery of the parent handover, learned
calibration, multi-ply KRK improvement, or a self-grown native R1 policy. The
canary uses a planted tiny graph and deterministic responses specifically to
validate plumbing and firewalls. A later preregistered native package must make
frame-local responses arise from frozen mature child topology and must test
behavior without host semantic selection.

The exact-evidence result remains unchanged: its next isolated scientific factor
is externally frozen support-conditioned lifecycle grace. Virtual frames are a
separate architectural layer and must not be mixed into that causal package.
