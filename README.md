# 🎯 SkillLens AI — Skill Assessment & Personalised Learning Plan Agent

> **Catalyst Hackathon Submission · deccan.ai · April 2026**

## 🚀 Live Demo
🔗 **[Try it live on Streamlit Cloud](your-streamlit-url-here)**

---

## 📌 What it does

**SkillLens AI** is an agentic AI system that:

1. **Extracts** required skills from a Job Description and candidate's resume
2. **Conversationally assesses** real proficiency for each skill — not just what's on paper
3. **Scores** each skill (1–10) with evidence and proficiency level
4. **Generates** a personalised learning plan with curated resources and time estimates
5. **Exports** a full JSON report for download

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│              (Streamlit Web Application)                 │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  ORCHESTRATION LAYER                     │
│   Phase Manager: Setup → Extract → Assess → Plan → Done │
└──────┬──────────────┬───────────────┬───────────────────┘
       │              │               │
       ▼              ▼               ▼
┌──────────┐  ┌──────────────┐  ┌────────────────────┐
│  SKILL   │  │  ASSESSMENT  │  │  LEARNING PLAN     │
│EXTRACTOR │  │    AGENT     │  │    GENERATOR       │
│          │  │              │  │                    │
│ Parses   │  │ Conversatio- │  │ Gap analysis       │
│ JD &     │  │ nal Q&A per  │  │ Resource curation  │
│ Resume   │  │ skill        │  │ Timeline estimates │
│ → JSON   │  │ Auto-scores  │  │ Learning paths     │
└────┬─────┘  └──────┬───────┘  └─────────┬──────────┘
     │               │                     │
     └───────────────┼─────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   ANTHROPIC CLAUDE API │
        │   (claude-opus-4-5)    │
        └────────────────────────┘
```

---

## 🧠 Scoring Logic

| Score | Level | Description |
|-------|-------|-------------|
| 1–3   | Beginner | Never used or very limited exposure |
| 4–6   | Intermediate | Used in projects, some practical experience |
| 7–9   | Advanced | Deep practical experience, can mentor others |
| 10    | Expert | Industry-level mastery, thought leader |

The agent uses **progressive questioning** — starts with conceptual understanding, then goes deeper with practical/scenario-based questions. Score is inferred from quality and depth of answers.

---

## ⚙️ Assessment Agent Flow

```
JD + Resume Input
      │
      ▼
[Skill Extractor Agent]
  → Parses required skills from JD
  → Maps against candidate resume
  → Identifies claimed vs. required gaps
      │
      ▼
[Conversational Assessment Agent]
  For each required skill:
    Q1: Conceptual understanding
    Q2: Practical application example
    Q3 (if needed): Edge case / depth check
  → Auto-scores based on response quality
      │
      ▼
[Learning Plan Generator Agent]
  → Identifies priority gaps
  → Finds adjacent learnable skills
  → Curates specific resources
  → Estimates realistic timelines
  → Sets 30-day and 90-day goals
      │
      ▼
Downloadable JSON Report
```

---

## 🚀 Run Locally

### Prerequisites
- Python 3.9+
- Anthropic API key ([Get one here](https://console.anthropic.com))

### Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/skilllens-ai
cd skilllens-ai

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

Then open http://localhost:8501 in your browser.
Enter your Anthropic API key in the sidebar and start assessing!

---

## 📦 Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| AI Engine | Anthropic Claude (claude-opus-4-5) |
| Language | Python 3.9+ |
| Deployment | Streamlit Cloud |
| API | Anthropic Messages API |

---

## 📊 Sample Input / Output

### Input — Job Description
```
Senior QA Engineer — BFSI Domain
Requirements:
- 4+ years manual testing experience
- BFSI/Capital Markets domain knowledge
- JIRA, HP ALM for test management
- SQL for database validation
- API testing with Postman
- Agile/Scrum methodology
- Selenium automation (preferred)
```

### Input — Resume
```
Shyam Kumar | QA Analyst | TCS
4 years experience at MCX (commodity exchange)
Skills: Manual Testing, JIRA, ALM, SQL, Postman, SEBI Compliance
Experience: Collateral Management, Clearing & Settlement testing
```

### Output — Assessment Scores
```json
{
  "Manual Testing": {"score": 8, "proficiency": "Advanced"},
  "BFSI Domain": {"score": 9, "proficiency": "Advanced"},
  "JIRA": {"score": 7, "proficiency": "Advanced"},
  "SQL": {"score": 6, "proficiency": "Intermediate"},
  "API Testing": {"score": 6, "proficiency": "Intermediate"},
  "Selenium": {"score": 3, "proficiency": "Beginner"}
}
```

### Output — Learning Plan (excerpt)
```json
{
  "overall_fit_score": 78,
  "priority_gaps": [{
    "skill": "Selenium",
    "current_score": 3,
    "target_score": 7,
    "total_time_estimate": "6-8 weeks",
    "resources": [
      {"name": "Selenium WebDriver with Java", "platform": "Udemy", "duration": "3 weeks"},
      {"name": "Test Automation University", "platform": "Applitools", "duration": "2 weeks"}
    ],
    "30_day_goal": "Complete basic Selenium course and write 10 automated test cases"
  }]
}
```

---

## 🏆 Judging Criteria Addressed

| Criteria | How SkillLens addresses it |
|----------|---------------------------|
| End-to-end working | Full pipeline from JD+Resume → Assessment → Plan |
| Core agent quality | Multi-phase agent with state management |
| Output quality | Scored assessments + detailed learning plans |
| Technical implementation | Clean Python, Streamlit, Anthropic API |
| Innovation | Conversational assessment (not just parsing) |
| UX | Intuitive UI, progress tracking, color-coded scores |
| Clean code | Documented, structured, modular |

---

## 📁 Repository Structure

```
skilllens-ai/
├── app.py              # Main application
├── requirements.txt    # Dependencies
├── README.md           # This file
└── samples/
    ├── sample_jd.txt   # Example job description
    └── sample_resume.txt # Example resume
```

---

## 👨‍💻 Built by
**Shyam Kumar Siringi** | QA Analyst & Business Analyst
- 4 years experience in BFSI/Capital Markets at MCX via TCS
- LinkedIn: linkedin.com/in/shyam-kumar-siringi-465005370

---

*Built for Catalyst Hackathon by deccan.ai · April 2026*
