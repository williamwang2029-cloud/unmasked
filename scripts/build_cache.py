"""Build data caches once: clean parquet, planted parquet, PII truth table.

Run from the repo root:
    python scripts/build_cache.py

The clean parquet (Role A) is always built. The planted parquet and PII truth
table need Role B's reid/plant.py; if that module isn't available yet, this
script still builds the clean parquet and prints a note, so Role A isn't
blocked waiting on Role B.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from reid.config import load_config
from reid.load import build_clean_cache

cfg = load_config()
df = build_clean_cache(cfg)
print("clean:", df.shape)

try:
    from reid.plant import plant_identifiers
except ImportError:
    print("plant.py not available yet (Role B); built clean parquet only.")
else:
    planted, truth = plant_identifiers(df, seed=cfg["seed"])
    planted.to_parquet(cfg["data"]["planted_parquet"], index=False)
    truth.to_parquet(cfg["data"]["truth_parquet"], index=False)
    print("planted:", planted.shape, "truth entities:", len(truth))
