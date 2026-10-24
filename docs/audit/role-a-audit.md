# Role A Audit Report

## 1. Summary
Role A owned data loading/caching, the re-identification risk engine, attacker personas and the linkage attack, the cache/experiment scripts, and the pitch charts notebook. All modules are delivered and **working**: `reid/load.py`, `reid/risk.py`, `reid/attacks.py`, `scripts/build_cache.py`, the Role A section of `scripts/run_experiments.py`, `scripts/check_numbers.py`, and `notebooks/results.ipynb` (6 PNG charts). A re-run of `scripts/check_numbers.py` on the real clean data passed **13/13** acceptance checks reproducing the reference numbers in the brief. Everything is committed and present on `main`; the headline numbers (67.8% unique on 8 fields, 73.9% on 14, 68.5% linkage attack → 0% after mitigation) are reproduced from the committed `results/` files.

## 2. Files
Commit hashes: `a0dd5c2` (loader/risk/attacks/specs), `d762bd5` (results + charts), `62b5049` (attack+fairness charts), `3190a15` (teammate commit "Risk Engine and attacks" that deleted the Role A spec), `139171b` (restore of the Role A spec).

| File | Created or modified | Purpose (one line) | Commit(s) | Owned by this role per steering? |
|---|---|---|---|---|
| `reid/load.py` | Created | Load NSSE xlsx, clean, cache to parquet, add `row_id` | `a0dd5c2` | Yes (Role A) |
| `reid/risk.py` | Created | k-anonymity / uniqueness / combos / leaks / l-diversity / risk-by-group | `a0dd5c2` | Yes (Role A) |
| `reid/attacks.py` | Created | Attacker personas + simulated linkage attack | `a0dd5c2` | Yes (Role A) |
| `scripts/build_cache.py` | Created | Build clean + planted + truth parquets once | `a0dd5c2` | Yes (Role A) |
| `scripts/run_experiments.py` | Created | Writes `results/` files; Role A section + guarded Role B section | `a0dd5c2` | Shared file; Role A owns its section (Role B owns mitigation/detection section) |
| `scripts/check_numbers.py` | Created | Acceptance harness: reproduce section-4 reference numbers | `d762bd5` | Yes (Role A; not in original brief, added as a verification aid) |
| `notebooks/results.ipynb` | Created | 6 pitch charts from `results/` only (no row data) | `d762bd5`, `62b5049` | Yes (Role A) |
| `results/baseline_risk.json` | Created | core9/core8/extended14/with_metadata risk summaries | `d762bd5` | Yes (Role A) |
| `results/staircase.csv` | Created | Uniqueness as fields are added | `d762bd5` | Yes (Role A) |
| `results/combos.csv` | Created | Riskiest field combinations (129 rows) | `d762bd5` | Yes (Role A) |
| `results/leaks.csv` | Created | Metadata (logdate/duration) leaks | `d762bd5` | Yes (Role A) |
| `results/personas.csv` | Created | Per-persona uniqueness | `d762bd5` | Yes (Role A) |
| `results/risk_by_group.csv` | Created | Risk by affiliation group | `d762bd5` | Yes (Role A) |
| `results/l_diversity.csv` | Created | l-diversity for sensitive scales | `d762bd5` | Yes (Role A) |
| `results/charts/staircase.png` | Created | Chart 1 | `d762bd5` | Yes (Role A) |
| `results/charts/riskiest_pairs.png` | Created/modified | Chart 2 (recoloured by %below-k; title fix) | `d762bd5`, `62b5049` | Yes (Role A) |
| `results/charts/personas.png` | Created | Chart 3 | `d762bd5` | Yes (Role A) |
| `results/charts/risk_by_group.png` | Created | Chart 4 | `d762bd5` | Yes (Role A) |
| `results/charts/attack_before_after.png` | Created | Chart 5 | `62b5049` | Yes (Role A); reads `results/attack.json` produced jointly with Role B |
| `results/charts/fairness.png` | Created | Chart 6 | `62b5049` | Yes (Role A); reads `results/fairness.csv` produced by Role B |
| `.kiro/specs/role-a-risk-engine/requirements.md` | Created, deleted, restored | Role A spec (requirements) | `a0dd5c2`, deleted in `3190a15`, restored in `139171b` | Yes (Role A) |
| `.kiro/specs/role-a-risk-engine/design.md` | Created, deleted, restored | Role A spec (design) | `a0dd5c2`, deleted in `3190a15`, restored in `139171b` | Yes (Role A) |
| `.kiro/specs/role-a-risk-engine/tasks.md` | Created, deleted, restored | Role A spec (tasks) | `a0dd5c2`, deleted in `3190a15`, restored in `139171b` | Yes (Role A) |
| `docs/audit/role-a-audit.md` | Created | This report | (this commit) | Yes (Role A) |

Files flagged as NOT owned by Role A but touched/relied upon:
- `scripts/run_experiments.py` is a **shared** file. Role A wrote the baseline/combos/leaks/personas/risk-by-group/staircase section plus a `try/except ImportError` guard; Role B owns the mitigation / attack-before-after / fairness / utility / detection section below it.
- `results/attack.json` and `results/fairness.csv` are produced by the **Role B** mitigation section of `run_experiments.py`; Role A's charts 5 and 6 read them.
- `config.yaml` is **Role C**-owned; Role A only reads it (never modified by Role A).

## 3. Work log and decisions
Chronological, with reasons.

1. **Recreated Role A modules from the brief's Appendix A reference implementation** (`a0dd5c2`). Decision: copy the tested reference verbatim rather than rewrite. Alternative: write from scratch. Reason: the brief states the reference was tested on the real data and the section-7 interface contracts must not change; rewriting risked breaking the contracts other roles depend on. Follows the brief.
2. **`scripts/build_cache.py` made resilient to a missing `reid/plant.py`** (Role B's file). Decision: wrap the plant import in `try/except ImportError` so the clean parquet builds even before Role B merged. Alternative: the bare reference, which imports `plant` unconditionally. Reason: Role A should not be blocked waiting on Role B. Documented as a deviation in `.kiro/specs/role-a-risk-engine/design.md`.
3. **`scripts/run_experiments.py` Role B section guarded** with `try/except ImportError` on `reid.mitigate`/`reid.utility`. Reason: the Role A result files write standalone; the Role B section lights up after their modules merge. Deviation from the bare reference for the same non-blocking reason.
4. **Added `scripts/check_numbers.py`** (not in the brief). Decision: build a dedicated acceptance harness that re-reads the real parquet and asserts the section-4 numbers within ±0.2 points. Reason: give the team a one-command regression check as modules merged. This is an addition, not a deviation.
5. **Notebook built via a generator script, then the generator deleted.** Decision: author `notebooks/results.ipynb` through a temporary `nbformat` generator and execute with `nbconvert`, rather than hand-editing the notebook JSON. Reason: the executed notebook embeds large Plotly JSON that is fragile to edit by hand. The generator was a temporary tool and was removed after each run (not committed).
6. **Troubleshooting — pandas 3.1 incompatibilities in chart code.** Two bugs found and fixed during notebook execution: (a) `Series.str.split(" + ")` returned one column because the `+` was treated as regex — fixed with `regex=False`; (b) `DataFrame.applymap` was removed in pandas 3.0 — switched to `DataFrame.map`. Both caught by `nbconvert` execution failing, then fixed and re-run to 0 errors.
7. **Troubleshooting — missing dev dependencies.** `kaleido`, `ipykernel`, `nbformat`, `jupyter_client`, `nbconvert` (for the notebook) and later `streamlit`, `python-dotenv` (to test Role C's app) were not in the local `.venv` despite being in `requirements.txt`. Installed into `.venv` to run/verify. These are environment installs, not repo changes.
8. **Troubleshooting — notebook working-directory bug.** nbconvert runs with the notebook's folder as CWD, so `results/...` relative paths failed. Fixed by resolving the repo root by walking up to find `config.yaml`.
9. **Git episode — accidental spec deletion.** Teammate commit `3190a15` ("Risk Engine and attacks") deleted the entire `.kiro/specs/role-a-risk-engine/` folder. Detected on a `git pull`. Restored the three files from `62b5049` and committed as `139171b` ("Restore Role A spec deleted in 3190a15"). A push was rejected (teammate had pushed concurrently); resolved with `git pull --rebase` (clean, no conflicts) then push.
10. **Git episode — branch pointer drift.** An earlier `git pull origin main` while checked out on `role-a` fast-forwarded the `role-a` pointer onto the merged-main commit. Straightened out by checking out `main` and fast-forwarding it to `origin/main`.

## 4. Data used
- **`data/NSSE-synthetic.xlsx`** — source, BU IS&T synthetic NSSE data, sheet `in`. Read by `reid/load.py`. Not committed (gitignored).
- **`data/lookup-synthetic.xlsx`** — code→name lookup, sheet `in`. Read by `load_lookup`. Not committed.
- **`data/nsse_clean.parquet`** — produced by `build_clean_cache`; **shape (20731, 133)** = 132 source columns + `row_id` (verified: `scripts/check_numbers.py` prints `clean parquet shape: (20731, 133)`). Not committed.
- **`data/nsse_planted.parquet`** — produced by Role B's `plant.py` via `build_cache.py` (shape 20731 × 137 per earlier app-flow run, which sampled this file). Role A reads it in `run_experiments.py`. Not committed.
- **`data/pii_truth.parquet`** — PII ground truth from `plant.py`. Not committed.

Cleaning/transformations applied by `reid/load.py`: rename `First Time First Year`→`FTFY`; cast `MAJsecond` to `str` while keeping `NaN` as `NaN`; parse `logdate` as datetime; prepend `row_id` (0..n-1). Data quirks handled: `-9` kept as a valid category (not missing); `MAJsecond` mixed int/str/NaN cast to str; all risk group-bys use `dropna=False` so missing values form their own group; `row_id` is never part of any released file.

Gitignore confirmed (`git check-ignore`): `data/nsse_clean.parquet`, `data/NSSE-synthetic.xlsx`, `keys/vault.key`, `.env` are all ignored. `git ls-files data/ keys/ .env` returns empty — nothing from those paths is tracked.

## 5. Methods
- **Equivalence classes / k-anonymity** (`reid/risk.py`, `class_sizes`, `risk_summary`): group records by identical quasi-identifier (QI) values; class size = number of records sharing those values; k-anonymity = minimum class size ≥ k. Default **k=5** (`config.yaml` `targets.k`), the common statistical minimum-cell threshold. `pct_unique` = share in size-1 classes; `pct_below_k` = share in classes < k; `avg_risk` = mean of 1/size; `max_risk` = 1/min size. All group-bys `dropna=False`.
- **Riskiest combinations** (`riskiest_combos`, `max_size=3`): enumerate all QI combinations up to size 3 (129 for 9 QIs), rank by uniqueness. Shows which field pairs/triples drive risk.
- **Metadata leaks** (`metadata_leaks`): uniqueness of `logdate`/`duration` alone and combined with Class+affiliation — survey paradata as a hidden quasi-identifier.
- **l-diversity** (`l_diversity_report`): within classes of size ≥ 2, count distinct values of each sensitive engagement scale; ignores classes where nobody answered. Reports l_min and share of classes with l≤1.
- **Risk by group** (`risk_by_group`, `group_col=affiliation`): uniqueness/below-k per demographic group — the fairness lens.
- **Attacker personas** (`persona_risk`): 5 personas, each a set of fields a real adversary might know (classmate, club_roster, linkedin, survey_insider, everything), from `config.yaml` `personas`.
- **Simulated linkage attack** (`linkage_attack`): sample **n=200** targets with **seed=42** (`config.yaml` `attack`), join their known fields against the (optionally generalized via `transform`) release; NaN matches NaN; a target is "correctly re-identified" only when exactly one release row matches and its `row_id` is theirs. Reports `correct_rate`. Seed/sample fixed for reproducibility across before/after.

## 6. Results ledger
All values re-read from committed files or reproduced by re-running `scripts/check_numbers.py`.

| Metric | Value | Source (file + key/column, or command) | How computed | Caveats |
|---|---|---|---|---|
| % unique, 8 core fields | 67.80% | `results/baseline_risk.json` → `core8.pct_unique` (0.6779701895711736) | `risk_summary` k=5 on 8 QIs | Synthetic data |
| % below k=5, 8 core | 89.87% | `results/baseline_risk.json` → `core8.pct_below_k` | same | — |
| % unique, 9 core (adds FTFY) | 67.80% | `results/baseline_risk.json` → `core9.pct_unique` | same | FTFY adds nothing (identical to core8) |
| % unique, 14 fields | 73.87% | `results/baseline_risk.json` → `extended14.pct_unique` (0.738748733780329) | `risk_summary` on core9 + 5 attend_* | — |
| % below k=5, 14 fields | 90.85% | `results/baseline_risk.json` → `extended14.pct_below_k` | same | — |
| % unique, all QIs + metadata | 99.99% | `results/baseline_risk.json` → `with_metadata.pct_unique` (0.999903526120303) | `risk_summary` on extended14 + logdate + duration | "nearly 100%" claim |
| logdate alone % unique | 11.66% | `results/leaks.csv` row `logdate` | `metadata_leaks` k=5 | — |
| duration alone % unique | 11.62% | `results/leaks.csv` row `duration` | same | — |
| logdate+Class+affiliation % unique | 22.89% | `results/leaks.csv` | same | — |
| Riskiest pair (by % unique), MAJfirst+MAJsecond | 5.35% unique / 10.84% below k | `results/combos.csv` row `MAJfirstcode + MAJsecondcode`, size 2 | `riskiest_combos` | pairs rarely make anyone fully unique |
| riskiest_combos row count | 129 | `scripts/check_numbers.py` output | C(9,1)+C(9,2)+C(9,3) | runs <2s |
| Persona classmate % unique | 0.99% | `results/personas.csv` `classmate.pct_unique` (0.009888…) | `persona_risk` k=5 | — |
| Persona club_roster % unique | 0.53% | `results/personas.csv` | same | — |
| Persona linkedin % unique | 25.97% | `results/personas.csv` | same | — |
| Persona survey_insider % unique | 22.89% | `results/personas.csv` | same | — |
| Persona everything % unique | 67.80% | `results/personas.csv` | same | equals 8-core |
| Linkage attack, everything, before | 68.5% (137/200) | `results/attack.json` → `protect_on.everything.before.correct_rate` (0.685); confirmed by `check_numbers.py` | `linkage_attack` seed=42 | 200 targets |
| Linkage attack, everything, after | 0.0% (0/200) | `results/attack.json` → `protect_on.everything.after.correct_rate` | `linkage_attack` with mitigation `transform` | after = Role B mitigation applied |
| Linkage attack, linkedin, before→after | 27% → 0% | `results/attack.json` → `protect_on.linkedin` | same | — |
| Linkage attack, survey_insider, before→after | 24% → 0% | `results/attack.json` → `protect_on.survey_insider` | same | — |
| Risk by group, Gray mouse lemur (n=864) | 98.84% below k | `results/risk_by_group.csv` | `risk_by_group` core9 | smallest group, highest risk |
| Risk by group, Ring-tailed lemur (n=10460) | 84.69% below k | `results/risk_by_group.csv` | same | largest group, lowest risk |
| l-diversity, l_min across scales | 1 | `results/l_diversity.csv` `l_min` column (all rows = 1) | `l_diversity_report` | at least one class has a single sensitive value |

Note: `baseline_risk.json` `core8` and `core9` are identical because adding `FTFY` to the other 8 fields changes nothing (FTFY is derivable within existing groups).

## 7. Validation and tests
| Check | What it verified | Expected | Actual | Pass/Fail | When / commit |
|---|---|---|---|---|---|
| `scripts/check_numbers.py` (full) | Loading + 13 risk/attack reference numbers on real clean data | 13 within ±0.2 pts | 13/13 pass, printed | PASS | re-run this session on HEAD `139171b` |
| Loading acceptance | shape, ID unique, FTFY present, MAJsecond str/NaN, parquet reload | (20731,133), <2s | (20731,133), 0.06s | PASS | this session |
| Risk acceptance | 8-core 67.8%/89.9%, 14-field 73.9%, leaks 11.7/11.6/22.9%, combos=129 | match | match | PASS | this session |
| Attack acceptance (raw) | everything 137/200=68.5%; persona uniqueness | match | match | PASS | this session |
| Attack after mitigation | everything → 0% with Role B `transform` | 0% | 0% (`results/attack.json`) | PASS | after Role B merge |
| `scripts/smoke_test.py` (Role C's, full agent) | end-to-end load→classify→agent on 3000-row sample | k≥5, 0% unique after, no PII in release | k_min=5, pct_unique_after=0.0, attack 89%→0% | PASS | this session after full merge |
| Notebook execution (`nbconvert`) | all code cells run, 6 PNGs produced | 0 error outputs | 0 error outputs, 7/7 cells, 6 charts | PASS | `62b5049` |

Checks that initially FAILED and the fix:
- Notebook cell 2 `FileNotFoundError` for `results/staircase.csv` — cause: nbconvert CWD is the notebook folder; fix: resolve repo root by walking up to `config.yaml`.
- Notebook heatmap `KeyError: 1` — cause: `str.split(" + ")` treated `+` as regex, returned 1 column; fix: `regex=False`.
- Notebook `AttributeError: 'DataFrame' object has no attribute 'applymap'` — cause: removed in pandas 3.0; fix: `DataFrame.map`.

## 8. AI and LLM usage
- **Role A code uses NO LLM.** `reid/load.py`, `reid/risk.py`, `reid/attacks.py` are pure pandas/NumPy; they do not import `reid.llm`. (The LLM is used only in Role C's `classify.py`/`agent.py`, out of scope here.) No student rows and no data of any kind are sent anywhere by Role A code.
- **Kiro usage for Role A:** created the spec `.kiro/specs/role-a-risk-engine/` with `requirements.md` (6 EARS-format requirements), `design.md` (architecture + component contracts + one documented deviation), and `tasks.md`. Per `tasks.md`, tasks 1–6 (load, risk engine, attacks, build_cache, run_experiments Role A section, section-4 verification incl. the attack-after-mitigation subtask) are checked complete; tasks 7 (pitch charts) and 8 (share caches + post numbers) are shown unchecked in `tasks.md` even though the charts were in fact produced (`notebooks/results.ipynb`, 6 PNGs in `results/charts/`) and verified — i.e. the checkboxes lag the actual work. Steering files used (shared): `.kiro/steering/product.md`, `structure.md`, `tech.md`.

## 9. Ethics, privacy, and security
- **Never committed:** `data/` (all parquets + source xlsx), `keys/`, `.env` — confirmed by `git check-ignore` (all ignored) and `git ls-files data/ keys/ .env` (empty).
- **No row-level data leaves the pipeline from Role A:** risk/attack functions operate in-process and return only aggregate metrics; the charts notebook reads only `results/` aggregate files, explicitly no row data.
- **Pseudonymization/key separation** are Role B concerns (tokens.py/vault); Role A does not handle keys.
- **Fairness:** `risk_by_group` and the fairness chart make per-group suppression visible (the central equity finding).
- **Transparency/accessibility:** charts use the colorblind-safe `px.colors.qualitative.Safe` palette, text labels on every bar, percent-formatted axes, plain-language titles.
- **Leak scan scope:** I verified the **current tracked files** only (working tree + `git ls-files`), not the full history. UNVERIFIED: whether any earlier commit ever added and later removed a data/key file in history (no evidence of it, but not exhaustively scanned).

## 10. Known issues and limitations
- **`reid.pii_text` import fails locally** — `presidio_analyzer` not installed in `.venv`. **Low** impact for Role A (only affects Role B's PII detection experiments; risk/attacks/agent all run). Environment, not code.
- **Notebook requires pandas ≥ 2.1 behaviour** (uses `DataFrame.map`, `str.split(regex=False)`); verified on pandas 3.1.0. **Low** — matches `requirements.txt` (`pandas>=2.0`), though the `applymap`/`regex` fixes specifically need ≥2.1/modern pandas.
- **`role-a` branch is 7 commits behind `main`** (local & origin `role-a` = `62b5049`; `main` = `139171b`). All Role A work is already on `main`; `role-a` just wasn't fast-forwarded. **Low** (bookkeeping).
- **`tasks.md` checkboxes for tasks 7–8 are unchecked** despite the work being done. **Low** (documentation lag).
- **Methodological:** k-anonymity does not prevent attribute inference (l_min=1 in `l_diversity.csv` shows some classes are not l-diverse); the linkage attack models only our 5 personas; "after = 0%" depends on Role B's mitigation `transform`. **Medium** — important to state honestly in the pitch.
- **Dev dependencies missing from a fresh `.venv`** (kaleido/ipykernel/nbconvert/streamlit) had to be pip-installed to run the notebook/app. **Low–Medium** — teammates reproducing the charts need those installed (Role C updated `requirements.txt`).

## 11. Claims to make and claims to avoid
Accurate claims (each tied to a ledger row):
- "Using 8 ordinary fields, 67.8% of students are uniquely identifiable" (baseline_risk.json core8).
- "74% with prior-attendance flags, ~100% with survey timing" (extended14 73.9%, with_metadata 99.99%).
- "A simulated attacker knowing all core fields re-identifies 68.5% of 200 targets; 0% after our fix" (attack.json protect_on.everything).
- "Survey timing alone makes 11.7% of students unique" (leaks.csv logdate).
- "The smallest group is in a <5 cell 98.8% of the time vs 84.7% for the largest" (risk_by_group.csv).

Claims to AVOID:
- Do NOT claim FERPA compliance or that the data is "anonymous" — tokenized/mitigated data is pseudonymous and k-anonymity has known limits (l_min=1).
- Do NOT claim the attack figures generalize beyond the 5 modelled personas or beyond this synthetic dataset.
- Do NOT present "0% after" as absolute safety — it is 0% re-identification for these 200 seeded targets under this release/transform.
- Do NOT cite the 68.5%/0% as real-student results — the data is synthetic.

## 12. Presentation material
Talking points (Role A's ~1 min of the pitch):
1. "No names, yet 8 ordinary fields single out 67.8% of students — removing names is not anonymity."
2. "Each added field ratchets up uniqueness: 2 fields ≈ 0%, 8 fields 67.8%, with survey timing ≈ 100%."
3. "We modelled real attackers: a LinkedIn-level adversary re-identifies 26%, an all-fields adversary 68.5% of 200 targets."
4. "Risk is not evenly distributed — the smallest demographic group sits in an unsafe cell 98.8% of the time vs 84.7% for the largest."
5. "After the fix, the same attack drops to 0%."

Best charts (from `results/charts/`):
- `staircase.png` — opening slide: uniqueness climbing as fields are added.
- `attack_before_after.png` — the money shot: 68.5% → 0%.
- `risk_by_group.png` / `fairness.png` — the equity insight (who is most exposed / who pays).

One-sentence key insight: **Ordinary, "harmless" survey fields combine to single out two-thirds of students, and that risk falls hardest on the smallest groups.**

## 13. Open items and questions for the team
- **`role-a` is behind `main` by 7 commits** — not a problem (all A work is on main), but the team should decide whether to keep fast-forwarding feature branches or treat `main` as the source of truth. (This audit commits to `role-a` per instructions, which will add 1 commit on top of `62b5049`.)
- **`tasks.md` tasks 7–8 unchecked** though done — someone should tick them for an accurate spec.
- **Cross-role contract:** charts 5–6 depend on Role B's `results/attack.json` and `results/fairness.csv` schemas (`protect_on`/`protect_off`, `setting` column). If Role B regenerates with different keys, the notebook's section 5/6 must track it.
- **Shared file `scripts/run_experiments.py`:** confirm Role B is the single owner of the mitigation/detection section to avoid future merge conflicts.
- **Heads-up (resolved):** the Role A spec was accidentally deleted in `3190a15` and restored in `139171b`; ensure no stale branch re-deletes it on merge.
- UNVERIFIED for the team: full git-history leak scan (only current tracked files were checked).

## 14. Git state
- **Current branch at report time:** `main` (HEAD `139171b` "Restore Role A spec deleted in 3190a15"), in sync with `origin/main`.
- **Role A branch:** local `role-a` = `origin/role-a` = `62b5049` ("Role A: attack and fairness charts"), pushed. `role-a` is behind `main` by 7 commits; `main` contains all Role A commits (`a0dd5c2`, `d762bd5`, `62b5049`) plus the spec restore.
- **Merged into main?** Yes — all Role A work (`a0dd5c2`, `d762bd5`, `62b5049`, and restore `139171b`) is on `origin/main`.
- **Uncommitted/untracked at report time:** none from `data/`, `keys/`, `.env`. Any `scripts/_*.txt` temp files used during this audit were deleted. This report (`docs/audit/role-a-audit.md`) will be the only new file committed, to branch `role-a`.
