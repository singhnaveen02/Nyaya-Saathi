"""Pipeline functions used by both the Streamlit app and the eval script."""
import json
import re

from . import prompts
from .citations import check_citations
from .drafts import make_draft
from .kb import kb_block
from .llm import call_llm

# Rule-based triage (code, not AI): cheap, predictable, runs on every user message.
URGENT_WORDS = [
    "threat", "kill", "maar", "maarne", "jaan se", "beat", "hit me", "assault", "police", "fir",
    "arrest", "rape", "dhamki", "धमकी", "मार", "पुलिस", "goonda", "weapon", "suicide",
    "forcefully", "lock me", "thrown out", "zabardasti",
]
OUT_OF_SCOPE_WORDS = [
    "property dispute", "land", "zameen", "जमीन", "partition", "divorce", "talaq", "custody",
    "dowry", "dahej", "cheque bounce", "bail", "murder", "inheritance", "builder", "rera",
]


def _hits(words, t):
    # word boundaries for Latin words (so "land" != "landlord", "fir" != "first");
    # plain substring for Devanagari, where \b is unreliable
    return [w for w in words
            if (re.search(r"\b" + re.escape(w.strip()) + r"\b", t) if w.isascii() else w in t)]


def triage(text: str) -> dict:
    t = text.lower()
    urgent = _hits(URGENT_WORDS, t)
    oos = _hits(OUT_OF_SCOPE_WORDS, t)
    big = bool(re.search(r"(\d+(\.\d+)?)\s*(crore|cr\b|करोड़)", t))
    return {"urgent": urgent, "out_of_scope": oos, "high_value": big}


def _sys(base: str, lang: str) -> str:
    return base + "\n" + prompts.LANG_RULE[lang]


def intake_reply(history: list[dict], lang: str) -> str:
    return call_llm(_sys(prompts.INTAKE, lang), history)


def extract_facts(history: list[dict]) -> dict:
    convo = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in history)
    raw = call_llm(prompts.EXTRACT, [{"role": "user", "content": convo}], temperature=0)
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        return json.loads(m.group()) if m else {"category": "out_of_scope", "summary": raw}
    except json.JSONDecodeError:
        return {"category": "out_of_scope", "summary": "Could not parse facts. Raw: " + raw[:500]}


def explain_options(facts: dict, lang: str) -> tuple[str, list[str]]:
    cat = facts.get("category", "out_of_scope")
    if cat == "out_of_scope":
        msg = ("This problem is outside the three areas I can help with (deposit, consumer refund, unpaid salary). "
               + prompts.LEGAL_AID)
        return msg, []
    system = _sys(prompts.OPTIONS.format(kb=kb_block(cat), facts=json.dumps(facts, ensure_ascii=False)), lang)
    text = call_llm(system, [{"role": "user", "content": "Explain my position and options."}])
    return text, check_citations(text)


def draft_document(facts: dict, lang: str) -> tuple[str, list[str]]:
    text = make_draft(facts)
    if lang == "Hindi" and facts.get("category") in ("deposit", "consumer", "salary"):
        text = call_llm(prompts.TRANSLATE, [{"role": "user", "content": text}], temperature=0)
    return text, check_citations(text)


ROLES = {"deposit": "the landlord", "consumer": "the seller's customer-care manager",
         "salary": "the employer / HR manager"}


def practice_reply(history: list[dict], facts: dict, lang: str) -> str:
    role = ROLES.get(facts.get("category"), "the other party")
    system = _sys(prompts.PRACTICE.format(role=role, facts=json.dumps(facts, ensure_ascii=False)), lang)
    return call_llm(system, history, temperature=0.6)
