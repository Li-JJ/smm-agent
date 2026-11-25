"""Persistent memory: one JSON file you can open and read."""
import copy
import json
import os
import time
import uuid

from .config import DATA_DIR

PATH = os.path.join(DATA_DIR, "memory.json")
EMB_PATH = os.path.join(DATA_DIR, "embeddings.json")

EMPTY = {
    "field": "",          # what you write about
    "profile": "",        # headline, summary, positions
    "style": {},          # style profile learned from your writing
    "favorite_words": [],
    "banned_words": [],
    "corpus": [],         # your past posts and comments
    "drafts": [],         # everything the agent wrote
    "feedback": [],       # your edits and rejections
    "metrics": [],        # impressions, reactions, comments
    "lessons": [],        # rules the agent learned from feedback and metrics
}


def _read(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def load():
    mem = _read(PATH, {})
    for key, value in EMPTY.items():
        mem.setdefault(key, copy.deepcopy(value))
    return mem


def save(mem):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2, ensure_ascii=False)


def add(mem, key, item):
    item.setdefault("id", uuid.uuid4().hex[:8])
    item.setdefault("ts", time.strftime("%Y-%m-%d %H:%M"))
    mem[key].append(item)
    save(mem)
    return item


def find(mem, key, item_id):
    return next((x for x in mem[key] if x["id"] == item_id), None)


def load_embeddings():
    return _read(EMB_PATH, {})


def save_embeddings(embeddings):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(EMB_PATH, "w", encoding="utf-8") as f:
        json.dump(embeddings, f)
