"""
becon_summarizer.py — Claude-powered summarizer for the Behavioral Economics digest.
"""

import os
from collections import defaultdict


def summarize_becon(articles: list[dict]) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback(articles, reason="ANTHROPIC_API_KEY not set")

    by_topic: dict[str, list[dict]] = defaultdict(list)
    for a in articles:
        by_topic[a.get("topic", "Other")].append(a)

    articles_text = ""
    topics = [
        "Behavioral Economics",
        "Behavioral Game Theory",
        "Experiments & Methods",
        "Applied Behavioral",
    ]
    for topic in topics:
        topic_articles = by_topic.get(topic, [])
        articles_text += f"\n### {topic}\n"
        if topic_articles:
            for a in topic_articles[:5]:
                articles_text += (
                    f"- Title: {a.get('title', 'No title')}\n"
                    f"  Authors: {a.get('authors', 'Unknown')}\n"
                    f"  Journal/Source: {a.get('source', 'Unknown')}\n"
                    f"  URL: {a.get('link', '')}\n"
                    f"  Published: {a.get('published', 'Unknown')}\n"
                    f"  Abstract: {a.get('summary', 'No abstract available')}\n"
                )
        else:
            articles_text += "(no new papers found)\n"

    prompt = f"""You are writing a daily research briefing email for someone who is intellectually curious about behavioral economics and behavioral game theory — not a professional academic, but smart, well-read, and genuinely interested in how people actually make decisions (not how textbooks say they should).

Here are today's new papers and articles from top journals and NBER — none of these have appeared in a previous digest:
{articles_text}

Write a digest with 4 sections:

**Behavioral Economics** — new findings on how humans deviate from "rational" choice: biases, heuristics, nudges, framing, present bias, etc.
**Behavioral Game Theory** — new findings on social preferences, strategic interaction, fairness, cooperation, and experimental games.
**Experiments & Methods** — notable new lab or field experiments, or methodological advances worth knowing about.
**Applied Behavioral** — behavioral research applied to real-world policy: health, savings, poverty, education, finance, etc.

RULES:
- Every section MUST have at least 1 bullet. Never write "Nothing new today" or leave a section empty.
- If a section has new papers from the feeds above: cover those, ending each bullet with (Source: URL) — exact URL only, never invented.
- If a section has no new papers: write 1-2 bullets drawing from your knowledge of the field — a classic foundational finding, an important concept, a famous experiment, a counterintuitive result, or an idea that changed how economists think. Present it as "worth knowing" context, not as breaking news. No URL needed in this case.
- NEVER present old knowledge as a new discovery. If it's a classic, say so naturally ("One of the most replicated findings in behavioral economics..." or "A concept worth revisiting...").
- For each item: what was studied or what is the concept, what the finding/insight is, and why it matters practically. 2-3 plain-English sentences. No jargon without explanation.
- Max 3 bullets per section.
- After the 4 sections, add:

**Paper of the Week** — pick the single most interesting or surprising result from today's batch and explain it in 4-5 sentences, like you're telling a curious friend about it over coffee. Go deeper here than the section bullets.

**One Idea to Sit With** — one sentence: a question or implication raised by today's research that is worth thinking about.

Format exactly:
**Behavioral Economics**
• [finding — what, result, why it matters] (Source: URL if available)

**Behavioral Game Theory**
• [finding] (Source: URL if available)

**Experiments & Methods**
• [finding] (Source: URL if available)

**Applied Behavioral**
• [finding] (Source: URL if available)

**Paper of the Week**
[4-5 sentences going deeper on the most interesting result]

**One Idea to Sit With**
[one sentence question or implication]
"""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    except ImportError:
        return _fallback(articles, reason="anthropic package not installed")
    except Exception as e:
        return _fallback(articles, reason=f"API call failed: {e}")


def _fallback(articles: list[dict], reason: str = "") -> str:
    lines = ["=== Behavioral Economics Digest (fallback mode) ==="]
    if reason:
        lines.append(f"Note: {reason}\n")
    for a in articles:
        lines.append(f"• [{a.get('topic')}] {a.get('title')} — {a.get('source')} ({a.get('published')})")
    return "\n".join(lines)
