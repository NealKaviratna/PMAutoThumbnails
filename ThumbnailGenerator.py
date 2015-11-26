#!/usr/bin/python

import httplib2
import os
import sys
import time

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

from PIL import Image, ImageDraw


# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains

# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google Developers Console at
# https://console.developers.google.com/.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#    https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#    https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secrets.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:
     %s
with information from the APIs Console
https://console.developers.google.com

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__), CLIENT_SECRETS_FILE))

# Authorize the request and store authorization credentials.
def get_authenticated_service():
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_READ_WRITE_SCOPE,
        message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
        http=credentials.authorize(httplib2.Http()))


# Return videos of given channel
def get_video_titles(youtube, channel_id):
    uploadsId = youtube.channels().list(part="contentDetails", id=channel_id).execute()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    print "Uploads playlist ID: " + uploadsId

    videoIds = []
    
    result = youtube.playlistItems().list(playlistId=uploadsId, part="contentDetails", maxResults=50).execute()
    try:
        nextPage = result['nextPageToken']
    except KeyError:
        nextPage = None

    i = 1
    while nextPage is not None:
        videoIds += [item['contentDetails']['videoId'] for item in result['items']]
        
        result = youtube.playlistItems().list(playlistId=uploadsId, part="contentDetails", maxResults=50, pageToken=nextPage).execute()
        try:
            nextPage = result['nextPageToken']
        except KeyError:
            nextPage = None
        i += 1
        nextPage = None
        print "Next Page " + str(i)

    titles = []
    i = 0
    for videoId in videoIds:
        i += 1
        print "Video " + str(i) #+ youtube.videos().list(id=videoId, part="snippet").execute()['items'][0]['snippet']['title']
        titles.append([ youtube.videos().list(id=videoId, part="snippet").execute()['items'][0]['snippet']['title'] , videoId])
        #print youtube.videos().list(id=videoId, part="snippet").execute()['items'][0]['snippet']['title']
        
    return titles

# Recorded Set class, represents a full youtube video and its data
# TODO: make parsing exceptions for Chillin bodies everyone @ S@X
class RecordedSet:
    def __init__(self, title_data):
        self.title = title_data[0]
        self.videoID = title_data[1]
        self.image = None

        # TODO: why isn't this check working?
        if len(self.title) > 2:
            self.isImportantSet = self.title[2] is ':'
            self.Importance = "None"
            if self.isImportantSet:
                print "importance check working"
                if self.title[:2] is 'GF':
                    self.Importance = "Grand Finals"
                elif self.title[:2] is 'LF':
                    self.Importance = "Loser's Finals"
                elif self.title[:2] is 'LS':
                    self.Importance = "Loser's Semis"
                elif self.title[:2] is 'WF':
                    self.Importance = "Winner's Finals"
                elif self.title[:2] is 'WS':
                    self.Importance = "Winner's Semis"
                else:
                    self.Importance = "None"
                self.title = self.title[4:]
            
        self.eventName = self.title.partition(' - ')[0]
        self.date = None

        if len(self.eventName) > 3 and self.eventName[:-3] is '/':
            self.date = self.eventName[7:]
            self.eventName = 'Xanadu'
        else:
            #TODO hard code dates for other events
            pass

        playerData = self.title.partition(' - ')[2]
        player1Data = playerData.partition(' vs. ')[0]
        player2Data = playerData.partition(' vs. ')[2]

        self.p1 = player1Data.partition(' (')[0]
        p1CharData = player1Data.partition(' (')[2][:-1]
        self.p1Chars = p1CharData.split('/')
        self.p2 = player2Data.partition(' (')[0]
        p2CharData = player2Data.partition(' (')[2][:-1]
        self.p2Chars = p2CharData.split('/')

    def generate_thumbnail(self):
        base = Image.open("source/base.png")
        char1Path = "source/" + self.p1Chars[-1] + "Render.png"
        char2Path = "source/" + self.p2Chars[-1] + "Render.png"
        char1 = Image.open(char1Path)
        char2 = Image.open(char2Path)

        base.paste(char1, (10, 130))
        base.paste(char2, (800, 130))

        draw = ImageDraw.Draw(base)
        if self.isImportantSet:
            draw.text((640 - draw.textsize(self.Importance), 400), self.Importance, fill=255)
        draw.text((320 - draw.textsize(self.p1)[0], 60), self.p1, fill=255)
        draw.text((960 - draw.textsize(self.p2)[0], 60), self.p2, fill=255)

        draw.text((640 - draw.textsize(self.eventName)[0], 660), self.eventName, fill=255)
        if self.date is not None:
            draw.text((1000 - draw.textsize(self.date)[0], 660), self.date, fill=255)

        base.save("output/temp"+self.videoID+".jpg")
        self.image = base
        
        
            

    def upload_thumbnail(self):
        pass

    def __str__(self):
        if self.date is not None:
            return self.p1 + " using " + self.p1Chars[0] + " vs " + self.p2 + " using " + self.p2Chars[0] + " at " + self.eventName + "on" + self.date
        else:
            return self.p1 + " using " + self.p1Chars[0] + " vs " + self.p2 + " using " + self.p2Chars[0] + " at " + self.eventName
        

def main():
    youtube = get_authenticated_service()
    channel_id = "UClrSoHwVCJN_jtj7X1HXJaQ"
    titles = get_video_titles(youtube, channel_id)
    sets = []

    print "Creating Sets"
    for title in titles:
        sets.append(RecordedSet(title))

    for s in sets:
        s.generate_thumbnail()
        s.upload_thumbnail()
        time.sleep(30)
        print s


