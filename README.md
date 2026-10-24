# Unmasked: Re-identification Risk Meter

> No names, no IDs, and still 68% of students can be singled out from eight ordinary survey fields
> (74% with prior-attendance flags, nearly 100% with survey timing). Unmasked finds that risk, fixes it,
> and shows what the fix costs, and who pays for it.

Built at BU Spark! DS+X × Hackachusetts 2026 for BU IS&T's Data Scrubbing / Tokenization challenge.

## Demo
[2-minute video](VIDEO_URL) · screenshots in results/charts/

## The problem
Removing names does not make data anonymous. Combinations of ordinary fields (year, class, program, major,
demographic group) single students out. FERPA asks whether a reasonable person in the school community could
identify a student with reasonable certainty.

## What it does
1. An AI agent labels each column's privacy role using metadata only.
2. Measures k-anonymity, uniqueness, riskiest field combinations, metadata leaks, attacker personas,
   and a simulated linkage attack.
3. Tokenizes IDs (keyed HMAC tokens + encrypted vault with a separate key), removes direct identifiers,
   scrubs free text with Presidio.
4. Optimizes generalization and suppression to reach k ≥ 5 with ≤ 5% of records removed, optionally
   protecting small demographic groups.
5. Verifies with the attack, measures usefulness (group means, ML utility test) and fairness, and writes a
   plain-English report and a privacy nutrition label.

## Results (synthetic NSSE data, 20,731 students)
| | Before | After (protect small groups) |
|---|---|---|
| Uniquely identifiable (14 fields) | 73.9% | 0% |
| Linkage attack success (attacker knows all core fields) | 68.5% | 0% |
| Records removed | – | 2.5% |
| ML utility, predicting engagement (R²) | 0.42 | 0.37 |

**Key finding:** without the safeguard, the optimizer deletes the demographic column entirely, so equity
analysis becomes impossible. With it, small groups lose up to 8× more records than the largest group
(6.9% vs. 0.9%). Privacy protection is not free, and it is not evenly paid.

PII detection on planted ground truth: see results/detection.csv (precision/recall per entity type).

## Data
Synthetic NSSE-style survey data provided by BU IS&T (not included in this repo). Names, emails, IDs, and
comments were planted with Faker for testing and are entirely fake.

## Responsible AI and ethics
- The LLM never sees student rows, only column metadata and computed metrics.
- Keys and vaults are stored separately and never committed; tokenized data is pseudonymous, not anonymous.
- We measure who loses data (fairness) and let data owners protect small groups.
- Limitations: k-anonymity does not prevent every inference about a group's answers (see l-diversity),
  attackers may know more than our personas, and combining releases can re-identify people. A human data
  steward must approve every release; this tool is not a FERPA compliance certificate.

## Built with Kiro
We used Kiro's spec-driven workflow for each module (specs in `.kiro/specs/`, steering in `.kiro/steering/`):
TODO: describe briefly what Kiro planned and generated (add screenshots for the video).

## Run it
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && python -m spacy download en_core_web_sm
cp .env.example .env   # optional LLM settings
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
A · B · C

## Credits
BU IS&T (challenge and synthetic data), NSSE codebooks, Microsoft Presidio, spaCy, Faker, scikit-learn, Streamlit.
