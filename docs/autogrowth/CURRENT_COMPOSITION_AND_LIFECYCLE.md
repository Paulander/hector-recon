# Composition and lifecycle in the current fresh owner learner

Inspected 2026-09-15. These distinctions apply to the active FreshOwnerDevelopment
path, not every historical class in this repository. No mechanism changes are
made by this inspection or by the four-versus-eight-owner experiment.

| Mechanism | Formal engine / representation | Current automatic learner |
| --- | --- | --- |
| AND, OR | Nested Boolean child confirmations | Scoring proposals over one to three raw equality readers |
| XOR | Exactly one child confirms; binary XOR is ordinary XOR | Present in the shallow scoring proposal grammar |
| NOT | Binary exactly-one of TRUE and a child | Available in recursive expressions, including route complements |
| k-of-n / quorum | At least k children confirm | Not accepted by the current Expression grammar or birth generator |
| Recursive ownership | A child owner can split again, inheriting independent scoring weights | Active, subject to local evidence and allocation/depth limits |
| Reusing learned compounds | Immutable recursive definitions can be instantiated in several places | New scoring compounds are not automatically added to the frozen route pool or used as arbitrary birth subgraphs |
| TRIAL to MATURE | Historical stem-cell lifecycle code exists | No active promotion path in this learner |
| Retirement | Structures can be removed from live scoring while retaining history | Non-bias conditions are eligible after256 local visits with absolute effective weight below .02, checked at local development opportunities |

## XOR between subgraphs

Yes: a Boolean composition's child may itself have a Boolean child graph. A
parent consumes the child's settled Boolean confirmation, not its number of
descendants. Assuming `+` means OR, one possible explicit grouping of the user's
example is `a = b ^ ((c ^ d) | (e | !f))`. The particular intended grouping matters;
the general ability to nest XOR/OR/NOT is supported. Each named child may be a
predicate subgraph, provided the complete expression fits the configured depth
and execution budgets. The current compiler has depth-four bounds; it does not
promise arbitrary-length chains.

Binary XORs must remain nested to obtain parity over several inputs: a single
three-child `xor` node means exactly one, and fails when all three confirm.
A weighted scorer's numerical activation is not automatically a Boolean
predicate; combining scorers requires specifying the Boolean result being used.

An executing SCRIPT instance has one owning parent. Reusable immutable
definitions are compiled into separate execution instances under different
parents, so mutable request/confirmation state does not leak between uses.
Input terminals are leaves. This permits hierarchical expression execution;
it does not establish automatic discovery of the hierarchy.

Fresh owner route candidates are sampled once from state-coordinate equality
tests and eligible state-only source definitions of depth at most two. The
fresh source contains only a TRUE bias, which is not an eligible route. Thus
the present four-state-bit task starts with eight atomic state tests. The
24 scoring-birth candidates are a separate fixed shallow pool. Newly learned
compound conditions do not automatically become route candidates or building
blocks for arbitrary deeper scoring proposals.

## What currently develops

Actual outcome credit updates the active owner's participating scoring weights
on every training action. Every64 visits to that owner, the current law checks
retirement and then supported residual-based splitting. A successful split
replaces the ordinary scoring-birth opportunity. Its children inherit effective
weights in independent parameter objects and start their own visit/evidence
counts; ancestor histories remain available. New scoring conditions start with
zero weight and can immediately participate and learn.

The unit that splits is the whole local decision owner. It is not an arbitrary
individual scoring condition waiting to become mature. Child owners can split
without a maturity test; a cap on live owners and other resource budgets may
prevent them. This is recursive specialization already, with restricted route
discovery and finite opportunity/exposure budgets.

The Condition state defaults to TRIAL. The active path does not call the older
stem-cell promotion machinery. Existing fast-to-slow weight transfer preserves
the effective sum and is not a demonstrated maturity or retention controller.
Age-plus-small-weight retirement is a heuristic, not proof that a condition is
causally useless. Therefore 'trials become permanent after a while' would be an
incorrect description of these current runs.

A future maturity mechanism should distinguish durable definitions, ongoing
weight learning, permission to compose/specialize, and retirement eligibility.
Simply surviving for a long time does not establish usefulness, and requiring
every subpart to prove individual utility can block jointly useful compositions.
Any future eligibility/promotion mechanism must use local available evidence,
preserve ancestry and allow reconsideration; offline diagnostic answers must
not choose the structures. No such new mechanism is installed here.

Code: `libs/recon-lite/src/recon_lite/formal_engine.py` for settled quorum/XOR;
`src/recon_lite_hector/learning/recursive_context.py` for recursive Expression
and compilation; `context_decision.py` for whole-owner cloning and limits;
`owner_development.py` for frozen routes, visits and retirement;
`owner_birth_search.py` for the fixed scoring candidate pool;
`fresh_owner.py` for zero-training initialization;
`terminal_development.py` for Condition state and ordinary credit.
