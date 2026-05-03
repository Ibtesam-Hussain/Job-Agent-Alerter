"""
Twilio WhatsApp sender helper for job alerts.
"""

import os
from twilio.rest import Client


def send_whatsapp_message(body: str) -> bool:
    """
    Send a WhatsApp message using Twilio.

    Args:
        body: Message text to send

    Returns:
        bool: True if the message was sent, False otherwise
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_WHATSAPP_FROM")
    to_number = os.getenv("USER_WHATSAPP_NUMBER")

    if not all([account_sid, auth_token, from_number, to_number]):
        print("[WHATSAPP] Missing Twilio configuration. Please set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, and USER_WHATSAPP_NUMBER.")
        return False

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number
        )
        print(f"[WHATSAPP] Sent message SID: {message.sid}")
        return True
    except Exception as e:
        print(f"[WHATSAPP] Error sending message: {e}")
        return False
