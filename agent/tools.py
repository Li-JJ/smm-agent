"""Tools the research agent can call. Each is a plain Python function plus a JSON spec."""
import json

import feedparser
import requests

from . import memory
from .config import FEEDS


def get_hacker_news(limit=15):
    """Current Hacker News front page stories."""
    r = requests.get(
        "https://hn.algolia.com/api/v1/search",
        params={"tags": "front_page", "hitsPerPage": limit},
        timeout=15,
    )
    r.raise_for_status()
    return [
        {
            "title": h["title"],
            "url": h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
            "points": h.get("points"),
            "comments": h.get("num_comments"),
        }
        for h in r.json()["hits"]
    ]


def get_rss(feed, limit=10):
    """Latest entries from one of the feeds configured in config.FEEDS."""
    if feed not in FEEDS:
        return {"error": f"Unknown feed. Choose one of {list(FEEDS)}"}
    parsed = feedparser.parse(FEEDS[feed])
    return [
        {"title": e.get("title"), "url": e.get("link"), "summary": (e.get("summary") or "")[:300]}
        for e in parsed.entries[:limit]
    ]


def get_my_recent_posts(limit=8):
    """Topics the author already wrote about recently, so the agent avoids repeats."""
    mem = memory.load()
    posts = [d for d in mem["drafts"] if d["kind"] == "post" and d["status"] in ("approved", "published")]
    return [{"topic": d["topic"], "date": d["ts"]} for d in posts[-limit:]]


TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "get_hacker_news",
            "description": "Get the current Hacker News front page stories.",
            "parameters": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "description": "Number of stories, up to 30"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rss",
            "description": "Get the latest entries from a named RSS feed. Feeds: " + ", ".join(FEEDS),
            "parameters": {
                "type": "object",
                "properties": {"feed": {"type": "string", "enum": list(FEEDS)}},
                "required": ["feed"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_recent_posts",
            "description": "List topics the author already posted about recently.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

REGISTRY = {f.__name__: f for f in (get_hacker_news, get_rss, get_my_recent_posts)}


def run_tool(name, args):
    """Run a tool by name. Errors go back to the model as text, so it can adapt."""
    try:
        result = REGISTRY[name](**args)
    except Exception as e:  # a broken feed must not crash the agent
        result = {"error": str(e)}
    return json.dumps(result)[:6000]
