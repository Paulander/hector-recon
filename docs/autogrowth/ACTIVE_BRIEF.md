# Active Brief: KRK Autogrowth v0

Status: learning-core reset branch.

The previous branch mode over-optimized for not approving bad mechanisms. This branch should optimize for allowing a minimal learner to act in sandbox, receive credit, promote or delete candidate topology, and prove whether the loop is alive.

## Current Direction

Build and evaluate one causal trace-derived topology-growth loop:

```text
rollout -> trace -> triplet candidate -> sandbox activation -> credit ->
M3 update -> promotion/deletion -> M4 consolidation -> held-out evaluation
```

The experiment is not "finish Stage7" or "prepare Stage8". It is:

> Can ReCoN grow one useful topology addition from traces that improves held-out KRK conversion without learner-visible stage labels?

## What To Keep Active

- Core ReCoN graph/request-confirmation engine.
- Triplet representation.
- Baseline-to-ReCoN compiler.
- KRK evaluation harness, refactored toward competence metrics.
- M3 fast plasticity and M4 consolidation as active experimental variables.
- A small promotion-boundary safety gate.

## What Is Historical Only

Archived under `archive/pre_autogrowth_2026_06_10/`:

- Old report/control-plane packets.
- Stage7/Stage8 completion/quarantine artifacts.
- Selector behavior/review artifacts.
- Previous external audit pack.
- Report-gate tests.

Do not rebuild those as the mainline workflow.

## Current Checkpoint State

- M0-M3 are implemented as the active baseline: cleaned branch guidance, feature firewall, locked KRK generation, and baseline/sham evaluation.
- M4 is implemented as non-behavior-changing evidence preparation: train traces plus mechanical triplet candidate mining under `reports/autogrowth/`.
- M5/M6 now run one mined candidate in sandbox-only ReCoN topology, record M3 fast-credit updates, and automatically quarantine on failure.
- Current selected candidate activates on heldout but is rejected: 0/200 mates, 18 rook-loss regressions at h40/h80, M3 updates nonzero, M4 consolidation zero.
- M7 full three-arm artifact is generated: baseline, sham-growth, and autogrowth sandbox are compared in `reports/autogrowth/krk_autogrowth_v0_experiment.json`.
- Current v0 result is a useful fail, not a promotion: candidate is quarantined after 0/200 h40/h80 mates, 18 blunder regressions, M3 updates nonzero, and M4 consolidation zero.
- M8 multi-candidate lifecycle training is implemented: multiple mined candidates can gain experience, receive M3 fast credit, mature, or be quarantined.
- Current M8 result is also a useful fail: 8/8 default candidates and 12/12 broader candidates quarantine under negative credit/rook-loss evidence, leaving no heldout candidate.
- External review clarified the next step: do not add a second candidate architecture. Normalize the existing `StemCellTerminal` / TRIAL / MATURE lifecycle into a stricter local candidate contract with separate relevance and outcome-credit stats.
- M9-M11 local suppressor checkpoint is implemented. `StemCellTerminal` now carries separate candidate-local relevance, credit, and survival stats; XP alone cannot mature a candidate.
- Current M11 result is a safety improvement, not KRK competence: `reports/autogrowth/krk_autogrowth_m11_local_suppressor.json` reduces heldout rook losses from 18 to 3 for the bad M4 sibling action, with 77 local suppressions, zero illegal moves, zero stalemates, and no conversion gain.
- M12 local ACTION arbitration is implemented. Move choice may occur through first-class local ACTION sibling nodes, but the harness cannot install an external move selector or direct override.
- Current M12 result is a safe fail: `reports/autogrowth/krk_autogrowth_m12_local_arbitration.json` rejects every trained M4 ACTION sibling because each receives negative causal intervention evidence. Arbitration falls back to baseline, giving 0 rook losses but still 0/200 mates.
- M13 risk-aware candidate generation is implemented. It enumerates legal training actions offline, rejects projected negative continuations, emits ReCoN-compatible ACTION candidates, and then evaluates them through M12 local arbitration.
- Current M13 result is still a safe fail: `reports/autogrowth/krk_autogrowth_m13_risk_aware_candidates.json` generates 12 candidates from 3,841 legal actions, but arbitration selects 0 heldout actions after local negative-evidence gating; result is 0 rook losses and 0/200 mates.
- M14 context-specialized candidate generation is implemented. It uses 18 generic before-context features with exact-match activation to test whether one-step ACTION candidates were failing from overly broad context.
- Current M14 result is another safe fail: `reports/autogrowth/krk_autogrowth_m14_context_specialized_candidates.json` generates 12 context-specific candidates, but arbitration selects 0 heldout actions; result is 0 rook losses and 0/200 mates.
- M15 local multi-step SCRIPT candidates are implemented. Candidates contain one SCRIPT with two sequential ACTION children and local TRIAL/survival stats.
- Current M15 result is a safe activation failure: `reports/autogrowth/krk_autogrowth_m15_local_scripts.json` generates 12 SCRIPT candidates, but heldout starts/steps/completions are all 0; result is 0 rook losses and 0/200 mates.
- Next checkpoint should address candidate generalization/activation without loosening the safety gate, likely by learning reusable subconditions or script fragments rather than exact full-context script starts.

## Current Architecture Guardrail

- Reuse `src/recon_lite_hector/nodes/stem_cell.py`, `src/recon_lite_hector/learning/m5_structure.py`, and `src/recon_lite_hector/nodes/pack_template.py` before adding new lifecycle concepts.
- Keep relevance separate from valence. Relevance can keep a candidate alive; causal intervention credit is required for maturity/promotion.
- Disable or label as non-causal for autonomy claims: KRK box-method discovery, forced hoisting, perfect/survivor/extreme-failure/sample bypasses, random fallback credited as success, selector/arbiter special modes, and runtime tablebase/DTM.
- Before claiming KRK structural growth, verify the KRK online path runs evolved registry/topology causally rather than rebuilding a fresh demo graph that ignores candidates.

## Current No-Go List

- More readiness packets.
- More selector-runtime work.
- More Stage7/Stage8 patching.
- Report row IDs or stage labels as learner features.
- Runtime tablebase/DTM as a move provider.
- Direct provider override as the growth mechanism.

## Reporting Rule

One run should produce one machine-readable result artifact and, when useful, one short markdown summary. If a report does not summarize a run or decision that changes the next experiment, do not write it.
