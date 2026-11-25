"""The same agent built with the OpenAI Agents SDK. Run with: python sdk_version.py"""
import json

from agents import Agent, Runner, function_tool
from pydantic import BaseModel

from agent import generate, memory, tools
from agent.config import MODEL


@function_tool
def hacker_news(limit: int = 15) -> str:
    """Current Hacker News front page stories."""
    return json.dumps(tools.get_hacker_news(limit))


@function_tool
def rss(feed: str) -> str:
    """Latest entries from a configured RSS feed."""
    return json.dumps(tools.get_rss(feed))


@function_tool
def recent_posts() -> str:
    """Topics the author already posted about."""
    return json.dumps(tools.get_my_recent_posts())


class Topic(BaseModel):
    title: str
    angle: str
    why_it_fits: str
    source_url: str


class TopicList(BaseModel):
    topics: list[Topic]


researcher = Agent(
    name="Researcher",
    instructions="Find five current topics that fit the author's field and avoid recent repeats.",
    tools=[hacker_news, rss, recent_posts],
    model=MODEL,
    output_type=TopicList,
)


@function_tool
def write_post(title: str, angle: str) -> str:
    """Write a post in the author's voice and add it to the approval queue."""
    mem = memory.load()
    draft = generate.write_post(mem, {"title": title, "angle": angle})
    return draft["text"]


manager = Agent(
    name="Social media manager",
    instructions="Research topics, then write a post for the best one. Never publish anything.",
    tools=[researcher.as_tool(tool_name="research_topics", tool_description="Find fresh topics"), write_post],
    model=MODEL,
)

if __name__ == "__main__":
    mem = memory.load()
    result = Runner.run_sync(manager, f"My field is {mem['field']}. Draft one post for me.")
    print(result.final_output)
