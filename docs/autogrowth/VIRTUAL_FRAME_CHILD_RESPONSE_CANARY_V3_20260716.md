# Virtual-Frame Mature-Child Handover Canary v3

Date: 2026-07-16. Status: deterministic contract-versioning pass. This is not
a fresh experiment, KRK learning result, or native-transfer authorization.

Canary v3 preserves v2 and versions the deterministic artifact because the child
contract now serializes POLICY_RESPONSE and AVAILABLE separately. The compatible
`confirmed` field is an alias for AVAILABLE; VALUE remains conditional on it,
and GROUNDING remains provenance rather than present applicability. The virtual
execution behavior and causal controls are otherwise unchanged.

## Correction

Canary v1 protected the top-level `FrameContext.values` mapping but retained
shallow references to nested mutable values. A terminal could therefore reach a
caller-owned list, mapping, or board through either the direct environment key
or `env["__frame_context__"].values`. The capability firewall remained useful,
but the state-isolation claim was too broad.

`FrameContext` now deep-snapshots values at construction and creates a second
deep-isolated runtime `FrameContext` for each environment overlay. Within one
evaluation, direct environment values and `__frame_context__.values` deliberately
refer to the same runtime objects. Neither path refers to the caller's object or
the source context's retained snapshot. `VirtualFrameExecutor` combines this
explicit value isolation with capability denial and protected-state rollback. It
is not a universal Python sandbox: arbitrary closures or external resources must
still be declared/protected or isolated by the caller.

The raw imagined-versus-observed delta is now named `PREDICTION_RESIDUAL`. The
old `prediction_surprise_terminal` remains only as a compatibility alias. No
actionable surprise is claimed; a future attention signal must be gated by
confidence, calibration, maturity, grounding, and effective experience.

## Evidence

Canary v3 retains the original causal handover and firewall controls and adds a
deep nested-mutable isolation control. All 11 artifact checks pass. The focused
package passes 30 tests and the full repository suite passes 886 tests,

- mutation through the direct runtime nested mapping;
- mutation through the same object reached via `__frame_context__.values`;
- caller and source-context snapshots remaining unchanged;
- a real `chess.Board` being copied, mutated in the virtual evaluation, and
  leaving both the caller board and source-frame board unchanged; and
- all actuation, reward, weight, lifecycle, reservoir, and maturity capabilities
  remaining prohibited in virtual execution.

Artifact:
`reports/autogrowth/virtual_frame_child_response_canary_v3_20260716.json`.
File SHA-256:
`fedc49c9780a1a1a49260481f5f9ee3c428e8cfda71699a662b11d60a5a29738`.
Canonical content SHA-256:
`deecc4e6b30225d477355782a45fad9112d05a893418c89c992e7d35d9aa18b1`.

Canary v1 and v2 remain immutable historical evidence. This correction
does not alter the lifecycle-grace scientific factor and introduces no virtual
frames into that package.
