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
bu_path = pathlib.Path(cfg["data"]["planted_parquet"])
if bu_path.exists():
    print(f"Using dataset: BU synthetic NSSE ({bu_path})")
    df = pd.read_parquet(bu_path).sample(3000, random_state=1)
else:
    demo_path = pathlib.Path("examples/demo_planted.csv")
    print(f"Using dataset: generated demo data ({demo_path}) — BU parquet not found")
    df = pd.read_csv(demo_path, dtype={"MAJsecond": "string"}, parse_dates=["logdate"])
    if "row_id" not in df.columns:
        df.insert(0, "row_id", range(len(df)))
    df = df.sample(min(3000, len(df)), random_state=1)
roles = classify.classify_columns(classify.profile_columns(df), classify.roles_from_config(cfg))
t = time.time()
r = run_agent(df, roles, personas=cfg["personas"], scales=cfg["utility_analyses"]["scales"],
              by_list=cfg["utility_analyses"]["by"])
assert r["after"]["k_min"] >= 5, "k target not met"
assert r["label"]["pct_unique_after"] == 0.0
rel = r["mitigation"]["release_df"]
assert not {"full_name", "email", "comment"} & set(rel.columns), "PII column leaked into release"
print(f"OK in {time.time() - t:.1f}s:", {k: v for k, v in r["label"].items() if k != "remaining_risks"})
