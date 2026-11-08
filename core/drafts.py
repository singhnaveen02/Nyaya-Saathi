"""Deterministic draft templates. Decision: the LLM never writes the document body,
so it cannot invent facts or sections. Unknown -> [PLACEHOLDER] for the user to fill."""
from datetime import date


def _v(x, label):
    return x if x not in (None, "", []) else f"[{label}]"


def _dates(facts):
    rows = [f"   - {d.get('event')}: {_v(d.get('date'), 'DATE')}" for d in facts.get("key_dates") or []]
    return "\n".join(rows) or "   - [EVENT]: [DATE]"


def _proof(facts):
    items = facts.get("proof_available") or []
    return "\n".join(f"   - {p}" for p in items) or "   - [LIST YOUR DOCUMENTS: receipts / bank statement / chats]"


DEMAND = {
    "deposit": ("Refund of security deposit",
                "I was your tenant at [RENTED PROPERTY ADDRESS] under a rent agreement dated [AGREEMENT DATE]. "
                "I paid a security deposit of {amount}. I vacated and handed over possession on [HANDOVER DATE]. "
                "Despite this, the deposit has not been refunded."),
    "consumer": ("Refund / replacement for defective product or deficient service",
                 "I purchased [PRODUCT/SERVICE] from you on [PURCHASE DATE] (order/invoice no. [INVOICE NO.]) "
                 "for {amount}. The product/service is defective/deficient: {summary}"),
    "salary": ("Payment of unpaid wages",
               "I was employed with you as [DESIGNATION] from [JOINING DATE] to [LAST WORKING DAY / TILL DATE]. "
               "Wages of {amount} for the period [MONTHS UNPAID] remain unpaid."),
}

LAW_LINE = {
    "deposit": "This is a breach of the rent agreement. I reserve my right to approach the appropriate "
               "forum under the applicable law [CHECK WITH LAWYER: your state's rent law].",
    "consumer": "This amounts to a defect/deficiency under Section 2(10)/2(11) of the Consumer Protection "
                "Act, 2019, and I am entitled to approach the District Consumer Commission.",
    "salary": "Under Section 17 of the Code on Wages, 2019, wages are required to be paid within the time "
              "limits stated there. I am entitled to file a claim under Section 45 of the Code.",
}


def make_draft(facts: dict) -> str:
    cat = facts.get("category")
    if cat not in DEMAND:
        return "No draft: this matter is outside the three supported areas. Please contact NALSA 15100 / your DLSA."
    subject, body = DEMAND[cat]
    body = body.format(amount=_v(facts.get("amount_claimed"), "AMOUNT IN RS"),
                       summary=_v(facts.get("summary"), "DESCRIBE THE PROBLEM"))
    return f"""DEMAND LETTER / NOTICE
(Draft prepared with an AI tool. Have it checked by a lawyer or legal aid before sending.)

Date: {date.today().strftime('%d-%m-%Y')}

From: {_v(facts.get('user_name'), 'YOUR FULL NAME')}
      {_v(facts.get('user_address'), 'YOUR ADDRESS')}

To:   {_v(facts.get('other_party'), 'NAME OF LANDLORD / COMPANY / EMPLOYER')}
      {_v(facts.get('other_party_address'), 'THEIR ADDRESS')}

Subject: {subject}

1. {body}

2. Key dates:
{_dates(facts)}

3. Documents in my possession (copies available on request):
{_proof(facts)}

4. {LAW_LINE[cat]}

5. I request you to pay {_v(facts.get('amount_claimed'), 'AMOUNT IN RS')} to me within [15] days of
   receiving this letter, by bank transfer to [YOUR BANK DETAILS — share only with the recipient].

6. If this is not done, I will pursue the remedies available to me in law, without further notice,
   and will hold you responsible for costs.

Signed,
{_v(facts.get('user_name'), 'YOUR FULL NAME')}

Send by Registered Post / Speed Post with acknowledgement, and keep the receipt + a copy.
"""
