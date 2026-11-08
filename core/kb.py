"""Load the curated knowledge base and format it for prompts."""
import json
from pathlib import Path

KB_PATH = Path(__file__).resolve().parent.parent / "kb" / "laws.json"


def load_kb() -> list[dict]:
    return json.loads(KB_PATH.read_text(encoding="utf-8"))["entries"]


def entries_for(category: str) -> list[dict]:
    return [e for e in load_kb() if e["area"] in (category, "all")]


def kb_block(category: str) -> str:
    """Text block injected into the prompt. Only these may be cited."""
    lines = []
    for e in entries_for(category):
        sec = f" Section {e['section']}" if e["section"] and not e["section"].startswith("Order") else (f" {e['section']}" if e["section"] else "")
        lines.append(f"[{e['id']}] {e['statute']}{sec} — {e['title']}: {e['plain_en']} (source: {e['source_url']})")
    return "\n".join(lines)
