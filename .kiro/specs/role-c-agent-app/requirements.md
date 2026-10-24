# Requirements: Role C — Privacy Agent & Demo App

## Description (Role C scope)

Role C owns the user-facing and orchestration layer of Unmasked: the AI privacy agent that ties together
the measure → plan → act → verify → report pipeline, the LLM wrapper and column-role classifier that feed
it, and the 6-tab Streamlit demo app that a judge or data owner actually clicks through. Role C also owns
the shared config loader and the smoke test used as the merge gate.

Owned files (per steering `tech.md` / `structure.md`):
`config.yaml`, `reid/config.py`, `reid/llm.py`, `reid/classify.py`, `reid/agent.py`, `app.py`,
`scripts/smoke_test.py`, `README.md`, `requirements.txt`, `.gitignore`, `.env.example`.

Role C consumes interface contracts from Role A (`reid/risk.py`, `reid/attacks.py`, `reid/load.py`) and
Role B (`reid/tokens.py`, `reid/pii_text.py`, `reid/mitigate.py`, `reid/utility.py`) without editing them.

### Guardrails (non-negotiable, from steering)

- The LLM only ever receives column metadata and computed metrics, never student rows.
- `llm.complete()` returns `None` when disabled or on error; every caller MUST have a rule-based fallback.
- Synthetic data only. Tokenized data is pseudonymous, not anonymous. Never claim FERPA compliance.
- Every DataFrame carries `row_id` and it is never exported. `First Time First Year` is renamed `FTFY`.
- A human data steward must approve every release.

## Requirements

### Requirement 1 — Swappable, fail-safe LLM wrapper

**User Story:** As a developer, I want a thin LLM wrapper that degrades gracefully, so the app runs with or
without an API key and never crashes because of the model.

#### Acceptance Criteria

1. WHEN `LLM_PROVIDER` is unset or not in (`anthropic`, `openai`) THEN `llm.llm_enabled()` SHALL return `False`
   and `llm.complete(...)` SHALL return `None`.
2. WHEN the provider is `anthropic` or `openai` and a valid key is present THEN `llm.complete(...)` SHALL return
   model text, reading the key from the environment (`ANTHROPIC_API_KEY` / `OPENAI_API_KEY`).
3. WHEN the LLM call raises any exception THEN the wrapper SHALL catch it, log a single line, and return `None`
   rather than propagating.
4. WHEN `json_mode=True` is requested THEN `llm.parse_json(...)` SHALL tolerate code fences and surrounding prose
   and return `None` on unparseable output.
5. The wrapper SHALL NOT include any student row values in prompts.

### Requirement 2 — Metadata-only column profiling and role classification

**User Story:** As a data owner, I want the agent to label every column's privacy role from metadata only, so I
can review and correct roles before any risk is measured.

#### Acceptance Criteria

1. WHEN `profile_columns(df)` runs THEN it SHALL emit per-column metadata (dtype, n_unique, pct_missing,
   pct_unique_values, optional top ≤8 category labels, optional avg_text_len) and SHALL exclude `row_id`.
2. The profile SHALL NOT leak row-level values beyond at most 8 category labels per low-cardinality column.
3. WHEN a known schema (config) is supplied THEN `classify_columns` SHALL use it as a prior with `source="schema"`.
4. WHEN no schema entry exists THEN a deterministic heuristic SHALL assign a role with `source="heuristic"`.
5. WHEN the LLM is enabled THEN classifications MAY be upgraded to `source="llm"`, except `derived` columns SHALL
   keep following their source column's hierarchy.
6. Every produced role SHALL be one of the eight values in `classify.ROLES`.

### Requirement 3 — Agent pipeline: measure → plan → act → verify → report

**User Story:** As a data owner, I want one action that measures risk, applies fixes, verifies them, and writes a
report, so I get an end-to-end safe release without manual steps.

#### Acceptance Criteria

1. WHEN `run_agent(df, roles, ...)` runs THEN it SHALL measure baseline risk on quasi-identifiers and again
   including survey metadata, and record a human-readable step for each stage.
2. The agent SHALL produce a plan via the LLM when available and SHALL fall back to a deterministic plan otherwise.
3. The agent SHALL tokenize direct identifiers (and `student_id`) into a separate vault, drop remaining planted PII,
   and either drop or Presidio-scrub free-text columns per the `scrub_comments` setting.
4. The agent SHALL generalize and suppress quasi-identifiers + metadata to reach `target_k` within `max_suppression`,
   and WHEN `protect_small_groups` is true THEN it SHALL NOT merge or drop the demographic `group_col`.
5. The agent SHALL verify by re-running simulated linkage attacks per persona (before vs. after) and SHALL compute
   utility and fairness reports.
6. The agent SHALL return a result dict containing `plan`, `steps`, `before`, `after`, `attacks`, `mitigation`,
   `utility`, `fairness`, a `label` (privacy nutrition label), and `report_md`.
7. The report SHALL be built from computed facts only and SHALL NOT claim FERPA compliance.

### Requirement 4 — Streamlit demo app (6 tabs)

**User Story:** As a judge or data owner, I want a guided 6-tab UI, so I can see the dataset, roles, risk, the fix,
before/after, and a downloadable report in a 2-minute demo.

#### Acceptance Criteria

1. The app SHALL offer the built-in BU synthetic dataset and a CSV/XLSX upload, and SHALL show row/column counts
   and whether the LLM is connected or in rule-based fallback.
2. Tab 1 SHALL preview data without `row_id`. Tab 2 SHALL classify columns, allow role overrides via an editor, and
   let the user confirm roles.
3. Tab 3 SHALL show % unique, % below k, % unique including timing, average risk, the staircase chart, riskiest
   pairs heatmap, attacker personas, risk by group, and metadata leaks when applicable.
4. Tab 4 SHALL expose controls for target k, max suppression, protect-small-groups, and comment scrubbing, and run
   the agent with a live step log.
5. Tab 5 SHALL render the privacy nutrition label, before/after attack chart, fairness chart, surviving analyses,
   ML utility, privacy-utility curve, and PII detection table when result files exist.
6. Tab 6 SHALL render the report and offer safe downloads (release CSV without `row_id`, report Markdown), with a
   note that vault keys are never bundled.
7. The app SHALL cache the built-in dataset load and SHALL NOT crash when optional `results/` files are missing.

### Requirement 5 — Config loader and smoke test merge gate

**User Story:** As a team, I want a single config source and a fast smoke test, so every merge to main is verified
end to end in seconds.

#### Acceptance Criteria

1. `reid/config.py` SHALL load `config.yaml` and expose targets, roles, personas, and utility-analysis settings.
2. `scripts/smoke_test.py` SHALL exercise profiling → classification → `run_agent` on a small sample and SHALL exit
   non-zero on failure, so it can gate merges (`python scripts/smoke_test.py`).
3. The smoke test SHALL pass with the LLM disabled (rule-based fallback only), requiring no API key.
