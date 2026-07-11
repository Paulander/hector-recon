# External audit: native intrinsic KRK work package

Date: 2026-07-11  
Branch: `codex/native-from-scratch-krk`  
Audited implementation boundary: `c565634` through `9aba7c9`, plus the completed preregistered artifact described below.

## Executive verdict

This branch materially advances the project, but it does not yet demonstrate an end-to-end self-contained, self-growing ReCoN that solves KRK.

The strongest result is now a clean causal partial success:

- A graph with one generic receptor root and no learned KRK nodes, edges, triplets, or weights learned the balanced Mate-in-1 rung (R0) and reached 16/16 validation plus 16/16 regression at epoch 8.
- The same persistent graph was frozen at R0 and trained on a disjoint, symmetry-balanced Mate-in-2 rung (R1).
- With mature-child virtual-frame bootstrap, R1 reached 8/16 validation and 5/16 regression after 240 epochs. The matched no-bootstrap control remained 0/16 and 0/16. R0 retention was 16/16 in both arms.
- Therefore mature, outcome-grounded child competence causes held-out R1 behavior. However R1 did not reach the preregistered joint 100% gate and must not advance to R2.

The result supports the central mechanism—"a known positive state" can be emitted by a mature child and can train its parent—but it also shows that this mechanism alone does not yet organize exact quiet setup/approach selection across all KRK orientations. The next scientific problem is autonomous selectivity/composition, not adding more externally supplied chess rules.

A second boundary matters for publication claims: the graph and credit are native/persistent, but the current scientific contract explicitly reports `pure_in_graph_arbitration_claimed=false` and `python_weighted_arbitration_used=true`. This is a defensible experimental bridge, not yet the final fully self-contained architecture.

## What was actually tested

### Purity and initialization

The initial audit was:

| Quantity | Value |
|---|---:|
| Nodes | 1 generic receptor root |
| Edges | 0 |
| Triplets | 0 |
| Trainable learned edges | 0 |
| Nonzero learned node weights | 0 |
| M3 updates | 0 |

Generic embodiment remained available: board sensors, legal move enumeration/execution, observable terminal facts, formal confirmation, and content-blind growth/plasticity. Exact chess predicates were used trainer-side to schedule and stratify curriculum positions and post-hoc to measure outcomes. They were not supplied as action targets, features, shaping rewards, initial weights, or topology.

The reward channels were observed world terminal outcome, real-move metabolic cost, and mature outcome-grounded child value. Virtual frames did not create grounding.

### Frozen pools

The correction experiment was committed before execution. Combined pool hash:

`49a680bc4c91f91dc0c5f1d8b7f68c62e7dae8c75209d6e2470339d8f7935f12`

All pools were FEN-disjoint. R0 and R1 train/validation/regression were also disjoint under all eight D4 board symmetries. No final test was created or touched.

R0 used 48/16/16 positions balanced across four black-king edges and four corners. The 40 R0 positions observed in the failed preceding run, and every D4 equivalent, were retired before correction.

R1 used 48/16/16 positions balanced across:

- rook-barrier setup on left/right/bottom/top;
- king approach with the black king on left/right/bottom/top edge;
- king approach in corners a1/a8/h1/h8.

### Main arm result

| Gate | Full intrinsic bootstrap | No bootstrap |
|---|---:|---:|
| R0 validation before R1 | 16/16 | same frozen snapshot |
| R0 regression before R1 | 16/16 | same frozen snapshot |
| R1 validation | 8/16 | 0/16 |
| R1 regression | 5/16 | 0/16 |
| R0 retention after R1 | 16/16 | 16/16 |
| Null/illegal R1 selections | 0/0 | 0/0 |
| Mature-child handoffs | 1,591 | 0 |
| Virtual-frame queries | 11,241 | 0 |
| Training episodes | 11,520 | 11,520 |
| Stopped epoch | 240 | 240 |
| Joint mastery | no | no |
| Duration | 10,909.7 s | 3,035.7 s |

The full arm's validation trajectory was 0% at epoch 20, 12.5% at 40, 31.25% at 100–120, 50% at 160, and 56.25% at 180–220. It fell to 50% at epoch 240. This reproduces the earlier warning that continuing plasticity after a local peak can degrade a useful configuration. Because interval snapshots were not durable, the epoch-180 state cannot now be consolidated or causally evaluated.

R1 fast value saturated at 1.0 in the full arm, but slow value remained 0, causal confirmations remained 0, and the R1 competence correctly remained immature. The no-bootstrap R1 fast value reached -1.0. These values changed behavior only in the full arm, unlike an earlier implementation where hierarchy credit was learned but omitted from action scoring.

The final graph in either arm contained 6,808 nodes, 322,942 edges, 1,291 triplets, and 161,471 trainable edges. Existing R0 parameters (2,194 node parameters and 46,778 edge parameters) were frozen before R1.

## Chess interpretation of the remaining R1 failures

The graph has learned that reaching a mature Mate-in-1 successor is valuable. It has not learned a sufficiently selective policy for the exact first move that guarantees that successor after every Black reply.

Post-hoc inspection found 19 held-out failures in the full arm. Eleven were premature rook checks: the selected move checked the black king immediately, while the exact Mate-in-2 move was an adjacent quiet rook placement that established the correct barrier and left no escape after the reply. Examples include selecting `c2c7` instead of quiet `c2c8`, `d5d3` instead of quiet `d5d4`, and `f8f5` instead of quiet `f8f6`.

The other eight failures were wrong quiet rook offsets or wrong king-approach squares. In every failed row, the selected move failed at least one legal reply; most premature checks failed all replies.

This is not evidence that the sensor vocabulary aliases checks and quiet moves. Earlier atom audits showed distinct `gives_check`, escape-availability, and geometric successor atoms. It is evidence that ordinary shared-atom weighting plus current hierarchy-edge credit does not reliably form the required conjunction/competition rule. "Check" remains attractive because it shares many positive contexts, while the negative evidence for preserving the exact quiet barrier is diluted.

The per-stratum result reinforces this. The full arm generalized to several corner and king-edge cases, but right/top rook-barrier strata were especially weak. Balancing exposure removed gross absence; it did not automatically create a symmetry-general composite rule.

## Work-package chronology and what each change established

| Commit | Contribution | Remaining boundary |
|---|---|---|
| `c565634` | Intrinsic hierarchical competence credit with parent-distance decay | Credit existed outside native action consumption |
| `28805bb` | Recorded intrinsic outward curriculum as central doctrine | Documentation did not guarantee execution fidelity |
| `c510f49` | Empty-state persistent native R0/R1 runner and purity tripwires | Early R1 integration and retention were weak |
| `bc77182` | Frozen R0 snapshot, child routing/retention, cache parity evidence | Flat routing and later candidates could interfere |
| `8d46239` | Immediate freeze on joint validation+regression mastery | No durable interval snapshots |
| `4e6b633` | Consumed exact hierarchy-edge credit in R1 action scoring | Shared atoms still lacked exact selectivity |
| `37fcba7` | Recovered and documented historical corner-coverage lesson | R0 of the next preregistration was still random |
| `ebcfd88` | Preregistered symmetry-balanced high-resolution R1 | New seed failed random R0 gate; R1 was not executed |
| `9aba7c9` | Added balanced R0, retired-orbit exclusion, and correction preregistration | Single seed; R1 still below gate |

## What this chat/work package repeatedly missed

1. **The central curriculum rule was rediscovered more than once instead of being enforced end-to-end.** Earlier work broadened into edge/fence distributions before a high-resolution persistent chain was certified. In this round, R1 was balanced while R0 was initially left random; the first preregistered run failed 6/8 validation even though regression was 8/8. Applying the historical edge/corner lesson to R0 immediately produced 16/16 plus 16/16 at epoch 8.

2. **Aggregate accuracy hid geometric holes.** Small random pools could pass or plateau depending on corner/orientation composition. Explicit strata and D4 orbit isolation should have existed from the first R0 runner.

3. **Learning a value was confused with using it in action competition.** R1 competence and per-edge credit changed internally in earlier runs, but the policy scored only shared terminal local weights. `4e6b633` repaired that integration defect.

4. **Plasticity and structure were allowed to chase each other too long.** R0 previously hit 100% and then degraded. The current R1 full arm peaked at 9/16 and ended at 8/16. Immediate joint freeze helps only at full mastery; sub-mastery consolidation/model selection is still absent.

5. **Parent/child isolation was incomplete.** R1 learning initially rewrote shared R0 parameters, then new R1 candidates competed on R0 states. Freezing the mature snapshot plus verified child priority restored R0 retention without replay.

6. **Replay was treated as the first retention remedy.** Replay was expensive and could rehearse a drifting policy. The cleaner solution was parameter freeze and scoped child routing; this run used zero R0 replay and retained 100%.

7. **Historical branch evidence was consulted too late.** February work had already identified corner under-coverage, and later work had identified a corner-plus-support conjunction. The reusable lesson was balanced failure strata plus autonomous composite growth, not copying the old teacher/scaffold.

8. **Internal terminology obscured the chess question.** "Handoff", "availability", and "edge credit" are useful implementation labels, but the concrete task is simple to state: choose the quiet rook/king setup whose every Black reply lands in a position the mature Mate-in-1 child can solve.

9. **Observability and resumability were underbuilt.** The full arm ran for over three hours while the durable progress file exposed no epoch number or intermediate validation. Arm-level checkpointing was an improvement, but interval-level graph/credit snapshots are necessary.

10. **Performance improvements were overgeneralized.** The earlier approximately 45–70× gain came from indexed scheduling, early exit, and cached continuation/dispatch. Parts are active here, but 11,241 live-verified child queries still made the full arm 3.6× slower than the control. High-resolution multi-seed work is not practical yet.

11. **The self-contained claim remained broader than the implementation.** The current run is empty-start, persistent, outcome-grounded, and native in graph growth/credit, but final weighted arbitration still occurs in Python. Serialized snapshot/resume is also not implemented; clone parity is currently an in-memory deepcopy probe only.

12. **Artifact handling was not planned early.** Full graph/event artifacts are tens of megabytes and prior oversized commits triggered push review. A compact, hash-linked research artifact should be the committed default; full snapshots belong in an explicit artifact store or LFS policy.

## What improved

- The project now has an executable empty-learned-state R0→R1 chain rather than disconnected curriculum pieces.
- "Known positive state" is implemented as a mature, outcome-grounded child response, not a Python recognizer reward.
- The child response is tested through virtual frames and live formal confirmation; cache hits are not trusted as providers and produced zero live mismatches.
- Parent-distance credit and exact SCRIPT-to-terminal hierarchy-edge weights are consumed by the policy.
- Mature R0 parameters are frozen while later topology remains plastic.
- Child requests are scoped to the frozen R0 triplet snapshot; R1 candidates cannot impersonate the child.
- R0 retention is 100% with zero replay.
- Curriculum pools are explicit, hash-frozen, D4-orbit-disjoint, balanced by historical failure family, and exclude retired development orbits.
- Validation and regression must both reach 100%; no promotion occurred on partial success.
- Per-arm progress survives interruption, and the full/control causal result is now unambiguous.
- Failure analysis is expressed both in chess terms and ReCoN terms.

## Claims that are supported now

1. A native ReCoN ecology can start without learned KRK content and learn a balanced Mate-in-1 policy from observed outcomes for one seed.
2. A mature outcome-grounded Mate-in-1 child can provide an intrinsic successor signal that causally improves held-out Mate-in-2 behavior.
3. Frozen child routing can preserve the earlier competence perfectly while later topology and weights grow.
4. Balanced orientation coverage is essential at R0 and insufficient by itself at R1.
5. The current R1 bottleneck is exact quiet-setup/approach selectivity and consolidation, not total absence of representation or hierarchy signal.

## Claims that are not supported

- R1 mastery, full KRK solution, or advancement to R2.
- Five-seed robustness or a touched-once final-test result.
- Fully in-graph arbitration with no Python weighted policy layer.
- Autonomous discovery of the needed composite conjunction; historical hand-added composites do not count.
- General domain learning, imagination-based multi-step planning, or surprise-driven learning.
- A production-ready fast implementation or serialized crash-safe continuation.

## Immediate next work package

The next package should not run another long R1 experiment unchanged.

1. Add durable interval checkpoints containing graph, credit state, epoch, pool hash, validation/regression probe, and RNG/scheduler state. Prove resume parity against uninterrupted small runs.
2. Profile the full arm and port the earlier cache/index ideas specifically to repeated virtual successor confirmation and hierarchy-edge scoring. Require exact move, score, update-count, checkpoint, and final-artifact parity on a fixed small run before accepting speedups.
3. Add an outcome-driven composite proposal mechanism. Candidate conjunctions should arise from co-active internal terminals/edges in successful child handoffs versus failed/premature-check actions, not from chess-coded move labels. Freeze existing slow weights during bounded structural proposals.
4. Alternate: structural proposal; topology-frozen fast equilibration; validation/replay consolidation; paired candidate on/off confirmation; accept/prune. Preserve the mature R0 snapshot throughout.
5. Compare self-grown composites with firing-rate/size-matched random composites. The key gate is selective improvement in the weak quiet-barrier strata, not aggregate training fit.
6. Add fast/slow consolidation selection below full mastery: retain a validated peak only under a preregistered rule, then continue from a clone rather than overwriting the best known state. Do not tune on the current held-out rows.
7. After performance and composite machinery are frozen, preregister fresh R1 pools and at least three development seeds. Move to five seeds and a touched-once final set only after the mechanism is stable.
8. Do not open R2 until R1 reaches 100% validation and regression, preserves R0, beats control, and passes every stratum.

## Mid- and long-term roadmap

After R1 certification, continue the same persistent ecology outward:

- R2: black king trapped at edge, fence up, white king close; reach mature R1/R0.
- R3: same-side rook/king tempo; learn the handover into R2.
- R4: edge trapped with king farther away; learn approach without losing rook/fence.
- R5: edge drive with established fence.
- R6: safe fence establishment.
- R7: broad legal nonterminal KRK.

At each rung, the positive intermediate signal must be the mature child's learned expected value. Rook loss, stalemate, and real move cost are observable intrinsic negatives. No exact mate-distance or forced-move provider should select runtime actions or supply reward.

Hierarchy-dependent plasticity is a plausible research extension, but it must be tested rather than assumed. Candidate schedules include slower parent learning with depth, age/maturation-based decay, and activation-frequency normalization. Hebbian co-activation may propose wider patterns, but causal outcome/child-value intervention must decide whether they survive.

Dreaming/imagination belongs after the one-step R0→R1 mechanism is reliable. Virtual frames already test immediate successor competence. Multi-step internal rollout and surprise (predicted versus observed successor/outcome) can then address wider "gnome gaps" without obscuring the core result. These mechanisms are scientifically interesting icing; they are not a substitute for closing the native curriculum chain.

The publishable end state would be: empty learned start; one persistent graph; autonomous topology proposal/pruning; intrinsic outcome and mature-child credit; frozen/consolidated competencies; full KRK held-out solution across seeds; then transfer to KPK/KQK without KRK-specific handcrafted nodes.

## Questions for the external expert

1. Does the 8/16 and 5/16 versus 0/16 and 0/16 result adequately isolate mature-child value as a causal mechanism, given common topology and Python weighted arbitration?
2. Is the proposed matched-random composite control sufficient to distinguish useful self-grown conjunctions from capacity increase?
3. What preregistered peak-consolidation rule would avoid both post-hoc model selection and destructive continued plasticity?
4. Which exact parity invariants should gate the performance rewrite?
5. Is R1 the right minimal publication unit, or should the claim require at least one outward strategic rung beyond Mate-in-2?
6. What additional ablation is needed to separate mature-child value, child-priority routing, and hierarchy-edge credit?

## Evidence map

- Central doctrine: `docs/autogrowth/KRK_INTRINSIC_CURRICULUM_LEDGER.md`
- Previous status/dose response: `docs/autogrowth/NATIVE_INTRINSIC_KRK_STATUS.md`
- Failed first preregistration: `reports/autogrowth/native_from_scratch/r1_highres_balanced_seed_20260718_preregistration.json`
- Failed R0-gate result: `reports/autogrowth/native_from_scratch/r1_highres_balanced240_seed_20260718.json`
- Correction preregistration: `reports/autogrowth/native_from_scratch/r0_r1_balanced_seed_20260719_preregistration.json`
- Compact correction result: `reports/autogrowth/native_from_scratch/r0_r1_balanced96_240_seed_20260719_compact.json`
- Full local result SHA-256: `1a4a70ab17c0caf1c1a6cf878b5db3ab707bd02209a56e7bd8a7031fa08af5ed`
