"""Prompt optimization engine - converts aggregated feedback into prompt hints."""

from feedback import aggregate_feedback, load_all_feedback

MIN_RECORDS_FOR_OPTIMIZATION = 3


def generate_optimization_hints(topic: str = "", audience_level: str = "") -> str:
    """Build prompt augmentation text from aggregated feedback.

    Returns a string to append to the system prompt. Returns empty string
    if there is insufficient feedback data.

    Operates at three levels per the PRD:
    1. Global patterns - system-wide trends
    2. Topic-category patterns - topic + audience specific calibration
    3. Illustration effectiveness - visual generation guidance
    """
    records = load_all_feedback()
    if len(records) < MIN_RECORDS_FOR_OPTIMIZATION:
        return ""

    agg = aggregate_feedback(records)
    hints = []

    # --- Level 1: Global patterns ---
    global_hints = _global_hints(agg)
    if global_hints:
        hints.append("## Optimization Notes (from learner feedback)\n")
        hints.extend(global_hints)

    # --- Level 2: Topic-category patterns ---
    topic_hints = _topic_hints(agg, topic, audience_level)
    if topic_hints:
        hints.append("")
        hints.extend(topic_hints)

    # --- Level 3: Illustration effectiveness ---
    illustration_hints = _illustration_hints(agg, topic)
    if illustration_hints:
        hints.append("")
        hints.extend(illustration_hints)

    return "\n".join(hints)


def _global_hints(agg: dict) -> list[str]:
    """Generate system-wide optimization hints."""
    hints = []

    # Identify weak module positions
    position_scores = agg.get("module_position_scores", {})
    for pos, scores in sorted(position_scores.items(), key=lambda x: int(x[0])):
        total = scores["up"] + scores["down"]
        if total >= MIN_RECORDS_FOR_OPTIMIZATION and scores["down"] > scores["up"]:
            ratio = round(scores["down"] / total * 100)
            hints.append(
                f"- Module {pos} is rated negatively {ratio}% of the time. "
                f"Ensure module {pos} includes a concrete worked example and clear transitions."
            )

    # Global difficulty skew
    diff_dist = agg.get("difficulty_distribution", {})
    total_diff = sum(diff_dist.values())
    if total_diff >= MIN_RECORDS_FOR_OPTIMIZATION:
        too_advanced = diff_dist.get("Too advanced", 0)
        too_easy = diff_dist.get("Too easy", 0)
        if too_advanced / total_diff > 0.4:
            hints.append(
                "- Learners frequently report courses as 'Too advanced'. "
                "Simplify language and add more foundational context."
            )
        elif too_easy / total_diff > 0.4:
            hints.append(
                "- Learners frequently report courses as 'Too easy'. "
                "Increase depth, add nuance, and include more challenging examples."
            )

    return hints


def _topic_hints(agg: dict, topic: str, audience_level: str) -> list[str]:
    """Generate topic + audience specific calibration hints."""
    if not topic:
        return []

    hints = []
    by_topic = agg.get("by_topic", {})

    # Look for matching topic entries (partial match on topic name)
    topic_lower = topic.lower()
    for key, data in by_topic.items():
        if topic_lower in key.lower() and data["count"] >= MIN_RECORDS_FOR_OPTIMIZATION:
            diff = data.get("difficulty_distribution", {})
            total = sum(diff.values())
            if total > 0:
                too_advanced = diff.get("Too advanced", 0)
                too_easy = diff.get("Too easy", 0)
                if too_advanced / total > 0.4:
                    hints.append(
                        f"- Prior feedback for \"{key}\" indicates the content was too advanced. "
                        f"Calibrate down: use simpler vocabulary and more scaffolding."
                    )
                elif too_easy / total > 0.4:
                    hints.append(
                        f"- Prior feedback for \"{key}\" indicates the content was too easy. "
                        f"Increase complexity and include expert-level insights."
                    )

            if data["avg_rating"] < 3.0:
                hints.append(
                    f"- Courses on \"{key}\" have a low average rating ({data['avg_rating']}/5). "
                    f"Focus on practical relevance and clearer explanations."
                )

    return hints


def _illustration_hints(agg: dict, topic: str) -> list[str]:
    """Generate illustration effectiveness hints."""
    hints = []
    ill_eff = agg.get("illustration_effectiveness", {})

    # Check topic-specific illustration feedback
    topic_lower = topic.lower() if topic else ""
    for ill_topic, scores in ill_eff.items():
        total = scores["helpful"] + scores["not_helpful"]
        if total < MIN_RECORDS_FOR_OPTIMIZATION:
            continue

        if topic_lower and topic_lower not in ill_topic.lower():
            continue

        helpful_ratio = scores["helpful"] / total
        if helpful_ratio < 0.4:
            hints.append(
                f"- Illustrations for \"{ill_topic}\" topics were rated unhelpful. "
                f"Deprioritize visual generation or use simpler diagram styles."
            )
        elif helpful_ratio > 0.7:
            hints.append(
                f"- Illustrations for \"{ill_topic}\" topics were rated highly helpful. "
                f"Include richer, more detailed visual specifications."
            )

    return hints


def get_active_rules() -> list[dict]:
    """Return a summary of currently active optimization rules for the dashboard.

    Each rule is a dict with 'level', 'description', and 'based_on' count.
    """
    records = load_all_feedback()
    if len(records) < MIN_RECORDS_FOR_OPTIMIZATION:
        return []

    agg = aggregate_feedback(records)
    rules = []

    for hint in _global_hints(agg):
        rules.append({"level": "Global", "description": hint.lstrip("- "), "based_on": agg["total_count"]})

    for key, data in agg.get("by_topic", {}).items():
        if data["count"] >= MIN_RECORDS_FOR_OPTIMIZATION and data["avg_rating"] < 3.0:
            rules.append({
                "level": "Topic",
                "description": f"Low rating for \"{key}\" ({data['avg_rating']}/5)",
                "based_on": data["count"],
            })

    for topic, scores in agg.get("illustration_effectiveness", {}).items():
        total = scores["helpful"] + scores["not_helpful"]
        if total >= MIN_RECORDS_FOR_OPTIMIZATION:
            ratio = round(scores["helpful"] / total * 100)
            rules.append({
                "level": "Illustration",
                "description": f"\"{topic}\" illustrations rated {ratio}% helpful",
                "based_on": total,
            })

    return rules
