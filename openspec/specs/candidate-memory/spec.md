# candidate-memory Specification

## Purpose

Definir la memoria operativa minima y la unicidad por post para el slice diario posterior a la coleccion, sin introducir backlog editorial ni estados de negocio adicionales.

## Requirements

### Requirement: Exclude final decisions before daily review

The system MUST exclude any post already persisted as `sent` or `rejected` before daily review, MUST sort the remaining eligible posts by `created_at` descending, and MUST pass only the first 8 posts to downstream review.

#### Scenario: Filter and cut the eligible set

- GIVEN a daily candidate set containing posts already marked as `sent`, `rejected`, and still undecided posts
- WHEN the daily review set is prepared
- THEN only undecided posts remain eligible
- AND only the 8 most recent eligible posts are passed downstream

#### Scenario: Allow a skipped post to compete tomorrow

- GIVEN an eligible post was not inside today's top 8 and remains within the 7-day window
- WHEN the next daily run starts
- THEN the post is eligible again unless it has since become `sent` or `rejected`

### Requirement: Persist only the minimal state model

The system MUST use `sent` and `rejected` as the only final business decisions, MUST keep any pre-send persistence distinct from those final decisions, and MUST NOT persist an `approved` state, an explicit editorial backlog, or `not selected today`.

#### Scenario: Keep non-selected posts out of persistence

- GIVEN an eligible post is not chosen in one daily execution
- WHEN the execution finishes without a final decision for that post
- THEN no persistent state such as `approved`, backlog entry, or `not selected today` is created

### Requirement: Final AI rejection closes the post

The system MUST persist `rejected` when the AI determines the post is not a valid business opportunity, and a `rejected` post MUST NOT re-enter later daily runs.

#### Scenario: Close a post as rejected

- GIVEN an eligible post is evaluated by AI and the result is a final rejection
- WHEN the evaluation result is stored
- THEN the post is persisted as `rejected`
- AND future daily runs exclude that post before review

### Requirement: Preserve accepted opportunities for delivery retry

When AI accepts a post, the system MUST persist the structured evaluation output as the retry source of truth in `opportunity_data`, SHALL keep that pre-send record distinct from `sent`, and MUST reuse the persisted structured result for downstream deterministic rendering and Telegram retries without re-evaluating AI.

#### Scenario: Reuse persisted structured evaluation on retry

- GIVEN a post was accepted and its structured evaluation was persisted in `opportunity_data`
- WHEN a later delivery retry is attempted
- THEN downstream rendering uses that persisted structured evaluation
- AND no new AI evaluation is triggered

### Requirement: Mark sent only after successful Telegram delivery

The system MUST persist `sent` only after Telegram confirms successful delivery, and MUST NOT mark a post as `sent` or convert it to `rejected` solely because delivery failed.

#### Scenario: Close a post only on delivery success

- GIVEN a post has been accepted by AI and is pending Telegram delivery
- WHEN Telegram confirms successful delivery
- THEN the post is persisted as `sent`

#### Scenario: Keep pre-send state after delivery failure

- GIVEN a post has been accepted by AI and Telegram delivery fails
- WHEN the failed attempt is recorded
- THEN the post remains only in the distinct pre-send operational persistence
- AND it is not marked as `sent`
