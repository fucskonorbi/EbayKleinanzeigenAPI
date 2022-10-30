import os
import socket

import uvicorn
from bs4 import BeautifulSoup
import requests
from time import sleep
from fastapi import FastAPI
import datetime
import argparse

BASE_URL = "https://www.ebay-kleinanzeigen.de/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    'Connection': 'keep-alive', 'Accept-Encoding': 'gzip, deflate', 'Accept': '*/*'}


def find_items_on_ebay_kleinanzeigen_after_timestamp(keyword, timestamp, item_ids_to_skip):
    url = BASE_URL + "s-" + keyword + "/k0"
    response = requests.get(url, headers=HEADERS, timeout=5)
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")
    items = soup.find_all("article", {"class": "aditem"})
    items_to_return = []
    print(items)
    for item in items:
        try:
            # time of item is in a div tag with aditem-main--top--right class. Remove the i tag and get the text
            time = item.find("div", {"class": "aditem-main--top--right"})
            # if the i tag does not have an icon-calendar-open class, then move to the next item
            if time.find("i", {"class": "icon-calendar-open"}) is None:
                continue

            time.find("i").decompose()
            time = time.text
            # strip of leading and trailing non-alphanumeric characters
            time = time.strip()
            # convert the time to a datetime object and compare it with the timestamp
            # the time is in the format of "Heute, HH:MM" or "Gestern, HH:MM" or "DD.MM.YYYY"
            if "Heute" in time:
                time = time.replace("Heute, ", "")
                time = datetime.datetime.strptime(time, "%H:%M")
                time = datetime.datetime.combine(datetime.date.today(), time.time())
            elif "Gestern" in time:
                time = time.replace("Gestern, ", "")
                time = datetime.datetime.strptime(time, "%H:%M")
                time = datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=1), time.time())
            else:
                time = datetime.datetime.strptime(time, "%d.%m.%Y")

            # if time and timestamp are on the same day, compare the time, otherwise compare the date
            # only add the link to the list if the time is after the timestamp
            item_id = item["data-adid"]
            title = item.find("a", {"class": "ellipsis"})
            if title is not None:
                title = title.text.strip()
            link = item.find("a", {"class": "ellipsis"})["href"]
            price = item.find("p", {"class": "aditem-main--middle--price-shipping--price"})
            if price is not None:
                price = price.text.strip()
            address = item.find("div", {"class": "aditem-main--top--left"})
            if address is not None:
                # get the text
                address = address.text.strip()
            print(time, title)
            if time.date() == timestamp.date():
                if time.time() > timestamp.time():
                    items_to_return.append({"timestamp": time, "link": link, "item_id": item_id, "title": title, "price": price, "address": address})
                elif time.time() == timestamp.time():
                    if item_id not in item_ids_to_skip:
                        items_to_return.append({"timestamp": time, "link": link, "item_id": item_id, "title": title, "price": price, "address": address})
            elif time.date() > timestamp.date():
                items_to_return.append({"timestamp": time, "link": link, "item_id": item_id, "title": title, "price": price, "address": address})
        except Exception as e:
            print("Jaj", e)

    return items_to_return


# simulate the mobile app user agent
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, required=True, default="api", help="Can be 'simulate' or 'api'")
    args = parser.parse_args()
    if args.mode == "simulate":
        found_items = []
        while True:
            if len(found_items) == 0:
                # get items from the last 5 minutes
                timestamp = datetime.datetime.now() - datetime.timedelta(minutes=5)
                found_items = find_items_on_ebay_kleinanzeigen_after_timestamp("macbook", timestamp, [])
                # reverse the list so that the newest items are at the beginning
                found_items.reverse()
            else:
                # get the timestamp of the last item
                timestamp = found_items[-1]["timestamp"]
                # get the ids of the items which have the same timestamp
                item_ids_to_skip = [item["item_id"] for item in found_items if item["timestamp"] == timestamp]
                # get items
                new_items = find_items_on_ebay_kleinanzeigen_after_timestamp("macbook", timestamp, item_ids_to_skip)
                # reverse the list so that the newest items are at the beginning
                new_items.reverse()
                print("New items:", new_items)
                # add the new items to the list
                found_items.extend(new_items)
            # print time and ids of the items
            print("Time: ", datetime.datetime.now(), "Found items: ", [item for item in found_items])
            sleep(180)
    elif args.mode == "api":
        # create an API where the user can search for a keyword and get the results
        # create a FastAPI instance
        app = FastAPI()
        # define the api endpoint, where the user can search for a keyword (needs to provide a keyword, timestamp and
        # item_ids_to_skip)
        print("Starting API")
        @app.get("/search")
        def search(keyword: str, timestamp: str, item_ids_to_skip: str):
            timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
            item_ids_to_skip = item_ids_to_skip.split(",")
            return find_items_on_ebay_kleinanzeigen_after_timestamp(keyword, timestamp, item_ids_to_skip)

        uvicorn.run("main:app", host="0.0.0.0", port=os.getenv("PORT", default=50000), log_level="info")

    else:
        print("Invalid mode")
