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

