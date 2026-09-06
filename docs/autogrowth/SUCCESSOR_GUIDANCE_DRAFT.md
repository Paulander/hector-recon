# Successor guidance and mainline promotion draft

Status: proposed on 2026-09-06 for cross-check with the previous Codex instance.
The user's sequence is review first, then return here to establish the official
main line. This draft does not declare `main` promoted or authorize bypassing
that sequence. The architecture constitution already governs the current branch.

## Proposed entry points after the review

Keep one short, maintained entry point per purpose:

1. `AGENTS.md`: current operating instructions and links, with superseded commands
   moved to historical reference rather than contradicted by later paragraphs.
2. `ARCHITECTURE_CONSTITUTION.md`: the user's enduring objective and information
   boundary. Engineering convenience does not silently amend it.
3. `MATE_ONE_COACH.md`: the actual runnable implementation, evidence and limits.
4. This document: lessons and the accepted continuation decision, after recording
   the old instance's response and changing its status from draft.

The July `CODEX_HANDOFF_BRIEF.md`, accumulated `docs/BRIEF.md` ledger and old TG/V
plans are source material. Do not execute their old phases or assume their
word “current” overrides the present user's direction. Read historical files
when a bounded question or reuse decision requires them.

## The objective a new instance must preserve

Two developmental capabilities must eventually cooperate:

- Useful graph structure grows and is retained, corrected, reused or pruned
  through the organism's own terminal-mediated experience and scalar outcomes.
- Independently trained subgraphs learn contextual delegation and strategic
  handover in a larger graph. Parent requests and child competence/value signals
  must matter to actual behavior.

Train real chess exercises, starting with M1 and then M2 before outward KRK.
KQK, KPK and promotion handover are subsequent goals. An empty learned graph still
has generic embodiment and learning operators. It does not contain authored
mating/opposition plans, a trained finisher or a correct-action lookup.

Environment observations and teaching signals are distinct. A fixed typed
feature schema is supplied; actual terminals select coordinates/regions from it.
Geometry is allowed. A Boolean, bounded integer and continuous coordinate can
have different domains without making the feature vector variable-length.
The present equality-reader implementation supports only finite Boolean/integer
domains; that is its initial scope, not an architectural ban on other domains.

The coach gives scalar reward after the run and binds it to the submitted action;
it supplies no target move, node identity, stage label or internal-state score.
Current M1: +1 actual mate, -1 failure within one own move. No fabricated geometry
reward or ideal-move label. Learned child value later supplies an internal
prediction/credit signal, not an extra externally supplied success label.

Input/output/internal terminals remain leaves. Shared sensor implementations
are allowed only when equivalent terminal reads retain correct independent
binding/frame/request state. Current action-target geometry describes legal
actuator parameters relative to current pieces; no successor board is evaluated.
Virtual frames, when integrated, must not mint real success evidence or execute
real actuators. Known rules do not establish learned world dynamics.

## Lessons from the history and this conversation

| Mistake or ambiguity | Guiding correction |
| --- | --- |
| A Python board/scorer wrapped in an opaque organism was called sufficient. | Inspect the complete observation-to-action path. Putting an external tactical answer behind a terminal does not fix its provenance. |
| Sparse terminals were mistaken for a requirement to train dense vectors or use only raw squares. | Preserve the allowed typed geometric basis and sparse reader families. Declare every supplied measurement. |
| Individual relevance/maturity blocked synergistic components. | Permit immature components to compose; protect readers needed by useful compositions. Negative value can be useful inhibition. |
| Automatically born nodes were described as learned structural discovery. | Separate birth, learned contributions, experience-guided proposals, survival, reuse and behavioral attribution. |
| An action-producing child was treated as a competent child. | CONFIRMED action selection is not successful goal completion. Learn competence in context through actual outcomes. |
| A material detector or uncalibrated activation sum was treated as general handover. | Learn delegation and parent-relative value. Different goals, branch sizes and exploration signals are not automatically comparable. |
| Fast/slow fields or certificates were taken as proof of consolidation. | Test their behavioral role. Current fast-to-slow transfer preserves effective dynamics; it alone does not prevent forgetting. |
| Frozen baselines or certification rules became prerequisites for ordinary learning. | Young structures must act and learn. Preserve skill and evidence while allowing correction; keep scientific certification distinct from the learner's operational plasticity. |
| Rebirth erased known failures or identical materialization reset evidence. | Preserve applicable experience across identity-preserving transitions. Separate new hypotheses from new storage representations. |
| Passing many protocol tests substituted for actual learning. | Report real actions/outcomes as well as the mechanism tests, without inflating either into general autonomy. |
| New adapters ignored older successful components. | Check and reuse existing mechanisms where compatible; explain concrete reasons for an alternative. July residual-guided composition is an asset, not a new invention. |
| Old “current” docs survived each reset and contradicted new ones. | Maintain explicit entry points, provenance and statuses. Historical records retain evidence without issuing live commands. |

These corrections concern mechanisms and evidence, not blame assigned to a model.
A reviewer should revise any historical attribution that the code does not support.

Before accepting this guidance, reconcile the constitution's older 100%
curriculum thresholds and mature-child M2 credit wording with the current
scalar-outcome coaching contract. Keep scientific confirmation standards
explicit and separate from ordinary learning permission. Learned child value
is an internal mechanism; final real-outcome reward remains the external signal.

## Current implementation and honest evidence

Review target: `e3900df7a9e4167bd4c66a0ed55596e751504a16` on
`codex/mate-in-one-coach`. The current graph learns a weighted combination of
randomly born shallow Boolean conditions. There is no recursive SCRIPT discovery,
learned birth distribution, integrated virtual planning or module handover yet.
The node named `goal` confirms choice; it does not certify that chess was won.

The seed-1 engineering run played 182 moves, observed 99 mates and improved
nonlearning development validation from 4/128 to 124/128. Validation spans 25
symmetry orbits. Final test unopened. There are 96 condition definitions and
3,385 actual vertices across binding instances. No chess pruning occurred before
the 256-exercise grace period. Tests cover pruning separately. The 79 focused
tests support their stated invariants, not an open-ended autonomy conclusion.

Detailed report and source identity are linked from `MATE_ONE_COACH.md`. Keep the
checkpoint private unless Oskar explicitly authorizes its publication; it and
the real-move log were supplied separately after automatic upload review blocked
publication to GitHub. This restriction is about publishing that artifact, not
permission to run ordinary authorized local chess experiments.

## Proposed next work after agreement

1. Freeze an additional budget for longer unchanged M1 training and independent
   seeds. Verify retained behavior when pruning/consolidation actually occur.
2. Separate representation and growth effects with atomic-only and comparable
   fixed-random-representation controls. Do not claim the current random birth
   rule is adaptive just because the full learner scores well.
3. Integrate the smallest useful part of existing residual-based composition
   using real terminal responses. Add recursive composition as a distinct factor.
4. Learn contextual child competence and parent-relative delegation. Test actual
   behavioral effects of disconnecting/shuffling child responses and retain
   independently learned skills while coordination adapts.
5. Demonstrate M1 reuse during real M2 play, including actual opponent replies.
   Expand the curriculum only after reliable disjoint performance and retention.

These are proposed decisions, not permission for an unattended sequence of new
experiments. Routine implementation fixes within an authorized task should not
be stalled by historical blanket approval requirements. Scientific comparisons
need an explicit hypothesis, information boundary, controls, budget and claim
limit. A completed negative run remains recorded; do not silently tune it into
the same supposed confirmation. Viewed validation remains development data and
exposed failures remain available to learn from.

## Concrete mainline promotion plan after cross-check

At the read-only check on 2026-09-06:

- `origin/main`: `2b8642c0d63abe4297b9dcc78fa11a53a2a7881e`.
- Tested candidate: `e3900df7a9e4167bd4c66a0ed55596e751504a16`.
- `main` is the common ancestor: 0 main-only and 516 candidate-only commits.
- Thus promotion currently permits a fast-forward, but adopts the full intervening
  history. It is not merely merging the latest 14-file implementation change.
- No default-branch change or merge has been performed for this review request.

After Oskar brings back the old instance's assessment:

1. Record accepted findings and resolve substantive disagreements. Preserve the
   measured e3900df result; new mechanism changes require their own evidence.
2. Select the official continuation base explicitly. The proposed base is this
   branch, with any agreed corrections, rather than reviving an old TG runner.
3. Refresh both remote heads and inspect the full merge scope and required checks.
   Preserve the old main tip in an archival ref before promotion. If new commits
   diverge, resolve them without overwriting unrelated work; never force-reset main.
4. Consolidate AGENTS.md into one current rule set, mark superseded guidance as
   historical, and change this draft to an accepted continuation record. Preserve
   legitimate safeguards; remove contradictory historical implementation commands.
5. Run the checks relevant to the actual merge diff and repository CI requirements,
   then fast-forward or normally merge as appropriate. A friendly alignment review
   does not substitute for checking the larger merge scope.
6. Make `main` the documented official line once the merge succeeds; retain the
   development branch as provenance. If merge scope needs separate integration,
   document the selected official branch and that specific pending integration.

A new instance must report what changed, why, what actual tests/play established,
what remains unknown and the next bounded decision. It should not restart the
entire historical audit or construct another laboratory around an untested learner.
