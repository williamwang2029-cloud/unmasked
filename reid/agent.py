"""Privacy agent: measure -> plan (LLM) -> act (tools) -> verify -> report (LLM).
The LLM only ever receives metadata and computed metrics, never student rows."""
import json
import pandas as pd
from reid import llm
from reid.attacks import linkage_attack, make_attacker_table
from reid.mitigate import greedy_generalize
from reid.risk import risk_summary
from reid.tokens import tokenize_column
from reid.utility import fairness_report, utility_report

DEFAULT_PERSONAS = {
    "classmate": ["Year", "Class", "MAJfirstcode"],
    "club_roster": ["Year", "Class", "program", "affiliation"],
    "linkedin": ["Year", "Class", "program", "MAJfirstcode", "MAJsecondcode"],
    "survey_insider": ["logdate", "Class", "affiliation"],
}


def _cols(roles, *names):
    return [c for c, r in roles.items() if r["role"] in names]


def run_agent(df, roles, target_k=5, max_suppression=0.05, protect_small_groups=True,
              group_col="affiliation", max_group_suppression=0.10, personas=None,
              scales=("HO", "SF", "QI", "SE"), by_list=("Class", "affiliation", "MAJfirstcol", "Year"),
              scrub_comments="drop", log=None):
    steps = []

    def say(msg):
        steps.append(msg)
        if log:
            log(msg)

    personas = personas or DEFAULT_PERSONAS
    quasi = [c for c in _cols(roles, "quasi_id") if c in df.columns]
    meta = [c for c in _cols(roles, "metadata") if c in df.columns]
    direct = [c for c in _cols(roles, "direct_id") if c in df.columns]
    pii = [c for c in _cols(roles, "planted_pii") if c in df.columns]
    text = [c for c in _cols(roles, "free_text") if c in df.columns]

    before = risk_summary(df, quasi, target_k)
    before_meta = risk_summary(df, quasi + meta, target_k)
    say(f"Measured risk: {before['pct_unique']:.1%} of students are unique on {len(quasi)} quasi-identifiers "
        f"({before_meta['pct_unique']:.1%} including survey metadata).")

    plan = _plan(before, before_meta, quasi, meta, direct + pii, text, target_k, max_suppression, protect_small_groups)
    say("Plan: " + plan)

    work = df.copy()
    for c in direct + [c for c in pii if c in ("student_id",)]:
        work = tokenize_column(work, c)
        say(f"Replaced {c} with keyed tokens; originals are encrypted in a separate vault.")
    drop_pii = [c for c in pii if c not in ("student_id",)]
    if drop_pii:
        work = work.drop(columns=drop_pii)
        say(f"Removed direct identifiers: {', '.join(drop_pii)}.")
    for c in text:
        if scrub_comments == "presidio":
            from reid.pii_text import scrub_text
            work[c] = work[c].astype(str).map(scrub_text)
            say(f"Scrubbed personal details from {c} with Presidio.")
        else:
            work = work.drop(columns=[c])
            say(f"Dropped free-text column {c} (scrub mode off for speed).")

    protect = [group_col] if protect_small_groups and group_col in quasi else []
    mit = greedy_generalize(work, quasi + meta, k=target_k, max_suppression=max_suppression,
                            max_group_suppression=max_group_suppression if protect else None,
                            group_col=group_col, protect=protect)
    for s in mit["steps"][1:]:
        say(f"Generalized {s['column']} to level {s['new_level']}: {s['pct_below_k']:.1%} of records still in groups under {target_k}.")
    release = mit["release_df"]
    after = risk_summary(release, mit["active_qis"], target_k)
    say(f"Suppressed {mit['suppressed_mask'].mean():.1%} of records. Verified: smallest group size is now {after['k_min']}.")

    attacks = {}
    for name, cols in personas.items():
        atk = make_attacker_table(df, cols)
        attacks[name] = {"before": linkage_attack(df, atk, cols),
                         "after": linkage_attack(release, atk, cols, transform=mit["transform"])}
    say("Re-ran simulated linkage attacks: " + ", ".join(
        f"{n} {a['before']['correct_rate']:.0%}→{a['after']['correct_rate']:.0%}" for n, a in attacks.items()))

    util = utility_report(df, release, list(scales), [b for b in by_list if b in df.columns], mit["levels"])
    fair = fairness_report(df, mit["suppressed_mask"], group_col) if group_col in df.columns else pd.DataFrame()
    result = {"plan": plan, "steps": steps, "before": before, "before_with_metadata": before_meta,
              "after": after, "attacks": attacks, "mitigation": mit, "utility": util, "fairness": fair,
              "protect_small_groups": protect_small_groups, "target_k": target_k}
    result["label"] = privacy_label(result)
    result["report_md"] = write_report(result)
    return result


def _plan(before, before_meta, quasi, meta, ids, text, k, max_sup, protect):
    facts = {"pct_unique": round(before["pct_unique"], 3), "pct_unique_with_metadata": round(before_meta["pct_unique"], 3),
             "quasi_identifiers": quasi, "metadata": meta, "identifiers": ids, "free_text": text,
             "target_k": k, "max_suppression": max_sup, "protect_small_groups": protect}
    txt = llm.complete("Facts about a dataset release (metrics only, no rows):\n" + json.dumps(facts) +
                       "\nWrite a 3-sentence mitigation plan for a data owner: what to remove, what to coarsen first and why, "
                       "and the tradeoff to watch. Plain language.", max_tokens=250)
    if txt:
        return txt.strip()
    return (f"Tokenize or remove {len(ids)} identifier columns and handle {len(text)} free-text columns. "
            f"Coarsen survey timing first, then the most detailed quasi-identifiers, until every group has at least {k} students "
            f"with no more than {max_sup:.0%} of records removed. "
            + ("Keep the demographic group column intact so equity analyses stay possible." if protect else
               "Any column may be coarsened, which can erase small demographic groups."))


def privacy_label(r):
    fair = r["fairness"]
    worst = fair.sort_values("pct_suppressed", ascending=False).iloc[0] if len(fair) else None
    atk = r["attacks"].get("everything") or r["attacks"].get("club_roster") or next(iter(r["attacks"].values()))
    lost = [k for k, v in r["utility"]["analysis_status"].items() if v == "lost"]
    risks = ["k-anonymity does not stop every inference about a group's answers (check l-diversity)."]
    if lost:
        risks.append(f"Analyses no longer possible by: {', '.join(lost)}.")
    if worst is not None and worst["pct_suppressed"] > 0:
        risks.append(f"Removed records fall hardest on {worst['group']} ({worst['pct_suppressed']:.1%}).")
    return {"pct_unique_before": r["before"]["pct_unique"], "pct_unique_after": r["after"]["pct_unique"],
            "k_after": r["after"]["k_min"], "pct_suppressed": float(r["mitigation"]["suppressed_mask"].mean()),
            "most_affected_group": None if worst is None else str(worst["group"]),
            "most_affected_pct": None if worst is None else float(worst["pct_suppressed"]),
            "attack_before_pct": atk["before"]["correct_rate"], "attack_after_pct": atk["after"]["correct_rate"],
            "max_mean_shift": r["utility"]["max_abs_shift"], "remaining_risks": risks}


def write_report(r):
    lab = r["label"]
    facts = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in lab.items()}
    facts["generalization_levels"] = r["mitigation"]["levels"]
    facts["analysis_status"] = r["utility"]["analysis_status"]
    txt = llm.complete("Write a one-page privacy report in Markdown for a university data owner, using ONLY these computed "
                       "facts (no rows were shared):\n" + json.dumps(facts, default=str) +
                       "\nSections: Summary, What was risky, What we changed, What it cost, Remaining risks, "
                       "Human review needed. Plain language, short. Do not claim FERPA compliance.", max_tokens=900)
    if txt:
        return txt.strip()
    lines = ["# Privacy report", "",
             f"**Summary:** before release, {lab['pct_unique_before']:.1%} of students were uniquely identifiable. "
             f"After mitigation, every group has at least {lab['k_after']} students and {lab['pct_unique_after']:.1%} are unique.",
             "", "## What we changed", *[f"- {s}" for s in r["steps"][2:]],
             "", "## What it cost",
             f"- {lab['pct_suppressed']:.1%} of records removed; largest shift in a group average: {lab['max_mean_shift']:.2f} points.",
             f"- Simulated linkage attack (attacker knows all core fields): {lab['attack_before_pct']:.0%} of targets re-identified before, {lab['attack_after_pct']:.0%} after.",
             "", "## Remaining risks", *[f"- {x}" for x in lab["remaining_risks"]],
             "", "## Human review needed",
             "- A data steward must confirm column roles and approve this release. This report is not a FERPA compliance certificate."]
    return "\n".join(lines)
