"""MicroCourse Generator - Streamlit Application."""

import json

import streamlit as st

from generator import generate_course
from validators import validate_course
from export import course_to_markdown

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
