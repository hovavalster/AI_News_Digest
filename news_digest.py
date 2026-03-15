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
import logging
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
        # ── Step 1: Fetch news ───────────────────────────────────────────────────
        print("Fetching news...")
        articles = fetch_news()
        print(f"  -> {len(articles)} article(s) found.")

        # ── Step 2: Summarise — always calls Claude, always returns something useful ──
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
