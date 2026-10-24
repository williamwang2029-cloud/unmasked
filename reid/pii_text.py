"""Role B — PII detection, scrubbing, and scoring.

Presidio (small spaCy model `en_core_web_sm`) + a custom BU_ID regex recognizer,
an optional LLM detector (Role C), span de-overlapping, scrubbing, and scoring
against ground truth. Transcribed from the authoritative reference in design.md.
"""
import re
import pandas as pd
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from reid import llm

ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "BU_ID"]
# Common single words the small spaCy model mis-tags as PERSON. A PERSON span
# whose text is exactly one of these (case-insensitive) is dropped after detection.
PERSON_DENYLIST = ["Email", "Call", "Text", "Please", "My", "Room", "Hi", "Thanks"]
# Place words: if the word immediately AFTER a PERSON span is one of these, the
# span is a building/location name (e.g. "Mugar Library"), not a person. This is a
# general rule keyed on the following word, not on any specific planted decoy.
PLACE_WORDS = ["Library", "Hall", "Center", "Centre", "Building", "Towers", "Room"]
_analyzer = None

def _engine():
    global _analyzer
    if _analyzer is None:
        provider = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]})
        _analyzer = AnalyzerEngine(nlp_engine=provider.create_engine(), supported_languages=["en"])
        _analyzer.registry.add_recognizer(PatternRecognizer(
            supported_entity="BU_ID", patterns=[Pattern("bu_id", r"\bU\d{8}\b", 0.9)]))
    return _analyzer

def presidio_detect(text, threshold=0.35):
    res = _engine().analyze(text=text, language="en", entities=ENTITIES, score_threshold=threshold)
    _deny = {w.lower() for w in PERSON_DENYLIST}
    _places = {w.lower() for w in PLACE_WORDS}
    spans = [{"entity_type": r.entity_type, "start": r.start, "end": r.end, "score": float(r.score)} for r in res]

    def _drop_person(s):
        span_text = text[s["start"]:s["end"]].strip()
        if span_text.lower() in _deny:
            return True
        # Drop building/location names flagged as PERSON. A place word (Library,
        # Hall, ...) either ends the span itself ("Mugar Library") or immediately
        # follows it ("Warren Towers") -> treat the whole thing as a place, not a person.
        words = re.findall(r"[A-Za-z]+", span_text)
        if words and words[-1].lower() in _places:
            return True
        m = re.match(r"\s*([A-Za-z]+)", text[s["end"]:])
        return bool(m) and m.group(1).lower() in _places

    return [s for s in spans if not (s["entity_type"] == "PERSON" and _drop_person(s))]

LLM_SYSTEM = ("You find personal information in short survey comments. Entity types: "
              "PERSON (a person's name), EMAIL_ADDRESS, PHONE_NUMBER, BU_ID (U followed by 8 digits). "
              "Building names, course codes, and room numbers are NOT personal information.")

def llm_detect(text):
    out = llm.parse_json(llm.complete(
        f'Comment: """{text}"""\nReturn a JSON list of objects with keys "entity_type" and "text" '
        f'(the exact substring). Return [] if none.', system=LLM_SYSTEM, json_mode=True, max_tokens=300))
    if not isinstance(out, list):
        return []
    spans = []
    for item in out:
        if not isinstance(item, dict) or item.get("entity_type") not in ENTITIES:
            continue
        sub = str(item.get("text", ""))
        start = text.find(sub) if sub else -1
        while start != -1:
            spans.append({"entity_type": item["entity_type"], "start": start, "end": start + len(sub), "score": 1.0})
            start = text.find(sub, start + 1)
    return spans

def _dedupe(spans):
    spans = sorted(spans, key=lambda s: (-s["score"], s["start"]))
    kept = []
    for s in spans:
        if all(s["end"] <= k["start"] or s["start"] >= k["end"] for k in kept):
            kept.append(s)
    return sorted(kept, key=lambda s: s["start"])

def scrub_text(text, method="presidio", spans=None):
    if spans is None:
        spans = presidio_detect(text) if method == "presidio" else llm_detect(text)
    for s in sorted(_dedupe(spans), key=lambda s: -s["start"]):
        text = text[:s["start"]] + f"<{s['entity_type']}>" + text[s["end"]:]
    return text

def combine(a, b):
    return _dedupe(list(a) + list(b))

def evaluate_detection(truth_df, predictions):
    """predictions: {row_id: [span dicts]} for the rows that were scored.
    Only rows present in `predictions` are evaluated."""
    rows = {e: {"tp": 0, "fp": 0, "fn": 0} for e in ENTITIES}
    truth_by_row = {rid: g.to_dict("records") for rid, g in truth_df.groupby("row_id")}
    for rid, preds in predictions.items():
        truth = truth_by_row.get(rid, [])
        matched = set()
        for p in _dedupe(preds):
            hit = None
            for i, t in enumerate(truth):
                if i not in matched and t["entity_type"] == p["entity_type"] and p["start"] < t["end"] and t["start"] < p["end"]:
                    hit = i
                    break
            if hit is None:
                rows[p["entity_type"]]["fp"] += 1
            else:
                matched.add(hit)
                rows[p["entity_type"]]["tp"] += 1
        for i, t in enumerate(truth):
            if i not in matched:
                rows[t["entity_type"]]["fn"] += 1
    out = pd.DataFrame([{"entity_type": e, **v} for e, v in rows.items()])
    tot = out[["tp", "fp", "fn"]].sum()
    out.loc[len(out)] = {"entity_type": "ALL", **tot.to_dict()}
    out["precision"] = out.tp / (out.tp + out.fp).replace(0, float("nan"))
    out["recall"] = out.tp / (out.tp + out.fn).replace(0, float("nan"))
    out["f1"] = 2 * out.precision * out.recall / (out.precision + out.recall)
    return out
