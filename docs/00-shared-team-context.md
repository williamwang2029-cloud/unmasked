# Unmasked (DS+X × Hackachusetts 2026): Shared Team Context

This is the shared context (sections 1–10) that also appears at the top of each role brief. Use it for Kiro steering files, team reference, or any AI session that needs the whole-project picture without a specific role.

Roles: **A** data, risk engine, attacks · **B** mitigation, tokens, PII detection, evaluation · **C** repo, Kiro, agent, app, submissions.

## How to use this file

This file is a complete, self-contained brief for one team member's part of a hackathon project. It is written to be pasted into an AI coding assistant (Kiro, Claude, or similar) at the start of a session.

**Instructions for the AI assistant reading this:**

- You are helping exactly one team member, whose role is described in the ROLE section near the end of this file. Build only the files that role owns.
- The other two roles are building the other modules in parallel. Follow the **interface contracts** in section 7 exactly (file names, function names, arguments, return types, column names). Do not rename or change them without the team agreeing, because the other modules depend on them.
- Use Python 3.11+, pandas, and the libraries listed in section 8. Keep code simple, readable, and runnable. Prefer working code over clever code.
- Never send row-level student data to an LLM (see section 9).
- Never commit data files, keys, or `.env` to Git.
- When unsure, choose the simplest approach that satisfies the acceptance criteria, and leave a `# TODO` note.
- **This file includes a reference implementation of the role's modules that was tested on the real dataset on Saturday.** Use it as the starting point: recreate the files (in Kiro, so Kiro is genuinely used to build), run them, check the results against the reference numbers in section 4, then improve. Do not rewrite working code from scratch.

---

## 1. Project summary

**Name (working):** Unmasked: Re-identification Risk Meter

**Hackathon:** BU Spark! DS+X Hackathon 2026, integrated with Hackachusetts 2026 (Mass AI Coalition). Track: CollegeHack. Challenge: BU IS&T "Data Scrubbing / Tokenization Tool" (category V4, Better College Experiences). Eligibility for Hackachusetts has been confirmed by organizers.

**Team size:** 3 people (Roles A, B, C).

**One-line pitch:** This survey file has no names, yet using eight ordinary fields, 68% of students can still be singled out. Our privacy agent finds that risk, fixes it, and shows exactly what the fix costs, including which students it costs most.

**What the challenge asks for (from BU IS&T):** a reusable tool to de-identify and tokenize datasets for student projects, applicable to any student data, built on provided synthetic data. Suggested outputs: a PII detector, a reversible-token demo with separate key storage, and a privacy risk report. Deliverables: synthetic-data demonstration, documented transformation pipeline, test results, or prototype. Suggested tools: Microsoft Presidio, spaCy, Faker. Difficulty: Advanced.

**What we are building (end to end):**

1. Load the synthetic NSSE survey dataset and plant fake identifiers (names, emails, student IDs, comments) so detection can be scored against ground truth.
2. An AI agent classifies each column's privacy role using metadata only.
3. Measure re-identification risk: k-anonymity, % unique, average risk, riskiest column combinations, metadata leaks, attacker personas, a simulated linkage attack, and risk by demographic group.
4. Mitigate: tokenize IDs (reversible vault with a separate key), scrub free text, generalize and suppress quasi-identifiers until a target k is met.
5. Verify and measure cost: re-run risk and the attack, measure utility loss (group means and an ML utility test), and measure suppression by group (fairness).
6. Report: the agent writes a plain-English privacy report and a one-card "privacy nutrition label"; the user downloads the safe dataset.

## 2. Hackathon requirements and deadlines

### Saturday, October 24 (build day)

| Time | Event |
|---|---|
| 11:15 and 1:15 | Kiro workshops, room B62 |
| 1:15–2:15 | Workshop "RAGs, MCPs & AI Agents", room 263 |
| 2:00 | Ethics Genius Bar opens (lower level) |
| 3:00 | Mentor stations open (lower level) |
| 6:30 | Dinner; Hackachusetts submission help |
| **8:00 PM** | **Hackachusetts hard deadline** (target 7:30) |
| **8:15 PM** | **Mandatory DS+X evening session, Room 164** (whole team) |
| **9:30 PM** | **DS+X Devpost project page must exist** |
| 10:00 PM | Sleeping rooms open; after 7 PM non-BU students cannot re-enter until 8 AM, after 10 PM BU students cannot re-enter |

### Sunday, October 25

| Time | Event |
|---|---|
| **11:00 AM** | **DS+X Devpost submission due; status must show "Submitted"** |
| 11:30–1:00 | DS+X presentations, **3 minutes per team**, hard limit |
| 11:00–2:00 | Hackachusetts finalist presentations at WHOOP HQ (only if selected; finalists notified around midnight). Overlaps DS+X presentations. |
| 2:45 | Closing ceremony and awards |

### Hackachusetts requirements

- Team of at most 4 (we have 3).
- **Kiro must be used to build the project.** Commit the `.kiro/` folder and mention Kiro in the README and video.
- Submit on the **Sundai portal** by 8:00 PM Saturday with a **GitHub repo + video demo**.
- .edu email and student ID; Sundai participation terms at tinyurl.com/sundaiterms.
- Judging guidelines: problem definition, innovation, technical implementation, **AI integration**, responsible innovation, real-world impact, Kiro integration. Judges review submissions (repo + video) Saturday 8–11 PM.
- Prizes per challenge area: $3,000 / $1,500 / $500.

### DS+X requirements

- Team of 3–5, every member listed on Devpost or they cannot win.
- All work created during the hackathon by the team. Open-source libraries, public datasets, AI tools allowed.
- Ethics and responsibility reflection is required for prizes.
- **Rubric:** Idea impact & relevance 25%; **Data science application 25%** (substantial dataset, at least one identifiable data science method, preprocessing, rigor, validation, interpretation); Technical implementation 20%; Design 10%; Responsibility & ethics 10%; Presentation 10%.
- **Important rule:** calling an API or LLM, installing a tool, or making charts without meaningful analysis does not, by itself, count as data science. Our data science must stand on its own without the LLM.
- Ethics principles emphasized: data privacy & security, fairness, transparency, human-centered, inclusion & accessibility.
- Prizes we target: HackCollege ($750 / $500 / $250), Top Overall ($1,000), BU Libraries Data Ethics & Data Literacy Prize ($500, judged on data science application and ethics).

### Team plan around the deadlines

- Hackachusetts version: features frozen at 5:30 PM, submitted by 7:30 PM, Git tag `hackachusetts-submission`.
- After 9:30 PM: polish and stretch features for the DS+X version only.

## 3. The data

Files (BU-provided synthetic data; keep out of Git; place in `data/`):

- `data/NSSE-synthetic.xlsx`: one sheet named `in`, **20,731 rows × 132 columns**. Reading it with openpyxl takes about 17 seconds, so convert it once to parquet (`data/nsse_clean.parquet`) and read the parquet afterward.
- `data/lookup-synthetic.xlsx`: one sheet named `in`, 206 rows, columns `field`, `value`, `meaning`. Maps `MAJfirstcol`/`MAJsecondcol` (12 fields) and `MAJfirstcode`/`MAJsecondcode` (91 specific majors) to names.

This is synthetic data modeled on the National Survey of Student Engagement (NSSE). Demographics are replaced by fictional categories (lemur species, whimsical majors).

### Key columns

| Column | Type | Values | Privacy role |
|---|---|---|---|
| `ID` | int | unique, 10000–99997 | **direct identifier** |
| `Year` | int | 2014, 2016, 2018, 2020, 2022, 2024 (counts 4556, 3878, 3217, 3276, 3786, 2018) | quasi-identifier |
| `Class` | str | FY 9926, SR 9452, Other 1353 | quasi-identifier |
| `program` | str | CLF 5548, LAG 4006, VAN 3858, HIG 3304, TSI 1904, MAN 1007, BAO 695, ZEB 409 (meaning unknown; asked IS&T) | quasi-identifier |
| `First Time First Year` | str | Y 11279, N 9452 | quasi-identifier (renamed to `FTFY` on load) |
| `affiliation` | str | Ring-tailed lemur 10460, Indri 3794, Aye-aye 1980, Golden bamboo lemur 1279, Crowned lemur 1208, Diademed sifaka 1146, Gray mouse lemur 864 | quasi-identifier and **demographic group for fairness analysis** (stand-in for a real demographic; meaning asked of IS&T) |
| `MAJfirstcode` | float | 1001–1091 (91 majors), 13% missing | quasi-identifier |
| `MAJsecondcode` | float | -9 = no second major (15090), 1001–1091, 13% missing | quasi-identifier |
| `MAJfirstcol`, `MAJsecondcol` | float | 21–32 (12 fields); -9 for no second major | derived from the codes |
| `MAJfirst`, `MAJsecond` | str/mixed | names like "Tea Sciences: Policy"; `MAJsecond` mixes int -9, str, NaN | derived (convert to str) |
| `MAJnum` | float | 1 or 2 majors | derived |
| `begincol` | float | 0/1, 14% missing | quasi-identifier |
| `edaspire` | float | 1–4 education aspiration, 14% missing | quasi-identifier |
| `attend_voc`, `attend_com`, `attend_col`, `attend_none`, `attend_other` | float | 0/1 prior institution attendance | extended quasi-identifiers (optional) |
| `logdate` | datetime | survey completion date, 2014-02-11 to 2024-05-12, 3406 distinct | **metadata (paradata) leak** |
| `duration` | float | minutes on survey; median 12.5, 75th pct 19.1, max 55995 (outliers) | **metadata leak** |
| `HO RI LS QR CL DD SF ET QI SE` | float | NSSE engagement indicator scores, 0–60 | **sensitive** (main utility targets) |
| ~100 item columns | float | e.g. `askquest`, `CLaskhelp`, `HOapply` (1–4 scales), `QIstudent`...`QIadmin` (1–7, **9 = not applicable**), `tm*` time use (1–8), `pg*` perceived gains (1–4), `evalexp`, `sameinst` | sensitive |

Major field names (`MAJfirstcol` → meaning): 21 Kite Studies, 22 Tea Sciences, 23 Lighthouse Engineering, 24 Puzzle Design, 25 Orchard Management, 26 Clockmaking, 27 Map Arts, 28 Weather Studies, 29 Bridge Sciences, 30 Lantern Studies, 31 Garden Logistics, 32 Wayfinding.

### Data quirks (all modules must respect these)

- `-9` means "not applicable" (for example, no second major). It is a **real category**, not missing.
- `MAJsecond` mixes int, str, and NaN; cast to str.
- Missing values in quasi-identifiers count as their own group (`groupby(..., dropna=False)`).
- `QI*` item values of 9 mean "not applicable"; treat as NaN only when computing averages of those items.
- `duration` has extreme outliers; band or cap it.
- No names, emails, IDs other than `ID`, or free text exist. Role B plants them (section 7, `plant.py`).
- Generalize derived major columns in lockstep with their codes, or the detail leaks back.

### Open questions sent to IS&T

1. Meaning of program codes. 2. What `affiliation` stands in for. 3. Location of the real data guide.

## 4. Preliminary findings (reproduce these; they anchor the pitch)

Computed with missing values as their own group, k = 5.

**Uniqueness as fields are combined:**

| Fields | % unique | % in group < 5 |
|---|---|---|
| Year + Class | 0.0% | 0.0% |
| + affiliation | 0.0% (smallest group: 3) | 0.0% |
| Year + Class + detailed first major | 1.0% | 5.7% |
| Year + Class + affiliation + first major | 10.3% | 33.0% |
| + program | 37.0% | 73.4% |
| + second major | 48.6% | 80.0% |
| + begincol + edaspire (8 core fields; adding FTFY changes nothing) | **67.8%** | **89.9%** |
| + 5 prior-attendance flags `attend_*` (14 fields) | **73.9%** | |
| + survey timing (`logdate`, `duration`) | **~100%** | |

**Metadata leaks:** `logdate` alone 11.7% unique; `duration` alone 11.6% unique; `logdate + Class + affiliation` 22.9% unique.

**Privacy-utility tradeoff (k = 5):**

| Release configuration | % unique | % suppressed |
|---|---|---|
| 9 core QIs raw | 67.8% | 89.9% |
| majors → field, second major → yes/no, edaspire → 2 bands, merge ZEB/BAO/MAN → OTHER | 27.1% | 60.3% |
| + Year → 3 bands, drop begincol and FTFY | 14.8% | 40.1% |
| year band + Class + program(merged) + affiliation + major field | 4.3% | 19.9% |
| same but affiliation merged (keep Ring-tailed, Indri, Aye-aye; rest → Other lemur) | 2.0% | 11.4% |
| Year + Class + affiliation + major field | 1.0% | 6.0% |
| **year band + Class + affiliation + major field** | **0.3%** | **2.3%** |

**Fairness finding:** in the best configuration, suppression by group is Gray mouse lemur 9%, Diademed sifaka 9%, Crowned lemur 7%, Golden bamboo lemur 6%, Aye-aye 4%, Indri 1%, Ring-tailed lemur 0%. On Year + Class + affiliation + program + first major (k=5), 98% of Gray mouse lemur and Crowned lemur students are at risk vs. 58% of Ring-tailed lemur. On all 9 core fields, 99% vs. 85%. Merging small groups shrinks the suppression gap but erases those groups' identity. **The smallest groups pay the highest price for privacy.** This is the project's most original insight.

### Reference implementation results (the code in these briefs, run on the real data)

Mitigation on 14 quasi-identifiers + 2 metadata columns, target k = 5, at most 5% of records removed, planted PII columns removed or tokenized:

| | Protect small groups ON (affiliation never generalized, max 10% removed per group) | Protect small groups OFF |
|---|---|---|
| Records removed | 2.5% | 3.5% |
| Unique after | 0% (every group ≥ 5) | 0% |
| What the optimizer gave up | program, first major, `Class`, begincol, edaspire, duration dropped; second major → yes/no; survey date → year | **affiliation dropped entirely**, first and second major dropped, edaspire, begincol, duration dropped; survey date → year |
| Analyses still possible | by Year and affiliation (by Class and major field lost) | by Year and Class (**by affiliation lost**) |
| Removed records by group | Diademed sifaka 6.9%, Gray mouse lemur 6.8%, Crowned 6.5%, Golden bamboo 5.9%, Aye-aye 3.6%, Indri 1.7%, Ring-tailed 0.9% | 3.0%–4.9%, roughly even |
| ML utility (predict SE score, R²) | 0.42 original → 0.37 release | 0.42 → 0.41 |
| Linkage attack, attacker knows all core fields (200 targets) | 68.5% re-identified before → 0% after | 68.5% → 0% |

**Pitch story from these numbers:** an unconstrained optimizer "solves" privacy by quietly deleting the demographic column, so the release looks fair but equity analysis becomes impossible. Protecting the group keeps those analyses possible, but then the smallest groups lose up to 8× more records than the largest. Our tool makes this tradeoff visible and lets the data owner choose.

Privacy-utility curve (protect OFF, max 5% removed):

| k | Records removed | Quasi-identifier columns dropped | Utility analyses lost (of 4) |
|---|---|---|---|
| 2 | 4.8% | 4 | 2 |
| 3 | 3.3% | 6 | 2 |
| 5 | 3.5% | 7 | 2 |
| 10 | 2.4% | 7 | 4 |

Higher k does not remove many more rows, because the optimizer drops more columns instead. Lost analyses, not lost rows, are the real cost; show that in the curve chart.

Persona risk on raw data (% unique): classmate 1.0%, club roster 0.5%, LinkedIn 26.0%, survey insider 22.9%, everything 67.8%. Runtime: greedy mitigation ~4–5 s, full agent ~10 s, all experiments ~50 s (without Presidio).

## 5. Key concepts

- **Direct identifier:** identifies a person alone (ID, name, email). Remove or tokenize.
- **Quasi-identifier (QI):** harmless alone, identifying in combination.
- **Equivalence class:** all records with identical QI values. **Class size** = number of records in it.
- **k-anonymity:** minimum class size is at least k. A class of size 1 = a unique student.
- **% unique:** share of records in classes of size 1. **% below k:** share in classes smaller than k.
- **Average risk:** mean of 1/class size = number of classes ÷ number of records. **Max (prosecutor) risk:** 1/min class size.
- **l-diversity:** each class has at least l distinct values of a sensitive attribute.
- **Generalization:** coarsen values using a hierarchy. **Suppression:** remove records still in classes below k.
- **Linkage attack:** an attacker with outside knowledge of some QIs (club roster, LinkedIn) joins it to the release; a target is exposed if they match exactly one released record, and the attack is correct if that record is truly theirs.
- **Pseudonymization:** reversible tokens; data remains sensitive because a key can re-link it.
- **FERPA anchor:** de-identification is judged by whether a reasonable person in the school community could identify a student with reasonable certainty (34 CFR §99.3). Many statisticians treat 3 as the minimum cell size; many education agencies suppress groups under 10.

## 6. Architecture

```
data/NSSE-synthetic.xlsx
  → load.py          clean + cache parquet, add row_id                        [A]
  → plant.py         add fake name/email/student_id/comment + truth table     [B]
  → classify.py      LLM labels column roles from metadata only               [C]
  → risk.py          k, % unique, combos, leaks, l-diversity, risk by group   [A]
  → attacks.py       personas, linkage attack before/after                    [A]
  → pii_text.py      Presidio + LLM detection, scrubbing, scoring             [B]
  → tokens.py        HMAC join tokens + Fernet vault, separate key           [B]
  → mitigate.py      hierarchies, greedy generalization, suppression          [B]
  → utility.py       group mean shifts, ML utility test, curve, fairness      [B]
  → agent.py         plan → act → verify loop, report + privacy label         [C]
  → app.py           Streamlit UI (6 screens)                                 [C]
```

## 7. Interface contracts (shared by all roles; do not change without team agreement)

### Repo layout and ownership

```
unmasked/                       (GitHub repo; C creates it)
├── .kiro/                      Kiro specs/steering (everyone; commit it)
├── .gitignore                  C: data/, keys/, .env, results/raw/, __pycache__/, *.parquet
├── .env.example                C: JOIN_KEY=, LLM_PROVIDER=none, LLM_MODEL=, ANTHROPIC_API_KEY=, OPENAI_API_KEY=
├── README.md                   C
├── requirements.txt            C (see section 8)
├── config.yaml                 C creates; all read
├── hierarchies.yaml            B
├── app.py                      C
├── reid/
│   ├── __init__.py             C
│   ├── config.py               C: load_config() -> dict
│   ├── load.py                 A
│   ├── risk.py                 A
│   ├── attacks.py              A
│   ├── plant.py                B
│   ├── pii_text.py             B
│   ├── tokens.py               B
│   ├── mitigate.py             B
│   ├── utility.py              B
│   ├── llm.py                  C
│   ├── classify.py             C
│   └── agent.py                C
├── scripts/
│   ├── build_cache.py          A: xlsx -> parquet (+ planted parquet via B's plant.py)
│   ├── run_experiments.py      A + B: writes results/*.json|csv
│   └── smoke_test.py           C: fast end-to-end integration check
├── notebooks/results.ipynb     A + B: charts for the pitch
├── results/                    precomputed outputs read by the app (small files; OK to commit)
├── data/                       NOT committed
└── keys/                       NOT committed
```

Each person edits only the files they own. Work on a branch per role (`role-a`, `role-b`, `role-c`) and merge into `main` at checkpoints.

### config.yaml (canonical content)

```yaml
data:
  raw_xlsx: data/NSSE-synthetic.xlsx
  lookup_xlsx: data/lookup-synthetic.xlsx
  clean_parquet: data/nsse_clean.parquet
  planted_parquet: data/nsse_planted.parquet
  truth_parquet: data/pii_truth.parquet
roles:
  direct_ids: [ID]
  quasi_ids: [Year, Class, program, FTFY, affiliation, MAJfirstcode, MAJsecondcode, begincol, edaspire]
  quasi_ids_extended: [attend_voc, attend_com, attend_col, attend_none, attend_other]
  metadata: [logdate, duration]
  derived_major: [MAJnum, MAJfirst, MAJsecond, MAJfirstcol, MAJsecondcol]
  sensitive_scales: [HO, RI, LS, QR, CL, DD, SF, ET, QI, SE]
  group_col: affiliation
  planted: [full_name, email, student_id, comment]
targets:
  k: 5
  max_suppression: 0.05
  max_group_suppression: 0.10
utility_analyses:          # group means of these scales by these columns
  scales: [HO, SF, QI, SE]
  by: [Class, affiliation, MAJfirstcol, Year]
personas:
  classmate: [Year, Class, MAJfirstcode]
  club_roster: [Year, Class, program, affiliation]
  linkedin: [Year, Class, program, MAJfirstcode, MAJsecondcode]
  survey_insider: [logdate, Class, affiliation]
  everything: [Year, Class, program, FTFY, affiliation, MAJfirstcode, MAJsecondcode, begincol, edaspire]
attack:
  n_targets: 200
  seed: 42
seed: 42
```

### Common data conventions

- Every DataFrame has a `row_id` column (int, 0..n-1, original row order), added by `load.py`. It is **never** part of a released file; it exists only so experiments can check who is who. Exports drop it.
- Column `First Time First Year` is renamed `FTFY` on load. All code uses `FTFY`.
- `MAJsecond` is str. Numeric codes keep `-9` as a valid value.
- Missing values stay as NaN; all group-bys use `dropna=False`.

### Module contracts (match the reference implementations exactly)

Roles used everywhere: `direct_id`, `quasi_id`, `metadata`, `sensitive`, `free_text`, `planted_pii`, `derived`, `other`. `derived` columns (MAJfirst, MAJsecond, MAJfirstcol, MAJsecondcol, MAJnum) are not risk-measured on their own; they are dropped in lockstep when their source code column is generalized.

**reid/config.py (C):** `load_config(path="config.yaml") -> dict`

**reid/load.py (A)**
```python
load_raw(cfg) -> DataFrame            # xlsx sheet "in"; FTFY rename; MAJsecond -> str; logdate datetime; row_id first column
build_clean_cache(cfg) -> DataFrame   # writes data/nsse_clean.parquet
load_clean(cfg) -> DataFrame          # parquet, building it if missing
load_lookup(cfg) -> {field: {int code: name}}
```

**reid/risk.py (A)**
```python
class_sizes(df, qis) -> Series                       # aligned to df.index; groupby dropna=False
risk_summary(df, qis, k=5) -> dict                   # n, n_classes, k_min, pct_unique, pct_below_k, avg_risk, max_risk
                                                     # (ignores qis not in df.columns)
riskiest_combos(df, qis, max_size=3, k=5) -> DataFrame   # combo ("A + B"), size, pct_unique, pct_below_k
metadata_leaks(df, cols=("logdate","duration"), combos=(("logdate","Class","affiliation"),), k=5) -> DataFrame
risk_by_group(df, qis, group_col, k=5) -> DataFrame       # group, n, pct_unique, pct_below_k
l_diversity_report(df, qis, sensitive_cols) -> DataFrame  # sensitive, l_min, pct_classes_l1
```

**reid/attacks.py (A)**
```python
make_attacker_table(original_df, known_cols, n=200, seed=42) -> DataFrame   # row_id + raw known cols
linkage_attack(release_df, attacker_df, known_cols, transform=None) -> dict
    # transform: callable applying the release generalization to the attacker's raw knowledge
    # keys: n_targets, cols_used, n_unique_match, n_correct, unique_match_rate, correct_rate
persona_risk(df, personas: dict, k=5) -> DataFrame   # persona, fields, pct_unique, pct_below_k
```

**reid/plant.py (B)**
```python
plant_identifiers(df, seed=42, pct_pii=0.30, pct_decoy=0.10) -> (planted_df, truth_df)
    # adds full_name, email, student_id ("U"+8 digits), comment
    # truth_df: row_id, entity_type (PERSON|EMAIL_ADDRESS|PHONE_NUMBER|BU_ID), value, start, end
```

**reid/pii_text.py (B)**
```python
ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "BU_ID"]
presidio_detect(text, threshold=0.4) -> list[{entity_type, start, end, score}]
llm_detect(text) -> same shape ([] if LLM disabled)
combine(a, b) -> merged, de-overlapped span list
scrub_text(text, method="presidio", spans=None) -> str      # spans replaced by <ENTITY_TYPE>
evaluate_detection(truth_df, predictions: {row_id: spans}) -> DataFrame
    # entity_type (+ "ALL"), tp, fp, fn, precision, recall, f1; only rows in predictions are scored
```

**reid/tokens.py (B)**
```python
ensure_keys(keys_dir="keys")              # keys/vault.key (Fernet) and keys/join.key if JOIN_KEY env not set
join_token(value) -> str                  # HMAC-SHA256 hex[:16], deterministic
tokenize_column(df, col, vault_path=None) -> DataFrame   # vault at keys/vault_<col>.csv: token, encrypted_value
detokenize(token, col, vault_path=None) -> str
```

**reid/mitigate.py (B)** (reads `hierarchies.yaml`)
```python
load_hierarchies(path="hierarchies.yaml") -> dict
max_level(col) -> int                      # last level = drop
apply_levels(df, levels: {col: int}) -> DataFrame      # skips columns not present; drops derived in lockstep
make_transform(levels) -> callable(df) -> df
suppress(df, qis, k) -> (kept_df, suppressed_mask)
greedy_generalize(df, qis, k=5, max_suppression=0.05, max_group_suppression=None,
                  group_col="affiliation", protect=(), must_keep=()) -> dict
    # keys: levels, release_df (row_id kept), suppressed_mask (aligned to input index),
    #       steps (list of {step, column, new_level, pct_below_k, max_group_below_k}),
    #       final_risk (risk_summary), active_qis (qis still present), transform (callable)
```

**reid/utility.py (B)**
```python
group_means(df, scales, by) -> DataFrame
utility_report(original_df, release_df, scales, by_list, levels=None) -> dict
    # table (by, group, scale, orig_mean, release_mean, abs_shift), max_abs_shift, mean_abs_shift,
    # pct_rows_kept, analysis_status {by: "available"|"coarsened"|"lost"}
ml_utility(original_df, release_df, transform, target="SE", exclude=(), seed=42) -> dict
    # mae_original, mae_release, r2_original, r2_release, n_train_original, n_train_release
fairness_report(df, suppressed_mask, group_col="affiliation") -> DataFrame   # group, n, n_suppressed, pct_suppressed
privacy_utility_curve(df, qis, scales, by_list, ks=(2,3,5,10), **greedy_kwargs) -> DataFrame
    # k, pct_suppressed, pct_unique_after, n_qis_dropped, analyses_lost, max_abs_shift, mean_abs_shift
```

**reid/llm.py (C)**
```python
llm_enabled() -> bool                     # env LLM_PROVIDER in {"anthropic","openai"}
complete(prompt, system=None, json_mode=False, max_tokens=800) -> str | None   # None on error/disabled
parse_json(text) -> dict | list | None
```

**reid/classify.py (C)**
```python
ROLES = [...]                             # list above
profile_columns(df) -> list[dict]         # name, dtype, n_unique, pct_missing, pct_unique_values, top_values?, avg_text_len?
roles_from_config(cfg) -> {col: role}     # known schema for the BU file
classify_columns(profile, known_roles=None, batch=40) -> {col: {role, reason, confidence, source}}
    # source: "schema" | "heuristic" | "llm"; LLM never overrides "derived"
```

**reid/agent.py (C)**
```python
run_agent(df, roles, target_k=5, max_suppression=0.05, protect_small_groups=True, group_col="affiliation",
          max_group_suppression=0.10, personas=None, scales=("HO","SF","QI","SE"),
          by_list=("Class","affiliation","MAJfirstcol","Year"), scrub_comments="drop", log=None) -> dict
    # keys: plan, steps (log lines), before, before_with_metadata, after, attacks {persona: {before, after}},
    #       mitigation (greedy dict), utility, fairness (DataFrame), protect_small_groups, target_k, label, report_md
privacy_label(result) -> dict   # pct_unique_before/after, k_after, pct_suppressed, most_affected_group/pct,
                                # attack_before_pct/after_pct ("everything" persona), max_mean_shift, remaining_risks
write_report(result) -> str     # Markdown; LLM if enabled, template otherwise
```

### results/ files (written by `scripts/run_experiments.py`; read by the app)

| File | Content |
|---|---|
| baseline_risk.json | risk_summary for core9, core8, extended14, with_metadata |
| staircase.csv | uniqueness as fields are added (opening chart) |
| combos.csv, leaks.csv, personas.csv, risk_by_group.csv, l_diversity.csv | risk outputs |
| attack.json | `{mode: {persona: {before, after}}}`, mode ∈ protect_on, protect_off |
| fairness.csv | fairness_report + `setting` column (protect_on / protect_off) |
| mitigation_summary.json | per mode: levels, pct_suppressed, final_risk, shifts, analysis_status, ml (ml_utility) |
| curve.csv | privacy_utility_curve (protect off) |
| detection.csv | evaluate_detection + `method` (presidio, presidio_same_sample, llm, combined) |

## 8. Environment

```
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt     # contents listed in Role C's file
python -m spacy download en_core_web_sm
cp .env.example .env                # then fill in LLM settings if you have an API key
```

Use the **small** spaCy model (`en_core_web_sm`); the default large model is several hundred MB and slow to download on event Wi-Fi.

## 9. Ethics and safety rules (apply to all code)

- Synthetic data only. Planted identifiers are fake and labeled as planted in the README and UI.
- **No row-level data to LLMs.** The column classifier, planner, and report writer receive only column names, types, counts, category labels, and computed metrics. The single exception: planted synthetic comments may be sent to the LLM for the detection comparison, because they are entirely fake.
- `keys/`, `data/`, and `.env` are never committed. The vault key is stored separately from the release.
- Tokenized data is pseudonymous, not anonymous; say so in the UI and README.
- The attack code runs only on synthetic data and is framed as a testing tool for data owners.
- The tool advises; a human data steward confirms roles and signs off. It is not a FERPA compliance certificate.
- Limitations to state: k-anonymity does not prevent all attribute inference (see l-diversity report), attackers may have knowledge beyond our personas, and combining multiple releases can re-identify people.
- Fairness: report suppression by group; offer the small-group safeguard.
- Accessibility: text labels on all charts, colorblind-safe palette, plain language.

## 10. Team checkpoints (Saturday)

| Time | Checkpoint |
|---|---|
| 12:45 | Repo created by C; config.yaml, requirements, .gitignore, stub modules with the contract signatures pushed. Everyone clones. |
| 1:45 | **CP1:** A: clean parquet built and shared (via USB/AirDrop, not Git). B: hierarchies.yaml + plant.py working. C: Streamlit skeleton with 6 screens using fake data. |
| 3:30 | **CP2:** A: risk.py + attacks.py on real data, numbers in section 4 reproduced. B: greedy_generalize v1 + tokens + presidio detection. C: classify + llm + UI reads real risk functions. Merge to main. |
| 5:00 | **CP3 (integration):** full flow runs end to end in the app: upload/load → roles → risk → fix → before/after → report → download. Merge to main. |
| 5:30 | **Feature freeze** for Hackachusetts. Only bug fixes after this. |
| 5:30–6:30 | A + B run scripts/run_experiments.py and finalize results/; C writes README. |
| 6:30–7:00 | Record 2-minute video (C leads, all appear or narrate). |
| 7:00–7:30 | C submits on Sundai: repo URL + video URL. Tag `hackachusetts-submission`. |
| 8:15 | Whole team at the mandatory evening session, Room 164. |
| by 9:30 | C creates Devpost page, adds A and B. |
