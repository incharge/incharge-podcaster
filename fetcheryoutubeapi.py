import os
import sys
#from datetime import datetime, timezone

from googleapiclient.discovery import build
#from googleapiclient.errors import HttpError

from fetcher import Fetcher

class FetcherPlugin(Fetcher):
    def __init__(self, config):
        Fetcher.__init__(self, config) 

    def fetch(self, source):
        print(f"Download episodes for channel {source['channel']} via Youtube API")

        if not 'GOOGLE_API_KEY' in os.environ:
            print("ERROR: Define environment variable: GOOGLE_API_KEY")
            sys.exit(1)

        apiKey = os.environ['GOOGLE_API_KEY']
        youtube = build('youtube', 'v3', developerKey=apiKey)

        # Equivalent to: https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=UUTUcatGD6xu4tAcxG-1D4Bg&key=<SPI_KEY>
        playlistitems_list_request = youtube.playlistItems().list(
            playlistId = source['channel'],
            part = 'snippet',
            maxResults = 50
        )

        print("Extracting episodes via YouTube API")
        #print( 'Videos in list %s' % uploads_playlist_id)
        newepisode = True
        onlyNewEpisodes = source['only-new'] if 'only-new' in source else True
        if not onlyNewEpisodes:
            print("Importing all episodes")
        while (not onlyNewEpisodes or newepisode) and playlistitems_list_request:
            # Fetch the next page
            playlistitems_list_response = playlistitems_list_request.execute()

            for playlist_item in playlistitems_list_response['items']:
                title = playlist_item['snippet']['title'].strip()
                episodeNo = self.GetEpisodeNo(title)
                if episodeNo != 0: # and episodeNo > 850:
                    episode = {}
                    episode['id'] = self.MakeEpisodeId(episodeNo)
                    episode['title'] = title

                    publishedDate = playlist_item['snippet']['publishedAt']
                    publishedDate = publishedDate[0:10]
                    episode['published'] = publishedDate

                    episode['shownotes'] = self.TrimShownotes(playlist_item['snippet']['description'])

                    episode['filename'] = self.NormaliseFilename(title)
                    episode['excerpt'] = self.MakeSummary(episode['shownotes'])

                    episode['youtubeid'] = playlist_item['snippet']['resourceId']['videoId']
                    episode['image'] = self.NormaliseImageUrl(playlist_item['snippet']['thumbnails']['maxres']['url'])

                    episode['interviewee'] = self.getSpeakers(title)

                    newepisode = self.UpdateEpisodeDatafile(episode, source["primary"])
                    if onlyNewEpisodes and not newepisode:
                        print('Done importing from YouTube API')
                        break

            # if episodeNo < 850:
            #     return
            # else:

            # Set up the query for the next page
            playlistitems_list_request = youtube.playlistItems().list_next(
                playlistitems_list_request, playlistitems_list_response)
    