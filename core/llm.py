"""ONE function to call any LLM. Swap provider/model with env vars only.

LLM_PROVIDER = gemini | groq | ollama | openai_compat | mock
LLM_MODEL    = model name for that provider
Decision: plain HTTP via `requests` (no vendor SDKs) so swapping costs nothing.
"""
import os
import requests

DEFAULT_MODELS = {
    "gemini": "gemini-3.5-flash",          # or gemini-3.6-flash
    "groq": "llama-3.3-70b-versatile",     # verify on console.groq.com/docs/models
    "ollama": "qwen2.5:7b",                # any model you have pulled: `ollama list`
    "openai_compat": "gpt-4o-mini",
}


KEY_FOR = {"gemini": "GEMINI_API_KEY", "groq": "GROQ_API_KEY", "openai_compat": "OPENAI_API_KEY"}


def pick_provider() -> str:
    """Use LLM_PROVIDER if set; otherwise auto-pick whichever API key is present."""
    p = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    if not p:
        p = "groq" if os.getenv("GROQ_API_KEY") else "gemini" if os.getenv("GEMINI_API_KEY") else "mock"
    key = KEY_FOR.get(p)
    if key and not os.getenv(key):
        raise RuntimeError(
            f"LLM_PROVIDER is '{p}' but {key} is empty. Either add {key}, or set LLM_PROVIDER "
            f"to the provider whose key you have (e.g. LLM_PROVIDER=groq with GROQ_API_KEY).")
    return p


def _need(name: str, provider: str) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        raise RuntimeError(
            f"{name} is not set (LLM_PROVIDER='{provider}'). Put it in the .env file next to app.py, "
            f"or in Hugging Face Settings -> Variables and secrets. If you meant another provider, set LLM_PROVIDER.")
    return val


def call_llm(system: str, messages: list[dict], temperature: float = 0.2) -> str:
    """messages: [{"role": "user"|"assistant", "content": str}, ...]. Returns text."""
    provider = pick_provider()
    model = os.getenv("LLM_MODEL") or DEFAULT_MODELS.get(provider, "")

    if provider == "mock":  # offline smoke tests, no API key
        return "[MOCK] " + messages[-1]["content"][:200]

    if provider == "gemini":
        key = _need("GEMINI_API_KEY", provider)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        body = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [
                {"role": "model" if m["role"] == "assistant" else "user",
                 "parts": [{"text": m["content"]}]}
                for m in messages
            ],
            "generationConfig": {"temperature": temperature},
        }
        r = requests.post(url, params={"key": key}, json=body, timeout=90)
        r.raise_for_status()
        cands = r.json().get("candidates", [])
        if not cands:
            return "(The model returned no answer — possibly blocked by its safety filter.)"
        return "".join(p.get("text", "") for p in cands[0]["content"]["parts"])

    # groq and any OpenAI-compatible endpoint share one code path
    if provider == "groq":
        base, key = "https://api.groq.com/openai/v1", _need("GROQ_API_KEY", provider)
    elif provider == "ollama":  # local, free, no key; Ollama speaks the OpenAI API
        base, key = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"), "ollama"
    elif provider == "openai_compat":
        base, key = _need("OPENAI_BASE_URL", provider), _need("OPENAI_API_KEY", provider)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")

    r = requests.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model, "temperature": temperature,
              "messages": [{"role": "system", "content": system}] + messages},
        timeout=300 if provider == "ollama" else 90,  # local CPU models are slow
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
