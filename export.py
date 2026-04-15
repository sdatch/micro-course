"""Export generated courses to Markdown format."""


def course_to_markdown(course: dict) -> str:
    """Convert a structured course dictionary to a formatted markdown string."""
    lines = []

    # Title
    lines.append(f"# {course['course_title']}")
    lines.append("")

    # Learning Objectives
    lines.append("## Learning Objectives")
    lines.append("")
    for obj in course["learning_objectives"]:
        lines.append(f"- {obj}")
    lines.append("")

    # Modules
    for i, module in enumerate(course["modules"], 1):
        lines.append(f"## Module {i}: {module['title']}")
        lines.append("")
        lines.append(module["content"])
        lines.append("")

        # Example
        lines.append("### Practical Example")
        lines.append("")
        lines.append(module["example"])
        lines.append("")

        # Illustration
        illustration = module.get("illustration")
        if illustration:
            if illustration["type"] == "mermaid" and illustration.get("mermaid"):
                lines.append("### Diagram")
                lines.append("")
                lines.append(f"*{illustration['alt_text']}*")
                lines.append("")
                lines.append("```mermaid")
                lines.append(illustration["mermaid"]["markup"])
                lines.append("```")
                lines.append("")
            elif illustration["type"] == "chart" and illustration.get("chart"):
                chart = illustration["chart"]
                lines.append(f"### Chart: {chart.get('title', 'Data Visualization')}")
                lines.append("")
                lines.append(f"*{illustration['alt_text']}*")
                lines.append("")
                # Render chart data as a simple markdown table
                data = chart.get("data", {})
                labels = data.get("labels", [])
                values = data.get("values", [])
                if labels and values:
                    x_label = chart.get("x_label", "Category")
                    y_label = chart.get("y_label", "Value")
                    lines.append(f"| {x_label} | {y_label} |")
                    lines.append("|---|---|")
                    for label, value in zip(labels, values):
                        lines.append(f"| {label} | {value} |")
                    lines.append("")

        # Comprehension Check
        check = module["comprehension_check"]
        lines.append("### Comprehension Check")
        lines.append("")
        lines.append(f"**Q:** {check['question']}")
        lines.append("")
        lines.append(f"<details><summary>Show Answer</summary>\n\n{check['answer']}\n\n</details>")
        lines.append("")

        lines.append("---")
        lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(course["summary"])
    lines.append("")

    # Next Steps
    lines.append("## Suggested Next Steps")
    lines.append("")
    for step in course["next_steps"]:
        lines.append(f"- {step}")
    lines.append("")

    return "\n".join(lines)
