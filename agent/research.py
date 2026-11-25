"""Topic discovery: a hand-written tool-calling loop."""
import json

from .config import MODEL
from .llm import client, extract_json
from .tools import TOOL_SPECS, run_tool

SYSTEM = (
    "You are a research assistant for a social media manager. Use the tools to find current "
    "topics. Pick topics that fit the author's field and have not been covered recently. "
    'Finish with JSON only, in this shape: {"topics": [{"title": "", "angle": "", '
    '"why_it_fits": "", "source_url": ""}]}'
)


def discover_topics(mem, n=5, max_steps=6, verbose=True):
    messages = [
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": (
                f"Author field: {mem['field']}\n"
                f"Author background: {mem['profile'][:800]}\n"
                f"Return {n} topics. Call get_my_recent_posts first to avoid repeats."
            ),
        },
    ]
    for _ in range(max_steps):
        response = client().chat.completions.create(model=MODEL, messages=messages, tools=TOOL_SPECS)
        message = response.choices[0].message
        if not message.tool_calls:  # the model is done
            return extract_json(message.content)["topics"]
        messages.append(message)
        for call in message.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            if verbose:
                print("tool call:", call.function.name, args)
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": run_tool(call.function.name, args)}
            )
    raise RuntimeError("The agent did not finish within max_steps")
