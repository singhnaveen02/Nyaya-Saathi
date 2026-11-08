# Nyay Saathi — AI legal helper for ordinary people in India
*Kuku "AI Generalist" assignment · [YOUR NAME] · [DATE] · Demo: [HF SPACE URL] · Code: [REPO URL]*

## 1. Problem choice and why
People with small, everyday legal problems rarely see a lawyer: the fee is often larger than the amount at stake. I picked three problems that are (a) very common, (b) mostly about money owed, and (c) usually solvable with a well-written demand letter before any court: **security deposit not returned, defective product / refund, unpaid salary.** Narrow scope lets me hand-curate every law the bot may cite, which is the only way I could make "no invented sections" a hard guarantee rather than a hope. English + Hindi (Hinglish input) covers most users I could test with.
Deliberate exclusions: criminal matters, threats, property/land, family law — these need a human lawyer quickly and an error is costly.

## 2. Assumptions
- Users are adults in India with a phone/browser; dispute value well under ₹50 lakh.
- Information, not advice: the bot never represents the user and says so.
- Law as of 7 Nov 2026: the four Labour Codes are in force from 21 Nov 2025 (Payment of Wages Act repealed); e-Daakhil was merged into e-Jagriti; NALSA helpline 15100 and National Consumer Helpline 1915 are active. [CONFIRM ON OFFICIAL SITES BEFORE SUBMITTING]
- Deposit rules depend on state law; the Model Tenancy Act 2021 is treated as a model only.
- Free-tier LLM (Gemini Flash by default) is good enough for Hindi; swappable by env var.
- [ADD ANY ASSUMPTION YOU CHANGED]

## 3. How it works
Flow: **story (chat) → case summary the user edits and confirms → options → draft notice → optional role-play practice.**

| Step | AI (LLM) does | Code / rules do | Human does |
|---|---|---|---|
| Intake | asks the next 1–2 questions, empathetic tone, understands Hinglish | keyword triage on every message → red banner for threats/police/out-of-scope/high value | tells the story |
| Case summary | extracts facts into JSON (null if unknown) | renders editable panel; nothing proceeds until confirmed | **corrects and confirms facts** |
| Options | explains position + options in plain language | injects only the KB entries for that category; regex checker flags any section/Act/case not in KB | decides what to do |
| Draft | only translates to Hindi (if chosen) | fixed template fills confirmed facts; unknowns become `[PLACEHOLDER]` | fills blanks, gets it checked, sends |
| Practice | plays landlord/employer/seller + one coaching tip per turn | — | practises |
| Escalation | states when a lawyer is needed | always shows NALSA 15100 / DLSA, NCH 1915 | lawyer / legal-aid volunteer for flagged cases |

Anti-hallucination: (1) curated `kb/laws.json` (statute, section, plain meaning, source URL, verification status); (2) prompt forbids anything else and prescribes "I'm not sure; verify with a lawyer or legal aid"; (3) deterministic post-check flags unknown sections, unknown Acts (e.g. the repealed Payment of Wages Act) and any case-law pattern; (4) the legal document itself is a template, so the model cannot put invented law or facts into it.

## 4. Scale and cost
- **More languages:** prompts are language-parameterised; add a `LANG_RULE` entry + translated template. Main cost is human review of legal wording per language, not engineering. Voice: add speech-to-text (e.g. an Indic ASR model) in front of the same pipeline.
- **More legal areas:** each area = KB entries + a template + test cases + a lawyer's sign-off. KB grows as a reviewed file, not by letting the model "know" more law. Beyond ~50 entries, switch from "inject all entries for the category" to retrieval over the KB.
- **Lawyer review queue:** triage-flagged cases and every draft the user marks "send" go to a queue (simple DB + dashboard); legal-aid volunteers/paralegals approve or edit. Priority = urgent flag > deadline near > amount.
- **Cost per conversation (estimate, not measured):** ~[N] LLM calls (≈6 intake turns + extract + options + optional translate + practice) × ~[X]k input + ~[Y]k output tokens each. Cost = tokens × provider price from its pricing page on [DATE]: ≈ ₹[___] per conversation; ₹0 on free tier within rate limits. [REPLACE WITH NUMBERS FROM YOUR OWN RUN — count tokens from the API responses]

## 5. Quality checking and honest failures
- **Automated (deterministic):** `pytest` — 9 tests on citation checker, triage and templates. [PASTE RESULT]
- **Model behaviour:** 10 scenario cases (clean, vague/emotional, Hinglish, missing proof, 2 out-of-scope, fake-section trap, repealed-law trap, "will I win?"). Raw outputs saved unedited in `outputs/`; graded by me with `RUBRIC.md`.
- **Results:** [INSERT YOUR FILLED RESULTS TABLE / SUMMARY: e.g. "A: _/10, B: _/10 …"]
- **Real failures I saw:** [INSERT 2–3 ACTUAL FAILURES WITH QUOTED OUTPUT LINES AND CASE IDs]
- **Known limits by design:** checker catches unknown *numbers*, not a correct section explained *wrongly*; keyword triage misses indirect threats and can over-fire; deposit advice is generic because state laws differ; one run per case, and LLM output varies.

## 6. Tools used and one place they got it wrong
Tools: Python, Streamlit, Gemini/Groq API, Claude (for scaffolding code, drafting docs and web-checking legal facts), web sources listed in `kb/laws.json`.
Where the AI tooling got it wrong (observed while building; all fixed and covered by tests):
1. The first triage used substring matching, so "landlord" matched "land" (out-of-scope) and "first" matched "fir" (urgent) — it would have wrongly told tenants their case was a property dispute.
2. The first citation checker linked a section to the first Act name in the window, not the nearest, so valid text ("Consumer Protection Act, 2019 (Section 2(10)) and the Model Tenancy Act…") was falsely flagged.
3. The first draft template was headed "WITHOUT PREJUDICE" — wrong for a demand notice the user may later rely on as evidence.
[ADD ONE FAILURE YOU FOUND YOURSELF IN THE MODEL'S LIVE OUTPUTS — this is the most valuable line in the doc]
