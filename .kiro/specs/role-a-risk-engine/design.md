# Design: Role A — Data, Risk Engine, and Attacks

## Overview

Role A is a small set of pure-function modules plus two driver scripts and a notebook. The design follows the tested reference implementation in Appendix A of the brief verbatim; this document explains the structure, data flow, and the reasoning behind the key decisions so a reviewer can follow the code at any depth.

The guiding principle: **functions are pure and return JSON-serializable primitives.** That lets Role C call them from both the Streamlit app and the AI agent without any wrapping, and lets Role A persist every result as small JSON/CSV files the app reads directly.

## Architecture

```
data/NSSE-synthetic.xlsx  (BU synthetic, not committed)
        │
        ▼
reid/load.py ──► data/nsse_clean.parquet  (cached; row_id added; FTFY renamed)
        │
        ├────────────────► reid/plant.py (Role B) ──► nsse_planted.parquet + pii_truth.parquet
        │
        ▼
reid/risk.py   ── k-anonymity, % unique, riskiest combos, metadata leaks, l-diversity, risk-by-group
        │
        ▼
reid/attacks.py ── attacker personas, linkage attack (before / after, with transform)
        │
        ├──► scripts/build_cache.py      (xlsx → parquets, once)
        ├──► scripts/run_experiments.py  (Role A section → results/*.json|csv)
        └──► notebooks/results.ipynb     (results/ → results/charts/*.png)
```

Role A consumes `reid/config.py` (Role C) for configuration and, in the experiment script, `reid/mitigate.py` and `reid/utility.py` (Role B) for the before/after sections. Those cross-role calls use only the section 7 contracts.

## Components and interfaces

### reid/load.py

Responsible for turning the slow, messy xlsx into a fast, canonical parquet.

```python
load_raw(cfg) -> DataFrame            # sheet "in"; FTFY rename; MAJsecond->str; logdate datetime; row_id first
build_clean_cache(cfg) -> DataFrame   # writes data/nsse_clean.parquet
load_clean(cfg) -> DataFrame          # read parquet, building it if missing
load_lookup(cfg) -> {field: {int code: name}}
```

**Design decisions:**
- `row_id` is prepended with `pd.concat([pd.Series(range(len(df)), name="row_id"), df], axis=1)` so it is always column 0 and reflects original order. It exists only so experiments can check identity in attacks; it is dropped from any released file.
- `MAJsecond` is cast with `.where(isna, astype(str))` so genuine `NaN` stays `NaN` while `-9` and real codes become strings. This respects the data quirk that `-9` ("no second major") is a real category, not missing.
- The parquet cache exists because reading the xlsx with openpyxl takes ~17 s vs. under 2 s for parquet. `load_clean` is the function every other module and the app should call.

### reid/risk.py

The quantitative heart. Every metric is derived from equivalence-class sizes.

```python
class_sizes(df, qis) -> Series                 # transform("size") with dropna=False
risk_summary(df, qis, k=5) -> dict             # n, n_classes, k_min, pct_unique, pct_below_k, avg_risk, max_risk
riskiest_combos(df, qis, max_size=3, k=5) -> DataFrame
risk_by_group(df, qis, group_col, k=5) -> DataFrame
metadata_leaks(df, cols, combos, k=5) -> DataFrame
l_diversity_report(df, qis, sensitive_cols) -> DataFrame
```

**Design decisions:**
- `class_sizes` uses `groupby(qis, dropna=False)[qis[0]].transform("size")` so the result is aligned to `df.index` and every row carries its class size. `dropna=False` is essential: without it, students with a missing major silently vanish and risk is understated.
- `risk_summary` filters `qis` to those present in `df.columns` first. This single guard lets the same function run on a full dataset and on a generalized release where columns were dropped, which the agent and attack code rely on.
- Metrics map directly to standard definitions: `pct_unique` = share in classes of size 1; `pct_below_k` = share in classes smaller than k; `avg_risk` = mean of 1/size (equals n_classes/n); `max_risk` = 1/min size (prosecutor risk).
- `riskiest_combos` enumerates `combinations(qis, r)` for r in 1..max_size. With 9 QIs and max_size 3 that is 129 combinations, each a cheap groupby, completing in under 2 s.
- `l_diversity_report` restricts to classes of size ≥ 2 (a singleton trivially has l=1) and drops classes where `nunique` is 0 (nobody answered that item), so the l_min reflects real attribute diversity.

### reid/attacks.py

Models adversaries and a join-based linkage attack.

```python
make_attacker_table(original_df, known_cols, n=200, seed=42) -> DataFrame
persona_risk(df, personas, k=5) -> DataFrame
linkage_attack(release_df, attacker_df, known_cols, transform=None) -> dict
```

**Design decisions:**
- `make_attacker_table` fixes `random_state=seed` so the 200 target students are reproducible across runs and across before/after comparisons.
- `linkage_attack` applies `transform` (the generalization callable from Role B's mitigation) to the attacker's *raw* knowledge before matching. This is the correct threat model: the attacker knows raw facts, and we coarsen them the same way the release was coarsened, then join.
- Matching uses a string "keyify" step that collapses `NaN`, `NaT`, and `None` to a single `__NA__` token so that missing-matches-missing joins work and dtype differences do not break the join.
- A target is **uniquely matched** when exactly one release row shares its key (`_n == 1`) and **correctly re-identified** when that row's `row_id` equals the target's `row_id`. Reporting both `unique_match_rate` and `correct_rate` separates "looks identified" from "actually identified."

### scripts/build_cache.py

Builds the clean parquet always; builds the planted/truth parquets when Role B's `plant.py` exists. The `try/except ImportError` around the plant import means Role A is never blocked waiting on Role B — a deliberate deviation from the bare reference that keeps the build runnable mid-hackathon.

### scripts/run_experiments.py (Role A section)

Writes the result files the app and pitch read: `baseline_risk.json` (core9/core8/extended14/with_metadata), `combos.csv`, `leaks.csv`, `personas.csv`, `risk_by_group.csv`, `l_diversity.csv`, and `staircase.csv` (uniqueness as fields are added — the opening chart). The Role B section (mitigation, attack before/after, fairness, utility, curve, detection) is added by Role B into the same script.

### notebooks/results.ipynb

Reads `results/*` and renders five Plotly charts to `results/charts/*.png` using `px.colors.qualitative.Safe` (colorblind-safe), `text_auto` labels, percentage tick formatting, and finding-first titles. PNG export needs `kaleido`; screenshots are the fallback.

## Data models

**Clean DataFrame:** `(20731, 133)` — the 132 source columns plus `row_id`. Conventions: `FTFY` present, `MAJsecond` str/NaN, `-9` preserved, `logdate` datetime, missing values as NaN.

**risk_summary dict:**
```
{n: int, n_classes: int, k_min: int, pct_unique: float,
 pct_below_k: float, avg_risk: float, max_risk: float}
```

**linkage_attack dict:**
```
{n_targets: int, cols_used: list[str], n_unique_match: int,
 n_correct: int, unique_match_rate: float, correct_rate: float}
```

**Quasi-identifier sets (from config.yaml):**
- core9 = `quasi_ids` = Year, Class, program, FTFY, affiliation, MAJfirstcode, MAJsecondcode, begincol, edaspire
- core8 = core9 minus FTFY
- extended14 = core9 + attend_voc, attend_com, attend_col, attend_none, attend_other
- metadata = logdate, duration

## Error handling

- `risk_summary` returns a safe default dict for empty QI lists or empty DataFrames instead of raising, so the agent's iterative generalization (which can drop all QIs) never crashes.
- `linkage_attack` returns zeroed counts when no known columns survive in the release.
- `build_cache.py` degrades gracefully when `plant.py` is absent.
- All group-bys use `dropna=False`; missing values are a valid group everywhere.

## Testing strategy

Primary verification is **reproducing the reference numbers in section 4** on the real data (Tasks A2, A3 acceptance criteria), within ±0.2 points. Because the real data is shared privately and may not be present on every machine, the modules are also exercised against a small synthetic stand-in DataFrame with the same column names and quirks (`-9`, NaN, datetime `logdate`) to confirm they import and run, that `dropna=False` keeps missing-value rows, and that `linkage_attack` with a `transform` returns the expected keys. The end-to-end integration check is Role C's `scripts/smoke_test.py`, which runs the full agent on a 3,000-row sample and asserts `k_min >= 5`, zero uniqueness after, and no PII columns in the release.

## Deviations from the reference implementation

1. `scripts/build_cache.py` wraps the `reid.plant` import in `try/except ImportError` so Role A can build the clean parquet before Role B finishes `plant.py`. Behavior is identical to the reference once `plant.py` exists.

All other modules follow Appendix A exactly, since that code was tested on the real dataset and the interface contracts in section 7 must not change.
