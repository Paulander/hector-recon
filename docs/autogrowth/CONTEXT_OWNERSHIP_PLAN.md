# Context-owned decisions: plan and checkpoints

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
