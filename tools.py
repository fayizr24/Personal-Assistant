import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from langchain.tools import tool

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an HTML-formatted email to the given recipient with the given subject and body.
    The body should be valid HTML (e.g. <h2>, <b>, <ul><li>)."""
    sender = os.environ["EMAIL_ADDRESS"]
    password = os.environ["EMAIL_APP_PASSWORD"]

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))  # <-- changed from "plain" to "html"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, to, msg.as_string())
        return f"Email sent to {to}"
    except Exception as e:
        return f"Failed to send email: {e}"