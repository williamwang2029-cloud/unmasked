# Unmasked: Re-identification Risk Meter

> No names, no IDs, and still 68% of students can be singled out from eight ordinary survey fields
> (74% once prior-attendance flags are added, and virtually 100% once survey timing is included).
> Unmasked finds that risk, fixes it, and shows what the fix costs, and who pays for it.

Built at BU Spark! DS+X × Hackachusetts 2026 for BU IS&T's Data Scrubbing / Tokenization challenge.

## Demo
[2-minute video](VIDEO_URL) · screenshots in `results/charts/`

## The problem
Removing names does not make data anonymous. Combinations of ordinary fields (year, class, program, major,
demographic group) single students out. FERPA asks whether a reasonable person in the school community could
identify a student with reasonable certainty, and ordinary survey fields clear that bar easily.

## What it does
1. An AI agent labels each column's privacy role using metadata only (names, types, counts, and computed
   metrics, never student rows).
2. Measures k-anonymity, uniqueness, the riskiest field combinations, metadata leaks, attacker personas,
   and a simulated linkage attack.
3. Tokenizes IDs (keyed HMAC tokens plus an encrypted vault with a separate key), removes direct identifiers,
   and scrubs free text with Microsoft Presidio.
4. Optimizes generalization and suppression to reach k ≥ 5 with ≤ 5% of records removed, optionally
   protecting small demographic groups.
5. Verifies with the attack, measures usefulness (group means and an ML utility test) and fairness, and writes
   a plain-English report plus a privacy nutrition label.

## Results (synthetic NSSE data, 20,731 students)

| | Before | After (protect small groups) |
|---|---|---|
| Uniquely identifiable (8 ordinary fields) | 67.8% | 0% |
| Uniquely identifiable (14 fields) | 73.9% | 0% |
| Uniquely identifiable (including survey timing) | ~100% | 0% |
| Linkage attack success (attacker knows all 9 core fields, 200 targets) | 68.5% | 0% |
| Records removed | – | 2.5% |
| ML utility, predicting engagement score (R²) | 0.42 | 0.37 |

Smallest group size after mitigation is k = 5 (every combination of quasi-identifiers is shared by at least
five students). Without protecting small groups, the optimizer instead removes 3.5% of records and coarsens the
demographic column away entirely.

**Key finding (fairness):** privacy protection is not free, and it is not evenly paid. Without the small-group
safeguard, the optimizer generalizes the demographic (affiliation) column until equity analysis by that column
is impossible. With the safeguard on, the demographic column is preserved, but the smallest groups absorb the
cost: the most-affected group loses about 6.9% of its records versus about 0.85% for the largest group, roughly
an 8× gap. The tool measures and surfaces this rather than hiding it.

## PII detection on planted ground truth
Held-out planted sample (`results/detection.csv`, Presidio + spaCy `en_core_web_sm`):

| Entity | Precision | Recall |
|---|---|---|
| Email | 1.00 | 1.00 |
| Phone | 1.00 | 1.00 |
| BU ID | 1.00 | 1.00 |
| Person name | 1.00 | 0.91 |

Out-of-sample stress test (`results/detection_stress_test.csv`, 20 hand-written sentences): on the 10
name sentences, person-name detection scores about 0.90 precision and 0.90 recall. The small spaCy model
misses some second names in a sentence (for example, a friend's full name introduced as a second subject) and
occasionally flags a campus place as a person, which is why names trail the near-perfect scores for structured
PII like emails and IDs.

## Data
Synthetic NSSE-style survey data provided by BU IS&T (not included in this repo). Names, emails, IDs, and
comments were planted with Faker for testing and are entirely fake. No real student data is used anywhere.

## Responsible AI and ethics
- The LLM (Gemini via an OpenAI-compatible endpoint) only ever sees column metadata and computed metrics,
  never student rows. The whole pipeline runs without an LLM too (rule-based fallback), so the data science
  stands on its own.
- Keys and token vaults are stored separately and never committed. Tokenized data is pseudonymous, not
  anonymous: whoever holds the vault key can re-link it.
- We measure who loses data (fairness) and let data owners protect small demographic groups.
- A human data steward must review column roles and approve every release. This tool is **not** a FERPA
  compliance certificate.
- Limitations: k-anonymity does not prevent every inference about a group's answers (see l-diversity),
  real attackers may know more than our personas, and combining this release with others can re-identify
  people.

## Built with Kiro
We used Kiro's spec-driven workflow, splitting the project into three specs so three people could build in
parallel against shared interface contracts. Specs live in `.kiro/specs/`, team-wide rules in `.kiro/steering/`.

- **`.kiro/specs/role-a-risk-engine`** (Role A): data loading and the risk engine, k-anonymity / uniqueness /
  riskiest-combination search, attacker personas, and the simulated linkage attack (`reid/load.py`,
  `reid/risk.py`, `reid/attacks.py`).
- **`.kiro/specs/role-b-mitigation`** (Role B): PII planting, Presidio text scrubbing, HMAC tokenization with an
  encrypted vault, the generalization/suppression optimizer, and the utility and fairness measures
  (`reid/plant.py`, `reid/pii_text.py`, `reid/tokens.py`, `reid/mitigate.py`, `reid/utility.py`).
- **`.kiro/specs/role-c-agent-app`** (Role C): the AI agent that orchestrates measure → plan → act → verify →
  report, the metadata-only LLM wrapper and column classifier, and the six-tab Streamlit app
  (`reid/agent.py`, `reid/llm.py`, `reid/classify.py`, `app.py`).

Steering files (`product.md`, `structure.md`, `tech.md`) kept everyone to the same file ownership, naming
conventions, and safety rules (for example: never send rows to the LLM; never commit data or keys). Kiro drafted
each spec's requirements, design, and task list, then generated and iterated on the implementation against them.

## Run it
```bash
# use Python 3.11 or 3.12 (some dependencies lag on 3.14)
python -m venv .venv && source .venv/bin/activate      # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt && python -m spacy download en_core_web_sm
cp .env.example .env   # optional LLM settings (see below)
# place NSSE-synthetic.xlsx and lookup-synthetic.xlsx in data/
python scripts/build_cache.py && python scripts/run_experiments.py
python scripts/smoke_test.py
streamlit run app.py
```

### LLM (optional)

The app runs fully without an LLM (rule-based fallback). With a key, the agent writes nicer plans, reports,
and role explanations. The LLM only ever sees column metadata and computed metrics, never student rows.

Set these in `.env` (copied from `.env.example`, never committed). You can use Anthropic, OpenAI, or any
OpenAI-compatible endpoint. Google's Gemini is free via AI Studio and works through the OpenAI-compatible
endpoint:

```env
LLM_PROVIDER=openai
LLM_MODEL=gemini-2.0-flash   # any model name from Google AI Studio
OPENAI_API_KEY=your-ai-studio-key
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

Omit `OPENAI_BASE_URL` to use OpenAI directly, or set `LLM_PROVIDER=anthropic` with `ANTHROPIC_API_KEY`.
Confirm it connected: the app sidebar shows "🟢 LLM connected" (not "⚪ rule-based fallback"). On any error
the wrapper silently falls back to rule-based mode, so the sidebar is the quickest way to tell it worked.

Troubleshooting: run `python scripts/check_llm.py` to make one live test call. It prints the resolved config
(API key masked), reports whether the LLM is enabled, and either shows the model's reply or the exact error, so
you can tell a key/model problem apart from a connection problem.

## Team
Role A · Role B · Role C

## Credits
BU IS&T (challenge and synthetic data), NSSE codebooks, Microsoft Presidio, spaCy, Faker, scikit-learn,
Streamlit, Plotly, and Kiro.
