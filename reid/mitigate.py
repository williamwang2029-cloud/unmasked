import numpy as np
import pandas as pd
import yaml
from reid.risk import class_sizes, risk_summary

_H = None

def load_hierarchies(path="hierarchies.yaml"):
    global _H
    with open(path) as f:
        _H = yaml.safe_load(f)
    return _H

def _h():
    return _H if _H is not None else load_hierarchies()

# QIs present in an uploaded file but absent from hierarchies.yaml get this default
# two-level ladder: keep as-is (identity) or drop entirely. This lets the optimizer
# generalize/drop unmapped identifying columns (e.g. "age", "zip") instead of silently
# leaving them at full detail. Columns that DO have a hierarchy are unaffected.
DEFAULT_LADDER = [{"type": "identity"}, {"type": "drop"}]

def _col_hier(col):
    """Hierarchy ladder for a column: its configured entry, or the default ladder."""
    return _h().get(col, DEFAULT_LADDER)

def max_level(col):
    return len(_col_hier(col)) - 1

def _apply_rule(df, col, rule):
    t = rule["type"]
    s = df[col]
    if t == "identity":
        return s
    if t == "map":
        m = rule["map"]
        return s.map(lambda v: m.get(v, m.get(str(v), v)) if pd.notna(v) else v)
    if t == "map_other":
        keep = set(rule["keep"])
        return s.where(s.isna() | s.isin(keep), rule["other"])
    if t == "from_column":
        return df[rule["source"]]
    if t == "has_value":
        none = set(rule["none_values"])
        return s.map(lambda v: v if pd.isna(v) else (rule["label_no"] if v in none else rule["label_yes"]))
    if t == "month":
        return pd.to_datetime(s).dt.to_period("M").astype(str)
    if t == "year":
        return pd.to_datetime(s).dt.year
    if t == "bins":
        return pd.cut(s, bins=rule["edges"], labels=rule["labels"], include_lowest=True).astype(str).replace("nan", np.nan)
    raise ValueError(f"unknown rule type {t}")

def apply_levels(df, levels):
    """Return a generalized copy. Columns at their 'drop' level are removed,
    and derived columns are dropped in lockstep with their source."""
    h = _h()
    out = df.copy()
    to_drop = []
    for col, lvl in levels.items():
        if col not in out.columns:
            continue
        rule = _col_hier(col)[lvl]
        if rule["type"] == "drop":
            to_drop.append(col)
        else:
            out[col] = _apply_rule(out, col, rule)
        for min_lvl, derived in h.get("derived", {}).get(col, []):
            if lvl >= min_lvl and derived in out.columns:
                to_drop.append(derived)
    return out.drop(columns=sorted(set(to_drop)))

def make_transform(levels):
    return lambda d: apply_levels(d, levels)

def suppress(df, qis, k):
    qis = [q for q in qis if q in df.columns]
    if not qis:
        mask = pd.Series(False, index=df.index)
        return df.copy(), mask
    s = class_sizes(df, qis)
    mask = s < k
    return df.loc[~mask].copy(), mask

def _group_supp(df, qis, k, group_col, group_series):
    qis = [q for q in qis if q in df.columns]
    if not qis:
        return 0.0
    below = class_sizes(df, qis) < k
    return float(below.groupby(group_series.values).mean().max())

def greedy_generalize(df, qis, k=5, max_suppression=0.05, max_group_suppression=None,
                      group_col="affiliation", protect=(), must_keep=()):
    qis = [q for q in qis if q in df.columns]  # unmapped QIs get DEFAULT_LADDER via _col_hier
    levels = {q: 0 for q in qis}
    groups = df[group_col] if group_col in df.columns else pd.Series("all", index=df.index)
    steps = []

    def evaluate(lv):
        cur = apply_levels(df, lv)
        active = [q for q in qis if q in cur.columns]
        below = float((class_sizes(cur, active) < k).mean()) if active else 0.0
        gmax = _group_supp(cur, active, k, group_col, groups) if max_group_suppression is not None else 0.0
        return cur, below, gmax

    cur, below, gmax = evaluate(levels)
    steps.append({"step": 0, "column": None, "new_level": None, "pct_below_k": below, "max_group_below_k": gmax})

    def ok(b, g):
        return b <= max_suppression and (max_group_suppression is None or g <= max_group_suppression)

    step = 0
    while not ok(below, gmax):
        best = None
        for q in qis:
            if q in protect:
                continue
            limit = 1 if q in must_keep else max_level(q)
            if levels[q] >= limit:
                continue
            trial = dict(levels, **{q: levels[q] + 1})
            _, b, g = evaluate(trial)
            # objective: reduce overall below-k and the worst group's below-k; dropping costs more
            is_drop = (levels[q] + 1) == max_level(q)
            cost = 2.0 if is_drop else 1.0
            gain = (below - b) + (0.5 * (gmax - g) if max_group_suppression is not None else 0.0)
            score = gain / cost
            if best is None or score > best[0]:
                best = (score, q, trial, b, g)
        if best is None:
            break
        _, q, levels, below, gmax = best
        step += 1
        steps.append({"step": step, "column": q, "new_level": levels[q],
                      "pct_below_k": below, "max_group_below_k": gmax})

    cur = apply_levels(df, levels)
    active = [q for q in qis if q in cur.columns]
    release, mask = suppress(cur, active, k)
    return {"levels": levels, "release_df": release, "suppressed_mask": mask,
            "steps": steps, "final_risk": risk_summary(release, active, k),
            "active_qis": active, "transform": make_transform(levels)}
