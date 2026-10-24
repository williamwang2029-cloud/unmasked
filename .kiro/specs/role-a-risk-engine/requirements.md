# Requirements: Role A — Data, Risk Engine, and Attacks

## Introduction

Role A owns the data foundation and the quantitative core of **Unmasked: Re-identification Risk Meter**, a tool that measures how easily students in a "de-identified" survey file can still be singled out, then feeds those measurements to the mitigation (Role B), the agent and app (Role C), and the pitch.

The dataset is BU-provided synthetic NSSE survey data (20,731 rows × 132 columns). It has no real names or emails; Role B plants fake identifiers so detection can be scored. Role A is responsible for: loading and caching the data, computing re-identification risk metrics (k-anonymity, uniqueness, riskiest column combinations, metadata leaks, l-diversity, risk by demographic group), modeling attacker personas and a linkage attack, and producing the experiment outputs and charts that anchor the headline numbers.

Role A functions are pure and JSON-serializable so the Streamlit app and the AI agent can call them directly. The interface contracts in section 7 of the brief are fixed: Roles B and C depend on exact file names, function names, arguments, return keys, and column names.

### Scope

**In scope (Role A owns):** `reid/load.py`, `reid/risk.py`, `reid/attacks.py`, `scripts/build_cache.py`, the Role A section of `scripts/run_experiments.py`, `notebooks/results.ipynb`, and `results/charts/`.

**Out of scope (owned by B/C, consumed here):** `reid/plant.py`, `reid/mitigate.py`, `reid/utility.py` (Role B); `reid/config.py`, `reid/llm.py`, `reid/classify.py`, `reid/agent.py`, `app.py` (Role C).

### Non-functional constraints

- Python 3.11+, pandas, numpy, openpyxl, pyarrow, pyyaml.
- All group-bys use `dropna=False` (missing values are their own group).
- All returned numbers are plain Python `int`/`float` (JSON-serializable).
- Functions are pure: no prints, no globals, no mutation of inputs.
- Never commit `data/`. Never send row-level student data to an LLM.
- Reference numbers in section 4 of the brief must be reproduced within ±0.2 percentage points.

---

## Requirements

### Requirement 1: Load and cache the raw survey data

**User story:** As a teammate on Roles B and C, I want a single clean, cached DataFrame with stable conventions, so that every downstream module reads identical data quickly.

#### Acceptance criteria

1. WHEN `load_raw(cfg)` runs THEN THE SYSTEM SHALL read sheet `in` of the configured raw xlsx.
2. WHEN `load_raw(cfg)` runs THEN THE SYSTEM SHALL rename column `First Time First Year` to `FTFY`.
3. WHEN `load_raw(cfg)` runs THEN THE SYSTEM SHALL cast `MAJsecond` to `str` while leaving `NaN` as `NaN`, and SHALL preserve `-9` as a valid value.
4. WHEN `load_raw(cfg)` runs THEN THE SYSTEM SHALL parse `logdate` as a datetime.
5. WHEN `load_raw(cfg)` runs THEN THE SYSTEM SHALL insert `row_id` (integers `0..n-1`, original row order) as the first column.
6. WHEN `build_clean_cache(cfg)` runs THEN THE SYSTEM SHALL write the clean DataFrame to `data/nsse_clean.parquet`, creating the parent directory if needed, and SHALL return the DataFrame.
7. WHEN `load_clean(cfg)` runs AND `data/nsse_clean.parquet` exists THEN THE SYSTEM SHALL read and return it.
8. WHEN `load_clean(cfg)` runs AND the parquet is missing THEN THE SYSTEM SHALL build it via `build_clean_cache`.
9. WHEN `load_lookup(cfg)` runs THEN THE SYSTEM SHALL return a mapping `{field: {int code: meaning}}` from the lookup xlsx.

**Verification (section A2, Task A1):** shape `(20731, 133)`; `ID` unique; `FTFY` present; `MAJsecond` contains only `str` and `NaN`; the parquet reloads in under 2 seconds.

### Requirement 2: Compute re-identification risk metrics

**User story:** As a data owner, I want to know how many students are uniquely identifiable and which field combinations drive the risk, so that I can judge whether a release is safe.

#### Acceptance criteria

1. WHEN `class_sizes(df, qis)` runs THEN THE SYSTEM SHALL return a Series aligned to `df.index` giving each row's equivalence-class size, using `groupby(dropna=False)`.
2. WHEN `risk_summary(df, qis, k)` runs THEN THE SYSTEM SHALL return a dict with keys `n`, `n_classes`, `k_min`, `pct_unique`, `pct_below_k`, `avg_risk`, `max_risk`, all JSON-serializable.
3. WHEN `risk_summary` receives QI names not present in `df.columns` THEN THE SYSTEM SHALL ignore the missing names and compute on the remainder.
4. WHEN `risk_summary` receives an empty QI list or empty DataFrame THEN THE SYSTEM SHALL return a safe default dict without error.
5. WHEN `riskiest_combos(df, qis, max_size, k)` runs THEN THE SYSTEM SHALL return a DataFrame with columns `combo`, `size`, `pct_unique`, `pct_below_k`, sorted by `pct_unique` then `pct_below_k` descending, covering all combinations from size 1 up to `max_size`.
6. WHEN `risk_by_group(df, qis, group_col, k)` runs THEN THE SYSTEM SHALL return a DataFrame with columns `group`, `n`, `pct_unique`, `pct_below_k` grouped with `dropna=False`.
7. WHEN `metadata_leaks(df, cols, combos, k)` runs THEN THE SYSTEM SHALL return a DataFrame with columns `fields`, `pct_unique`, `pct_below_k` for each single metadata column and each requested combo.
8. WHEN `l_diversity_report(df, qis, sensitive_cols)` runs THEN THE SYSTEM SHALL compute l-diversity using only classes with at least 2 records and SHALL ignore classes where nobody answered a given sensitive column, returning columns `sensitive`, `l_min`, `pct_classes_l1`.

**Verification (section A2, Task A2), within ±0.2 points:**
- 8 core fields (`Year, Class, program, affiliation, MAJfirstcode, MAJsecondcode, begincol, edaspire`) → 67.8% unique, 89.9% below k=5.
- Adding `FTFY` (9 core) changes nothing.
- 14 fields (core 9 + `attend_*`) → 73.9% unique.
- `logdate` alone 11.7% unique; `duration` alone 11.6% unique; `logdate + Class + affiliation` 22.9% unique.
- `riskiest_combos` on 9 QIs with `max_size=3` returns 129 rows in under 2 seconds.

### Requirement 3: Model attacker personas and a linkage attack

**User story:** As a data owner, I want to simulate realistic adversaries joining outside knowledge to a release, so that I can see how many students would actually be re-identified before and after mitigation.

#### Acceptance criteria

1. WHEN `make_attacker_table(original_df, known_cols, n, seed)` runs THEN THE SYSTEM SHALL sample `n` rows with `random_state=seed` and return `row_id` plus the subset of `known_cols` present in the data.
2. WHEN `persona_risk(df, personas, k)` runs THEN THE SYSTEM SHALL return a DataFrame with columns `persona`, `fields`, `pct_unique`, `pct_below_k`.
3. WHEN `linkage_attack(release_df, attacker_df, known_cols, transform)` runs AND `transform` is provided THEN THE SYSTEM SHALL apply `transform` to the attacker's table before matching, so raw knowledge is coarsened the same way as the release.
4. WHEN `linkage_attack` matches THEN THE SYSTEM SHALL use only known columns present in both the release and the transformed attacker table, SHALL treat `NaN` as a matchable value (NaN matches NaN), and SHALL count a target as re-identified only when exactly one release row matches and its `row_id` equals the target's.
5. WHEN no known columns survive in the release THEN THE SYSTEM SHALL return zero matches without error.
6. WHEN `linkage_attack` returns THEN THE SYSTEM SHALL provide keys `n_targets`, `cols_used`, `n_unique_match`, `n_correct`, `unique_match_rate`, `correct_rate`.

**Verification (section A2, Task A3):**
- Persona `everything` on raw data → 137 of 200 (68.5%) correctly re-identified.
- On Role B's mitigated release with `transform` → 0%.
- Persona risk on raw data: classmate 1.0%, club_roster 0.5%, linkedin 26.0%, survey_insider 22.9%, everything 67.8%.

### Requirement 4: Build caches and run experiments

**User story:** As the team, I want one command to build the data caches and another to produce every result file, so that the app and pitch read precomputed outputs.

#### Acceptance criteria

1. WHEN `scripts/build_cache.py` runs THEN THE SYSTEM SHALL build and write `data/nsse_clean.parquet` and print its shape.
2. WHEN `scripts/build_cache.py` runs AND `reid/plant.py` is available THEN THE SYSTEM SHALL build and write the planted parquet and the PII truth parquet.
3. WHEN `scripts/build_cache.py` runs AND `reid/plant.py` is NOT yet available THEN THE SYSTEM SHALL still build the clean parquet and report that planting was skipped, without crashing.
4. WHEN `scripts/run_experiments.py --skip-presidio` runs THEN THE Role A section SHALL write `baseline_risk.json`, `combos.csv`, `leaks.csv`, `personas.csv`, `risk_by_group.csv`, `l_diversity.csv`, and `staircase.csv` into `results/`.
5. WHEN the experiment script runs THEN the output files SHALL match the schemas in the section 7 results table.

### Requirement 5: Produce pitch charts

**User story:** As the presenter, I want saved, accessible charts of the headline findings, so that the demo communicates the risk clearly.

#### Acceptance criteria

1. WHEN `notebooks/results.ipynb` runs THEN THE SYSTEM SHALL save PNGs to `results/charts/` for: the uniqueness staircase, the riskiest-pairs heatmap, the persona risk bars, the attack before/after (protect_on mode), and risk by group.
2. WHEN a chart is produced THEN it SHALL include text labels on every bar, percentages formatted as percentages, a colorblind-safe palette, and a title that states the finding.

### Requirement 6: Ethics, safety, and interface stability

**User story:** As a responsible team, I want Role A to respect the project's privacy and contract rules, so that the tool is trustworthy and the modules integrate cleanly.

#### Acceptance criteria

1. THE SYSTEM SHALL NOT send any row-level student data to an LLM from Role A code.
2. THE SYSTEM SHALL NOT commit `data/` or any parquet caches to Git.
3. THE SYSTEM SHALL keep all Role A functions pure and free of side effects so the app and agent can call them.
4. THE SYSTEM SHALL NOT change the function names, arguments, return keys, or column names defined in the section 7 contracts without team agreement.
5. WHEN computing any grouped metric THE SYSTEM SHALL use `dropna=False` so students with missing values are not dropped.
