# Product Requirements Document

## MicroCourse Generator Agent

*AI-Powered 10–15 Minute Micro-Learning Content Generator*

**Version:** 1.0  
**Date:** 2026-04-14  
**Status:** Draft  
**Classification:** Internal

---

## 1. Overview

This PRD defines the requirements for an AI-powered agent that generates structured micro-course learning materials from a user-supplied topic. Each generated course is designed to be consumed in 10–15 minutes and includes learning objectives, lesson content, comprehension checks, and a summary. The application will be built in Python and hosted on Streamlit Community Cloud.

## 2. Problem Statement

Creating effective short-form learning content is time-consuming and requires instructional design expertise. Subject matter experts often have the knowledge but lack the time or pedagogical training to structure it into digestible micro-courses. This agent automates the instructional design process, transforming a plain-language topic into a ready-to-use learning module in seconds.

## 3. Goals and Success Metrics

### 3.1 Goals

- Reduce micro-course authoring time from hours to under 60 seconds
- Produce consistently structured, pedagogically sound learning modules
- Enable non-instructional-designers to generate quality training content
- Provide a low-friction Streamlit-based interface requiring no local setup

### 3.2 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Generation latency | < 30 seconds per course | Streamlit logs / API timing |
| User satisfaction | ≥ 4.0 / 5.0 rating | In-app feedback widget |
| Content completeness | 100% of sections populated | Automated output validation |
| Adoption | 50+ courses generated in first 30 days | Usage analytics |
| Improvement loop impact | Optimized courses rate ≥ 0.3 stars higher than baseline | A/B feedback comparison |

## 4. Target Users

- Subject matter experts needing to create quick training materials
- L&D / training teams seeking to accelerate content pipelines
- Managers building onboarding or upskilling modules for their teams
- Internal teams requiring rapid knowledge-sharing artifacts

## 5. Functional Requirements

### 5.1 Input Interface

The Streamlit application will present a clean input form with the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Topic | Text input | Yes | The subject of the micro-course (e.g., "Introduction to API Security") |
| Audience Level | Select box | Yes | Beginner / Intermediate / Advanced |
| Target Duration | Slider | Yes | 10–15 minutes (default: 12) |
| Tone | Select box | No | Professional / Conversational / Technical (default: Professional) |
| Additional Context | Text area | No | Optional notes, constraints, or focus areas |

### 5.2 Course Generation Engine

Upon submission, the agent calls the Anthropic Messages API (Claude Sonnet) with a structured system prompt that enforces the following output schema:

1. **Course Title** – A concise, descriptive title
2. **Learning Objectives** – 3–5 measurable objectives (Bloom's Taxonomy aligned)
3. **Lesson Modules** – 3–5 modules, each containing a module title, key concepts (2–4 paragraphs), a practical example or scenario, and a single comprehension check question with answer
4. **Illustrations** – Conditional chart data (JSON) for quantitative content and/or Mermaid diagram markup for process/interaction content
5. **Summary** – Key takeaways recap
6. **Suggested Next Steps** – 2–3 recommendations for further learning

The system prompt will instruct the model to calibrate vocabulary, depth, and examples to the selected audience level and tone.

### 5.3 Output Rendering

Generated content will be rendered in the Streamlit UI using the following display components:

- Expandable sections (`st.expander`) for each lesson module
- Styled markdown rendering for headings, lists, and emphasis
- A collapsible "Quiz" section with reveal-on-click answers
- Visual progress indicator showing estimated reading time per module

### 5.4 Export Options

- **Markdown (.md)** – download the full course as a single markdown file
- **PDF** – rendered via a markdown-to-PDF conversion library (e.g., weasyprint or md2pdf)
- **JSON** – structured output for integration with LMS or Content Lake systems

### 5.5 Session History

Streamlit session state will maintain a history of generated courses for the current session, allowing users to revisit, compare, or regenerate previous topics without re-entering parameters.

### 5.6 Auto-Generated Illustrations

The agent will generate contextual illustrations to accompany lesson content where visual aids improve comprehension. Two categories of illustrations are supported:

#### 5.6.1 Quantitative Data Visualizations

When a lesson module involves quantitative concepts (statistics, trends, comparisons, distributions), the agent will generate chart specifications as part of the structured output. The application will render these using Matplotlib or Plotly within the Streamlit UI. Supported chart types include bar charts, line graphs, pie charts, scatter plots, and simple histograms. The generation prompt will instruct the model to produce chart data as JSON arrays with axis labels, titles, and annotation notes, which the rendering layer will consume.

#### 5.6.2 Physical Interaction and Process Diagrams

For topics involving physical systems, workflows, cause-and-effect relationships, or spatial interactions, the agent will generate Mermaid diagram markup embedded in the structured output. Supported diagram types include flowcharts, sequence diagrams, state diagrams, and simple entity-relationship diagrams. The Streamlit app will render these via the streamlit-mermaid component or by converting Mermaid markup to SVG at render time. This approach avoids the need for image generation models while still providing clear, accurate visual representations of processes and interactions.

Illustration generation will be conditional: the system prompt will instruct the model to include visual specifications only when they materially enhance understanding, not as decoration. Each illustration will include an alt-text description for accessibility.

### 5.7 Continuous Improvement Loop

The agent will implement a feedback-driven improvement loop that captures learner responses at the end of each generated course and uses that signal to optimize future course generation. This transforms the system from a stateless generator into one that learns from its output quality over time.

#### 5.7.1 End-of-Course Feedback Collection

Upon completing a generated course, learners will be presented with a lightweight feedback form embedded in the Streamlit UI. The form will capture:

- Overall rating (1–5 stars)
- Per-module usefulness ratings (thumbs up/down per section)
- Difficulty calibration ("Too easy" / "Just right" / "Too advanced")
- Comprehension check accuracy (did the learner answer correctly?)
- Free-text comments on what was most/least helpful
- Whether illustrations aided understanding (per illustration, if present)

#### 5.7.2 Feedback Storage and Aggregation

Feedback records will be stored as structured JSON, keyed by course topic, audience level, and generation timestamp. In the MVP, feedback will be persisted using a lightweight store (SQLite for local development, or a JSON-lines file on the Streamlit server). In Phase 3, this migrates to the Content Lake or a dedicated feedback table in Supabase/PostgreSQL. An aggregation layer will compute rolling metrics per topic category including average rating, difficulty calibration distribution, most-downvoted module positions, and comprehension check pass rates.

#### 5.7.3 Prompt Optimization Engine

Aggregated feedback will be injected into the system prompt as contextual guidance for future generation. The optimization operates at three levels:

1. **Global patterns** – System-wide trends (e.g., "Learners consistently rate Module 3 lowest; ensure the third module includes a concrete worked example") are appended to the base system prompt as standing instructions.
2. **Topic-category patterns** – When generating a course in a topic area that has prior feedback (e.g., "API Security" courses are consistently rated "Too advanced" for Beginner audiences), the prompt is augmented with category-specific calibration notes.
3. **Illustration effectiveness** – If feedback indicates diagrams or charts in a topic category were not useful, the prompt will deprioritize visual generation for similar topics. Conversely, if visuals were highly rated, the prompt will encourage richer illustration specs.

The optimization engine does not fine-tune the model itself. It operates entirely through dynamic prompt augmentation, making it transparent, auditable, and easy to override. A dashboard view will surface the current active optimization rules so course authors can review and manually approve or suppress specific prompt adjustments.

#### 5.7.4 A/B Variant Testing (Phase 2+)

In Phase 2 and beyond, the system can optionally generate two variants of a course for the same topic: one using the baseline prompt and one incorporating optimization rules. By comparing feedback scores across variants, the system can validate whether prompt adjustments are genuinely improving course quality before promoting them to the default prompt configuration.

## 6. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | End-to-end generation completes in < 30 seconds for typical topics |
| Scalability | Streamlit Community Cloud supports concurrent users; API rate limits managed via exponential backoff |
| Security | API key stored in Streamlit secrets management (st.secrets); never exposed in client code or repo |
| Availability | Dependent on Streamlit Cloud SLA and Anthropic API uptime; no custom HA required for MVP |
| Accessibility | Semantic HTML output; screen-reader-compatible Streamlit components |
| Maintainability | Modular Python codebase; prompt templates externalized as YAML/JSON config files |

## 7. Technical Architecture

### 7.1 Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Framework | Streamlit |
| AI Model | Claude Sonnet 4.6 via Anthropic Messages API |
| SDK | anthropic (Python SDK) |
| Export – PDF | weasyprint or md2pdf |
| Export – Markdown | Native string generation |
| Illustrations – Charts | Matplotlib / Plotly (rendered in Streamlit) |
| Illustrations – Diagrams | Mermaid markup (via streamlit-mermaid or SVG conversion) |
| Config Management | YAML prompt templates + Streamlit secrets |
| Hosting | Streamlit Community Cloud (free tier) |
| Source Control | GitHub (public or private repo) |

### 7.2 Application Flow

1. User opens Streamlit app URL in browser
2. User enters topic, selects audience level, duration, and optional parameters
3. User clicks "Generate Course"
4. App constructs prompt from template + user inputs
5. App calls Anthropic Messages API with structured system prompt
6. API response is parsed (JSON mode) and validated against expected schema
7. Illustration specs (if present) are rendered: chart data via Matplotlib/Plotly, diagrams via Mermaid
8. Validated content and rendered illustrations are displayed in Streamlit UI with expandable modules
9. User reviews content, optionally exports as Markdown / PDF / JSON
10. Course is added to session history sidebar
11. Learner completes end-of-course feedback form (ratings, difficulty, comments)
12. Feedback is stored and aggregated; optimization engine updates prompt rules if thresholds are met
13. Subsequent course generations incorporate active optimization rules in the system prompt

### 7.3 Project Structure

```
microcourse-generator/
├── app.py                  # Main Streamlit application
├── generator.py             # API call logic and prompt construction
├── prompts/
│   ├── system_prompt.yaml   # System prompt template
│   └── output_schema.json   # Expected JSON output schema
├── data/
│   ├── feedback.jsonl       # Feedback records (MVP flat-file store)
│   └── optimization_rules.json  # Active prompt optimization rules
├── export.py                # Markdown, PDF, JSON export logic
├── illustrations.py         # Chart rendering (Matplotlib/Plotly) and Mermaid SVG conversion
├── feedback.py              # Feedback collection, storage, and aggregation
├── optimizer.py             # Prompt optimization engine (feedback-to-prompt rules)
├── validators.py            # Output schema validation
├── requirements.txt         # Python dependencies
├── .streamlit/
│   └── secrets.toml         # API key (local dev only)
└── README.md                # Setup and usage docs
```

## 8. Prompt Engineering Strategy

The quality of generated courses depends heavily on prompt design. The system prompt will incorporate the following techniques:

- **Role assignment:** Instruct the model to act as an experienced instructional designer
- **Structured output:** Request JSON-formatted response matching a predefined schema
- **Audience calibration:** Dynamically adjust vocabulary, abstraction level, and example complexity based on the selected audience level
- **Bloom's Taxonomy alignment:** Require learning objectives to use action verbs from the appropriate cognitive level
- **Time-boxing:** Instruct the model to target word counts corresponding to the selected duration (~150 words per minute reading speed)
- **Few-shot examples:** Include one exemplar course structure in the system prompt for consistency
- **Dynamic optimization:** Append aggregated learner feedback signals (see Section 5.7) as contextual calibration notes to improve course quality over time

## 9. MVP Scope and Phasing

### 9.1 MVP (Phase 1)

- Single-topic course generation with all five output sections
- Streamlit UI with input form and rendered output
- Markdown export
- Deployed on Streamlit Community Cloud

### 9.2 Phase 2 Enhancements

- PDF and JSON export options
- Session history with sidebar navigation
- End-of-course feedback collection with per-module ratings and difficulty calibration
- Prompt optimization engine – aggregated feedback drives dynamic prompt augmentation
- A/B variant testing to validate optimization rule effectiveness
- Optimization rules dashboard for manual review and override
- Prompt template customization via admin panel
- Usage analytics and feedback collection

### 9.3 Phase 3 – Integration

- API endpoint mode (FastAPI wrapper) for programmatic access
- Content Lake integration – store generated courses as markdown in S3/Supabase
- Feedback store migration – move from flat-file to Supabase/PostgreSQL for cross-session and multi-user feedback aggregation
- Moodle LMS integration – export courses as SCORM 1.2/2004 packages or Moodle XML format for direct import into Moodle course structures
- Moodle quiz mapping – convert comprehension check questions to Moodle Quiz activity format (GIFT or Moodle XML) for automated grading
- Multi-course curriculum builder (sequence of related micro-courses mapped to Moodle course categories)
- Migration to Next.js frontend if integrated into broader web experience layer

## 10. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Hallucinated content | Medium | Incorrect learning material distributed | SME review step; disclaimer in output |
| API rate limits | Low | Degraded availability under load | Exponential backoff; usage caps |
| Prompt injection via topic input | Low | Unexpected model behavior | Input sanitization; constrained system prompt |
| API cost overrun | Medium | Unexpected billing | Token usage tracking; monthly budget alerts |
| Streamlit Cloud downtime | Low | App unavailable | No mitigation needed for MVP |

## 11. Dependencies

- Anthropic API account with active API key and sufficient usage quota
- GitHub repository (public or private) connected to Streamlit Community Cloud
- Python 3.11+ runtime (provided by Streamlit Cloud)
- Claude Code for initial project scaffolding and iterative development

## 12. Estimated Timeline

| Phase | Deliverable | Duration |
|-------|-------------|----------|
| Week 1 | Project scaffolding, prompt engineering, core generation logic | 3–5 working sessions |
| Week 2 | Streamlit UI, markdown export, Streamlit Cloud deployment | 3–4 working sessions |
| Week 3 | Testing, prompt refinement, user feedback collection | 2–3 working sessions |
| Week 4+ | Phase 2 enhancements based on feedback | Ongoing |

## 13. Open Questions

### 13.1 Resolved

- **Auto-generated illustrations:** Yes – the agent will generate Matplotlib/Plotly charts for quantitative data and Mermaid diagrams for physical interactions and process flows. See Section 5.6.
- **Target LMS platform:** Moodle – Phase 3 will target SCORM and Moodle XML export formats for direct course import. See Section 9.3.

### 13.2 Outstanding

- Should the agent support multi-language course generation?
- What review/approval workflow (if any) is needed before courses are published?
- Should the Content Lake integration use the existing S3/Supabase infrastructure from the web scraper project?
