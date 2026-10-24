# Implementation Plan: Role C — Privacy Agent & Demo App

- [x] 1. Config loader and shared settings
  - Implement `load_config()` in `reid/config.py` to read `config.yaml` into a plain dict.
  - Ensure `config.yaml` defines `targets` (k, max_suppression, max_group_suppression), `roles`
    (direct_ids, quasi_ids, quasi_ids_extended, metadata, derived_major, planted, group_col), `personas`,
    `utility_analyses` (scales, by), and `data` paths.
  - _Requirements: 5.1_

- [x] 2. Fail-safe LLM wrapper
- [x] 2.1 Implement provider dispatch and enable check
  - `llm_enabled()` returns true only for providers `anthropic`/`openai`; `complete(...)` returns `None` otherwise.
  - Read keys from the environment; support `system` and `max_tokens`.
  - _Requirements: 1.1, 1.2, 1.5_
- [x] 2.2 Harden against failures and JSON parsing
  - Wrap the call in try/except, log one line, return `None` on any error.
  - Implement `parse_json` to tolerate code fences and surrounding prose, returning `None` on failure.
  - _Requirements: 1.3, 1.4_

- [x] 3. Metadata-only profiling and role classification
- [x] 3.1 `profile_columns`
  - Emit dtype, n_unique, pct_missing, pct_unique_values, optional top ≤8 labels and avg_text_len; skip `row_id`.
  - Verify no row-level values leak beyond category labels.
  - _Requirements: 2.1, 2.2_
- [x] 3.2 Schema prior + heuristic + LLM upgrade
  - `roles_from_config` builds the known-schema prior; heuristic covers unknown columns.
  - Optional LLM pass upgrades to `source="llm"` but never overrides `derived`; all roles ∈ `ROLES`.
  - _Requirements: 2.3, 2.4, 2.5, 2.6_

- [x] 4. Privacy agent pipeline (`run_agent`)
- [x] 4.1 Measure stage
  - Compute baseline risk on quasi-ids and on quasi-ids + metadata; record step messages.
  - _Requirements: 3.1_
- [x] 4.2 Plan stage
  - `_plan(...)` returns an LLM 3-sentence plan when available, else a deterministic plan.
  - _Requirements: 3.2_
- [x] 4.3 Act stage
  - Tokenize direct ids + `student_id` into a vault; drop remaining planted PII; drop or Presidio-scrub free text.
  - Run `greedy_generalize` to `target_k` within `max_suppression`, honoring `protect` for `group_col`.
  - _Requirements: 3.3, 3.4_
- [x] 4.4 Verify + report stages
  - Re-run per-persona linkage attacks before/after; compute utility and fairness.
  - Build `privacy_label` and `write_report` (LLM or deterministic) using computed facts only; no FERPA claim.
  - Return the full result dict with all required keys.
  - _Requirements: 3.5, 3.6, 3.7_

- [x] 5. Streamlit app (`app.py`)
- [x] 5.1 Sidebar + data source
  - Built-in dataset (cached) vs CSV/XLSX upload; show counts and LLM connected/fallback status.
  - Normalize uploads (`First Time First Year`→`FTFY`, inject `row_id`).
  - _Requirements: 4.1, 4.7_
- [x] 5.2 Tabs 1–2 (data + roles)
  - Preview data without `row_id`; classify, edit roles in a data editor, confirm roles into session state.
  - _Requirements: 4.2_
- [x] 5.3 Tab 3 (risk)
  - Metrics, staircase, riskiest-pairs heatmap, personas, risk-by-group, metadata leaks; warn when no quasi-ids.
  - _Requirements: 4.3_
- [x] 5.4 Tab 4 (fix it)
  - Controls for k, max suppression, protect-small-groups, comment scrubbing; run agent with live log.
  - _Requirements: 4.4_
- [x] 5.5 Tabs 5–6 (before/after + report)
  - Nutrition label, attack chart, fairness, surviving analyses, ML utility, curve, detection table.
  - Render report; safe downloads (release CSV without `row_id`, report Markdown); skip missing `results/` files.
  - _Requirements: 4.5, 4.6, 4.7_

- [x] 6. Smoke test merge gate
  - `scripts/smoke_test.py` runs profile → classify → `run_agent` on a small sample with the LLM disabled.
  - Assert result keys and that the release has no `row_id`; exit non-zero on failure.
  - _Requirements: 5.2, 5.3_

> Note: a later Role C change (not in the original spec) added `reid/release_warnings.py` and wired it into
> `app.py` tabs 4 and 5 to warn when a release is strongly private but low-usefulness, with unit tests in
> `scripts/checks/test_release_warnings.py`.
