# CLAUDE.md — AI News Digest

This file documents the codebase structure, conventions, and development workflows for AI assistants working on this repository.

## Project Overview

AI News Digest is a Python-based automated pipeline that:
1. Fetches AI news from RSS feeds
2. Summarizes it using Claude (Anthropic API)
3. Formats it as a styled HTML email
4. Sends it via Gmail SMTP

It runs on a schedule via GitHub Actions every 3 days, with two independent digest variants:
- **AI News Digest** — general AI/ML news from tech blogs, Reddit, HackerNews
- **Behavioral Economics Digest** — academic papers from journals (NBER, AER, QJE, etc.)

---

## Repository Structure

```
AI_News_Digest/
├── .github/workflows/
│   ├── daily_digest.yml        # Schedules & runs news_digest.py every 3 days
│   └── becon_digest.yml        # Schedules & runs becon_digest.py every 3 days
├── data/
│   ├── seen_links.json         # Persisted set of sent AI news article URLs
│   └── becon_seen_links.json   # Persisted set of sent behavioral econ article URLs
├── news_digest.py              # ENTRY POINT: AI news pipeline orchestrator
├── fetcher.py                  # RSS feed fetching & keyword filtering for AI news
├── summarizer.py               # Claude API call + prompt engineering for AI news
├── emailer.py                  # HTML email formatter & Gmail SMTP sender
├── becon_digest.py             # ENTRY POINT: Behavioral econ pipeline orchestrator
├── becon_fetcher.py            # RSS feed fetching for academic journals
├── becon_summarizer.py         # Claude API call for behavioral econ digest
├── ai_tools.py                 # Curated list of 30+ AI tools (date-rotated daily)
├── podcasts.py                 # Curated list of 50+ podcast episodes (date-rotated daily)
├── setup_secrets.py            # One-time utility: push .env secrets to GitHub Actions
├── requirements.txt            # Python dependencies
└── .env.template               # Environment variable template (copy to .env)
```

---

## Key Architecture: Data Pipeline

Both digest variants follow the same 5-step pipeline:

```
Fetch (RSS) → Filter (keywords) → Summarize (Claude API) → Format (HTML) → Send (Gmail SMTP)
                                                                              ↓
                                                            Persist seen URLs → data/*.json
```

**Deduplication:** Each pipeline maintains a JSON file of seen article URLs. After a successful email send, newly covered URLs are appended. GitHub Actions commits the updated JSON file back to the repo with `[skip ci]` to avoid triggering another run.

---

## Running Locally

### Prerequisites

1. Copy `.env.template` to `.env` and fill in all values:
   ```
   ANTHROPIC_API_KEY=your_key_here
   EMAIL_SENDER=you@gmail.com
   EMAIL_PASSWORD=xxxx xxxx xxxx xxxx   # Gmail App Password (16 chars)
   EMAIL_RECIPIENT=recipient@example.com
   ```
   > Gmail App Passwords require 2FA enabled. Generate at https://myaccount.google.com/apppasswords

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Digests

```bash
# AI News Digest
python news_digest.py             # Full run: fetch → summarize → send email
python news_digest.py --dry-run   # Test: fetch & summarize, skip email send

# Behavioral Economics Digest
python becon_digest.py            # Full run
python becon_digest.py --dry-run  # Test mode

# Test individual components
python fetcher.py                 # Print fetched AI articles to console
python emailer.py                 # Generate HTML email preview
```

---

## Module Responsibilities

### `news_digest.py` (188 lines)
Orchestrates the full AI news pipeline. Handles:
- CLI argument parsing (`--dry-run`)
- Loading/saving `data/seen_links.json`
- Filtering already-seen articles before summarization
- Logging (format: `%(asctime)s [%(levelname)s] %(name)s — %(message)s`)
- Exit with non-zero code on failure (so GitHub Actions marks the run as failed)

### `fetcher.py` (288 lines)
Fetches from 16 RSS feeds. Key constants to modify:
- `FEEDS` dict — add/remove RSS sources
- `KEYWORDS` list — terms that qualify an article for inclusion
- `TOPIC_PRIORITY` list — ordered rules mapping keywords → topic labels (`Claude Code`, `Gemini`, `NotebookLM`, `AI Agents`, `AI News`)

**Adaptive window:** tries last 24 hours first; expands to 30 days if fewer than 3 articles found.

### `summarizer.py` (170 lines)
Calls `claude-sonnet-4-6` with a structured prompt. Key behaviors:
- Injects a daily podcast episode (from `podcasts.py`) and AI tool (from `ai_tools.py`) into the digest
- On Fridays (`weekday() == 4`), adds a "Best of the Week" section
- Caps output at `max_tokens=1900`
- Falls back to `_fallback_digest()` (plain text list) if API key is missing or call fails

### `emailer.py` (415 lines)
Converts the plain-text digest to a styled HTML email (620px wide, table layout). Features:
- Color-coded section headers (Claude=blue, Gemini=blue, Agents=orange, etc.)
- Badge pills for difficulty tags: `[Beginner]`, `[Intermediate]`, `[Deep Dive]`
- URL linkification with domain extraction
- Sends to `EMAIL_RECIPIENT` and optionally `EMAIL_RECIPIENT_2` via Gmail SMTP (`smtp.gmail.com:587`)

### `ai_tools.py` (225 lines)
Contains a curated list of 30+ AI tools. `pick_tool_of_the_day()` selects one deterministically by `date.today().toordinal() % len(TOOLS)`, ensuring the same tool appears all day but rotates daily.

### `podcasts.py` (590 lines)
Contains a curated list of 50+ famous AI/ML podcast episodes. `pick_episode_of_the_day()` uses the same date-rotation pattern as `ai_tools.py`.

### `becon_fetcher.py` (289 lines)
Like `fetcher.py` but for academic behavioral economics journals. Uses a different `KEYWORDS` list (behavioral economics, game theory, mechanism design, etc.) and `FEEDS` dict pointing to NBER, AER, QJE, Econometrica, etc.

### `becon_summarizer.py` (320 lines)
Like `summarizer.py` but tailored for academic content. Includes a "Classic Paper of the Week" feature: rotates through a curated list of seminal behavioral economics papers by week of year.

### `setup_secrets.py` (129 lines)
One-time utility (not used in production). Reads local `.env`, encrypts each secret using the repo's public key, and uploads via GitHub API. Requires a GitHub Personal Access Token.

---

## Data Files

### `data/seen_links.json`
- Format: `[{"url": "https://...", "date": "YYYY-MM-DD"}, ...]`
- Entries older than **60 days** are pruned on each save
- Updated after every successful email send; never updated in `--dry-run` mode
- Backward-compatible with old format (plain string list): treated as `date: "2000-01-01"`

### `data/becon_seen_links.json`
- Same format as above
- Entries older than **90 days** are pruned (academic papers have longer relevance)

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Claude API key from console.anthropic.com |
| `EMAIL_SENDER` | Yes | Gmail address used to send digests |
| `EMAIL_PASSWORD` | Yes | Gmail App Password (16-char, requires 2FA) |
| `EMAIL_RECIPIENT` | Yes | Primary recipient email address |
| `EMAIL_RECIPIENT_2` | No | Optional second recipient email address |

All variables are loaded via `python-dotenv` at startup. In GitHub Actions, they come from repository secrets.

---

## GitHub Actions Workflows

### `.github/workflows/daily_digest.yml`
- **Trigger:** Every 3 days at 08:00 UTC, plus manual dispatch
- **Python version:** 3.11
- **Steps:** checkout → install deps → `python news_digest.py` → commit `seen_links.json` back

### `.github/workflows/becon_digest.yml`
- **Trigger:** Every 3 days at 09:00 UTC (offset by 1 hour from AI digest)
- Same structure; runs `becon_digest.py` and commits `becon_seen_links.json`

**Important:** The commit step uses `[skip ci]` in the commit message to prevent an infinite loop. It also runs `git pull --rebase` before push to handle concurrent updates.

---

## Dependencies

```
feedparser==6.0.11    # RSS/Atom feed parsing
anthropic>=0.40.0     # Claude API client
python-dotenv>=1.0.0  # .env file loading
```

Standard library only beyond these three. No web framework, no database.

---

## Coding Conventions

- **Python 3.11+** — uses `dict[str, str]` style type hints (not `Dict` from `typing`)
- **Module-level docstrings** — every file starts with a docstring explaining its purpose
- **Function docstrings** — all public functions have docstrings explaining parameters and return values
- **Logger naming convention:** `logging.getLogger("ai_news_digest.<module>")` — e.g., `ai_news_digest.fetcher`, `ai_news_digest.main`
- **Logging format:** `%(asctime)s [%(levelname)s] %(name)s — %(message)s`
- **No `__init__.py`** — the project is a flat package; modules import each other directly
- **UTF-8 on Windows:** `news_digest.py` reconfigures `sys.stdout`/`sys.stderr` encoding at startup to prevent crashes on accented characters
- **Graceful degradation:** feed fetch failures log a warning and skip that feed; API failures fall back to a plain-text digest
- **No test suite** — testing is done via `--dry-run` flags and `if __name__ == "__main__"` blocks in individual modules

---

## Common Modification Patterns

### Add a new RSS feed (AI news)
Edit `fetcher.py`, add to the `FEEDS` dict:
```python
"New Source Name": "https://example.com/rss.xml",
```

### Add a new keyword filter
Edit `fetcher.py`, append to `KEYWORDS`:
```python
"new keyword",
```

### Add topic labeling for a new keyword
Edit `fetcher.py`, insert into `TOPIC_PRIORITY` (order matters — more specific first):
```python
("new keyword", "AI Agents"),  # or whichever topic bucket
```

### Add a new AI tool to the daily spotlight
Edit `ai_tools.py`, append to the `TOOLS` list following the existing dict structure:
```python
{
    "name": "Tool Name",
    "category": "Category",
    "what": "What it does in one sentence.",
    "try_this": "A specific task to try with the tool.",
    "url": "https://example.com",
},
```

### Add a new podcast episode
Edit `podcasts.py`, append to the `EPISODES` list following the existing dict structure.

### Change the digest schedule
Edit `.github/workflows/daily_digest.yml` and update the cron expression. Current: `0 8 */3 * *` (every 3 days at 08:00 UTC).

### Adjust seen-links retention window
- AI news: change `_SEEN_LINKS_MAX_AGE_DAYS = 60` in `news_digest.py`
- Behavioral econ: change the equivalent constant in `becon_digest.py`

---

## Secrets Setup (First Time)

To configure GitHub Actions secrets for a fresh repo clone:
```bash
# Set GITHUB_TOKEN in .env first, then:
python setup_secrets.py
```

This reads all variables from `.env` (except `GITHUB_TOKEN`) and uploads them as encrypted GitHub Actions secrets using the repo's public key.

---

## Git Commit Style

The project uses conventional commit prefixes:
- `chore:` — automated maintenance (e.g., `chore: update seen_links.json [skip ci]`)
- `feat:` — new features
- `fix:` — bug fixes

The `[skip ci]` tag in automated commits prevents GitHub Actions from re-triggering on the `seen_links.json` update.
