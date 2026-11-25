"""Thin wrappers around the OpenAI API. Every other module calls these."""
import json
import re

from openai import OpenAI

from .config import EMBED_MODEL, MODEL

_client = None


def client():
    """Create the client on first use, so the API key can be set after import."""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def chat(messages, **kwargs):
    response = client().chat.completions.create(model=MODEL, messages=messages, **kwargs)
    return response.choices[0].message.content.strip()


def extract_json(text):
    """Parse the first JSON object or array found in a model reply."""
    match = re.search(r"[\[{].*[\]}]", text, re.S)
    if not match:
        raise ValueError("No JSON found in reply: " + text[:200])
    return json.loads(match.group(0))


def chat_json(messages):
    """Ask for a JSON object. The word JSON must appear in the messages."""
    text = chat(messages, response_format={"type": "json_object"})
    return extract_json(text)


def embed(texts, batch=100):
    vectors = []
    for i in range(0, len(texts), batch):
        response = client().embeddings.create(model=EMBED_MODEL, input=texts[i:i + batch])
        vectors.extend(d.embedding for d in response.data)
    return vectors
