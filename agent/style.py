"""Learn the author's voice from past writing, and retrieve similar examples later."""
import csv
import hashlib
import os
import re
import uuid

import numpy as np

from . import memory
from .config import SOURCES_DIR
from .llm import chat_json, embed

TEXT_COLUMNS = ["sharecommentary", "commentary", "message", "text", "post"]
MIN_CHARS = {"post": 40, "comment": 20}


def _find_file(folder, name):
    """Case-insensitive file lookup, because LinkedIn exports use names like Profile.csv."""
    for f in os.listdir(folder):
        if f.lower() == name:
            return os.path.join(folder, f)
    return None


def _read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            yield {(k or "").strip().lower().replace(" ", ""): (v or "").strip() for k, v in row.items()}


def load_texts(folder=SOURCES_DIR):
    """Return [{'text', 'kind', 'source'}] for every post or comment found in the folder."""
    items = []
    if not os.path.isdir(folder):
        return items
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        low = name.lower()
        kind = "comment" if "comment" in low else "post"
        if low.endswith((".txt", ".md")):
            with open(path, encoding="utf-8") as f:
                chunks = f.read().split("\n---\n")
        elif low.endswith(".csv") and low not in ("profile.csv", "positions.csv"):
            chunks = [next((row[c] for c in TEXT_COLUMNS if row.get(c)), "") for row in _read_csv(path)]
        else:
            continue
        for chunk in chunks:
            text = chunk.strip()
            if len(text) >= MIN_CHARS[kind]:
                items.append({"text": text, "kind": kind, "source": low})
    return items


def load_profile(folder=SOURCES_DIR):
    """Build a short background text from Profile.csv and Positions.csv, if present."""
    parts = []
    if not os.path.isdir(folder):
        return ""
    path = _find_file(folder, "profile.csv")
    if path:
        for row in _read_csv(path):
            parts += [row.get("headline", ""), row.get("summary", "")]
    path = _find_file(folder, "positions.csv")
    if path:
        for row in list(_read_csv(path))[:6]:
            parts.append(f"{row.get('title', '')} at {row.get('companyname', '')}. {row.get('description', '')}")
    return "\n".join(p for p in parts if p.strip())


def ingest(mem, folder=SOURCES_DIR):
    """Add new texts from the folder to memory. Safe to run again after adding files."""
    known = {c["hash"] for c in mem["corpus"]}
    new = []
    for item in load_texts(folder):
        item["hash"] = hashlib.sha1(item["text"].encode()).hexdigest()[:12]
        if item["hash"] in known:
            continue
        known.add(item["hash"])
        item["id"] = uuid.uuid4().hex[:8]
        new.append(item)
    if new:
        vectors = embed([n["text"] for n in new])
        embeddings = memory.load_embeddings()
        embeddings.update({n["id"]: v for n, v in zip(new, vectors)})
        memory.save_embeddings(embeddings)
        mem["corpus"].extend(new)
    profile = load_profile(folder)
    if profile:
        mem["profile"] = profile
    memory.save(mem)
    return len(new)


def build_profile(mem, max_posts=40, max_comments=15):
    """Ask the model to describe how the author writes. The result is stored as JSON."""
    posts = [c["text"] for c in mem["corpus"] if c["kind"] == "post"][-max_posts:]
    comments = [c["text"] for c in mem["corpus"] if c["kind"] == "comment"][-max_comments:]
    prompt = (
        "Analyze the writing samples below and describe how this author writes.\n"
        "Return JSON with these keys: voice (two sentences), sentence_length (short, medium or long, "
        "with a typical word count), openers (three typical ways posts begin), structure (how a typical "
        "post is organized), signature_phrases (list), vocabulary_level, emoji_use, formatting "
        "(line breaks, lists, hashtags), avoid (things the author never does).\n"
        "Describe only patterns that appear in the samples.\n\n"
        "POSTS:\n" + "\n\n---\n\n".join(posts) + "\n\nCOMMENTS:\n" + "\n\n---\n\n".join(comments)
    )
    mem["style"] = chat_json([{"role": "user", "content": prompt}])
    memory.save(mem)
    return mem["style"]


def retrieve_examples(mem, query, k=4, kind="post"):
    """Return the k past texts most similar to the query, using cosine similarity."""
    embeddings = memory.load_embeddings()
    items = [c for c in mem["corpus"] if c["kind"] == kind and c["id"] in embeddings]
    if not items:
        return []
    q = np.array(embed([query])[0])
    matrix = np.array([embeddings[c["id"]] for c in items])
    sims = matrix @ q / (np.linalg.norm(matrix, axis=1) * np.linalg.norm(q))
    return [items[i]["text"] for i in np.argsort(-sims)[:k]]


def set_words(mem, favorite=None, banned=None):
    if favorite is not None:
        mem["favorite_words"] = [w.strip() for w in favorite if w.strip()]
    if banned is not None:
        mem["banned_words"] = [w.strip() for w in banned if w.strip()]
    memory.save(mem)


def banned_hits(text, banned):
    """Return the banned words or symbols that appear in the text."""
    return [w for w in banned if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", text, re.I)]
