"""
summarizer.py — Agent 2 (Summarizer) for AI News Digest
Generates a clean daily digest from collected news articles using Claude.
"""

import os
from collections import defaultdict
from podcasts import pick_podcast_of_the_day


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

    # Pick today's podcast recommendation
    podcast = pick_podcast_of_the_day()
    podcast_block = (
        f"Name: {podcast['name']}\n"
        f"Host: {podcast['host']}\n"
        f"Category: {podcast['category']}\n"
        f"Why listen: {podcast['why']}\n"
        f"Search on Spotify: \"{podcast['spotify_search']}\""
    )

    # Group articles by topic for the prompt
    by_topic: dict[str, list[dict]] = defaultdict(list)
    for article in articles:
        topic = article.get("topic", "Other")
        by_topic[topic].append(article)

    # Build the articles section of the prompt
    articles_text = ""
    for topic in ["Claude Code", "Gemini", "NotebookLM", "AI Agents"]:
        topic_articles = by_topic.get(topic, [])
        articles_text += f"\n### {topic}\n"
        if topic_articles:
            for a in topic_articles:
                articles_text += (
                    f"- Title: {a.get('title', 'No title')}\n"
                    f"  URL: {a.get('link', '')}\n"
                    f"  Published: {a.get('published', 'Unknown date')}\n"
                    f"  Summary: {a.get('summary', 'No summary available')}\n"
                )
        else:
            articles_text += "(no articles found in feeds)\n"

    prompt = f"""You are writing a daily AI digest email for a curious non-technical reader who wants to learn something new every single day.

Here are the real articles fetched from RSS feeds today (URLs are real — use them exactly):
{articles_text}

Write a digest with exactly 4 sections: **Claude Code**, **Gemini**, **NotebookLM**, and **AI Agents** (covering tools like AutoGPT, CrewAI, LangGraph, n8n, OpenAI Agents SDK, and similar agentic AI tools).

IMPORTANT RULES:
- Every section MUST have at least 1 bullet. Never write "No updates today."
- If a section has no articles, share ONE genuinely useful thing from your own knowledge — a real feature, tip, or use case. Do NOT invent a URL in this case — just omit the source link entirely.
- If a section HAS articles with a URL, end the bullet with: (Source: URL) — copy the URL exactly as given above, do NOT modify or invent URLs.
- NEVER make up or guess any URL. A missing source is better than a wrong one.
- Each bullet is 1-2 sentences: what it is + how the reader can use it today.
- Maximum 4 bullets per section.
- Simple English only — explain it like talking to a smart friend, not a developer.
- Focus on things that are actually useful or surprising. Skip boring press releases.
- After the 4 sections, add: **Tip of the Day** — one specific, actionable thing to try right now.
- Then add a **Podcast of the Day** section using EXACTLY the podcast info provided below — do not change or invent anything, just present it warmly in 2-3 sentences.
- End with: "Today's Key Takeaway:" — one sentence on the most important thing.

Today's podcast to include:
{podcast_block}

Format:
**Claude Code**
• [bullet]. (Source: https://real-url-from-above)

**Gemini**
• [bullet]. (Source: https://real-url-from-above)

**NotebookLM**
• [bullet]

**AI Agents**
• [bullet]. (Source: https://real-url-from-above)

**Tip of the Day**
• [one specific thing to try]

**Podcast of the Day**
🎙️ [podcast name and host, then 2-3 warm sentences about why it's worth your time]. Search for it on Spotify: "[search term]"

Today's Key Takeaway: [one sentence]
"""

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1800,
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
