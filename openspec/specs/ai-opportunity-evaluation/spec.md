# ai-opportunity-evaluation Specification

## Purpose

Definir la evaluacion IA de cada `ThreadContext` normalizado para decidir si existe una oportunidad valida y producir una salida estructurada para revision humana, manteniendo fuera el delivery y cualquier autopublicacion.

## Requirements

### Requirement: Evaluate only normalized upstream thread context

The system MUST evaluate only `ThreadContext` items received from upstream extraction, MUST treat that normalized context as the complete input for this change, and MUST NOT fetch additional Reddit data or perform delivery/publication actions.

#### Scenario: Evaluate the upstream handoff only

- GIVEN the upstream batch contains normalized `ThreadContext` items
- WHEN AI opportunity evaluation starts
- THEN only those items are evaluated
- AND no extra Reddit fetch or publish action is triggered

### Requirement: Return bounded structured review output

The system MUST return a binary evaluation outcome of accepted or rejected. Accepted results MUST include structured review fields for `title`, `link`, `post_language`, `opportunity_type`, `post_summary_es`, `comment_summary_es`, `suggested_response_es`, and `suggested_response_en`. Rejected results MUST include a distinct `rejection_type`. The output MUST support later deterministic rendering and MUST NOT be a final Telegram-formatted message.

#### Scenario: Accept a valid opportunity with review data

- GIVEN a `ThreadContext` shows a valid Odoo opportunity
- WHEN the evaluation accepts the post
- THEN the result contains the required accepted structured fields
- AND the result is suitable for human review rather than direct Telegram delivery

#### Scenario: Reject a non-opportunity with explicit reason class

- GIVEN a `ThreadContext` does not qualify as an opportunity
- WHEN the evaluation rejects the post
- THEN the result is marked as rejected
- AND a distinct `rejection_type` is included

### Requirement: Apply context-quality prudence rules

The system MUST allow normal evaluation when context quality is `partial`. The system MUST allow evaluation when context quality is `degraded`, but SHALL include an explicit warning and human-review bullet points when the result is **accepted**. Rejected results MUST NOT carry warning or bullet fields regardless of context quality. The system MUST NOT introduce a separate explicit field or third outcome for insufficient evidence; prudence MUST be expressed within the accepted or rejected evaluation itself.

#### Scenario: Evaluate partial context without extra gating

- GIVEN a `ThreadContext` has quality `partial`
- WHEN the evaluation runs
- THEN the post is evaluated normally
- AND no degraded-context warning is required solely because it is partial

#### Scenario: Evaluate degraded context with reinforced review cues on accepted results

- GIVEN a `ThreadContext` has quality `degraded`
- WHEN the evaluation accepts the post
- THEN the accepted result includes a warning plus human-review bullet points
- AND the outcome remains accepted or rejected rather than a third state

#### Scenario: Rejected degraded context carries no warning or bullets

- GIVEN a `ThreadContext` has quality `degraded`
- WHEN the evaluation rejects the post
- THEN the rejected result contains only `post_id` and `rejection_type`
- AND no warning or human-review bullets are present on the rejected result
