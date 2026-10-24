"""Pure-Python release-quality warnings (no third-party dependencies).

Given what the mitigation did, decide whether to warn the user that the release is
strongly private but weakly useful, or that the suppression limit could not be met.
Kept dependency-free so it can be unit-tested without Streamlit/pandas installed.
"""


def release_warnings(considered_qis, active_qis, analysis_status, pct_removed, max_removed):
    """Return warnings/errors about a mitigated release.

    Args:
        considered_qis: list of quasi-identifier column names the optimizer considered.
        active_qis: list of column names that survived (were not fully generalized/dropped).
        analysis_status: dict {by_column: "available" | "coarsened" | "lost"}.
        pct_removed: float, fraction of records suppressed (0..1).
        max_removed: float, the user's max-removal limit (0..1).

    Returns:
        {"warnings": [str, ...], "errors": [str, ...], "fields_kept": "comma list"}
    """
    considered_qis = list(considered_qis or [])
    active_qis = list(active_qis or [])
    analysis_status = dict(analysis_status or {})

    warnings = []
    errors = []

    total = len(considered_qis)
    kept = len(active_qis)
    lost = sorted(by for by, status in analysis_status.items() if status == "lost")
    n_by = len(analysis_status)

    too_many_analyses_lost = n_by > 0 and len(lost) > n_by / 2
    too_few_fields_kept = total > 0 and kept < 0.25 * total

    if too_many_analyses_lost or too_few_fields_kept:
        warnings.append(
            f"Strong privacy, low usefulness: only {kept} of {total} fields survived and "
            f"{len(lost)} of {n_by} analyses are lost ({', '.join(lost) or 'none'}). "
            f"Try a smaller k or allowing a little more record removal."
        )

    if pct_removed > max_removed + 1e-9:
        errors.append(
            f"Couldn't meet your limit: {pct_removed:.1%} of records were removed vs. your limit "
            f"of {max_removed:.0%}."
        )

    fields_kept = ", ".join(active_qis) or "none"

    return {"warnings": warnings, "errors": errors, "fields_kept": fields_kept}
