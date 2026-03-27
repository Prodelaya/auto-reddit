# reddit-candidate-collection Specification

## Purpose

Definir el comportamiento funcional del change 1: recoger todos los posts de `r/Odoo` creados en los ultimos 7 dias y entregarlos como candidatos normalizados para el siguiente paso del pipeline.

## Boundary Note

La validacion tecnica de endpoints mediante scripts y snapshots JSON en `raw/` puede hacerse antes de design, pero SHALL NOT cambiar ni ampliar el comportamiento funcional definido aqui.

## Requirements

### Requirement: Collect posts from the active source window

The system MUST collect posts only from `r/Odoo`, MUST include every post whose `created_at` is within the last 7 days at execution time, and MUST order the delivered list by recency.

#### Scenario: Collect all in-window posts from r/Odoo

- GIVEN Reddit returns multiple posts from `r/Odoo` created within the last 7 days
- WHEN the collection step runs
- THEN the output includes all of those posts
- AND the posts are ordered from most recent to least recent

#### Scenario: Exclude out-of-scope posts

- GIVEN Reddit returns posts older than 7 days or from another subreddit
- WHEN the collection step runs
- THEN those posts are excluded from the delivered candidate list

### Requirement: Normalize each candidate to the minimum contract

The system MUST deliver each collected post as a normalized candidate exposing `post_id`, `title`, `body/selftext`, `url/permalink`, `author`, `subreddit`, and `created_at`.

#### Scenario: Normalize heterogeneous source shapes

- GIVEN a provider returns equivalent Reddit post data with different field names or relative links
- WHEN the post is normalized
- THEN the candidate exposes the minimum contract fields with canonical meanings

### Requirement: Preserve incomplete posts explicitly

The system MUST NOT discard an in-scope post only because one or more minimum-contract fields are missing, and MUST mark that candidate explicitly as incomplete.

#### Scenario: Keep incomplete but still relevant posts

- GIVEN an in-scope post is missing one or more minimum-contract fields
- WHEN the post is normalized
- THEN the candidate remains in the output list
- AND the candidate carries an explicit incomplete marker

### Requirement: Hand off the full candidate set without downstream rules

The system MUST deliver the normalized candidates in memory/process to the next pipeline step, MUST NOT fetch comments as part of this change, MUST NOT apply the downstream cut to 8 candidates, and MUST NOT include the `old but alive` case.

#### Scenario: Deliver the full handoff set

- GIVEN more than 8 in-scope posts exist in the last 7 days
- WHEN the collection step completes
- THEN all normalized candidates are handed off in memory/process
- AND no truncation to 8 occurs in this change

#### Scenario: Keep comments outside this change

- GIVEN a collected post has comments available in Reddit
- WHEN the collection step completes
- THEN no comment payload is required in the delivered candidates
