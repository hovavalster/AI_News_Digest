"""
becon_digest.py — Main entry point for the Behavioral Economics & Game Theory digest.
Runs daily at 11:00 AM Israel time (09:00 UTC) via GitHub Actions.

Usage:
  python becon_digest.py            # full run — fetch, summarize, send email
  python becon_digest.py --dry-run  # print digest, skip sending
"""

import argparse
import datetime
import json
import logging
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from becon_fetcher    import fetch_becon_news
from becon_summarizer import summarize_becon
from emailer          import send_email, format_html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("becon_digest.main")

_SEEN_LINKS_FILE    = os.path.join(os.path.dirname(__file__), "data", "becon_seen_links.json")
_SEEN_LINKS_MAX_AGE = 90  # behavioral papers stay relevant longer — keep 90 days


def _load_seen() -> dict[str, str]:
    try:
        with open(_SEEN_LINKS_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        result = {}
        for item in raw:
            if isinstance(item, str):
                result[item] = "2000-01-01"
            elif isinstance(item, dict):
                result[item["url"]] = item.get("date", "2000-01-01")
        return result
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_seen(seen: dict[str, str]) -> None:
    cutoff = (
        datetime.date.today() - datetime.timedelta(days=_SEEN_LINKS_MAX_AGE)
    ).isoformat()
    pruned = [
        {"url": url, "date": date}
        for url, date in seen.items()
        if date >= cutoff
    ]
    os.makedirs(os.path.dirname(_SEEN_LINKS_FILE), exist_ok=True)
    with open(_SEEN_LINKS_FILE, "w", encoding="utf-8") as f:
        json.dump(pruned, f, indent=2)
    logger.info("Saved %d seen links.", len(pruned))


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main():
    args = _parse_args()

    try:
        seen = _load_seen()
        logger.info("Loaded %d previously seen links.", len(seen))

        print("Fetching papers...")
        all_articles = fetch_becon_news()
        print(f"  -> {len(all_articles)} article(s) found.")

        articles = [a for a in all_articles if a.get("link") not in seen]
        print(f"  -> {len(articles)} are new (not previously sent).")

        print("Summarizing with Claude...")
        digest = summarize_becon(articles)

        print("\n" + "=" * 60)
        print(digest)
        print("=" * 60 + "\n")

        today     = datetime.date.today()
        date_str  = today.strftime("%B %d, %Y")
        subject   = f"Behavioral Economics Digest — {date_str}"
        html_body = format_html(digest, date_str)

        if args.dry_run:
            print("[Dry-run] Skipping send.")
        else:
            success = send_email(subject, digest, html_body)
            if success:
                print("Email sent!")
                today_str = today.isoformat()
                for a in articles:
                    url = a.get("link")
                    if url:
                        seen[url] = today_str
                _save_seen(seen)
            else:
                print("Email failed.")
                sys.exit(1)

    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
