# reid/risk.py
"""Role A: the re-identification risk engine.

Core idea: records that share the same quasi-identifier (QI) values form an
*equivalence class*. A class of size 1 is a uniquely identifiable student.
k-anonymity means the smallest class has at least k records.

All group-bys use dropna=False so students with missing values form their own
group instead of vanishing (otherwise risk is understated). Every returned
number is a plain Python int/float so results are JSON-serializable. Functions
are pure (no prints, no globals) so the app and the agent can call them freely.
"""
from itertools import combinations

import pandas as pd


def class_sizes(df, qis):
    """Size of the equivalence class each row belongs to, aligned to df.index."""
    qis = list(qis)
    return df.groupby(qis, dropna=False)[qis[0]].transform("size")


def risk_summary(df, qis, k=5):
    """Risk metrics for a set of QIs. Ignores QI names not present in df.columns
    (so it works on releases where columns were dropped)."""
    qis = [q for q in qis if q in df.columns]
    if not qis or len(df) == 0:
        return {"n": len(df), "n_classes": 1, "k_min": len(df), "pct_unique": 0.0,
                "pct_below_k": 0.0, "avg_risk": 1 / max(len(df), 1), "max_risk": 1 / max(len(df), 1)}
    s = class_sizes(df, qis)
    return {"n": int(len(df)),
            "n_classes": int(df.groupby(qis, dropna=False).ngroups),
            "k_min": int(s.min()),
            "pct_unique": float((s == 1).mean()),       # share in classes of size 1
            "pct_below_k": float((s < k).mean()),       # share in classes smaller than k
            "avg_risk": float((1 / s).mean()),          # mean of 1/class size
            "max_risk": float(1 / s.min())}             # prosecutor risk = 1/min class size


def riskiest_combos(df, qis, max_size=3, k=5):
    """Every QI combination up to max_size, ranked by uniqueness."""
    rows = []
    for r in range(1, max_size + 1):
        for c in combinations(qis, r):
            m = risk_summary(df, list(c), k)
            rows.append({"combo": " + ".join(c), "size": r,
                         "pct_unique": m["pct_unique"], "pct_below_k": m["pct_below_k"]})
    return pd.DataFrame(rows).sort_values(["pct_unique", "pct_below_k"], ascending=False)


def risk_by_group(df, qis, group_col, k=5):
    """Uniqueness and below-k rates broken down by a demographic group column.
    Reveals that the smallest groups carry the highest re-identification risk."""
    s = class_sizes(df, qis)
    tmp = pd.DataFrame({"group": df[group_col], "unique": s == 1, "below": s < k})
    out = (tmp.groupby("group", dropna=False)
              .agg(n=("unique", "size"), pct_unique=("unique", "mean"), pct_below_k=("below", "mean"))
              .reset_index())
    return out.sort_values("pct_below_k", ascending=False)


def metadata_leaks(df, cols=("logdate", "duration"), combos=(("logdate", "Class", "affiliation"),), k=5):
    """How much survey paradata (completion date, duration) leaks on its own."""
    rows = []
    for fields in [[c] for c in cols] + [list(c) for c in combos]:
        m = risk_summary(df, fields, k)
        rows.append({"fields": " + ".join(fields), "pct_unique": m["pct_unique"], "pct_below_k": m["pct_below_k"]})
    return pd.DataFrame(rows)


def l_diversity_report(df, qis, sensitive_cols):
    """l-diversity: within each equivalence class, how many distinct values of a
    sensitive attribute appear. Uses only classes with >= 2 records and ignores
    classes where nobody answered a given sensitive column."""
    qis = [q for q in qis if q in df.columns]
    sizes = class_sizes(df, qis)
    sub = df[sizes >= 2]
    rows = []
    for col in sensitive_cols:
        nun = sub.groupby(qis, dropna=False)[col].nunique()
        nun = nun[nun > 0]  # ignore classes where nobody answered this item
        rows.append({"sensitive": col,
                     "l_min": int(nun.min()) if len(nun) else None,
                     "pct_classes_l1": float((nun <= 1).mean()) if len(nun) else None})
    return pd.DataFrame(rows)
