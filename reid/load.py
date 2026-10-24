# reid/load.py
"""Role A: load the synthetic NSSE survey file, clean it, and cache it as parquet.

Reading the .xlsx with openpyxl takes ~17 s, so build_clean_cache() writes a
parquet (data/nsse_clean.parquet) once and load_clean() reads that afterwards.

Conventions enforced here (all other modules rely on them):
  - row_id (0..n-1, original row order) is the first column and is never released.
  - "First Time First Year" is renamed to FTFY.
  - MAJsecond is cast to str (NaN stays NaN); numeric -9 stays a valid value.
  - logdate is parsed as datetime.
  - Missing values stay NaN; group-bys elsewhere use dropna=False.
"""
from pathlib import Path

import pandas as pd


def load_raw(cfg):
    """Read sheet 'in' of the raw xlsx and apply the cleaning conventions."""
    df = pd.read_excel(cfg["data"]["raw_xlsx"], sheet_name="in")
    df = df.rename(columns={"First Time First Year": "FTFY"})
    # Cast MAJsecond to str but keep NaN as NaN (it mixes int -9, str, and NaN).
    df["MAJsecond"] = df["MAJsecond"].where(df["MAJsecond"].isna(), df["MAJsecond"].astype(str))
    df["logdate"] = pd.to_datetime(df["logdate"])
    # row_id = original row order, placed first; never part of a released file.
    df = pd.concat([pd.Series(range(len(df)), name="row_id"), df], axis=1)
    return df


def build_clean_cache(cfg):
    """Build the clean DataFrame and write it to data/nsse_clean.parquet."""
    df = load_raw(cfg)
    out = Path(cfg["data"]["clean_parquet"])
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    return df


def load_clean(cfg):
    """Return the cached clean DataFrame, building the parquet if it is missing."""
    p = Path(cfg["data"]["clean_parquet"])
    return pd.read_parquet(p) if p.exists() else build_clean_cache(cfg)


def load_lookup(cfg):
    """Map code columns to names: {field: {int code: meaning}}."""
    lk = pd.read_excel(cfg["data"]["lookup_xlsx"], sheet_name="in")
    return {f: dict(zip(g["value"].astype(int), g["meaning"])) for f, g in lk.groupby("field")}
