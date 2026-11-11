"""Email new contact-form messages to Pranav through the Brevo API."""
import json
import logging
import threading
import urllib.error
import urllib.request
from html import escape

from django.conf import settings

log = logging.getLogger(__name__)

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def _row(label, value):
    if not value:
        return ""
    return (f'<tr><td style="padding:8px 14px 8px 0;color:#8a7a4a;font-size:13px;'
            f'text-transform:uppercase;letter-spacing:.08em;white-space:nowrap;vertical-align:top">{label}</td>'
            f'<td style="padding:8px 0;color:#111;font-size:15px">{value}</td></tr>')


def build_payload(msg):
    name, email = escape(msg.name), escape(msg.email)
    body = escape(msg.message).replace("\n", "<br>")
    html = f"""
<div style="background:#f4f1ea;padding:28px 12px;font-family:Arial,Helvetica,sans-serif">
  <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e6dcc0">
    <div style="background:#0b0b0b;padding:22px 26px">
      <div style="color:#d4af37;font-size:12px;letter-spacing:.2em;text-transform:uppercase">New enquiry</div>
      <div style="color:#fff;font-size:22px;font-weight:bold;margin-top:6px">{name} wants to work with you</div>
    </div>
    <div style="padding:22px 26px">
      <table style="border-collapse:collapse;width:100%">
        {_row("Name", name)}
        {_row("Email", f'<a href="mailto:{email}" style="color:#a67c1b">{email}</a>')}
        {_row("Project", escape(msg.project_type))}
        {_row("Budget", escape(msg.budget))}
      </table>
      <div style="margin-top:16px;padding:16px 18px;background:#faf7ef;border-left:3px solid #d4af37;border-radius:6px;color:#222;font-size:15px;line-height:1.6">{body}</div>
      <a href="mailto:{email}?subject=Re:%20your%20project%20enquiry"
         style="display:inline-block;margin-top:20px;padding:12px 22px;background:#d4af37;color:#0b0b0b;text-decoration:none;border-radius:999px;font-weight:bold">Reply to {name}</a>
    </div>
  </div>
  <div style="text-align:center;color:#9a917a;font-size:12px;margin-top:14px">Sent from your portfolio contact form · also saved in Admin → Messages</div>
</div>"""
    subject = f"New enquiry from {msg.name}" + (f" · {msg.project_type}" if msg.project_type else "")
    return {
        "sender": {"name": settings.BREVO_SENDER_NAME, "email": settings.BREVO_SENDER_EMAIL},
        "to": [{"email": settings.CONTACT_RECEIVER_EMAIL}],
        "replyTo": {"email": msg.email, "name": msg.name},   # hitting "Reply" answers the visitor
        "subject": subject[:150],
        "htmlContent": html,
        "textContent": (f"New enquiry from {msg.name} <{msg.email}>\n"
                        f"Project: {msg.project_type or '-'}\nBudget: {msg.budget or '-'}\n\n{msg.message}"),
    }


def send_contact_email(msg):
    """Send synchronously. Returns True on success; never raises."""
    if not settings.BREVO_API_KEY:
        log.warning("BREVO_API_KEY not set — contact email skipped")
        return False
    req = urllib.request.Request(
        BREVO_URL,
        data=json.dumps(build_payload(msg)).encode("utf-8"),
        headers={"api-key": settings.BREVO_API_KEY, "content-type": "application/json", "accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return 200 <= r.status < 300
    except urllib.error.HTTPError as e:
        log.error("Brevo rejected the contact email (%s): %s", e.code, e.read()[:500])
    except Exception as e:  # network down, timeout…
        log.error("Could not reach Brevo: %s", e)
    return False


def notify_new_message(msg):
    """Email in the background so the visitor isn't kept waiting."""
    threading.Thread(target=send_contact_email, args=(msg,), daemon=True).start()
