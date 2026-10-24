# How we used Kiro

Unmasked was built by three people in about ten hours. Kiro was the development environment for all three,
and its spec-driven workflow is what let us build in parallel without breaking each other''s code. This
write-up covers what we used, how, and what we didn''t use.

Everything referenced here is in the repo: specs in `.kiro/specs/`, steering in `.kiro/steering/`, the agent
hook in `.kiro/hooks/`, and the property-based tests in `tests/`.

## 1. Our strategy: one project, three specs, fixed contracts

Before writing code, we planned the architecture and the **interface contracts** between modules: exact file
names, function signatures, return keys, and column conventions. We wrote these into a planning brief for each
role (drafted with help from a general-purpose AI assistant) and fed each brief into Kiro as the source for
that role''s spec:

| Spec | Owner | Builds |
|---|---|---|
| `role-a-risk-engine` | Kieran McBride | data loading, risk metrics, attacker personas, linkage attack, charts |
| `role-b-mitigation` | Kealoha Comcowich | planted PII, Presidio detection, token vault, generalization optimizer, utility and fairness |
| `role-c-agent-app` | William Wang | LLM wrapper, column classifier, privacy agent, Streamlit app |

Each spec only covered its owner''s files and treated the other two as external interfaces. That boundary is
why three people could work in separate Kiro sessions all day and still merge cleanly.

## 2. Kiro tools used

We used the **Kiro IDE** for all development: the agentic chat, spec creation, spec task execution, steering,
and agent hooks. We did not use the Kiro CLI, Kiro Web, or Crew.

## 3. Spec-driven development

**How the specs are structured.** Each spec has the standard three documents:

- **`requirements.md`**: user stories with acceptance criteria in EARS notation ("WHEN ... THE SYSTEM SHALL
  ..."). Acceptance criteria include exact reference numbers (for example, "8 core fields -> 67.8% unique,
  within +/-0.2 points").
- **`design.md`**: architecture, component contracts, data conventions, error handling, and testing strategy.
  Role A''s design documents one deliberate deviation (making the cache builder tolerate Role B''s module not
  existing yet, so Role A was never blocked).
- **`tasks.md`**: ordered tasks, each ending in an acceptance check. Role B''s spec used Kiro''s
  **design-first** workflow (recorded in `.kiro/specs/role-b-mitigation/.config.kiro`), because the
  interface contracts were the fixed starting point and requirements were derived from them.

**How we ran them.** We executed tasks one at a time from `tasks.md` using Kiro''s task execution, rather than
"run all," so we could verify each acceptance check before moving on. Kiro tracks each task''s execution
history and chat session in `tasks.meta.json`.

**Where the spec approach paid off:**

- **Acceptance checks caught problems early.** Every module had to reproduce reference numbers before its task
  was marked done: 67.8% unique on 8 fields, a 68.5% attack success rate, 2.50% of records removed with
  small-group protection, an R2 of 0.42 -> 0.37. When those numbers matched, we knew the module was right.
- **Contracts made modules swappable.** Role B''s optimizer depends on Role A''s risk functions, which weren''t
  ready yet. Kiro built a temporary stand-in strictly from the contract in the spec. When Role A''s real module
  arrived, the optimizer produced the identical result (2.503% removed), confirming both sides followed the
  same contract.
- **Merges had zero code conflicts.** Because each spec owned specific files, merging three branches into
  `main` produced no conflicts in any module.
- **The specs are durable project documentation.** When a teammate''s commit accidentally deleted part of the
  `.kiro/specs/` folder, we restored it from Git history, and the specs and task status came back intact.

**How it compared to vibe coding.** We used Kiro''s chat ("vibe" mode) for work that was exploratory or
one-off, where writing a spec first would have slowed us down: tuning the PII detector, writing a 20-sentence
out-of-sample stress test, diagnosing a data comparison that falsely reported differences (it compared
missing values as unequal), fixing chart code for a newer pandas version, and Git troubleshooting. Our rule of
thumb: **specs for anything another role depends on, chat for experiments and fixes.** The spec work was
slower to start but almost never had to be redone; chat was fast but needed more checking.

## 4. Steering docs

Three steering files in `.kiro/steering/` gave every Kiro session the same standing context:

- **`product.md`**: the pitch, the end-to-end flow, the deadlines, and the judging priorities.
- **`structure.md`**: the repo layout and which role owns each file.
- **`tech.md`**: the stack, the data conventions (`row_id` is never exported, `-9` is a real category,
  group-bys keep missing values), and the safety rules.

**What made the biggest difference:** putting **file ownership** and **safety rules** in steering rather than
repeating them in prompts. Concrete effects we saw:

- Kiro **stayed in its lane**. When Role B''s Kiro found work that touched Role A''s files, it reported the issue
  instead of editing them, and when it checked Role A''s code against the contracts, it listed mismatches
  rather than "fixing" another role''s module.
- Kiro **flagged ownership drift**. Role C''s Kiro noted that a diagnostic script it had created wasn''t on the
  steering ownership list.
- Kiro **enforced the privacy rules** consistently: it staged files by name, verified that nothing from
  `data/`, `keys/`, or `.env` was ever committed, and kept the LLM limited to column metadata, which matches
  the steering rule "never send row-level student data to an LLM."

## 5. Agent hooks

We created a **Privacy guard** hook (`.kiro/hooks/`). When a Python file in `reid/` or `app.py` is saved, it
runs the release-warning tests and the property-based tests, and checks that nothing from `data/`, `keys/`, or
`.env` is staged in Git, then reports any failure.

This automates the two checks we were doing by hand all day: "did this change break a privacy guarantee?" and
"am I about to commit something sensitive?" We added it late in the build, so it guarded the final round of
fixes; in a longer project we''d create it on day one.

## 6. Property-based testing

`tests/test_properties.py` uses the Hypothesis library to check properties across many generated inputs,
implementing four optional property tasks from the Role B spec:

| Spec task | Property checked |
|---|---|
| 3.2 | Tokens are deterministic, and tokenize -> detokenize always returns the original value |
| 2.5 | After mitigation, every group of matching records has at least k members (the core k-anonymity guarantee) |
| 2.4 | When a major code is generalized, its derived columns are always dropped with it (no detail leaks back) |
| 1.2 | Every planted identifier sits at exactly the character position recorded in the ground truth |

These complement our acceptance checks, which only test the BU dataset. The properties test the guarantees
themselves on many random small datasets, including edge cases a single real dataset might never contain.
The remaining optional unit-test tasks in the spec are still open.

## 7. MCP

We did not use MCP servers. Our data was local and access-restricted, so we deliberately kept the build
offline. Next steps where MCP would help: a GitHub MCP server to manage the many pull requests between three
branches, and a documentation server for library references (Presidio, Streamlit).

## 8. Kiro powers

We did not use Kiro powers.

## 9. What we learned

- **Contracts first, then specs.** Writing the interfaces down before anyone coded was the single best
  decision. Kiro''s specs turned those contracts into tasks with checks, and the checks kept everyone honest.
- **Steering is cheap and high-leverage.** Three short files prevented whole categories of mistakes across
  three separate Kiro sessions.
- **Use hooks from the start.** We added the Privacy guard hook late; it would have saved repeated manual
  checks if we''d created it in the first hour.
- **Keep specs truthful.** Several task checkboxes lagged behind finished work during the day. Updating
  `tasks.md` as we went would have made the specs a more accurate record.
