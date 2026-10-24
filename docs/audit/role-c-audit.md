# Role C Audit Report

> Scope note: "verify, don't recall." Every fact below is sourced to a repo file, a git command
> run this session, a `.kiro` spec, or a `results/` file. Items that could not be executed in this
> environment (no dependencies, no `.env`, no `data/` parquet files installed) are marked UNVERIFIED
> with the reason. Role C owns the orchestration/UI layer, not the risk or mitigation math, so most
> numeric results in the ledger were *produced by Role A/B scripts* and are consumed/displayed by
> Role C; that provenance is stated per row.

## 1. Summary

Role C owns the user-facing and orchestration layer: the metadata-only LLM wrapper (`reid/llm.py`),
the column-role classifier (`reid/classify.py`), the privacy agent that runs measure → plan → act →
verify → report (`reid/agent.py`), the config loader (`reid/config.py` + `config.yaml`), the six-tab
Streamlit app (`app.py`), the smoke-test merge gate (`scripts/smoke_test.py`), and the project
`README.md` / `.env.example` / `requirements.txt`. This session added Gemini support through the
OpenAI-compatible endpoint, a connection diagnostic (`scripts/check_llm.py`), the `role-c-agent-app`
spec, and finalized the README and submission drafts with verified numbers. Current state: code is
written, committed, and merged into `main`; it is **not runtime-verified this session** because
dependencies, `.env`, and data files are absent from this machine. So: **partially working (written and
merged, end-to-end run UNVERIFIED here)**.

## 2. Files

| File | Created/Modified | Purpose (one line) | Commit(s) | Owned by Role C per steering? |
|---|---|---|---|---|
| `reid/llm.py` | Modified | Swappable LLM wrapper; added `OPENAI_BASE_URL` for Gemini | `5fd57bd`, `e48e520` | Yes |
| `reid/classify.py` | (prior) | Metadata-only column profiling + role classification | `e48e520` | Yes |
| `reid/agent.py` | (prior) | Privacy agent pipeline `run_agent` | `e48e520` | Yes |
| `reid/config.py` | (prior) | `load_config()` reads `config.yaml` | `e48e520` | Yes |
| `config.yaml` | (prior) | Targets, roles, personas, utility, data paths | `e48e520` | Yes |
| `app.py` | (prior) | Six-tab Streamlit UI | `e48e520` | Yes |
| `scripts/smoke_test.py` | (prior) | Merge-gate integration check | `e48e520` | Yes |
| `scripts/check_llm.py` | Created | One-call LLM connection diagnostic | `5fd57bd` | **Not listed in steering** (added pragmatically; see §10) |
| `README.md` | Modified | Project README; LLM section + final numbers | `5fd57bd`, `e48e520`, and `main` commit `253384d` | Yes |
| `requirements.txt` | Modified | Switched LLM SDK to `openai` | `5fd57bd`, `2c8f3b4`, `e48e520` | Yes |
| `.env.example` | Modified | Safe placeholders + Gemini block | `5fd57bd`, `677c846`, `e48e520` | Yes |
| `docs/submission_drafts.md` | Modified | Sundai + Devpost final text | `main` commit `253384d`; prior `e48e520` | Shared docs (not code-owned; Role C edited submission text) |
| `.kiro/specs/role-c-agent-app/{requirements,design,tasks}.md` | Created | Role C spec | `d52bcfc` | Yes |
| `docs/audit/role-c-audit.md` | Created (this report) | This audit | pending commit | Yes (docs) |

Source for ownership: `.kiro/steering/tech.md` lists Role C as owner of `config.yaml`, `reid/config.py`,
`reid/llm.py`, `reid/classify.py`, `reid/agent.py`, `app.py`, `scripts/smoke_test.py`, `README.md`,
`requirements.txt`, `.gitignore`, `.env.example`.
Source for commits: `git log --oneline -- <file>` run this session.
**Flag:** `scripts/check_llm.py` is NOT in the steering ownership list — it was created this session as a
dev diagnostic. No Role A/B files were modified by Role C.

## 3. Work log and decisions

Chronological, with rationale. (Commit hashes from `git log`.)

1. **`e48e520 "Add privacy risk meter prototype"`** — initial Role C code (llm/classify/agent/config/app/
   smoke_test) plus other scaffolding. (Pre-existing before this session's edits; baseline.)

2. **Spec `role-c-agent-app` (`d52bcfc`)** — created requirements/design/tasks for Role C. Decision: ground
   the spec in the existing code + steering files because no external "Role C brief" was available to paste.
   Alternative considered: wait for the brief. Reason for choosing: the steering files unambiguously define
   Role C ownership, so the spec documents real behavior. Deviation note: tasks.md checkboxes are all left
   unchecked `[ ]` even though the code exists (see §8), so the spec reads as "planned" rather than "done."

3. **Gemini enablement (`5fd57bd "Enable Gemini via OpenAI-compatible endpoint; add LLM diagnostic"`)**:
   - **Decision:** make the OpenAI client honor `OPENAI_BASE_URL` so a free Google AI Studio (Gemini) key
     works via Gemini's OpenAI-compatible endpoint. Code: `base_url = os.getenv("OPENAI_BASE_URL"); client =
     OpenAI(base_url=base_url) if base_url else OpenAI()` (`reid/llm.py`).
   - **Alternatives:** (a) use Anthropic (what `requirements.txt` originally installed); (b) add a native
     Gemini SDK path. **Chosen** the OpenAI-compatible route because it's free, needs one line, and reuses the
     existing OpenAI code path.
   - **Verification of the approach:** a web search this session confirmed Gemini's OpenAI-compatible endpoint
     accepts `max_tokens` (which the code sends). This is an external claim, not a live test.
   - `requirements.txt`: switched to install `openai` (commented `anthropic`).
   - `.env.example`: a previous state had active (uncommented) `OPENAI_*` lines with placeholder-but-live-
     looking values — a committed-hygiene issue. **Fixed** to all-commented placeholders + a documented Gemini
     block.
   - `scripts/check_llm.py`: added to diagnose connection issues fast.

4. **Troubleshooting episodes (this session):**
   - **Python 3.14 only / no deps:** `py -0p` showed only Python 3.14; `import streamlit`/`openai` failed
     (`ModuleNotFoundError`). Resolution: advised installing Python 3.11/3.12 for a venv (spaCy/presidio wheels
     lag on 3.14). Not resolved in-repo; it's an environment action for the user.
   - **OneDrive vs git:** the repo lives under `OneDrive\Documents`. `git checkout` between branches hung on a
     Windows "Deletion of directory failed (y/n)" prompt for `.kiro/specs/role-a-risk-engine` and left a stale
     `.git/index.lock`; hung `git.exe` processes swallowed subsequent commands. Resolution: pause OneDrive
     syncing before branch switches; after pausing, `git checkout main` and later merges ran cleanly. This is
     documented as the #1 git gotcha.
   - **Push rejected on `main`:** when finalizing README/drafts, `git push origin main` was rejected because a
     teammate pushed `ea8c951` first. Per plan, fetched + merged (`ort` strategy, no conflicts, merged a Role B
     `.config.kiro` restore) then pushed. Final `origin/main` = `0a2e33d`.

5. **README + submission finalization (on `main`, commit `253384d`, now under merge `0a2e33d`)** — filled the
   README results table and PII tables with verified numbers from `results/`, wrote Sundai card + Devpost
   sections in `docs/submission_drafts.md`. Team labels kept as A/B/C per user instruction. `VIDEO_URL` and
   `GITHUB_URL` left as literal placeholders pending Role B's video.

## 4. Data used

Role C code does **not** produce dataset files; it reads them and displays metrics. Relevant paths from
`config.yaml`:
- `data/nsse_clean.parquet`, `data/nsse_planted.parquet`, `data/pii_truth.parquet` (produced by Role A/B
  scripts, gitignored).
- Source Excel: `data/NSSE-synthetic.xlsx`, `data/lookup-synthetic.xlsx` (gitignored).
- `app.py` loads `cfg["data"]["planted_parquet"]` for the built-in dataset; `scripts/smoke_test.py` reads the
  same and samples 3,000 rows (`random_state=1`).
- **Shapes:** `results/baseline_risk.json` reports n = 20,731 students for the full dataset. Column count is
  not independently re-derived here (data files absent this session) → row count VERIFIED via results file,
  exact column count UNVERIFIED this session.
- **Quirks handled (in Role C code):** `app.py` `read_upload()` renames `First Time First Year` → `FTFY` and
  injects `row_id` if absent; `classify.profile_columns` skips `row_id` and emits at most 8 category labels.
  The `-9`-as-real-category and `MAJsecond`-as-str conventions are steering rules (`tech.md`), enforced mainly
  in Role A/B code.
- **Gitignore confirmation:** `.gitignore` excludes `data/`, `keys/`, `.env`, `*.parquet`, `*.pkl`,
  `results/raw/`. A full-history secret scan this session (`git log --all -p | Select-String`) found no real
  keys committed. A tracked-file check (`git ls-tree -r origin/main`) found no `data/`, `keys/`, `.env`, or
  parquet tracked.

## 5. Methods (Role C–implemented)

- **Metadata-only column profiling** (`classify.profile_columns`): emits per-column dtype, n_unique,
  pct_missing, pct_unique_values, optional top ≤8 category labels, optional avg_text_len; excludes `row_id`.
  Purpose: give the classifier/LLM enough signal without sending rows. Key guardrail: ≤8 labels per column.
- **Role classification** (`classify.classify_columns`, 8 roles in `ROLES`): schema prior
  (`roles_from_config`) → deterministic heuristic (`_heuristic`) → optional LLM upgrade. `derived` columns are
  never overwritten by the LLM. Batch size 40.
- **LLM wrapper** (`reid/llm.py`): `complete(prompt, system, json_mode, max_tokens=800)`; returns `None` on
  disabled/error; `parse_json` strips code fences and falls back to a regex object/array match. Providers:
  `anthropic` (default model `claude-haiku-5-5`) or `openai` (model from `LLM_MODEL`, optional
  `OPENAI_BASE_URL`).
- **Privacy agent** (`agent.run_agent`): measure baseline risk on quasi-ids and quasi-ids+metadata; LLM or
  deterministic 3-sentence plan; tokenize direct ids + `student_id` and drop other planted PII; drop or
  Presidio-scrub free text per `scrub_comments`; `greedy_generalize` to `target_k` (default 5) within
  `max_suppression` (default 0.05), honoring `protect` for the group column; re-run per-persona linkage
  attacks before/after; compute utility + fairness; build `privacy_label` and `write_report`. Note: the
  underlying risk/attack/mitigation/utility functions are Role A/B's; Role C orchestrates them.
- **Parameters and why** (from `config.yaml`): `k=5` (a common k-anonymity floor), `max_suppression=0.05`
  (≤5% record loss budget), `max_group_suppression=0.10`, attack `n_targets=200`, `seed=42`. These live in
  config, read by Role C's loader.

## 6. Results ledger

Every number that could surface in README/pitch. **Provenance is explicit**: Role C *displays* these; Role
A/B *computed* them via `scripts/run_experiments.py`. Values re-read from `results/` this session.

| Metric | Value | Source (file + key/column) | How computed | Caveats |
|---|---|---|---|---|
| Unique, 8 core fields | 67.80% | `results/baseline_risk.json` → `core8.pct_unique` = 0.6779701895711736 | share of rows unique on 8 quasi-ids | synthetic data; `core8`==`core9` value in file |
| Unique, 9 core fields | 67.80% | `results/baseline_risk.json` → `core9.pct_unique` | same, 9 fields | identical to core8 in file |
| Unique, 14 fields | 73.87% | `results/baseline_risk.json` → `extended14.pct_unique` = 0.738748733780329 | 14 quasi-ids | — |
| Unique, incl. timing | 99.99% | `results/baseline_risk.json` → `with_metadata.pct_unique` = 0.999903526120303 | adds logdate/duration | README rounds to "~100%" |
| Staircase (8 fields) | 67.80% | `results/staircase.csv` row n_fields=8, pct_unique=0.6779701895711736 | cumulative field add | — |
| Staircase (14 fields) | 73.87% | `results/staircase.csv` n_fields=14 | — | — |
| Linkage attack "everything" before | 68.5% | `results/attack.json` → `protect_on.everything.before.correct_rate` = 0.685 | 200 targets, attacker knows 9 core fields | — |
| Linkage attack "everything" after | 0.0% | `results/attack.json` → `protect_on.everything.after.correct_rate` = 0.0 | post-mitigation | holds for all 5 personas |
| Records removed (protect on) | 2.50% | `results/mitigation_summary.json` → `protect_on.pct_suppressed` = 0.02503497178139019 | suppressed mask mean | — |
| Records removed (protect off) | 3.54% | `results/mitigation_summary.json` → `protect_off.pct_suppressed` = 0.03535767690897689 | — | protect_off coarsens `affiliation` to level 2 and marks it "lost" |
| k_min after | 5 | `results/mitigation_summary.json` → `protect_on.final_risk.k_min` = 5 | smallest group size | target met |
| ML utility R² original | 0.419 | `results/mitigation_summary.json` → `protect_on.ml.r2_original` | predict SE | README rounds 0.42 |
| ML utility R² release (protect on) | 0.367 | `protect_on.ml.r2_release` = 0.3668401283933783 | — | README rounds 0.37 |
| Fairness: worst group (protect on) | Diademed sifaka 6.89% | `results/fairness.csv` setting=protect_on, pct_suppressed=0.06893542757417102 | records removed by group | — |
| Fairness: largest group (protect on) | Ring-tailed lemur 0.85% | `results/fairness.csv` pct_suppressed=0.008508604206500956 | — | — |
| Fairness gap | ≈8.1× | derived: 0.0689/0.0085 | ratio worst/largest | "up to ~8×" is accurate |
| PII detection — PERSON | P=1.00, R=0.910 | `results/detection.csv` PERSON row (tp 212, fp 0, fn 21) | Presidio+spaCy on planted sample | — |
| PII detection — EMAIL | P=1.00, R=1.00 | `results/detection.csv` EMAIL_ADDRESS | — | — |
| PII detection — PHONE | P=1.00, R=1.00 | `results/detection.csv` PHONE_NUMBER | — | — |
| PII detection — BU_ID | P=1.00, R=1.00 | `results/detection.csv` BU_ID | — | — |
| PII detection — ALL | P=1.00, R=0.966 | `results/detection.csv` ALL row | — | — |
| Stress test names | P≈0.90, R≈0.90 | `results/detection_stress_test.csv` (20 rows) | **derived** by counting: 10 name rows, 9 found, 1 MISS ("Ana Ruiz"), 1 false alarm ("Agganis Arena") → R=9/10, P=9/10 | NOT a stored metric; derived in-report |

## 7. Validation and tests

| Check | What it verifies | Expected | Actual | Pass/Fail | Date/commit |
|---|---|---|---|---|---|
| `scripts/smoke_test.py` (code assertions) | profile→classify→`run_agent` on 3,000-row sample (LLM off); asserts `after.k_min >= 5`, `pct_unique_after == 0.0`, no `full_name/email/comment` in release | prints "OK in ...s" | **UNVERIFIED this session** — could not run (no deps/data). Assertions are present in committed `scripts/smoke_test.py` @ `e48e520` | N/A (not executed) | n/a |
| `reid/llm.py` syntax | file parses | parse OK | `ast.parse` → "llm.py OK" | Pass | this session |
| `scripts/check_llm.py` syntax | file parses | parse OK | `ast.parse` → "check_llm.py parses OK" | Pass | this session |
| Live Gemini call via `check_llm.py` | one real LLM round-trip | "live call SUCCEEDED" | **UNVERIFIED** — `openai` not installed, no `.env` key here | N/A | n/a |
| Results-number cross-check | README/pitch numbers match `results/` | match | all 8 result files re-read; values match ledger §6 | Pass | this session |
| Full-history secret scan | no real keys in any commit/branch | no matches | only placeholders/docs matched (`your-ai-studio-key`, var-name mentions); no `AIza`/`sk-`/`sk-ant-` | Pass | this session |
| Tracked-file hygiene | no data/keys/.env/parquet tracked | none | `git ls-tree -r origin/main` → none | Pass | this session |

Initially-failed items this session: the `git push origin main` (rejected, then fetch+merge+push fixed it);
the branch-switch hang (fixed by pausing OneDrive). Both documented in §3.

## 8. AI and LLM usage

**LLM in Role C code:**
- Used in `reid/classify.py` (classify columns), `reid/agent.py` (`_plan`, `write_report`). All calls go
  through `reid/llm.py`.
- **What is sent:** column metadata and computed metrics only — profiles (names, dtypes, counts, ≤8 category
  labels) and aggregate facts (e.g. pct_unique, levels). Confirmed by reading `classify.py` (sends the
  `profile` list) and `agent.py` (`_plan`/`write_report` send JSON of metrics). **No student rows are sent.**
  Exception to note: free-text *planted synthetic comments* are scrubbed by Presidio locally (Role B code),
  not sent to the LLM.
- **Fallback:** `llm.complete()` returns `None` when disabled or on any exception; every caller has a
  deterministic path (heuristic roles, deterministic plan, deterministic Markdown report).
- **Provider/model config (no keys):** `LLM_PROVIDER` ∈ {none, anthropic, openai}; `LLM_MODEL`; optional
  `OPENAI_BASE_URL` (Gemini via AI Studio OpenAI-compatible endpoint:
  `https://generativelanguage.googleapis.com/v1beta/openai/`). Documented in `.env.example` and README.

**Kiro usage for Role C:**
- Spec created: `.kiro/specs/role-c-agent-app/` (requirements.md, design.md, tasks.md), commit `d52bcfc`.
- Steering used: `.kiro/steering/product.md`, `structure.md`, `tech.md` (ownership, conventions, safety rules).
- Tasks completed vs remaining: `tasks.md` lists 6 task groups (config loader, LLM wrapper, classifier, agent
  pipeline, Streamlit app, smoke-test gate). **All checkboxes are `[ ]` unchecked.** The corresponding code
  exists and is merged, so functionally the work is done, but the spec's task list was not ticked off —
  treat tasks.md as not reflecting completion state (a documentation gap, not missing code).

## 9. Ethics, privacy, and security

- **Never committed:** `data/`, `keys/`, `.env`, `*.parquet`, `*.pkl` (`.gitignore`), verified by
  `git ls-tree` showing none tracked.
- **Key/vault separation:** tokenization (Role B) stores originals in an encrypted vault under `keys/` with a
  separate key; README states tokenized data is pseudonymous, not anonymous.
- **LLM privacy:** metadata/metrics only, never rows (see §8).
- **Fairness:** the agent computes a fairness report (who loses records) and the app surfaces it; the
  "protect small groups" toggle prevents the optimizer from deleting the demographic column.
- **Transparency:** plain-English report + privacy nutrition label; agent step log shown in the app.
- **Accessibility:** charts use a colorblind-safe palette (`px.colors.qualitative.Safe` in `app.py`).
  Full WCAG compliance is NOT validated (would require assistive-tech testing) → UNVERIFIED.
- **Leak scans:** (a) current-files scan of `origin/main` tip — clean; (b) full-history scan across all
  branches (`git log --all -p`) — clean (only placeholders/doc text matched). Scope stated so another role
  need not repeat it.

## 10. Known issues and limitations

| Issue | Impact |
|---|---|
| App never run end-to-end this session (no deps/data/.env) — runtime behavior UNVERIFIED | **High** (submission claims "works"; must be confirmed on Role B's machine) |
| Live Gemini connection unproven; wrapper silently falls back to rule-based on any error, so a bad model name looks like "no LLM" | **Medium** |
| `scripts/check_llm.py` not in Role C's steering ownership list | **Low** (harmless helper; flag for strict ownership) |
| `role-c-agent-app/tasks.md` checkboxes all unchecked despite code existing | **Low** (doc/evidence mismatch; fix before judging if Kiro task-completion is scored) |
| Python 3.14 lacks spaCy/presidio wheels; needs 3.11/3.12 venv | **Medium** (blocks install if not handled) |
| Repo inside OneDrive breaks git branch switches unless OneDrive paused | **Medium** (process risk during crunch) |
| Finalized README (67.8% table) is on `main`/`origin/main`, NOT on `role-c` | **Medium** (see §14; `role-c` README is the older version) |
| Exact dataset column count not re-derived (data absent) | **Low** |
| Stress-test P/R derived by hand-count, not a stored metric | **Low** (documented in §6) |

## 11. Claims to make and claims to avoid

**Safe to claim (each tied to a §6 ledger row):**
- "68% of students are unique on eight ordinary fields" (ledger: core8 0.678).
- "An attacker knowing all nine core fields re-identifies 68.5% of 200 targets; 0% after mitigation" (attack.json).
- "Reaches k≥5 removing only 2.5% of records" (mitigation_summary protect_on).
- "ML utility R² 0.42 → 0.37" (mitigation_summary).
- "The smallest group loses ~8× more records than the largest" (fairness.csv, ratio 6.89%/0.85%).
- "Email/phone/BU-ID detection at 1.00 precision and recall; names 1.00 precision / 0.91 recall" (detection.csv).
- "The LLM only sees column metadata and computed metrics, never student rows" (code-verified, §8).

**Do NOT claim:**
- "FERPA compliant" — explicitly disclaimed; this is a risk meter, not a certificate.
- "The app is fully tested / verified working" — end-to-end run is UNVERIFIED this session.
- "Anonymous data" — output is pseudonymous (vault can re-link).
- "Gemini is confirmed connected" — no live call succeeded here.
- Any claim that names are detected perfectly — recall is 0.91 (tuned) / ~0.90 (out-of-sample).

## 12. Presentation material

**Talking points (Role C):**
1. "An AI agent labels each column's privacy role from metadata only — never from student rows."
2. "One click runs the whole pipeline: measure → plan → fix → verify → report, in the app's six tabs."
3. "The agent runs with or without an LLM; the data science stands on its own, the LLM just writes the
   plain-English plan and report."
4. "We wire in Gemini for free via its OpenAI-compatible endpoint — one config line, no vendor lock-in."
5. "The nutrition label and report make the tradeoffs legible to a non-technical data steward."

**Best charts (from `results/charts/`):**
- `staircase.png` — shows each added field making more students unique (sets up the problem).
- `attack_before_after.png` — 68.5% → 0% linkage attack (the headline fix).
- `fairness.png` — who pays for privacy (the equity insight).

**Key insight (one sentence):** The privacy fix is not evenly paid — without a safeguard the optimizer hides
the cost by deleting the demographic column, and with it the smallest groups lose up to ~8× more records.

## 13. Open items and questions for the team

- **Video:** `VIDEO_URL` (README + submission_drafts) still a placeholder — need Role B's link to run the tag
  step and finish submission.
- **End-to-end run:** needs a machine with deps + data + `.env` (Role B is running the app) to confirm the
  agent and Gemini actually work. Please report the smoke-test output and sidebar LLM status.
- **Branch/README divergence:** the finalized README lives on `main` (`0a2e33d`), not on `role-c`. Decide
  whether `role-c` should be re-synced from main or retired (A and B are already merged into main).
- **tasks.md:** should Role C's spec task checkboxes be ticked to reflect the merged code? (Matters only if
  Kiro task-completion is judged.)
- **Cross-role contract:** `agent.run_agent` depends on Role A `risk/attacks` and Role B
  `mitigate/tokens/utility/pii_text` signatures; confirm none changed after this audit.

## 14. Git state

- **Current branch:** `role-c` (from `git branch --show-current`).
- **Latest commit:** `c729fb2` — "Merge pull request #7 from williamwang2029-cloud/role-c".
- **Pushed?** Yes — `role-c` == `origin/role-c` == `c729fb2`.
- **Merged into main?** Yes — `git merge-base --is-ancestor role-c origin/main` returned exit 0.
- **Uncommitted/untracked before writing this report:** none (`git status --porcelain` empty).
- **Note:** the finalized README/submission_drafts commit (`253384d`, under merge `0a2e33d`) is on `main`/
  `origin/main`, NOT on `role-c`; `role-c`'s README is the older `5fd57bd` version. This report will be
  committed to `role-c` per instructions and NOT pushed to main.
