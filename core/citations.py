"""Post-check: flag any legal citation in model output that is not in the KB.

Decision: regex, not an LLM — deterministic, cheap, and cannot itself hallucinate.
It catches unknown section numbers / Acts / case-law patterns, NOT wrong meanings.
"""
import re
from .kb import load_kb

# Short names the model may use for each KB statute
ALIASES = {
    "Consumer Protection Act": ["consumer protection act", "cpa", "उपभोक्ता संरक्षण"],
    "Code on Wages": ["code on wages", "wage code", "मजदूरी संहिता", "वेतन संहिता"],
    "Model Tenancy Act": ["model tenancy act", "मॉडल किरायेदारी"],
    "Indian Contract Act": ["indian contract act", "contract act", "संविदा अधिनियम"],
    "Code of Civil Procedure": ["code of civil procedure", "cpc", "सिविल प्रक्रिया"],
    "Legal Services Authorities Act": ["legal services authorities act", "विधिक सेवा"],
}

SECTION_RE = re.compile(
    r"(?:section|sec\.|s\.|धारा)\s*(\d+[A-Z]?)(?:\s*\(\s*\w+\s*\))*", re.IGNORECASE)
ORDER_RE = re.compile(r"\border\s+([IVXLC]+|\d+)\b", re.IGNORECASE)
ARTICLE_RE = re.compile(r"\barticle\s+(\d+[A-Z]?)", re.IGNORECASE)
ACT_RE = re.compile(
    r"\b([A-Z][a-z]+(?:\s+(?:[A-Z][a-z]+|of|on|and|the|for|to))*\s+(?:Act|Code|Sanhita|Adhiniyam)),?\s*(\d{4})")
CASE_RES = [
    re.compile(r"\b[A-Z][\w.&]+(?:\s+[A-Z][\w.&]+)*\s+(?:v\.|vs\.?|versus)\s+[A-Z][\w.&]+"),
    re.compile(r"\bAIR\s+\d{4}\b"),
    re.compile(r"\(\d{4}\)\s*\d+\s*SCC\b"),
    re.compile(r"\b\d{4}\s+SCC\s+(?:OnLine\s+)?\w+"),
]


def _allowed():
    kb = load_kb()
    statutes = {e["statute"].split(",")[0].strip().lower() for e in kb}
    secs = {}  # canonical act -> set of base section numbers
    orders = set()
    for e in kb:
        act = e["statute"].split(",")[0].strip()
        s = e["section"]
        if s.lower().startswith("order"):
            orders.add(s.split()[-1].upper())
        elif s:
            secs.setdefault(act, set()).add(re.match(r"\d+", s).group())
    return statutes, secs, orders


def _act_near(text: str, idx: int, span: int = 70) -> str | None:
    """Return the Act whose name appears closest to position idx (either side)."""
    lo = max(0, idx - span)
    window = text[lo: idx + span].lower()
    best, best_dist = None, 10**9
    for act, names in ALIASES.items():
        for n in names:
            pat = r"\b" + re.escape(n) + r"\b" if n.isascii() else re.escape(n)
            for m in re.finditer(pat, window):
                s, e = lo + m.start(), lo + m.end()
                d = idx - e if e <= idx else s - idx  # gap between name and the section mention
                if d < best_dist:
                    best, best_dist = act, d
    return best


def check_citations(text: str) -> list[str]:
    """Return human-readable flags. Empty list = nothing suspicious found."""
    statutes, secs, orders = _allowed()
    all_secs = set().union(*secs.values()) if secs else set()
    flags = []

    for m in SECTION_RE.finditer(text):
        num = re.match(r"\d+", m.group(1)).group()
        act = _act_near(text, m.start())
        if act is not None:
            if num not in secs.get(act, set()):
                flags.append(f"Section {m.group(1)} of {act} is NOT in the knowledge base.")
        elif num not in all_secs:
            flags.append(f"'{m.group(0).strip()}' is NOT in the knowledge base (Act unclear).")

    for m in ORDER_RE.finditer(text):
        if m.group(1).upper() not in orders and _act_near(text, max(0, m.start() - 40)) == "Code of Civil Procedure":
            flags.append(f"'{m.group(0)}' is NOT in the knowledge base.")

    for m in ARTICLE_RE.finditer(text):
        flags.append(f"'{m.group(0)}' cited — no Articles are in the knowledge base.")

    for m in ACT_RE.finditer(text):
        name = m.group(1).strip().lower()
        if not any(s in name or name.endswith(s) for s in statutes):
            flags.append(f"Statute '{m.group(1).strip()}, {m.group(2)}' is NOT in the knowledge base.")

    for rx in CASE_RES:
        for m in rx.finditer(text):
            flags.append(f"Possible case-law citation '{m.group(0)}' — the knowledge base has NO cases.")

    return sorted(set(flags))
