# Session Handoff — Unmasked (Role C)

Context handoff for another assistant picking up this project. Written by Kiro after a working session
focused on Role C (the privacy agent + Streamlit demo app) plus git/environment troubleshooting.

## Project in one line

"Unmasked: Re-identification Risk Meter" — a BU hackathon project (Hackachusetts 2026). An AI agent labels
column privacy roles from metadata only, measures re-identification risk, tokenizes/generalizes data to reach
k-anonymity, then reports what the fix cost and who it affected. Python + Streamlit. The repo lives inside a
OneDrive folder: `C:\Users\willi\OneDrive\Documents\GitHub\unmasked` (this matters — see Gotchas).

## Role ownership (from .kiro/steering)

- Role A: `reid/risk.py`, `reid/attacks.py`, `reid/load.py`, `scripts/build_cache.py`, `scripts/run_experiments.py`
- Role B: `reid/plant.py`, `reid/pii_text.py`, `reid/tokens.py`, `reid/mitigate.py`, `reid/utility.py`
- Role C (this session): `config.yaml`, `reid/config.py`, `reid/llm.py`, `reid/classify.py`, `reid/agent.py`,
  `app.py`, `scripts/smoke_test.py`, `README.md`, `requirements.txt`, `.gitignore`, `.env.example`

## What was done this session

### 1. Created a spec: `.kiro/specs/role-c-agent-app/`
- `requirements.md`, `design.md`, `tasks.md` describing the Role C agent + app. Grounded in the existing code
  and the steering files (there was no external "brief" available). Documents current behavior more than net-new work.

### 2. Enabled Gemini (Google AI Studio) via the OpenAI-compatible endpoint
The team uses Gemini because it is free. Gemini exposes an OpenAI-compatible Chat Completions API, so the
OpenAI SDK works if you point it at Gemini's base URL.

- `reid/llm.py`: the OpenAI client now reads `OPENAI_BASE_URL` and passes it through:
  ```python
  base_url = os.getenv("OPENAI_BASE_URL")
  client = OpenAI(base_url=base_url) if base_url else OpenAI()
  ```
  (Verified via web search that Gemini's OpenAI-compatible endpoint accepts `max_tokens`, which the code sends.)
- `requirements.txt`: switched the LLM SDK to install `openai` (commented out `anthropic`).
- `.env.example`: cleaned to all-commented placeholders (no real/live values) + a documented Gemini block.
  IMPORTANT: it previously contained active OPENAI_* lines with placeholder-but-live-looking values; that was a
  committed-hygiene problem and is now fixed.
- `README.md`: added an "LLM (optional)" section with the Gemini `.env` setup and a troubleshooting pointer.

### 3. Added a diagnostic script: `scripts/check_llm.py`
Makes ONE live LLM call, prints resolved config with the API key masked, and reports success or the exact
error. Loads `.env` via `load_dotenv()` (note: `reid/config.py` does NOT load .env; the app does, in `app.py`).
Run with: `python scripts/check_llm.py`.

### 4. Guardrails preserved (do not break these)
- The LLM only ever receives column metadata + computed metrics, never student rows.
- `llm.complete()` returns `None` on disabled/error; every caller must have a rule-based fallback.
- Synthetic data only; tokenized data is pseudonymous, not anonymous; never claim FERPA compliance.
- Never commit `data/`, `keys/`, `.env`, or `*.parquet` (enforced by `.gitignore`).

## Git state (as of end of session)

- All five Role C edits are committed as `5fd57bd "Enable Gemini via OpenAI-compatible endpoint; add LLM
  diagnostic"` and pushed to `origin/role-c`.
- That commit is ALREADY MERGED into `main` via PR #4. Verified: `role-c` is an ancestor of `origin/main`,
  and the `OPENAI_BASE_URL` change + `check_llm.py` are present on `origin/main`.
- Role A (PR #5) and Role B are also merged into `main`. `origin/main` tip was `3190a15 "Risk Engine and attacks"`.
- Local `main` is clean and in sync with `origin/main`.
- NOTE: `scripts/check_llm.py` is NOT in the Role C ownership list in steering. It was added pragmatically as a
  dev diagnostic. Harmless, but flag if strict ownership matters.

## Pre-submission leak scan (PASSED)

Scanned the tip of `origin/main` (62 tracked files):
- No tracked `.env`, `data/`, `keys/`, `*.parquet`, `*.pkl`, `*.key`.
- No real API keys, no private-key blocks, no `*_API_KEY=` with real values.
- The only pattern hits were placeholders/docs (`OPENAI_API_KEY=your-ai-studio-key` in README, variable-name
  mentions in docs). All safe.
- CAVEAT: this scanned the current tip only, NOT full git history. If belt-and-suspenders certainty is needed,
  scan history or use GitHub's secret scanning.

## Current blockers to running the app locally (NOT yet resolved)

The app cannot run yet. Verified missing on this machine:
1. Dependencies not installed (no `streamlit`, etc.). Need `pip install -r requirements.txt`.
2. No `.env` file (so Gemini won't connect; app falls back to rule-based).
3. No data files — neither the generated parquets (`data/nsse_planted.parquet`, `pii_truth.parquet`,
   `nsse_clean.parquet`) NOR the source Excel (`data/NSSE-synthetic.xlsx`, `data/lookup-synthetic.xlsx`).
   The user must get these from Role A. `results/` charts exist, but the dataset is required.
4. Only Python 3.14 is installed. spaCy/presidio may lack 3.14 wheels. Recommended: install Python 3.12 and
   build the venv from it. (3.12 and 3.14 coexist fine on Windows via the `py` launcher.)

## How to run the app (once blockers are cleared)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_sm
# create .env (see below)
# put NSSE-synthetic.xlsx + lookup-synthetic.xlsx in data\ (from Role A)
python scripts/build_cache.py        # skip if the 3 parquet files already exist
python scripts/run_experiments.py    # regenerates results/ (~1 min)
python scripts/check_llm.py          # confirm "live call SUCCEEDED"
python scripts/smoke_test.py         # should print "OK in ...s"
streamlit run app.py                 # 6-tab UI; sidebar should show "LLM connected"
```

`.env` contents for Gemini:
```
LLM_PROVIDER=openai
LLM_MODEL=gemini-2.0-flash
OPENAI_API_KEY=<real AI Studio key>
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

Note: `streamlit run app.py` is a long-running server — run it in a terminal the user controls, not via an
automated/background tool. Ctrl+C stops it.

## Gotchas learned the hard way

- OneDrive syncing locks files in `.kiro/specs/...`, which breaks `git checkout` between branches (it hangs on
  a Windows "Deletion of directory failed (y/n)" prompt and leaves a stale `.git/index.lock`). Fix: PAUSE
  OneDrive before any branch switch/merge; if stuck, kill `git.exe` (Task Manager), delete `.git/index.lock`,
  switch branches via GitHub Desktop. Long-term fix: move the repo outside OneDrive.
- The `py` launcher works; a bare `python` may not be on PATH in some shells.

## Remaining submission steps (not started; user-driven)

1. Run the app end-to-end with real data + Gemini `.env`; confirm the LLM connects.
2. Record 2-min video (script in `docs/submission_drafts.md`), upload unlisted to YouTube, verify in incognito.
3. Put the video link in `README.md` (replace `VIDEO_URL`), fill "Built with Kiro" and real numbers from results/.
4. Create a GitHub release tagged `hackachusetts-submission`.
5. Final leak check on github.com (search `sk-`, `ANTHROPIC_API_KEY=`).
6. Submit on the Sundai portal (Civic Action track) and Devpost; add all three team members.
```
