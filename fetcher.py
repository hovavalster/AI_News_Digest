"""
fetcher.py — RSS feed fetcher for AI News Digest.

Fetches articles from Anthropic, Google AI, TechCrunch AI, and The Verge AI feeds,
filters for Claude / Claude Code / Gemini / NotebookLM mentions, and returns a
deduplicated list of article dicts.
"""

import logging
import feedparser

from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FEEDS: dict[str, str] = {
    "Anthropic Blog":   "https://www.anthropic.com/rss.xml",
    "Google Blog AI":   "https://blog.google/technology/ai/rss/",
    "TechCrunch AI":    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI":     "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
}

# Keywords that qualify an article for inclusion (case-insensitive)
KEYWORDS: list[str] = [
    "claude", "claude code", "gemini", "notebooklm",
    "ai agent", "agentic", "multi-agent", "autogpt", "crewai", "langgraph",
    "n8n", "agentops", "openai agents", "agent sdk",
]

# Topic labels in priority order (most specific first)
# An article is labelled with the first topic whose keyword appears in the text.
TOPIC_PRIORITY: list[tuple[str, str]] = [
    ("claude code",    "Claude Code"),
    ("notebooklm",     "NotebookLM"),
    ("gemini",         "Gemini"),
    ("claude",         "Claude Code"),
    ("autogpt",        "AI Agents"),
    ("crewai",         "AI Agents"),
    ("langgraph",      "AI Agents"),
    ("agentops",       "AI Agents"),
    ("openai agents",  "AI Agents"),
    ("agent sdk",      "AI Agents"),
    ("multi-agent",    "AI Agents"),
    ("agentic",        "AI Agents"),
    ("ai agent",       "AI Agents"),
]

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("ai_news_digest.fetcher")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _parse_published(entry: feedparser.FeedParserDict) -> Optional[datetime]:
    """
    Try to extract a timezone-aware datetime from a feed entry.

    feedparser stores the raw date string in entry.published (RFC 2822 format
    from most feeds).  Falls back to entry.updated if published is absent.
    Returns None when no date can be parsed.
    """
    raw: str = getattr(entry, "published", "") or getattr(entry, "updated", "")
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        # Ensure the datetime is timezone-aware (some feeds omit tz → assume UTC)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        # Some feeds use ISO 8601 instead of RFC 2822 — try a simple fallback
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                dt = datetime.strptime(raw, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
    logger.debug("Could not parse date string: %r", raw)
    return None


def _pick_topic(text: str) -> Optional[str]:
    """
    Return the most-specific topic label found in *text*, or None if none match.

    Checks TOPIC_PRIORITY in order so that "Claude Code" beats plain "Claude".
    """
    lower = text.lower()
    for keyword, label in TOPIC_PRIORITY:
        if keyword in lower:
            return label
    return None


def _entry_to_article(entry: feedparser.FeedParserDict, source: str) -> Optional[dict]:
    """
    Convert a feedparser entry into an article dict.

    Returns None if the entry does not mention any of the tracked keywords.
    """
    title:   str = getattr(entry, "title",   "") or ""
    link:    str = getattr(entry, "link",    "") or ""
    summary: str = getattr(entry, "summary", "") or ""

    # Combine title + summary for keyword and topic matching
    combined_text = f"{title} {summary}"

    # Filter: must contain at least one tracked keyword
    lower = combined_text.lower()
    if not any(kw in lower for kw in KEYWORDS):
        return None

    topic = _pick_topic(combined_text)
    if topic is None:
        return None

    published_dt = _parse_published(entry)
    published_str = (
        published_dt.strftime("%Y-%m-%d %H:%M UTC")
        if published_dt
        else "Unknown"
    )

    return {
        "title":     title.strip(),
        "link":      link.strip(),
        "source":    source,
        "published": published_str,
        "summary":   summary[:300].strip(),
        "topic":     topic,
        # Keep the raw datetime for 24-hour filtering (not exposed to callers)
        "_published_dt": published_dt,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _fetch_with_cutoff(cutoff: datetime) -> list[dict]:
    """Internal: fetch all feeds and filter by the given cutoff datetime."""
    seen_links: set[str] = set()
    articles: list[dict] = []

    for source, url in FEEDS.items():
        logger.info("Fetching feed: %s (%s)", source, url)
        try:
            feed = feedparser.parse(url)

            # feedparser does not raise on network errors — check bozo flag
            if feed.bozo and not feed.entries:
                raise ValueError(f"Feed parse error: {feed.bozo_exception}")

            logger.info("  -> %d entries retrieved", len(feed.entries))

            for entry in feed.entries:
                article = _entry_to_article(entry, source)
                if article is None:
                    continue

                pub_dt = article.pop("_published_dt")  # remove internal field
                if pub_dt is not None and pub_dt < cutoff:
                    continue

                link = article["link"]
                if link in seen_links:
                    continue
                seen_links.add(link)

                articles.append(article)

        except Exception as exc:
            logger.warning("Skipping feed '%s' due to error: %s", source, exc)
            continue

    return articles


def fetch_news() -> list[dict]:
    """
    Fetch AI news articles from all configured RSS feeds.

    Tries the last 24 hours first. If fewer than 3 articles are found,
    automatically expands to the last 7 days so there is always something
    interesting to read.

    Only articles mentioning Claude, Claude Code, Gemini, or NotebookLM
    are included. Duplicates are removed.

    Returns a list of article dicts with keys:
        title, link, source, published, summary, topic
    """
    now = datetime.now(tz=timezone.utc)

    # First try: last 24 hours
    articles = _fetch_with_cutoff(now - timedelta(hours=24))
    logger.info("24-hour window: %d article(s) found.", len(articles))

    # If slim pickings, widen to 7 days
    if len(articles) < 3:
        logger.info("Fewer than 3 articles in 24 hrs — expanding to 7 days.")
        articles = _fetch_with_cutoff(now - timedelta(days=7))
        logger.info("7-day window: %d article(s) found.", len(articles))

    logger.info("Total articles collected: %d", len(articles))
    return articles


# ---------------------------------------------------------------------------
# Quick test — run with:  python fetcher.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    results = fetch_news()

    if not results:
        print("No matching articles found in the last 24 hours.")
    else:
        print(f"\nFound {len(results)} article(s):\n{'=' * 60}")
        for i, art in enumerate(results, start=1):
            print(f"\n[{i}] {art['title']}")
            print(f"    Source  : {art['source']}")
            print(f"    Topic   : {art['topic']}")
            print(f"    Published: {art['published']}")
            print(f"    Link    : {art['link']}")
            print(f"    Summary : {art['summary'][:150]}{'...' if len(art['summary']) > 150 else ''}")
