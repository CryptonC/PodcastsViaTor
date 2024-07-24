#!/usr/bin/python3
# Based loosely off of RSSNSA https://notabug.org/SuspiciousActions/RSSNSA

# Dependencies:
# * Tor
# * torsocks
# * curl
# * python3

from FetchFiles import getPage, parseHeaders
import time
from datetime import datetime

def getTime():
    return datetime.now().strftime('%H:%M')


# Get the config
config = ConfigParser()
config.read("data/config.cfg")

# Keep trying to get the tor check page until we succeed 
print(f"[{getTime()}] Waiting on Tor...")
torCheckReturn = getPage("https://check.torproject.org/")
while "Congratulations. This browser is configured to use Tor." not in torCheckReturn:
    time.sleep(2)
    torCheckReturn = getPage("https://check.torproject.org/")
print(f"[{getTime()}] Tor check succeeded!")

# Get the target feed links
feedList = open("data/feeds.txt", "r")

# For each feed
for feedLink in feedList:
    # Get the feed
    targetFeed = getPage(feedLink)

    # Create the new feed, starting with the headers
    headers = parseHeaders(targetFeed)
    newFeed = f"""<rss version=\"2.0\">
    <channel>
        <title>{headers["title"]}</title>
        <link>https://google.com</link>
        <description>{headers["description"]}</description>
    </channel>"""
    print(newFeed)

    # Get the feed image if we don't have it

    # Get a list of all episodes

    # For each episode

        # Check if we have the episode downloaded already. If we don't, download it

        # Add the episode information

    # Save the new feed