import json
import re
import numpy as np
import pandas as pd
from reid import llm

ROLES = ["direct_id", "quasi_id", "metadata", "sensitive", "free_text", "planted_pii", "derived", "other"]


def profile_columns(df):
    """Metadata only: no row-level values leave this function except <=8 category labels."""
    prof = []
    for c in df.columns:
        if c == "row_id":
            continue
        s = df[c]
        nun = int(s.nunique(dropna=True))
        p = {"name": c, "dtype": str(s.dtype), "n_unique": nun,
             "pct_missing": round(float(s.isna().mean()), 3),
             "pct_unique_values": round(nun / max(int(s.notna().sum()), 1), 3)}
        if nun <= 20:
            p["top_values"] = [str(v) for v in s.value_counts().index[:8]]
        if s.dtype == object or str(s.dtype) in ("str", "string"):
            p["avg_text_len"] = round(float(s.dropna().astype(str).str.len().mean() or 0), 1)
        prof.append(p)
    return prof


def _is_numeric_dtype(dt):
    try:
        return np.issubdtype(np.dtype(dt), np.number)
    except TypeError:
        return False


def _heuristic(p):
    name, dt = p["name"].lower(), p["dtype"]
    if re.search(r"(^|_)(name|email|phone|ssn)($|_)|student_id", name):
        return "planted_pii", "Name suggests a personal identifier."
    if p.get("avg_text_len", 0) > 30:
        return "free_text", "Long free text may contain personal details."
    if p["pct_unique_values"] > 0.95 and p["n_unique"] > 1000:
        return "direct_id", "Almost every value is unique, so it points to one person."
    if "date" in name or "time" in name or "duration" in name or "datetime" in dt:
        return "metadata", "Survey timing data can single people out."
    if (dt in ("object", "str", "string") and p["n_unique"] <= 100) or \
       re.search(r"^(year|class|program|affiliation|gender|sex|race|ethnicity|age|ftfy|residence)$|^maj|aspire|^begin|^attend", name):
        return "quasi_id", "Demographic or enrollment detail that could be known to outsiders."
    if _is_numeric_dtype(dt):
        return "sensitive", "Survey answer or score."
    return "other", "No clear privacy role."


def roles_from_config(cfg):
    """Known schema for the BU NSSE file (used as the prior)."""
    r = cfg["roles"]
    known = {}
    for c in r["direct_ids"]:
        known[c] = "direct_id"
    for c in r["quasi_ids"] + r["quasi_ids_extended"]:
        known[c] = "quasi_id"
    for c in r["metadata"]:
        known[c] = "metadata"
    for c in r["derived_major"]:
        known[c] = "derived"
    for c in r["planted"]:
        known[c] = "free_text" if c == "comment" else "planted_pii"
    return known


def classify_columns(profile, known_roles=None, batch=40):
    known_roles = known_roles or {}
    result = {}
    for p in profile:
        if p["name"] in known_roles:
            result[p["name"]] = {"role": known_roles[p["name"]], "reason": "Known schema for this dataset.",
                                 "confidence": 0.9, "source": "schema"}
        else:
            role, reason = _heuristic(p)
            result[p["name"]] = {"role": role, "reason": reason, "confidence": 0.6, "source": "heuristic"}
    if not llm.llm_enabled():
        return result
    system = ("You are a data privacy analyst. Classify each column of a student survey dataset into one role: "
              "direct_id (identifies a person alone), quasi_id (harmless alone but identifying in combination, "
              "e.g. year, major, demographics), metadata (survey timing such as dates or durations), "
              "sensitive (survey answers), free_text, planted_pii (fake names/emails/IDs added for testing), derived, other. "
              "You see only column metadata, never rows.")
    for i in range(0, len(profile), batch):
        chunk = profile[i:i + batch]
        out = llm.parse_json(llm.complete(
            "Columns:\n" + json.dumps(chunk) +
            '\nReturn a JSON object mapping each column name to {"role": ..., "reason": "<12 words", "confidence": 0-1}.',
            system=system, json_mode=True, max_tokens=4000))
        if isinstance(out, dict):
            for col, v in out.items():
                if col in result and result[col]["role"] == "derived":
                    continue  # derived columns follow their source column's hierarchy
                if col in result and isinstance(v, dict) and v.get("role") in ROLES:
                    result[col] = {"role": v["role"], "reason": str(v.get("reason", ""))[:120],
                                   "confidence": float(v.get("confidence", 0.7)), "source": "llm"}
    return result
