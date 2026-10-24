# Unmasked (DS+X × Hackachusetts 2026): Role B Brief
## Mitigation, Tokenization, PII Detection, and Evaluation

**Paste this entire file into a new AI assistant session (Kiro, Claude, or similar). You are assisting the team member in Role B.**

The team has three roles working in parallel toward the **8:00 PM Saturday Hackachusetts deadline** (target 7:30 PM), then polishing for the **DS+X Devpost deadline at 11:00 AM Sunday**:

- **Role A:** data loading, risk engine, attacker personas, linkage attack, charts (holds the BU login and the data)
- **Role B:** generalization hierarchies, mitigation optimizer, tokenization vault, planted PII, Presidio/LLM detection, utility and fairness evaluation
- **Role C:** repo and Kiro setup, LLM wrapper, column classifier, AI agent, Streamlit app, README, video, Sundai and Devpost submissions

Sections 1–10 are shared context, identical in all three briefs. The ROLE B section and Appendix B are specific to this role.

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

---

# ROLE B: Mitigation, Tokenization, PII Detection, and Evaluation

## B0. At a glance

- **You own:** `hierarchies.yaml`, `reid/plant.py`, `reid/pii_text.py`, `reid/tokens.py`, `reid/mitigate.py`, `reid/utility.py`, and the Role B section of `scripts/run_experiments.py`.
- **Your outputs feed:** Role C's agent (it calls `tokenize_column`, `greedy_generalize`, `utility_report`, `fairness_report`, `scrub_text`), Role A's attack "after" numbers (they need your `release_df` and `transform`), and the pitch's strongest evidence (privacy-utility curve, fairness chart, ML utility test, detection scores).
- **You need from Role A:** the clean parquet (by ~1:45). Until then, read the xlsx directly with A's `load_raw` (slow but works).
- **Reference implementations of all your files are in Appendix B.** Everything except Presidio was tested on the real data (Presidio could not be installed in the test environment), so **Presidio setup and tuning is your main unknown**: start it first.

## B1. Setup (first 20 minutes)

1. Clone the repo, create the venv, `pip install -r requirements.txt`.
2. **Immediately** run `python -m spacy download en_core_web_sm` (small model; do not use the large default).
3. Quick Presidio check:

```python
from reid.pii_text import presidio_detect
print(presidio_detect("Email jsmith4@bu.edu or call 617-555-0142. My ID is U12345678 and my advisor Maria Lopez helped."))
```

   Expect EMAIL_ADDRESS, PHONE_NUMBER, BU_ID, and PERSON spans. If PERSON is missed, lower `threshold` to 0.3 and retest.
4. Create your files from Appendix B in Kiro.

## B2. Tasks, requirements, and acceptance criteria

### Task B1: Hierarchies and mitigation (done by 2:45)

- `hierarchies.yaml` defines levels for every quasi-identifier and metadata column; the **last level is always `drop`**. Derived major columns are dropped in lockstep (`derived:` section).
- `apply_levels` skips columns not present (attacker tables have only a few columns) and drops derived columns when their source reaches the listed level.
- `greedy_generalize`: at each step, try one more level on every non-protected column; pick the step with the best gain per cost (dropping a column costs 2, coarsening costs 1); stop when overall below-k ≤ `max_suppression` and (if set) every group's below-k ≤ `max_group_suppression`; then suppress the rest.
- **Acceptance (reference results, 14 QIs + 2 metadata, k=5, max 5%):** protect ON → 2.5% removed, 0% unique, affiliation kept, removal by group from 6.9% (Diademed sifaka) down to 0.9% (Ring-tailed lemur); protect OFF → 3.5% removed, affiliation dropped. Runtime 4–5 s each.

**YAML gotchas (both already fixed in the reference):** PyYAML reads `yes`/`no` keys as booleans (so use `label_yes`/`label_no`), and reads `1.0e12` as a string (use a plain integer like `1000000000`).

### Task B2: Planted identifiers (done by 1:45)

- `plant_identifiers(df, seed=42)` adds `full_name`, `email` (`first initial + last name + number @bu.edu`), `student_id` (`U` + 8 digits), and `comment`. About 30% of comments contain PII from templates (names, emails, 617 phone numbers, student IDs, sometimes two entities), 10% are decoys (Mugar Library, CS 111, Warren Towers, Room 617), 60% are clean.
- The truth table records exact character spans. **Acceptance:** for every truth row, `comment[start:end] == value` (verified in testing: 0 span errors).
- Give A the function so `scripts/build_cache.py` can write the planted and truth parquets.

### Task B3: Tokenization vault (done by 3:00)

- `join_token`: HMAC-SHA256 with `JOIN_KEY` (from `.env`, or generated into `keys/join.key`), hex, first 16 characters. Deterministic, so tokenized datasets can still be joined.
- `tokenize_column`: replaces the column with tokens and writes a **per-column** vault `keys/vault_<col>.csv` (token, Fernet-encrypted original). The Fernet key lives in `keys/vault.key`. Fernet ciphertext is randomized, which is why the join key is a separate HMAC token.
- **Acceptance:** `detokenize(tokenize_column(df, "student_id").student_id[0], "student_id")` returns the original; nothing in `keys/` is committed.

### Task B4: PII detection and scoring (done by 4:30)

- `presidio_detect` uses the small spaCy model plus a custom `BU_ID` regex recognizer (`\bU\d{8}\b`, score 0.9) and returns only our four entity types.
- `llm_detect` (only if C's LLM is enabled) asks for `{entity_type, text}` pairs and maps them to spans with `str.find`. **Send only planted synthetic comments**, never real data.
- `evaluate_detection`: a true positive needs the same entity type and overlapping spans; each truth entity can be matched once.
- Run on a **1,500-comment sample** for Presidio (full 20k is slow) and **200 comments** for the LLM. Write `results/detection.csv` with methods `presidio`, `presidio_same_sample`, `llm`, `combined`.
- **Expected pattern (not yet measured):** emails and BU IDs near 100% precision and recall; phone numbers high; PERSON lower with the small model; decoys may cause a few false positives (Room 617, Mugar). The combined method should have the best recall. Whatever the numbers are, report them honestly; misses are a finding.
- Tuning knobs: `threshold` (try 0.3–0.6), add a deny-list of known decoys, or add context words.

### Task B5: Utility, fairness, and the curve (done by 5:00)

- `utility_report`: group labels come from the **original** data joined on `row_id`, so shifts measure suppression distortion; `analysis_status` marks each grouping column as `available`, `coarsened`, or `lost`.
- `ml_utility`: trains a HistGradientBoosting regressor to predict `SE` (excluding `SE*` item columns, IDs, metadata, and planted columns), once on original training rows and once on released training rows; tests both on the same held-out original rows (generalized with `transform` for the release model). **Reference:** R² 0.42 original vs. 0.37 (protect ON) and 0.41 (protect OFF).
- `fairness_report`: share of each group's records removed.
- `privacy_utility_curve`: runs the optimizer at k = 2, 3, 5, 10 (reference in section 4).

### Task B6: Experiments (by 6:00)

- Run `python scripts/run_experiments.py` (full, with Presidio) once Presidio works; otherwise `--skip-presidio` and add detection later.
- Post to the team chat: removed %, removal by group (both modes), analyses lost, ML R², curve table, detection precision/recall.

## B3. Stretch (overnight, DS+X version only)

1. **Must-keep analyses:** `greedy_generalize(..., must_keep=["MAJfirstcode"])` already limits those columns to one level. C can add a multiselect in tab 4; report how the cost moves elsewhere.
2. **Differential privacy comparison:** release noisy group averages instead of rows and compare accuracy with the k-anonymized release. Tested code:

```python
import numpy as np
import pandas as pd

def dp_group_means(df, scale, by, epsilon=1.0, lower=0.0, upper=60.0, seed=42):
    """Differentially private group means (Laplace mechanism). Half the budget goes to the
    noisy sum (sensitivity = upper - lower) and half to the noisy count (sensitivity = 1)."""
    rng = np.random.default_rng(seed)
    d = df[[by, scale]].dropna(subset=[scale]).copy()
    d[scale] = d[scale].clip(lower, upper)
    g = d.groupby(by, dropna=False)[scale].agg(["sum", "count"])
    eps = epsilon / 2
    noisy_sum = g["sum"] + rng.laplace(0, (upper - lower) / eps, len(g))
    noisy_cnt = (g["count"] + rng.laplace(0, 1 / eps, len(g))).clip(lower=1)
    return pd.DataFrame({"true_mean": g["sum"] / g["count"],
                         "dp_mean": (noisy_sum / noisy_cnt).clip(lower, upper),
                         "n": g["count"]})
```

   At epsilon = 1, SE means by affiliation moved by under 0.5 points, and the smallest group (Gray mouse lemur, n=759) moved the most. Plot error vs. epsilon (0.1, 0.5, 1, 5) per group: smaller groups get noisier, which echoes the fairness finding.
3. **Presidio scrubbing on all comments** precomputed into a cached column, so the app can show scrubbed text instantly.

## B4. Pitfalls

- Generalize derived columns in lockstep or detail leaks back (the `derived:` section handles this; do not remove it).
- `release_df` keeps `row_id` for evaluation; C drops it on export. Never drop it inside your functions.
- The vault and keys must never be committed or bundled with the release.
- `pd.cut` labels must be strings; the reference converts and restores NaN.
- If a run of `greedy_generalize` cannot meet the target (all columns exhausted), it stops and suppresses the remainder; the agent reports it.

## B5. Definition of done (5:00 PM)

- [ ] `hierarchies.yaml`, `plant.py`, `tokens.py`, `mitigate.py`, `utility.py` match contracts and reproduce reference results.
- [ ] Presidio running; `results/detection.csv` written (at least the presidio method).
- [ ] `results/fairness.csv`, `curve.csv`, `mitigation_summary.json`, `attack.json` written.
- [ ] Code on `role-b`, merged at CP2 and CP3. No keys or data committed.

## B6. Kiro instructions

Create a spec named `role-b-mitigation` in Kiro by pasting this file and asking for requirements, design, and tasks from sections 3, 4, 5, 7 and ROLE B, with Appendix B as the design. Let Kiro write the files, run the acceptance checks, and commit `.kiro/specs/role-b-mitigation/`.

---

# Appendix B: Reference implementation

### hierarchies.yaml
```yaml
# Generalization hierarchies. Level 0 = original. The last level of every column is "drop".
Year:
  - {type: identity}
  - {type: map, map: {2014: "2014-16", 2016: "2014-16", 2018: "2018-20", 2020: "2018-20", 2022: "2022-24", 2024: "2022-24"}}
  - {type: drop}
Class:
  - {type: identity}
  - {type: drop}
program:
  - {type: identity}
  - {type: map_other, keep: [CLF, LAG, VAN, HIG, TSI], other: OTHER}
  - {type: drop}
FTFY:
  - {type: identity}
  - {type: drop}
affiliation:
  - {type: identity}
  - {type: map_other, keep: [Ring-tailed lemur, Indri, Aye-aye], other: Other lemur}
  - {type: drop}
MAJfirstcode:
  - {type: identity}
  - {type: from_column, source: MAJfirstcol}
  - {type: drop}
MAJsecondcode:
  - {type: identity}
  - {type: from_column, source: MAJsecondcol}
  - {type: has_value, none_values: [-9], label_yes: has_second, label_no: no_second}
  - {type: drop}
begincol:
  - {type: identity}
  - {type: drop}
edaspire:
  - {type: identity}
  - {type: map, map: {1: low, 2: low, 3: high, 4: high}}
  - {type: drop}
logdate:
  - {type: identity}
  - {type: month}
  - {type: year}
  - {type: drop}
duration:
  - {type: identity}
  - {type: bins, edges: [0, 5, 15, 30, 1000000000], labels: ["<5", "5-15", "15-30", "30+"]}
  - {type: drop}

attend_voc:
  - {type: identity}
  - {type: drop}
attend_com:
  - {type: identity}
  - {type: drop}
attend_col:
  - {type: identity}
  - {type: drop}
attend_none:
  - {type: identity}
  - {type: drop}
attend_other:
  - {type: identity}
  - {type: drop}

# Derived columns that must follow their source column's level.
# For each source: list of [min_level_of_source, derived_column_to_drop]
derived:
  MAJfirstcode:
    - [1, MAJfirst]
    - [2, MAJfirstcol]
  MAJsecondcode:
    - [1, MAJsecond]
    - [2, MAJsecondcol]
    - [3, MAJnum]
```

### reid/plant.py
```python
import random
import pandas as pd
from faker import Faker

CLEAN = [
    "The tutoring center really helped me this semester.",
    "I wish there were more evening study spaces.",
    "Advising appointments are hard to book.",
    "Dining options improved a lot this year.",
    "Group projects taught me the most.",
    "I felt welcome in my first-year seminar.",
]
DECOYS = [  # look like PII but are not (should NOT be flagged)
    "Mugar Library is my favorite place to study.",
    "CS 111 was the hardest course I took.",
    "The Warren Towers dining hall gets crowded at noon.",
    "Room 617 in the CDS building is always cold.",
    "I joined the Kite Studies club in my second year.",
]
PII_TEMPLATES = [  # (text pieces, entity types) - None marks a literal piece
    [("My advisor ", None), ("{person}", "PERSON"), (" was incredibly supportive.", None)],
    [("Please follow up with me at ", None), ("{email}", "EMAIL_ADDRESS"), (" about the survey.", None)],
    [("You can text me at ", None), ("{phone}", "PHONE_NUMBER"), (" if you want details.", None)],
    [("My student ID is ", None), ("{bu_id}", "BU_ID"), (", my financial aid is still wrong.", None)],
    [("I'm ", None), ("{person}", "PERSON"), (" and my roommate ", None), ("{person}", "PERSON"), (" agrees housing is too expensive.", None)],
    [("Email ", None), ("{email}", "EMAIL_ADDRESS"), (" or call ", None), ("{phone}", "PHONE_NUMBER"), (" to reach me.", None)],
]

def _bu_id(rng):
    return "U" + "".join(str(rng.randint(0, 9)) for _ in range(8))

def _phone(rng):
    return f"617-{rng.randint(200, 999)}-{rng.randint(0, 9999):04d}"

def plant_identifiers(df, seed=42, pct_pii=0.30, pct_decoy=0.10):
    fake = Faker("en_US")
    Faker.seed(seed)
    rng = random.Random(seed)
    out = df.copy()
    names, emails, ids, comments, truth = [], [], [], [], []
    for row_id in out["row_id"]:
        first, last = fake.first_name(), fake.last_name()
        name = f"{first} {last}"
        email = f"{first[0].lower()}{last.lower()}{rng.randint(1, 99)}@bu.edu"
        sid = _bu_id(rng)
        names.append(name); emails.append(email); ids.append(sid)
        u = rng.random()
        if u < pct_pii:
            text = ""
            for piece, etype in rng.choice(PII_TEMPLATES):
                if etype is None:
                    text += piece
                    continue
                value = {"PERSON": lambda: rng.choice([name, fake.name()]),
                         "EMAIL_ADDRESS": lambda: email,
                         "PHONE_NUMBER": lambda: _phone(rng),
                         "BU_ID": lambda: sid}[etype]()
                start = len(text)
                text += value
                truth.append({"row_id": row_id, "entity_type": etype, "value": value,
                              "start": start, "end": start + len(value)})
            comments.append(text)
        elif u < pct_pii + pct_decoy:
            comments.append(rng.choice(DECOYS))
        else:
            comments.append(rng.choice(CLEAN))
    out["full_name"], out["email"], out["student_id"], out["comment"] = names, emails, ids, comments
    return out, pd.DataFrame(truth, columns=["row_id", "entity_type", "value", "start", "end"])
```

### reid/pii_text.py (not runnable in the test environment; verify first)
```python
import pandas as pd
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from reid import llm

ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "BU_ID"]
_analyzer = None

def _engine():
    global _analyzer
    if _analyzer is None:
        provider = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]})
        _analyzer = AnalyzerEngine(nlp_engine=provider.create_engine(), supported_languages=["en"])
        _analyzer.registry.add_recognizer(PatternRecognizer(
            supported_entity="BU_ID", patterns=[Pattern("bu_id", r"\bU\d{8}\b", 0.9)]))
    return _analyzer

def presidio_detect(text, threshold=0.4):
    res = _engine().analyze(text=text, language="en", entities=ENTITIES, score_threshold=threshold)
    return [{"entity_type": r.entity_type, "start": r.start, "end": r.end, "score": float(r.score)} for r in res]

LLM_SYSTEM = ("You find personal information in short survey comments. Entity types: "
              "PERSON (a person's name), EMAIL_ADDRESS, PHONE_NUMBER, BU_ID (U followed by 8 digits). "
              "Building names, course codes, and room numbers are NOT personal information.")

def llm_detect(text):
    out = llm.parse_json(llm.complete(
        f'Comment: """{text}"""\nReturn a JSON list of objects with keys "entity_type" and "text" '
        f'(the exact substring). Return [] if none.', system=LLM_SYSTEM, json_mode=True, max_tokens=300))
    if not isinstance(out, list):
        return []
    spans = []
    for item in out:
        if not isinstance(item, dict) or item.get("entity_type") not in ENTITIES:
            continue
        sub = str(item.get("text", ""))
        start = text.find(sub) if sub else -1
        while start != -1:
            spans.append({"entity_type": item["entity_type"], "start": start, "end": start + len(sub), "score": 1.0})
            start = text.find(sub, start + 1)
    return spans

def _dedupe(spans):
    spans = sorted(spans, key=lambda s: (-s["score"], s["start"]))
    kept = []
    for s in spans:
        if all(s["end"] <= k["start"] or s["start"] >= k["end"] for k in kept):
            kept.append(s)
    return sorted(kept, key=lambda s: s["start"])

def scrub_text(text, method="presidio", spans=None):
    if spans is None:
        spans = presidio_detect(text) if method == "presidio" else llm_detect(text)
    for s in sorted(_dedupe(spans), key=lambda s: -s["start"]):
        text = text[:s["start"]] + f"<{s['entity_type']}>" + text[s["end"]:]
    return text

def combine(a, b):
    return _dedupe(list(a) + list(b))

def evaluate_detection(truth_df, predictions):
    """predictions: {row_id: [span dicts]} for the rows that were scored.
    Only rows present in `predictions` are evaluated."""
    rows = {e: {"tp": 0, "fp": 0, "fn": 0} for e in ENTITIES}
    truth_by_row = {rid: g.to_dict("records") for rid, g in truth_df.groupby("row_id")}
    for rid, preds in predictions.items():
        truth = truth_by_row.get(rid, [])
        matched = set()
        for p in _dedupe(preds):
            hit = None
            for i, t in enumerate(truth):
                if i not in matched and t["entity_type"] == p["entity_type"] and p["start"] < t["end"] and t["start"] < p["end"]:
                    hit = i
                    break
            if hit is None:
                rows[p["entity_type"]]["fp"] += 1
            else:
                matched.add(hit)
                rows[p["entity_type"]]["tp"] += 1
        for i, t in enumerate(truth):
            if i not in matched:
                rows[t["entity_type"]]["fn"] += 1
    out = pd.DataFrame([{"entity_type": e, **v} for e, v in rows.items()])
    tot = out[["tp", "fp", "fn"]].sum()
    out.loc[len(out)] = {"entity_type": "ALL", **tot.to_dict()}
    out["precision"] = out.tp / (out.tp + out.fp).replace(0, float("nan"))
    out["recall"] = out.tp / (out.tp + out.fn).replace(0, float("nan"))
    out["f1"] = 2 * out.precision * out.recall / (out.precision + out.recall)
    return out
```

### reid/tokens.py
```python
import hashlib, hmac, os
from pathlib import Path
import pandas as pd
from cryptography.fernet import Fernet

KEYS_DIR = Path("keys")

def ensure_keys(keys_dir="keys"):
    global KEYS_DIR
    KEYS_DIR = Path(keys_dir)
    KEYS_DIR.mkdir(exist_ok=True)
    vk = KEYS_DIR / "vault.key"
    if not vk.exists():
        vk.write_bytes(Fernet.generate_key())
    jk = KEYS_DIR / "join.key"
    if not os.environ.get("JOIN_KEY") and not jk.exists():
        jk.write_bytes(os.urandom(32).hex().encode())

def _join_key():
    k = os.environ.get("JOIN_KEY")
    if k:
        return k.encode()
    ensure_keys(KEYS_DIR)
    return (KEYS_DIR / "join.key").read_bytes()

def _vault():
    ensure_keys(KEYS_DIR)
    return Fernet((KEYS_DIR / "vault.key").read_bytes())

def join_token(value):
    return hmac.new(_join_key(), str(value).encode(), hashlib.sha256).hexdigest()[:16]

def _vault_path(col):
    return str(KEYS_DIR / f"vault_{col}.csv")

def tokenize_column(df, col, vault_path=None):
    """Replace `col` with deterministic HMAC tokens. Originals are Fernet-encrypted into a
    per-column vault file (keys/vault_<col>.csv). The vault key lives in keys/vault.key."""
    vault_path = vault_path or _vault_path(col)
    f = _vault()
    values = df[col].astype(str)
    tokens = values.map(join_token)
    vault = pd.DataFrame({"token": tokens, "encrypted_value": values.map(lambda v: f.encrypt(v.encode()).decode())}).drop_duplicates("token")
    Path(vault_path).parent.mkdir(exist_ok=True)
    vault.to_csv(vault_path, index=False)
    out = df.copy()
    out[col] = tokens
    return out

def detokenize(token, col, vault_path=None):
    vault = pd.read_csv(vault_path or _vault_path(col))
    enc = vault.loc[vault["token"] == token, "encrypted_value"]
    if enc.empty:
        raise KeyError("token not found")
    return _vault().decrypt(enc.iloc[0].encode()).decode()
```

### reid/mitigate.py
```python
import numpy as np
import pandas as pd
import yaml
from reid.risk import class_sizes, risk_summary

_H = None

def load_hierarchies(path="hierarchies.yaml"):
    global _H
    with open(path) as f:
        _H = yaml.safe_load(f)
    return _H

def _h():
    return _H if _H is not None else load_hierarchies()

def max_level(col):
    return len(_h()[col]) - 1

def _apply_rule(df, col, rule):
    t = rule["type"]
    s = df[col]
    if t == "identity":
        return s
    if t == "map":
        m = rule["map"]
        return s.map(lambda v: m.get(v, m.get(str(v), v)) if pd.notna(v) else v)
    if t == "map_other":
        keep = set(rule["keep"])
        return s.where(s.isna() | s.isin(keep), rule["other"])
    if t == "from_column":
        return df[rule["source"]]
    if t == "has_value":
        none = set(rule["none_values"])
        return s.map(lambda v: v if pd.isna(v) else (rule["label_no"] if v in none else rule["label_yes"]))
    if t == "month":
        return pd.to_datetime(s).dt.to_period("M").astype(str)
    if t == "year":
        return pd.to_datetime(s).dt.year
    if t == "bins":
        return pd.cut(s, bins=rule["edges"], labels=rule["labels"], include_lowest=True).astype(str).replace("nan", np.nan)
    raise ValueError(f"unknown rule type {t}")

def apply_levels(df, levels):
    """Return a generalized copy. Columns at their 'drop' level are removed,
    and derived columns are dropped in lockstep with their source."""
    h = _h()
    out = df.copy()
    to_drop = []
    for col, lvl in levels.items():
        if col not in out.columns or col not in h:
            continue
        rule = h[col][lvl]
        if rule["type"] == "drop":
            to_drop.append(col)
        else:
            out[col] = _apply_rule(out, col, rule)
        for min_lvl, derived in h.get("derived", {}).get(col, []):
            if lvl >= min_lvl and derived in out.columns:
                to_drop.append(derived)
    return out.drop(columns=sorted(set(to_drop)))

def make_transform(levels):
    return lambda d: apply_levels(d, levels)

def suppress(df, qis, k):
    qis = [q for q in qis if q in df.columns]
    if not qis:
        mask = pd.Series(False, index=df.index)
        return df.copy(), mask
    s = class_sizes(df, qis)
    mask = s < k
    return df.loc[~mask].copy(), mask

def _group_supp(df, qis, k, group_col, group_series):
    qis = [q for q in qis if q in df.columns]
    if not qis:
        return 0.0
    below = class_sizes(df, qis) < k
    return float(below.groupby(group_series.values).mean().max())

def greedy_generalize(df, qis, k=5, max_suppression=0.05, max_group_suppression=None,
                      group_col="affiliation", protect=(), must_keep=()):
    qis = [q for q in qis if q in df.columns and q in _h()]
    levels = {q: 0 for q in qis}
    groups = df[group_col] if group_col in df.columns else pd.Series("all", index=df.index)
    steps = []

    def evaluate(lv):
        cur = apply_levels(df, lv)
        active = [q for q in qis if q in cur.columns]
        below = float((class_sizes(cur, active) < k).mean()) if active else 0.0
        gmax = _group_supp(cur, active, k, group_col, groups) if max_group_suppression is not None else 0.0
        return cur, below, gmax

    cur, below, gmax = evaluate(levels)
    steps.append({"step": 0, "column": None, "new_level": None, "pct_below_k": below, "max_group_below_k": gmax})

    def ok(b, g):
        return b <= max_suppression and (max_group_suppression is None or g <= max_group_suppression)

    step = 0
    while not ok(below, gmax):
        best = None
        for q in qis:
            if q in protect:
                continue
            limit = 1 if q in must_keep else max_level(q)
            if levels[q] >= limit:
                continue
            trial = dict(levels, **{q: levels[q] + 1})
            _, b, g = evaluate(trial)
            # objective: reduce overall below-k and the worst group's below-k; dropping costs more
            is_drop = (levels[q] + 1) == max_level(q)
            cost = 2.0 if is_drop else 1.0
            gain = (below - b) + (0.5 * (gmax - g) if max_group_suppression is not None else 0.0)
            score = gain / cost
            if best is None or score > best[0]:
                best = (score, q, trial, b, g)
        if best is None:
            break
        _, q, levels, below, gmax = best
        step += 1
        steps.append({"step": step, "column": q, "new_level": levels[q],
                      "pct_below_k": below, "max_group_below_k": gmax})

    cur = apply_levels(df, levels)
    active = [q for q in qis if q in cur.columns]
    release, mask = suppress(cur, active, k)
    return {"levels": levels, "release_df": release, "suppressed_mask": mask,
            "steps": steps, "final_risk": risk_summary(release, active, k),
            "active_qis": active, "transform": make_transform(levels)}
```

### reid/utility.py
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

def group_means(df, scales, by):
    return df.groupby(by, dropna=False)[list(scales)].mean()

def utility_report(original_df, release_df, scales, by_list, levels=None):
    """Compare group means of `scales` on the original data vs. the rows kept in the release.
    Group labels always come from the ORIGINAL data (joined on row_id), so the shift measures
    the distortion caused by suppression. An analysis is 'lost' if its grouping column was
    dropped from the release, 'coarsened' if it was generalized, else 'available'."""
    kept = original_df[original_df["row_id"].isin(release_df["row_id"])]
    rows, status = [], {}
    for by in by_list:
        if by not in release_df.columns:
            status[by] = "lost"
        elif levels and levels.get(by, 0) > 0:
            status[by] = "coarsened"
        else:
            status[by] = "available"
        o = group_means(original_df, scales, by)
        r = group_means(kept, scales, by).reindex(o.index)
        for g in o.index:
            for sc in scales:
                rows.append({"by": by, "group": g, "scale": sc,
                             "orig_mean": o.loc[g, sc], "release_mean": r.loc[g, sc],
                             "abs_shift": abs(o.loc[g, sc] - r.loc[g, sc]) if pd.notna(r.loc[g, sc]) else np.nan})
    table = pd.DataFrame(rows)
    return {"table": table,
            "max_abs_shift": float(table["abs_shift"].max()),
            "mean_abs_shift": float(table["abs_shift"].mean()),
            "pct_rows_kept": float(len(kept) / len(original_df)),
            "analysis_status": status}

_EXCLUDE_PREFIXES = ("SE",)  # SE items would leak the SE target

def _features(df, target, exclude):
    cols = [c for c in df.columns
            if c != target and c not in exclude and not c.startswith(_EXCLUDE_PREFIXES)]
    X = df[cols].copy()
    for c in X.columns:
        if X[c].dtype == object or str(X[c].dtype) in ("str", "string", "category") or np.issubdtype(X[c].dtype, np.datetime64):
            X[c] = X[c].astype(str)
    return pd.get_dummies(X, dummy_na=True)

def ml_utility(original_df, release_df, transform, target="SE", exclude=(), seed=42):
    """Train the same model on original vs. released data; test both on the same held-out
    ORIGINAL rows (generalized with `transform` for the release model)."""
    exclude = set(exclude) | {"row_id", "ID", "logdate", "duration",
                              "full_name", "email", "student_id", "comment"}
    data = original_df[original_df[target].notna()]
    train_ids, test_ids = train_test_split(data["row_id"], test_size=0.2, random_state=seed)
    o_train = data[data["row_id"].isin(train_ids)]
    o_test = data[data["row_id"].isin(test_ids)]
    r_train = release_df[release_df["row_id"].isin(train_ids) & release_df[target].notna()]
    r_test = transform(o_test)

    def fit_eval(train, test):
        Xtr, Xte = _features(train, target, exclude), _features(test, target, exclude)
        Xte = Xte.reindex(columns=Xtr.columns, fill_value=0)
        m = HistGradientBoostingRegressor(random_state=seed).fit(Xtr, train[target])
        p = m.predict(Xte)
        return mean_absolute_error(test[target], p), r2_score(test[target], p)

    mae_o, r2_o = fit_eval(o_train, o_test)
    mae_r, r2_r = fit_eval(r_train, r_test)
    return {"target": target, "mae_original": float(mae_o), "mae_release": float(mae_r),
            "r2_original": float(r2_o), "r2_release": float(r2_r),
            "n_train_original": int(len(o_train)), "n_train_release": int(len(r_train))}

def fairness_report(df, suppressed_mask, group_col="affiliation"):
    t = pd.DataFrame({"group": df[group_col].values, "sup": suppressed_mask.values})
    out = t.groupby("group", dropna=False).agg(n=("sup", "size"), n_suppressed=("sup", "sum")).reset_index()
    out["pct_suppressed"] = out["n_suppressed"] / out["n"]
    return out.sort_values("pct_suppressed", ascending=False)

def privacy_utility_curve(df, qis, scales, by_list, ks=(2, 3, 5, 10), **greedy_kwargs):
    from reid.mitigate import greedy_generalize
    rows = []
    for k in ks:
        r = greedy_generalize(df, qis, k=k, **greedy_kwargs)
        u = utility_report(df, r["release_df"], scales, by_list, r["levels"])
        rows.append({"k": k, "pct_suppressed": float(r["suppressed_mask"].mean()),
                     "pct_unique_after": r["final_risk"]["pct_unique"],
                     "n_qis_dropped": int(sum(1 for q in qis if q not in r["release_df"].columns)),
                     "analyses_lost": int(sum(v == "lost" for v in u["analysis_status"].values())),
                     "max_abs_shift": u["max_abs_shift"], "mean_abs_shift": u["mean_abs_shift"]})
    return pd.DataFrame(rows)
```

### scripts/run_experiments.py (shared with A; you own the "Role B" sections)
```python
"""Run all experiments and write small result files to results/ for the app and the pitch.
Usage: python scripts/run_experiments.py [--skip-presidio] [--llm-sample 200]"""
import argparse, json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pandas as pd
from reid.config import load_config
from reid import risk, attacks, mitigate, utility

ap = argparse.ArgumentParser()
ap.add_argument("--skip-presidio", action="store_true")
ap.add_argument("--presidio-sample", type=int, default=1500)
ap.add_argument("--llm-sample", type=int, default=200)
args = ap.parse_args()

cfg = load_config()
out = pathlib.Path("results"); out.mkdir(exist_ok=True)
df = pd.read_parquet(cfg["data"]["planted_parquet"])
truth = pd.read_parquet(cfg["data"]["truth_parquet"])
R = cfg["roles"]; k = cfg["targets"]["k"]
core = R["quasi_ids"]
core8 = [q for q in core if q != "FTFY"]
ext = core + R["quasi_ids_extended"]

# ---------- Role A ----------
json.dump({"core9": risk.risk_summary(df, core, k), "core8": risk.risk_summary(df, core8, k),
           "extended14": risk.risk_summary(df, ext, k),
           "with_metadata": risk.risk_summary(df, ext + R["metadata"], k)},
          open(out / "baseline_risk.json", "w"), indent=2)
risk.riskiest_combos(df, core, 3, k).to_csv(out / "combos.csv", index=False)
risk.metadata_leaks(df, k=k).to_csv(out / "leaks.csv", index=False)
attacks.persona_risk(df, cfg["personas"], k).to_csv(out / "personas.csv", index=False)
risk.risk_by_group(df, core, R["group_col"], k).to_csv(out / "risk_by_group.csv", index=False)
risk.l_diversity_report(df, ["Year", "Class", "affiliation", "MAJfirstcol"], R["sensitive_scales"]).to_csv(out / "l_diversity.csv", index=False)

# staircase for the opening chart
stairs = [["Year", "Class"], ["Year", "Class", "affiliation"], ["Year", "Class", "affiliation", "MAJfirstcode"],
          ["Year", "Class", "affiliation", "MAJfirstcode", "program"],
          ["Year", "Class", "affiliation", "MAJfirstcode", "program", "MAJsecondcode"],
          core8, ext]
pd.DataFrame([{"fields": " + ".join(s), "n_fields": len(s), **risk.risk_summary(df, s, k)} for s in stairs]).to_csv(out / "staircase.csv", index=False)

# ---------- Role B: mitigation in both modes ----------
qis = ext + R["metadata"]
work = df.drop(columns=R["planted"])
modes = {"protect_on": dict(protect=[R["group_col"]], max_group_suppression=cfg["targets"]["max_group_suppression"]),
         "protect_off": {}}
attack_rows, fair_rows, util_rows = {}, [], {}
for mode, kw in modes.items():
    m = mitigate.greedy_generalize(work, qis, k=k, max_suppression=cfg["targets"]["max_suppression"],
                                   group_col=R["group_col"], **kw)
    f = utility.fairness_report(work, m["suppressed_mask"], R["group_col"]); f["setting"] = mode; fair_rows.append(f)
    u = utility.utility_report(work, m["release_df"], cfg["utility_analyses"]["scales"], cfg["utility_analyses"]["by"], m["levels"])
    util_rows[mode] = {"levels": m["levels"], "pct_suppressed": float(m["suppressed_mask"].mean()),
                       "final_risk": m["final_risk"], "max_abs_shift": u["max_abs_shift"],
                       "mean_abs_shift": u["mean_abs_shift"], "analysis_status": u["analysis_status"],
                       "ml": utility.ml_utility(work, m["release_df"], m["transform"], target="SE")}
    attack_rows[mode] = {}
    for p, cols in cfg["personas"].items():
        atk = attacks.make_attacker_table(work, cols, cfg["attack"]["n_targets"], cfg["attack"]["seed"])
        attack_rows[mode][p] = {"before": attacks.linkage_attack(work, atk, cols),
                                "after": attacks.linkage_attack(m["release_df"], atk, cols, transform=m["transform"])}
json.dump(attack_rows, open(out / "attack.json", "w"), indent=2)
pd.concat(fair_rows).to_csv(out / "fairness.csv", index=False)
json.dump(util_rows, open(out / "mitigation_summary.json", "w"), indent=2, default=str)
utility.privacy_utility_curve(work, qis, cfg["utility_analyses"]["scales"], cfg["utility_analyses"]["by"],
                              ks=(2, 3, 5, 10), max_suppression=cfg["targets"]["max_suppression"]).to_csv(out / "curve.csv", index=False)

# ---------- Role B: PII detection ----------
if not args.skip_presidio:
    from reid import pii_text, llm
    sample = df.sample(n=min(args.presidio_sample, len(df)), random_state=cfg["seed"])
    t = truth[truth.row_id.isin(sample.row_id)]
    pres = {r.row_id: pii_text.presidio_detect(r.comment) for r in sample.itertuples()}
    rows = [pii_text.evaluate_detection(t, pres).assign(method="presidio")]
    if llm.llm_enabled():
        small = sample.head(args.llm_sample)          # synthetic comments only
        t2 = truth[truth.row_id.isin(small.row_id)]
        llmp = {r.row_id: pii_text.llm_detect(r.comment) for r in small.itertuples()}
        both = {rid: pii_text.combine(pres[rid], llmp[rid]) for rid in llmp}
        rows += [pii_text.evaluate_detection(t2, {rid: pres[rid] for rid in llmp}).assign(method="presidio_same_sample"),
                 pii_text.evaluate_detection(t2, llmp).assign(method="llm"),
                 pii_text.evaluate_detection(t2, both).assign(method="combined")]
    pd.concat(rows).to_csv(out / "detection.csv", index=False)
print("done; results written to results/")
```
