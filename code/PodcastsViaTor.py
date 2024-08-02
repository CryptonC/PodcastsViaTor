#!/usr/bin/python3
# Based loosely off of RSSNSA https://notabug.org/SuspiciousActions/RSSNSA

# Dependencies:
# * Tor
# * torsocks
# * curl
# * python3

from FetchFiles import getPage, parseHeaders, parseAllEpisodeInfo
import time
from datetime import datetime
from configparser import ConfigParser
import os
import http.server
import socketserver
import threading

WEB_PORT = 80

# Get the config
config = ConfigParser()
config.read("data/config.cfg")

def getTime():
    return datetime.now().strftime('%H:%M')


def makeAlphanumeric(text):
    newText = ""
    for char in text:
        if char.lower() in "abcdefghijklmnopqrstuvwxyz1234567890":
            newText += char
    return newText

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

def fetchAllFeeds():
    # Get the target feed links
    feedList = open("data/feeds.txt", "r")

    # For each feed
    for feedLink in feedList:
        feedLink = feedLink.strip()
        print(f"[{getTime()}] Getting feed: {feedLink}")
        # Get the feed
        targetFeed = getPage(feedLink)
        while targetFeed is None:
            print(f"[{getTime()}] Retrying fetching feed")
            targetFeed = getPage(feedLink)

        # Create the new feed, starting with the headers
        headers = parseHeaders(targetFeed)
        newFeedUrl = config["Main"]["hostname"] + "/" + makeAlphanumeric(headers["title"])

        newFeed = f"""<rss version=\"2.0\">
    <channel>
        <title>{headers["title"]}</title>
        <link>{newFeedUrl}</link>
        <description>{headers["description"]}</description>"""

        # Create a folder for the feed if we don't have one
        feedPath = "data/podcasts/" + makeAlphanumeric(headers["title"])
        os.makedirs(feedPath, exist_ok = True)

        # Get the feed image if we don't have it
        thumbnailName = headers["image"]["url"].split("/")[-1]
        if not os.path.exists(feedPath + "/" + thumbnailName):
            print(f"[{getTime()}] Getting podcast image")
            getPage(headers["image"]["url"], feedPath + "/" + thumbnailName)
        newFeed += f"""
        <image>
            <url>{newFeedUrl + "/" + thumbnailName}</url>
            <title>{headers["image"]["title"]}</title>
            <link>{newFeedUrl}</link>
        </image>"""

        # Get a list of all episodes
        episodeList = parseAllEpisodeInfo(targetFeed)

        # For each episode
        for episode in episodeList:
            print(f"[{getTime()}] Adding episode {episode['title']}")
            newFeed += f"""
        <item>
            <title>{episode['title']}</title>
            <pubDate>{episode['pubDate']}</pubDate>
            <description>{episode['description']}</description>"""

            if episode["enclosure"] is not None:
                # Create file name
                # Get the file extension at the end of the url
                episodeFileExtension = episode["enclosure"]["url"].split(".")[-1]
                # Make sure the file name only has alphanumeric characters
                episodeFilename = makeAlphanumeric(episode["title"])
                if len(episodeFilename) > 250:
                    episodeFilename = episodeFilename[:250]
                episodeFilename = episodeFilename + "." + episodeFileExtension

                # Check if we have the episode downloaded already. If we don't, download it
                episodePath = feedPath + "/" + episodeFilename
                if not os.path.exists(episodePath):
                    print(f'[{getTime()}] Downloading file for: {episode["title"]}')
                    getPage(episode["enclosure"]["url"], episodePath)

                # Add the episode information
                newFeed += f"""
            <enclosure url="{newFeedUrl}/{episodeFilename}" length="{episode['enclosure']['length']}" type="{episode['enclosure']['type']}"/>"""
            newFeed += """
        </item>"""

        newFeed += """
    </channel>
</rss>"""
        print(f"[{getTime()}] {headers['title']} feed created")

        # Save the new feed
        with open(feedPath + "/feed.txt", "w") as feedFile:
            feedFile.write(newFeed)


class podcastFetch(threading.Thread):
    def run(self):
        while True:
            fetchAllFeeds()
            time.sleep(int(config["Main"]["refreshInterval"]))

# Start the podcast fetcher
fetcher = podcastFetch()
fetcher.start()

# Start up the web server
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/work/data/podcasts", **kwargs)

with socketserver.TCPServer(("", WEB_PORT), Handler) as httpserver:
    print(f"[{getTime()}] Started web server on port {WEB_PORT}")
    httpserver.serve_forever()