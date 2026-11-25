"""Post generation: retrieve examples, write, check, revise, save to the approval queue."""
import json
import re

from . import memory
from .config import PLATFORMS
from .llm import chat, chat_json
from .style import banned_hits, retrieve_examples


def system_prompt(mem, platform, kind="post"):
    p = PLATFORMS[platform]
    limit = p["max_chars"] if kind == "post" else p["comment_max_chars"]
    lessons = "\n".join("- " + x for x in mem["lessons"][-8:]) or "none yet"
    return f"""You write {platform} {kind}s as the author described below.

AUTHOR BACKGROUND:
{mem['profile'][:1000] or 'not provided'}

FIELD: {mem['field']}

STYLE PROFILE:
{json.dumps(mem['style'], indent=2)}

FAVORITE WORDS (use when natural): {', '.join(mem['favorite_words']) or 'none'}
BANNED WORDS (never use): {', '.join(mem['banned_words']) or 'none'}

LESSONS FROM PAST EDITS AND PERFORMANCE:
{lessons}

PLATFORM RULES: at most {limit} characters. {p['rules']}

HARD RULES:
- Use only facts from the source material and the author background.
- Never invent statistics, quotes or personal experiences.
- Where a personal example would help, write a placeholder in square brackets,
  like [ADD: a project where you saw this], for the author to fill in.
- Write in first person. Output only the text of the {kind}."""


def hard_checks(text, mem, max_chars):
    """Deterministic checks. These cost nothing and never disagree with themselves."""
    issues = []
    if len(text) > max_chars:
        issues.append(f"Too long: {len(text)} characters, limit {max_chars}")
    hits = banned_hits(text, mem["banned_words"])
    if hits:
        issues.append("Uses banned words: " + ", ".join(hits))
    return issues


def critique(draft, examples, source, mem):
    """LLM check against the author's real examples. Returns {'pass': bool, 'issues': [...]}"""
    prompt = (
        'Return JSON: {"pass": true or false, "issues": ["..."]}.\n'
        "Compare the DRAFT with the author's REAL EXAMPLES. Fail the draft if its tone, sentence "
        "length or structure clearly differs, if it contains buzzword filler, or if it states a "
        "specific fact that is not in the SOURCE. Placeholders in square brackets are allowed.\n\n"
        f"REAL EXAMPLES:\n{examples}\n\nSOURCE:\n{source}\n\nDRAFT:\n{draft}"
    )
    return chat_json([{"role": "user", "content": prompt}])


def write_post(mem, topic, platform="linkedin", max_revisions=2):
    query = f"{topic['title']} {topic.get('angle', '')}"
    examples = "\n\n---\n\n".join(retrieve_examples(mem, query, k=4, kind="post"))
    source = json.dumps(topic)
    messages = [
        {"role": "system", "content": system_prompt(mem, platform)},
        {
            "role": "user",
            "content": f"Real posts by the author:\n{examples}\n\nSOURCE MATERIAL:\n{source}\n\n"
                       "Write a new post about this topic.",
        },
    ]
    draft = chat(messages)
    for _ in range(max_revisions):
        issues = hard_checks(draft, mem, PLATFORMS[platform]["max_chars"])
        verdict = critique(draft, examples, source, mem)
        if not verdict.get("pass"):
            issues += verdict.get("issues", [])
        if not issues:
            break
        messages += [
            {"role": "assistant", "content": draft},
            {"role": "user", "content": "Revise the post. Fix these issues and keep everything else:\n- "
                                        + "\n- ".join(issues)},
        ]
        draft = chat(messages)
    return memory.add(mem, "drafts", {
        "kind": "post",
        "platform": platform,
        "topic": topic["title"],
        "text": draft,
        "original": draft,
        "placeholders": re.findall(r"\[[^\]]+\]", draft),
        "status": "pending",
    })
