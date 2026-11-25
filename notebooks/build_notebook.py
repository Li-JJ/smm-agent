"""Builds workshop.ipynb from the files in the repo, so notebook and repo never drift apart."""
import os

import nbformat as nbf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
read = lambda p: open(os.path.join(ROOT, p), encoding="utf-8").read().rstrip() + "\n"
nb = nbf.v4.new_notebook()
cells = nb.cells
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))
writefile = lambda path: code(f"%%writefile {path}\n" + read(path))

md("""# Your First AI Employee: Building a Personalized Social Media Agent
Run the cells from top to bottom. Each section writes one module of the agent into the `agent/` folder, then runs it.
You need an OpenAI API key. In Colab, open the key icon in the left sidebar, add a secret named `OPENAI_API_KEY`, and switch on notebook access.""")

md("## 0. Setup")
code("!pip -q install openai openai-agents feedparser requests numpy pandas streamlit\n%load_ext autoreload\n%autoreload 2")
code('''import os
try:
    from google.colab import userdata
    os.environ["OPENAI_API_KEY"] = userdata.get("OPENAI_API_KEY")
except Exception:
    from getpass import getpass
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY") or getpass("OpenAI API key: ")
os.makedirs("agent", exist_ok=True); os.makedirs("sources", exist_ok=True)''')
md("Smoke test: one API call. If this prints a reply, your key works.")
code('''from openai import OpenAI
r = OpenAI().chat.completions.create(model="gpt-5.4-mini", messages=[{"role": "user", "content": "Say hello in five words."}])
print(r.choices[0].message.content)''')

md("## 1. Settings, model wrappers and memory\nThree small modules. `config.py` holds the model name and platform rules. `llm.py` wraps the API. `memory.py` stores everything in one JSON file.")
code('%%writefile agent/__init__.py\n"""A personal AI social media manager."""')
for p in ("agent/config.py", "agent/llm.py", "agent/memory.py"):
    writefile(p)

md("""## 2. Style learning
First give the agent your writing. Choose one:
- **LinkedIn export:** request your data archive (Settings, Data privacy, Get a copy of your data), then upload `Shares.csv`, `Comments.csv`, `Profile.csv` and `Positions.csv`.
- **Your own text:** upload `.txt` files with posts separated by a line containing only `---`.
- **Neither yet:** run the sample cell to use the example author.""")
code('''from google.colab import files
uploaded = files.upload()   # skip this cell if you want the sample data
for name, data in uploaded.items():
    open(f"sources/{name}", "wb").write(data)''')
writefile("sources/sample_posts.txt")
writefile("sources/sample_comments.txt")
writefile("agent/style.py")
code('''from agent import memory, style
mem = memory.load()
mem["field"] = "applied machine learning and AI startups"   # change this to your field
print("new items:", style.ingest(mem))
print(style.build_profile(mem))''')
code('''style.set_words(mem, favorite=["practical", "ship"], banned=["synergy", "game-changer", "\\u2014"])
mem["banned_words"]''')

md("## 3. Topic discovery with tool calling\nThe model decides which tools to call. Your code runs them and sends the results back.")
writefile("agent/tools.py")
writefile("agent/research.py")
code('''from agent import research
topics = research.discover_topics(mem)
for t in topics:
    print(t["title"], "->", t["angle"])''')

md("## 4. Post generation\nRetrieve similar posts of yours, write, check with code, check with a critic, revise, save to the approval queue.")
writefile("agent/generate.py")
code('''from agent import generate
draft = generate.write_post(mem, topics[0])
print(draft["text"])
print("Fill in:", draft["placeholders"])''')

md("## 5. Comment drafting")
writefile("agent/comment.py")
code('''from agent import comment
post = "Most teams add agents before they have an evaluation set. Here is how we build the eval first."
for c in comment.draft_comments(mem, post):
    print(c["intent"], "\\n", c["text"], "\\n")''')

md("## 6. Human in the loop and measurement")
writefile("agent/review.py")
writefile("agent/measure.py")
code('''from agent import review, measure
review.approve(mem, draft["id"], edited_text=draft["text"] + "\\n\\n(my edit)", note="added a closing line")
measure.mark_published(mem, draft["id"])
measure.log_metrics(mem, draft["id"], impressions=1800, reactions=42, comments=7)
print(measure.leaderboard(mem)[0]["engagement_rate"])
print(review.learn_from_edits(mem))''')

md("""## 7. The app
The Streamlit app wires every module together. Run it on your laptop for the final demo. Download the project with the next cell, unzip it, then run:
```
pip install -r requirements.txt
streamlit run app.py
```""")
writefile("app.py")
writefile("requirements.txt")
code('''import shutil, os
os.makedirs("export/smm-agent", exist_ok=True)
for item in ["agent", "sources", "app.py", "requirements.txt"]:
    dest = os.path.join("export/smm-agent", item)
    shutil.copytree(item, dest, dirs_exist_ok=True) if os.path.isdir(item) else shutil.copy(item, dest)
shutil.make_archive("smm-agent", "zip", "export")
from google.colab import files
files.download("smm-agent.zip")''')

md("## 8. Optional: the same agent with the OpenAI Agents SDK")
writefile("sdk_version.py")
code("!python sdk_version.py")

nbf.write(nb, os.path.join(ROOT, "notebooks", "workshop.ipynb"))
print("cells:", len(cells))
