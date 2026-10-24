# Tasks: Role A — Data, Risk Engine, and Attacks

- [x] 1. Implement data loading and caching (`reid/load.py`)
  - Write `load_raw(cfg)`: read sheet `in`, rename `First Time First Year`→`FTFY`, cast `MAJsecond` to str keeping NaN, parse `logdate` as datetime, prepend `row_id` (0..n-1).
  - Write `build_clean_cache(cfg)`: build and write `data/nsse_clean.parquet`, create parent dir, return the DataFrame.
  - Write `load_clean(cfg)`: read the parquet, building it if missing.
  - Write `load_lookup(cfg)`: return `{field: {int code: meaning}}` from the lookup xlsx.
  - _Requirements: 1.1–1.9_

- [x] 2. Implement the risk engine (`reid/risk.py`)
- [x] 2.1 Core class-size and summary metrics
  - Write `class_sizes(df, qis)` using `groupby(dropna=False)[qis[0]].transform("size")`, aligned to `df.index`.
  - Write `risk_summary(df, qis, k=5)` returning `n, n_classes, k_min, pct_unique, pct_below_k, avg_risk, max_risk` as plain int/float; ignore QI names absent from `df.columns`; return a safe default for empty inputs.
  - _Requirements: 2.1, 2.2, 2.3, 2.4_
- [x] 2.2 Combination, group, metadata, and l-diversity reports
  - Write `riskiest_combos(df, qis, max_size=3, k=5)` → DataFrame `combo, size, pct_unique, pct_below_k`, sorted descending.
  - Write `risk_by_group(df, qis, group_col, k=5)` → DataFrame `group, n, pct_unique, pct_below_k` (`dropna=False`).
  - Write `metadata_leaks(df, cols, combos, k=5)` → DataFrame `fields, pct_unique, pct_below_k`.
  - Write `l_diversity_report(df, qis, sensitive_cols)` → DataFrame `sensitive, l_min, pct_classes_l1`, using classes of size ≥ 2 and ignoring classes where nobody answered.
  - _Requirements: 2.5, 2.6, 2.7, 2.8_

- [x] 3. Implement attacker personas and the linkage attack (`reid/attacks.py`)
  - Write `make_attacker_table(original_df, known_cols, n=200, seed=42)` → `row_id` + present known cols, `random_state=seed`.
  - Write `persona_risk(df, personas, k=5)` → DataFrame `persona, fields, pct_unique, pct_below_k`.
  - Write `linkage_attack(release_df, attacker_df, known_cols, transform=None)`: apply `transform` to the attacker table, match on surviving cols with NaN-matches-NaN, count unique matches and correct re-identifications; return `n_targets, cols_used, n_unique_match, n_correct, unique_match_rate, correct_rate`.
  - _Requirements: 3.1–3.6_

- [x] 4. Implement `scripts/build_cache.py`
  - Build and write the clean parquet, print its shape.
  - Build and write the planted/truth parquets when `reid/plant.py` is available; skip gracefully (no crash) when it is not.
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 5. Implement the Role A section of `scripts/run_experiments.py`
  - Load the planted parquet; compute core9/core8/extended14/with_metadata and write `baseline_risk.json`.
  - Write `combos.csv`, `leaks.csv`, `personas.csv`, `risk_by_group.csv`, `l_diversity.csv`.
  - Build and write the uniqueness `staircase.csv` for the opening chart.
  - Support `--skip-presidio` so the script runs before Role B adds detection.
  - _Requirements: 4.4, 4.5_

- [x] 6. Verify against the reference numbers (section 4) — `scripts/check_numbers.py`, 13/13 passed on real clean data
- [x] 6.1 Loading acceptance
  - Confirmed shape `(20731, 133)`, `ID` unique, `FTFY` present, `MAJsecond` only str/NaN, parquet reload 0.63 s.
  - _Requirements: 1 (verification)_
- [x] 6.2 Risk acceptance (±0.2 points)
  - 8 core → 67.80% / 89.87%; +FTFY unchanged; 14 fields → 73.87%; `logdate` 11.66%; `duration` 11.62%; `logdate+Class+affiliation` 22.89%; `riskiest_combos` 129 rows in 0.61 s. All within tolerance.
  - _Requirements: 2 (verification)_
- [x] 6.3 Attack acceptance (raw-data portion)
  - `everything` persona → 137/200 (68.5%) correct on raw. Persona risk: classmate 0.99%, club_roster 0.53%, linkedin 25.97%, survey_insider 22.89%, everything 67.80%. All match.
  - Pending: 0% re-id on the mitigated release with `transform` — needs Role B's `plant.py` + `mitigate.py`. `check_numbers.py` auto-runs this once `nsse_planted.parquet` exists.
  - _Requirements: 3 (verification)_

- [ ] 7. Produce pitch charts (`notebooks/results.ipynb`, `results/charts/`)
  - Save PNGs for: uniqueness staircase, riskiest-pairs heatmap (size 2), persona risk bars, attack before/after (protect_on), risk by group.
  - Every chart: text labels on bars, percentage formatting, `px.colors.qualitative.Safe`, finding-first titles.
  - _Requirements: 5.1, 5.2_

- [ ] 8. Share caches and post numbers to the team
  - Send `nsse_clean.parquet`, `nsse_planted.parquet`, `pii_truth.parquet` to B and C privately (never via Git).
  - Post % unique (8, 14, with metadata), metadata leaks, persona numbers, attack before/after, top 3 riskiest pairs, risk by group.
  - Confirm `data/` and `keys/` are not staged before any push.
  - _Requirements: 6.1, 6.2, 6.4_
