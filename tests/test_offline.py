"""Offline smoke test. A fake OpenAI client replaces the network, so no API key is needed."""
import json
import os
import shutil
import sys
import tempfile
from types import SimpleNamespace as NS

tmp = tempfile.mkdtemp()
os.environ["SMM_DATA_DIR"] = os.path.join(tmp, "data")
os.environ["OPENAI_API_KEY"] = "test"
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agent import comment, generate, llm, measure, memory, research, review, style  # noqa: E402
from agent import tools  # noqa: E402

QUEUE = []  # scripted chat replies


def msg(content=None, tool_calls=None):
    return NS(choices=[NS(message=NS(content=content, tool_calls=tool_calls))])


class FakeCompletions:
    def create(self, **kw):
        return QUEUE.pop(0)


class FakeEmbeddings:
    def create(self, model, input):
        def vec(t):
            v = [0.0] * 8
            for i, ch in enumerate(t.lower()):
                v[i % 8] += ord(ch) % 7
            return v
        return NS(data=[NS(embedding=vec(t)) for t in input])


llm._client = NS(chat=NS(completions=FakeCompletions()), embeddings=FakeEmbeddings())

mem = memory.load()
mem["field"] = "applied ML"
mem["banned_words"] = ["synergy", "\u2014"]
n = style.ingest(mem, "sources")
assert n == 14, n
assert style.ingest(mem, "sources") == 0  # re-running adds nothing

QUEUE.append(msg(json.dumps({"voice": "direct", "sentence_length": "short"})))
assert style.build_profile(mem)["voice"] == "direct"
assert len(style.retrieve_examples(mem, "monitoring features", k=3)) == 3
assert style.banned_hits("pure synergy \u2014 here", mem["banned_words"]) == ["synergy", "\u2014"]

# tool calling loop: one tool call, then a final JSON answer
call = NS(id="c1", function=NS(name="get_my_recent_posts", arguments="{}"))
final = json.dumps({"topics": [{"title": "T1", "angle": "A", "why_it_fits": "W", "source_url": "u"}]})
QUEUE += [msg(None, [call]), msg(final)]
topics = research.discover_topics(mem, verbose=False)
assert topics[0]["title"] == "T1"
assert json.loads(tools.run_tool("nope", {}))["error"]

# generation: first draft fails the critic, revision passes
QUEUE += [
    msg("Draft one with synergy."),
    msg(json.dumps({"pass": False, "issues": ["too salesy"]})),
    msg("Draft two [ADD: your example]."),
    msg(json.dumps({"pass": True, "issues": []})),
]
d = generate.write_post(mem, topics[0])
assert d["text"].startswith("Draft two") and d["placeholders"] == ["[ADD: your example]"]

QUEUE.append(msg(json.dumps({"comments": [{"intent": "i", "text": "Nice point."}] * 3})))
cs = comment.draft_comments(mem, "Some post about evals")
assert len(cs) == 3

review.approve(mem, d["id"], edited_text="Draft two, edited.")
assert memory.find(mem, "drafts", d["id"])["status"] == "approved"
QUEUE.append(msg(json.dumps({"rules": ["Cut the first sentence"]})))
assert review.learn_from_edits(mem) == ["Cut the first sentence"]

ids = []
for i in range(4):
    QUEUE += [msg("Post %d" % i), msg(json.dumps({"pass": True, "issues": []}))]
    p = generate.write_post(mem, {"title": "P%d" % i, "angle": ""})
    ids.append(p["id"])
    measure.log_metrics(mem, p["id"], 1000, 10 * (i + 1), i)
assert measure.leaderboard(mem)[0]["draft_id"] == ids[-1]
QUEUE.append(msg(json.dumps({"lessons": ["Short posts win"]})))
assert measure.learn_from_performance(mem) == ["Short posts win"]

mem2 = memory.load()  # persistence round trip
assert len(mem2["drafts"]) == len(mem["drafts"]) and mem2["lessons"]
shutil.rmtree(tmp)
print("all offline checks passed")
