# TG48 Edge-Killbox Audit

Date: 2026-06-30

## Scope

This audit checked whether the repository already contains an intermediate KRK curriculum equivalent to an edge-killbox ladder between the TG46d Mate-in-1/Mate-in-2 foundation and broad TG47 edge/fence positions.

Search terms included: edge killbox, killbox, king on edge, rook fence, fence establishment, edge conversion, black king edge, rook lateral move, king support, knight-distance support, tempo/opposition diagnostics, and DTM/mate-distance shaping.

## Findings

- No existing `TG48`, `edge_killbox`, or `killbox` module, runner, test, or report artifact exists.
- `src/recon_lite_chess/autogrowth/clean_edge_fence_stage.py` implements TG47 broad edge/fence training over families such as `edge_trap_progress`, `fence_hold_progress`, and `bridge_frontier_near`.
- TG47 generation classifies broad local-progress positions using generic edge distance, mobility, king distance, and rook distance. It does not enforce a narrow edge-killbox conversion basin where the black king is already on the edge, the white king is in a support band, and rook same-side/opposed-side geometry is explicitly balanced.
- TG47 reward and evaluation are primarily local progress/safety oriented: confinement improvement, edge progress, black mobility reduction, king approach, rook safety, and graph-positive/all-reply foundation handoff diagnostics.
- TG47g/TG47h/TG47i show that broad graph-positive handoff was overgeneralized and then collapsed under stricter validation. TG47i reports 0/24 non-decoy validated all-reply reachability and a remaining validated decoy all-reply leak.
- Older TG26/TG27/TG29 modules contain edge/fence, boundary, bridge, and foundation-basin diagnostics, but these are either pre-clean-slate, broad edge/fence scaffolding, or shadow/boundary diagnostics. They are not a clean TG46d-frozen edge-killbox conversion curriculum.

## Classification

The existing TG47 edge/fence system is **only a local progress/safety curriculum**, not an already-sufficient conversion-to-mate edge-killbox curriculum.

It can provide implementation patterns for:

- frozen TG46d parent loading;
- `TerminalAffordanceLearner` M3/M4 mechanics;
- compressed trace and graph-summary artifacts;
- safety, decoy, and purity accounting.

It should not be treated as proof that the missing intermediate basin already exists.

## TG48 Implication

TG48 should create a fresh clean-slate child curriculum over generated edge-killbox substages, keep TG46d frozen, use trainer-side labels only for scheduling/evaluation, and keep learner-visible terminal keys restricted to generic board/action geometry.
