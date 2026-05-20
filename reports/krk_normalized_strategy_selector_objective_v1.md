# KRK Normalized Strategy Selector Objective v1

This design defines a non-causal offline objective to replace broad additive support as the next arbitration experiment.

- Objective id: `objective.krk.normalized_contrastive_strategy_selector.v1`
- Causal status: `non_causal_design_only`

## Purpose

Learn strategy/provider ownership from normalized provider-local evidence and explicit label semantics, rather than raw global score or broad additive support.

## Required Input Fields

- `state_id`
- `active_landmark_label`
- `provider_id`
- `skill_id`
- `provider_version`
- `provider_family`
- `provider_maturity`
- `provider_local_rank`
- `normalized_score`
- `source_terms`
- `role_licenses`
- `plan_capsule_context`
- `move_shape_terms`
- `post_move_terms`
- `safety_terms`
- `known_outcome_label`
- `causal_status=non_causal`

## Label Channels

### `selected_playout`

- Meaning: result when current normal arbitration selected this provider/move
- Use: context, not sole target

### `forced_provider`

- Meaning: conversion result when a provider family is forced from the same state
- Use: contrastive candidate ownership signal

### `same_move_provider_compatibility`

- Meaning: whether another provider can support the same move without conflict
- Use: compatibility and guardrail-safety signal

### `heldout_stage7_challenge`

- Meaning: unresolved Stage7 residual family evidence
- Use: evaluation only, never training in v1

## Normalization Policy

- `raw_global_score`: `audit_only_not_selector_target`
- `provider_local_rank`: `required`
- `normalized_score`: `required_if_available`
- `provider_family_maturity_prior`: `allowed_as_feature_not_hidden_router`
- `support_scale`: `not_used_in_training_target`

## Candidate Objectives

### `family_maturity_ranked_logistic`

- Features: `['provider_family', 'provider_maturity', 'provider_local_rank']`
- Blocked from runtime use: `True`

### `normalized_rank_plus_visible_terms`

- Features: `['provider_local_rank', 'normalized_score', 'source_terms', 'move_shape_terms', 'post_move_terms', 'safety_terms']`
- Blocked from runtime use: `True`

### `contrastive_owner_pairwise`

- Features: `['same_state_provider_pair', 'forced_provider_conversion_delta', 'provider_family', 'provider_maturity', 'provider_local_rank_delta']`
- Blocked from runtime use: `True`

## Evaluation Protocol

Splits:
- `protected_stage_family_holdout`
- `leave_provider_family_out_if_feasible`
- `stage7_challenge_holdout`

Metrics:
- `positive_owner_top1`
- `positive_owner_top3`
- `protected_negative_suppression`
- `stage7_challenge_no_training_leakage`
- `selected_stage0_dominance_reduction_offline`
- `guardrail_label_no_regression_proxy`

Minimum before runtime review:
- `beats provider_family_maturity_prior on heldout protected rows`
- `does not train on Stage7 challenge rows`
- `can explain selected ownership with visible source terms`
- `keeps label channels separate in artifacts`

## Forbidden Uses

- `runtime selector`
- `runtime provider support`
- `score bonus or provider penalty`
- `Stage7 repair`
- `Stage7 promotion`
- `Stage8 training`
- `runtime DTM/tablebase`
- `gameplay topology mutation`
- `hidden Python controller`

## Decision

- Status: `normalized_selector_objective_design_ready_for_offline_probe`
- Recommended next step: `run_offline_normalized_selector_objective_probe_v1`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
