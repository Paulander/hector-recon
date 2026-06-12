# Active Brief: KRK Autogrowth v0

Status: learning-core reset branch.

The previous branch mode over-optimized for not approving bad mechanisms. This branch should optimize for allowing a minimal learner to act in sandbox, receive credit, promote or delete candidate topology, and prove whether the loop is alive.

## Current Direction

Build and evaluate one causal trace-derived topology-growth loop. Triplets are the current narrow proof pattern, not the full candidate space:

```text
rollout -> trace -> triplet candidate -> sandbox activation -> credit ->
M3 update -> promotion/deletion -> M4 consolidation -> held-out evaluation
```

The experiment is not "finish Stage7" or "prepare Stage8". It is:

> Can ReCoN grow one useful topology addition from traces that improves held-out KRK conversion without learner-visible stage labels?

## What To Keep Active

- Core ReCoN graph/request-confirmation engine.
- Triplet representation.
- Stand-alone or shared-performance sensor TERMINAL candidates, when they are equivalent to per-script terminal instantiations in saved/real ReCoN topology.
- Primitive local sensor-composition candidates: AND, OR, XOR, and LAG/temporal terminals that compare current sensor values against prior ticks to expose change, low-pass behavior, and derivative-like signals.
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

## Current Topological-Growth Checkpoint State

The old `M` labels in this file are subcheckpoints inside one larger milestone: **TG: topological growth works**. They should not be read as separate research milestones.

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
- M16 reusable SCRIPT fragments are implemented. M15 exact starts are generalized through local TERMINAL subcondition fragments over generic KRK features, still under SCRIPT/ACTION/stem-cell structure.
- Current M16 result opens only a narrow partial-curriculum runway: `reports/autogrowth/krk_autogrowth_m16_script_fragments.json` gives 11 train starts, 10 heldout starts, 12 heldout steps, 2 completions, zero heldout rook losses, and 0/200 mates. `partial_curriculum_ready=true`, `broad_curriculum_ready=false`.
- TG17 triplet-chain runway is implemented. `reports/autogrowth/krk_autogrowth_tg17_triplet_chain_runway.json` inventories four ready/formally validated legacy predefined-topology KRK control runs, exposes current candidates as before-terminal -> ACTION delta -> after-terminal triplets, and finds 42 after-to-before chain edges.
- Current TG17 result allows only a bounded partial curriculum: 11 train starts, 5 train mates, 10 heldout starts, 42 chain edges, zero heldout rook losses/illegal moves/stalemates, and 0/200 heldout mates. `bounded_partial_curriculum_allowed=true`, `broad_curriculum_allowed=false`.
- TG18 bounded fragment-chain curriculum is implemented. `reports/autogrowth/krk_autogrowth_tg18_fragment_chain_curriculum.json` runs protected baseline, sham fragment-chain, and real fragment-chain arms over the locked TG17/M16 runway.
- Current TG18 result is a clean failure with rollback/quarantine: h40 real chain remains 0/200 mates and reduces repetition events from 2,600 to 2,574, but causes 2 rook-loss regressions. Training M3 updates: 16; heldout M3 updates: 10; heldout chain starts: 8; completions: 1; M4 consolidation: 0.
- TG19 isolated LAG terminal checkpoint is implemented. `reports/autogrowth/krk_autogrowth_tg19_lag_terminals.json` adds a local temporal TERMINAL over generic feature deltas (`rook_attacked_by_black`, `rook_present`, repetition seen) that can inhibit a candidate transition but cannot choose a replacement move.
- Current TG19 result is partial-continue, not competence: h40 LAG keeps 0/200 mates, removes the 2 no-LAG rook losses, triggers 2 local suppressions, and keeps safety clean, but chain completions drop from 1 to 0 and repetition only improves by 1 event vs baseline. Training M3 updates: 16; heldout M3 updates: 9; M4 consolidation: 0.
- TG20 local continuation retry is implemented. `reports/autogrowth/krk_autogrowth_tg20_continuation_retry.json` lets a LAG-suppressed active SCRIPT completion locally retry another same-parent SCRIPT sibling if that sibling passes the same local TERMINAL checks.
- Current TG20 result is the first small conversion signal on this autogrowth runway, but still only partial-continue: h40/h80 retry reaches 1/200 mates, keeps 0 rook losses/illegal moves/stalemates, restores 1 chain completion vs TG19 LAG-only, reduces h40 repetition by 16 vs baseline, and records 2 heldout retry successes. Training M3 updates: 22; heldout M3 updates: 11; M4 consolidation: 0.
- TG21 local retry-edge reinforcement is implemented. `reports/autogrowth/krk_autogrowth_tg21_retry_edges.json` mines train-only active-SCRIPT -> sibling-SCRIPT retry edges and applies their bonus only inside the same local LAG-suppressed retry context.
- Current TG21 result is a clean no-scale failure: 4 retry edges were mined, 2 edge bonuses fired on heldout, and safety stayed clean, but h40/h80 remained identical to TG20 retry at 1/200 mates, 1 chain completion, 0 rook losses, and the same repetition counts. M4 consolidation: 0.
- TG22 retry diagnostics is implemented. `reports/autogrowth/krk_autogrowth_tg22_retry_diagnostics.json` traces TG20/TG21 retry events without changing behavior.
- Current TG22 diagnosis: retry edges are redundant. The artifact records 43 retry events and 18 heldout no-edge/edge comparisons; edge bonuses fired in 4 comparisons but changed the chosen sibling 0 times. Most retry requests had no local sibling available: 34 no-sibling events vs 4 completion/mate-linked events.
- TG23 retry-candidate expansion is implemented. `reports/autogrowth/krk_autogrowth_tg23_retry_candidate_expansion.json` mines additional train-only SCRIPT siblings from retry contexts where TG22 saw no local sibling.
- Current TG23 result is a clean precision failure: 8 expansion candidates were generated from 6 train retry contexts, but heldout h40/h80 dropped from TG20's 1/200 mates to 0/200, completions dropped from 1 to 0, retry successes dropped from 2 to 1, repetition returned to baseline, and safety stayed clean. The new candidates created more starts/steps and negative credit, not better continuation.
- TG24 curriculum reward recovery is implemented. `reports/autogrowth/krk_autogrowth_tg24_curriculum_reward_recovery.json` recovers the old `src/recon_lite_chess/training/krk_curriculum.py` reward/stage diagnostics as evaluation and credit instrumentation only.
- Current TG24 result: TG18-TG23 did not use `krk_reward`, `KRK_STAGES`, `box_min_side`, or `did_box_grow` in their runtime loops. TG24 now records old curriculum reward components, excess moves where exact curriculum positions apply, box/confinement trajectories, generic progress trajectories, repetition/fivefold, repeated white actions, rook attacked/missing, paired candidate-on/off deltas, and a yoked random SCRIPT-fragment control. Heldout h40 candidate-on remains TG20-like at 1/200 mates with no rook-loss/stalemate regressions and +0.97 graded-credit delta; yoked random also reaches 1/200 mates but has -0.46 graded-credit delta, worse non-terminal progress, and more confinement regressions. Trace-mined therefore beats yoked random on graded credit, but still exposes 3 confinement regressions and only a tiny mate signal.
- TG25 local precision gate is implemented but superseded as the active path. `reports/autogrowth/krk_autogrowth_tg25_local_precision_gate.json` audits confinement sign semantics first: positive `box_min_side_delta` means looser/worse confinement because `did_box_grow` is `box_min_side_after > box_min_side_before`.
- TG25 precision-gate result is a clean no-M4 failure: train evidence had 11 changed candidate rollouts, 5 negative-or-confinement-regression changes, and 2 confinement-regression changes. The local TERMINAL/RET gate suppressed 21 heldout candidate actions and reduced total confinement-worsened events from 1546 to 1540, but h40 mate signal dropped from ungated 1/200 to gated 0/200, graded credit fell by -2.56 versus ungated and -1.59 versus baseline, and one paired confinement regression remained. M3 was frozen for confirmation; M4 consolidation stays 0.
- Active TG25 direction is now foundation curriculum re-entry: use the old KRK curriculum as the actual experience distribution and training/evaluation runway, not merely diagnostics. Start with dense generated Mate_In_1 positions, then verified forced Mate_In_2 positions, before returning to edge-trap/fence/cut/box stages.
- Curriculum scheduling is allowed and is not a purity violation. Stage/curriculum labels may choose the training distribution and appear in diagnostics, but learner-visible features remain generic board/graph/action/outcome features. Runtime tablebase/DTM move provision, direct provider override, stage-label features, and hand-authored tactical names remain forbidden.
- Current TG25 foundation implementation trains local ACTION TRIAL nodes with M3 credit over legal generated Mate_In_1 moves, uses checkmate only as the reward label, and promotes via M4 only when heldout accuracy clears threshold. Mate_In_2 is generated by mechanical forced-mate verification, not by trusting old stage templates.
- Current TG25 foundation result: `reports/autogrowth/krk_autogrowth_tg25_foundation_curriculum.json` passes. Mate_In_1 improves from pre-training 28/300 to 300/300 heldout and 120/120 mirrored generalization; wrong-action suppression is 5179/5253, M3 updates are 591,698, and Mate_In_1 M4 event count is 1. Verified Mate_In_2 reaches 83/100 first-move success and 83/100 3-ply conversion with M4 event count 1. Labels remain schedule/diagnostic only; learner-visible records use generic ACTION feature nodes.
- TG26 edge/fence curriculum is implemented as a bounded continuation of TG25. `reports/autogrowth/krk_autogrowth_tg26_edge_fence_curriculum.json` uses curriculum as the training distribution, reuses the Mate_In_1/Mate_In_2 foundation, and switches harder-stage credit to graded reward: mate dominates; slow mate is still better than non-mate; reaching earlier solved regions is good; confinement/fence/king approach are small shaping terms; repetition/no progress, confinement regression, rook loss, stalemate, and illegal moves are penalized.
- Current TG26 result is a useful fail, not an advancement: bounded edge-trap heldout is 1/8 conversion with 1/8 earlier-region handoff, 2 rook-loss events, 2 confinement regressions, M3 updates 8,717, and M4 0. Fence-hold heldout is 0/8 conversion, 0/8 handoff, 3 rook-loss events, 4 confinement regressions, M3 updates 8,970, and M4 0. Foundation regression passes in the bounded run, but stage advancement/safety fail.
- TG26 also exposes a throughput issue: 500/100 edge/fence chunks with all-legal-action, all-black-reply handoff scoring were not practical in this run. Before long edge/fence training, optimize/cap scoring or cache reusable foundation/handoff evaluations. Do not return to broad random KRK or ecological spawning until edge/fence small slices pass safely.
- TG26b failure repair is implemented. `reports/autogrowth/krk_autogrowth_tg26b_edge_fence_failure_repair.json` adds detailed failure-slice audit, cheap generic safety/progress scoring for all legal actions, deep foundation handoff scoring only for top-K actions, cached cheap/deep scores, and a strict local safety gate for rook-loss, one-reply rook-loss risk, stalemate, and confinement regression. This is local board/action/outcome safety credit, not a global strategy provider.
- Current TG26b result is a safe partial continue, not M4: larger bounded slice uses 160 train samples, 48 heldout positions, and 2 chunks per edge/fence stage. Edge-trap improves to 10/48 conversion and 10/48 earlier-region handoff, with 0 rook losses, 0 confinement regressions, M3 updates 142,876, M4 0. Fence-hold improves to 7/48 conversion and 7/48 handoff, with 0 rook losses, 0 confinement regressions, M3 updates 143,152, M4 0. Foundation regression still passes: Mate_In_1 1.0 heldout, Mate_In_2 0.8125.
- TG26b throughput improved: edge-trap cheap-scored 3,708 actions, deep-scored 1,589, pruned 4,397, and safety-rejected 608; fence cheap-scored 3,740, deep-scored 1,585, pruned 4,497, and safety-rejected 924. Continue conditions pass, but stage advancement thresholds do not, so M4 correctly remains 0.
- TG26c handoff-filtered curriculum is implemented. It keeps TG26b safety/graded credit but optionally requires the position generator to find at least one deep-scored candidate action that can hand off to the Mate_In_1/Mate_In_2 foundation. This filter is trainer-side curriculum scheduling only: it is not a learner-visible feature, not a provider override, and not a runtime DTM/tablebase move source.
- Current TG26c result is a sharper partial continue: `reports/autogrowth/krk_autogrowth_tg26c_edge_fence_curriculum_handoff.json` uses edge handoff-filtered generation over a 160-train/48-heldout, 2-chunk bounded slice. Edge-trap improves to 34/48 conversion and 34/48 earlier-region handoff, with 0 rook losses, 0 confinement regressions, 0 stalemates, M3 updates 138,920, and M4 0. Fence-hold remains at 7/48 conversion/handoff with clean safety because fence handoff filtering was disabled in the larger run.
- `reports/autogrowth/krk_autogrowth_tg26c_edge_fence_handoff_generation_smoke.json` proves combined edge+fence handoff-filtered generation at smoke scale: edge 7/12 and fence 7/12 conversion/handoff, both with 0 rook losses, 0 confinement regressions, 0 stalemates, M3 nonzero, and M4 0. Larger combined fence-filtered runs were too slow at 96/32 and 160/48, so the next bottleneck is throughput, not another retry candidate.
- TG26d handoff-filter validation is implemented. `reports/autogrowth/krk_autogrowth_tg26d_handoff_filter_validation.json` first verifies the canonical TG26c main artifact as full parseable JSON: 3,343,251 bytes, schema `krk_autogrowth_tg26c_edge_fence_handoff_curriculum.v0`, sha256 `50e6cb6eecb52f9ddddff6a61b8ac665f162dedd1333ce640b2a342720844d6a`. Smoke is no longer the only evidence.
- TG26d conservative interpretation: handoff-filtered heldout measures curriculum runway usefulness, not stage competence. The bounded main TG26d run uses 40 filtered train-pool positions, 80 train samples per chunk, 12 heldout positions per slice, and 2 chunks. Edge-trap gets filtered 4/12, unfiltered 6/12, boundary-near-miss 1/12 conversion/handoff with 0 rook loss/stalemate/illegal/confinement regression, M3 68,356, M4 0. Fence-hold gets filtered 7/12 but unfiltered 0/12 and boundary 0/12 with clean safety, M3 69,184, M4 0. This is partial edge generalization evidence and fence runway-only evidence; it is not an edge/fence competence claim.
- TG26d generator stats show the selection pressure directly. Edge filtered train-pool acceptance is 40/172 attempts (23.3%) with 87 no-handoff rejections. Fence filtered train-pool acceptance is 40/630 attempts (6.35%) with 397 invalid generations and 191 no-handoff rejections. On-demand 80/24 and 160/48 TG26d validation runs were stopped after several minutes, so the remaining blocker is persistent/indexed handoff-eligible pool generation, especially for fence.
- Next checkpoint: build reusable handoff-eligible and boundary/near-miss position pools with persisted generator stats, then rerun larger filtered/unfiltered/boundary validation. Do not proceed to broad KRK, ecological spawning, or M4 consolidation until fence shows safe unfiltered or boundary transfer and foundation regression stays clean.

## Current Architecture Guardrail

- Reuse `src/recon_lite_hector/nodes/stem_cell.py`, `src/recon_lite_hector/learning/m5_structure.py`, and `src/recon_lite_hector/nodes/pack_template.py` before adding new lifecycle concepts.
- Do not reduce topological growth to triplets only. Valid candidate nodes/subgraphs include stand-alone input terminals, local sensor-composition terminals, and small circuits built from generic primitives, as long as behavior-changing use is mediated through ReCoN graph structure.
- Shared sensor implementations are allowed as a training/runtime performance shortcut only when semantically equivalent to each consuming SCRIPT owning its own TERMINAL instance; saved topology and trace audit should make that equivalence explicit.
- LAG terminals are important future primitives because they add temporal resolution: they can compare a sensor with one or more previous ticks and let local circuits detect change, persistence, low-pass filtered state, or derivative-like movement.
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
