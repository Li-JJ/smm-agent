"""Streamlit front end. Run with: streamlit run app.py"""
import os

import streamlit as st

from agent import comment, generate, measure, memory, research, review, style
from agent.config import PLATFORMS, SOURCES_DIR

st.set_page_config(page_title="My AI Social Media Manager", layout="wide")

with st.sidebar:
    st.header("Settings")
    key = st.text_input("OpenAI API key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    if key:
        os.environ["OPENAI_API_KEY"] = key
    platform = st.selectbox("Platform", list(PLATFORMS))

mem = memory.load()
st.title("My AI Social Media Manager")
tab_style, tab_topics, tab_post, tab_comment, tab_queue = st.tabs(
    ["1. Style", "2. Topics", "3. Post", "4. Comment", "5. Queue and results"]
)

with tab_style:
    mem["field"] = st.text_input("What do you write about?", value=mem["field"])
    files = st.file_uploader("LinkedIn export files or text files", accept_multiple_files=True,
                             type=["csv", "txt", "md"])
    fav = st.text_input("Favorite words (comma separated)", value=", ".join(mem["favorite_words"]))
    ban = st.text_input("Banned words (comma separated)", value=", ".join(mem["banned_words"]))
    if st.button("Learn my style"):
        os.makedirs(SOURCES_DIR, exist_ok=True)
        for f in files or []:
            with open(os.path.join(SOURCES_DIR, f.name), "wb") as out:
                out.write(f.getbuffer())
        style.set_words(mem, fav.split(","), ban.split(","))
        with st.spinner("Reading your writing..."):
            added = style.ingest(mem)
            style.build_profile(mem)
        st.success(f"Added {added} new items.")
    if mem["style"]:
        st.json(mem["style"])

with tab_topics:
    if st.button("Find topics"):
        with st.spinner("Checking Hacker News and RSS feeds..."):
            st.session_state["topics"] = research.discover_topics(mem, verbose=False)
    for t in st.session_state.get("topics", []):
        st.markdown(f"**{t['title']}**  \n{t['angle']}  \n_{t['why_it_fits']}_  \n{t['source_url']}")

with tab_post:
    topics = st.session_state.get("topics", [])
    if not topics:
        st.info("Find topics first.")
    else:
        choice = st.selectbox("Topic", [t["title"] for t in topics])
        if st.button("Write post"):
            topic = next(t for t in topics if t["title"] == choice)
            with st.spinner("Writing and checking..."):
                st.session_state["last_post"] = generate.write_post(mem, topic, platform)
        post = st.session_state.get("last_post")
        if post:
            st.code(post["text"], language=None)  # the copy button comes with st.code
            if post["placeholders"]:
                st.warning("Fill in before posting: " + "; ".join(post["placeholders"]))

with tab_comment:
    target = st.text_area("Paste the post you want to comment on", height=200)
    if st.button("Draft comments") and target.strip():
        with st.spinner("Drafting..."):
            st.session_state["comments"] = comment.draft_comments(mem, target, platform)
    for c in st.session_state.get("comments", []):
        st.caption(c["intent"])
        st.code(c["text"], language=None)

with tab_queue:
    mem = memory.load()
    for d in [d for d in mem["drafts"] if d["status"] == "pending"]:
        with st.expander(f"{d['kind']}: {d['topic']}"):
            edited = st.text_area("Edit", value=d["text"], key="edit" + d["id"], height=200)
            c1, c2 = st.columns(2)
            if c1.button("Approve", key="ok" + d["id"]):
                review.approve(mem, d["id"], edited)
                st.rerun()
            if c2.button("Reject", key="no" + d["id"]):
                review.reject(mem, d["id"], "rejected in UI")
                st.rerun()
    st.subheader("Log results")
    approved = [d for d in mem["drafts"] if d["status"] in ("approved", "published") and d["kind"] == "post"]
    if approved:
        pick = st.selectbox("Post", [f"{d['id']} | {d['topic']}" for d in approved])
        imp = st.number_input("Impressions", 0, step=100)
        rea = st.number_input("Reactions", 0)
        com = st.number_input("Comments", 0)
        if st.button("Save results"):
            measure.mark_published(mem, pick.split(" | ")[0])
            measure.log_metrics(mem, pick.split(" | ")[0], int(imp), int(rea), int(com))
            st.success("Saved.")
    if st.button("Learn from edits and results"):
        rules = review.learn_from_edits(mem) + measure.learn_from_performance(mem)
        st.write(rules or "Not enough data yet.")
    if mem["metrics"]:
        st.dataframe([{k: v for k, v in r.items() if k != "text"} for r in measure.leaderboard(mem)])
