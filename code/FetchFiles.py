#!/usr/bin/python3
# Based loosely off of RSSNSA https://notabug.org/SuspiciousActions/RSSNSA

# Dependencies:
# * Tor
# * torsocks
# * curl
# * python3

import subprocess

TOR_IP='127.0.0.1'
TOR_PORT='9050'
FAKE_USER_AGENT='Mozilla/5.0 (Windows NT 6.1) AppleWebKit/602.1 (KHTML, like Gecko) QuiteRSS/0.18.12 Safari/602.1'

def getPage(URL, outputPath=None):
    args = ['torsocks','--address',TOR_IP,'--port',TOR_PORT,'-i','curl','-L','--user-agent',FAKE_USER_AGENT]
    if outputPath is not None:
        subprocess.run(args + ["--output",outputPath,URL])
    else:
        output = subprocess.run(args + [URL], capture_output=True)
        return output.stdout.decode()


# Find and get the contents of a tag in a string
#
# searchString: the string to search in
# tagName: the name of the tag to get the contents of
# returns: String of the contents or None on failure
def parseTagContents(searchString, tagName):
    # Find the end of the opening tag, which is the start of the content
    start = searchString.find("<" + tagName)
    if start == -1:
        return
    # Find where the opening tag ends, and set the start to that
    start += searchString[start:].find(">") + 1

    end = searchString.find("</" + tagName + ">")
    if end == -1:
        return
    return searchString[start:end]


# Parse all episode information into a list of dictionaries
# feed: the RSS feed as a string
# Returns: dictionary with title, guid, enclosure(link to audio, length, and type), duration, pubDate or None on failure
def parseAllEpisodeInfo(feed):
    if feed.find("<rss") == -1:
        return

    episodeInfos = []
    currentIndex = 0
    while (True):
        # Get one episode tag at a time, break when we can't find any more
        episode = parseTagContents(feed[currentIndex:], "item")
        if episode is None:
            break

        # Get the information from the tags
        episodeInfo = dict()
        for value in ["title", "guid", "pubDate", "itunes:duration", "description"]:
            episodeInfo[value] = parseTagContents(episode, value)

        # Get the enclosure information
        if episode.find("<enclosure ") == -1:
            episodeInfo["enclosure"] = None
        else:
            enclosureText = episode[episode.find("<enclosure ") + len("<enclosure "):]
            enclosureText = enclosureText[:enclosureText.find("/>")]
            enclosureValues = dict()
            enclosureList = enclosureText.split(" ")
            for value in enclosureList:
                if value.find("=") == -1:
                    continue
                keyValue = value.split("=")
                enclosureValues[keyValue[0]] = keyValue[1][1:-1]
            episodeInfo["enclosure"] = enclosureValues

        episodeInfos.append(episodeInfo)
        currentIndex += feed[currentIndex:].find("</item>") + 7

    return episodeInfos


# Parse the headers for the feed and return them as a dictionary
# feed: the RSS feed as a string
# Returns: dictionary with most tags as strings, and image as a dict. None on failure
def parseHeaders(feed):
    if feed.find("<rss") == -1:
        return

    headers = dict()
    for tagName in ["ttl", "generator", "title", "language", "copyright", "description"]:
        headers[tagName] = parseTagContents(feed, tagName)

    imageTagContents = parseTagContents(feed, "image")
    imageDict = dict()
    for tagName in ["url", "link", "title"]:
        imageDict[tagName] = parseTagContents(imageTagContents, tagName)
    headers["image"] = imageDict

    return headers