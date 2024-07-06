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
