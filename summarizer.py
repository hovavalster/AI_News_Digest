"""
summarizer.py — AI News Digest summarizer.
"""

import os
from collections import defaultdict
from datetime import date
from podcasts import pick_episode_of_the_day
from ai_tools import pick_tool_of_the_day


def summarize_news(articles: list[dict]) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_digest(articles, reason="ANTHROPIC_API_KEY not set")

    today = date.today()
    is_friday = today.weekday() == 4

    # Podcast episode
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

    # Tool spotlight
    tool = pick_tool_of_the_day()
    tool_block = (
        f"Name: {tool['name']}\n"
        f"Category: {tool['category']}\n"
        f"What it does: {tool['what']}\n"
        f"Try this: {tool['try_this']}\n"
        f"URL: {tool['url']}"
    )

    # Group articles by topic
    by_topic: dict[str, list[dict]] = defaultdict(list)
    for article in articles:
        by_topic[article.get("topic", "Other")].append(article)

    articles_text = ""
    for topic in ["Claude Code", "Gemini", "NotebookLM", "AI Agents", "AI News"]:
        topic_articles = by_topic.get(topic, [])
        articles_text += f"\n### {topic}\n"
        if topic_articles:
            for a in topic_articles[:6]:
                articles_text += (
                    f"- Title: {a.get('title', 'No title')}\n"
                    f"  URL: {a.get('link', '')}\n"
                    f"  Source: {a.get('source', '')}\n"
                    f"  Published: {a.get('published', 'Unknown date')}\n"
                    f"  Summary: {a.get('summary', 'No summary available')}\n"
                )
        else:
            articles_text += "(no articles found in feeds)\n"

    friday_instruction = ""
    friday_section = ""
    if is_friday:
        friday_instruction = (
            "- Since today is Friday, add a **Best of the Week** section at the end "
            "(before the podcast): 3 bullets recapping the most important AI stories "
            "or ideas from this week. Draw from the articles above and your knowledge "
            "of what happened in AI this week."
        )
        friday_section = "\n**Best of the Week**\n• [story 1]\n• [story 2]\n• [story 3]\n"

    prompt = f"""You are writing a concise AI digest email for a curious, non-technical reader who follows AI closely. Keep it tight — every word should earn its place.

Today's fresh articles (ALL new — not previously sent):
{articles_text}

Today's Tool Spotlight to include verbatim at the end:
{tool_block}

Today's Podcast Episode to include verbatim at the end:
{podcast_block}

Write the digest in this exact order and format:

---

📊 **One Number**
[One striking AI statistic or data point from this week — something that puts the current AI moment in perspective. 1 sentence.]

---

**Claude & Anthropic**
• [Beginner] or [Deep Dive] tag — then bullet. (Source: URL if from feeds)

**Gemini & Google AI**
• [tag] — bullet. (Source: URL if from feeds)

**AI Agents & Tools**
• [tag] — bullet. (Source: URL if from feeds)

**AI News**
• [tag] — bullet. (Source: URL if from feeds)

**What People Are Saying**
• [tag] — hot community discussion or reaction. (Source: URL if from feeds)

---

💡 **Prompt of the Day**
[A specific, copy-paste-ready prompt. 2-3 sentences max: one line for the prompt itself, one line on what to use it for.]

---

🛠️ **Tool Spotlight: {tool['name']}** ({tool['category']})
[Use EXACTLY the tool info provided above. 1-2 sentences on what it does and why it's useful, then the Try This tip, then the URL.]

---

🎙️ **Podcast Episode of the Day**
[Use EXACTLY the podcast info provided above. Format: Show — Episode (ID) — Guest — Duration, then 1-2 sentences on why this episode is worth listening to.]
Search on Spotify: "[search term]"
{friday_section}
---

**Today's Key Takeaway:** [one sentence — the single most important thing from today]

---

RULES:
- Tag each news bullet [Beginner], [Intermediate], or [Deep Dive].
- NO EMPTY SECTIONS. If no articles for a section, write 1 bullet from your knowledge — specific, not generic. No invented URL.
- Real URLs only — copy exactly from the feeds data. Never invent one.
- 1 sentence per news bullet. Max 2 bullets per section.
- Friendly, smart tone — like a well-informed friend, not a press release.
{friday_instruction}
"""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1900,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    except ImportError:
        return _fallback_digest(articles, reason="anthropic package not installed")
    except Exception as e:
        return _fallback_digest(articles, reason=f"API call failed: {e}")


def _fallback_digest(articles: list[dict], reason: str = "") -> str:
    lines = ["=== AI News Digest (fallback mode) ==="]
    if reason:
        lines.append(f"Note: {reason}\n")
    by_topic: dict[str, list[dict]] = defaultdict(list)
    for article in articles:
        by_topic[article.get("topic", "Other")].append(article)
    for topic in ["Claude Code", "Gemini", "NotebookLM", "AI Agents", "AI News"]:
        lines.append(f"\n{topic}")
        for a in by_topic.get(topic, []):
            lines.append(f"• {a.get('title')} — {a.get('source')} ({a.get('published')})")
        if not by_topic.get(topic):
            lines.append("• No updates today.")
    return "\n".join(lines)
