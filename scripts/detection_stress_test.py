"""Out-of-sample stress test for presidio_detect.

20 hand-written sentences that were NOT used for tuning: 10 contain real-looking
PERSON names (several as the SECOND name in the sentence), 10 contain BU place or
course names that do NOT appear in reid/plant.py templates/decoys. We score the
CURRENT detector as-is and report; no rules are changed based on this test.

Each case carries a hand label:
  expect_person = True  -> at least one PERSON span is the desired outcome
  expect_person = False -> any PERSON span is a false positive (place/course only)
"""
import os
import pandas as pd
from reid.pii_text import presidio_detect

# (sentence, expect_person, note)
CASES = [
    # 10 with real-looking names (several as the second / later name)
    ("My friend Ana Ruiz and I went to the career fair.", True, "name as second subject"),
    ("I'm Jordan and my lab partner Priya Nair did the writeup.", True, "second name, partner"),
    ("Coach Marcus Bell changed the whole season for us.", True, "name after a title"),
    ("The TA, Wei Zhang, explained recursion clearly.", True, "name in appositive"),
    ("My roommate Diego Fernandez never cleans the kitchen.", True, "second name, roommate"),
    ("I met Fatima Al-Sayed at the transfer orientation.", True, "hyphenated surname"),
    ("Thanks to Nia Okafor and her study group I passed.", True, "name after Thanks"),
    ("Both Liam O'Connor and Grace Park ran for senate.", True, "two names, apostrophe"),
    ("Dr. Rosa Martinez wrote my recommendation letter.", True, "name after Dr."),
    ("Ask Samuel Greene in the registrar about my transcript.", True, "name mid-sentence"),
    # 10 with BU place or course names NOT in our templates
    ("Marsh Chapel was peaceful on Sunday morning.", False, "BU place: Marsh Chapel"),
    ("I study at the GSU between classes.", False, "BU place acronym: GSU"),
    ("Questrom classes are hard but worth it.", False, "BU school: Questrom"),
    ("Agganis Arena games are fun to attend.", False, "BU venue: Agganis Arena"),
    ("Professor office hours were in Kenmore Square.", False, "BU area: Kenmore Square"),
    ("The Fitrec gym gets packed after 5pm.", False, "BU facility: FitRec"),
    ("I love grabbing food on Comm Ave.", False, "BU street: Comm Ave"),
    ("Photonics Center labs stay open late.", False, "BU building: Photonics Center"),
    ("CAS WR 120 was my hardest writing seminar.", False, "BU course code"),
    ("The BU Beach is crowded when it is sunny.", False, "BU landmark: BU Beach"),
]

rows = []
for sentence, expect_person, note in CASES:
    spans = presidio_detect(sentence)
    persons = [sentence[s["start"]:s["end"]] for s in spans if s["entity_type"] == "PERSON"]
    other = [f"{s['entity_type']}:{sentence[s['start']:s['end']]}" for s in spans if s["entity_type"] != "PERSON"]
    got_person = len(persons) > 0
    if expect_person:
        outcome = "correct (name found)" if got_person else "MISS (name not found)"
    else:
        outcome = "false alarm (PERSON on place)" if got_person else "correct (no PERSON)"
    rows.append({
        "category": "name" if expect_person else "place_or_course",
        "sentence": sentence,
        "note": note,
        "expect_person": expect_person,
        "person_spans": "; ".join(persons),
        "other_spans": "; ".join(other),
        "got_person": got_person,
        "outcome": outcome,
    })

df = pd.DataFrame(rows)
os.makedirs("results", exist_ok=True)
df.to_csv("results/detection_stress_test.csv", index=False)
print("Saved results/detection_stress_test.csv")

pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 60)
print("\n--- NAME sentences (want PERSON) ---")
print(df[df.category == "name"][["sentence", "person_spans", "outcome"]].to_string(index=False))
print("\n--- PLACE/COURSE sentences (want NO PERSON) ---")
print(df[df.category == "place_or_course"][["sentence", "person_spans", "other_spans", "outcome"]].to_string(index=False))

names = df[df.category == "name"]
places = df[df.category == "place_or_course"]
name_hits = int(names.got_person.sum())
place_fp = int(places.got_person.sum())
print(f"\nNames detected:        {name_hits}/{len(names)}  (misses = {len(names)-name_hits})")
print(f"Place/course clean:    {len(places)-place_fp}/{len(places)}  (false alarms = {place_fp})")
