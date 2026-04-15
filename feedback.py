"""Feedback collection, storage, and aggregation for the improvement loop."""

import json
import time
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent / "data"
FEEDBACK_FILE = DATA_DIR / "feedback.jsonl"


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_feedback(feedback: dict) -> None:
    """Append a feedback record as a JSON line.

    Expected feedback dict keys:
        topic: str
        audience_level: str
        course_title: str
        overall_rating: int (1-5)
        difficulty: str ("Too easy" | "Just right" | "Too advanced")
        module_ratings: dict[str, bool]  # module title -> thumbs up (True) / down (False)
        illustration_ratings: dict[str, bool]  # module title -> helpful (True/False)
        comments: str
        timestamp: float (auto-set if missing)
    """
    _ensure_data_dir()
    record = dict(feedback)
    if "timestamp" not in record:
        record["timestamp"] = time.time()
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_all_feedback() -> list[dict]:
    """Load all feedback records from the JSONL file."""
    if not FEEDBACK_FILE.exists():
        return []
    records = []
    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def aggregate_feedback(records: list[dict] | None = None) -> dict:
    """Compute rolling metrics from feedback records.

    Returns a dict with:
        global_avg_rating: float
        total_count: int
        difficulty_distribution: dict[str, int]
        by_topic: dict[topic, {avg_rating, count, difficulty_distribution}]
        module_position_scores: dict[int, {up, down}]  (1-indexed position)
        illustration_effectiveness: dict[topic, {helpful, not_helpful}]
    """
    if records is None:
        records = load_all_feedback()

    if not records:
        return {
            "global_avg_rating": 0.0,
            "total_count": 0,
            "difficulty_distribution": {},
            "by_topic": {},
            "module_position_scores": {},
            "illustration_effectiveness": {},
        }

    # Global metrics
    ratings = [r["overall_rating"] for r in records if "overall_rating" in r]
    global_avg = sum(ratings) / len(ratings) if ratings else 0.0

    difficulty_dist = defaultdict(int)
    for r in records:
        if "difficulty" in r:
            difficulty_dist[r["difficulty"]] += 1

    # Per-topic metrics
    by_topic = defaultdict(lambda: {"ratings": [], "difficulty": defaultdict(int)})
    for r in records:
        topic = r.get("topic", "Unknown")
        level = r.get("audience_level", "")
        key = f"{topic} [{level}]" if level else topic
        if "overall_rating" in r:
            by_topic[key]["ratings"].append(r["overall_rating"])
        if "difficulty" in r:
            by_topic[key]["difficulty"][r["difficulty"]] += 1

    topic_summary = {}
    for key, data in by_topic.items():
        topic_ratings = data["ratings"]
        topic_summary[key] = {
            "avg_rating": sum(topic_ratings) / len(topic_ratings) if topic_ratings else 0.0,
            "count": len(topic_ratings),
            "difficulty_distribution": dict(data["difficulty"]),
        }

    # Module position scores (which module positions get thumbs up/down)
    position_scores = defaultdict(lambda: {"up": 0, "down": 0})
    for r in records:
        module_ratings = r.get("module_ratings", {})
        for i, (_, vote) in enumerate(module_ratings.items()):
            pos = i + 1
            if vote:
                position_scores[pos]["up"] += 1
            else:
                position_scores[pos]["down"] += 1

    # Illustration effectiveness per topic
    illustration_eff = defaultdict(lambda: {"helpful": 0, "not_helpful": 0})
    for r in records:
        topic = r.get("topic", "Unknown")
        for _, helpful in r.get("illustration_ratings", {}).items():
            if helpful:
                illustration_eff[topic]["helpful"] += 1
            else:
                illustration_eff[topic]["not_helpful"] += 1

    return {
        "global_avg_rating": round(global_avg, 2),
        "total_count": len(records),
        "difficulty_distribution": dict(difficulty_dist),
        "by_topic": topic_summary,
        "module_position_scores": {k: dict(v) for k, v in position_scores.items()},
        "illustration_effectiveness": {k: dict(v) for k, v in illustration_eff.items()},
    }
