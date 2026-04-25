import streamlit as st
import anthropic
import json
import re
from datetime import datetime

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SkillLens AI – Skill Assessment Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem; border-radius: 12px; margin-bottom: 2rem; text-align: center;
    }
    .main-header h1 { color: #e94560; font-size: 2.5rem; margin: 0; }
    .main-header p  { color: #a8b2d8; font-size: 1.1rem; margin-top: 0.5rem; }
    .skill-card {
        background: #1e1e2e; border: 1px solid #333; border-radius: 10px;
        padding: 1rem; margin: 0.5rem 0;
    }
    .score-high   { color: #4ade80; font-weight: bold; }
    .score-medium { color: #fbbf24; font-weight: bold; }
    .score-low    { color: #f87171; font-weight: bold; }
    .phase-badge {
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        font-size: 0.8rem; font-weight: bold; margin-bottom: 1rem;
    }
    .stChatMessage { border-radius: 10px; }
    .metric-box {
        background: #0f3460; border-radius: 10px; padding: 1rem;
        text-align: center; border: 1px solid #e94560;
    }
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are SkillLens, an expert AI skill assessment agent. You conduct professional, 
conversational skill assessments for job candidates. 

Your assessment process:
1. EXTRACT phase: When given a JD and resume, extract the required skills from the JD and the candidate's claimed skills from the resume.
2. ASSESS phase: Ask targeted, progressive questions for each skill — start with a basic concept question, then go deeper based on the answer. Ask ONE question at a time.
3. SCORE phase: After assessing each skill, assign a proficiency score 1-10 with reasoning.
4. PLAN phase: Generate a detailed personalised learning plan for skill gaps.

Scoring rubric:
- 1-3: Beginner (never used or very limited exposure)
- 4-6: Intermediate (used in projects, some practical experience)
- 7-9: Advanced (deep practical experience, can mentor others)
- 10: Expert (industry-level mastery, thought leader)

When assessing:
- Be conversational and encouraging, not interrogative
- Ask practical, real-world questions not theoretical definitions
- Acknowledge good answers positively
- After 2-3 questions per skill, move to the next skill
- Keep responses concise and focused

When generating learning plans:
- Focus on ADJACENT skills the candidate can realistically acquire
- Provide specific resource names (courses, books, platforms)
- Give realistic time estimates in weeks
- Prioritise skills by impact on job fit
- Format as structured JSON when asked

Always maintain context of the job role being assessed for."""

def get_client():
    api_key = st.session_state.get("api_key", "")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)

# ── SESSION STATE INIT ─────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "phase": "setup",           # setup → extracting → assessing → planning → done
        "messages": [],             # chat history
        "jd": "",
        "resume": "",
        "skills_required": [],      # from JD
        "skills_assessed": {},      # skill → {score, evidence, questions_asked}
        "current_skill_idx": 0,
        "questions_per_skill": 0,
        "learning_plan": None,
        "assessment_started": False,
        "api_key": ""
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ── HELPER FUNCTIONS ───────────────────────────────────────────────────────────
def chat_with_agent(user_message: str) -> str:
    client = get_client()
    if not client:
        return "⚠️ Please enter your Anthropic API key in the sidebar."

    st.session_state.messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=st.session_state.messages
    )
    assistant_msg = response.content[0].text
    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
    return assistant_msg

def extract_skills_from_jd(jd: str, resume: str) -> str:
    client = get_client()
    if not client:
        return ""

    prompt = f"""Analyze this Job Description and Resume. Return a JSON object with this exact structure:
{{
  "required_skills": ["skill1", "skill2", ...],
  "candidate_claimed_skills": ["skill1", "skill2", ...],
  "role_title": "...",
  "skill_gaps": ["skill1", ...],
  "matching_skills": ["skill1", ...]
}}

Job Description:
{jd}

Resume:
{resume}

Return ONLY the JSON, no other text."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def generate_learning_plan(skills_assessed: dict, jd: str) -> str:
    client = get_client()
    if not client:
        return ""

    skills_summary = json.dumps(skills_assessed, indent=2)

    prompt = f"""Based on this skill assessment, generate a detailed personalised learning plan.

Job Description Context:
{jd[:500]}

Skills Assessment Results:
{skills_summary}

Generate a JSON learning plan with this structure:
{{
  "overall_fit_score": 0-100,
  "summary": "brief assessment summary",
  "strengths": ["skill1", ...],
  "priority_gaps": [
    {{
      "skill": "skill name",
      "current_score": X,
      "target_score": Y,
      "why_important": "reason",
      "resources": [
        {{"name": "resource name", "type": "course/book/practice", "platform": "platform", "url_hint": "search term", "duration": "X weeks"}}
      ],
      "total_time_estimate": "X-Y weeks",
      "learning_path": ["step1", "step2", "step3"]
    }}
  ],
  "quick_wins": ["thing to do this week 1", "thing 2"],
  "30_day_goal": "what they can achieve in 30 days",
  "90_day_goal": "what they can achieve in 90 days"
}}

Return ONLY the JSON."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def score_color(score):
    if score >= 7: return "score-high"
    if score >= 4: return "score-medium"
    return "score-low"

def score_emoji(score):
    if score >= 7: return "🟢"
    if score >= 4: return "🟡"
    return "🔴"

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
    st.title("SkillLens AI")
    st.caption("Catalyst Hackathon — deccan.ai")
    st.divider()

    api_key = st.text_input("🔑 Anthropic API Key", type="password",
                             value=st.session_state.api_key,
                             help="Get your key from console.anthropic.com")
    if api_key:
        st.session_state.api_key = api_key
        st.success("API Key set ✓")

    st.divider()

    # Progress tracker
    st.markdown("### 📊 Assessment Progress")
    phases = {"setup": 0, "extracting": 1, "assessing": 2, "planning": 3, "done": 4}
    current_phase = phases.get(st.session_state.phase, 0)
    phase_names = ["Setup", "Extract Skills", "Assess Skills", "Learning Plan", "Complete"]
    for i, name in enumerate(phase_names):
        if i < current_phase:
            st.markdown(f"✅ {name}")
        elif i == current_phase:
            st.markdown(f"▶️ **{name}**")
        else:
            st.markdown(f"⬜ {name}")

    if st.session_state.skills_assessed:
        st.divider()
        st.markdown("### 🎯 Scores So Far")
        for skill, data in st.session_state.skills_assessed.items():
            score = data.get("score", 0)
            emoji = score_emoji(score)
            st.markdown(f"{emoji} **{skill}**: {score}/10")

    st.divider()
    if st.button("🔄 Reset Everything", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ── MAIN CONTENT ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🎯 SkillLens AI</h1>
    <p>AI-Powered Skill Assessment & Personalised Learning Plan Agent</p>
    <p style="font-size:0.85rem; color:#667eea;">Catalyst Hackathon · deccan.ai · 2026</p>
</div>
""", unsafe_allow_html=True)

# ── PHASE: SETUP ───────────────────────────────────────────────────────────────
if st.session_state.phase == "setup":
    st.markdown("## 📋 Step 1: Provide Job Description & Resume")
    st.info("Paste the Job Description and candidate resume below. The agent will extract required skills and begin a conversational assessment.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📄 Job Description")
        jd = st.text_area("Paste JD here", height=350, placeholder="""Example:
We are looking for a Senior QA Engineer with:
- 3+ years of manual testing experience
- Strong knowledge of BFSI domain
- Experience with JIRA, ALM
- SQL database testing
- API testing with Postman
- Knowledge of Agile/Scrum
- Selenium automation (preferred)
        """, key="jd_input")

    with col2:
        st.markdown("### 👤 Candidate Resume")
        resume = st.text_area("Paste resume here", height=350, placeholder="""Example:
John Doe | QA Analyst | 4 years experience
Skills: Manual Testing, JIRA, SQL, Postman, Python
Experience: TCS (2021-Present) - QA at banking client
- Performed functional testing of banking systems
- Wrote 200+ test cases for core banking modules
- Used JIRA for defect tracking
Education: B.Tech Computer Science
        """, key="resume_input")

    col_btn1, col_btn2, col_btn3 = st.columns([1,2,1])
    with col_btn2:
        if st.button("🚀 Start Assessment", use_container_width=True, type="primary"):
            if not st.session_state.api_key:
                st.error("Please enter your Anthropic API key in the sidebar first!")
            elif not jd.strip() or not resume.strip():
                st.error("Please provide both the Job Description and Resume!")
            else:
                st.session_state.jd = jd
                st.session_state.resume = resume
                st.session_state.phase = "extracting"
                st.rerun()

# ── PHASE: EXTRACTING ──────────────────────────────────────────────────────────
elif st.session_state.phase == "extracting":
    with st.spinner("🔍 Analyzing JD and Resume... Extracting skills..."):
        raw = extract_skills_from_jd(st.session_state.jd, st.session_state.resume)
        try:
            # clean possible markdown fences
            clean = re.sub(r"```json|```", "", raw).strip()
            data = json.loads(clean)
            st.session_state.skills_required   = data.get("required_skills", [])
            st.session_state.role_title         = data.get("role_title", "the role")
            st.session_state.skill_gaps         = data.get("skill_gaps", [])
            st.session_state.matching_skills    = data.get("matching_skills", [])
            st.session_state.candidate_skills   = data.get("candidate_claimed_skills", [])
        except:
            st.session_state.skills_required = ["Communication", "Technical Skills", "Problem Solving"]
            st.session_state.role_title = "the role"

    # Show extraction results
    st.markdown("## ✅ Skills Extracted!")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Required Skills", len(st.session_state.skills_required))
    with c2:
        st.metric("Matching Skills", len(st.session_state.get("matching_skills", [])))
    with c3:
        st.metric("Skill Gaps", len(st.session_state.get("skill_gaps", [])))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📌 Skills to Assess (from JD)")
        for i, skill in enumerate(st.session_state.skills_required, 1):
            match = skill in st.session_state.get("matching_skills", [])
            icon = "✅" if match else "❓"
            st.markdown(f"{icon} **{i}.** {skill}")

    with col2:
        st.markdown("### 👤 Candidate Claims (from Resume)")
        for skill in st.session_state.get("candidate_skills", []):
            st.markdown(f"• {skill}")

    # Kickoff message
    kickoff = f"""I've analyzed the Job Description and Resume. 

**Role:** {st.session_state.get('role_title', 'the position')}
**Skills I'll assess:** {', '.join(st.session_state.skills_required[:8])}

I'll now ask you targeted questions for each skill to assess your actual proficiency — not just what's listed on paper.

Let's begin with the first skill: **{st.session_state.skills_required[0] if st.session_state.skills_required else 'your core skills'}**

{f"Can you tell me — in your own words — what {st.session_state.skills_required[0]} means to you, and give me a real example from your work where you used it?" if st.session_state.skills_required else "Tell me about your strongest technical skill."}"""

    st.session_state.messages.append({"role": "assistant", "content": kickoff})
    st.session_state.phase = "assessing"

    if st.button("▶️ Begin Conversational Assessment", type="primary", use_container_width=True):
        st.rerun()

# ── PHASE: ASSESSING ───────────────────────────────────────────────────────────
elif st.session_state.phase == "assessing":
    st.markdown("## 💬 Skill Assessment in Progress")

    # Skills progress bar
    total = len(st.session_state.skills_required)
    done  = len(st.session_state.skills_assessed)
    if total > 0:
        st.progress(done / total, text=f"Assessed {done}/{total} skills")

    # Control panel
    with st.expander("⚙️ Assessment Controls", expanded=False):
        cols = st.columns(len(st.session_state.skills_required[:8]) or 1)
        for i, skill in enumerate(st.session_state.skills_required[:8]):
            with cols[i % len(cols)]:
                assessed = skill in st.session_state.skills_assessed
                color = "✅" if assessed else "🔵"
                st.caption(f"{color} {skill}")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            manual_score = st.number_input("Manually score current skill (1-10)", 1, 10, 5)
            skill_note   = st.text_input("Evidence/Note")
        with col2:
            if st.button("✅ Record Score & Next Skill"):
                skills = st.session_state.skills_required
                idx    = st.session_state.current_skill_idx
                if idx < len(skills):
                    skill = skills[idx]
                    st.session_state.skills_assessed[skill] = {
                        "score": manual_score,
                        "evidence": skill_note or "Assessed via conversation",
                        "proficiency": "Advanced" if manual_score >= 7 else "Intermediate" if manual_score >= 4 else "Beginner"
                    }
                    st.session_state.current_skill_idx += 1
                    st.session_state.questions_per_skill = 0

                    if st.session_state.current_skill_idx >= len(skills):
                        st.session_state.phase = "planning"
                    else:
                        next_skill = skills[st.session_state.current_skill_idx]
                        transition = f"✅ Got it! Moving to the next skill: **{next_skill}**\n\nLet's talk about your experience with {next_skill}. Can you describe a specific situation where you had to use {next_skill} to solve a real problem?"
                        st.session_state.messages.append({"role": "assistant", "content": transition})
                    st.rerun()

            if st.button("⏭️ Skip to Learning Plan"):
                st.session_state.phase = "planning"
                st.rerun()

    # Chat display
    chat_container = st.container(height=450)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🎯" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Type your answer here..."):
        with st.spinner("SkillLens is analyzing your response..."):
            skills = st.session_state.skills_required
            idx    = st.session_state.current_skill_idx

            # Build context-aware prompt
            current_skill = skills[idx] if idx < len(skills) else "general skills"
            q_count = st.session_state.questions_per_skill

            context = f"""[ASSESSMENT CONTEXT]
Current skill being assessed: {current_skill}
Questions asked so far for this skill: {q_count}
All skills to assess: {', '.join(skills)}
Skills already assessed: {', '.join(st.session_state.skills_assessed.keys())}
Candidate answer: {prompt}

[INSTRUCTIONS]
- If this is question 2+ for this skill, also provide a score estimate in format: SKILL_SCORE: X/10
- If questions_asked >= 2, wrap up this skill and move to next one
- Keep your response under 150 words
- Be encouraging and professional"""

            response = chat_with_agent(prompt + "\n\n" + context)
            st.session_state.questions_per_skill += 1

            # Auto-extract score if agent provides it
            score_match = re.search(r"SKILL_SCORE:\s*(\d+)/10", response)
            if score_match and q_count >= 1:
                score = int(score_match.group(1))
                if idx < len(skills) and skills[idx] not in st.session_state.skills_assessed:
                    st.session_state.skills_assessed[skills[idx]] = {
                        "score": score,
                        "evidence": "Assessed via conversational Q&A",
                        "proficiency": "Advanced" if score >= 7 else "Intermediate" if score >= 4 else "Beginner"
                    }
                    st.session_state.current_skill_idx += 1
                    st.session_state.questions_per_skill = 0
                    if st.session_state.current_skill_idx >= len(skills):
                        st.session_state.phase = "planning"

            st.rerun()

# ── PHASE: PLANNING ────────────────────────────────────────────────────────────
elif st.session_state.phase == "planning":
    st.markdown("## 📚 Generating Your Personalised Learning Plan...")

    with st.spinner("🧠 AI is crafting your personalised learning journey..."):
        raw_plan = generate_learning_plan(st.session_state.skills_assessed, st.session_state.jd)
        try:
            clean = re.sub(r"```json|```", "", raw_plan).strip()
            plan  = json.loads(clean)
            st.session_state.learning_plan = plan
        except:
            st.session_state.learning_plan = {"error": "Could not parse plan", "raw": raw_plan}

    st.session_state.phase = "done"
    st.rerun()

# ── PHASE: DONE ────────────────────────────────────────────────────────────────
elif st.session_state.phase == "done":
    plan = st.session_state.learning_plan or {}

    st.markdown("## 🎉 Assessment Complete!")

    # Overall fit score
    fit_score = plan.get("overall_fit_score", 0)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🎯 Overall Fit Score", f"{fit_score}/100")
    with col2:
        assessed_count = len(st.session_state.skills_assessed)
        avg_score = sum(v["score"] for v in st.session_state.skills_assessed.values()) / max(assessed_count, 1)
        st.metric("📊 Avg Skill Score", f"{avg_score:.1f}/10")
    with col3:
        st.metric("✅ Skills Assessed", assessed_count)

    st.markdown(f"> 💡 **{plan.get('summary', 'Assessment complete. See your personalised learning plan below.')}**")

    # Scores visualization
    st.markdown("### 📊 Skill Assessment Results")
    cols = st.columns(min(len(st.session_state.skills_assessed), 4) or 1)
    for i, (skill, data) in enumerate(st.session_state.skills_assessed.items()):
        with cols[i % len(cols)]:
            score = data["score"]
            emoji = score_emoji(score)
            st.markdown(f"""
            <div class="skill-card">
                <b>{emoji} {skill}</b><br>
                <span class="{score_color(score)}">{score}/10</span> — {data.get('proficiency','')}<br>
                <small style="color:#888">{data.get('evidence','')[:60]}</small>
            </div>""", unsafe_allow_html=True)

    # Strengths
    if plan.get("strengths"):
        st.markdown("### 💪 Your Strengths")
        for s in plan["strengths"]:
            st.markdown(f"✅ {s}")

    # Priority gaps + learning plan
    st.markdown("### 📚 Personalised Learning Plan")
    for gap in plan.get("priority_gaps", []):
        with st.expander(f"🎯 {gap.get('skill','')} — Current: {gap.get('current_score','?')}/10 → Target: {gap.get('target_score','?')}/10 | ⏱️ {gap.get('total_time_estimate','?')}"):
            st.markdown(f"**Why this matters:** {gap.get('why_important','')}")
            st.markdown(f"**Learning Path:** {' → '.join(gap.get('learning_path',[]))}")
            st.markdown("**Recommended Resources:**")
            for res in gap.get("resources", []):
                st.markdown(f"- 📖 **{res.get('name','')}** ({res.get('type','')}) — {res.get('platform','')} | ⏱️ {res.get('duration','')}")

    # Quick wins
    if plan.get("quick_wins"):
        st.markdown("### ⚡ Quick Wins — Do This Week")
        for w in plan["quick_wins"]:
            st.markdown(f"→ {w}")

    # Timeline
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"🗓️ **30-Day Goal:** {plan.get('30_day_goal','')}")
    with col2:
        st.success(f"🏆 **90-Day Goal:** {plan.get('90_day_goal','')}")

    # Export
    st.divider()
    st.markdown("### 💾 Export Results")
    export_data = {
        "assessment_date": datetime.now().isoformat(),
        "skills_assessed": st.session_state.skills_assessed,
        "learning_plan": plan
    }
    st.download_button(
        "⬇️ Download Full Report (JSON)",
        data=json.dumps(export_data, indent=2),
        file_name="skilllens_report.json",
        mime="application/json",
        use_container_width=True
    )

    if st.button("🔄 Start New Assessment", use_container_width=True, type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
