import os
import sys
import yaml
#from datetime import datetime, timezone

# https://pypi.org/project/google-api-python-client/
# https://github.com/googleapis/google-api-python-client/blob/main/docs/README.md
from googleapiclient.discovery import build
#from googleapiclient.errors import HttpError

from fetcher import Fetcher

class FetcherPlugin(Fetcher):
    def __init__(self, config):
        Fetcher.__init__(self, config) 

    def playlistsFromYouTube(self, youtube, source):
        playlists =  {}
        playlistNo = 1

        # Get playlists
        pageToken = ''
        while pageToken is not None:
            request = youtube.playlists().list(
                channelId = source['channel'],
                part = 'snippet',
                maxResults = 50,
                pageToken = pageToken
            )
            response = request.execute()
            for item in response['items']:
                playlists[ playlistNo ] = { 'id': item['id'], 'title': item['snippet']['title'], 'count': 0 }
                playlistNo += 1
            pageToken = response['nextPageToken'] if 'nextPageToken' in response else None
        return playlists

    def getPlaylistItems(self, youtube, playlists, videoId = None ):
        if len(playlists) == 0 and videoId:
            raise 'getPlaylistItems: playlists must be populated in only-new mode'
        episodes = {}

        # For each playlist
        for playlistNo, playlist in playlists.items():
            # Get the videos for this playlist
            pageToken = ''
            while pageToken is not None:
                request = youtube.playlistItems().list(
                    playlistId = playlist['id'],
                    videoId = videoId if videoId else '',
                    part = 'snippet',
                    maxResults = 50,
                    pageToken = pageToken
                )
                response = request.execute()
                for item in response['items']:
                    episodeId = self.GetEpisodeNo(item['snippet']['title'])
                    if episodeId:
                        if episodeId in episodes:
                            if type(episodes[episodeId]) == list:
                                episodes[episodeId].append(playlistNo)
                            else:
                                episodes[episodeId] = [episodes[episodeId], playlistNo]
                        else:
                            episodes[episodeId] = playlistNo
                    if videoId:
                        playlist['count'] += 1
                pageToken = response['nextPageToken'] if 'nextPageToken' in response else None

        # Resolve duplicates
        for episodeId, playlistNos in episodes.items():
            if type(playlistNos) == list:
                # This episode is on more than one playlist
                print(f"Episode {episodeId} is in multiple playlists:")
                selectedPlaylistCount = 0
                for playlistNo in playlistNos:
                    # Find the playlist with the most videos
                    print(f"\t{playlists[playlistNo]['title']}")
                    playlistCount = playlists[playlistNo]['count']
                    if selectedPlaylistCount <= playlistCount:
                        selectedPlaylistNo = playlistNo
                        selectedPlaylistCount = playlistCount
                # This video is being removed from the other playlists, so decrement their counts
                if videoId:
                    for playlistNo in playlistNos:
                        if playlistNo != selectedPlaylistNo:
                            playlists[playlistNo]['count'] -= 1
                episodes[episodeId] = selectedPlaylistNo

        # Remove empty playlists
        if videoId:
            playlistNos = [playlistNo for playlistNo, playlist in playlists.items() if playlist['count'] == 0]
            for playlistNo in playlistNos:
                del playlists[playlistNo]

        return episodes

    def playlistsFromFile(self):
        configpath = 'categories.yaml'
        if os.path.isfile(configpath):
            try:
                with open(configpath, mode='r', encoding='utf-8') as configfile:
                    self.config['playlists'] = yaml.safe_load(configfile)
            except Exception as error:
                print(f"Error reading the playlists file ({type(error).__name__}): {error}")

    def playlistsToFile(self):
        with open('categories.yaml', mode='w', encoding='utf-8') as configfile:
            yaml.dump(self.config['playlists'], configfile)

    def fetch(self, source):
        print(f"Download episodes for channel {source['channel']} via Youtube API")

        if not 'GOOGLE_API_KEY' in os.environ:
            print("ERROR: Define environment variable: GOOGLE_API_KEY")
            sys.exit(1)

        apiKey = os.environ['GOOGLE_API_KEY']
        youtube = build('youtube', 'v3', developerKey=apiKey)

        playlistsChanged = False
        if source['only-new']:
            self.playlistsFromFile()

        if 'playlists' not in self.config or not source['only-new']:
            # Get playlists via YouTube API
            self.config['playlists'] = self.playlistsFromYouTube(youtube, source)
            playlistsChanged = True
        # else - Playlists are already in the config

        if source["only-new"]:
            # Get PlaylistItems as required
            playlistItems = None
        else:
            # Get all PlaylistItems now
            playlistItems = self.getPlaylistItems(youtube, self.config['playlists'])
            playlistsChanged = True

        # Equivalent to: https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=UUTUcatGD6xu4tAcxG-1D4Bg&key=<SPI_KEY>
        # https://googleapis.github.io/google-api-python-client/docs/dyn/youtube_v3.playlistItems.html#list
        playlistitems_list_request = youtube.playlistItems().list(
            playlistId = source['playlist'],
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

                    if source['only-new']:
                        playlistItems = self.getPlaylistItems(youtube, self.config['playlists'], episode['youtubeid'])
                        playlistsChanged = True
                    if episodeNo in playlistItems:
                        episode['category'] = self.config['playlists'][playlistItems[episodeNo]]['title']
                    else:
                        print(f"Episode {episodeNo} is in no playlists")
                        # TODO: Re-load the playlists?  Maybe there's a new one
                    newepisode = self.UpdateEpisodeDatafile(episode, source["primary"])
                    if onlyNewEpisodes:
                        if newepisode:
                            if episodeNo in playlistItems:
                                self.config['playlists'][playlistItems[episodeNo]]['count'] += 1
                        else:
                            print('Done importing from YouTube API')
                        break

            # if episodeNo < 850:
            #     return
            # else:

            # Set up the query for the next page
            playlistitems_list_request = youtube.playlistItems().list_next(
                playlistitems_list_request, playlistitems_list_response)

        if playlistsChanged:
            self.playlistsToFile()
