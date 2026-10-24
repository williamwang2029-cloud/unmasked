# Submission drafts (Sundai + Devpost)

---

# FINAL SUBMISSION TEXT (verified numbers — use these)

## Sundai project card

**Title:** Unmasked: Re-identification Risk Meter

**Track:** Civic Action (CollegeHack V4 — BU IS&T Data Scrubbing / Tokenization challenge)

**One-liner (under 20 words):**
Removing names isn't anonymity: Unmasked measures, fixes, and explains re-identification risk in student survey data.

**Description (~150 words):**
"De-identified" student data often isn't. In BU's synthetic NSSE survey file, 67.8% of students are unique on
just eight ordinary fields, 73.9% on fourteen, and 99.99% on all 14 fields plus survey timing. Unmasked is an
AI-agent pipeline that labels each column's privacy role from metadata only, measures k-anonymity, uniqueness,
and attacker-persona risk, then runs a simulated linkage attack: an attacker knowing all nine core fields
re-identifies 68.5% of targets. The agent tokenizes IDs into an encrypted vault, scrubs free text with Presidio,
and generalizes and suppresses fields until every group has at least five students, dropping attack success from
68.5% to 0% while removing only 2.5% of records. It then measures what the fix costs: ML utility falls modestly
(R² 0.42 to 0.37), and the smallest demographic group loses about 8x more records than the largest. Built with
Kiro; the LLM sees only column metadata and computed metrics (never student rows).

**Tech used:** Python, pandas, scikit-learn, Microsoft Presidio + spaCy, Faker, cryptography (HMAC + Fernet),
Streamlit + Plotly, Kiro (spec-driven development), Gemini via an OpenAI-compatible endpoint.

**Links:**
- GitHub: GITHUB_URL
- Video: VIDEO_URL

---

## DS+X Devpost page

**Inspiration**
BU wants students to build on institutional data, but "de-identified" files can still expose individuals. In BU's
synthetic survey data, 67.8% of students are unique on eight ordinary fields, and 99.99% on all 14 fields plus
survey timing (the survey date alone makes 11.7% unique, duration alone 11.6%). Removing names clearly isn't
enough.

**What it does**
1. An AI agent labels each column's privacy role using metadata only.
2. Measures k-anonymity, uniqueness, riskiest field combinations, metadata leaks, attacker personas, and a
   simulated linkage attack (68.5% re-identified by an attacker who knows all nine core fields).
3. Tokenizes IDs (keyed HMAC tokens + encrypted vault with a separate key), removes direct identifiers, and
   scrubs free text with Presidio.
4. Optimizes generalization and suppression to reach k >= 5 with only 2.5% of records removed, optionally
   protecting small demographic groups.
5. Verifies with the attack (down to 0%), measures usefulness (group means, ML utility test) and fairness, and
   writes a plain-English report and a privacy nutrition label.

**How we built it**
Python, pandas, scikit-learn, Microsoft Presidio + spaCy, Faker, cryptography (HMAC + Fernet), Streamlit + Plotly,
and an LLM agent (Gemini, supported through an OpenAI-compatible endpoint) that sees only column metadata and
computed metrics, never student rows (the one exception is an optional detection test on fully synthetic planted
comments). Built with Kiro: three specs (role-a-risk-engine, role-b-mitigation, role-c-agent-app) and shared
steering files let three people build in parallel against fixed interface contracts. Roles A and B built their
modules spec-first; Role C's spec documents its agent and app, with Kiro used for the Gemini integration, a
release-warning feature, drafting, merges, and troubleshooting.

**Challenges**
Steep privacy-utility tradeoffs, keeping derived columns consistent through generalization, never sending row
data to the LLM, and coordinating three branches in a repo that lived inside OneDrive (which fought git).

**Accomplishments**
Linkage-attack success from 68.5% to 0% with only 2.5% of records removed; PII detection at 1.00
precision/recall on structured identifiers (emails, phones, IDs) on our planted test data, with names at 1.00
precision / 0.91 recall (0.90 / 0.90 on an out-of-sample stress test); and a fairness finding: the smallest
group loses about 8x more records than the largest.

**What we learned**
Privacy protection costs small groups the most, and an unconstrained optimizer can hide that by deleting the
group column entirely. Measuring who pays is as important as measuring the risk.

**What's next**
Differential-privacy releases, must-keep analysis constraints, and a pilot with BU IS&T on real data in a secure
environment.

**Built with**
python, pandas, scikit-learn, presidio, spacy, faker, cryptography, streamlit, plotly, kiro, gemini

---

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
| 0:15-0:30 | Tab 3 staircase + heatmap | "Each field you add makes more students unique. Even the survey's completion date alone singles out about 12% (11.7%)." |
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
