"""
podcasts.py — Curated daily podcast recommendation for AI News Digest.

All podcasts are real, widely known, and available on Spotify.
One is selected per day using a date-based rotation (same pick for the whole day).
"""

from datetime import date

# ---------------------------------------------------------------------------
# Curated list — AI, business, tech, culture, all famous & widely heard
# ---------------------------------------------------------------------------
PODCASTS: list[dict] = [
    {
        "name": "Lex Fridman Podcast",
        "host": "Lex Fridman",
        "category": "AI & Science",
        "why": "Deep, long-form conversations with the world's leading AI researchers, scientists, and entrepreneurs. Guests have included Elon Musk, Sam Altman, and Geoffrey Hinton.",
        "spotify_search": "Lex Fridman Podcast",
    },
    {
        "name": "Hard Fork",
        "host": "Kevin Roose & Casey Newton (The New York Times)",
        "category": "AI & Tech",
        "why": "The New York Times' weekly tech podcast — smart, funny, and accessible. They cover AI news the way a very well-informed friend would explain it over lunch.",
        "spotify_search": "Hard Fork NYT",
    },
    {
        "name": "Pivot",
        "host": "Kara Swisher & Scott Galloway",
        "category": "Business & Tech",
        "why": "Two of the most opinionated voices in tech debate the week's biggest stories. Fast-paced, sharp, and never boring — great for business and AI news together.",
        "spotify_search": "Pivot Kara Swisher Scott Galloway",
    },
    {
        "name": "All-In Podcast",
        "host": "Chamath Palihapitiya, Jason Calacanis, David Sacks & David Friedberg",
        "category": "Business & Tech",
        "why": "Four Silicon Valley billionaires give unfiltered takes on tech, AI, politics, and markets every week. Love them or hate them, they're always interesting.",
        "spotify_search": "All-In Podcast",
    },
    {
        "name": "Acquired",
        "host": "Ben Gilbert & David Rosenthal",
        "category": "Business History",
        "why": "Incredibly deep storytelling about how the world's greatest companies — NVIDIA, Apple, Amazon, OpenAI — were actually built. Episodes are long but feel like movies.",
        "spotify_search": "Acquired Podcast",
    },
    {
        "name": "How I Built This",
        "host": "Guy Raz (NPR)",
        "category": "Entrepreneurship",
        "why": "Founders of iconic companies — Airbnb, Spanx, Instagram — tell the real, messy story of how they started. Perfect if you like building things or thinking about startups.",
        "spotify_search": "How I Built This NPR Guy Raz",
    },
    {
        "name": "Masters of Scale",
        "host": "Reid Hoffman (LinkedIn co-founder)",
        "category": "Business & Entrepreneurship",
        "why": "Reid Hoffman interviews world-class founders and CEOs to uncover the counterintuitive rules behind scaling companies. Guests include Mark Zuckerberg, Reed Hastings, and more.",
        "spotify_search": "Masters of Scale Reid Hoffman",
    },
    {
        "name": "No Priors",
        "host": "Sarah Guo & Elad Gil",
        "category": "AI & Venture Capital",
        "why": "Two top AI investors interview the people actually building frontier AI — researchers, founders, and lab leaders. Very insider, very current.",
        "spotify_search": "No Priors AI Podcast",
    },
    {
        "name": "My First Million",
        "host": "Sam Parr & Shaan Puri",
        "category": "Business Ideas & Entrepreneurship",
        "why": "Two entrepreneurs brainstorm business ideas, share how they'd build them today using AI tools, and interview interesting builders. High energy and very practical.",
        "spotify_search": "My First Million Podcast",
    },
    {
        "name": "The Tim Ferriss Show",
        "host": "Tim Ferriss",
        "category": "Personal Development & Business",
        "why": "Tim deconstructs world-class performers — investors, athletes, CEOs — to find the tools and tactics you can apply yourself. One of the longest-running and most downloaded podcasts ever.",
        "spotify_search": "Tim Ferriss Show",
    },
    {
        "name": "a16z Podcast",
        "host": "Andreessen Horowitz",
        "category": "Tech & Venture Capital",
        "why": "The team at one of Silicon Valley's most influential VC firms breaks down big ideas in AI, software, and the future of technology — always forward-looking.",
        "spotify_search": "a16z Podcast",
    },
    {
        "name": "Latent Space",
        "host": "Alessio Fanelli & swyx",
        "category": "AI Engineering",
        "why": "The best technical AI podcast for understanding what's actually happening in AI research and engineering. Guests are the engineers and researchers building the tools you use.",
        "spotify_search": "Latent Space Podcast AI",
    },
    {
        "name": "20VC",
        "host": "Harry Stebbings",
        "category": "Venture Capital & Startups",
        "why": "Harry interviews the world's top venture capitalists and startup founders. He asks the questions everyone wants to know but doesn't always ask — blunt and fast-paced.",
        "spotify_search": "20VC Harry Stebbings",
    },
    {
        "name": "Darknet Diaries",
        "host": "Jack Rhysider",
        "category": "Cybersecurity & Tech",
        "why": "True stories from the dark side of the internet — hacks, data breaches, and espionage told like thrillers. Some of the best storytelling in tech podcasting.",
        "spotify_search": "Darknet Diaries",
    },
    {
        "name": "The Daily",
        "host": "Michael Barbaro (The New York Times)",
        "category": "News",
        "why": "The most listened-to podcast in the world. 20 minutes every weekday, one big story explained clearly. A great habit if you want to stay informed without doomscrolling.",
        "spotify_search": "The Daily New York Times",
    },
    {
        "name": "Huberman Lab",
        "host": "Andrew Huberman (Stanford neuroscientist)",
        "category": "Science & Productivity",
        "why": "A Stanford neuroscientist explains the science behind focus, sleep, performance, and health — all with practical protocols you can use immediately. Wildly popular for good reason.",
        "spotify_search": "Huberman Lab Podcast",
    },
    {
        "name": "Invest Like the Best",
        "host": "Patrick O'Shaughnessy",
        "category": "Investing & Business",
        "why": "Conversations with the world's best investors and business builders. Goes deep on how they think, not just what they did. Essential listening for anyone interested in markets.",
        "spotify_search": "Invest Like the Best Podcast",
    },
    {
        "name": "Eye on AI",
        "host": "Craig S. Smith",
        "category": "AI & Business",
        "why": "Weekly interviews with AI researchers and executives about what's actually happening in artificial intelligence — calm, intelligent, and jargon-free.",
        "spotify_search": "Eye on AI Podcast",
    },
    {
        "name": "The Knowledge Project",
        "host": "Shane Parrish (Farnam Street)",
        "category": "Mental Models & Decision Making",
        "why": "Shane interviews world-class thinkers to extract the mental models and frameworks behind great decisions. If you like thinking about how to think, this is the one.",
        "spotify_search": "The Knowledge Project Shane Parrish",
    },
    {
        "name": "Freakonomics Radio",
        "host": "Stephen Dubner",
        "category": "Economics & Ideas",
        "why": "Uses economics and data to uncover surprising truths about everyday life. One of the most intellectually stimulating podcasts out there — always leaves you with something to think about.",
        "spotify_search": "Freakonomics Radio",
    },
]


def pick_podcast_of_the_day() -> dict:
    """Returns a podcast deterministically based on today's date — same pick all day."""
    day_index = date.today().timetuple().tm_yday  # 1–365
    return PODCASTS[day_index % len(PODCASTS)]
