"""Measurement: log results by hand or from a CSV, and turn them into lessons."""
import pandas as pd

from . import memory
from .llm import chat_json


def mark_published(mem, draft_id, url=""):
    draft = memory.find(mem, "drafts", draft_id)
    draft["status"] = "published"
    draft["url"] = url
    memory.save(mem)


def log_metrics(mem, draft_id, impressions, reactions, comments):
    if not memory.find(mem, "drafts", draft_id):
        raise KeyError(f"No draft with id {draft_id}")
    return memory.add(mem, "metrics", {
        "draft_id": draft_id, "impressions": impressions, "reactions": reactions, "comments": comments,
    })


def import_csv(mem, path):
    """CSV columns: draft_id, impressions, reactions, comments."""
    df = pd.read_csv(path)
    for r in df.itertuples():
        log_metrics(mem, str(r.draft_id), int(r.impressions), int(r.reactions), int(r.comments))
    return len(df)


def leaderboard(mem):
    latest = {m["draft_id"]: m for m in mem["metrics"]}  # last entry per draft wins
    rows = []
    for draft_id, m in latest.items():
        draft = memory.find(mem, "drafts", draft_id)
        rate = (m["reactions"] + m["comments"]) / max(m["impressions"], 1)
        rows.append({
            "draft_id": draft_id,
            "topic": draft["topic"],
            "impressions": m["impressions"],
            "engagement_rate": round(rate, 4),
            "text": draft["text"],
        })
    return sorted(rows, key=lambda r: -r["engagement_rate"])


def learn_from_performance(mem, top=3, min_posts=4):
    rows = leaderboard(mem)
    if len(rows) < min_posts:
        return []
    best, worst = rows[:top], rows[-top:]
    show = lambda rs: "\n\n".join(f"[{r['engagement_rate']:.2%}] {r['text']}" for r in rs)
    prompt = (
        'Return JSON: {"lessons": ["..."]} with at most three specific, testable lessons about what '
        "separates the best posts from the worst. Base them only on the texts below.\n\n"
        f"BEST:\n{show(best)}\n\nWORST:\n{show(worst)}"
    )
    lessons = chat_json([{"role": "user", "content": prompt}])["lessons"]
    mem["lessons"] = (mem["lessons"] + [x for x in lessons if x not in mem["lessons"]])[-20:]
    memory.save(mem)
    return lessons
