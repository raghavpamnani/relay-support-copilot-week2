import json
import os
from pathlib import Path

import requests
import streamlit as st

st.set_page_config(page_title="Relay | Support Copilot", page_icon="◈", layout="wide")
API = os.getenv("API_URL", "http://127.0.0.1:8000")
SAMPLES = json.loads((Path(__file__).resolve().parent.parent / "examples/tickets.json").read_text())
st.markdown(
    """<style>
.block-container {max-width:1220px;padding-top:2.5rem;}
h1 {letter-spacing:-1.7px;font-weight:750!important;}
[data-testid="stMetric"] {background:white;border:1px solid #e3e9ef;border-radius:14px;
padding:15px;}
[data-testid="stSidebar"] {border-right:1px solid #e3e9ef;}
.eyebrow {color:#0e766e;font-weight:700;letter-spacing:2px;font-size:12px;}
.hero-sub {color:#62738a;font-size:17px;max-width:700px;margin-bottom:28px;}
</style>""",
    unsafe_allow_html=True,
)


def api(method, path, **kwargs):
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    try:
        response = requests.request(method, API + path, headers=headers, timeout=105, **kwargs)
        if response.status_code == 401 and path != "/api/v1/auth/token":
            st.session_state.pop("token", None)
            st.session_state.pop("result", None)
            st.error("Session expired. Sign in again.")
            return None
        if not response.ok:
            try:
                detail = response.json().get("detail", "Request failed")
            except ValueError:
                detail = "Service returned an unexpected response."
            st.error(f"Request failed ({response.status_code}): {detail}")
            return None
        return response.json()
    except requests.RequestException:
        st.error("Cannot reach the API, or inference timed out. Check the service and retry.")
        return None


with st.sidebar:
    st.markdown("## ◈ Relay")
    st.caption("SUPPORT OPERATIONS")
    st.divider()
    st.markdown("**From incoming ticket\nto a considered response.**")
    st.caption("Local-first AI · Validated output · Human review")
    st.divider()
    st.caption("WEEK 02 / ENGINEERING DEMO")
    st.markdown("Python · FastAPI · Pydantic v2\n\nStreamlit · uv · Docker")
    st.caption("Synthetic examples only. No messages are sent to customers.")
    if st.session_state.get("token") and st.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.markdown('<div class="eyebrow">SUPPORT, WITH A HEAD START</div>', unsafe_allow_html=True)
st.title("Every ticket. A clearer next step.")
st.markdown(
    '<p class="hero-sub">Turn a customer issue into structured triage and a useful '
    "reply draft—with the execution details to back it up.</p>",
    unsafe_allow_html=True,
)

if not st.session_state.get("token"):
    left, right = st.columns([1, 1], gap="large")
    with left, st.container(border=True):
        st.subheader("Welcome to your support desk")
        st.caption("Sign in with the credentials you created during setup.")
        with st.form("login"):
            username = st.text_input("Username", value="reviewer")
            password = st.text_input("Password", type="password")
            if st.form_submit_button(
                "Open support desk →", type="primary", use_container_width=True
            ):
                data = api(
                    "POST", "/api/v1/auth/token", json={"username": username, "password": password}
                )
                if data:
                    st.session_state.token = data["access_token"]
                    st.rerun()
    with right:
        st.subheader("Built for a thoughtful handoff")
        st.markdown(
            "**01 · Understand**\n\nClassify the issue and identify its urgency.\n\n"
            "**02 · Prepare**\n\nDraft a response with clear next steps.\n\n"
            "**03 · Verify**\n\nInspect the model, timing, and validated JSON."
        )
    st.stop()

with st.expander("Provider status & usage limits"):
    if st.button("Check providers"):
        info = api("GET", "/api/v1/providers")
        if info:
            st.json(info)

left, right = st.columns([0.9, 1.25], gap="large")
with left, st.container(border=True):
    st.subheader("01 / Incoming ticket")
    sample = st.selectbox("Try a scenario", ["Write your own"] + [s["name"] for s in SAMPLES])
    selected = next((s for s in SAMPLES if s["name"] == sample), {})
    with st.form("ticket"):
        subject = st.text_input("Subject", value=selected.get("subject", ""), max_chars=200)
        description = st.text_area(
            "Customer message", value=selected.get("description", ""), height=210, max_chars=4000
        )
        mode = st.selectbox("Execution mode", ["Auto", "Local", "Cloud"])
        st.caption(
            "Auto prefers local. Cloud fallback requires server opt-in. "
            "Selecting Cloud sends this ticket to Groq."
        )
        submitted = st.form_submit_button(
            "Analyze ticket →", type="primary", use_container_width=True
        )
    if submitted:
        st.session_state.pop("result", None)
        if len(subject.strip()) < 5 or len(description.strip()) < 15:
            st.warning("Add a subject of at least 5 characters and a message of at least 15.")
        else:
            with st.spinner("Reading the ticket and preparing a validated draft…"):
                result = api(
                    "POST",
                    "/api/v1/tickets/triage",
                    json={"subject": subject, "description": description, "provider": mode.lower()},
                )
            if result:
                st.session_state.result = result
                st.session_state.analyzed_subject = subject

with right:
    st.subheader("02 / Agent workspace")
    result = st.session_state.get("result")
    if not result:
        with st.container(border=True):
            st.markdown("### A useful response starts here.")
            st.write("Choose a scenario or paste a ticket, then select **Analyze ticket**.")
            st.info("You’ll get a category, priority, suggested reply, and clear next steps.")
            st.caption("Results come from the selected model. There are no canned AI responses.")
    else:
        t, m = result["triage"], result["metadata"]
        st.caption("RESULT FOR: " + st.session_state.analyzed_subject)
        a, b, c = st.columns(3)
        a.metric("Category", t["category"].title())
        b.metric("Priority", t["priority"].title())
        c.metric("Inference", f"{m['latency_ms'] / 1000:.1f}s")
        if t["needs_human_review"]:
            st.warning("Human review required · Verify the facts before taking action.")
        else:
            st.success("Draft prepared · Review before sending.")
        with st.container(border=True):
            st.markdown("**Summary**")
            st.write(t["summary"])
            st.caption(t["rationale"])
        reply, steps, evidence = st.tabs(["Suggested reply", "Next steps", "Execution evidence"])
        with reply:
            st.write(t["suggested_reply"])
            st.download_button("Download reply draft", t["suggested_reply"], "reply-draft.txt")
        with steps:
            for i, step in enumerate(t["next_steps"], 1):
                st.write(f"{i}. {step}")
        with evidence:
            st.write(f"**{m['provider'].title()}** · {m['model']} · {m['prompt_version']}")
            st.caption("Schema valid means structurally valid; it does not prove factual accuracy.")
            st.json(m)
        with st.expander("Validated API response"):
            st.json(result)
        st.download_button(
            "Export result JSON",
            json.dumps(result, indent=2),
            "triage.json",
            mime="application/json",
        )
