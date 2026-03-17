"""
becon_fetcher.py — RSS fetcher for the Behavioral Economics & Game Theory digest.

Sources: NBER working papers, top peer-reviewed journals (AER, QJE, JPE, RestUD,
Econometrica, Games & Economic Behavior, Experimental Economics, and more),
plus VoxEU policy summaries and SSRN.

Returns deduplicated article dicts filtered to behavioral economics / game theory content.
"""

import logging
import feedparser

from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

FEEDS: dict[str, str] = {
    # ── Working paper repositories (most current — papers appear here before journals) ──
    "NBER Working Papers":          "https://www.nber.org/rss/new_working_papers.xml",

    # ── Top-5 general journals ────────────────────────────────────────────────
    "American Economic Review":
        "https://www.aeaweb.org/journals/aer/issues/rss",
    "AEJ Microeconomics":
        "https://www.aeaweb.org/journals/mic/issues/rss",
    "AEJ Applied Economics":
        "https://www.aeaweb.org/journals/app/issues/rss",
    "Quarterly Journal of Economics":
        "https://academic.oup.com/rss/content/xml/1531108",
    "Review of Economic Studies":
        "https://academic.oup.com/rss/content/xml/1467937X",
    "Journal of Political Economy":
        "https://www.journals.uchicago.edu/action/showFeed?type=etoc&feed=rss&jc=jpe",
    "Econometrica":
        "https://onlinelibrary.wiley.com/feed/14680262/most-recent",

    # ── Specialist behavioral / experimental / game theory journals ──────────
    "Games and Economic Behavior":
        "https://rss.sciencedirect.com/publication/science/08996987",
    "Journal of Economic Theory":
        "https://rss.sciencedirect.com/publication/science/00220531",
    "Experimental Economics":
        "https://link.springer.com/search.rss?facet-journal-id=10683&query=",
    "Journal of Behavioral Decision Making":
        "https://onlinelibrary.wiley.com/feed/10990771/most-recent",
    "Journal of Economic Behavior and Organization":
        "https://rss.sciencedirect.com/publication/science/01672681",
    "Journal of Economic Psychology":
        "https://rss.sciencedirect.com/publication/science/01674870",
    "Journal of Public Economics":
        "https://rss.sciencedirect.com/publication/science/00472727",

    # ── Policy-facing summaries of top research (more readable, very timely) ─
    "VoxEU (CEPR)":                 "https://feeds.feedburner.com/voxeu/whys",
    "NBER Digest":                  "https://www.nber.org/rss/digest.xml",
}

# ---------------------------------------------------------------------------
# Keyword filtering — must match at least one (case-insensitive)
# ---------------------------------------------------------------------------

KEYWORDS: list[str] = [
    # Core behavioral econ
    "behavioral economics", "behavioural economics",
    "behavioral finance", "behavioural finance",
    "prospect theory", "loss aversion", "reference dependence",
    "mental accounting", "framing effect", "anchoring",
    "status quo bias", "default effect", "choice architecture",
    "nudge", "nudging", "libertarian paternalism",
    "bounded rationality", "heuristics", "cognitive bias",
    "overconfidence", "present bias", "hyperbolic discounting",
    "time preferences", "intertemporal choice",
    "ambiguity aversion", "risk preferences", "risk aversion",
    "endowment effect", "sunk cost",
    # Behavioral game theory
    "behavioral game theory",
    "social preferences", "inequality aversion",
    "reciprocity", "altruism", "other-regarding preferences",
    "fairness", "trust game", "dictator game",
    "ultimatum game", "public goods game",
    "level-k", "cognitive hierarchy", "quantal response",
    "cursed equilibrium", "psychological game theory",
    "cooperation", "coordination game",
    # Experimental methods
    "lab experiment", "laboratory experiment",
    "field experiment", "randomized controlled trial",
    "natural experiment", "rct",
    "mechanism design", "auction theory",
    # Adjacent topics often covered
    "happiness", "subjective well-being", "life satisfaction",
    "identity economics", "social norms", "cultural economics",
    "neuroeconomics", "decision neuroscience",
    "poverty traps", "self-control", "temptation",
    "savings behavior", "retirement savings",
    "health behavior", "health economics behavioral",
    "education economics", "human capital behavioral",
]

# ---------------------------------------------------------------------------
# Topic bucketing — first match wins
# ---------------------------------------------------------------------------

TOPIC_PRIORITY: list[tuple[str, str]] = [
    # Specific behavioral game theory
    ("behavioral game theory",    "Behavioral Game Theory"),
    ("social preferences",        "Behavioral Game Theory"),
    ("trust game",                "Behavioral Game Theory"),
    ("dictator game",             "Behavioral Game Theory"),
    ("ultimatum game",            "Behavioral Game Theory"),
    ("public goods game",         "Behavioral Game Theory"),
    ("level-k",                   "Behavioral Game Theory"),
    ("cognitive hierarchy",       "Behavioral Game Theory"),
    ("quantal response",          "Behavioral Game Theory"),
    ("reciprocity",               "Behavioral Game Theory"),
    ("cooperation",               "Behavioral Game Theory"),
    ("coordination game",         "Behavioral Game Theory"),
    ("mechanism design",          "Behavioral Game Theory"),
    # Core behavioral economics
    ("prospect theory",           "Behavioral Economics"),
    ("loss aversion",             "Behavioral Economics"),
    ("mental accounting",         "Behavioral Economics"),
    ("nudge",                     "Behavioral Economics"),
    ("choice architecture",       "Behavioral Economics"),
    ("default effect",            "Behavioral Economics"),
    ("present bias",              "Behavioral Economics"),
    ("hyperbolic discounting",    "Behavioral Economics"),
    ("bounded rationality",       "Behavioral Economics"),
    ("behavioral economics",      "Behavioral Economics"),
    ("behavioural economics",     "Behavioral Economics"),
    # Experimental / empirical methods
    ("field experiment",          "Experiments & Methods"),
    ("lab experiment",            "Experiments & Methods"),
    ("laboratory experiment",     "Experiments & Methods"),
    ("randomized controlled trial", "Experiments & Methods"),
    ("rct",                       "Experiments & Methods"),
    # Applied behavioral
    ("behavioral finance",        "Applied Behavioral"),
    ("behavioural finance",       "Applied Behavioral"),
    ("savings behavior",          "Applied Behavioral"),
    ("retirement savings",        "Applied Behavioral"),
    ("health behavior",           "Applied Behavioral"),
    ("poverty",                   "Applied Behavioral"),
    ("self-control",              "Applied Behavioral"),
    ("neuroeconomics",            "Applied Behavioral"),
    ("happiness",                 "Applied Behavioral"),
    ("well-being",                "Applied Behavioral"),
]

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("becon_digest.fetcher")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_published(entry) -> Optional[datetime]:
    raw: str = getattr(entry, "published", "") or getattr(entry, "updated", "")
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                dt = datetime.strptime(raw, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
    return None


def _pick_topic(text: str) -> Optional[str]:
    lower = text.lower()
    for keyword, label in TOPIC_PRIORITY:
        if keyword in lower:
            return label
    return None


def _entry_to_article(entry, source: str) -> Optional[dict]:
    title:   str = getattr(entry, "title",   "") or ""
    link:    str = getattr(entry, "link",    "") or ""
    summary: str = getattr(entry, "summary", "") or ""
    authors: str = ""
    if hasattr(entry, "authors"):
        authors = ", ".join(a.get("name", "") for a in entry.authors)
    elif hasattr(entry, "author"):
        authors = entry.author or ""

    combined = f"{title} {summary}"
    lower = combined.lower()

    if not any(kw in lower for kw in KEYWORDS):
        return None

    topic = _pick_topic(combined)
    if topic is None:
        return None

    pub_dt = _parse_published(entry)
    pub_str = pub_dt.strftime("%Y-%m-%d") if pub_dt else "Unknown"

    return {
        "title":     title.strip(),
        "link":      link.strip(),
        "source":    source,
        "published": pub_str,
        "authors":   authors.strip(),
        "summary":   summary[:500].strip(),
        "topic":     topic,
        "_published_dt": pub_dt,
    }


def _fetch_with_cutoff(cutoff: datetime) -> list[dict]:
    seen_links: set[str] = set()
    articles:   list[dict] = []

    for source, url in FEEDS.items():
        logger.info("Fetching: %s", source)
        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                raise ValueError(f"Parse error: {feed.bozo_exception}")
            logger.info("  -> %d entries", len(feed.entries))

            for entry in feed.entries:
                article = _entry_to_article(entry, source)
                if article is None:
                    continue
                pub_dt = article.pop("_published_dt")
                if pub_dt is not None and pub_dt < cutoff:
                    continue
                link = article["link"]
                if link in seen_links:
                    continue
                seen_links.add(link)
                articles.append(article)

        except Exception as exc:
            logger.warning("Skipping '%s': %s", source, exc)

    return articles


def fetch_becon_news() -> list[dict]:
    """
    Fetch behavioral economics / game theory articles.
    Tries 7 days first; expands to 30 days if fewer than 3 found.
    """
    now = datetime.now(tz=timezone.utc)

    articles = _fetch_with_cutoff(now - timedelta(days=7))
    logger.info("7-day window: %d article(s).", len(articles))

    if len(articles) < 3:
        logger.info("Expanding to 30 days.")
        articles = _fetch_with_cutoff(now - timedelta(days=30))
        logger.info("30-day window: %d article(s).", len(articles))

    logger.info("Total collected: %d", len(articles))
    return articles


if __name__ == "__main__":
    results = fetch_becon_news()
    print(f"\nFound {len(results)} article(s):\n{'=' * 60}")
    for i, a in enumerate(results, 1):
        print(f"\n[{i}] {a['title']}")
        print(f"    Authors  : {a.get('authors', 'N/A')}")
        print(f"    Source   : {a['source']}")
        print(f"    Topic    : {a['topic']}")
        print(f"    Published: {a['published']}")
        print(f"    Link     : {a['link']}")
        print(f"    Abstract : {a['summary'][:200]}...")
