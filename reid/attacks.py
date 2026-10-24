# reid/attacks.py
"""Role A: attacker personas and a simulated linkage attack.

A linkage attack models an adversary who already knows some quasi-identifiers
about target students (from a club roster, LinkedIn, being a classmate, etc.)
and joins that outside knowledge against a released dataset. A target is
"uniquely matched" when exactly one released record matches their known values,
and "correctly re-identified" when that single match is really their record.

These tools run only on synthetic data and exist so a data owner can test how
risky a release is before and after mitigation.
"""
import pandas as pd

from reid.risk import risk_summary


def make_attacker_table(original_df, known_cols, n=200, seed=42):
    """Sample up to n target students and return row_id plus the raw columns the
    attacker is assumed to know. Caps the sample at len(original_df) so small
    uploads (fewer than n rows) do not crash."""
    cols = [c for c in known_cols if c in original_df.columns]
    sample_n = min(n, len(original_df))
    return original_df.sample(n=sample_n, random_state=seed)[["row_id"] + cols].reset_index(drop=True)


def persona_risk(df, personas, k=5):
    """Uniqueness for each attacker persona (each persona = a set of known fields)."""
    rows = []
    for name, fields in personas.items():
        m = risk_summary(df, fields, k)
        rows.append({"persona": name, "fields": " + ".join(fields),
                     "pct_unique": m["pct_unique"], "pct_below_k": m["pct_below_k"]})
    return pd.DataFrame(rows)


def linkage_attack(release_df, attacker_df, known_cols, transform=None):
    """Join the attacker's raw knowledge against a (possibly generalized) release.

    If the release was generalized, pass `transform` (the callable from the
    mitigation step) so the attacker's raw values are coarsened the same way
    before matching. NaN is treated as a matchable value (NaN matches NaN).
    """
    atk = attacker_df.copy()
    if transform is not None:
        atk = transform(atk)
    cols = [c for c in known_cols if c in release_df.columns and c in atk.columns]
    n = len(attacker_df)
    if not cols:
        # Nothing the attacker knows survived in the release -> no one can be matched.
        return {"n_targets": n, "cols_used": [], "n_unique_match": 0, "n_correct": 0,
                "unique_match_rate": 0.0, "correct_rate": 0.0}

    def keyify(d):
        # Normalize to strings so NaN/NaT/None all collapse to one matchable token.
        return (d[cols].astype(str).fillna("__NA__")
                .replace({"nan": "__NA__", "NaT": "__NA__", "None": "__NA__"}))

    rel = keyify(release_df).assign(_rel_row=release_df["row_id"].values)
    a = keyify(atk).assign(_atk_row=atk["row_id"].values)
    counts = rel.groupby(cols).size().rename("_n").reset_index()
    a = a.merge(counts, on=cols, how="left").fillna({"_n": 0})
    uniq = a[a["_n"] == 1].merge(rel, on=cols, how="left")
    n_unique = int((a["_n"] == 1).sum())
    n_correct = int((uniq["_rel_row"] == uniq["_atk_row"]).sum())
    return {"n_targets": n, "cols_used": cols, "n_unique_match": n_unique, "n_correct": n_correct,
            "unique_match_rate": n_unique / n, "correct_rate": n_correct / n}
