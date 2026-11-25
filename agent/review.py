"""Human in the loop: approve, edit or reject drafts, and learn from what the human changed."""
from . import memory
from .llm import chat_json


def approve(mem, draft_id, edited_text=None, note=""):
    draft = memory.find(mem, "drafts", draft_id)
    if edited_text and edited_text != draft["text"]:
        memory.add(mem, "feedback", {
            "draft_id": draft_id, "before": draft["text"], "after": edited_text, "note": note,
        })
        draft["text"] = edited_text
    draft["status"] = "approved"
    memory.save(mem)
    return draft


def reject(mem, draft_id, reason):
    draft = memory.find(mem, "drafts", draft_id)
    draft["status"] = "rejected"
    memory.add(mem, "feedback", {"draft_id": draft_id, "reason": reason, "before": draft["text"]})
    return draft


def learn_from_edits(mem, last=6):
    """Turn the human's edits and rejections into short writing rules."""
    edits = [f for f in mem["feedback"] if f.get("after")][-last:]
    rejections = [f for f in mem["feedback"] if f.get("reason")][-last:]
    if not edits and not rejections:
        return []
    prompt = (
        'Return JSON: {"rules": ["..."]} with at most three short, specific writing rules that '
        "explain these changes. Skip rules that only apply to one topic.\n\nEDITS (before, after):\n"
        + "\n\n".join(f"BEFORE: {e['before']}\nAFTER: {e['after']}" for e in edits)
        + "\n\nREJECTIONS:\n"
        + "\n".join(f"- {r['reason']}" for r in rejections)
    )
    rules = chat_json([{"role": "user", "content": prompt}])["rules"]
    mem["lessons"] = (mem["lessons"] + [r for r in rules if r not in mem["lessons"]])[-20:]
    memory.save(mem)
    return rules
