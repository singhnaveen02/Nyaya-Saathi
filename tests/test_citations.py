"""Unit tests for the deterministic parts (no API key needed). Run: python -m pytest -q"""
from core.agent import triage
from core.citations import check_citations
from core.drafts import make_draft


def test_kb_sections_pass():
    txt = "Under Section 69 of the Consumer Protection Act, 2019 you have 2 years. Code on Wages, 2019 Section 17 applies."
    assert check_citations(txt) == []


def test_fake_section_flagged():
    assert check_citations("Section 420 of the Consumer Protection Act, 2019 gives triple refund.")


def test_unknown_act_flagged():
    assert check_citations("As per the Tenant Deposit Protection Act, 2022 you get interest.")


def test_case_law_flagged():
    assert check_citations("In Sharma v. Gupta (2019) 5 SCC 123 the court held...")


def test_triage_no_false_hits():
    t = triage("My landlord did not return the deposit, first I asked politely. Will I win?")
    assert not t["urgent"] and not t["out_of_scope"]


def test_triage_threat():
    assert triage("Malik ne dhamki di ki police bulayega")["urgent"]


def test_draft_placeholders_not_invented():
    d = make_draft({"category": "salary", "user_name": None, "amount_claimed": None, "key_dates": []})
    assert "[YOUR FULL NAME]" in d and "[AMOUNT IN RS]" in d


def test_mixed_valid_citations_no_false_flags():
    txt = ("Under the Consumer Protection Act, 2019 (Section 2(10)) and the Model Tenancy Act, 2021 "
           "Section 11, plus Order XXXVII of the Code of Civil Procedure, 1908.")
    assert check_citations(txt) == []


def test_repealed_act_flagged():
    assert any("Payment of Wages Act" in f for f in check_citations("under the Payment of Wages Act, 1936"))
