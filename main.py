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
from datetime import datetime
import pickle
import re
import pandas as pd
import pathlib

PATH = pathlib.Path(__file__).parent.absolute()

USERS = [
    "Newsfilter",
    "fla",
    "cctranscripts"
]

EMAIL_LIST = ["MARA",
            "NAK",
            "FNKO",
            "STAF",
            "EMAN",
            "BNED",
            "TTOO",
            "IDEX",
            "LAC",
            "OXLC",
            "RNET",
            "APHA",
            "IEX",
            "AYRO",
            "GEVO",
            "LTHM",
            "SOLO",
            "BLIN",
            "FAMI",
            "GRIL",
            "TGC"
              ]


MONTHS = {1 : ["January", "Jan"],
          2 : ["February", "Feb"],
          3 : ["March"],
          4 : ["April"],
          5 : ["May"],
          6 : ["June"],
          7 : ["July"],
          8 : ["August", "Aug"],
          9 : ["September", "Sep"],
          10: ["October", "Oct"],
          11: ["November", "Nov"],
          12: ["December", "Dec"]}

def find_catalysts(filename, headlines, search_terms:list, after_day=None):

    headlines_filtered = headlines.loc[(headlines["message"].str.contains(search_terms[0])) | (headlines["message"].str.contains(search_terms[1]))]

    with open(filename, "w+") as f:
        if after_day:
            for _, row in headlines_filtered.iterrows():
                row_split = row["message"].split(" ")
                messages = []
                for i, r in enumerate(row_split):
                    if r in search_terms:
                        possible_num = row_split[i+1].replace(",", "").replace(".","")
                        try:
                            num = int(possible_num)
                            if num > after_day and num != 2021:
                                rows = row["message"] = row["message"].replace("\n", " ")
                                if len(row["message"]) >= 200:
                                    rows = [rows[:200] + "\n\t|", rows[200:]]
                                else:
                                    rows = [rows]

                                if rows not in messages:
                                    rows_as_str = " ".join(rows)
                                    s = row["tickers"] + "\t|" + rows_as_str
                                    f.write(s)
                                    f.write("\n----------------------------------------------------------------------------------------------------------------\n")
                                    messages.append(rows)
                        except:
                            pass


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
                search_key = "".join(("$", ticker, " "))
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


def save_list_as_pickle(lst,fname='todays_entries.pkl'):
    with open(os.path.join(PATH, fname), 'wb+') as f:
        pickle.dump(lst, f)


def load_list_from_pickle(fname='todays_entries.pkl'):
    with open(os.path.join(PATH, fname), 'rb') as f:
        return pickle.load(f)


today = datetime.now()
if today.time().hour == 6 and today.time().minute <=10:
    todays_entries = load_list_from_pickle()

    info_dict = {}
    info_dict["tickers"] = []
    info_dict["message"] = []

    for entry in todays_entries:

        tickers = re.findall(r'[$][A-Za-z]+', entry)

        for ticker in tickers:
            info_dict["tickers"].append(ticker)
            info_dict["message"].append(entry)

    headlines = pd.DataFrame.from_dict(info_dict)

    # To filter out the bullshit
    headlines = headlines.loc[~headlines["message"].str.contains("Why")]
    headlines = headlines.loc[~headlines["message"].str.contains("Stocks Moving")]
    headlines = headlines.loc[~headlines["message"].str.contains("gainers")]
    headlines = headlines.loc[~headlines["message"].str.contains("Gainers")]
    headlines = headlines.loc[~headlines["message"].str.contains("movers")]
    headlines = headlines.loc[~headlines["message"].str.contains("Movers")]
    headlines = headlines.loc[~headlines["message"].str.contains("Trading Higher")]
    headlines = headlines.loc[~headlines["message"].str.contains("Market Update")]

    headlines.to_csv(os.path.join(PATH, "records", str(today).split(" ")[0]+".csv"))

    todays_entries = []
    save_list_as_pickle(todays_entries)

    # The catalysts document
    try:
        filename = os.path.join(PATH, "catalysts", str(today).split(" ")[0]+".txt")
        if not os.path.exists(filename):
            open(filename, 'w+').close()

        with open(filename, "a+") as f:
            find_catalysts(filename,
                                headlines,
                                search_terms=MONTHS[today.month],
                                after_day=today.day)
    except:
        pass





todays_entries = load_list_from_pickle()
tickers_of_interest = set(secrets.WATCHLIST + EMAIL_LIST)
email_raw = scrape(USERS, tickers_of_interest)
email_raw_filtered = [email for email in email_raw if email not in todays_entries]

if len(email_raw_filtered):
    todays_entries = email_raw_filtered + todays_entries
    save_list_as_pickle(todays_entries)

    # Only send an email if it contains one of the special tickers we're watching
    email_messages = []
    for ticker in EMAIL_LIST:
        for entry in email_raw_filtered:
            search_key = "".join(("$", ticker, " "))
            if search_key in entry:
                email_messages.append(entry)

    if len(email_messages) > 0:
        email_formatted = format_email_message(email_messages)
        send_email(email_formatted)


print("SUCCESS")
