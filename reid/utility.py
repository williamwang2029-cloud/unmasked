import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

def group_means(df, scales, by):
    return df.groupby(by, dropna=False)[list(scales)].mean()

def utility_report(original_df, release_df, scales, by_list, levels=None):
    """Compare group means of `scales` on the original data vs. the rows kept in the release.
    Group labels always come from the ORIGINAL data (joined on row_id), so the shift measures
    the distortion caused by suppression. An analysis is 'lost' if its grouping column was
    dropped from the release, 'coarsened' if it was generalized, else 'available'."""
    kept = original_df[original_df["row_id"].isin(release_df["row_id"])]
    # Only compare scales that actually exist in the uploaded data.
    scales = [s for s in scales if s in original_df.columns]
    rows, status = [], {}
    for by in by_list:
        if by not in release_df.columns:
            status[by] = "lost"
        elif levels and levels.get(by, 0) > 0:
            status[by] = "coarsened"
        else:
            status[by] = "available"
        # Skip grouping columns or scale sets we cannot compute for this upload.
        if by not in original_df.columns or not scales:
            if by not in original_df.columns:
                status[by] = "lost"
            continue
        o = group_means(original_df, scales, by)
        r = group_means(kept, scales, by).reindex(o.index)
        for g in o.index:
            for sc in scales:
                rows.append({"by": by, "group": g, "scale": sc,
                             "orig_mean": o.loc[g, sc], "release_mean": r.loc[g, sc],
                             "abs_shift": abs(o.loc[g, sc] - r.loc[g, sc]) if pd.notna(r.loc[g, sc]) else np.nan})
    # Fixed columns so the frame is never column-less even when rows is empty.
    table = pd.DataFrame(rows, columns=["by", "group", "scale", "orig_mean", "release_mean", "abs_shift"])
    shift = table["abs_shift"].dropna()
    return {"table": table,
            "max_abs_shift": float(shift.max()) if len(shift) else 0.0,
            "mean_abs_shift": float(shift.mean()) if len(shift) else 0.0,
            "pct_rows_kept": float(len(kept) / len(original_df)) if len(original_df) else 1.0,
            "analysis_status": status}

_EXCLUDE_PREFIXES = ("SE",)  # SE items would leak the SE target

def _features(df, target, exclude):
    cols = [c for c in df.columns
            if c != target and c not in exclude and not c.startswith(_EXCLUDE_PREFIXES)]
    X = df[cols].copy()
    for c in X.columns:
        if X[c].dtype == object or str(X[c].dtype) in ("str", "string", "category") or np.issubdtype(X[c].dtype, np.datetime64):
            X[c] = X[c].astype(str)
    return pd.get_dummies(X, dummy_na=True)

def ml_utility(original_df, release_df, transform, target="SE", exclude=(), seed=42):
    """Train the same model on original vs. released data; test both on the same held-out
    ORIGINAL rows (generalized with `transform` for the release model)."""
    exclude = set(exclude) | {"row_id", "ID", "logdate", "duration",
                              "full_name", "email", "student_id", "comment"}
    data = original_df[original_df[target].notna()]
    train_ids, test_ids = train_test_split(data["row_id"], test_size=0.2, random_state=seed)
    o_train = data[data["row_id"].isin(train_ids)]
    o_test = data[data["row_id"].isin(test_ids)]
    r_train = release_df[release_df["row_id"].isin(train_ids) & release_df[target].notna()]
    r_test = transform(o_test)

    def fit_eval(train, test):
        Xtr, Xte = _features(train, target, exclude), _features(test, target, exclude)
        Xte = Xte.reindex(columns=Xtr.columns, fill_value=0)
        m = HistGradientBoostingRegressor(random_state=seed).fit(Xtr, train[target])
        p = m.predict(Xte)
        return mean_absolute_error(test[target], p), r2_score(test[target], p)

    mae_o, r2_o = fit_eval(o_train, o_test)
    mae_r, r2_r = fit_eval(r_train, r_test)
    return {"target": target, "mae_original": float(mae_o), "mae_release": float(mae_r),
            "r2_original": float(r2_o), "r2_release": float(r2_r),
            "n_train_original": int(len(o_train)), "n_train_release": int(len(r_train))}

def fairness_report(df, suppressed_mask, group_col="affiliation"):
    # If the grouping column is absent from the upload, treat everyone as one group
    # instead of raising KeyError.
    groups = df[group_col].values if group_col in df.columns else np.full(len(df), "all")
    t = pd.DataFrame({"group": groups, "sup": suppressed_mask.values})
    out = t.groupby("group", dropna=False).agg(n=("sup", "size"), n_suppressed=("sup", "sum")).reset_index()
    out["pct_suppressed"] = out["n_suppressed"] / out["n"]
    return out.sort_values("pct_suppressed", ascending=False)

def privacy_utility_curve(df, qis, scales, by_list, ks=(2, 3, 5, 10), **greedy_kwargs):
    from reid.mitigate import greedy_generalize
    rows = []
    for k in ks:
        r = greedy_generalize(df, qis, k=k, **greedy_kwargs)
        u = utility_report(df, r["release_df"], scales, by_list, r["levels"])
        rows.append({"k": k, "pct_suppressed": float(r["suppressed_mask"].mean()),
                     "pct_unique_after": r["final_risk"]["pct_unique"],
                     "n_qis_dropped": int(sum(1 for q in qis if q not in r["release_df"].columns)),
                     "analyses_lost": int(sum(v == "lost" for v in u["analysis_status"].values())),
                     "max_abs_shift": u["max_abs_shift"], "mean_abs_shift": u["mean_abs_shift"]})
    return pd.DataFrame(rows)
