import json
import os

import requests


def send_message(message: str) -> requests.Response:
    """
    Send a message to a Discord channel via a webhook.

    Args:
        message: Message to send.
        webhook_url: Discord webhook URL.
    """
    headers = {"Content-Type": "application/json"}
    content = {"content": message}
    response = requests.post(
        url=os.environ.get("DISCORD_WEBHOOK_URL"),
        data=json.dumps(content),
        headers=headers
    )
    return response


def send_error_message(error_message: str, traceback_message: str) -> requests.Response:
    total_error_message = f"error:{error_message}\n{traceback_message}"
    if len(total_error_message) > 1500:
        total_error_message = total_error_message[:1500]
    response = send_message(message=total_error_message)
    return response

