"""MicroCourse Generator - Streamlit Application."""

import json

import streamlit as st

from generator import generate_course
from validators import validate_course
from export import course_to_markdown
from feedback import save_feedback, aggregate_feedback, load_all_feedback
from optimizer import get_active_rules

# ---------- Page config ----------
st.set_page_config(
    page_title="MicroCourse Generator",
    page_icon="📚",
    layout="wide",
)

st.title("MicroCourse Generator")
st.caption("AI-powered 10-15 minute micro-learning content generator")

# ---------- Session state init ----------
if "history" not in st.session_state:
    st.session_state.history = []
if "current_course" not in st.session_state:
    st.session_state.current_course = None

# ---------- Sidebar: session history ----------
with st.sidebar:
    st.header("Session History")
    if st.session_state.history:
        for i, entry in enumerate(reversed(st.session_state.history)):
            if st.button(entry["course_title"], key=f"hist_{i}"):
                st.session_state.current_course = entry
    else:
        st.info("Generated courses will appear here.")

# ---------- Input form ----------
with st.form("course_form"):
    topic = st.text_input(
        "Topic",
        placeholder="e.g., Introduction to API Security",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        audience_level = st.selectbox(
            "Audience Level",
            ["Beginner", "Intermediate", "Advanced"],
        )
    with col2:
        target_duration = st.slider(
            "Target Duration (minutes)",
            min_value=10,
            max_value=15,
            value=12,
        )
    with col3:
        tone = st.selectbox(
            "Tone",
            ["Professional", "Conversational", "Technical"],
        )

    additional_context = st.text_area(
        "Additional Context (optional)",
        placeholder="Any specific focus areas, constraints, or notes...",
    )

    submitted = st.form_submit_button("Generate Course", type="primary")

# ---------- Generation ----------
if submitted:
    if not topic.strip():
        st.error("Please enter a topic.")
    else:
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        except (KeyError, FileNotFoundError):
            api_key = ""
        if not api_key:
            st.error(
                "Anthropic API key not configured. "
                "Add `ANTHROPIC_API_KEY` to `.streamlit/secrets.toml`."
            )
        else:
            with st.spinner("Generating your micro-course..."):
                try:
                    course = generate_course(
                        api_key=api_key,
                        topic=topic,
                        audience_level=audience_level,
                        target_duration=target_duration,
                        tone=tone,
                        additional_context=additional_context,
                    )

                    errors = validate_course(course)
                    if errors:
                        st.warning(
                            "Course generated with schema warnings:\n- "
                            + "\n- ".join(errors)
                        )

                    st.session_state.current_course = course
                    st.session_state.history.append(course)

                except json.JSONDecodeError as e:
                    st.error(f"Failed to parse course output as JSON: {e}")
                except Exception as e:
                    import traceback
                    st.error(f"Generation failed: {type(e).__name__}: {e}")
                    st.code(traceback.format_exc())

# ---------- Render course ----------
course = st.session_state.current_course
if course:
    st.divider()
    st.header(course["course_title"])

    # Learning Objectives
    st.subheader("Learning Objectives")
    for obj in course["learning_objectives"]:
        st.markdown(f"- {obj}")

    # Modules
    words_per_minute = 150
    for i, module in enumerate(course["modules"], 1):
        word_count = len(module["content"].split()) + len(module["example"].split())
        reading_time = max(1, round(word_count / words_per_minute))

        with st.expander(f"Module {i}: {module['title']}  ({reading_time} min read)", expanded=(i == 1)):
            st.markdown(module["content"])

            st.markdown("#### Practical Example")
            st.markdown(module["example"])

            # Illustration rendering
            illustration = module.get("illustration")
            if illustration:
                if illustration["type"] == "mermaid" and illustration.get("mermaid"):
                    st.markdown("#### Diagram")
                    st.caption(illustration["alt_text"])
                    markup = illustration["mermaid"]["markup"]
                    # Render mermaid via st.markdown code block
                    st.code(markup, language="mermaid")

                elif illustration["type"] == "chart" and illustration.get("chart"):
                    chart_spec = illustration["chart"]
                    st.markdown(f"#### Chart: {chart_spec.get('title', '')}")
                    st.caption(illustration["alt_text"])
                    data = chart_spec.get("data", {})
                    labels = data.get("labels", [])
                    values = data.get("values", [])
                    if labels and values:
                        import pandas as pd
                        df = pd.DataFrame({
                            chart_spec.get("x_label", "Category"): labels,
                            chart_spec.get("y_label", "Value"): values,
                        })
                        chart_type = chart_spec.get("chart_type", "bar")
                        if chart_type == "bar":
                            st.bar_chart(df.set_index(chart_spec.get("x_label", "Category")))
                        elif chart_type == "line":
                            st.line_chart(df.set_index(chart_spec.get("x_label", "Category")))
                        else:
                            st.bar_chart(df.set_index(chart_spec.get("x_label", "Category")))

            # Comprehension check
            st.markdown("---")
            st.markdown("#### Comprehension Check")
            check = module["comprehension_check"]
            st.markdown(f"**Q:** {check['question']}")
            with st.popover("Show Answer"):
                st.markdown(check["answer"])

    # Summary
    st.subheader("Summary")
    st.markdown(course["summary"])

    # Next Steps
    st.subheader("Suggested Next Steps")
    for step in course["next_steps"]:
        st.markdown(f"- {step}")

    # ---------- Export ----------
    st.divider()
    st.subheader("Export")

    markdown_content = course_to_markdown(course)
    safe_title = course["course_title"].replace(" ", "_").replace("/", "-")[:50]

    col_md, col_json = st.columns(2)
    with col_md:
        st.download_button(
            label="Download Markdown",
            data=markdown_content,
            file_name=f"{safe_title}.md",
            mime="text/markdown",
        )
    with col_json:
        st.download_button(
            label="Download JSON",
            data=json.dumps(course, indent=2),
            file_name=f"{safe_title}.json",
            mime="application/json",
        )

    # ---------- Feedback form ----------
    st.divider()
    st.subheader("Course Feedback")
    st.caption("Help us improve future courses by sharing your experience.")

    feedback_key = f"feedback_{course['course_title']}"
    if feedback_key in st.session_state:
        st.success("Thank you for your feedback!")
    else:
        with st.form("feedback_form"):
            overall_rating = st.slider(
                "Overall Rating", min_value=1, max_value=5, value=4
            )

            difficulty = st.radio(
                "Difficulty Calibration",
                ["Too easy", "Just right", "Too advanced"],
                index=1,
                horizontal=True,
            )

            # Per-module thumbs up/down
            st.markdown("**Module Usefulness**")
            module_ratings = {}
            for mod in course["modules"]:
                module_ratings[mod["title"]] = st.checkbox(
                    f"Thumbs up: {mod['title']}", value=True,
                    key=f"mod_{mod['title']}",
                )

            # Illustration helpfulness (only if illustrations exist)
            illustration_ratings = {}
            modules_with_illustrations = [
                m for m in course["modules"] if m.get("illustration")
            ]
            if modules_with_illustrations:
                st.markdown("**Illustration Helpfulness**")
                for mod in modules_with_illustrations:
                    illustration_ratings[mod["title"]] = st.checkbox(
                        f"Helpful: {mod['title']} illustration", value=True,
                        key=f"ill_{mod['title']}",
                    )

            comments = st.text_area(
                "Comments (optional)",
                placeholder="What was most or least helpful?",
            )

            feedback_submitted = st.form_submit_button("Submit Feedback")

        if feedback_submitted:
            feedback_data = {
                "topic": course.get("course_title", ""),
                "audience_level": course.get("audience_level", ""),
                "course_title": course["course_title"],
                "overall_rating": overall_rating,
                "difficulty": difficulty,
                "module_ratings": module_ratings,
                "illustration_ratings": illustration_ratings,
                "comments": comments,
            }
            save_feedback(feedback_data)
            st.session_state[feedback_key] = True
            st.rerun()

# ---------- Optimization Dashboard (sidebar) ----------
with st.sidebar:
    st.divider()
    st.header("Improvement Loop")
    all_feedback = load_all_feedback()
    if all_feedback:
        agg = aggregate_feedback(all_feedback)
        st.metric("Total Feedback", agg["total_count"])
        st.metric("Avg Rating", f"{agg['global_avg_rating']}/5")

        if agg["difficulty_distribution"]:
            st.caption("Difficulty Distribution")
            diff_items = agg["difficulty_distribution"]
            for label, count in diff_items.items():
                st.text(f"  {label}: {count}")

        rules = get_active_rules()
        if rules:
            st.caption("Active Optimization Rules")
            for rule in rules:
                st.text(f"[{rule['level']}] {rule['description'][:60]}")
    else:
        st.info("No feedback yet. Generate and review a course to start the improvement loop.")
