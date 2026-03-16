"""
news_digest.py — Main entry point for the AI News Digest.

Run this script to fetch today's AI news, summarise it with Claude,
and email the result. It is also what GitHub Actions runs on the
daily schedule defined in .github/workflows/daily_digest.yml.

Usage
-----
  python news_digest.py            # full run — fetches, summarises, sends email
  python news_digest.py --dry-run  # skips the email send; just prints the digest
"""

# ── Standard library ────────────────────────────────────────────────────────────
import argparse
import datetime
import json
import logging
import os
import sys

# Force UTF-8 output on Windows (prevents crashes on accented chars from article titles)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Load .env FIRST — before any os.environ.get() calls ────────────────────────
# python-dotenv reads the .env file and injects its contents into os.environ
# so that ANTHROPIC_API_KEY, EMAIL_SENDER, etc. are available everywhere below.
from dotenv import load_dotenv
load_dotenv()  # loads .env from the current working directory (or parents)

# ── Project modules ─────────────────────────────────────────────────────────────
from fetcher    import fetch_news
from summarizer import summarize_news
from emailer    import send_email, format_html

# ── Seen-links persistence ───────────────────────────────────────────────────────
_SEEN_LINKS_FILE = os.path.join(os.path.dirname(__file__), "data", "seen_links.json")
_SEEN_LINKS_MAX_AGE_DAYS = 60  # prune entries older than this


def _load_seen_links() -> dict[str, str]:
    """Return {url: date_str} for all previously sent articles."""
    try:
        with open(_SEEN_LINKS_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        # Support both old format (list of strings) and new format (list of {url, date})
        result = {}
        for item in raw:
            if isinstance(item, str):
                result[item] = "2000-01-01"  # legacy — treat as old
            elif isinstance(item, dict):
                result[item["url"]] = item.get("date", "2000-01-01")
        return result
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_seen_links(seen: dict[str, str], dry_run: bool) -> None:
    """Persist seen links, pruning entries older than _SEEN_LINKS_MAX_AGE_DAYS."""
    if dry_run:
        return
    cutoff = (
        datetime.date.today() - datetime.timedelta(days=_SEEN_LINKS_MAX_AGE_DAYS)
    ).isoformat()
    pruned = [
        {"url": url, "date": date}
        for url, date in seen.items()
        if date >= cutoff
    ]
    os.makedirs(os.path.dirname(_SEEN_LINKS_FILE), exist_ok=True)
    with open(_SEEN_LINKS_FILE, "w", encoding="utf-8") as f:
        json.dump(pruned, f, indent=2)
    logger_placeholder = logging.getLogger("ai_news_digest.main")
    logger_placeholder.info("Saved %d seen links to %s", len(pruned), _SEEN_LINKS_FILE)

# ── Logging ─────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("ai_news_digest.main")


# ── CLI argument parser ──────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    --dry-run  Print the digest to the console but skip sending the email.
               Useful for testing without burning email quota.
    """
    parser = argparse.ArgumentParser(
        description="Fetch, summarise, and email the daily AI news digest."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the digest without sending an email.",
    )
    return parser.parse_args()


# ── Main logic ───────────────────────────────────────────────────────────────────

def main() -> None:
    """
    Orchestrates the full pipeline:
      1. Fetch articles from RSS feeds
      2. Summarise them with Claude
      3. Format as HTML
      4. Send by email (or just print if --dry-run)
    """
    args = _parse_args()

    try:
        # ── Step 1: Load previously sent article URLs ────────────────────────────
        seen_links = _load_seen_links()
        logger.info("Loaded %d previously seen article links.", len(seen_links))

        # ── Step 2: Fetch news ───────────────────────────────────────────────────
        print("Fetching news...")
        all_articles = fetch_news()
        print(f"  -> {len(all_articles)} article(s) found in feeds.")

        # Filter out articles already covered in a previous digest
        articles = [a for a in all_articles if a.get("link") not in seen_links]
        print(f"  -> {len(articles)} article(s) are new (not previously sent).")
        if len(articles) < len(all_articles):
            logger.info(
                "Filtered out %d already-sent article(s).",
                len(all_articles) - len(articles),
            )

        # ── Step 3: Summarise — always calls Claude, always returns something useful ──
        print("Summarizing with Claude...")
        digest = summarize_news(articles)

        # ── Step 3: Print digest to console ────────────────────────────────────
        print("\n" + "=" * 60)
        print(digest)
        print("=" * 60 + "\n")

        # ── Step 4: Build email subject and HTML body ───────────────────────────
        # Format today's date as "March 15, 2026"
        today = datetime.date.today()
        date_str = today.strftime("%B %d, %Y")
        subject = f"AI News Digest - {date_str}"

        # Convert the plain-text digest into a styled HTML email
        html_body = format_html(digest, date_str)

        # ── Step 5: Send (or skip if --dry-run) ────────────────────────────────
        if args.dry_run:
            print("[Dry-run mode] Skipping email send.")
            print(f"Would have sent: \"{subject}\"")
        else:
            success = send_email(subject, digest, html_body)
            if success:
                print("Email sent!")
                # ── Mark these articles as seen so they won't repeat ─────────────
                today_str = today.isoformat()
                for article in articles:
                    url = article.get("link")
                    if url:
                        seen_links[url] = today_str
                _save_seen_links(seen_links, dry_run=False)
            else:
                print("Email failed. Check logs above for details.")
                # Exit with a non-zero code so GitHub Actions marks the run as failed
                sys.exit(1)

    except Exception as exc:
        # Catch any unexpected error so the script always exits cleanly.
        # The full traceback is logged; a short message is printed for the user.
        logger.exception("Unexpected error in news_digest.py: %s", exc)
        print(f"\nUnexpected error: {exc}")
        print("Check the log output above for the full traceback.")
        sys.exit(1)


# ── Entry point ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
