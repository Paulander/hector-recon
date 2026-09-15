# Recorder correction after a stopped attempt

The first 2026-09-12 attempt at `4afc34a4` stopped after 30.514 seconds, at the
block-completion guard. No timeout or memory exhaustion occurred (peak33.13MiB).
Its final status remains incomplete; it is never resumed or counted as a full
replication. All original files and exact source dependencies are preserved.

Nine deleted `actions.partial.jsonl` names reappeared as shorter, exact prefixes
of their corresponding sealed journals, with different inodes. The cause of
the reappearance is unknown. All twelve sealed blocks still match every payload
hash: 1536 training actions, 176 scheduled evaluation actions, fifteen checkpoints.
A separate read-only audit restored them and reproduced all eleven evaluations
(176 additional frozen actions). No action record was missing or reconstructed.
The audit retained the unexpected files; it verified copied manifest-listed
payloads without treating the extra prefixes as independent evidence.

The broad current instruction is to carry out the next test with resource checks.
After inspecting the failure, one corrective attempt is prepared with the exact
same seeds, schedules, learner, budgets and reporting criteria. This is a recorder
repair, not a score-selected restart; earlier outcomes are retained as development
observations. The stopped attempt stays closed. There is no retry loop, automatic
resume, parameter tuning, or further training attempt if this correction fails.

The correction supersedes only the original protocol's journal sealing detail:

- Keep each block's growing `progress.jsonl` permanently as a crash breadcrumb.
- Collect the actual recorded outcome rows in a bounded in-memory block buffer;
  after 128 actions, write them once to a separate `training.jsonl` with exclusive
  creation. Do not hard-link, rename or delete either file.
- The exclusive completion manifest hashes the complete training journal,
  checkpoint, intent and evaluation. Completeness depends on those payloads.
  A stale progress prefix is redundant; contradictory progress content is rejected.
- Also permit restoring the legitimate empty initial actor before it has bound
  action options; formal execution validation still applies after schema binding.

Focused tests include stale progress prefixes, contradictory content, interrupted
blocks, missing sealed records and the empty start. A file-only multi-block probe
checks the new write-once path across tool boundaries before the corrected run.
The corrected run retains the original one-core, 2-GiB and ten-minute total cap.
Its scientific results will explicitly distinguish the stopped attempt.
