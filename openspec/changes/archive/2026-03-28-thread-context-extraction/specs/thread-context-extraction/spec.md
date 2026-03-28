# thread-context-extraction Specification

## Purpose

Definir el paso que enriquece solo los posts ya seleccionados aguas arriba con contexto bruto normalizado del hilo, manteniendo separadas la extraccion de datos y la evaluacion/delivery posterior.

## Requirements

### Requirement: Enrich only upstream-selected posts

The system MUST attempt thread-context extraction only for posts already selected by the upstream daily slice, and MUST NOT expand the batch with posts outside that upstream handoff.

#### Scenario: Process only the selected handoff set

- GIVEN the upstream handoff contains only the selected posts for that daily run
- WHEN thread-context extraction starts
- THEN only those posts are processed for context enrichment

#### Scenario: Ignore posts outside the handoff

- GIVEN another in-window Reddit post was not included in the upstream handoff
- WHEN thread-context extraction runs
- THEN that post is not queried or added to the batch

### Requirement: Deliver normalized raw thread context

For each successfully enriched post, the system MUST deliver normalized raw thread context containing the original post material plus any recovered thread context, and MUST NOT convert that output into an AI summary, opportunity decision, or delivery-ready message.

#### Scenario: Normalize heterogeneous provider payloads

- GIVEN a selected post is recovered from a provider with source-specific field names or nesting
- WHEN the context is normalized
- THEN the downstream output exposes one common raw thread-context contract

#### Scenario: Preserve raw context without editorial judgment

- GIVEN recovered thread context is available for a selected post
- WHEN the output is produced
- THEN the payload remains raw normalized context rather than a summary or business verdict

### Requirement: Expose simple context degradation

The system MUST expose a simple degradation indicator for each delivered thread-context payload so downstream evaluation can distinguish complete context from degraded context.

#### Scenario: Mark degraded context explicitly

- GIVEN a selected post required a degraded fallback or returned partial context
- WHEN the normalized payload is emitted
- THEN the payload includes an explicit simple degradation indicator

### Requirement: Drop posts with total context failure

If all configured context/comment sources fail for a selected post, the system MUST drop that post from the current batch instead of emitting an empty or misleading thread-context payload.

#### Scenario: Exclude a post after total context failure

- GIVEN a selected post exhausts all available context/comment sources without usable recovery
- WHEN thread-context extraction completes for that post
- THEN that post is excluded from the downstream batch

### Requirement: Preserve downstream decision boundaries

This change MUST NOT decide whether a post is an opportunity, whether the thread is resolved or closed, or how/when delivery or publication happens.

#### Scenario: Hand off context without downstream decisions

- GIVEN normalized raw thread context was produced for a selected post
- WHEN the step hands off its output downstream
- THEN no opportunity classification, resolved/closed status, or delivery action is attached by this change
