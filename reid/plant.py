import random
import pandas as pd
from faker import Faker

CLEAN = [
    "The tutoring center really helped me this semester.",
    "I wish there were more evening study spaces.",
    "Advising appointments are hard to book.",
    "Dining options improved a lot this year.",
    "Group projects taught me the most.",
    "I felt welcome in my first-year seminar.",
]
DECOYS = [  # look like PII but are not (should NOT be flagged)
    "Mugar Library is my favorite place to study.",
    "CS 111 was the hardest course I took.",
    "The Warren Towers dining hall gets crowded at noon.",
    "Room 617 in the CDS building is always cold.",
    "I joined the Kite Studies club in my second year.",
]
PII_TEMPLATES = [  # (text pieces, entity types) - None marks a literal piece
    [("My advisor ", None), ("{person}", "PERSON"), (" was incredibly supportive.", None)],
    [("Please follow up with me at ", None), ("{email}", "EMAIL_ADDRESS"), (" about the survey.", None)],
    [("You can text me at ", None), ("{phone}", "PHONE_NUMBER"), (" if you want details.", None)],
    [("My student ID is ", None), ("{bu_id}", "BU_ID"), (", my financial aid is still wrong.", None)],
    [("I'm ", None), ("{person}", "PERSON"), (" and my roommate ", None), ("{person}", "PERSON"), (" agrees housing is too expensive.", None)],
    [("Email ", None), ("{email}", "EMAIL_ADDRESS"), (" or call ", None), ("{phone}", "PHONE_NUMBER"), (" to reach me.", None)],
]

def _bu_id(rng):
    return "U" + "".join(str(rng.randint(0, 9)) for _ in range(8))

def _phone(rng):
    return f"617-{rng.randint(200, 999)}-{rng.randint(0, 9999):04d}"

def plant_identifiers(df, seed=42, pct_pii=0.30, pct_decoy=0.10):
    fake = Faker("en_US")
    Faker.seed(seed)
    rng = random.Random(seed)
    out = df.copy()
    names, emails, ids, comments, truth = [], [], [], [], []
    for row_id in out["row_id"]:
        first, last = fake.first_name(), fake.last_name()
        name = f"{first} {last}"
        email = f"{first[0].lower()}{last.lower()}{rng.randint(1, 99)}@bu.edu"
        sid = _bu_id(rng)
        names.append(name); emails.append(email); ids.append(sid)
        u = rng.random()
        if u < pct_pii:
            text = ""
            for piece, etype in rng.choice(PII_TEMPLATES):
                if etype is None:
                    text += piece
                    continue
                value = {"PERSON": lambda: rng.choice([name, fake.name()]),
                         "EMAIL_ADDRESS": lambda: email,
                         "PHONE_NUMBER": lambda: _phone(rng),
                         "BU_ID": lambda: sid}[etype]()
                start = len(text)
                text += value
                truth.append({"row_id": row_id, "entity_type": etype, "value": value,
                              "start": start, "end": start + len(value)})
            comments.append(text)
        elif u < pct_pii + pct_decoy:
            comments.append(rng.choice(DECOYS))
        else:
            comments.append(rng.choice(CLEAN))
    out["full_name"], out["email"], out["student_id"], out["comment"] = names, emails, ids, comments
    return out, pd.DataFrame(truth, columns=["row_id", "entity_type", "value", "start", "end"])
