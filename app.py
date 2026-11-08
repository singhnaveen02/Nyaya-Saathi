"""Nyay Saathi — Streamlit UI. Run: streamlit run app.py"""
import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from core import agent
from core.prompts import LEGAL_AID

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)  # .env next to this file wins
st.set_page_config(page_title="Nyay Saathi — AI legal helper", page_icon="⚖️", layout="wide")

ss = st.session_state
for k, v in {"chat": [], "facts": None, "confirmed": False, "options": None,
             "draft": None, "practice": [], "flags": []}.items():
    ss.setdefault(k, v)

# ---------- Sidebar: language + case summary panel ----------
with st.sidebar:
    lang = st.radio("Language / भाषा", ["English", "Hindi"], horizontal=True)
    st.caption("Hinglish typing is fine. Covers: deposit not returned · defective product/refund · unpaid salary.")
    st.divider()
    st.subheader("📋 Case summary")
    if ss.facts is None:
        st.info("Tell your story in the chat, then press **Build case summary**.")
    else:
        edited = st.text_area("Check and correct the facts (JSON)",
                              json.dumps(ss.facts, indent=2, ensure_ascii=False), height=380)
        if st.button("✅ Facts are correct", type="primary", use_container_width=True):
            try:
                ss.facts, ss.confirmed = json.loads(edited), True
                ss.options = ss.draft = None
            except json.JSONDecodeError:
                st.error("That is not valid JSON — fix the edit and try again.")
        if ss.confirmed:
            st.success("Confirmed")
    st.divider()
    st.caption("⚠️ Legal information, not legal advice. " + LEGAL_AID)
    if st.button("Start over"):
        ss.clear()
        st.rerun()

st.title("⚖️ Nyay Saathi")
st.caption("AI legal helper for three everyday problems in India. Not a lawyer.")

tab_chat, tab_opts, tab_draft, tab_practice = st.tabs(
    ["1 · Tell your story", "2 · Your options", "3 · Draft notice", "4 · Practice (optional)"])

# ---------- 1. Intake ----------
with tab_chat:
    alerts = ss.setdefault("alerts", set())
    if "urgent" in alerts:
        st.error("🚨 This may involve threats/violence or police. Please contact a lawyer, or "
                 "call 112 if you are in danger. Free legal aid: 15100.")
    if "refer" in alerts:
        st.warning("This may be outside my scope or a high-value matter — a real lawyer is recommended. " + LEGAL_AID)
    for m in ss.chat:
        st.chat_message(m["role"]).write(m["content"])
    if user := st.chat_input("What happened? / क्या हुआ?"):
        ss.chat.append({"role": "user", "content": user})
        t = agent.triage(user)
        if t["urgent"]:
            alerts.add("urgent")
        if t["out_of_scope"] or t["high_value"]:
            alerts.add("refer")
        with st.spinner("Thinking…"):
            try:
                reply = agent.intake_reply(ss.chat, lang)
            except Exception as e:  # show provider errors instead of crashing
                reply = f"(Model error: {e})"
        ss.chat.append({"role": "assistant", "content": reply})
        st.rerun()
    if ss.chat and st.button("📋 Build case summary"):
        with st.spinner("Extracting facts…"):
            ss.facts, ss.confirmed = agent.extract_facts(ss.chat), False
        st.rerun()

# ---------- 2. Options ----------
with tab_opts:
    if not ss.confirmed:
        st.info("Confirm the case summary in the sidebar first.")
    else:
        if st.button("Explain my position and options"):
            with st.spinner("Checking the law I'm allowed to cite…"):
                ss.options, ss.flags = agent.explain_options(ss.facts, lang)
        if ss.options:
            if ss.flags:
                st.error("⚠️ Citation check: the text below mentions law that is NOT in my verified list. "
                         "Treat these as unverified:\n\n- " + "\n- ".join(ss.flags))
            st.markdown(ss.options)

# ---------- 3. Draft ----------
with tab_draft:
    if not ss.confirmed:
        st.info("Confirm the case summary in the sidebar first.")
    else:
        if st.button("Generate draft notice"):
            with st.spinner("Filling the template…"):
                ss.draft, dflags = agent.draft_document(ss.facts, lang)
                if dflags:
                    st.error("Citation check flags: " + "; ".join(dflags))
        if ss.draft:
            st.caption("Everything in [SQUARE BRACKETS] is unknown — fill it yourself. Nothing was guessed.")
            st.text_area("Draft (editable)", ss.draft, height=520)
            st.download_button("⬇️ Download .txt", ss.draft, file_name="draft_notice.txt")

# ---------- 4. Practice ----------
with tab_practice:
    if not ss.confirmed:
        st.info("Confirm the case summary first; then practise talking to the other side.")
    else:
        st.caption("I'll play the other side. Try to stay calm and refer to your proof.")
        for m in ss.practice:
            st.chat_message(m["role"]).write(m["content"])
        if msg := st.chat_input("Say what you'd say to them…", key="practice_in"):
            ss.practice.append({"role": "user", "content": msg})
            with st.spinner("…"):
                ss.practice.append({"role": "assistant",
                                    "content": agent.practice_reply(ss.practice, ss.facts, lang)})
            st.rerun()
