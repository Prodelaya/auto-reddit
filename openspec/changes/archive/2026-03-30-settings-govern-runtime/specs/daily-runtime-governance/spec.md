# Delta for daily-runtime-governance

## ADDED Requirements

### Requirement: Document the operational settings contract without decorative knobs

The documentation MUST describe only settings that have a verified runtime consumer, and SHALL treat `deepseek_api_key`, `telegram_bot_token`, `telegram_chat_id`, `reddit_api_key`, `review_window_days`, `daily_review_limit`, `max_daily_opportunities`, `deepseek_model`, and `db_path` as part of the documented operational contract. The documentation MUST NOT describe any of these settings as optional decoration or as non-runtime placeholders.

#### Scenario: Runtime-backed settings inventory is documented consistently

- GIVEN the runtime contract is verified from `Settings` and its real consumers
- WHEN the configuration documentation is reviewed
- THEN the documented settings inventory matches the runtime-backed inventory
- AND no documented setting is presented as unused or decorative

#### Scenario: Operational parameters are not omitted from the contract

- GIVEN `deepseek_model` and `db_path` affect runtime behavior through real consumers
- WHEN maintainers review the documented configuration surface
- THEN both settings appear as operational parameters in the documented contract

### Requirement: Distinguish pre-evaluation and post-evaluation daily caps

The documentation MUST state that `daily_review_limit` caps the candidate set before AI evaluation, while `max_daily_opportunities` caps the delivered opportunity set after evaluation and selection. The documentation SHOULD use the same pipeline vocabulary across artifacts so operators can see that equal defaults do not mean the same control point.

#### Scenario: Pre-evaluation cap is explained correctly

- GIVEN a maintainer reads the daily-limit documentation
- WHEN they inspect the meaning of `daily_review_limit`
- THEN the documentation states that it trims the review set before AI evaluation

#### Scenario: Post-evaluation cap remains distinct even with same default

- GIVEN both daily caps default to 8
- WHEN an operator compares both settings in the documentation
- THEN the documentation makes clear that `max_daily_opportunities` applies after evaluation/selection and before Telegram delivery
- AND the two limits are not described as synonyms

### Requirement: Keep architecture, product, and example environment documents aligned

The change MUST align `docs/architecture.md`, `docs/product/product.md`, and `.env.example` to the same settings contract. `docs/architecture.md` SHALL define the full documented surface, `docs/product/product.md` SHALL describe the observable product-facing semantics of the daily limits, and `.env.example` SHALL clarify the operational `DB_PATH` example without contradicting the runtime default or its precedence.

#### Scenario: Cross-document review no longer produces contradictory guidance

- GIVEN a reviewer compares `docs/architecture.md`, `docs/product/product.md`, and `.env.example`
- WHEN they check settings names, semantics, and DB path guidance
- THEN the three documents present one coherent contract

#### Scenario: Example DB path does not misstate the runtime default

- GIVEN `.env.example` shows a Docker-oriented `DB_PATH` example
- WHEN a developer reads the surrounding guidance
- THEN they can distinguish the operational example from the runtime default value
- AND the document does not imply a false default or precedence rule
