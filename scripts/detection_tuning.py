"""Detection tuning: build planted/truth parquet if missing, then score a
1,500-comment sample across four settings and save results/detection_tuning.csv.

Settings:
  1. threshold 0.4,  no deny-list (original Presidio behaviour)
  2. threshold 0.4,  with the PERSON word deny-list
  3. threshold 0.35, with the PERSON word deny-list
  4. threshold 0.35, with deny-list + the general place-word rule (current module default)
"""
import os
import re
import pandas as pd
import yaml

from reid.plant import plant_identifiers
from reid.pii_text import (ENTITIES, PERSON_DENYLIST, PLACE_WORDS, _engine,
                           presidio_detect, evaluate_detection, _dedupe)

cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
planted_path = cfg["data"]["planted_parquet"]
truth_path = cfg["data"]["truth_parquet"]

# 1) Ensure planted + truth parquet exist (regenerate from the raw xlsx if not).
if os.path.exists(planted_path) and os.path.exists(truth_path):
    print(f"Using existing {planted_path} and {truth_path}")
    planted = pd.read_parquet(planted_path)
    truth = pd.read_parquet(truth_path)
else:
    print("Planted/truth parquet missing -> regenerating from raw xlsx via plant_identifiers")
    df = pd.read_excel(cfg["data"]["raw_xlsx"], sheet_name="in")
    df.insert(0, "row_id", range(len(df)))
    planted, truth = plant_identifiers(df)
    planted = planted.copy()
    # pyarrow cannot serialize object columns holding mixed int/str values.
    # Stringify ONLY the non-null cells so real missing values stay missing
    # (NaN) instead of turning into the literal text "nan".
    converted = []
    for col in planted.columns:
        if planted[col].dtype == object:
            mask = planted[col].notna()
            planted.loc[mask, col] = planted.loc[mask, col].astype(str)
            converted.append(col)
    print("Stringified object columns (NaN preserved):", converted)
    os.makedirs(os.path.dirname(planted_path), exist_ok=True)
    planted.to_parquet(planted_path)
    truth.to_parquet(truth_path)
    print(f"Wrote {planted_path} ({len(planted)} rows) and {truth_path} ({len(truth)} entities)")

# 2) 1,500-comment tuning sample (rows with non-empty comments), random_state=7.
commented = planted[planted["comment"].astype(str).str.len() > 0]
sample = commented.sample(1500, random_state=7)
print(f"Sampled {len(sample)} commented rows (random_state=7)")

_deny = {w.lower() for w in PERSON_DENYLIST}

def detect_raw(text, threshold):
    """Raw Presidio spans, no post-filtering."""
    res = _engine().analyze(text=text, language="en", entities=ENTITIES, score_threshold=threshold)
    return [{"entity_type": r.entity_type, "start": r.start, "end": r.end, "score": float(r.score)} for r in res]

def apply_denylist(text, spans):
    return [s for s in spans
            if not (s["entity_type"] == "PERSON" and text[s["start"]:s["end"]].strip().lower() in _deny)]

def predict(label, threshold):
    preds = {}
    for r in sample.itertuples():
        if label == "threshold 0.4, no deny-list (original)":
            spans = detect_raw(r.comment, threshold)
        elif label == "threshold 0.35, deny-list + place-word rule":
            # Full current module behaviour (deny-list + place rule) at its default threshold.
            spans = presidio_detect(r.comment, threshold)
        else:
            spans = apply_denylist(r.comment, detect_raw(r.comment, threshold))
        preds[r.row_id] = spans
    return preds

SETTINGS = [
    ("threshold 0.4, no deny-list (original)",        0.40),
    ("threshold 0.4, with deny-list",                 0.40),
    ("threshold 0.35, with deny-list",                0.35),
    ("threshold 0.35, deny-list + place-word rule",   0.35),
]

all_tables, pred_cache = [], {}
for label, thr in SETTINGS:
    preds = predict(label, thr)
    pred_cache[label] = preds
    tbl = evaluate_detection(truth, preds)
    tbl.insert(0, "setting", label)
    all_tables.append(tbl)

result = pd.concat(all_tables, ignore_index=True)
os.makedirs("results", exist_ok=True)
result.to_csv("results/detection_tuning.csv", index=False)
print("\nSaved results/detection_tuning.csv")

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
for label, _ in SETTINGS:
    sub = result[result["setting"] == label][["entity_type", "tp", "fp", "fn", "precision", "recall", "f1"]]
    print("\n=== " + label + " ===")
    print(sub.round(4).to_string(index=False))

# Best setting = highest ALL f1 (ties broken by lowest fp, then order).
all_rows = result[result["entity_type"] == "ALL"].copy()
best_label = all_rows.sort_values(["f1", "fp"], ascending=[False, True]).iloc[0]["setting"]
print("\nBest setting by ALL F1: " + best_label)

truth_by_row = {rid: g.to_dict("records") for rid, g in truth.groupby("row_id")}
comment_by_row = sample.set_index("row_id")["comment"].to_dict()

# False alarms (FP) and missed names (FN), mirroring evaluate_detection's matching.
false_alarms, missed_persons = [], []
for rid, preds in pred_cache[best_label].items():
    tr = truth_by_row.get(rid, [])
    matched = set()
    for pr in _dedupe(preds):
        hit = None
        for i, t in enumerate(tr):
            if i not in matched and t["entity_type"] == pr["entity_type"] and pr["start"] < t["end"] and t["start"] < pr["end"]:
                hit = i
                break
        if hit is None:
            c = comment_by_row[rid]
            false_alarms.append({"entity_type": pr["entity_type"], "text": c[pr["start"]:pr["end"]], "comment": c})
        else:
            matched.add(hit)
    for i, t in enumerate(tr):
        if i not in matched and t["entity_type"] == "PERSON":
            missed_persons.append({"row_id": rid, "value": t["value"], "comment": comment_by_row[rid]})

print(f"\nFalse alarms in best setting ({best_label}): {len(false_alarms)} total; showing up to 10:")
for fa in false_alarms[:10]:
    print("  [{}] {!r}  <- {!r}".format(fa["entity_type"], fa["text"], fa["comment"]))

print(f"\nMissed PERSON entities (false negatives) in best setting: {len(missed_persons)} total:")
for mp in missed_persons:
    print("  missed {!r}  <- {!r}".format(mp["value"], mp["comment"]))
