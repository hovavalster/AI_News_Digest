"""
emailer.py — Send the AI News Digest via Gmail SMTP.

Environment variables required:
    EMAIL_SENDER      — Gmail address used to send (e.g. yourname@gmail.com)
    EMAIL_PASSWORD    — Gmail App Password (16-char, spaces optional)
    EMAIL_RECIPIENT   — Destination address
"""

import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

# ── Section header colours ─────────────────────────────────────────────────────
SECTION_COLORS: dict[str, str] = {
    "claude":      "#2B6CB0",
    "anthropic":   "#2B6CB0",
    "gemini":      "#1A73E8",
    "google":      "#1A73E8",
    "notebooklm":  "#34A853",
    "notebook lm": "#34A853",
}

_DEFAULT_HEADER_COLOR = "#4A5568"  # slate-grey for unrecognised sections


# ── HTML formatter ─────────────────────────────────────────────────────────────

def format_html(digest_text: str, date_str: str) -> str:
    """
    Convert the plain-text digest (bullet points with •) into a styled HTML email.

    Rules
    -----
    - Lines that end with a colon  → coloured section heading
    - Lines that start with •      → <li> items (wrapped in <ul>)
    - Blank lines                  → paragraph break
    - Everything else              → plain paragraph
    """
    lines = digest_text.splitlines()

    body_html_parts: list[str] = []
    in_list = False  # tracks whether we are inside an open <ul>

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            body_html_parts.append("</ul>")
            in_list = False

    for raw_line in lines:
        line = raw_line.strip()

        # Blank line → paragraph spacer
        if not line:
            close_list()
            body_html_parts.append('<p style="margin:0 0 8px 0;">&nbsp;</p>')
            continue

        # Section heading: two formats are supported:
        #   1. Claude markdown bold:  **Claude Code**
        #   2. Plain colon suffix:    Claude Code:
        heading_text: str | None = None
        if line.startswith("**") and line.endswith("**") and len(line) > 4:
            # Strip the surrounding ** markers
            heading_text = line[2:-2].strip()
        elif line.endswith(":") and not line.startswith("•"):
            heading_text = line.rstrip(":")

        if heading_text is not None:
            close_list()
            color = _heading_color(heading_text)
            body_html_parts.append(
                f'<h2 style="margin:24px 0 8px 0; font-size:17px; '
                f'color:{color}; border-bottom:2px solid {color}; '
                f'padding-bottom:4px;">{_escape(heading_text)}</h2>'
            )
            continue

        # Bullet point
        if line.startswith("•"):
            item_text = line.lstrip("•").strip()
            if not in_list:
                body_html_parts.append(
                    '<ul style="margin:4px 0 4px 0; padding-left:20px;">'
                )
                in_list = True
            body_html_parts.append(
                f'<li style="margin-bottom:6px; line-height:1.5;">{_escape(item_text)}</li>'
            )
            continue

        # Plain text
        close_list()
        body_html_parts.append(
            f'<p style="margin:0 0 8px 0; line-height:1.6;">{_escape(line)}</p>'
        )

    close_list()

    body_html = "\n".join(body_html_parts)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI News Digest — {_escape(date_str)}</title>
</head>
<body style="margin:0; padding:0; background-color:#F7F8FA;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background-color:#F7F8FA; padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="620" cellpadding="0" cellspacing="0"
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
            <td style="padding:28px 32px 16px 32px;">
              {body_html}
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding:16px 32px 28px 32px;
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
Claude (Anthropic):
• Claude 3.7 Sonnet released with extended thinking mode and 200K context
• Anthropic publishes new Constitutional AI research paper
• Claude API adds batch processing endpoint for high-volume use cases

Gemini (Google):
• Gemini 2.0 Flash achieves top scores on MMLU and HumanEval benchmarks
• Google integrates Gemini natively into Google Docs and Sheets
• New Gemini API feature: grounding with Google Search

NotebookLM:
• NotebookLM now supports audio overviews in 10 additional languages
• New "Briefing Doc" export format added to NotebookLM
• Google expands NotebookLM enterprise tier with SSO support
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
