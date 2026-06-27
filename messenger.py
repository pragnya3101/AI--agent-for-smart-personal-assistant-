import smtplib
import os
from email.utils import formataddr
from email.mime.text import MIMEText

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

import config


def resolve_contact(contact):
    contact = contact.lower().strip()
    return config.CONTACT_ALIASES.get(contact, contact)


def _looks_like_email(value):
    return "@" in value and "." in value.rsplit("@", 1)[-1]


def _disable_broken_proxy():
    for name in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "http_proxy",
        "https_proxy",
        "ALL_PROXY",
        "all_proxy",
    ):
        os.environ.pop(name, None)


def _format_whatsapp_number(number):
    number = number.strip()

    if number.startswith("whatsapp:"):
        return number

    return f"whatsapp:{number}"


def send_whatsapp(contact, message):
    contact = resolve_contact(contact)
    message = message.strip()

    if contact not in config.CONTACTS and not _looks_like_email(contact):
        return "Contact not found"

    if not config.TWILIO_SID or not config.TWILIO_AUTH_TOKEN:
        return "Twilio credentials are missing"

    if config.TWILIO_AUTH_TOKEN.startswith("AC"):
        return "Twilio auth token is wrong. Copy Auth Token, not Account SID"

    if not config.TWILIO_WHATSAPP_NUM:
        return "Twilio WhatsApp number is missing"

    if not message:
        return "Message is empty"

    number = config.CONTACTS[contact]["phone"]

    try:
        _disable_broken_proxy()
        client = Client(config.TWILIO_SID, config.TWILIO_AUTH_TOKEN)
        message_result = client.messages.create(
            from_=_format_whatsapp_number(config.TWILIO_WHATSAPP_NUM),
            body=message,
            to=_format_whatsapp_number(number),
        )
        return f"Message sent to {contact}. Status is {message_result.status}. SID {message_result.sid}"
    except TwilioRestException as e:
        print(e)

        if e.code == 20003:
            return "Twilio login failed. Check TWILIO_SID and TWILIO_AUTH_TOKEN"

        if e.code in (21606, 63007):
            return "Twilio WhatsApp number is not enabled"

        if e.code in (21211, 21614, 63015, 63016):
            return "Receiver must join your Twilio WhatsApp sandbox first"

        return f"WhatsApp failed: {e.msg}"
    except Exception as e:
        print(e)
        return "WhatsApp failed"


def send_email(contact, subject, body):
    contact = resolve_contact(contact)
    subject = subject.strip()
    body = body.strip()

    if contact not in config.CONTACTS:
        return "Contact not found"

    if not config.GMAIL_ADDRESS or not config.GMAIL_APP_PASSWORD:
        return "Gmail credentials are missing"

    if not subject or not body:
        return "Subject or message is empty"

    email = contact if _looks_like_email(contact) else config.CONTACTS[contact]["email"]

    try:
        password = config.GMAIL_APP_PASSWORD.replace(" ", "")
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = formataddr(("Will AI Assistant", config.GMAIL_ADDRESS))
        msg["To"] = email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config.GMAIL_ADDRESS, password)
            server.send_message(msg)

        return f"Email sent to {contact}"
    except smtplib.SMTPAuthenticationError:
        return "Gmail login failed. Use a Gmail App Password, not your normal password"
    except smtplib.SMTPRecipientsRefused:
        return "Email address was rejected"
    except smtplib.SMTPException as e:
        print(e)
        return f"Email failed: {e}"
    except Exception as e:
        print(e)
        return "Email failed"
