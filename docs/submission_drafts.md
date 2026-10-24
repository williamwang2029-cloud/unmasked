# Submission drafts (Sundai + Devpost)

## Tagline
Removing names isn't anonymity. Unmasked measures, fixes, and explains re-identification risk in student data.

## Inspiration
BU wants students to work with institutional data, but "de-identified" files can still expose individuals. In BU's
synthetic survey data, 68% of students are unique on eight ordinary fields.

## What it does
1. An AI agent labels each column's privacy role using metadata only.
2. Measures k-anonymity, uniqueness, riskiest field combinations, metadata leaks, attacker personas, and a simulated linkage attack.
3. Tokenizes IDs (keyed HMAC tokens + encrypted vault with a separate key), removes direct identifiers, scrubs free text with Presidio.
4. Optimizes generalization and suppression to reach k >= 5 with <= 5% of records removed, optionally protecting small demographic groups.
5. Verifies with the attack, measures usefulness (group means, ML utility test) and fairness, and writes a plain-English report and a privacy nutrition label.

## How we built it
Python, pandas, scikit-learn, Microsoft Presidio + spaCy, Faker, cryptography (HMAC + Fernet), Streamlit + Plotly,
an LLM agent that only sees metadata, built with Kiro's spec-driven workflow.

## Data science
k-anonymity and l-diversity metrics, combinatorial risk search, a greedy constrained optimizer for generalization
and suppression, simulated linkage attacks with ground truth, precision/recall on planted PII, a privacy-utility
curve, an ML utility test, and a group fairness analysis.

## Challenges
Steep privacy-utility tradeoffs, keeping derived columns consistent, and avoiding sending data to the LLM.

## Accomplishments
Attack success from 68.5% to 0% with 2.5% of records removed; the fairness finding.

## What we learned
Privacy protection costs small groups the most, and optimizers can hide that by deleting the group column.

## What's next
Differential privacy releases, must-keep analysis constraints, and a pilot with BU IS&T on real data in a secure environment.

## Built with
python, pandas, scikit-learn, presidio, spacy, faker, cryptography, streamlit, plotly, kiro, [llm provider]

---

## Sunday pitch (3 min, hard limit)
1. Hook (20 s): "No names, no IDs, and still 68% of these students can be singled out."
2. Problem (30 s): removing names isn't enough; FERPA reasonable-certainty standard; BU wants student projects on real data.
3. Live demo (75 s): roles -> risk -> run agent -> attack fails. Keep a screen recording ready.
4. Evidence (35 s): curve, ML utility, detection scores.
5. Insight (20 s): fairness finding with the toggle.
6. Close (10 s): who uses it next.

Split: A (hook + risk), C (demo), B (evidence + insight). Rehearse with a timer at least three times after 9:30 PM.

## Video script (2:00)
| Time | Screen | Narration |
|---|---|---|
| 0:00-0:15 | Tab 1 | "This BU survey file has no names. Is it anonymous? Using just eight ordinary fields, 68% of students can be singled out." |
| 0:15-0:30 | Tab 3 staircase + heatmap | "Each field you add makes more students unique. Even the survey's completion date alone identifies 12%." |
| 0:30-0:45 | Tab 2 roles | "Our AI agent labels every column's privacy role using only column metadata." |
| 0:45-1:10 | Tab 4 live log | "It tokenizes IDs into an encrypted vault, removes names and emails, then coarsens fields until every group has at least five students." |
| 1:10-1:30 | Tab 5 attack + label | "We attack our own release: 68% re-identified before, zero after, with only 2.5% of records removed." |
| 1:30-1:50 | Tab 5 fairness chart | "But privacy isn't paid evenly. Without a safeguard, the optimizer silently deletes the demographic column. With it, the smallest groups lose up to eight times more records." |
| 1:50-2:00 | README / Kiro specs | "Built with Kiro's spec-driven workflow, for BU IS&T." |

## Sundai checklist (by 7:30 PM)
- [ ] All code merged to main; `python scripts/smoke_test.py` passes
- [ ] `git tag hackachusetts-submission && git push --tags`
- [ ] `git status` clean of data/keys/.env; search repo for `ANTHROPIC_API_KEY=` and `sk-`
- [ ] `.kiro/` committed (steering + 3 specs)
- [ ] README complete (Built with Kiro, ethics); video link works logged out
- [ ] Sundai portal: Civic Action track (CollegeHack V4), title, one-liner, description, repo URL, video URL, all 3 members
- [ ] Screenshot the confirmation
