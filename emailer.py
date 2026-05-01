"""
emailer.py — Send the AI News Digest via Gmail SMTP.

Environment variables required:
    EMAIL_SENDER      — Gmail address used to send (e.g. yourname@gmail.com)
    EMAIL_PASSWORD    — Gmail App Password (16-char, spaces optional)
    EMAIL_RECIPIENT   — Destination address
"""

import os
import re
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

# ── Section header colours ─────────────────────────────────────────────────────
SECTION_COLORS: dict[str, str] = {
    # AI digest sections
    "claude":           "#2B6CB0",
    "anthropic":        "#2B6CB0",
    "gemini":           "#1A73E8",
    "google":           "#1A73E8",
    "notebooklm":       "#34A853",
    "notebook lm":      "#34A853",
    "ai agents":        "#D97706",
    "what people":      "#7C3AED",
    "prompt":           "#0D9488",
    "tool spotlight":   "#DC2626",
    "podcast":          "#7C3AED",
    "one number":       "#1A202C",
    "key takeaway":     "#2B6CB0",
    "best of the week": "#D97706",
    # Behavioral econ digest sections
    "behavioral economics": "#6366F1",
    "behavioral game":      "#8B5CF6",
    "experiments":          "#0891B2",
    "applied behavioral":   "#059669",
    "in the wild":          "#D97706",
    "policy watch":         "#DC2626",
    "field vs":             "#7C3AED",
    "paper of the week":    "#2B6CB0",
    "classic paper":        "#4A5568",
    "one idea":             "#0D9488",
}

_DEFAULT_HEADER_COLOR = "#4A5568"  # slate-grey for unrecognised sections

# ── Difficulty badge colours [bg, fg] ──────────────────────────────────────────
_BADGE_COLORS: dict[str, tuple[str, str]] = {
    "[Beginner]":     ("#D1FAE5", "#065F46"),
    "[Intermediate]": ("#FEF3C7", "#92400E"),
    "[Deep Dive]":    ("#EDE9FE", "#5B21B6"),
}


# ── HTML formatter ─────────────────────────────────────────────────────────────

def _process_inline(raw: str) -> str:
    """
    Escape HTML, linkify URLs (showing domain name), bold **text**, add badge pills.

    Order matters: escape first so we don't double-escape URL href values,
    then apply bold and badges on the escaped text.
    """
    # 1. Split around bare URLs, escape text segments, linkify URL segments
    url_re = re.compile(r'(https?://[^\s<>"\')\]]+)')
    segments = url_re.split(raw)
    parts: list[str] = []
    for i, seg in enumerate(segments):
        if i % 2 == 0:
            parts.append(_escape(seg))
        else:
            safe_url = _escape(seg)
            try:
                domain = urlparse(seg).netloc.replace("www.", "") or seg[:40]
            except Exception:
                domain = seg[:40]
            parts.append(
                f'<a href="{safe_url}" style="color:#2B6CB0;text-decoration:none;'
                f'font-weight:500;" target="_blank">{_escape(domain)} ↗</a>'
            )
    text = "".join(parts)

    # 2. **bold** → <strong>
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

    # 3. [Badge] → colored pill
    for badge, (bg, fg) in _BADGE_COLORS.items():
        text = text.replace(
            badge,
            f'<span style="background:{bg};color:{fg};font-size:11px;font-weight:600;'
            f'padding:2px 8px;border-radius:10px;margin-right:5px;">'
            f'{badge[1:-1]}</span>',
        )

    return text


def format_html(digest_text: str, date_str: str) -> str:
    """
    Convert the plain-text Claude digest into a styled HTML email.

    Line types handled
    ------------------
    ---                        → <hr> divider
    📊 **One Number**          → emoji section heading (h2 with emoji)
    **Claude & Anthropic**     → plain section heading (h2 with colour)
    **Today's Key Takeaway:**  → bold label + inline text paragraph
    Claude Code:               → legacy colon-suffix heading
    • bullet text (Source: URL)→ <li> with clickable link + badge pills
    blank                      → vertical spacer
    everything else            → <p> with inline processing
    """
    lines = digest_text.splitlines()
    body_html_parts: list[str] = []
    in_list = False
    next_is_one_number = False  # render next paragraph as callout box

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            body_html_parts.append("</ul>")
            in_list = False

    def h2(text: str, color: str, prefix: str = "") -> str:
        pre = f"{_escape(prefix)}&nbsp;" if prefix else ""
        return (
            f'<h2 style="margin:24px 0 8px 0;font-size:16px;color:{color};'
            f'border-bottom:2px solid {color};padding-bottom:6px;">'
            f"{pre}{_escape(text)}</h2>"
        )

    for raw_line in lines:
        line = raw_line.strip()

        # ── Blank line ───────────────────────────────────────────────────────
        if not line:
            close_list()
            body_html_parts.append('<div style="height:8px;"></div>')
            continue

        # ── Horizontal rule ──────────────────────────────────────────────────
        if line == "---":
            close_list()
            body_html_parts.append(
                '<hr style="border:none;border-top:1px solid #E2E8F0;margin:20px 0;">'
            )
            continue

        # ── Bullet point ─────────────────────────────────────────────────────
        if line.startswith("•"):
            item_text = line.lstrip("•").strip()
            if not in_list:
                body_html_parts.append(
                    '<ul style="margin:4px 0 8px 0;padding-left:18px;">'
                )
                in_list = True
            body_html_parts.append(
                f'<li style="margin-bottom:8px;line-height:1.6;">'
                f"{_process_inline(item_text)}</li>"
            )
            continue

        # Everything below closes any open list
        close_list()

        # ── Emoji heading: "📊 **One Number**" ──────────────────────────────
        # First char is non-ASCII (emoji) and line contains **heading**
        if ord(line[0]) > 127:
            m = re.match(r"^(.{1,4})\s+\*\*(.+?)\*\*(.*)$", line)
            if m:
                emoji, heading, rest = m.group(1), m.group(2), m.group(3).strip()
                color = _heading_color(heading)
                suffix = (
                    f' <span style="color:#718096;font-size:13px;font-weight:normal;">'
                    f"{_escape(rest)}</span>"
                    if rest
                    else ""
                )
                body_html_parts.append(
                    f'<h2 style="margin:24px 0 8px 0;font-size:16px;color:{color};'
                    f'border-bottom:2px solid {color};padding-bottom:6px;">'
                    f"{_escape(emoji)}&nbsp;{_escape(heading)}{suffix}</h2>"
                )
                if "one number" in heading.lower():
                    next_is_one_number = True
                continue
            # Falls through if no ** found — treated as plain text below

        # ── Section heading: **Claude & Anthropic** (whole line is **…**) ───
        if line.startswith("**") and line.endswith("**") and len(line) > 4:
            heading_text = line[2:-2].strip()
            body_html_parts.append(h2(heading_text, _heading_color(heading_text)))
            continue

        # ── Bold-label line: "**Today's Key Takeaway:** text" ────────────────
        if line.startswith("**"):
            m = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", line)
            if m:
                label, rest = m.group(1), m.group(2)
                body_html_parts.append(
                    f'<p style="margin:12px 0;line-height:1.6;">'
                    f"<strong>{_escape(label)}:</strong> {_process_inline(rest)}</p>"
                )
                continue

        # ── Legacy colon-suffix heading: "Claude Code:" ──────────────────────
        if line.endswith(":") and not line.startswith("•"):
            heading_text = line.rstrip(":")
            body_html_parts.append(h2(heading_text, _heading_color(heading_text)))
            continue

        # ── Plain text ───────────────────────────────────────────────────────
        if next_is_one_number:
            next_is_one_number = False
            body_html_parts.append(
                f'<div style="background:#EFF6FF;border-left:4px solid #2B6CB0;'
                f'padding:14px 18px;margin:8px 0 20px 0;border-radius:0 6px 6px 0;">'
                f'<p style="margin:0;font-size:15px;line-height:1.6;color:#1E3A5F;">'
                f"{_process_inline(line)}</p></div>"
            )
        else:
            body_html_parts.append(
                f'<p style="margin:0 0 8px 0;line-height:1.6;">{_process_inline(line)}</p>'
            )

    close_list()

    body_html = "\n".join(body_html_parts)

    preheader = _escape(_extract_one_number(digest_text))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI News Digest — {_escape(date_str)}</title>
  <style>
    @media only screen and (max-width:640px) {{
      .email-wrap  {{ width:100% !important; }}
      .email-body  {{ padding:20px 16px 12px 16px !important; }}
      .email-footer {{ padding:12px 16px 20px 16px !important; }}
    }}
  </style>
</head>
<body style="margin:0; padding:0; background-color:#F7F8FA;">
  <!-- Preheader: hidden text shown as inbox preview snippet -->
  <div style="display:none;max-height:0;overflow:hidden;font-size:1px;color:#F7F8FA;">{preheader}</div>
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background-color:#F7F8FA; padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="620" cellpadding="0" cellspacing="0" class="email-wrap"
               style="background-color:#FFFFFF; border-radius:8px;
                      box-shadow:0 2px 8px rgba(0,0,0,0.08);
                      font-family:Arial, Helvetica, sans-serif;
                      font-size:14px; color:#1A202C;">
          <!-- Header banner -->
          <tr>
            <td style="background-color:#2B6CB0; border-radius:8px 8px 0 0;
                       padding:24px 32px;">
              <h1 style="margin:0; font-size:22px; color:#FFFFFF;
                         letter-spacing:0.5px;">AI News Digest</h1>
              <p style="margin:6px 0 0 0; font-size:13px;
                        color:#BEE3F8;">{_escape(date_str)}</p>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td class="email-body" style="padding:28px 32px 16px 32px;">
              {body_html}
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td class="email-footer" style="padding:16px 32px 28px 32px;
                       border-top:1px solid #E2E8F0;">
              <p style="margin:0; font-size:12px; color:#718096;
                        text-align:center;">
                This digest was generated automatically by AI News Digest
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return html


# ── SMTP sender ────────────────────────────────────────────────────────────────

def send_email(subject: str, text_body: str, html_body: str) -> bool:
    """
    Send an email via Gmail SMTP (STARTTLS, port 587).

    Reads EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT from environment.
    Optionally also sends to EMAIL_RECIPIENT_2 if set.
    Returns True on success, False on any failure (never raises).
    """
    sender    = os.environ.get("EMAIL_SENDER", "").strip()
    password  = os.environ.get("EMAIL_PASSWORD", "").strip()
    recipient = os.environ.get("EMAIL_RECIPIENT", "").strip()

    if not sender or not password or not recipient:
        logger.error(
            "send_email: missing env vars — need EMAIL_SENDER, "
            "EMAIL_PASSWORD, EMAIL_RECIPIENT"
        )
        return False

    # Collect all recipients
    recipients = [recipient]
    extra = os.environ.get("EMAIL_RECIPIENT_2", "").strip()
    if extra:
        recipients.append(extra)

    # Build MIMEMultipart("alternative") — plain-text first, HTML second
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = ", ".join(recipients)

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html",  "utf-8"))

    try:
        with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
        logger.info("Email sent successfully to %s (subject: %s)", ", ".join(recipients), subject)
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error(
            "send_email: authentication failed — check EMAIL_SENDER and "
            "EMAIL_PASSWORD (use a Gmail App Password, not your account password)"
        )
    except smtplib.SMTPException as exc:
        logger.error("send_email: SMTP error — %s", exc)
    except OSError as exc:
        logger.error("send_email: network error — %s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.error("send_email: unexpected error — %s", exc)

    return False


# ── Helpers ────────────────────────────────────────────────────────────────────

def _heading_color(text: str) -> str:
    """Return an appropriate colour for a section heading."""
    lower = text.lower()
    for keyword, color in SECTION_COLORS.items():
        if keyword in lower:
            return color
    return _DEFAULT_HEADER_COLOR


def _extract_one_number(digest_text: str) -> str:
    """Return the One Number paragraph for use as inbox preheader text."""
    lines = digest_text.splitlines()
    found_heading = False
    for line in lines:
        stripped = line.strip()
        if found_heading:
            if stripped and stripped != "---":
                # Strip markdown bold markers for plain preview text
                return re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
        elif "one number" in stripped.lower() and "**" in stripped:
            found_heading = True
    return ""


def _escape(text: str) -> str:
    """Minimal HTML escaping."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ── Dry-run test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import datetime

    SAMPLE_DIGEST = """\
---

📊 **One Number**
700 million: the number of people Sam Altman says he wants AI to eventually serve as a "brilliant friend."

---

**Claude & Anthropic**
• [Beginner] — Anthropic expands Claude's tool-use and memory across sessions — infrastructure for persistent AI collaborators, not just chatbots. (Source: https://techcrunch.com/2026/03/18/anthropic-tool-use/)
• [Deep Dive] — New research paper from Anthropic on constitutional AI scaling. Interesting take on how values are baked in at training time. (Source: https://www.anthropic.com/research/constitutional-ai-2)

**Gemini & Google AI**
• [Beginner] — NotebookLM gaining momentum with educators turning dense PDFs into conversational audio summaries. (Source: https://venturebeat.com/ai/notebooklm-educators/)
• [Intermediate] — Gemini 2.0 Flash now available via API with significantly lower latency than 1.5 Pro. (Source: https://ai.google.dev/blog/gemini-flash-update)

**AI Agents & Tools**
• [Intermediate] — The agent race is heating up. Anthropic, OpenAI, and Google all shipping agentic frameworks within the same week. (Source: https://www.theverge.com/ai/agents-race-2026)

**AI News**
• [Beginner] — A photo of a war zone went viral; journalists couldn't confirm if it was real or AI-generated. Media literacy is lagging badly.

**What People Are Saying**
• [Beginner] — Reddit thread on brain cells playing Doom is oscillating between "incredible neuroscience" and "this is how every sci-fi horror movie starts." (Source: https://reddit.com/r/artificial/comments/doom_neurons)

---

💡 **Prompt of the Day**
Paste any news article and ask: "(1) summarize in 3 bullets, (2) give me background context I might be missing, (3) flag any one-sided claims I should verify." Works in Claude or ChatGPT.

---

🛠️ **Tool Spotlight: Windsurf** (AI Code Editor)
Codeium's AI-native IDE has a mode called Cascade that plans and executes multi-step coding tasks across your entire project. It's like having a junior developer who reads all your files before touching anything. Try this: open a project and ask it to "add dark mode support" — it figures out which files to change automatically.
URL: https://codeium.com/windsurf

---

🎙️ **Podcast Episode of the Day**
The Tim Ferriss Show — Naval Ravikant: The Angel Philosopher (#97) — Naval Ravikant — ~2h 5min
One of the most-shared podcast episodes ever recorded. Naval breaks down his framework for wealth, happiness, and leverage in a way that makes you rethink how you approach work. Still completely relevant years later.
Search on Spotify: "Tim Ferriss Naval Ravikant Angel Philosopher 97"

---

**Today's Key Takeaway:** AI is now advanced enough that it's genuinely hard to tell what's real in a conflict zone — and that's not a future problem, it's happening today.

---
"""

    today = datetime.date.today().strftime("%B %d, %Y")
    html_output = format_html(SAMPLE_DIGEST, today)

    # Write to a local file for easy browser preview
    out_path = "emailer_preview.html"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html_output)

    print(f"HTML preview written to: {out_path}")
    print("-" * 60)
    print(html_output[:800], "...")
