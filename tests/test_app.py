"""Runs the Streamlit app headlessly with a fake OpenAI client and clicks through the main flow."""
import json
import os
import shutil
import sys
import tempfile
from types import SimpleNamespace as NS

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tmp = tempfile.mkdtemp()
os.environ["SMM_DATA_DIR"] = os.path.join(tmp, "data")
os.environ["SMM_SOURCES_DIR"] = os.path.join(root, "sources")
os.environ["OPENAI_API_KEY"] = "test"
sys.path.insert(0, root)

from streamlit.testing.v1 import AppTest  # noqa: E402

from agent import llm  # noqa: E402

QUEUE = []


def msg(content=None, tool_calls=None):
    return NS(choices=[NS(message=NS(content=content, tool_calls=tool_calls))])


class FakeCompletions:
    def create(self, **kw):
        return QUEUE.pop(0)


class FakeEmbeddings:
    def create(self, model, input):
        return NS(data=[NS(embedding=[float(len(t) % 7 + i) for i in range(8)]) for t in input])


llm._client = NS(chat=NS(completions=FakeCompletions()), embeddings=FakeEmbeddings())

at = AppTest.from_file(os.path.join(root, "app.py"), default_timeout=30).run()
assert not at.exception, at.exception
assert len(at.tabs) == 5

QUEUE.append(msg(json.dumps({"voice": "direct", "sentence_length": "short"})))
[b for b in at.button if b.label == "Learn my style"][0].click().run()
assert not at.exception, at.exception

QUEUE.append(msg(json.dumps({"topics": [{"title": "Evals first", "angle": "Write the eval before the prompt",
                                          "why_it_fits": "Matches your posts", "source_url": "https://example.com"}]})))
[b for b in at.button if b.label == "Find topics"][0].click().run()
assert not at.exception, at.exception

QUEUE += [msg("A short draft [ADD: your example]."), msg(json.dumps({"pass": True, "issues": []}))]
[b for b in at.button if b.label == "Write post"][0].click().run()
assert not at.exception, at.exception

[b for b in at.button if b.label == "Approve"][0].click().run()
assert not at.exception, at.exception
mem = json.load(open(os.path.join(tmp, "data", "memory.json")))
assert mem["drafts"][0]["status"] == "approved" and mem["style"]["voice"] == "direct"
shutil.rmtree(tmp)
print("app flow passed")
