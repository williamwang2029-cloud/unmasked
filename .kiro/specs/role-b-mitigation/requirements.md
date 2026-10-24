# Requirements Document

## Introduction

Role B of the *Unmasked: Re-identification Risk Meter* project owns the data-mitigation half of
the privacy pipeline. These requirements are derived from the approved design document
(`design.md`) and the interface contracts in section 7 of the Role B brief. They cover **only**
Role B's seven deliverables: `hierarchies.yaml`, `reid/plant.py`, `reid/pii_text.py`,
`reid/tokens.py`, `reid/mitigate.py`, `reid/utility.py`, and the Role B sections of
`scripts/run_experiments.py`. All other modules (`config.py`, `load.py`, `risk.py`, `attacks.py`,
`llm.py`, `classify.py`, `agent.py`, `app.py`) are owned by Roles A and C and are consumed as
external interfaces.

The task is to recreate working code that matches the reference implementation in Appendix B of
the brief exactly, run it, and verify the output against the documented acceptance numbers — not
to redesign working code. The requirements are ordered to support the requested build sequence:
(1) planted identifiers, (2) hierarchies and mitigation, (3) tokenization, (4) PII detection,
(5) utility and fairness evaluation, (6) the experiment runner.

## Glossary

- **Plant_Module**: `reid/plant.py`, which adds synthetic identifiers and a ground-truth span table.
- **Hierarchies_File**: `hierarchies.yaml`, the declarative generalization ladder for each column.
- **Mitigation_Module**: `reid/mitigate.py`, the hierarchy loader and greedy k-anonymity optimizer.
- **Tokens_Module**: `reid/tokens.py`, the reversible HMAC + Fernet tokenization vault.
- **PII_Module**: `reid/pii_text.py`, the Presidio + optional LLM detection, scrubbing, and scoring.
- **Utility_Module**: `reid/utility.py`, the utility, fairness, and privacy-utility-curve evaluation.
- **Experiment_Runner**: the Role B sections of `scripts/run_experiments.py`.
- **row_id**: integer column (0..n-1, original order) added by `load.py`; used only for identity joins and never exported.
- **Quasi-identifier (QI)**: a field harmless alone but identifying in combination.
- **Equivalence class**: all records with identical QI values; its **class size** is the record count.
- **k-anonymity**: every equivalence class has size at least k (default k=5).
- **% unique**: share of records in classes of size 1.
- **Suppression**: removing records still in classes below k after generalization.
- **Generalization level**: an index into a column's hierarchy; level 0 is identity, the last level is `drop`.
- **Derived column**: a major column (`MAJfirst`, `MAJsecond`, `MAJfirstcol`, `MAJsecondcol`, `MAJnum`) dropped in lockstep with its source code column.
- **Truth table (`truth_df`)**: ground-truth PII spans with columns `row_id, entity_type, value, start, end`.
- **Entity type**: one of `PERSON`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `BU_ID`.
- **Join token**: a deterministic HMAC-SHA256 hex token (first 16 chars) that lets tokenized datasets still be joined.
- **Vault**: a per-column CSV (`keys/vault_<col>.csv`) mapping tokens to Fernet-encrypted originals.
- **protect_on / protect_off**: mitigation modes; `protect_on` never generalizes the group column and caps per-group suppression, `protect_off` applies no such constraint.
- **Protected value**: `-9`, a valid category meaning "not applicable", never treated as missing.

## Requirements

### Requirement 1: Planted Identifiers and Ground Truth

**User Story:** As a Role B developer, I want to plant synthetic identifiers and a ground-truth span table into the clean dataset, so that PII detection can be scored against known answers.

#### Acceptance Criteria

1. THE Plant_Module SHALL expose `plant_identifiers(df, seed=42, pct_pii=0.30, pct_decoy=0.10)` returning the tuple `(planted_df, truth_df)`.
2. WHEN `plant_identifiers` is called, THE Plant_Module SHALL add the columns `full_name`, `email`, `student_id`, and `comment` to `planted_df`.
3. THE Plant_Module SHALL format `email` as first-initial plus last-name plus a number from 1 to 99 followed by `@bu.edu`, and SHALL format `student_id` as `"U"` followed by 8 digits.
4. WHEN generating comments, THE Plant_Module SHALL produce approximately 30 percent PII-bearing comments, approximately 10 percent decoy comments, and approximately 60 percent clean comments, governed by `pct_pii` and `pct_decoy`.
5. THE Plant_Module SHALL emit `truth_df` with exactly the columns `row_id`, `entity_type`, `value`, `start`, and `end`, where `entity_type` is one of `PERSON`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, or `BU_ID`.
6. FOR ALL rows in `truth_df`, THE Plant_Module SHALL guarantee that `planted_df` joined on `row_id` satisfies `comment[start:end] == value`, producing 0 span errors.
7. WHEN `plant_identifiers` is called with a fixed `seed`, THE Plant_Module SHALL produce identical `planted_df` and `truth_df` across runs.

### Requirement 2: Generalization Hierarchies

**User Story:** As a Role B developer, I want a declarative generalization hierarchy for every quasi-identifier and metadata column, so that mitigation can coarsen data in consistent, auditable steps.

#### Acceptance Criteria

1. THE Hierarchies_File SHALL define an ordered list of levels for every quasi-identifier and metadata column, where level 0 is identity.
2. THE Hierarchies_File SHALL set the last level of every column to the `drop` rule type.
3. THE Hierarchies_File SHALL support the rule types `identity`, `map`, `map_other`, `from_column`, `has_value`, `month`, `year`, `bins`, and `drop`.
4. THE Hierarchies_File SHALL include a `derived:` section that lists, for each source code column, the minimum source level at which each derived major column is dropped.
5. THE Hierarchies_File SHALL use the keys `label_yes` and `label_no` rather than `yes` and `no`, and SHALL express large numeric bin edges as plain integers rather than exponential notation, to avoid PyYAML coercion.

### Requirement 3: Hierarchy Application and Greedy Mitigation

**User Story:** As a Role B developer, I want a greedy k-anonymity optimizer that applies generalization levels and suppresses the remainder, so that the released dataset meets a target k with minimal information loss.

#### Acceptance Criteria

1. THE Mitigation_Module SHALL expose `load_hierarchies(path="hierarchies.yaml")`, `max_level(col)`, `apply_levels(df, levels)`, `make_transform(levels)`, `suppress(df, qis, k)`, and `greedy_generalize(df, qis, k=5, max_suppression=0.05, max_group_suppression=None, group_col="affiliation", protect=(), must_keep=())`.
2. WHEN a column reaches its `drop` level, THE Mitigation_Module SHALL remove that column from the output of `apply_levels`.
3. WHEN a source code column reaches the level listed in the `derived:` section, THE Mitigation_Module SHALL remove the corresponding derived columns from the output of `apply_levels` in lockstep.
4. WHERE a column in `levels` is not present in the input frame, THE Mitigation_Module SHALL skip that column without error.
5. WHEN a column's generalization level increases, THE Mitigation_Module SHALL produce an output whose distinct-value count for that column does not increase.
6. WHEN `suppress(df, qis, k)` returns, THE Mitigation_Module SHALL ensure every equivalence class in the kept frame over the present `qis` has size at least k, and SHALL return a suppression mask aligned to the input index.
7. WHILE the stop condition is unmet, THE Mitigation_Module SHALL, at each step, select the non-protected column whose one-level increase yields the best gain-per-cost, where dropping a column costs 2 and coarsening costs 1.
8. WHERE a column is listed in `must_keep`, THE Mitigation_Module SHALL cap its generalization at level 1.
9. THE Mitigation_Module SHALL stop generalizing when overall below-k is at most `max_suppression` and, where `max_group_suppression` is set, every group's below-k is at most `max_group_suppression`.
10. IF no column can advance before the target is met, THEN THE Mitigation_Module SHALL stop and suppress the remainder, recording the shortfall in `steps` and `final_risk`.
11. THE Mitigation_Module SHALL return a dict with the keys `levels`, `release_df`, `suppressed_mask`, `steps`, `final_risk`, `active_qis`, and `transform`, where `release_df` retains `row_id`.
12. WHEN run in protect-on mode on 14 quasi-identifiers plus 2 metadata columns at k=5 with `max_suppression=0.05`, THE Mitigation_Module SHALL remove approximately 2.5 percent of records, achieve 0 percent unique, keep the `affiliation` column, and produce per-group removal ranging from approximately 6.9 percent (Diademed sifaka) down to approximately 0.9 percent (Ring-tailed lemur).
13. WHEN run in protect-off mode on the same inputs, THE Mitigation_Module SHALL remove approximately 3.5 percent of records and drop the `affiliation` column.
14. THE Mitigation_Module SHALL complete a single mitigation run on the 20,731-row dataset within approximately 5 seconds.

### Requirement 4: Reversible Tokenization Vault

**User Story:** As a Role B developer, I want deterministic join tokens and a reversible per-column vault, so that direct identifiers can be pseudonymized while still allowing joins and authorized re-linking.

#### Acceptance Criteria

1. THE Tokens_Module SHALL expose `ensure_keys(keys_dir="keys")`, `join_token(value)`, `tokenize_column(df, col, vault_path=None)`, and `detokenize(token, col, vault_path=None)`.
2. WHEN `ensure_keys` is called, THE Tokens_Module SHALL create `keys/vault.key` with a Fernet key and, unless the `JOIN_KEY` environment variable is set, SHALL create `keys/join.key`.
3. THE Tokens_Module SHALL compute `join_token(value)` as an HMAC-SHA256 digest of the value under the join key, rendered as hexadecimal and truncated to the first 16 characters.
4. WHEN `join_token` is given equal inputs under the same join key, THE Tokens_Module SHALL return equal tokens, so that tokenized datasets can be joined.
5. WHEN `tokenize_column(df, col)` is called, THE Tokens_Module SHALL replace `col` with join tokens and write a deduplicated per-column vault `keys/vault_<col>.csv` with columns `token` and `encrypted_value` holding the Fernet-encrypted originals.
6. WHEN `detokenize(tokenize_column(df, "student_id").student_id[0], "student_id")` is evaluated, THE Tokens_Module SHALL return the original `student_id` value.
7. IF `detokenize` is given a token absent from the vault, THEN THE Tokens_Module SHALL raise `KeyError("token not found")`.
8. THE Tokens_Module SHALL store the vault key in `keys/`, which SHALL be excluded from version control.

### Requirement 5: PII Detection, Scrubbing, and Scoring

**User Story:** As a Role B developer, I want Presidio and optional LLM detection with scoring against ground truth, so that I can report how well planted PII is caught and scrub it from released text.

#### Acceptance Criteria

1. THE PII_Module SHALL define `ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "BU_ID"]` and SHALL return only these entity types from detection.
2. THE PII_Module SHALL expose `presidio_detect(text, threshold=0.4)`, `llm_detect(text)`, `combine(a, b)`, `scrub_text(text, method="presidio", spans=None)`, and `evaluate_detection(truth_df, predictions)`.
3. THE PII_Module SHALL configure Presidio with the `en_core_web_sm` spaCy model and a custom `BU_ID` recognizer using the regex `\bU\d{8}\b` with score 0.9.
4. IF the LLM is disabled or returns a non-list, THEN THE PII_Module SHALL return an empty list from `llm_detect`.
5. WHEN `llm_detect` is used, THE PII_Module SHALL send only synthetic planted comments to the LLM and SHALL map returned entity-text pairs to spans via substring search.
6. WHEN `combine(a, b)` is called, THE PII_Module SHALL return the union of spans de-overlapped so that the highest-scoring span wins.
7. WHEN `scrub_text` is applied, THE PII_Module SHALL replace each detected span with `<ENTITY_TYPE>`.
8. WHEN `evaluate_detection` scores predictions, THE PII_Module SHALL count a prediction as a true positive if and only if an unmatched truth entity shares its entity type and overlaps its span, matching each truth entity at most once, and SHALL score only rows present in `predictions`.
9. THE PII_Module SHALL return from `evaluate_detection` one row per entity type plus an `ALL` row, with columns `tp`, `fp`, `fn`, `precision`, `recall`, and `f1`.
10. WHEN detection runs on planted comments, THE PII_Module SHALL achieve near 100 percent precision and recall for `EMAIL_ADDRESS` and `BU_ID` entities.

### Requirement 6: Utility, Fairness, and Privacy-Utility Curve

**User Story:** As a Role B developer, I want utility, fairness, and privacy-utility-curve measurements, so that the pitch can show exactly what the privacy fix costs and which groups pay most.

#### Acceptance Criteria

1. THE Utility_Module SHALL expose `group_means(df, scales, by)`, `utility_report(original_df, release_df, scales, by_list, levels=None)`, `ml_utility(original_df, release_df, transform, target="SE", exclude=(), seed=42)`, `fairness_report(df, suppressed_mask, group_col="affiliation")`, and `privacy_utility_curve(df, qis, scales, by_list, ks=(2,3,5,10), **greedy_kwargs)`.
2. WHEN `utility_report` computes shifts, THE Utility_Module SHALL draw group labels from `original_df` joined on `row_id`, so that the shift measures distortion from suppression.
3. THE Utility_Module SHALL set `analysis_status[by]` to `lost` when the grouping column is absent from the release, `coarsened` when it was generalized, and `available` otherwise.
4. WHEN `ml_utility` runs, THE Utility_Module SHALL train a `HistGradientBoostingRegressor` to predict `SE`, excluding `SE*` item columns, `row_id`, `ID`, metadata, and planted columns, and SHALL test both the original and release models on the same held-out original rows generalized through `transform` for the release model.
5. WHEN `ml_utility` runs on the reference dataset, THE Utility_Module SHALL report an original R² of approximately 0.42 against a release R² of approximately 0.37 in protect-on mode and approximately 0.41 in protect-off mode.
6. THE Utility_Module SHALL return from `fairness_report` the columns `group`, `n`, `n_suppressed`, and `pct_suppressed`, giving the share of each group's records removed.
7. WHEN `privacy_utility_curve` is called, THE Utility_Module SHALL run the optimizer at k values 2, 3, 5, and 10 and return one row per k with `pct_suppressed`, `pct_unique_after`, `n_qis_dropped`, `analyses_lost`, `max_abs_shift`, and `mean_abs_shift`.

### Requirement 7: Experiment Runner (Role B Sections)

**User Story:** As a Role B developer, I want the Role B sections of the experiment runner to write the result files, so that the Streamlit app and the pitch can read precomputed outputs.

#### Acceptance Criteria

1. WHEN `scripts/run_experiments.py` runs, THE Experiment_Runner SHALL run mitigation in both `protect_on` and `protect_off` modes and write `results/attack.json`, `results/fairness.csv`, `results/mitigation_summary.json`, and `results/curve.csv`.
2. THE Experiment_Runner SHALL drop the planted columns from the working frame before mitigation.
3. THE Experiment_Runner SHALL write `results/fairness.csv` with a `setting` column distinguishing `protect_on` from `protect_off`, and SHALL write `results/attack.json` as `{mode: {persona: {before, after}}}`.
4. WHERE the `--skip-presidio` flag is supplied, THE Experiment_Runner SHALL skip PII detection and omit `results/detection.csv`.
5. WHERE PII detection runs, THE Experiment_Runner SHALL write `results/detection.csv` with the methods `presidio`, `presidio_same_sample`, `llm`, and `combined`, running Presidio on a 1,500-comment sample and the LLM on a 200-comment sample.

### Requirement 8: Interface Contract Conformance

**User Story:** As a team member depending on Role B modules, I want every Role B interface to match section 7 exactly, so that the other roles' modules integrate without changes.

#### Acceptance Criteria

1. THE Plant_Module, Hierarchies_File, PII_Module, Tokens_Module, Mitigation_Module, Utility_Module, and Experiment_Runner SHALL match the section 7 interface contracts exactly for function names, argument names, default values, return types, and column names.
2. THE Role B modules SHALL never include `row_id` in any released or exported file.
3. WHEN grouping records, THE Role B modules SHALL use `dropna=False`, so that missing values form their own group.
4. THE Role B modules SHALL treat `-9` as a valid category rather than a missing value.
5. THE Role B modules SHALL read cached parquet data rather than the source xlsx.

### Requirement 9: Ethics and Safety Constraints

**User Story:** As a responsible-innovation reviewer, I want the ethics and safety rules enforced in code and configuration, so that the tool handles data responsibly.

#### Acceptance Criteria

1. THE Role B modules SHALL operate only on synthetic data, and planted identifiers SHALL be labeled as synthetic.
2. THE Role B modules SHALL send no row-level student data to any LLM, with the single exception of synthetic planted comments passed to `llm_detect`.
3. THE Tokens_Module SHALL store the vault key in `keys/`, separate from the released dataset, and `keys/`, `data/`, and `.env` SHALL be excluded from version control.
4. THE Role B deliverables SHALL characterize tokenized data as pseudonymous rather than anonymous.
