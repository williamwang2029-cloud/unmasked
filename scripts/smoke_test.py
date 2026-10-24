"""Fast integration check: runs the whole agent on a 3,000-row sample.
Usage: python scripts/smoke_test.py"""
import sys
import pathlib
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pandas as pd
from reid.config import load_config
from reid import classify
from reid.agent import run_agent

cfg = load_config()
df = pd.read_parquet(cfg["data"]["planted_parquet"]).sample(3000, random_state=1)
roles = classify.classify_columns(classify.profile_columns(df), classify.roles_from_config(cfg))
t = time.time()
r = run_agent(df, roles, personas=cfg["personas"], scales=cfg["utility_analyses"]["scales"],
              by_list=cfg["utility_analyses"]["by"])
assert r["after"]["k_min"] >= 5, "k target not met"
assert r["label"]["pct_unique_after"] == 0.0
rel = r["mitigation"]["release_df"]
assert not {"full_name", "email", "comment"} & set(rel.columns), "PII column leaked into release"
print(f"OK in {time.time() - t:.1f}s:", {k: v for k, v in r["label"].items() if k != "remaining_risks"})
