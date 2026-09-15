# Mac Mini: independent recursive split-budget replication

Paste the prompt below into the local coding agent after extracting
`HECTOR_SPLIT_BUDGET_MAC_20260914.zip`. The bundle includes the exact required
source files, protocol and tests; it does not require an unpublished Git branch.

## Prompt

Work in the extracted HECTOR_SPLIT_BUDGET_MAC_20260914 directory. Read README.md,
docs/autogrowth/RECURSIVE_SPLIT_BUDGET.md and MAC_AGENT_INSTRUCTIONS.md first.

Run the declared independent replication on fresh seeds 7, 8 and 9. The cloud
is testing saved seeds 4, 5 and 6. Use the supplied runner unchanged: build each
fresh guided actor through 1024 actions, then fork it into cumulative split caps
6 and 12 for 768 more actions per arm. Do not select actors by their scores.

First check Python 3.12, available memory/disk, dependencies, source hashes and
the 20 focused tests. Use an isolated virtual environment and one worker with
one numeric-library thread. Run through the independent 620-second supervisor,
with the worker's 600-second budget and sampled 2 GiB RSS limit. Do not launch
unbounded training, use a GPU, install Torch, tune settings, import another
branch, or add candidate/weight advice from offline analysis. No Git publication.

Run all seeds/arms once. If training, logging, verification or the guard fails,
preserve every file and report the failure; do not automatically retry or resume.
On success, run the separate bounded frozen verification. It must confirm 7680
training records, 912 scheduled evaluation actions, 60 blocks and 75 checkpoints;
the verification adds 912 frozen evaluation actions and zero training actions.

Report per-seed starting, middle and final A/B scores for both split caps, exact
gained/lost row identities, newly learned B successes retained on returning to A,
and whether initially solved rows ever fail at the scheduled measurements. Include
actual split counts, depth, definitions, physical nodes, elapsed time, peak RSS,
Python/dependency versions and verification results. Keep fresh-seed replication
separate from the cloud's selected-actor comparison. Do not claim general retention
or chess mastery from sixteen development rows. Archive the complete output,
including source snapshots, logs and checkpoints, so I can return it to the cloud
agent for comparison. Finish with a concise results summary and the archive path.

## Commands supplied in the bundle README

No repo-wide installation is needed. Its legacy dependency list includes Torch,
which this experiment never uses. The bundle is a source snapshot for this finite
experiment, not a full checkout or a new production ReCoN release.
