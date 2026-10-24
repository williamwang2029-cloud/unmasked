# Product: Unmasked, Re-identification Risk Meter

Hackathon project (BU Spark! DS+X × Hackachusetts 2026, CollegeHack, BU IS&T "Data Scrubbing / Tokenization Tool").

Pitch: the synthetic NSSE survey file has no names, yet on eight ordinary fields 68% of students can be singled out.
Our privacy agent finds the risk, fixes it, and shows what the fix costs, including which student groups pay most.

Flow: load data + planted fake PII -> AI agent labels column roles (metadata only) -> measure risk
(k-anonymity, % unique, riskiest combos, metadata leaks, attacker personas, linkage attack, risk by group) ->
mitigate (tokenize IDs, scrub text, generalize + suppress to target k) -> verify, measure utility and fairness ->
plain-English report + release privacy summary + safe download.

Deadlines: Hackachusetts (Sundai: repo + video, Kiro required) Sat 8:00 PM; DS+X Devpost Sun 11:00 AM.
Judging stresses AI integration, responsible innovation, Kiro use. DS+X: data science must stand without the LLM.

Not a FERPA compliance certificate; a human data steward approves every release.
