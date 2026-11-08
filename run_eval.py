"""Run every test case end-to-end and save RAW, UNEDITED outputs to outputs/.
Usage: python run_eval.py   (needs a real LLM key in .env)
No scoring is done here on purpose — a human reads and grades with RUBRIC.md.
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from core import agent

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)  # .env next to this file wins
ROOT = Path(__file__).parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


def run_case(case: dict) -> dict:
    lang, history, log = case["lang"], [], {"triage": []}
    for turn in case["turns"]:
        history.append({"role": "user", "content": turn})
        log["triage"].append(agent.triage(turn))
        history.append({"role": "assistant", "content": agent.intake_reply(history, lang)})
    facts = agent.extract_facts(history)  # NOTE: auto-accepted here; in the app the user confirms
    options, opt_flags = agent.explain_options(facts, lang)
    draft, draft_flags = agent.draft_document(facts, lang)
    # one practice turn so role-play output is also inspectable
    practice = agent.practice_reply(
        [{"role": "user", "content": "I want my money back. Please pay within 15 days."}], facts, lang)
    log.update(conversation=history, facts=facts, options=options,
               options_citation_flags=opt_flags, draft=draft,
               draft_citation_flags=draft_flags, practice_sample=practice)
    return log


def main():
    cases = json.loads((ROOT / "tests" / "test_cases.json").read_text(encoding="utf-8"))
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    meta = {"run": stamp, "provider": __import__("core.llm", fromlist=["x"]).pick_provider(), "model": os.getenv("LLM_MODEL", "default")}
    for c in cases:
        print("running", c["id"], "...", flush=True)
        try:
            result = run_case(c)
        except Exception as e:  # keep going; the error itself is a result
            result = {"error": repr(e)}
        record = {"meta": meta, "case": c, "result": result}
        (OUT / f"{stamp}_{c['id']}.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        time.sleep(4)  # stay under free-tier rate limits
    print(f"Done. Raw outputs in {OUT}/ (prefix {stamp}). Now read them and fill RUBRIC.md.")


if __name__ == "__main__":
    main()
