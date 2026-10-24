"""Generate a fully synthetic demo dataset so the app can run without BU's
access-restricted files.

IMPORTANT: this script fabricates every value with numpy/Faker. It NEVER reads,
samples, or derives anything from the BU data under data/. The column names and
conventions match config.yaml and the pipeline (row_id, FTFY, -9 sentinels, the
10 scales, derived major columns, etc.) so the demo flows through risk ->
mitigation -> attack -> utility exactly like the real file.

Usage: python scripts/make_demo_data.py
Output: examples/demo_planted.csv
"""
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from reid.plant import plant_identifiers

SEED = 42
N = 5000
rng = np.random.default_rng(SEED)

# ---- helpers ----------------------------------------------------------------
def choice(options, p=None, size=N):
    return rng.choice(options, size=size, p=p)

# ---- Year: uneven counts over 6 cohorts ------------------------------------
years = [2014, 2016, 2018, 2020, 2022, 2024]
year = choice(years, p=[0.08, 0.10, 0.14, 0.20, 0.24, 0.24])

# ---- Class: FY / SR / Other ~ 45/45/10 -------------------------------------
klass = choice(["FY", "SR", "Other"], p=[0.45, 0.45, 0.10])

# ---- program: P1..P8 with a few small ones ---------------------------------
program = choice(["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"],
                 p=[0.30, 0.26, 0.18, 0.12, 0.07, 0.04, 0.02, 0.01])

# ---- FTFY: Y for most FY rows, else N --------------------------------------
ftfy = np.where((klass == "FY") & (rng.random(N) < 0.9), "Y", "N")

# ---- affiliation: 7 lemurs, one large + several small ----------------------
lemurs = ["Ring-tailed lemur", "Indri", "Aye-aye", "Golden bamboo lemur",
          "Crowned lemur", "Diademed sifaka", "Gray mouse lemur"]
aff = choice(lemurs, p=[0.50, 0.18, 0.10, 0.07, 0.06, 0.05, 0.04])

# ---- Major fields ----------------------------------------------------------
# 91 first-major codes 1001..1091; each code maps to a "college" group 21..32.
maj_codes = np.arange(1001, 1011)                 # 1001..1010 (small, concentrated pool -> realistic risk)
code_to_col = {c: 21 + (i * 12 // len(maj_codes)) for i, c in enumerate(maj_codes)}  # -> 21..32
FIELD_NAMES = ["Lantern Studies", "Kite Studies", "Wayfinding", "Tide Mechanics",
               "Ember Design", "Cartography", "Beacon Theory", "Harbor Systems",
               "Glasswork", "Foldcraft", "Driftwood Ecology", "Signal Arts"]

# Zipf-like weights so a handful of majors are common and the tail is rare.
_w = 1.0 / np.arange(1, len(maj_codes) + 1) ** 1.8
_w = _w / _w.sum()
rng.shuffle(_w)
maj1_code = choice(maj_codes, p=_w)                # uneven: few popular majors, long rare tail
maj1_col = np.array([code_to_col[c] for c in maj1_code])
maj1_text = np.array([f"{FIELD_NAMES[(c - 1001) % len(FIELD_NAMES)]}: Track {(c % 5) + 1}"
                      for c in maj1_code])

# ~15% have a second major
has_second = rng.random(N) < 0.15
majnum = np.where(has_second, 2, 1)
maj2_code = np.where(has_second, choice(maj_codes), -9)
maj2_col = np.array([code_to_col[c] if c != -9 else -9 for c in maj2_code])
maj2_text = np.where(
    has_second,
    np.array([f"{FIELD_NAMES[(c - 1001) % len(FIELD_NAMES)]}: Track {(c % 5) + 1}" if c != -9 else "-9"
              for c in maj2_code]),
    "-9")

# ---- begincol / edaspire / attendance --------------------------------------
begincol = choice([0, 1], p=[0.55, 0.45])
edaspire = choice([1, 2, 3, 4], p=[0.15, 0.30, 0.35, 0.20])
attend_voc = choice([0, 1], p=[0.85, 0.15])
attend_com = choice([0, 1], p=[0.70, 0.30])
attend_col = choice([0, 1], p=[0.40, 0.60])
attend_none = choice([0, 1], p=[0.88, 0.12])
attend_other = choice([0, 1], p=[0.90, 0.10])

# ---- logdate: random day Feb-May of the row's Year -------------------------
def rand_date(y):
    # Feb 1 .. May 31
    start = np.datetime64(f"{y}-02-01")
    span = (np.datetime64(f"{y}-05-31") - start).astype(int)
    return start + np.timedelta64(int(rng.integers(0, span + 1)), "D")
logdate = np.array([rand_date(y) for y in year], dtype="datetime64[D]")

# ---- duration: lognormal around ~12 min, few large outliers ----------------
duration = np.round(rng.lognormal(mean=np.log(12), sigma=0.5, size=N), 1)
outliers = rng.random(N) < 0.02
duration[outliers] = np.round(duration[outliers] * rng.uniform(3, 6, size=outliers.sum()), 1)

# ---- 10 engagement scales 0..60 (rounded 1 dp), mildly correlated ----------
base = rng.normal(35, 9, size=N)                   # shared latent engagement
SCALES = ["HO", "RI", "LS", "QR", "CL", "DD", "SF", "ET", "QI", "SE"]
scale_data = {}
for s in SCALES:
    vals = base + rng.normal(0, 7, size=N)
    scale_data[s] = np.round(np.clip(vals, 0, 60), 1)

# ---- assemble ---------------------------------------------------------------
df = pd.DataFrame({
    "row_id": np.arange(N),
    "ID": rng.choice(np.arange(10000, 100000), size=N, replace=False),  # unique 5-digit
    "Year": year,
    "Class": klass,
    "program": program,
    "FTFY": ftfy,
    "affiliation": aff,
    "MAJfirstcode": maj1_code,
    "MAJfirstcol": maj1_col,
    "MAJfirst": maj1_text,
    "MAJnum": majnum,
    "MAJsecondcode": maj2_code,
    "MAJsecondcol": maj2_col,
    "MAJsecond": maj2_text,
    "begincol": begincol,
    "edaspire": edaspire,
    "attend_voc": attend_voc, "attend_com": attend_com, "attend_col": attend_col,
    "attend_none": attend_none, "attend_other": attend_other,
    "logdate": logdate,
    "duration": duration,
    **scale_data,
})

# ---- inject ~10-14% missingness in the major block (together), begincol, edaspire
miss = rng.random(N) < 0.12
major_cols = ["MAJfirstcode", "MAJfirstcol", "MAJfirst", "MAJnum",
              "MAJsecondcode", "MAJsecondcol", "MAJsecond"]
for c in major_cols:
    df.loc[miss, c] = np.nan
df.loc[rng.random(N) < 0.12, "begincol"] = np.nan
df.loc[rng.random(N) < 0.10, "edaspire"] = np.nan

# ---- plant the fake PII (names/emails/IDs/comments) -------------------------
planted, _truth = plant_identifiers(df, seed=SEED)

# ---- save -------------------------------------------------------------------
out_path = pathlib.Path(__file__).resolve().parents[1] / "examples" / "demo_planted.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)
to_save = planted.copy()
to_save["logdate"] = pd.to_datetime(to_save["logdate"]).dt.strftime("%Y-%m-%d")
to_save.to_csv(out_path, index=False)  # NaN -> empty cell by default

# ---- summary ----------------------------------------------------------------
size_mb = out_path.stat().st_size / 1e6
print("Wrote", out_path)
print("shape:", to_save.shape, "| size: %.2f MB" % size_mb)
print("affiliation counts:\n", planted["affiliation"].value_counts(dropna=False).to_string())
print("Class counts:", dict(planted["Class"].value_counts()))
print("has 2nd major:", int((planted["MAJnum"] == 2).sum()),
      "| missing major rows:", int(planted["MAJfirstcode"].isna().sum()))
print("columns:", list(to_save.columns))
