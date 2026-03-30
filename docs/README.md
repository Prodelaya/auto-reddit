# Documentation Map — auto-reddit

> **How to use this map**: start here. Each section below routes you to the right place based on what you need. If you are a first-time reader, begin with **Current Truth**.

## Current Truth

The authoritative documents describing what the system does right now.

| Document | Role |
|----------|------|
| `docs/product/product.md` | Product source of truth for the current slice — goals, constraints, user, and decision model |
| `docs/product/ai-style.md` | AI behavior and response style guide — tone, format, and output rules |
| `docs/architecture.md` | Architectural decisions and component responsibilities |
| `docs/operations.md` | Operational runbook — deployment, environment, cron, and failure handling |
| `docs/integrations/reddit/api-strategy.md` | Reddit API strategy — provider selection, fallback order, and rate-limit handling |

## Planning & Archive

Change proposals, specs, designs, and completed change records. These describe *intended* or *past* work — not the current system state.

| Area | Role |
|------|------|
| `openspec/initiative/` | High-level initiative documents defining multi-change goals |
| `openspec/changes/` | Per-change proposals, specs, designs, and task breakdowns (active and archived) |
| `openspec/specs/` | Consolidated specs promoted from changes when merged |
| `openspec/discovery/` | Early discovery material feeding planning work |

## Didactic & Historical

Learning material and historical snapshots. These preserve the reasoning behind past decisions and are valuable for understanding evolution, but they are **not** current operating truth.

| Document | Role |
|----------|------|
| `TFM/guia-didactica-auto-reddit.md` | Didactic guide — step-by-step narrative of how the system was built, for learning purposes |
| `TFM/diario.md` | Development diary — daily log of decisions and discoveries during construction |
| `TFM/motivacion.md` | Motivation document — academic and personal context for the project |
| `docs/discovery/idea-inicial.md` | Historical ideation snapshot — early product discovery, contains superseded decisions |
| `docs/discovery/ideas.md` | Loose notes — raw ideas not yet promoted to product or planning artifacts |

## Agent Context (not project truth)

Files consumed by AI coding agents for operational context. Listed here for navigability only — their content is not maintained as human documentation and is not project truth.

| File | Role |
|------|------|
| `AGENTS.md` | Agent instructions — environment, build commands, and project constraints |
| `CLAUDE.md` | Claude Code context — tool usage, memory protocol, and session conventions |
| `skills/` | Project-specific skill files loaded by agents for coding standards and workflows |
