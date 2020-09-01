"""
* Needed to enable gmails "less secure apps" to allow the email portion to work
"""

import smtplib
import ssl
from email.mime.text import MIMEText
import os
import secrets
import requests
import json

USERS = [
    "Newsfilter",
    "fla",
    "cctranscripts"
]

def scrape(users_of_interest, tickers_of_interest):

    scraped_messages = []
    url_str = "https://api.stocktwits.com/api/2/streams/user/{}.json"

    for user in users_of_interest:
        url = url_str.format(user)
        response = requests.request("GET", url)

        parsed = json.loads(response.text)
        messages = parsed["messages"]

        for message in messages:
            message_body = message["body"]
            for ticker in tickers_of_interest:
                search_key = "".join(("$", ticker))
                if search_key in message_body:
                    scraped_messages.append(message_body)


    return scraped_messages


def format_email_message(email_content):
    return "\n---\n".join(email_content)


def send_email(email_content):
    msg = MIMEText(email_content)

    msg['Subject'] = "STOCKTWITS ALERT"
    msg['From'] = msg['To'] = secrets.USER

    context=ssl.create_default_context()

    with smtplib.SMTP("smtp.gmail.com", port=587) as smtp:
        smtp.starttls(context=context)
        smtp.login(secrets.USER, secrets.PASS)
        smtp.send_message(msg)


email_raw = scrape(USERS, secrets.WATCHLIST)
if len(email_raw):
    email_formatted = format_email_message(email_raw)
    send_email(email_formatted)
