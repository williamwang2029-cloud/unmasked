"""Run all experiments and write small result files to results/ for the app and the pitch.

Usage:
    python scripts/run_experiments.py [--skip-presidio] [--llm-sample 200]

Role A owns the first section (baseline risk, combos, leaks, personas,
risk-by-group, l-diversity, staircase). Role B owns the mitigation / attack /
fairness / utility / detection sections below.
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pandas as pd

from reid.config import load_config
from reid import risk, attacks

ap = argparse.ArgumentParser()
ap.add_argument("--skip-presidio", action="store_true")
ap.add_argument("--presidio-sample", type=int, default=1500)
ap.add_argument("--llm-sample", type=int, default=200)
args = ap.parse_args()

cfg = load_config()
out = pathlib.Path("results")
out.mkdir(exist_ok=True)
df = pd.read_parquet(cfg["data"]["planted_parquet"])
truth = pd.read_parquet(cfg["data"]["truth_parquet"])
R = cfg["roles"]
k = cfg["targets"]["k"]
core = R["quasi_ids"]
core8 = [q for q in core if q != "FTFY"]
ext = core + R["quasi_ids_extended"]

# ---------- Role A ----------
json.dump({"core9": risk.risk_summary(df, core, k),
           "core8": risk.risk_summary(df, core8, k),
           "extended14": risk.risk_summary(df, ext, k),
           "with_metadata": risk.risk_summary(df, ext + R["metadata"], k)},
          open(out / "baseline_risk.json", "w"), indent=2)
risk.riskiest_combos(df, core, 3, k).to_csv(out / "combos.csv", index=False)
risk.metadata_leaks(df, k=k).to_csv(out / "leaks.csv", index=False)
attacks.persona_risk(df, cfg["personas"], k).to_csv(out / "personas.csv", index=False)
risk.risk_by_group(df, core, R["group_col"], k).to_csv(out / "risk_by_group.csv", index=False)
risk.l_diversity_report(df, ["Year", "Class", "affiliation", "MAJfirstcol"],
                        R["sensitive_scales"]).to_csv(out / "l_diversity.csv", index=False)

# uniqueness staircase for the opening chart
stairs = [["Year", "Class"],
          ["Year", "Class", "affiliation"],
          ["Year", "Class", "affiliation", "MAJfirstcode"],
          ["Year", "Class", "affiliation", "MAJfirstcode", "program"],
          ["Year", "Class", "affiliation", "MAJfirstcode", "program", "MAJsecondcode"],
          core8, ext]
pd.DataFrame([{"fields": " + ".join(s), "n_fields": len(s), **risk.risk_summary(df, s, k)}
             for s in stairs]).to_csv(out / "staircase.csv", index=False)

# ---------- Role B: mitigation in both modes ----------
try:
    from reid import mitigate, utility
except ImportError:
    print("Role A results written. Role B modules (mitigate/utility) not available yet; "
          "skipping mitigation/attack/fairness/utility/detection sections.")
    sys.exit(0)

qis = ext + R["metadata"]
work = df.drop(columns=R["planted"])
modes = {"protect_on": dict(protect=[R["group_col"]],
                            max_group_suppression=cfg["targets"]["max_group_suppression"]),
         "protect_off": {}}
attack_rows, fair_rows, util_rows = {}, [], {}
for mode, kw in modes.items():
    m = mitigate.greedy_generalize(work, qis, k=k, max_suppression=cfg["targets"]["max_suppression"],
                                   group_col=R["group_col"], **kw)
    f = utility.fairness_report(work, m["suppressed_mask"], R["group_col"])
    f["setting"] = mode
    fair_rows.append(f)
    u = utility.utility_report(work, m["release_df"], cfg["utility_analyses"]["scales"],
                               cfg["utility_analyses"]["by"], m["levels"])
    util_rows[mode] = {"levels": m["levels"], "pct_suppressed": float(m["suppressed_mask"].mean()),
                       "final_risk": m["final_risk"], "max_abs_shift": u["max_abs_shift"],
                       "mean_abs_shift": u["mean_abs_shift"], "analysis_status": u["analysis_status"],
                       "ml": utility.ml_utility(work, m["release_df"], m["transform"], target="SE")}
    attack_rows[mode] = {}
    for p, cols in cfg["personas"].items():
        atk = attacks.make_attacker_table(work, cols, cfg["attack"]["n_targets"], cfg["attack"]["seed"])
        attack_rows[mode][p] = {"before": attacks.linkage_attack(work, atk, cols),
                                "after": attacks.linkage_attack(m["release_df"], atk, cols, transform=m["transform"])}
json.dump(attack_rows, open(out / "attack.json", "w"), indent=2)
pd.concat(fair_rows).to_csv(out / "fairness.csv", index=False)
json.dump(util_rows, open(out / "mitigation_summary.json", "w"), indent=2, default=str)
utility.privacy_utility_curve(work, qis, cfg["utility_analyses"]["scales"], cfg["utility_analyses"]["by"],
                              ks=(2, 3, 5, 10), max_suppression=cfg["targets"]["max_suppression"]).to_csv(out / "curve.csv", index=False)

# ---------- Role B: PII detection ----------
if not args.skip_presidio:
    from reid import pii_text, llm
    sample = df.sample(n=min(args.presidio_sample, len(df)), random_state=cfg["seed"])
    t = truth[truth.row_id.isin(sample.row_id)]
    pres = {r.row_id: pii_text.presidio_detect(r.comment) for r in sample.itertuples()}
    rows = [pii_text.evaluate_detection(t, pres).assign(method="presidio")]
    if llm.llm_enabled():
        small = sample.head(args.llm_sample)          # synthetic comments only
        t2 = truth[truth.row_id.isin(small.row_id)]
        llmp = {r.row_id: pii_text.llm_detect(r.comment) for r in small.itertuples()}
        both = {rid: pii_text.combine(pres[rid], llmp[rid]) for rid in llmp}
        rows += [pii_text.evaluate_detection(t2, {rid: pres[rid] for rid in llmp}).assign(method="presidio_same_sample"),
                 pii_text.evaluate_detection(t2, llmp).assign(method="llm"),
                 pii_text.evaluate_detection(t2, both).assign(method="combined")]
    pd.concat(rows).to_csv(out / "detection.csv", index=False)
print("done; results written to results/")
