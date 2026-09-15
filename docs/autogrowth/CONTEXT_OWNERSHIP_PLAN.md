# Context-owned decisions: plan and checkpoints

Latest status: [OWNER_TRIAL_LEARNING_STATUS.md](OWNER_TRIAL_LEARNING_STATUS.md).
The revision is implemented and tested, but its execution session disappeared
mid-study. Seed21 current/trial completed16/11; revised13 at its1,536 checkpoint,
plus39 credited actions without a checkpoint. Seeds22/23 never started. The first
early-negative split later earned acceptance, supporting the timing concern;
final superiority is unresolved. All surviving evidence is audited and archived.
No retry/extension or main merge under the predeclared one-attempt protocol.

Authorized next increment, 2026-09-15: [OWNER_TRIAL_LEARNING.md](OWNER_TRIAL_LEARNING.md).
Give the same live candidate an exposure-based learning phase before prospective
assessment, with one preallocated second review. Preserve the current and first
trial controls. Fresh seeds 21/22/23, three arms, 1,920 actions each; source and
protocol must be pinned before play. This is a combined lifecycle revision, with
no threshold tuning, retired-hypothesis revival, external coach or main merge.

Latest integration checkpoint,2026-09-15: [OWNER_SPLIT_TRIAL_RESULTS.md](OWNER_SPLIT_TRIAL_RESULTS.md).
The user authorized combining owner splits with existing trial-use/lifecycle
machinery. The fixed seeds18/19/20 comparison completed and lost all three pairs:
current16/14/14 versus trial12/12/12. Keep the current four-owner reference.
The new trial law and its earlier-birth schedule are an explicit combined
intervention; no maturation-benefit claim. Next investigate finite assessment,
rare-child exposure and history-preserving reconsideration before another run.
The cohort is CLOSED, private work-branch publication authorized, main unchanged.

Started 2026-09-14 on `codex/context-owned-decisions`, from `1212bdc4`.
User authorized a short plan and starting the separate restructuring prototype.
No publication or restart of an earlier experiment is implied.

## Question and assumptions

Does giving each contextual decision ownership of all its competing scoring
parameters reduce interference while preserving acquisition? Existing contributor
splits remain the control. Local freezing is a separate, not-yet-defined arm.

- Generic runtime code may implement the operation; terminal observations and
  actual action-bound scalar feedback remain the only environmental inputs.
- Boolean routing must be invariant across legal action bindings. A declaration
  of which coordinates are state measurements is an embodiment contract, not a
  supplied task/context label. Names and particular coordinate numbers do not
  determine the growth rule. Existing ports lack scope metadata; initially the
  mechanical fixture declares allowed coordinates explicitly. A runtime check
  rejects disagreeing routes across current bindings before executing an action.
- A split clones the complete local scorer, including bias, with independent
  parameter objects. It shares immutable expression definitions, never mutable
  SCRIPT request state. Each execution SCRIPT retains one parent.
- Score inheritance is mathematical; floating-point comparisons allow 1e-12.
  Branch-specific observation counts start empty; parent evidence remains as
  ancestry, never fabricated observations of the new branches.
- Isolation initially assumes fixed Boolean definitions/routing and fixed owned
  topology between explicit splits. It does not prove retention under learned
  routing, shared representation drift, later pruning or repeated restructuring.
- This first compiler gates each contribution within its owned context using
  existing formal SCRIPTs. It does not yet factor every common subexpression
  into one physical execution node, or learn a higher-level goal hierarchy.

## Checkpoints

1. **Ownership primitive.** Convert an existing scorer on a clone; preserve all
   scores, actual graph choice and source state. Split a whole local scorer,
   including nested splits, without sharing sibling parameters. Reject invalid
   or over-budget changes atomically. No automatic nomination in this checkpoint.
2. **Mechanical evidence.** Exhaustive small Boolean fixtures check scores,
   terminals, action renaming, inactive-context scores after actual feedback,
   active-context learning, ancestry, serialization and resumed continuation.
   Planted gates isolate the operation; they are not self-organized discoveries.
   Existing recursive/core focused tests remain controls. One CPU, numerical
   libraries one thread, 2 GiB address space, 180-second per-invocation wall limit
   with an independent hard stop. Large legacy checks can be split into bounded
   file batches. No training benchmark launched by this stage.
3. **Experience-driven development.** Specify and implement nomination from the
   owner's actual residual evidence; candidates use declared state measurements
   and reusable definitions. Specify preservation of applicable evidence and
   context-local growth/pruning. No offline repair or winning branch injection.
4. **Protection arm.** Specify what can freeze, a local evidence trigger and
   reopening rule before outcomes. Do not combine freezing and restructuring
   into one arm or call an analyst-selected freeze autonomous protection.
5. **Bounded comparison.** Predeclare seed cohort, common prefixes, A/B/A exercise
   schedule, action/memory/compute budgets and evaluation milestones. Compare
   ordinary contributor splitting, protection and context ownership. Match total
   parameter ceilings and disclose realized costs; whole-scorer forks cost more
   than single-contributor splits. Keep independent exploration RNG streams,
   immutable action journals, checkpoint verification and sufficient post-split
   learning. No automatic retries or extensions based on intermediate scores.

Primary comparisons: acquisition, row-level loss/recovery trajectories and worst
measured retention, alongside final score, parameters, shared definitions, physical
nodes and runtime. The 16-row Boolean environment is development evidence, not
general chess or broad retention. Exact factoring/duplicate-credit changes are
separate interventions. Mac results currently remain user-reported pending ZIP
inspection; they support retaining the ordinary learner as a credible control.

Stop or revise if score inheritance/isolation fails, runtime boundaries change,
or the cost of ownership exhausts the declared budget. A pass advances the next
engineering checkpoint; it is not evidence that the new learner performs better.

## First implementation checkpoint

Implemented `learning/context_decision.py` as an isolated subclass/compiler;
the original recursive learner, credit implementation and formal engine files
remain unchanged. Conversion clones the source, converts bias into an explicit
owned contribution and keeps the legacy global bias fixed at zero. Consequently
normalization is eta*(reward-prediction)/N with N including the owned bias: the
same original eta*(reward-prediction)/(1+k). Only the selected owner's confirmed
contributions receive outcome updates. Its own bias retains the existing neutral
fast/slow transfer. Automatic pruning/birth are deliberately absent in this
mechanical checkpoint; this is not a candidate for the full learning benchmark yet.

Fifteen new mechanical cases pass, including nested routes, depth-four formal
execution, full score preservation across the fixture domain, inactive-owner
parameter/statistic isolation through both competing actions' real feedback,
action renaming/binding expansion, independent checkpoint continuation, credit
normalization, invalid feedback, alias detection and atomic rejection of limits.
With direct existing controls, 58 tests pass in 56.99 seconds; peak RSS 69132 KiB.
The fixtures plant the gate and initial scorer; their passing scores are not
evidence of discovering a task or selecting the right restructuring autonomously.

The cost fixture contains three ordinary contributions plus bias:

| State | Owners | Effective parameters | Expression definitions retained | Physical nodes |
| --- | ---: | ---: | ---: | ---: |
| Original | 1 | 4 | 5 | 27 |
| Converted | 1 | 4 | 6 | 31 |
| One decision split | 2 | 8 | 16 | 67 |
| One child split again | 3 | 12 | 27 | 109 |

Each effective parameter has fast and slow storage. The old fixed-zero bias is
execution overhead, not another learned parameter. Definition counts include
retained identities. This is ownership isolation with additional cost, not graph
compression, semantic deduplication or one physically shared common trunk.

Next: checkpoint 3. Candidate nomination must be driven by the owner's actual
experience. Routing scope, inheritance of applicable nomination evidence and
local lifecycle rules require explicit implementation before a comparative run.

Verification note: a first broad legacy-test invocation used `pytest.main` from
standard input, which is incompatible with those tests' multiprocessing-spawn
entrypoint, and reached the 175-second worker alarm before completion. A later
oversized legacy batch also reached that alarm, without a reported assertion
failure before the stop. Neither is counted as a completed suite. Subsequent
checks use an importable file entrypoint and smaller fixed file groups under the
same limits. These are test-launch corrections, not changes to the learner or
retries of a training experiment. Use a file entrypoint or `python -m pytest`
when reproducing multiprocessing tests; keep the independent guard enabled.

Final verification: **256 distinct tests passed**, including all 15 new ownership
cases and the complete required AGENTS.md suite. Completed batches contain
58/22/30/53/93 disjoint cases, taking 56.99/22.26/85.31/172.24/58.39 seconds.
Peak individual test-process RSS was 84516 KiB; this is not aggregate child-process
RSS. All batches shared one CPU affinity and inherited a 2 GiB per-process address
space limit; each had a 175-second worker alarm and independent 180-second guard.
The compatibility tests intentionally create bounded subprocesses to check their
existing parallel runners. No task remains running. The machine-readable result,
source hashes and explicit limits are in
`reports/autogrowth/development/CONTEXT_OWNERSHIP_CHECKPOINT_20260914.json`.

## Recovered status, 2026-09-15

The original checkpoint sequence above is preserved as history. Current position:

| Step | Status and evidence |
| --- | --- |
| Whole-decision ownership and isolation | Implemented; 256 original focused checks passed. |
| Experience-driven owner nomination | Implemented; short pilot exposed insufficient action distinctions and local exposure. |
| Longer exposure before changing mechanisms | Fivefold run complete; split and unsplit total25/32 each, with mixed acquisition and selective endpoint retention. |
| Context-compatible births | Complete; nine impossible births prevented,96 physical nodes saved, identical observed trajectories. |
| Useful nomination versus opportunity scheduling | Current fixed factorial pilot; see OWNER_BIRTH_SEARCH.md. No outcome is claimed here. |
| Local protection/freezing/reopening | Not implemented; still a separate mechanism and later comparison. |
| Strong-skill retention benchmark | Still required; weak prefixes cannot establish broad retention. |
| Shared execution factoring and duplicate-credit handling | Separate later interventions; neither follows automatically from compatibility. |

The user's September15 instruction authorizes remote publication of this private
work branch, superseding older no-publication notes for this branch. Main remains
the stable baseline; promotion must distinguish importing experimental modules
from making their behavior the default. The branch contains a much larger chain
of experiments than the compatibility increment alone.

Latest update: the four-arm pilot is now complete; see
[OWNER_BIRTH_SEARCH_RESULTS.md](OWNER_BIRTH_SEARCH_RESULTS.md). Residual/current
finishes14/16 and16/16 versus13/16 and16/16 for the matched random control, with
faster seed11 acquisition and fewer final nodes. It still loses learned B rows
in seed10. Extra birth opportunities show no consistent advantage. Next define
a fresh-seed replication and a strong-prefix retention comparison; protection,
freezing/reopening and factoring remain separate. No additional run is started.

Latest user-directed continuation,2026-09-15: the user explicitly requested fresh
networks from the beginning and reiterated local, self-contained development
without external macro/network guidance. The fixed three-seed comparison is now
complete; see [OWNER_FRESH_START_RESULTS.md](OWNER_FRESH_START_RESULTS.md).
Zero-training random/current scores15/12/14 versus ranked/current14/14/16.
Ranked seed14 reaches16 at768 and retains it at later checks; seed12's additional
B loss remains. All180 blocks and186 checkpoints verify, with52 focused tests
passing. Starting ownership from zero differs from the earlier learned-prefix
conversion. Existing early splits delay first ordinary features until439–443
actions; delayed/coarse splitting remains a later, separate experiment at the
user's direction. No new timing, freeze, merge or task-oracle mechanism is added.
The fresh cohort is closed. Keep the random control and treat ranking as an
experimental option; a separately defined strong-skill retention comparison is
still outstanding. The recovered architecture plan above remains the plan.

Latest user-directed continuation,2026-09-15: the fixed fresh four/eight-owner
comparison is complete; see [OWNER_HEADROOM_RESULTS.md](OWNER_HEADROOM_RESULTS.md).
Only the owner ceiling changed. Final scores14/13/15 versus13/16/14 show mixed
benefit, delayed scoring births and less child exposure at the same global budget.
Exact endpoint checks distinguish missing capacity in three graphs from wrong
learned weights in two others. All180 blocks and186 checkpoints verify;23
focused checks pass,81 sources match and79 previous runtime sources are unchanged.
The cohort is closed. Current maturity is unimplemented, and compound definitions
are not automatically promoted into the frozen route pool or unrestricted birth
composition. Engine k-of-n and nested Boolean execution do not imply those
learning mechanisms; the exact distinctions are in CURRENT_COMPOSITION_AND_LIFECYCLE.md.
Keep the four-owner reference; do not automatically add mechanisms or start
another run. Main remains unchanged; private work-branch publication is authorized.
