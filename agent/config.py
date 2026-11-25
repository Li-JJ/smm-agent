"""Central settings. Change the model here or with the SMM_MODEL environment variable."""
import os

MODEL = os.getenv("SMM_MODEL", "gpt-5.4-mini")
EMBED_MODEL = "text-embedding-3-small"
DATA_DIR = os.getenv("SMM_DATA_DIR", "data")
SOURCES_DIR = os.getenv("SMM_SOURCES_DIR", "sources")

# One entry per platform. Add "threads" or "bluesky" here to support more.
PLATFORMS = {
    "linkedin": {
        "max_chars": 3000,
        "comment_max_chars": 600,
        "rules": "Open with a hook in the first two lines. Use short paragraphs. "
                 "Use at most three hashtags, at the end.",
    },
    "x": {
        "max_chars": 280,
        "comment_max_chars": 280,
        "rules": "One idea per post. Hashtags only if they fit naturally.",
    },
}

# Edit this dictionary to follow the sources you care about.
FEEDS = {
    "techcrunch_ai": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "arxiv_cs_ai": "http://export.arxiv.org/rss/cs.AI",
    "mit_tech_review": "https://www.technologyreview.com/feed/",
}
