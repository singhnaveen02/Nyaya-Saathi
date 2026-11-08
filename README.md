---
title: Nyay Saathi
emoji: ⚖️
sdk: docker
app_port: 8501
pinned: false
---

# Nyay Saathi — AI legal helper (deposit · consumer refund · unpaid salary)

Prototype for the Kuku "AI Generalist" assignment. English + Hindi (Hinglish input OK).
Legal information only — not legal advice.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # put your GEMINI_API_KEY (or set LLM_PROVIDER=groq + GROQ_API_KEY)
streamlit run app.py
```
No key? `LLM_PROVIDER=mock streamlit run app.py` runs the UI with echo replies.

## Deploy free on Hugging Face Spaces (Docker SDK)
HF has deprecated the built-in Streamlit SDK, so this repo ships a `Dockerfile`.
1. huggingface.co -> New Space -> SDK **Docker** -> Blank (CPU basic, free).
2. Upload all files keeping the folders (`core/`, `kb/`, `tests/`), including `Dockerfile` and this `README.md` (its YAML header sets `sdk: docker`, `app_port: 8501`).
3. Settings -> **Variables and secrets**: add a secret `GROQ_API_KEY` (or `GEMINI_API_KEY`). Optional variable `LLM_PROVIDER` must match the key you added. Never upload `.env`.
4. The Space builds automatically; check the **Logs** tab if it fails.

## Tests and evaluation
```bash
python -m pytest -q tests          # deterministic checks (citation checker, triage, drafts) — no key needed
python run_eval.py                 # runs tests/test_cases.json through the real model, saves raw outputs to outputs/
```
Then read `outputs/` and filled in `RUBRIC.md` myself.

## Files
| File | What it is |
|---|---|
| `app.py` | Streamlit UI: intake chat, case-summary panel, options, draft, practice |
| `core/llm.py` | `call_llm()` — the only place a model is called; provider via env var |
| `core/prompts.py` | system prompts and rules |
| `kb/laws.json` | curated law list — the ONLY law the bot may cite |
| `core/citations.py` | post-check that flags any section/Act/case not in the KB |
| `core/drafts.py` | deterministic notice templates with `[PLACEHOLDERS]` |
| `core/agent.py` | triage rules + pipeline functions (shared by app and eval) |
| `Dockerfile` | container for HF Spaces |
| `DESIGN.md` | design |
| `SOLUTION_DOC.md` | page doc |

## Key decisions
- **Templates write the notice, not the LLM** → no invented facts or sections in the document.
- **Regex citation checker, not an LLM judge** → deterministic and cannot hallucinate itself.
- **Keyword triage in code** → urgent/out-of-scope warnings appear even if the model misbehaves.
- **No vendor SDKs** → switching Gemini ↔ Groq is one env var.
