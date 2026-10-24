# Tech and rules

- Python 3.11+, pandas, scikit-learn, Presidio + spaCy (en_core_web_sm), Faker, cryptography, Streamlit >= 1.32, Plotly.
- Follow the interface contracts exactly (file names, function names, arguments, return types, column names).
  Each person edits only the files they own. Role C owns: config.yaml, reid/config.py, reid/llm.py,
  reid/classify.py, reid/agent.py, app.py, scripts/smoke_test.py, README.md, requirements.txt, .gitignore, .env.example.
- Conventions: every DataFrame has `row_id` (never exported); `First Time First Year` is renamed `FTFY`;
  `-9` is a real category; group-bys use `dropna=False`; `MAJsecond` is str.
- Safety: synthetic data only. NEVER send row-level student data to an LLM (only column names, types, counts,
  category labels, computed metrics). Never commit data/, keys/, .env, or parquet files.
- `llm.complete()` returns None when disabled or on error; every caller must have a rule-based fallback.
- Tokenized data is pseudonymous, not anonymous. Never claim FERPA compliance.
- Keep code simple and runnable; leave `# TODO` notes when unsure.
