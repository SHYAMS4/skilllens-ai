import streamlit as st
import google.generativeai as genai
import json
import re
from datetime import datetime

st.set_page_config(page_title="SkillLens AI", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem; border-radius: 12px; margin-bottom: 2rem; text-align: center; }
    .main-header h1 { color: #e94560; font-size: 2.5rem; margin: 0; }
    .main-header p  { color: #a8b2d8; font-size: 1.1rem; margin-top: 0.5rem; }
    .skill-card { background: #1e1e2e; border: 1px solid #333; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
    .score-high   { color: #4ade80; font-weight: bold; }
    .score-medium { color: #fbbf24; font-weight: bold; }
    .score-low    { color: #f87171; font-weight: bold; }
</style>""", unsafe_allow_html=True)

SYSTEM_PROMPT = """You are SkillLens, an expert AI skill assessment agent conducting professional conversational skill assessments.

Assessment process:
1. Ask targeted progressive questions per skill — start basic, go deeper. ONE question at a time.
2. After 2-3 questions per skill, assign a proficiency score 1-10.
3. Be conversational, encouraging, and practical — not interrogative.

Scoring: 1-3 Beginner | 4-6 Intermediate | 7-9 Advanced | 10 Expert

When q_count >= 1, include score as: SKILL_SCORE: X/10
When q_count >= 2, wrap up skill and move to next.
Keep responses under 120 words. Always maintain job role context."""

def init_session():
    defaults = {
        "phase": "setup", "messages": [], "jd": "", "resume": "",
        "skills_required": [], "skills_assessed": {}, "current_skill_idx": 0,
        "questions_per_skill": 0, "learning_plan": None, "api_key": "", "chat_session": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

def call_gemini(prompt: str, chat=False) -> str:
    api_key = st.session_state.get("api_key", "")
    if not api_key:
        return "⚠️ Please enter your Gemini API key."
    genai.configure(api_key=api_key)
    try:
        if chat:
            if st.session_state.chat_session is None:
                model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=SYSTEM_PROMPT)
                st.session_state.chat_session = model.start_chat(history=[])
            response = st.session_state.chat_session.send_message(prompt)
        else:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def score_emoji(s): return "🟢" if s >= 7 else "🟡" if s >= 4 else "🔴"
def score_color(s): return "score-high" if s >= 7 else "score-medium" if s >= 4 else "score-low"

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
    st.title("SkillLens AI")
    st.caption("Catalyst Hackathon — deccan.ai")
    st.divider()
    api_key = st.text_input("🔑 Google Gemini API Key", type="password",
                             value=st.session_state.api_key,
                             help="Free key from aistudio.google.com")
    if api_key:
        st.session_state.api_key = api_key
        st.success("API Key set ✓")
    else:
        st.warning("👆 Get FREE key at aistudio.google.com")

    st.divider()
    st.markdown("### 📊 Progress")
    phases = {"setup": 0, "extracting": 1, "assessing": 2, "planning": 3, "done": 4}
    phase_names = ["Setup", "Extract Skills", "Assess Skills", "Learning Plan", "Complete"]
    cp = phases.get(st.session_state.phase, 0)
    for i, name in enumerate(phase_names):
        st.markdown(f"{'✅' if i < cp else '▶️ **' + name + '**' if i == cp else '⬜'} {name if i != cp else ''}")

    if st.session_state.skills_assessed:
        st.divider()
        st.markdown("### 🎯 Scores")
        for skill, data in st.session_state.skills_assessed.items():
            st.markdown(f"{score_emoji(data['score'])} **{skill}**: {data['score']}/10")

    st.divider()
    if st.button("🔄 Reset", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""<div class="main-header">
    <h1>🎯 SkillLens AI</h1>
    <p>AI-Powered Skill Assessment & Personalised Learning Plan Agent</p>
    <p style="font-size:0.85rem;color:#667eea;">Catalyst Hackathon · deccan.ai · 2026 · Powered by Google Gemini (Free)</p>
</div>""", unsafe_allow_html=True)

# ── SETUP ──────────────────────────────────────────────────────────────────────
if st.session_state.phase == "setup":
    st.markdown("## 📋 Provide Job Description & Resume")
    st.info("Paste both below. AI will extract skills and begin conversational assessment.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📄 Job Description")
        jd = st.text_area("Paste JD here", height=320, key="jd_input",
            placeholder="Role: QA Analyst\nRequirements:\n- Manual Testing\n- JIRA\n- SQL\n- Agile/Scrum")
    with col2:
        st.markdown("### 👤 Candidate Resume")
        resume = st.text_area("Paste resume here", height=320, key="resume_input",
            placeholder="Name: Rahul Sharma\nSkills: Manual Testing, JIRA, SQL\nExp: 3 years banking QA")
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        if st.button("🚀 Start Assessment", use_container_width=True, type="primary"):
            if not st.session_state.api_key: st.error("Enter Gemini API key in sidebar!")
            elif not jd.strip() or not resume.strip(): st.error("Provide both JD and Resume!")
            else:
                st.session_state.jd = jd
                st.session_state.resume = resume
                st.session_state.phase = "extracting"
                st.rerun()

# ── EXTRACTING ─────────────────────────────────────────────────────────────────
elif st.session_state.phase == "extracting":
    with st.spinner("🔍 Analyzing JD and Resume with Gemini AI..."):
        raw = call_gemini(f"""Analyze this Job Description and Resume. Return ONLY a JSON object:
{{
  "required_skills": ["skill1", "skill2"],
  "candidate_claimed_skills": ["skill1"],
  "role_title": "...",
  "skill_gaps": ["skill1"],
  "matching_skills": ["skill1"]
}}

JD: {st.session_state.jd}
Resume: {st.session_state.resume}
Return ONLY JSON, no markdown, no extra text.""")
        try:
            clean = re.sub(r"```json|```", "", raw).strip()
            data = json.loads(clean)
            st.session_state.skills_required = data.get("required_skills", [])
            st.session_state.role_title       = data.get("role_title", "the role")
            st.session_state.skill_gaps       = data.get("skill_gaps", [])
            st.session_state.matching_skills  = data.get("matching_skills", [])
            st.session_state.candidate_skills = data.get("candidate_claimed_skills", [])
        except:
            st.session_state.skills_required = ["Manual Testing", "SQL", "JIRA", "Domain Knowledge"]
            st.session_state.role_title = "the position"

    st.markdown("## ✅ Skills Extracted!")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Required Skills", len(st.session_state.skills_required))
    with c2: st.metric("Matching Skills",  len(st.session_state.get("matching_skills", [])))
    with c3: st.metric("Skill Gaps",       len(st.session_state.get("skill_gaps", [])))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📌 Skills to Assess")
        for i, s in enumerate(st.session_state.skills_required, 1):
            st.markdown(f"{'✅' if s in st.session_state.get('matching_skills',[]) else '❓'} **{i}.** {s}")
    with col2:
        st.markdown("### 👤 Candidate Claims")
        for s in st.session_state.get("candidate_skills", []):
            st.markdown(f"• {s}")

    first = st.session_state.skills_required[0] if st.session_state.skills_required else "your skills"
    st.session_state.messages.append({"role": "assistant", "content":
        f"I've analyzed the JD and Resume.\n\n**Role:** {st.session_state.get('role_title','')}\n"
        f"**Skills to assess:** {', '.join(st.session_state.skills_required[:8])}\n\n"
        f"Let's begin with: **{first}**\n\n"
        f"In your own words, what does {first} mean to you? Give me a real example from your work."
    })
    st.session_state.phase = "assessing"
    if st.button("▶️ Begin Assessment", type="primary", use_container_width=True):
        st.rerun()

# ── ASSESSING ──────────────────────────────────────────────────────────────────
elif st.session_state.phase == "assessing":
    st.markdown("## 💬 Skill Assessment")
    total, done = len(st.session_state.skills_required), len(st.session_state.skills_assessed)
    if total: st.progress(done / total, text=f"Assessed {done}/{total} skills")

    with st.expander("⚙️ Controls", expanded=False):
        cols = st.columns(min(len(st.session_state.skills_required[:6]), 3) or 1)
        for i, s in enumerate(st.session_state.skills_required[:6]):
            with cols[i % len(cols)]:
                st.caption(f"{'✅' if s in st.session_state.skills_assessed else '🔵'} {s}")
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            ms = st.number_input("Score current skill (1-10)", 1, 10, 5)
            mn = st.text_input("Note/Evidence")
        with c2:
            if st.button("✅ Record & Next"):
                skills, idx = st.session_state.skills_required, st.session_state.current_skill_idx
                if idx < len(skills):
                    st.session_state.skills_assessed[skills[idx]] = {
                        "score": ms, "evidence": mn or "Assessed via conversation",
                        "proficiency": "Advanced" if ms >= 7 else "Intermediate" if ms >= 4 else "Beginner"
                    }
                    st.session_state.current_skill_idx += 1
                    st.session_state.questions_per_skill = 0
                    if st.session_state.current_skill_idx >= len(skills):
                        st.session_state.phase = "planning"
                    else:
                        ns = skills[st.session_state.current_skill_idx]
                        st.session_state.messages.append({"role": "assistant",
                            "content": f"✅ Moving to: **{ns}**\n\nDescribe a real situation where you used {ns}."})
                    st.rerun()
            if st.button("⏭️ Skip to Plan"):
                st.session_state.phase = "planning"; st.rerun()

    chat_box = st.container(height=430)
    with chat_box:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🎯" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])

    if prompt := st.chat_input("Type your answer here..."):
        with st.spinner("Analyzing your response..."):
            skills = st.session_state.skills_required
            idx    = st.session_state.current_skill_idx
            cs     = skills[idx] if idx < len(skills) else "general"
            qc     = st.session_state.questions_per_skill

            full_prompt = f"""{prompt}

[CONTEXT: assessing '{cs}', q_count={qc}, assessed={list(st.session_state.skills_assessed.keys())}]
{'Include SKILL_SCORE: X/10 and wrap up this skill, move to next.' if qc >= 1 else 'Ask one follow-up question.'}"""

            st.session_state.messages.append({"role": "user", "content": prompt})
            resp = call_gemini(full_prompt, chat=True)
            st.session_state.messages.append({"role": "assistant", "content": resp})
            st.session_state.questions_per_skill += 1

            m = re.search(r"SKILL_SCORE:\s*(\d+)/10", resp)
            if m and qc >= 1:
                score = int(m.group(1))
                if idx < len(skills) and skills[idx] not in st.session_state.skills_assessed:
                    st.session_state.skills_assessed[skills[idx]] = {
                        "score": score, "evidence": "Conversational Q&A",
                        "proficiency": "Advanced" if score >= 7 else "Intermediate" if score >= 4 else "Beginner"
                    }
                    st.session_state.current_skill_idx += 1
                    st.session_state.questions_per_skill = 0
                    if st.session_state.current_skill_idx >= len(skills):
                        st.session_state.phase = "planning"
            st.rerun()

# ── PLANNING ───────────────────────────────────────────────────────────────────
elif st.session_state.phase == "planning":
    st.markdown("## 📚 Generating Learning Plan...")
    with st.spinner("🧠 Gemini AI crafting your personalised learning journey..."):
        raw = call_gemini(f"""Generate a personalised learning plan as JSON only.

JD Context: {st.session_state.jd[:400]}
Skill Scores: {json.dumps(st.session_state.skills_assessed, indent=2)}

Return ONLY this JSON structure, no markdown:
{{
  "overall_fit_score": 75,
  "summary": "2 sentence summary",
  "strengths": ["skill1", "skill2"],
  "priority_gaps": [
    {{
      "skill": "Selenium",
      "current_score": 3,
      "target_score": 7,
      "why_important": "reason",
      "resources": [
        {{"name": "Selenium WebDriver Bootcamp", "type": "course", "platform": "Udemy", "duration": "3 weeks"}}
      ],
      "total_time_estimate": "6 weeks",
      "learning_path": ["step1", "step2", "step3"]
    }}
  ],
  "quick_wins": ["action 1", "action 2"],
  "30_day_goal": "what to achieve",
  "90_day_goal": "what to achieve"
}}""")
        try:
            plan = json.loads(re.sub(r"```json|```", "", raw).strip())
            st.session_state.learning_plan = plan
        except:
            st.session_state.learning_plan = {"summary": "Plan generated", "raw": raw,
                "overall_fit_score": 70, "strengths": [], "priority_gaps": [], "quick_wins": []}
    st.session_state.phase = "done"
    st.rerun()

# ── DONE ───────────────────────────────────────────────────────────────────────
elif st.session_state.phase == "done":
    plan = st.session_state.learning_plan or {}
    st.markdown("## 🎉 Assessment Complete!")

    assessed_count = len(st.session_state.skills_assessed)
    avg = sum(v["score"] for v in st.session_state.skills_assessed.values()) / max(assessed_count, 1)
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("🎯 Fit Score",       f"{plan.get('overall_fit_score',0)}/100")
    with c2: st.metric("📊 Avg Skill Score", f"{avg:.1f}/10")
    with c3: st.metric("✅ Skills Assessed", assessed_count)

    st.markdown(f"> 💡 **{plan.get('summary', 'Assessment complete!')}**")

    st.markdown("### 📊 Skill Scores")
    cols = st.columns(min(assessed_count, 4) or 1)
    for i, (skill, data) in enumerate(st.session_state.skills_assessed.items()):
        s = data["score"]
        with cols[i % len(cols)]:
            st.markdown(f"""<div class="skill-card"><b>{score_emoji(s)} {skill}</b><br>
            <span class="{score_color(s)}">{s}/10</span> — {data.get('proficiency','')}</div>""",
            unsafe_allow_html=True)

    if plan.get("strengths"):
        st.markdown("### 💪 Strengths")
        for s in plan["strengths"]: st.markdown(f"✅ {s}")

    st.markdown("### 📚 Personalised Learning Plan")
    for gap in plan.get("priority_gaps", []):
        with st.expander(f"🎯 {gap.get('skill','')} | {gap.get('current_score','?')} → {gap.get('target_score','?')} | ⏱️ {gap.get('total_time_estimate','?')}"):
            st.markdown(f"**Why:** {gap.get('why_important','')}")
            st.markdown(f"**Path:** {' → '.join(gap.get('learning_path',[]))}")
            for r in gap.get("resources", []):
                st.markdown(f"- 📖 **{r.get('name','')}** — {r.get('platform','')} | {r.get('duration','')}")

    if plan.get("quick_wins"):
        st.markdown("### ⚡ Quick Wins This Week")
        for w in plan["quick_wins"]: st.markdown(f"→ {w}")

    c1, c2 = st.columns(2)
    with c1: st.info(f"🗓️ **30 Days:** {plan.get('30_day_goal','')}")
    with c2: st.success(f"🏆 **90 Days:** {plan.get('90_day_goal','')}")

    st.divider()
    st.download_button("⬇️ Download Report (JSON)",
        data=json.dumps({"date": datetime.now().isoformat(),
                         "skills": st.session_state.skills_assessed, "plan": plan}, indent=2),
        file_name="skilllens_report.json", mime="application/json", use_container_width=True)

    if st.button("🔄 New Assessment", use_container_width=True, type="primary"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
