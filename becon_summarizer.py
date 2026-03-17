"""
becon_summarizer.py — Behavioral Economics digest summarizer.
"""

import os
from collections import defaultdict
from datetime import date


# ---------------------------------------------------------------------------
# Classic Papers — rotate by week of year (52 weeks → 52 papers)
# ---------------------------------------------------------------------------

CLASSIC_PAPERS: list[dict] = [
    {
        "title": "Prospect Theory: An Analysis of Decision under Risk",
        "authors": "Daniel Kahneman & Amos Tversky",
        "year": 1979, "journal": "Econometrica",
        "what": "People evaluate outcomes as gains/losses relative to a reference point, weight losses roughly 2.25x more than equivalent gains, and overweight small probabilities.",
        "why": "The most cited paper in economics. Replaced expected utility theory as the standard descriptive model of risky choice.",
    },
    {
        "title": "Toward a Positive Theory of Consumer Choice",
        "authors": "Richard Thaler",
        "year": 1980, "journal": "Journal of Economic Behavior & Organization",
        "what": "Introduced mental accounting — people segregate money into mental 'buckets' (rent, food, entertainment) and treat each differently, violating fungibility.",
        "why": "Explains why people make inconsistent financial decisions and forms the foundation of behavioral finance.",
    },
    {
        "title": "A Fine is a Price",
        "authors": "Uri Gneezy & Aldo Rustichini",
        "year": 2000, "journal": "Journal of Legal Studies",
        "what": "A daycare introduced a fine for late pickups — and late pickups increased. The fine replaced a social norm with a market transaction, removing guilt.",
        "why": "Classic proof that economic incentives can crowd out social/moral motivations, undermining the naive assumption that penalties always reduce bad behavior.",
    },
    {
        "title": "Libertarian Paternalism Is Not an Oxymoron",
        "authors": "Richard Thaler & Cass Sunstein",
        "year": 2003, "journal": "University of Chicago Law Review",
        "what": "Proposed 'nudges' — designing choice architectures that steer people toward better outcomes while preserving freedom of choice.",
        "why": "The intellectual foundation of nudge theory, later implemented by governments worldwide (UK Behavioural Insights Team, Obama's OIRA).",
    },
    {
        "title": "The Power of Suggestion: Inertia in 401(k) Participation",
        "authors": "Brigitte Madrian & Dennis Shea",
        "year": 2001, "journal": "Quarterly Journal of Economics",
        "what": "Simply switching 401(k) enrollment from opt-in to opt-out raised participation from 37% to 86% — same plan, same people, different default.",
        "why": "The single most impactful piece of applied behavioral research. Led to automatic enrollment becoming standard in retirement plans across the US.",
    },
    {
        "title": "Cooperation and Punishment in Public Goods Experiments",
        "authors": "Ernst Fehr & Simon Gächter",
        "year": 2000, "journal": "American Economic Review",
        "what": "People will pay their own money to punish free-riders in public goods games — even in one-shot games where they'll never meet again. Altruistic punishment.",
        "why": "Explains how cooperation is sustained in large groups of strangers. Overturned the prediction that free-riding would destroy cooperation.",
    },
    {
        "title": "Incorporating Fairness into Game Theory and Economics",
        "authors": "Matthew Rabin",
        "year": 1993, "journal": "American Economic Review",
        "what": "Formalized fairness as a payoff component — people are willing to sacrifice material gains to reward kind behavior and punish unkind behavior.",
        "why": "Launched behavioral game theory as a field. The first formal model integrating reciprocity into standard economic framework.",
    },
    {
        "title": "Coherent Arbitrariness",
        "authors": "Dan Ariely, George Loewenstein & Drazen Prelec",
        "year": 2003, "journal": "Quarterly Journal of Economics",
        "what": "People's first stated willingness-to-pay for a product is heavily influenced by an arbitrary anchor (e.g., the last 2 digits of their Social Security number), yet subsequent valuations are internally consistent.",
        "why": "Shows that preferences are not pre-formed and stable — they are constructed in the moment, shaped by irrelevant anchors.",
    },
    {
        "title": "Paying Not to Go to the Gym",
        "authors": "Stefano DellaVigna & Ulrike Malmendier",
        "year": 2006, "journal": "American Economic Review",
        "what": "Gym members who chose monthly flat-fee contracts paid an average of $17 per visit — while the pay-per-visit rate was $10. They consistently overestimated how often they'd go.",
        "why": "Landmark evidence of present bias and overconfidence in self-control. The gym industry's pricing exploits predictable human irrationality.",
    },
    {
        "title": "Anomalies in Intertemporal Choice",
        "authors": "George Loewenstein & Drazen Prelec",
        "year": 1992, "journal": "Quarterly Journal of Economics",
        "what": "Documented systematic violations of exponential discounting: people are far more impatient about immediate vs. near-future trade-offs than about distant future ones.",
        "why": "The definitive paper establishing hyperbolic discounting as a better model of time preferences than the standard exponential model.",
    },
    {
        "title": "Experimental Tests of the Endowment Effect",
        "authors": "Daniel Kahneman, Jack Knetsch & Richard Thaler",
        "year": 1990, "journal": "Journal of Political Economy",
        "what": "People randomly given a coffee mug demanded about twice as much to sell it as others were willing to pay to buy it — simply owning something raises its subjective value.",
        "why": "The definitive experimental proof of the endowment effect. Challenges the Coase theorem's assumption that ownership doesn't affect value.",
    },
    {
        "title": "Does Market Experience Eliminate Market Anomalies?",
        "authors": "John List",
        "year": 2003, "journal": "Quarterly Journal of Economics",
        "what": "Professional traders at a sportscard market showed no endowment effect, while casual consumers showed a strong one — market experience erodes the bias.",
        "why": "Critical pushback on lab findings. Suggests behavioral biases may be weaker in real markets where people learn, raising questions about external validity.",
    },
    {
        "title": "Salience and Taxation: Theory and Evidence",
        "authors": "Raj Chetty, Adam Looney & Kory Kroft",
        "year": 2009, "journal": "American Economic Review",
        "what": "Posting tax-inclusive prices on grocery store shelves reduced purchases by 8% compared to the standard tax-exclusive display — consumers respond to visible, not just actual, prices.",
        "why": "Formal proof that tax salience matters for behavior. Has major implications for how tax policy is communicated.",
    },
    {
        "title": "Social Preferences: Some Simple Tests and a New Model",
        "authors": "Gary Charness & Matthew Rabin",
        "year": 2002, "journal": "Quarterly Journal of Economics",
        "what": "People care about both efficiency (making the total pie bigger) and fairness — but efficiency concerns are stronger than inequality aversion in most situations.",
        "why": "Refined the model of social preferences, showing that fairness is more nuanced than simple inequality aversion.",
    },
    {
        "title": "A Dual-Self Model of Impulse Control",
        "authors": "Drew Fudenberg & David Levine",
        "year": 2006, "journal": "American Economic Review",
        "what": "Models the self as two agents: a patient 'planner' who sets goals and an impatient 'doer' who acts in the moment. Self-control is the planner constraining the doer.",
        "why": "A rigorous economic framework for self-control that bridges behavioral and standard economics.",
    },
    {
        "title": "Temptation and Self-Control",
        "authors": "Faruk Gul & Wolfgang Pesendorfer",
        "year": 2001, "journal": "Econometrica",
        "what": "People suffer disutility simply from being tempted — even if they successfully resist. Removing temptation from the choice set can therefore increase welfare.",
        "why": "The formal foundation for why commitment devices (Ulysses contracts, savings locks) have value even when never actually binding.",
    },
    {
        "title": "Giving According to GARP: An Experimental Test of Rationality",
        "authors": "James Andreoni & John Miller",
        "year": 2002, "journal": "Econometrica",
        "what": "Most subjects in dictator games satisfy the axioms of rational choice — their giving is consistent with utility maximization, just with utility that includes others' payoffs.",
        "why": "Showed that altruism can be modeled within the rational choice framework — people aren't irrational, they just have other-regarding preferences.",
    },
    {
        "title": "Labor Supply of New York City Cab Drivers",
        "authors": "Colin Camerer, Linda Babcock, George Loewenstein & Richard Thaler",
        "year": 1997, "journal": "Quarterly Journal of Economics",
        "what": "NYC cab drivers set a daily income target and quit when they hit it — working fewer hours on busy days (high wages) and more on slow days. The opposite of standard labor supply.",
        "why": "Field evidence of present-biased, target-based preferences in a real market. Launched a large literature on reference-dependent labor supply.",
    },
    {
        "title": "The Behavioural Insights Team: Early Findings",
        "authors": "UK Cabinet Office / BIT",
        "year": 2012, "journal": "Cabinet Office Report",
        "what": "A series of RCTs by the UK's nudge unit showed that adding social norms ('9 out of 10 people in your area pay on time') to tax letters increased on-time payment by up to 15%.",
        "why": "The most influential real-world application of behavioral economics to government policy. Spawned similar units in 200+ governments worldwide.",
    },
    {
        "title": "Stereotypes as Heuristics: A Dual Process Account",
        "authors": "Gerd Gigerenzer & Wolfgang Gaissmaier",
        "year": 2011, "journal": "Psychological Review",
        "what": "Heuristics are not just cognitive shortcuts that lead to error — in many real-world environments, simple rules outperform complex optimization because they are robust to noise.",
        "why": "Important corrective to the Kahneman/Tversky tradition: bounded rationality isn't just about bias, it's about ecological fit of decision strategies.",
    },
    {
        "title": "The Impact of Irrelevant Alternatives",
        "authors": "Itamar Simonson & Amos Tversky",
        "year": 1992, "journal": "Journal of Marketing Research",
        "what": "Adding an inferior 'decoy' option to a choice set systematically increases preference for the option it most resembles — the compromise effect.",
        "why": "Explains a common retail pricing strategy (the 'decoy effect') and shows that preferences are not stable across choice sets.",
    },
    {
        "title": "Identity Economics",
        "authors": "George Akerlof & Rachel Kranton",
        "year": 2000, "journal": "Quarterly Journal of Economics",
        "what": "People's social identities (gender, ethnicity, profession) shape what they believe they 'should' do, creating utility from conforming to identity norms and disutility from violating them.",
        "why": "Introduced identity as a formal economic variable, explaining phenomena like gender gaps in STEM and worker motivation beyond monetary incentives.",
    },
]


def _pick_classic_paper() -> dict:
    """Returns a classic paper based on week of year — rotates every 52 weeks."""
    week = date.today().isocalendar()[1]
    return CLASSIC_PAPERS[week % len(CLASSIC_PAPERS)]


def summarize_becon(articles: list[dict]) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback(articles, reason="ANTHROPIC_API_KEY not set")

    today = date.today()
    is_friday = today.weekday() == 4

    by_topic: dict[str, list[dict]] = defaultdict(list)
    for a in articles:
        by_topic[a.get("topic", "Other")].append(a)

    articles_text = ""
    for topic in ["Behavioral Economics", "Behavioral Game Theory", "Experiments & Methods", "Applied Behavioral"]:
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

    # Classic paper of the week
    cp = _pick_classic_paper()
    classic_block = (
        f"Title: \"{cp['title']}\"\n"
        f"Authors: {cp['authors']} ({cp['year']}) — {cp['journal']}\n"
        f"What it found: {cp['what']}\n"
        f"Why it matters: {cp['why']}"
    )

    friday_instruction = ""
    friday_section = ""
    if is_friday:
        friday_instruction = (
            "- Since today is Friday, add a **Best of the Week** section "
            "(after Applied Behavioral, before Paper of the Week): 3 bullets "
            "recapping the most important behavioral economics findings or ideas "
            "from this week. Draw from today's articles and your broader knowledge."
        )
        friday_section = "\n**Best of the Week**\n• [finding 1]\n• [finding 2]\n• [finding 3]\n"

    prompt = f"""You are writing a daily research briefing for someone intellectually curious about behavioral economics and behavioral game theory — smart and well-read, not a professional academic.

Today's new papers (none previously sent):
{articles_text}

This week's Classic Paper to feature verbatim at the end:
{classic_block}

Write in this exact order and format:

---

📊 **One Number**
[One striking statistic or data point from behavioral economics research — something concrete that illustrates how irrational or surprising human behavior is. 1 sentence. Can be from today's papers or your knowledge.]

---

**Behavioral Economics**
• [Beginner] or [Deep Dive] tag — finding: what was studied, what they found, why it matters. (Source: URL if from feeds)

**Behavioral Game Theory**
• [tag] — finding. (Source: URL if from feeds)

**Experiments & Methods**
• [tag] — finding. (Source: URL if from feeds)

**Applied Behavioral**
• [tag] — finding. (Source: URL if from feeds)

---

🌍 **In the Wild**
[One place where today's research concepts are already being used in a real product, company, or government policy. Be specific — name the organization, country, or product. 2-3 sentences.]

---

⚖️ **Policy Watch**
[One government, central bank, or institution currently applying behavioral insights to a real policy challenge. Be specific and current. 2-3 sentences.]

---

🔬 **Field vs. Lab**
[One sentence flagging a case where a lab finding does or doesn't hold up in the real world — either from today's papers or a well-known example. Frame it as a useful reality check.]
{friday_section}
---

**Paper of the Week**
[4-5 sentences on the single most interesting result from today — explain it like telling a curious friend over coffee. Go deeper than the section bullets.]

---

📚 **Classic Paper of the Week**
[Use EXACTLY the classic paper info provided above. 3-4 sentences: what they did, what they found, and why it's still relevant today. Present it as a foundational piece worth knowing.]

---

**One Idea to Sit With**
[One sentence — a question or implication from today's research worth thinking about.]

---

RULES:
- Tag each research bullet [Beginner] or [Deep Dive].
- NO EMPTY SECTIONS. If no new papers for a section, draw from your knowledge — a classic finding, an important concept, a famous experiment. No invented URL.
- Real URLs only — copy exactly from the feeds data above.
- 2-3 plain-English sentences per bullet. No jargon without explanation.
- Max 3 bullets per section.
- Never present classic knowledge as new. If it's a classic, say so.
{friday_instruction}
"""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2800,
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
