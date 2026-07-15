# Virtual-Frame Mature-Child Handover Canary v2

Date: 2026-07-15. Status: deterministic isolation hardening pass. This is not
a fresh experiment, KRK learning result, or native-transfer authorization.

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

Canary v2 retains the original causal handover and firewall controls and adds a
deep nested-mutable isolation control. All 11 artifact checks pass. Focused plus
full-core validation passes 102 tests, including:

- mutation through the direct runtime nested mapping;
- mutation through the same object reached via `__frame_context__.values`;
- caller and source-context snapshots remaining unchanged;
- a real `chess.Board` being copied, mutated in the virtual evaluation, and
  leaving both the caller board and source-frame board unchanged; and
- all actuation, reward, weight, lifecycle, reservoir, and maturity capabilities
  remaining prohibited in virtual execution.

Artifact:
`reports/autogrowth/virtual_frame_child_response_canary_v2_20260715.json`.
File SHA-256:
`72e5ab340c6e19c6b0d61cd257658e94af48513229e635456ce8a3651a688833`.
Canonical content SHA-256:
`35da04a39c2e4425268a290f8bfd5445f96cab8c91dea23016a13f082586e40e`.

Canary v1 and its artifact remain immutable historical evidence. This correction
does not alter the lifecycle-grace scientific factor and introduces no virtual
frames into that package.
