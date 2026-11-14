import os
import re
import json
import wave
import requests
import pandas as pd
import altair as alt
import streamlit as st
import speech_recognition as sr

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="LecturePulse",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- APPLE-INSPIRED DESIGN SYSTEM CSS ---
st.markdown("""
<style>
    /* Global Typography & Canvas */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Inter", sans-serif;
        color: #1D1D1F;
    }
    .stApp {
        background-color: #F5F5F7;
    }
    header[data-testid="stHeader"] {
        background-color: rgba(245, 245, 247, 0.8);
        backdrop-filter: blur(12px);
    }
    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 4rem;
        max-width: 1180px;
    }

    /* Headings */
    h1 {
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
        color: #1D1D1F !important;
        font-size: 2.35rem !important;
        margin-bottom: 0.2rem !important;
    }
    h2, h3 {
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
        color: #1D1D1F !important;
    }

    /* Apple Elevated White Cards */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border-radius: 18px !important;
        border: 1px solid rgba(0, 0, 0, 0.06) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03) !important;
        padding: 1.25rem 1.4rem !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid rgba(0, 0, 0, 0.06) !important;
    }

    /* Apple Pill Buttons */
    .stButton > button {
        border-radius: 980px !important;
        font-weight: 500 !important;
        letter-spacing: -0.01em !important;
        padding: 0.45rem 1.25rem !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #0071E3 !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #0077ED !important;
        box-shadow: 0 4px 12px rgba(0, 113, 227, 0.28) !important;
    }

    /* Segmented Step Indicator */
    .apple-stepper {
        display: flex;
        background: #E8E8ED;
        padding: 4px;
        border-radius: 12px;
        gap: 4px;
        margin: 1.2rem 0 1.6rem 0;
    }
    .apple-step {
        flex: 1;
        text-align: center;
        padding: 8px 12px;
        border-radius: 9px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #6E6E73;
        transition: all 0.2s ease;
    }
    .apple-step.active {
        background: #FFFFFF;
        color: #1D1D1F;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    }
    .apple-step.done {
        color: #0071E3;
    }

    /* Apple KPI Cards */
    .kpi-card {
        background: #FFFFFF;
        border-radius: 18px;
        padding: 18px 20px;
        border: 1px solid rgba(0, 0, 0, 0.06);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
    }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #86868B;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        color: #1D1D1F;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 0.82rem;
        font-weight: 500;
        margin-top: 6px;
    }

    /* Apple Semantic Pills */
    .pill-green {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 980px;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(52, 199, 89, 0.14);
        color: #248A3D;
    }
    .pill-orange {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 980px;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(255, 159, 10, 0.16);
        color: #B25000;
    }
    .pill-red {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 980px;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(255, 59, 48, 0.14);
        color: #D70015;
    }

    /* Insight Callout Banner */
    .apple-callout {
        background: linear-gradient(135deg, #FFFFFF 0%, #F0F7FF 100%);
        border: 1px solid rgba(0, 113, 227, 0.18);
        border-radius: 16px;
        padding: 16px 20px;
        margin: 1rem 0 1.4rem 0;
        font-size: 0.96rem;
        line-height: 1.5;
        color: #1D1D1F;
    }

    /* Clean Text Inputs */
    .stTextInput input, .stTextArea textarea {
        border-radius: 12px !important;
        border: 1px solid rgba(0, 0, 0, 0.12) !important;
        background-color: #FAFAFC !important;
    }
</style>
""", unsafe_allow_html=True)

# --- PATHS & ENV ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "recordings")
os.makedirs(OUTPUT_DIR, exist_ok=True)
AUDIO_FILE_PATH = os.path.join(OUTPUT_DIR, "lezione_corrente.wav")
QUIZ_FILE_PATH = os.path.join(BASE_DIR, "quiz_data.json")

def load_api_key() -> str:
    env_path = os.path.join(BASE_DIR, ".env")
    for path in [env_path, ".env"]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("OPENROUTER_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv("OPENROUTER_API_KEY", "")

API_KEY = load_api_key()

@st.cache_data(ttl=300)
def fetch_allowed_models(api_key: str) -> list:
    if not api_key:
        return ["openai/gpt-4o-mini"]
    try:
        res = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15
        )
        if res.status_code == 200:
            ids = [m["id"] for m in res.json().get("data", [])]
            preferred = [
                "openai/gpt-4o-mini",
                "anthropic/claude-3.5-haiku",
                "google/gemini-2.0-flash-001",
                "google/gemini-2.5-flash",
                "meta-llama/llama-3.3-70b-instruct",
                "mistralai/mistral-small-3.1-24b-instruct"
            ]
            ordered = [m for m in preferred if m in ids] + [m for m in ids if m not in preferred]
            if ordered:
                return ordered
    except Exception:
        pass
    return ["openai/gpt-4o-mini"]

# --- SESSION STATE ---
for key, default in [
    ("transcript", ""),
    ("last_audio_size", None),
    ("quizzes_started", False),
    ("feedback_result", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### LecturePulse")
    st.caption("Real-Time Classroom Intelligence")
    st.divider()

    if API_KEY:
        st.markdown(f"<span class='pill-green'>● API Connected · ...{API_KEY[-6:]}</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='pill-red'>● Missing API Key</span>", unsafe_allow_html=True)

    st.markdown("")
    speech_lang = st.selectbox(
        "Voice Language",
        ["en-US", "en-GB", "it-IT"],
        index=0
    )

    allowed_models = fetch_allowed_models(API_KEY)
    model_name = st.selectbox(
        "Intelligence Model",
        allowed_models,
        index=0
    )

    st.divider()
    st.caption("DEMO CONTROLS")
    if st.button("Load Sample Transcript", use_container_width=True):
        st.session_state["transcript"] = (
            "Today we are introducing Bayes' Theorem. Remember that the probability of having a disease "
            "given a positive test is not equal to the test sensitivity. We must weight the likelihood "
            "by the prior prevalence of the disease in the population. Also, two events like fever and cough "
            "may be correlated overall, but become conditionally independent once we know the patient has the flu."
        )
        st.session_state["feedback_result"] = None
        st.rerun()

    if st.button("Reset Session", use_container_width=True):
        st.session_state["transcript"] = ""
        st.session_state["last_audio_size"] = None
        st.session_state["quizzes_started"] = False
        st.session_state["feedback_result"] = None
        st.rerun()

# --- LLM & AUDIO FUNCTIONS ---
def call_openrouter(messages: list, max_tokens: int = 4000, json_mode: bool = False) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "LecturePulse-Hackathon"
    }
    payload = {
        "model": model_name,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.15
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )

    if response.status_code == 400 and json_mode:
        payload.pop("response_format", None)
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

    if response.status_code != 200:
        raise RuntimeError(f"OpenRouter Error ({response.status_code}): {response.text}")
    return response.json()["choices"][0]["message"]["content"].strip()

def transcribe_audio(audio_path: str, lang: str) -> str:
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
    return recognizer.recognize_google(audio_data, language=lang)

def generate_feedback(topic: str, transcript: str, quizzes: list) -> dict:
    prompt = f"""You are an expert university pedagogical analyst. Cross-reference the professor's lecture transcript with every single student quiz answer.
Keep all text concise (max 2 sentences per string) so the JSON stays compact and valid.

LECTURE TOPIC:
{topic}

LECTURE TRANSCRIPT:
{transcript}

QUIZ QUESTIONS & STUDENT ANSWERS:
{json.dumps(quizzes, ensure_ascii=False)}

Return ONLY a valid JSON object with this exact schema:
{{
  "summary_docente": "Direct 2-sentence executive insight linking what students missed directly to what the professor explained or omitted in the transcript.",
  "graded_responses": [
    {{
      "question_id": "Q1",
      "student": "Student 1",
      "status": "Mastered",
      "misconception_category": "None (Mastered)",
      "personalized_feedback": "1-sentence tailored feedback explaining why their reasoning holds or falls short."
    }}
  ],
  "teaching_actions": [
    {{
      "misconception_category": "Short canonical label (e.g. Base Rate Neglect)",
      "root_cause": "Why students made this logical error compared to the transcript.",
      "live_intervention": "Concrete 1-sentence counter-example or clarification the professor can say right now."
    }}
  ]
}}

Rules for "graded_responses":
- Include EVERY student answer from the input quizzes.
- "status" MUST be strictly one of: "Mastered", "Partial", "Misconception".
- If "status" is "Mastered", set "misconception_category" to "None (Mastered)".
- Otherwise, assign a concise, standardized 2-3 word "misconception_category" (e.g., "Base Rate Neglect", "Inverted Conditional", "Independence Confusion", "Zero-Prob Fallacy") so identical errors group cleanly."""

    raw = call_openrouter([{"role": "user", "content": prompt}], max_tokens=4000, json_mode=True)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    json_str = match.group(0) if match else raw
    return json.loads(json_str)

# --- HEADER & SEGMENTED STEPPER ---
st.title("LecturePulse")
st.markdown("<p style='color:#6E6E73; font-size:1.08rem; margin-top:-6px;'>Instant pedagogical clarity between what you teach and what students actually grasp.</p>", unsafe_allow_html=True)

s1_cls = "done" if st.session_state["transcript"] else "active"
s2_cls = "done" if st.session_state["feedback_result"] else ("active" if st.session_state["quizzes_started"] else "")
s3_cls = "active" if st.session_state["feedback_result"] else ""

st.markdown(f"""
<div class="apple-stepper">
    <div class="apple-step {s1_cls}">1 · Capture & Transcribe</div>
    <div class="apple-step {s2_cls}">2 · Mid-Lecture Check</div>
    <div class="apple-step {s3_cls}">3 · Instant Diagnostics</div>
</div>
""", unsafe_allow_html=True)

# --- STEP 1: CAPTURE & TRANSCRIBE ---
with st.container(border=True):
    col_top_l, col_top_r = st.columns([2, 1])
    with col_top_l:
        st.subheader("1. Capture Explanation")
    with col_top_r:
        topic = st.text_input("Topic", value="Bayes' Theorem & Conditional Independence", label_visibility="collapsed")

    col_rec, col_txt = st.columns([1, 2.2], gap="large")

    with col_rec:
        st.caption("Record up to 60s of live lecture")
        audio_bytes = st.audio_input("Record explanation", label_visibility="collapsed")

        if audio_bytes is not None:
            raw_bytes = audio_bytes.getbuffer()
            with open(AUDIO_FILE_PATH, "wb") as f:
                f.write(raw_bytes)

            with wave.open(AUDIO_FILE_PATH, "rb") as wf:
                duration_sec = round(wf.getnframes() / float(wf.getframerate()), 1)

            st.markdown(f"<span class='pill-green'>✓ Recorded {duration_sec}s</span>", unsafe_allow_html=True)

            if st.session_state["last_audio_size"] != len(raw_bytes):
                with st.spinner("Transcribing..."):
                    try:
                        st.session_state["transcript"] = transcribe_audio(AUDIO_FILE_PATH, speech_lang)
                        st.session_state["last_audio_size"] = len(raw_bytes)
                        st.session_state["feedback_result"] = None
                    except Exception as e:
                        st.warning(f"Audio unclear ({e}). Edit text or use sample transcript.")

    with col_txt:
        st.caption("Live Transcript (editable)")
        transcript_val = st.text_area(
            "Transcript",
            value=st.session_state["transcript"],
            height=120,
            placeholder="Tap the microphone on the left to record, or click 'Load Sample Transcript' in the sidebar...",
            label_visibility="collapsed"
        )
        st.session_state["transcript"] = transcript_val

        if st.session_state["transcript"].strip():
            if st.button("Start Quizzes →", type="primary"):
                st.session_state["quizzes_started"] = True

# --- STEP 2: MID-LECTURE CHECK ---
if st.session_state["quizzes_started"] and st.session_state["transcript"].strip():
    st.markdown("")
    with st.container(border=True):
        st.subheader("2. Mid-Lecture Comprehension Check")
        st.caption("Select active questions to evaluate against your spoken explanation.")

        with open(QUIZ_FILE_PATH, "r", encoding="utf-8") as f:
            all_quizzes = json.load(f)["quizzes"]

        selected_quizzes = []
        q_tabs = st.tabs([f"{q['id']} · {len(q['student_answers'])} responses" for q in all_quizzes])

        for idx, q in enumerate(all_quizzes):
            with q_tabs[idx]:
                include_q = st.checkbox(
                    f"Evaluate **{q['id']}**",
                    value=True,
                    key=f"chk_{q['id']}"
                )
                st.markdown(f"**Question:** *{q['question']}*")
                resp_df = pd.DataFrame(q["student_answers"])
                resp_df.columns = ["Student", "Response"]
                st.dataframe(resp_df, use_container_width=True, hide_index=True, height=195)

                if include_q:
                    selected_quizzes.append(q)

        st.markdown("")
        if selected_quizzes:
            if st.button("Produce Feedback →", type="primary"):
                with st.spinner("Analyzing classroom understanding..."):
                    try:
                        st.session_state["feedback_result"] = generate_feedback(
                            topic=topic,
                            transcript=st.session_state["transcript"],
                            quizzes=selected_quizzes
                        )
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")

# --- STEP 3: INSTANT 1-SECOND EDA DIAGNOSTICS ---
if st.session_state["feedback_result"]:
    res = st.session_state["feedback_result"]
    graded = res.get("graded_responses", [])
    actions = res.get("teaching_actions", [])

    st.markdown("")
    st.subheader("3. Classroom Pulse & Diagnostics")

    if graded:
        df = pd.DataFrame(graded)
        df["status"] = df["status"].apply(
            lambda x: x if x in ["Mastered", "Partial", "Misconception"] else "Misconception"
        )

        total_resp = len(df)
        mastered_cnt = int((df["status"] == "Mastered").sum())
        partial_cnt = int((df["status"] == "Partial").sum())
        misc_cnt = int((df["status"] == "Misconception").sum())

        mastery_rate = round((mastered_cnt / total_resp) * 100) if total_resp else 0
        misc_rate = round((misc_cnt / total_resp) * 100) if total_resp else 0

        misc_only_df = df[df["status"] != "Mastered"]
        top_misc = (
            misc_only_df["misconception_category"].value_counts().index[0]
            if not misc_only_df.empty else "All Clear"
        )
        top_misc_count = (
            int(misc_only_df["misconception_category"].value_counts().iloc[0])
            if not misc_only_df.empty else 0
        )

        # --- 4 APPLE KPI CARDS ---
        k1, k2, k3, k4 = st.columns(4, gap="medium")
        with k1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Class Mastery</div>
                <div class="kpi-value" style="color:#248A3D;">{mastery_rate}%</div>
                <div class="kpi-sub" style="color:#6E6E73;">{mastered_cnt} of {total_resp} answers solid</div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Needs Clarification</div>
                <div class="kpi-value" style="color:#D70015;">{misc_rate}%</div>
                <div class="kpi-sub" style="color:#6E6E73;">{misc_cnt} critical misconceptions</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Primary Blocker</div>
                <div class="kpi-value" style="font-size:1.35rem; padding-top:6px;">{top_misc}</div>
                <div class="kpi-sub" style="color:#D70015;">Affected {top_misc_count} responses</div>
            </div>
            """, unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Partial Grasp</div>
                <div class="kpi-value" style="color:#B25000;">{partial_cnt}</div>
                <div class="kpi-sub" style="color:#6E6E73;">Right intuition, incomplete logic</div>
            </div>
            """, unsafe_allow_html=True)

        # --- EXECUTIVE INSIGHT CALLOUT ---
        st.markdown(f"""
        <div class="apple-callout">
            <strong style="color:#0071E3;">Key Takeaway:</strong> {res.get('summary_docente', '')}
        </div>
        """, unsafe_allow_html=True)

        # --- TWO HERO CHARTS (1-SECOND COMPREHENSION) ---
        apple_palette = alt.Scale(
            domain=["Mastered", "Partial", "Misconception"],
            range=["#34C759", "#FF9F0A", "#FF3B30"]
        )

        c_left, c_right = st.columns(2, gap="large")

        with c_left:
            with st.container(border=True):
                st.markdown("#### Comprehension Split by Question")
                st.caption("Green = Mastered · Amber = Partial · Red = Misconception")

                comp_df = (
                    df.groupby(["question_id", "status"])
                    .size()
                    .reset_index(name="count")
                )
                comp_df["total_q"] = comp_df.groupby("question_id")["count"].transform("sum")
                comp_df["pct"] = (comp_df["count"] / comp_df["total_q"]) * 100
                comp_df["label"] = comp_df["pct"].round(0).astype(int).astype(str) + "%"

                bars = alt.Chart(comp_df).mark_bar(
                    height=44,
                    cornerRadius=8
                ).encode(
                    x=alt.X("pct:Q", stack="normalize", axis=None),
                    y=alt.Y(
                        "question_id:N",
                        title=None,
                        axis=alt.Axis(labelFontSize=14, labelFontWeight="bold", labelColor="#1D1D1F", domain=False, ticks=False)
                    ),
                    color=alt.Color(
                        "status:N",
                        scale=apple_palette,
                        legend=alt.Legend(orient="top", title=None, labelFontSize=12, symbolType="circle")
                    ),
                    tooltip=["question_id", "status", "count", alt.Tooltip("pct:Q", format=".0f", title="Share (%)")]
                )

                labels = alt.Chart(comp_df[comp_df["pct"] >= 14]).mark_text(
                    color="white",
                    fontWeight="bold",
                    fontSize=13
                ).encode(
                    x=alt.X("pct:Q", stack="normalize", bandPosition=0.5),
                    y=alt.Y("question_id:N"),
                    text="label:N",
                    detail="status:N"
                )

                chart1 = (bars + labels).configure_view(strokeWidth=0).properties(height=190)
                st.altair_chart(chart1, use_container_width=True)

        with c_right:
            with st.container(border=True):
                st.markdown("#### Top Misconceptions Blocking the Class")
                st.caption("Ranked by number of affected responses (direct count & share)")

                if not misc_only_df.empty:
                    pareto_df = (
                        misc_only_df.groupby("misconception_category")
                        .size()
                        .reset_index(name="students")
                        .sort_values("students", ascending=False)
                    )
                    pareto_df["share"] = ((pareto_df["students"] / total_resp) * 100).round(0).astype(int)
                    pareto_df["direct_label"] = pareto_df.apply(
                        lambda r: f"{r['students']} ({r['share']}%)", axis=1
                    )
                    max_val = int(pareto_df["students"].max())

                    p_bars = alt.Chart(pareto_df).mark_bar(
                        height=32,
                        cornerRadiusEnd=8,
                        color="#FF3B30"
                    ).encode(
                        x=alt.X("students:Q", scale=alt.Scale(domain=[0, max_val * 1.38]), axis=None),
                        y=alt.Y(
                            "misconception_category:N",
                            sort="-x",
                            title=None,
                            axis=alt.Axis(labelFontSize=13, labelFontWeight="bold", labelColor="#1D1D1F", domain=False, ticks=False, labelLimit=180)
                        ),
                        tooltip=["misconception_category", "students", alt.Tooltip("share:Q", title="Class Share (%)")]
                    )

                    p_labels = alt.Chart(pareto_df).mark_text(
                        align="left",
                        dx=8,
                        fontSize=13,
                        fontWeight="bold",
                        color="#1D1D1F",
                        clip=False
                    ).encode(
                        x=alt.X("students:Q"),
                        y=alt.Y("misconception_category:N", sort="-x"),
                        text="direct_label:N"
                    )

                    chart2 = (p_bars + p_labels).configure_view(strokeWidth=0).properties(height=190)
                    st.altair_chart(chart2, use_container_width=True)
                else:
                    st.success("100% of responses mastered the lecture concepts.")

        # --- CHART 3: APPLE FITNESS-STYLE STUDENT × QUESTION PULSE GRID ---
        with st.container(border=True):
            st.markdown("#### Classroom Pulse Matrix (Student × Question)")
            st.caption("Instant visual scan of every student's conceptual state across questions.")

            matrix_chart = alt.Chart(df).mark_rect(
                cornerRadius=8,
                stroke="#FFFFFF",
                strokeWidth=4
            ).encode(
                x=alt.X(
                    "student:N",
                    title=None,
                    axis=alt.Axis(labelAngle=0, labelFontSize=12, labelFontWeight="bold", labelColor="#1D1D1F", domain=False, ticks=False)
                ),
                y=alt.Y(
                    "question_id:N",
                    title=None,
                    axis=alt.Axis(labelFontSize=13, labelFontWeight="bold", labelColor="#1D1D1F", domain=False, ticks=False)
                ),
                color=alt.Color("status:N", scale=apple_palette, legend=None),
                tooltip=["student", "question_id", "status", "misconception_category", "personalized_feedback"]
            ).configure_view(strokeWidth=0).properties(height=135)

            st.altair_chart(matrix_chart, use_container_width=True)

        # --- ACTIONABLE INTERVENTIONS & 1-ON-1 FEEDBACK ---
        st.markdown("### Live Action Plan & Student Feedback")
        tab_prof, tab_stud = st.tabs([
            f"Professor Live Interventions ({len(actions)})",
            f"1-on-1 Student Feedback ({len(df)})"
        ])

        with tab_prof:
            if actions:
                for act in actions:
                    with st.container(border=True):
                        st.markdown(f"<span class='pill-red'>PRIORITY FIX</span> &nbsp; <strong style='font-size:1.05rem;'>{act.get('misconception_category', '')}</strong>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color:#6E6E73; margin-top:6px;'>{act.get('root_cause', '')}</p>", unsafe_allow_html=True)
                        st.info(f"🗣️ **Say out loud now:** \"{act.get('live_intervention', '')}\"")
            else:
                st.success("No corrective intervention needed.")

        with tab_stud:
            for _, row in df.iterrows():
                pill_cls = (
                    "pill-green" if row["status"] == "Mastered"
                    else ("pill-orange" if row["status"] == "Partial" else "pill-red")
                )
                with st.container(border=True):
                    st.markdown(
                        f"<strong>{row['student']}</strong> &nbsp;·&nbsp; <code style='color:#6E6E73;'>{row['question_id']}</code> &nbsp;&nbsp; "
                        f"<span class='{pill_cls}'>{row['status']} · {row['misconception_category']}</span>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"<p style='margin-top:6px; margin-bottom:0; color:#1D1D1F;'>{row['personalized_feedback']}</p>", unsafe_allow_html=True)
