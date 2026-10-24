# Implementation Plan: role-b-mitigation

## Overview

This plan recreates Role B's seven deliverables in Kiro by transcribing the authoritative
reference implementation from the Low-Level Design section of `design.md` (Appendix B of the
brief), running each module, and verifying it against the documented acceptance numbers in
section B2 of the brief. The reference code is authoritative — tasks transcribe it, they do not
redesign it.

Language: Python 3.11+ with pandas (as used throughout the reference implementation).

The build sequence follows the required order: (1) `reid/plant.py`, (2) `hierarchies.yaml` +
`reid/mitigate.py` together, (3) `reid/tokens.py`, (4) `reid/pii_text.py`, (5) `reid/utility.py`,
(6) the Role B sections of `scripts/run_experiments.py`. Each implementation task ends with its
acceptance check.

### External dependencies (owned by Roles A and C — NOT built here)

These are consumed as interfaces and must exist (or be stubbed) for acceptance checks to run:

- `reid/config.py` (C) — `load_config()`; and `config.yaml` (C).
- `reid/load.py` (A) — `load_clean(cfg)` / `load_raw(cfg)` (adds `row_id`, `FTFY`, casts `MAJsecond`).
- `reid/risk.py` (A) — `class_sizes`, `risk_summary` (consumed by `mitigate.py`, `utility.py`).
- `reid/attacks.py` (A) — `make_attacker_table`, `linkage_attack`, `persona_risk` (consumed by the runner).
- `reid/llm.py` (C) — `complete`, `parse_json`, `llm_enabled` (consumed by `pii_text.py`).
- `scripts/build_cache.py` (A) — writes the planted/truth parquet using Role B's `plant_identifiers`.
- `app.py` (C) — consumer only.

**Fallback (per brief B0):** if the clean parquet (`data/nsse_clean.parquet`) from Role A is not
yet available, read the xlsx directly via `reid/load.load_raw(cfg)` (slow but works) to obtain a
clean df with `row_id`. If Role A's `risk.py` is not yet present, the mitigation and utility
acceptance checks are blocked until it exists (or a minimal local stub of `class_sizes` /
`risk_summary` is used); note this when running the check.

## Tasks

- [x] 1. Recreate `reid/plant.py` (planted identifiers + ground truth)
  - [x] 1.1 Write `reid/plant.py` transcribing the reference implementation from design.md
    - Transcribe `CLEAN`, `DECOYS`, `PII_TEMPLATES`, `_bu_id`, `_phone`, and
      `plant_identifiers(df, seed=42, pct_pii=0.30, pct_decoy=0.10) -> (planted_df, truth_df)`.
    - Add `full_name`, `email` (first-initial + last-name + 1–99 + `@bu.edu`),
      `student_id` (`"U"` + 8 digits), and `comment` (~30% PII, ~10% decoy, ~60% clean).
    - Emit `truth_df` with columns `row_id, entity_type, value, start, end`;
      `entity_type ∈ {PERSON, EMAIL_ADDRESS, PHONE_NUMBER, BU_ID}`.
    - Depends on a clean df carrying `row_id` from `reid/load.py` (A) or, as fallback, `load_raw`.
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 8.1, 9.1_

  - [x]* 1.2 Write property test for plant span integrity
    - **Property 1: Span integrity (plant)** — for every truth row,
      `planted_df.loc[row_id, "comment"][start:end] == value`.
    - **Validates: Requirements 1.6**
    - Use `hypothesis` to generate seeds / comment variations; assert 0 span errors.

  - [ ]* 1.3 Write unit test for plant determinism
    - Assert fixed `seed` yields identical `planted_df` and `truth_df` across runs.
    - _Requirements: 1.7_

  - [x] 1.4 Acceptance check: run plant on the clean data (B2 Task B2)
    - Load the clean df (via `load_clean`, or `load_raw` fallback), call `plant_identifiers(df)`.
    - Verify for EVERY truth row `comment[start:end] == value` → **0 span errors**.
    - Note: `plant_identifiers` is given to Role A for `scripts/build_cache.py`
      (which writes the planted/truth parquet). Do NOT implement `build_cache.py` — it is Role A's.
    - _Requirements: 1.6, 1.7_

- [x] 2. Recreate `hierarchies.yaml` and `reid/mitigate.py` (hierarchies + greedy mitigation)
  - [x] 2.1 Write `hierarchies.yaml` transcribing the reference from design.md
    - Define ordered levels for every QI and metadata column; level 0 = identity, last level = `drop`.
    - Support rule types `identity`, `map`, `map_other`, `from_column`, `has_value`, `month`,
      `year`, `bins`, `drop`; include the `derived:` lockstep section.
    - Use `label_yes`/`label_no` (not `yes`/`no`) and plain integer `1000000000` (not `1.0e12`).
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 8.4_

  - [x] 2.2 Write `reid/mitigate.py` transcribing the reference from design.md
    - Transcribe `load_hierarchies`, `_h`, `max_level`, `_apply_rule`, `apply_levels`,
      `make_transform`, `suppress`, `_group_supp`, and
      `greedy_generalize(df, qis, k=5, max_suppression=0.05, max_group_suppression=None, group_col="affiliation", protect=(), must_keep=())`.
    - `apply_levels` drops columns at `drop` level, drops derived columns in lockstep, and skips
      columns not present. Greedy loop scores gain-per-cost (drop=2, coarsen=1); `must_keep` caps
      at level 1; stops at `max_suppression` (and per-group when set), else suppresses remainder.
    - Return dict keys `levels, release_df (row_id kept), suppressed_mask, steps, final_risk, active_qis, transform`.
    - Depends on `reid/risk.py` (A): `class_sizes`, `risk_summary`.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.7, 3.8, 3.9, 3.10, 3.11, 8.1, 8.2, 8.3, 8.4_

  - [ ]* 2.3 Write property test for monotone generalization
    - **Property 4: Monotone generalization** — raising a column's level never increases its
      distinct-value count; reaching `max_level` removes the column.
    - **Validates: Requirements 3.2, 3.5**

  - [x]* 2.4 Write property test for lockstep derived drop
    - **Property 5: Lockstep derived drop** — when a source code column reaches the listed level,
      its derived columns are absent from `apply_levels` output.
    - **Validates: Requirements 3.3**

  - [x]* 2.5 Write property test for suppression completeness
    - **Property 6: Suppression completeness** — after `suppress(df, qis, k)`, every equivalence
      class over present `qis` has size ≥ k.
    - **Validates: Requirements 3.6**

  - [x] 2.6 Acceptance check: run greedy_generalize both modes (B2 Task B1)
    - On 14 QIs + 2 metadata columns, k=5, `max_suppression=0.05`.
    - protect ON (`protect=[affiliation]`, `max_group_suppression=0.10`): verify ~2.5% removed,
      0% unique, `affiliation` kept, per-group removal from ~6.9% (Diademed sifaka) down to
      ~0.9% (Ring-tailed lemur).
    - protect OFF (`{}`): verify ~3.5% removed and `affiliation` dropped.
    - Verify each run completes in ~4–5 s.
    - _Requirements: 3.12, 3.13, 3.14_

- [x] 3. Recreate `reid/tokens.py` (reversible tokenization vault)
  - [x] 3.1 Write `reid/tokens.py` transcribing the reference from design.md
    - Transcribe `ensure_keys`, `_join_key`, `_vault`, `join_token`, `_vault_path`,
      `tokenize_column`, `detokenize`.
    - `join_token` = HMAC-SHA256 hex[:16] (deterministic). `tokenize_column` replaces the column
      with tokens and writes a deduped per-column vault `keys/vault_<col>.csv` (Fernet-encrypted
      originals); vault key in `keys/vault.key`. `detokenize` reverses or raises
      `KeyError("token not found")`.
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 4.7, 4.8, 8.1, 9.3, 9.4_

  - [x]* 3.2 Write property test for token determinism and round trip
    - **Property 2: Token determinism** — equal inputs yield equal tokens under the same key.
    - **Property 3: Reversibility** — `detokenize(tokenize_column(df, col).iloc[i][col], col) == str(df.iloc[i][col])`.
    - **Validates: Requirements 4.3, 4.4, 4.6**
    - Use `hypothesis` over random strings for the round trip.

  - [x] 3.3 Acceptance check: round-trip and key hygiene (B2 Task B3)
    - Verify `detokenize(tokenize_column(df, "student_id").student_id[0], "student_id")` returns
      the original value.
    - Confirm `keys/` (including `vault.key` and `vault_*.csv`) is gitignored and nothing in
      `keys/` is committed.
    - _Requirements: 4.6, 8.1, 9.3_

- [x] 4. Recreate `reid/pii_text.py` (PII detection, scrubbing, scoring)
  - [x] 4.1 Verify Presidio setup first (B1 quick check) — main unknown
    - Ensure `en_core_web_sm` is installed (`python -m spacy download en_core_web_sm`; small model).
    - Run `presidio_detect("Email jsmith4@bu.edu or call 617-555-0142. My ID is U12345678 and my advisor Maria Lopez helped.")`.
    - Expect EMAIL_ADDRESS, PHONE_NUMBER, BU_ID, and PERSON. If PERSON is missed, lower
      `threshold` to 0.3 and retest. Presidio setup is the main unknown — verify before scoring.
    - _Requirements: 5.1, 5.3_

  - [x] 4.2 Write `reid/pii_text.py` transcribing the reference from design.md
    - Transcribe `ENTITIES`, `_engine`, `presidio_detect`, `LLM_SYSTEM`, `llm_detect`, `_dedupe`,
      `scrub_text`, `combine`, `evaluate_detection`.
    - Presidio uses `en_core_web_sm` + custom `BU_ID` recognizer (`\bU\d{8}\b`, score 0.9); return
      only the four entity types. `llm_detect` returns `[]` when the LLM is disabled/non-list and
      sends only synthetic comments. `scrub_text` replaces spans with `<ENTITY_TYPE>`.
      `evaluate_detection` TP = same type + overlapping span, each truth matched once, scoring only
      rows present in `predictions`; output per-entity rows plus `ALL` with tp/fp/fn/precision/recall/f1.
    - Depends on `reid/llm.py` (C) for `llm_detect`.
    - _Requirements: 5.1, 5.2, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 8.1, 9.2_

  - [ ]* 4.3 Write property test for detection scoring
    - **Property 7: Detection scoring** — a prediction is TP iff an unmatched truth entity shares
      its type and overlaps its span; each truth matched at most once; only rows in `predictions`
      are scored.
    - **Validates: Requirements 5.8**
    - Build small hand-crafted truth/prediction pairs covering TP, FP, FN.

  - [x] 4.4 Acceptance check: score detection on a 1,500-comment sample (B2 Task B4)
    - Build `predictions = {row_id: presidio_detect(comment)}` over a 1,500-comment sample of the
      planted data; run `evaluate_detection(truth, predictions)`.
    - Expect EMAIL_ADDRESS and BU_ID near 100% precision/recall; phone high; PERSON lower with the
      small model. Report numbers honestly — misses are a finding.
    - _Requirements: 5.10_

- [x] 5. Recreate `reid/utility.py` (utility, fairness, curve)
  - [x] 5.1 Write `reid/utility.py` transcribing the reference from design.md
    - Transcribe `group_means`, `utility_report`, `_EXCLUDE_PREFIXES`, `_features`, `ml_utility`,
      `fairness_report`, `privacy_utility_curve`.
    - `utility_report` draws group labels from `original_df` joined on `row_id`; sets
      `analysis_status[by] ∈ {available, coarsened, lost}`. `ml_utility` trains
      `HistGradientBoostingRegressor` on `SE` (excluding `SE*`, `row_id`, `ID`, metadata, planted),
      testing both on the same held-out original rows (release via `transform`). `fairness_report`
      returns `group, n, n_suppressed, pct_suppressed`. `privacy_utility_curve` runs k=2,3,5,10.
    - Depends on `reid/mitigate.py` (Task 2) and `reid/risk.py` (A).
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.6, 6.7, 8.2, 8.3_

  - [ ]* 5.2 Write unit tests for utility and fairness
    - `analysis_status` labeling (available/coarsened/lost); `fairness_report` column shape and
      per-group `pct_suppressed`.
    - _Requirements: 6.3, 6.6_

  - [x] 5.3 Acceptance check: utility, ML, fairness, curve (B2 Task B5)
    - Run `utility_report`; run `ml_utility` and verify R² ≈ 0.42 original vs ≈ 0.37 (protect-on)
      / ≈ 0.41 (protect-off); run `fairness_report`; run `privacy_utility_curve` at k=2,3,5,10 and
      confirm one row per k with the expected columns.
    - _Requirements: 6.4, 6.5, 6.7_

- [x] 6. Recreate the Role B sections of `scripts/run_experiments.py`
  - [x] 6.1 Write the Role B sections transcribing the reference from design.md
    - Add argparse flags (`--skip-presidio`, `--presidio-sample`, `--llm-sample`); load config;
      read planted/truth parquet; build `work = df.drop(columns=R["planted"])`.
    - Mitigation in both modes (`protect_on` / `protect_off`) writing `results/attack.json`,
      `results/fairness.csv` (with `setting` column), `results/mitigation_summary.json`,
      `results/curve.csv`. PII detection writing `results/detection.csv` with methods `presidio`,
      `presidio_same_sample`, `llm`, `combined`, gated behind `--skip-presidio`.
    - Do NOT modify Role A's section of the file. Depends on `reid/config.py` (C),
      `reid/attacks.py` (A), and Tasks 1–5.
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.2_

  - [x] 6.2 Acceptance check: run the experiment runner (B2 Task B6)
    - Run `python scripts/run_experiments.py --skip-presidio` and confirm `results/attack.json`,
      `results/fairness.csv`, `results/mitigation_summary.json`, and `results/curve.csv` are written.
    - With Presidio available, run without the flag and confirm `results/detection.csv` is written
      with the four methods (`presidio`, `presidio_same_sample`, `llm`, `combined`).
    - _Requirements: 7.1, 7.3, 7.4, 7.5_

- [x] 7. Final checkpoint — ensure all acceptance checks pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional (unit and property tests) and can be skipped for a faster MVP.
- Each task references specific requirement clauses for traceability.
- The reference implementation in design.md's Low-Level Design is authoritative — transcribe it;
  do not redesign working code.
- Files owned by Roles A and C (`config.py`, `load.py`, `risk.py`, `attacks.py`, `llm.py`,
  `build_cache.py`, `app.py`) are NOT built here; several tasks depend on them existing.
- Fallback for blocked acceptance checks: read the xlsx via `reid/load.load_raw(cfg)` when the
  Role A clean parquet is unavailable (per brief B0).
- `release_df` keeps `row_id` for identity joins inside Role B functions; Role C drops it on export.
- `keys/`, `data/`, and `.env` must never be committed.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "3.1", "4.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4", "2.2", "3.2", "3.3", "4.2"] },
    { "id": 2, "tasks": ["2.3", "2.4", "2.5", "2.6", "4.3", "4.4", "5.1"] },
    { "id": 3, "tasks": ["5.2", "5.3", "6.1"] },
    { "id": 4, "tasks": ["6.2"] }
  ]
}
```
