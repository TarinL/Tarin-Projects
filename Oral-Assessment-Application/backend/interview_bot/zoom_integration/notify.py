"""
notify.py — Send interview meeting link emails via SMTP.

Requires in .env:
    SMTP_HOST       e.g. smtp.gmail.com
    SMTP_PORT       e.g. 587
    SMTP_USER       your sending address
    SMTP_PASSWORD   app password (Gmail: myaccount.google.com/apppasswords)
    EMAIL_FROM      display name + address, e.g. "Interview Bot <you@gmail.com>"
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_meeting_email(
    to: str,
    join_url: str,
    topic: str,
    scheduled_start: str,
    student_name: str,
) -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.environ["SMTP_PORT"])
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    from_addr = os.environ.get("EMAIL_FROM", user)

    subject = f"Your oral assessment interview: {topic}"

    body = f"""Hi {student_name},

Your oral assessment interview has been scheduled.

  Topic:      {topic}
  Time:       {scheduled_start}
  Join link:  {join_url}

Please join a couple of minutes early so the interviewer bot can connect.
When you are ready to begin, say "ready" and the interview will start.

Good luck!
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(host, port) as server:
        server.ehlo()
        server.starttls()
        server.login(user, password)
        server.sendmail(from_addr, to, msg.as_string())

    print(f"[notify] Email sent to {to}", flush=True)


def send_face_link_email(
    to: str,
    face_url: str,
    student_name: str,
    interview_id: int | None = None,
) -> None:
    """Email the operator the (per-run, ngrok) bot-face visualiser link.

    The remote/ECS URL embeds the run's wss tunnel, which changes every run on a
    free ngrok plan, so it can only be known once the tunnel is live."""
    host = os.environ["SMTP_HOST"]
    port = int(os.environ["SMTP_PORT"])
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    from_addr = os.environ.get("EMAIL_FROM", user)

    label = f" (interview {interview_id})" if interview_id is not None else ""
    subject = f"Bot-face visualiser link{label}"

    body = f"""The bot-face visualiser is live for this run{label}.

  Student:  {student_name}
  Open:     {face_url}

This link is unique to this run (the ngrok tunnel changes each time), so use it
for this interview only.
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(host, port) as server:
        server.ehlo()
        server.starttls()
        server.login(user, password)
        server.sendmail(from_addr, to, msg.as_string())

    print(f"[notify] Face-link email sent to {to}", flush=True)
