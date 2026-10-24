# Repo structure

```
unmasked/
├── .kiro/ (steering + specs, committed)
├── config.yaml, hierarchies.yaml, requirements.txt, .env.example, .gitignore, README.md
├── app.py                    Streamlit UI, 6 tabs (C)
├── reid/
│   ├── config.py, llm.py, classify.py, agent.py     (C)
│   ├── load.py, risk.py, attacks.py                 (A)
│   └── plant.py, pii_text.py, tokens.py, mitigate.py, utility.py   (B)
├── scripts/  build_cache.py (A), run_experiments.py (A+B), smoke_test.py (C)
├── notebooks/results.ipynb
├── results/  precomputed outputs read by the app (small, committed)
├── data/     NOT committed
└── keys/     NOT committed
```

Branches: role-a, role-b, role-c; merge into main at checkpoints. Run `python scripts/smoke_test.py` after every merge.
