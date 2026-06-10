# Stage 7 Post-Box-Shrink Continuation Diagnosis

Schema: `stage7_post_box_continuation_diagnosis.v1`
Causal status: `non_causal`
Stage 7 status: `local_valid_composition_quarantined`
Records: `25`
Conversion failures: `6`
Unique failed post-reply states: `2`

## Buckets

- `box_shrink_visible_confirmed_mate`: 2
- `box_shrink_visible_confirmed_max_plies`: 5
- `reward_confirmed_no_visible_shrink_mate`: 17
- `reward_confirmed_no_visible_shrink_max_plies`: 1

## Candidate Updates

### cand.krk.box_shrink.handoff_role_refinement.v1

- Status: `needs_bounded_forced_provider_probe`
- Role: `krk.post_box_shrink_continuation`
- Next action: `run_targeted_forced_provider_probe_on_unique_failed_post_reply_states`
- Diagnosis labels: `post_box_shrink_continuation_gap`, `reward_contract_mismatch_remaining`, `topology_present_untrained_or_miscalibrated`

### cand.krk.box_shrink.overlay_quarantine_confirmed.v1

- Status: `local_valid_composition_quarantined`
- Role: `krk.box_shrink`
- Next action: `do_not_promote_stage7_until_continuation_probe_or_repair_passes_guardrails`
- Diagnosis labels: `local_valid_composition_quarantined`

## Recommended Next Action

`targeted_forced_provider_probe_before_new_topology`

Do not promote Stage 7 or train Stage 8 from this artifact. This is a
non-causal diagnosis artifact for the next bounded forced-provider/M3 probe.
