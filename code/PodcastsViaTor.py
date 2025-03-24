#!/usr/bin/python3
# Based loosely off of RSSNSA https://notabug.org/SuspiciousActions/RSSNSA

# Dependencies:
# * Tor
# * python3
# * python3 requests
# * python3 requests[socks]
# * python3 selenium

from FetchFiles import getPage, parseHeaders, parseAllEpisodeInfo, AudioDownloader
import time
from datetime import datetime
from configparser import ConfigParser
import os
import http.server
import socketserver
import threading
import traceback
from string import Template

WEB_PORT = 80

def getTime():
    return datetime.now().strftime('%Y/%m/%d %H:%M')


def makeAlphanumeric(text):
    newText = ""
    for char in text:
        if char.lower() in "abcdefghijklmnopqrstuvwxyz1234567890":
            newText += char
    return newText


feedTemplate = Template("""<rss version=\"2.0\">
    <channel>
        <title>${title}</title>
        <link>${link}</link>
        <description>${description}</description>
        <image>
            <url>${imageUrl}</url>
            <title>${imageTitle}</title>
            <link>${imageLink}</link>
        </image>${items}
    </channel>
</rss>""")

itemTemplate = Template("""
        <item>
            <title>${title}</title>
            <pubDate>${pubDate}</pubDate>
            <guid isPermaLink="false">${guid}</guid>
            <description>${description}</description>
            ${enclosure}
        </item>""")

enclosureTemplate = Template("""<enclosure url="${url}" length="${length}" type="${type}"/>""")

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


class podcastFetch(threading.Thread):
    def fetchFeed(self, feedLink, audioDownloader):
        print(f"[{getTime()}] Getting feed: {feedLink}")
        # Get the feed
        targetFeed = getPage(feedLink)
        while targetFeed is None:
            print(f"[{getTime()}] Retrying fetching feed")
            targetFeed = getPage(feedLink)

        # Get the headers, for the new feed
        headers = parseHeaders(targetFeed)
        newFeedUrl = config["Main"]["hostname"] + "/" + makeAlphanumeric(headers["title"])

        # Create a folder for the feed if we don't have one
        feedPath = "data/podcasts/" + makeAlphanumeric(headers["title"])
        os.makedirs(feedPath, exist_ok = True)

        # Get the feed image if we don't have it
        # Remove any GET parameters
        thumbnailName = headers["image"]["url"].split("?")[0]
        thumbnailName = thumbnailName.split("/")[-1]

        if not os.path.exists(feedPath + "/" + thumbnailName):
            print(f"[{getTime()}] Getting podcast image")
            getPage(headers["image"]["url"], feedPath + "/" + thumbnailName)

        # Get a list of all episodes
        episodeList = parseAllEpisodeInfo(targetFeed)
        # Cut the list down to the maximum amount
        episodeLimit = int(config["Main"]["episodeLimit"])
        if episodeLimit != 0:
            episodeList = episodeList[:episodeLimit]

        noNewEpisodes = True
        # Make a set for storing episode file names, used for cleaning out older files. Includes thumbnail and feed file
        episodeFilenames = set()
        episodeFilenames.add(thumbnailName)
        episodeFilenames.add("feed.txt")

        newFeedItems = ""
        # For each episode
        for episode in episodeList:
            enclosure = ""
            if episode["enclosure"] is not None:
                # Get the file extension at the end of the url
                # Remove any GET parameters
                episodeFileExtension = episode["enclosure"]["url"].split("?")[0]
                episodeFileExtension = episodeFileExtension.split(".")[-1]
                # Create file name
                # Make sure the file name only has alphanumeric characters
                episodeFilename = makeAlphanumeric(episode["title"])
                if len(episodeFilename) > 250:
                    episodeFilename = episodeFilename[:250]
                episodeFilename = episodeFilename + "." + episodeFileExtension

                # Check if we have the episode downloaded already. If we don't, download it
                episodePath = feedPath + "/" + episodeFilename
                if not os.path.exists(episodePath):
                    noNewEpisodes = False
                    print(f'[{getTime()}] Downloading file for: {episode["title"]}')
                    audioDownloader.download(episode["enclosure"]["url"], episodePath)

                # Add the episode filename to the set
                episodeFilenames.add(episodeFilename)
                # Create the enclosure for the file
                enclosure = enclosureTemplate.substitute(url=newFeedUrl + "/" + episodeFilename, length=episode['enclosure']['length'], type=episode['enclosure']['type'])

            # Add the episode information
            newFeedItems += itemTemplate.substitute(title=episode['title'], pubDate=episode['pubDate'], guid=episode['guid'], description=episode['description'], enclosure=enclosure)

        # Clear out old files
        if feedLink in config["Main"]["cleanupFeeds"].split(","):
            for feedFile in os.listdir(feedPath):
                if not feedFile in episodeFilenames:
                    print(f"[{getTime()}] Cleaning up {feedFile}")
                    os.remove(f"{feedPath}/{feedFile}")

        if noNewEpisodes:
            print(f"[{getTime()}] No new episodes for {headers['title']}")

        newFeed = feedTemplate.substitute(title=headers["title"], link=newFeedUrl, description=headers["description"],
            imageUrl=newFeedUrl + "/" + thumbnailName, imageTitle=headers["image"]["title"], items=newFeedItems, imageLink=newFeedUrl)

        print(f"[{getTime()}] {headers['title']} feed created")

        # Save the new feed
        with open(feedPath + "/feed.txt", "w") as feedFile:
            feedFile.write(newFeed)


    def run(self):
        audioDownloader = AudioDownloader()
        while True:
            try:
                # Get the target feed links
                feedList = open("data/feeds.txt", "r")

                # Fetch each feed
                for feedLink in feedList:
                    feedLink = feedLink.strip()
                    self.fetchFeed(feedLink, audioDownloader)

                time.sleep(int(config["Main"]["refreshInterval"]))
            except:
                print(traceback.format_exc())

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