import pandas as pd
from reid.plant import plant_identifiers
df = pd.read_excel("data/NSSE-synthetic.xlsx", sheet_name="in")
df.insert(0, "row_id", range(len(df)))
p, t = plant_identifiers(df)
comments = p.set_index("row_id")["comment"]
bad = [r for r in t.itertuples() if comments[r.row_id][r.start:r.end] != r.value]
print(len(t), "planted entities,", len(bad), "span errors")
print(p[["full_name", "email", "student_id", "comment"]].head())
