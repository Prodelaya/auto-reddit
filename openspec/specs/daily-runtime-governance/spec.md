# daily-runtime-governance Specification

## Purpose

Define the single operational truth for when the daily runtime executes and which review window it applies.

## Requirements

### Requirement: Execute the scheduled daily pipeline only on weekdays

The system MUST execute the scheduled daily pipeline only from Monday through Friday. A scheduled run started on Saturday or Sunday MUST exit before collection, evaluation, or delivery side effects, and the operational documentation MUST describe the same weekday boundary.

#### Scenario: Weekday run proceeds normally

- GIVEN the scheduler starts the daily runtime on a Wednesday
- WHEN the runtime evaluates whether to run
- THEN the pipeline continues into its normal daily flow

#### Scenario: Weekend run is skipped cleanly

- GIVEN the scheduler starts the daily runtime on a Sunday
- WHEN the runtime evaluates whether to run
- THEN the pipeline stops before collection, evaluation, and delivery side effects

### Requirement: Govern the active review window from `review_window_days`

The system MUST use `review_window_days` as the effective runtime boundary for which candidates remain reviewable in the daily run, and the documentation MUST identify the same setting as the governing window.

#### Scenario: Shorter configured window excludes older candidates

- GIVEN `review_window_days` is 3 and a candidate is 4 days old at run time
- WHEN the daily run computes the active review set
- THEN that candidate is outside the review window

#### Scenario: Larger configured window includes still-valid candidates

- GIVEN `review_window_days` is 5 and a candidate is 4 days old at run time
- WHEN the daily run computes the active review set
- THEN that candidate remains inside the review window
