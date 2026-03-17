"""
summarizer.py — Agent 2 (Summarizer) for AI News Digest
Generates a clean daily digest from collected news articles using Claude.
"""

import os
from collections import defaultdict
from podcasts import pick_episode_of_the_day


def summarize_news(articles: list[dict]) -> str:
    """
    Takes a list of article dicts and returns a formatted daily digest string.

    Each article dict must have keys:
        title, link, source, published, summary, topic

    Returns a Claude-generated digest grouped into 3 sections:
        Claude Code | Gemini | NotebookLM

    Falls back to a simple plain-text listing if the API call fails.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return _fallback_digest(articles, reason="ANTHROPIC_API_KEY not set")

    # Pick today's episode recommendation
    ep = pick_episode_of_the_day()
    podcast_block = (
        f"Show: {ep['show']}\n"
        f"Episode: {ep['episode']} ({ep['episode_id']})\n"
        f"Guest: {ep['guest']}\n"
        f"Category: {ep['category']}\n"
        f"Duration: {ep['duration']}\n"
        f"Why listen: {ep['why']}\n"
        f"Search on Spotify: \"{ep['spotify_search']}\""
    )

    # Group articles by topic for the prompt
    by_topic: dict[str, list[dict]] = defaultdict(list)
    for article in articles:
        topic = article.get("topic", "Other")
        by_topic[topic].append(article)

    # Build the articles section of the prompt
    articles_text = ""
    for topic in ["Claude Code", "Gemini", "NotebookLM", "AI Agents", "AI News"]:
        topic_articles = by_topic.get(topic, [])
        articles_text += f"\n### {topic}\n"
        if topic_articles:
            for a in topic_articles[:6]:  # cap per-topic to keep prompt manageable
                articles_text += (
                    f"- Title: {a.get('title', 'No title')}\n"
                    f"  URL: {a.get('link', '')}\n"
                    f"  Source: {a.get('source', '')}\n"
                    f"  Published: {a.get('published', 'Unknown date')}\n"
                    f"  Summary: {a.get('summary', 'No summary available')}\n"
                )
        else:
            articles_text += "(no articles found in feeds)\n"

    prompt = f"""You are writing a daily AI digest email for a curious, non-technical reader who follows AI closely and wants to hear about things that are genuinely NEW — things that happened or were announced in the last few days.

Here are today's fresh articles pulled from 18 sources (Reddit, HackerNews, VentureBeat, MIT Tech Review, practitioner blogs, and lab blogs). These are ALL NEW — not previously sent:
{articles_text}

Write a digest with 5 sections: **Claude & Anthropic**, **Gemini & Google AI**, **AI Agents & Tools**, **AI News** (biggest story of the day from any lab or company), and **What People Are Saying** (a hot Reddit/HackerNews discussion or community reaction worth knowing about).

CRITICAL RULES — read carefully:
- NO EMPTY SECTIONS: Every section must have at least 1 bullet. Never write "Nothing notable today." If a section has no new articles from the feeds, write 1 bullet from your own knowledge — a genuinely useful or surprising thing about that tool: a lesser-known feature, a smart use case, something that changed recently, or something most people don't know. No URL needed in that case.
- FRESHNESS: Do NOT recycle obvious, well-known, months-old product features as if they are news (e.g. "NotebookLM can turn PDFs into podcasts" — everyone knows this). Be specific and interesting.
- REAL URLs ONLY: If an article has a URL in the data above, end the bullet with (Source: URL) — copy it exactly. NEVER invent or guess a URL. No URL is better than a wrong one.
- TONE: Write like a smart friend texting you the interesting stuff — not a press release. 1-2 sentences per bullet.
- MAX 3 bullets per section. Quality over quantity.
- After the 5 sections, add: **Tip of the Day** — one specific, actionable thing to try RIGHT NOW with any AI tool.
- Then add the podcast episode section below (use EXACTLY the info provided — do not change anything).
- End with: **Today's Key Takeaway:** one sentence on the single most important or surprising thing from today.

Today's podcast episode to include verbatim:
{podcast_block}

Format:
**Claude & Anthropic**
• [bullet] (Source: URL if available)

**Gemini & Google AI**
• [bullet] (Source: URL if available)

**AI Agents & Tools**
• [bullet] (Source: URL if available)

**AI News**
• [bullet] (Source: URL if available)

**What People Are Saying**
• [hot community discussion or reaction] (Source: URL if available)

**Tip of the Day**
• [one specific thing to try now]

**Podcast Episode of the Day**
🎙️ [Show — "Episode Title" (ID) with Guest — Duration]
[2-3 sentences on why THIS specific episode is worth your time today]
Search on Spotify: "[search term]"

**Today's Key Takeaway:** [one sentence]
"""

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2200,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        return message.content[0].text.strip()

    except ImportError:
        return _fallback_digest(articles, reason="anthropic package not installed")
    except Exception as e:
        return _fallback_digest(articles, reason=f"API call failed: {e}")


def _fallback_digest(articles: list[dict], reason: str = "") -> str:
    """
    Simple fallback: lists article titles grouped by topic.
    Used when the API key is missing or the Claude call fails.
    """
    lines = ["=== AI News Digest (fallback mode) ==="]
    if reason:
        lines.append(f"Note: {reason}\n")

    by_topic: dict[str, list[dict]] = defaultdict(list)
    for article in articles:
        topic = article.get("topic", "Other")
        by_topic[topic].append(article)

    for topic in ["Claude Code", "Gemini", "NotebookLM"]:
        lines.append(f"\n{topic}")
        lines.append("-" * len(topic))
        topic_articles = by_topic.get(topic, [])
        if topic_articles:
            for a in topic_articles:
                title = a.get("title", "No title")
                source = a.get("source", "Unknown source")
                published = a.get("published", "")
                date_str = f" ({published})" if published else ""
                lines.append(f"• {title} — {source}{date_str}")
        else:
            lines.append("• No updates today.")

    # Include any topics not in the main three
    other_topics = [t for t in by_topic if t not in ("Claude Code", "Gemini", "NotebookLM")]
    if other_topics:
        lines.append("\nOther")
        lines.append("-----")
        for topic in other_topics:
            for a in by_topic[topic]:
                title = a.get("title", "No title")
                lines.append(f"• [{topic}] {title}")

    return "\n".join(lines)


if __name__ == "__main__":
    # Quick test with 2 fake articles
    fake_articles = [
        {
            "title": "Claude Code Now Supports Multi-File Editing",
            "link": "https://example.com/claude-code-multi-file",
            "source": "Anthropic Blog",
            "published": "2026-03-15",
            "summary": (
                "Anthropic released an update to Claude Code that lets developers "
                "edit multiple files in a single conversation turn, saving time on "
                "large refactoring tasks."
            ),
            "topic": "Claude Code",
        },
        {
            "title": "Gemini 2.0 Adds Real-Time Voice Translation",
            "link": "https://example.com/gemini-voice-translation",
            "source": "Google DeepMind",
            "published": "2026-03-15",
            "summary": (
                "Google's Gemini 2.0 model can now translate spoken conversations "
                "in real time across 30 languages, with low latency suitable for "
                "live meetings."
            ),
            "topic": "Gemini",
        },
    ]

    print("Running summarize_news() with 2 fake articles...\n")
    result = summarize_news(fake_articles)
    print(result)
