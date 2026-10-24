# Design: Role C — Privacy Agent & Demo App

## Overview

Role C is the orchestration and presentation layer for Unmasked. It turns the measurement primitives (Role A)
and the mitigation primitives (Role B) into a single agent run and a guided Streamlit experience. The design
goal is a demo that works identically with or without an LLM key: the LLM only enriches wording (plans,
reports, role reasons) and never gates correctness.

```
            ┌──────────────────────────── app.py (Streamlit, 6 tabs) ─────────────────────────────┐
            │  data source  →  classify  →  risk  →  run_agent  →  before/after  →  report+download │
            └───────┬───────────────┬──────────────┬─────────────────┬───────────────────┬─────────┘
                    │               │              │                 │                   │
             reid/config.py   reid/classify.py  reid/risk (A)   reid/agent.run_agent  reid/utility (B)
                    │               │                                │
                    │          reid/llm.py  ◄── metadata + metrics only (never rows)
                    │                                               │
                    └─────────────── config.yaml ───────────────────┘
      agent.run_agent → tokens (B) · pii_text (B) · mitigate (B) · risk (A) · attacks (A) · utility (B)
```

## Architecture

Five Role-C modules, each with a single responsibility and a rule-based fallback where the LLM is involved.

### `reid/llm.py` — swappable LLM wrapper
- `llm_enabled()`: true only when `LLM_PROVIDER` ∈ {anthropic, openai}.
- `complete(prompt, system=None, json_mode=False, max_tokens=800)`: dispatches to Anthropic or OpenAI; wraps the
  whole call in try/except and returns `None` on any failure. Appends a strict "JSON only" instruction when
  `json_mode`.
- `parse_json(text)`: strips code fences, falls back to a regex object/array match, returns `None` if nothing parses.
- Contract: callers treat `None` as "use fallback". No student rows ever enter a prompt.

### `reid/classify.py` — profiling + role classification
- `profile_columns(df)`: metadata-only profile; skips `row_id`; emits at most 8 category labels per column.
- `ROLES`: the eight allowed roles.
- `roles_from_config(cfg)`: known-schema prior for the BU NSSE file.
- `classify_columns(profile, known_roles, batch=40)`: schema → heuristic → optional LLM upgrade. `derived`
  columns are never overwritten by the LLM. Each entry carries `role`, `reason`, `confidence`, `source`.

### `reid/agent.py` — the privacy agent
- `run_agent(df, roles, target_k, max_suppression, protect_small_groups, group_col, max_group_suppression,
  personas, scales, by_list, scrub_comments, log)`:
  1. **Measure**: `risk_summary` on quasi-ids, then quasi-ids + metadata.
  2. **Plan**: `_plan(...)` → LLM 3-sentence plan, else deterministic text.
  3. **Act**: `tokenize_column` for direct ids + `student_id`; drop other planted PII; drop or
     `scrub_text` free-text; `greedy_generalize` to `target_k` honoring `protect`.
  4. **Verify**: per-persona `make_attacker_table` + `linkage_attack` before/after; `utility_report`;
     `fairness_report`.
  5. **Report**: `privacy_label(result)` + `write_report(result)` (LLM or deterministic Markdown).
- Returns one result dict consumed by both the app and the smoke test.

### `app.py` — Streamlit UI (6 tabs)
- Sidebar: data source (built-in vs upload), counts, LLM status, safety caption.
- Tab 1 Data · Tab 2 Column roles (editable) · Tab 3 Risk · Tab 4 Fix it (controls + live log) ·
  Tab 5 Before vs after (label, attacks, fairness, utility, curve, detection) · Tab 6 Report & download.
- Uses `st.session_state` for `profile`, `roles`, `result`. Reads optional precomputed files from `results/`.

### `reid/config.py` + `config.yaml`
- Single source of truth for `targets` (k, suppression caps), `roles` (schema lists, `group_col`), `personas`,
  `utility_analyses`, and `data` paths. `load_config()` returns a plain dict.

### `scripts/smoke_test.py`
- Loads a small sample, runs profile → classify → `run_agent` with the LLM disabled, asserts the result dict has
  the expected keys and sane values, exits non-zero on failure. Serves as the post-merge gate.

## Components and Interfaces

| Component | Entry point | Consumes (not owned) | Fallback |
|---|---|---|---|
| LLM wrapper | `llm.complete`, `llm.parse_json` | provider SDKs | returns `None` |
| Classifier | `classify.profile_columns`, `classify.classify_columns` | `llm` | heuristic roles |
| Agent | `agent.run_agent` | risk/attacks (A), tokens/pii_text/mitigate/utility (B), `llm` | deterministic plan + report |
| App | `app.py` | all of the above | hides optional charts when files absent |
| Config | `config.load_config` | `config.yaml` | — |
| Smoke test | `scripts/smoke_test.py` | agent + classifier | runs with LLM off |

Role C treats Role A and Role B function signatures and column-name conventions as fixed contracts.

## Data Models

- **roles**: `{column: {role, reason, confidence, source}}` where `role ∈ classify.ROLES`.
- **agent result**: `{plan, steps[], before, before_with_metadata, after, attacks{persona:{before,after}},
  mitigation{release_df, suppressed_mask, levels, active_qis, transform, steps}, utility, fairness,
  protect_small_groups, target_k, label, report_md}`.
- **privacy label**: `{pct_unique_before, pct_unique_after, k_after, pct_suppressed, most_affected_group,
  most_affected_pct, attack_before_pct, attack_after_pct, max_mean_shift, remaining_risks[]}`.

## Error Handling

- LLM failures → `None` → rule-based path everywhere (Req 1, 2, 3).
- Missing `results/*.csv|json` → the corresponding chart/table is skipped, app stays up (Req 4.7).
- Empty quasi-identifier set → Tab 3 warns instead of computing.
- Upload normalization: rename `First Time First Year` → `FTFY`, inject `row_id` if absent.
- Never export `row_id`; never bundle vault keys with a release.

## Testing Strategy

- **Smoke test (gate)**: profile → classify → `run_agent` on a small sample, LLM disabled; assert result keys,
  `after.k_min ≥ target_k` within suppression budget, and that `release_df` has no `row_id`. Exit non-zero on failure.
- **Manual demo pass**: click all six tabs on the built-in dataset, with and without an LLM key, confirming the
  sidebar status flips and the report/download work.
- **Guardrail check**: grep prompts to confirm only metadata/metrics are sent; confirm no FERPA-compliance claims.
