"""Verify Role A against the section-4 reference numbers on the REAL clean data.

Usage: python scripts/check_numbers.py

Loading + risk checks (Tasks A1, A2) only need data/nsse_clean.parquet.
Attack checks (Task A3) and the staircase need the planted parquet from Role B's
plant.py; they are skipped with a note until that cache exists.
"""
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pandas as pd

from reid.config import load_config
from reid import risk, attacks

cfg = load_config()
R = cfg["roles"]
k = cfg["targets"]["k"]
TOL = 0.002  # +/- 0.2 percentage points

passed, failed = [], []


def check(label, got, want, tol=TOL):
    ok = abs(got - want) <= tol
    (passed if ok else failed).append(label)
    flag = "PASS" if ok else "FAIL"
    print(f"[{flag}] {label}: got {got:.4f}, want {want:.4f}")


# ---------- Task A1: loading ----------
t0 = time.time()
df = pd.read_parquet(cfg["data"]["clean_parquet"])
load_s = time.time() - t0
print(f"\nclean parquet shape: {df.shape} (reloaded in {load_s:.2f}s)")
assert df.shape == (20731, 133), f"expected (20731, 133), got {df.shape}"
assert df["ID"].is_unique, "ID not unique"
assert "FTFY" in df.columns, "FTFY missing"
maj2 = df["MAJsecond"]
assert maj2.dropna().map(lambda v: isinstance(v, str)).all(), "MAJsecond has non-str non-NaN values"
assert load_s < 2.0, f"parquet reload took {load_s:.2f}s (want < 2s)"
print("Task A1 loading checks: OK")

# ---------- Task A2: risk metrics ----------
core = R["quasi_ids"]                          # 9 core
core8 = [q for q in core if q != "FTFY"]       # 8 core
ext = core + R["quasi_ids_extended"]           # 14

print("\n-- risk metrics --")
r8 = risk.risk_summary(df, core8, k)
check("8 core % unique", r8["pct_unique"], 0.678)
check("8 core % below k", r8["pct_below_k"], 0.899)

r9 = risk.risk_summary(df, core, k)
check("9 core % unique (adding FTFY unchanged)", r9["pct_unique"], r8["pct_unique"], tol=1e-9)

r14 = risk.risk_summary(df, ext, k)
check("14 fields % unique", r14["pct_unique"], 0.739)

leaks = risk.metadata_leaks(df, k=k).set_index("fields")["pct_unique"]
check("logdate alone % unique", float(leaks["logdate"]), 0.117)
check("duration alone % unique", float(leaks["duration"]), 0.116)
check("logdate+Class+affiliation % unique", float(leaks["logdate + Class + affiliation"]), 0.229)

t0 = time.time()
rc = risk.riskiest_combos(df, core, max_size=3, k=k)
combo_s = time.time() - t0
print(f"riskiest_combos: {len(rc)} rows in {combo_s:.2f}s")
assert len(rc) == 129, f"expected 129 combos, got {len(rc)}"
assert combo_s < 2.0, f"riskiest_combos took {combo_s:.2f}s (want < 2s)"

# ---------- Task A3: attacks (needs planted parquet) ----------
planted = pathlib.Path(cfg["data"]["planted_parquet"])
print("\n-- attacks --")
if not planted.exists():
    print("planted parquet not found; run build_cache.py after Role B's plant.py is merged "
          "to check attack numbers. Using clean data for persona_risk only.")
    src = df
else:
    src = pd.read_parquet(planted)

personas = cfg["personas"]
pr = attacks.persona_risk(src, personas, k).set_index("persona")["pct_unique"]
for name, want in [("classmate", 0.010), ("club_roster", 0.005), ("linkedin", 0.260),
                   ("survey_insider", 0.229), ("everything", 0.678)]:
    check(f"persona {name} % unique", float(pr[name]), want)

atk = attacks.make_attacker_table(src, personas["everything"], n=200, seed=42)
res = attacks.linkage_attack(src, atk, personas["everything"])
print(f"everything persona linkage attack on raw: {res['n_correct']}/200 correct "
      f"({res['correct_rate']:.3f}); reference 137/200 (0.685)")
check("attack everything correct_rate", res["correct_rate"], 0.685, tol=0.01)

# ---------- summary ----------
print(f"\n{'='*50}\n{len(passed)} passed, {len(failed)} failed")
if failed:
    print("FAILED:", ", ".join(failed))
    sys.exit(1)
print("ALL SECTION-4 CHECKS PASSED")
