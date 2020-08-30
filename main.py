import requests
import json


def scrape(users_of_interest):

    url_str = "https://api.stocktwits.com/api/2/streams/user/{}.json"

    for user in users_of_interest:
        url = url_str.format(user)
        response = requests.request("GET", url)

        parsed = json.loads(response.text)
        messages = parsed["messages"]

        for message in messages:
            print(json.dumps(message["body"], indent=4, sort_keys=True))


users_of_interest = [
    "newsfilterio",
    "fla"
]

scrape(users_of_interest)
