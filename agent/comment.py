"""Comment drafting: three options in the author's voice for someone else's post."""
import json

from . import memory
from .config import PLATFORMS
from .generate import hard_checks, system_prompt
from .llm import chat_json
from .style import retrieve_examples

INTENTS = [
    "add one concrete point of view",
    "ask one sharp question",
    "share a short related experience, using an [ADD: ...] placeholder instead of inventing one",
]


def draft_comments(mem, post_text, platform="linkedin"):
    examples = retrieve_examples(mem, post_text, k=4, kind="comment") or retrieve_examples(mem, post_text, k=3)
    limit = PLATFORMS[platform]["comment_max_chars"]
    prompt = (
        "Write three comments on the post below, one per intent. "
        'Return JSON: {"comments": [{"intent": "", "text": ""}]}.\n'
        "Intents:\n- " + "\n- ".join(INTENTS) + "\n\n"
        "The author's real comments and posts, for voice:\n" + "\n---\n".join(examples) + "\n\n"
        "POST TO COMMENT ON:\n" + post_text
    )
    reply = chat_json([
        {"role": "system", "content": system_prompt(mem, platform, kind="comment")},
        {"role": "user", "content": prompt},
    ])
    drafts = []
    for c in reply["comments"]:
        drafts.append(memory.add(mem, "drafts", {
            "kind": "comment",
            "platform": platform,
            "topic": "comment on: " + post_text[:60],
            "intent": c["intent"],
            "text": c["text"],
            "original": c["text"],
            "issues": hard_checks(c["text"], mem, limit),
            "status": "pending",
        }))
    return drafts
