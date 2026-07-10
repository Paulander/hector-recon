# Native From-Scratch KRK Curriculum Plan

Date: 2026-07-10

Status: CENTRAL execution plan for the next KRK work package.

## Scientific target

Demonstrate one self-growing ReCoN ecology that starts with no learned KRK
topology or values and learns a complete KRK policy through its own world
outcomes, graph-local plasticity, and recursively grounded child competence.

This is the core result. Dreaming, longer virtual-frame search, surprise, and
other cognitive mechanisms are valuable follow-on mechanisms, but they are not
allowed to obscure whether the basic end-to-end learning chain works.

## What "empty graph" means

A literally node-free graph cannot sense a board, select a move, or observe an
outcome. The experiment therefore starts with an **empty learned graph** and a
minimal task-generic genome:

- generic board/transition feature terminals;
- legal-action enumeration and action execution;
- observable checkmate, stalemate, illegal transition, rook loss/capture, loss,
  draw, and time-step facts;
- the ReCoN request/confirmation protocol;
- content-blind stem-cell spawning, M3 plasticity, M4 consolidation, and pruning.

Initialization must contain no KRK rule, mating pattern, action triplet, geometry
skill, stage switch, learned weight, restored TG artifact, tablebase/DTM value, or
competence value. The artifact records node/edge hashes before the first episode.

## Audit of existing ingredients

- TG46b is fresh learned state on generated real boards, but it calls
  `_mate_moves`, `_forced_mate_in_two_first_moves`, and `train_position(...,
  positive_moves=...)`. It is supervised foundation evidence, not the target.
- TG26p grows real SCRIPT/TERMINAL nodes and SUB/SUR/POR/RET edges and uses
  `FormalReConEngine` for choice. Its trainer still constructs per-action rewards
  with `_mate_moves`, `_forced_mate_in_two_first_moves`, and `_move_reward`; its
  default evaluation also uses its curriculum positions.
- `IntrinsicCreditEngine` now supplies outcome-grounded child value, eligibility,
  depth-decayed parent credit, metabolic cost, cycle protection, and causal
  maturation. The missing work is a clean integration runner and strict pools,
  not another reward theory.

## Immediate bounded experiment: R0 -> R1

### 0. Freeze the contract before the long run

Implement a new runner; do not mutate or relabel TG46/TG26 history. Freeze seeds,
configuration, train/validation/regression/final manifests, hashes, gates, and
controls before execution. Existing v1 FINAL rows remain untouched.

Required runtime tripwires:

- zero learned cells/edges/values at episode zero;
- one graph UUID and monotonically continuous lifecycle counters across rungs;
- every White move selected by native graph confirmation, with no Python fallback
  selector or move provider;
- reward audit contains only observed world terminal, real/virtual time cost, and
  eligible mature-child value;
- training must fail closed if mate/forced-move/geometry/stage labels enter a
  learner record or reward channel;
- snapshot/resume produces deterministic parity on a fixed probe.

### 1. R0 -- Mate-in-1 from real consequences

Schedule diverse legal White-to-move Mate-in-1 positions, but never tell the
learner which move mates. ReCoN proposes/explores a legal action, the chess world
executes it, and the graph observes whether checkmate actually occurred. A
non-mating action gets no fabricated negative label; it gets its real continuation
or terminal result and the ordinary move cost.

Alternate bounded structural epochs with topology-frozen M3 training. Consolidate
only after a fresh confirmation split passes. Continue training until the fixed,
disjoint validation set reaches 100%, then require 100% on a separate regression
set with zero illegal moves, stalemates, and rook losses. Repeat across five seeds;
do not inspect FINAL until configuration freeze.

Expected interpretation: R0 should be the easy sanity gate. Failure means native
exploration, action representation, credit locality, or structural growth is
insufficient; do not proceed outward by adding a mating teacher.

### 2. R1 -- Mate-in-2 by mature-child handoff

Continue from the exact consolidated R0 graph. Schedule Mate-in-2 positions, but
do not expose mate distance or forced first moves. After ReCoN's first move and a
Black reply, query normal graph request/confirmation. If mature R0 recognizes the
successor as inside its competence basin, it emits its consolidated expected
value; that value, discounted and minus move cost, is the upstream signal.

Training must expose reply diversity, including every legal reply often enough
that a first move which succeeds against only one reply cannot dominate. This is
bounded local experience at the adjacent rung, not exhaustive KRK enumeration or
a retrograde move oracle. Heldout evaluation is stricter: the selected first move
must hand off successfully under every legal reply.

R1 advances only with:

- 100% disjoint all-reply Mate-in-2 validation and regression;
- 100% retained R0 validation/regression;
- zero protected safety regressions;
- the configured move-efficiency bound;
- a positive paired effect versus no-bootstrap and child-value ablation;
- actual promoted topology/weights whose enable/disable intervention changes
  heldout decisions, not merely counters.

Controls use identical pools, order, seeds, tie-breaks, and starting snapshot:
full intrinsic chain, no-bootstrap, mature-child ablation, topology frozen, and
yoked random/content-blind candidate growth.

Expected interpretation: if full passes and the causal controls do not, the
central chaining hypothesis is established at its first nontrivial step. If all
arms pass, the pool is too easy or another channel leaks the answer. If none pass,
inspect exploration, competence availability, reply aggregation, eligibility,
and consolidation before changing the curriculum.

## Continue outward only after R0/R1 certification

Keep the same graph and repeat the same protocol at finer rungs:

1. R2: opponent king trapped at an edge, fence present, White king close;
2. R3: opponent king on the same side as the rook; learn the tempo/handover move;
3. R4: edge trapped with White king progressively farther away;
4. R5: edge drive with an established safe fence;
5. R6: establish and retain the safe fence;
6. R7: broad legal nonterminal White-to-move KRK.

Each new training distribution begins just outside the mature child's confirmed
competence basin but within a short reachable boundary. Real entry into that
basin supplies the intrinsic signal. Add replay from every mastered rung,
consolidate before structural mutation resumes, and never skip directly to broad
KRK because a narrow rung looks conceptually obvious.

## When to add dreaming and imagination

First make R0 -> R1 work using real played transitions. Then add one-ply virtual
frames as a preregistered arm using the same graph interfaces and a computation
tax. Virtual frames may query children and accelerate exploration, but cannot
create terminal grounding or alter the evaluation gate. Surprise is the delta
between predicted child/world value and the realized transition; it becomes a
candidate-generation or attention signal, not a substitute reward.

Longer gnome-gap search is a later rung-specific intervention only if real local
handoffs stop spanning the gap. This ordering makes the core autonomy claim
independent of a search implementation.

## Desired claim if the ladder succeeds

The defensible result is not merely that ReCoN contains useful KRK patterns. It is
that a minimally embodied, initially untrained ReCoN ecology grows and
consolidates hierarchical competences, uses mature child value to train parent
behavior, retains earlier skills, and solves heldout KRK without solution labels
or a runtime move oracle. That is the publishable core; cognitive extensions can
then be evaluated as acceleration and transfer mechanisms.
