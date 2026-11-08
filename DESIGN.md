# STEP 1 — Design: "Nyay Saathi" (AI legal helper for 3 everyday problems)

## Scope (and one challenge to it)
In scope: (1) landlord not returning security deposit, (2) consumer refund / defective product, (3) unpaid salary. English + Hindi (Hinglish input OK). Everything else → polite "out of scope" + legal aid pointer.

**Challenge:** deposit disputes are the weakest of the three for an AI because the remedy depends on *state* rent law (the Model Tenancy Act 2021 is only a model; it binds only where a state adopted it). The bot therefore treats deposit cases as "notice + civil/Lok Adalat route, check your state's rent law" and never asserts a state-specific rule. If you want a stronger demo, consumer + salary are the safest two; I kept deposit because it is the most common real problem.

## Conversation flow
```
1. INTAKE (chat)   bot asks 1–2 questions at a time: what happened, who, when,
                   how much, what proof (agreement, receipts, chats, bank stmt).
                   Rule-based triage runs on every user message (urgent/criminal/
                   out-of-scope keywords) and shows a red banner if hit.
2. FACT SUMMARY    LLM extracts JSON {category, parties, dates, amounts, proof,
                   missing}. Shown in an editable side panel. User must click
                   "Facts are correct" before anything else unlocks.
3. OPTIONS         LLM explains position + options in plain language, given ONLY
                   the KB entries for that category. Citation checker runs.
4. DRAFT           Python template (not the LLM) fills the notice/complaint from
                   confirmed facts; every unknown field becomes [PLACEHOLDER].
                   LLM is used only to translate to Hindi if chosen.
5. PRACTICE (opt.) LLM role-plays landlord / employer / seller; gives a 1-line
                   coaching tip after each turn.
```

## Anti-hallucination strategy
1. **Curated KB** `kb/laws.json`: every entry = statute, section, plain meaning, source URL, `verify_status`. The prompt injects only entries for the case's category.
2. **Prompt rule:** "Cite ONLY entry IDs/sections given below. For anything else say: *I'm not sure; verify with a lawyer or legal aid (NALSA 15100).* Never name a court case."
3. **Post-check (code, `core/citations.py`):** regex finds `Section/धारा/s./Order/Article` + number, Act names (`... Act, 2019`), and case-law patterns (`X v. Y`, `AIR 19xx`, `SCC`). Anything not in the KB is flagged in the UI with a warning and logged in eval outputs. It does not silently delete — the user sees the flag.
4. **Drafts are templates**, so the LLM cannot invent facts or sections in the document itself.

## Safety rules
- Never promise an outcome ("will I win?" → explain what strengthens/weakens the case, no %).
- Rule-based escalation banner for: threats/violence/police/FIR/arrest, criminal words, property title disputes, family matters, amounts > ₹50 lakh (beyond District Consumer Commission limit), limitation possibly expired (>2 yrs consumer / >3 yrs wage claim).
- Every options/draft screen ends with: free legal aid via NALSA/DLSA, toll-free **15100** (verified 2026-11-07 on nalsa.gov.in and DoT short-code allocation); consumer pre-litigation: **National Consumer Helpline 1915** (Dept of Consumer Affairs, Lok Sabha reply 2024).
- No personal data stored server-side; session only.

## What could be wrong in Step 1 / what you should check
- Keyword triage will miss cleverly-worded urgent cases and over-flag some ("threat to complain to police" ≠ criminal). Read eval outputs for both.
- "Wages claim limit = 3 years" and "District Commission ≤ ₹50 lakh" come from secondary sources — confirm on India Code / gazette.
- The Model Tenancy Act framing: confirm whether your target state (e.g. Uttarakhand/UP/MP) adopted a version.
- The regex checker catches *numbers*, not *wrong meaning* — a correct section explained wrongly passes. Human reading is still needed.
