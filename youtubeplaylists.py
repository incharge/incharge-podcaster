import os
#import sys
import yaml
#from datetime import datetime, timezone

# https://pypi.org/project/google-api-python-client/
# https://github.com/googleapis/google-api-python-client/blob/main/docs/README.md
#from googleapiclient.discovery import build
#from googleapiclient.errors import HttpError

class YouTubePlaylists():
    def __init__(self, fetcher, youtube, channelId, singleMode = False):
        # self.config = config
        self.fetcher = fetcher
        self.youtube = youtube
        self.channelId = channelId
        self.singleMode = singleMode
        # Dictionary of playlistNo: {id, title, count}
        self.playlists = {}
        # Dictionary of episodeNo: playlistNo
        self.episodes = {}
        self.playlistsChanged = False

    def name(self, episodeNo, videoId):
        if self.singleMode:
            self.getPlaylistItems(videoId)
        # TODO: Re-load the playlists?  Maybe there's a new one
        return self.playlists[self.episodes[episodeNo]]['title'] if episodeNo in self.episodes else None

    def confirm(self):
        if not self.singleMode or len(self.playlists) == 0:
            return
        if len(self.episodes) != 1:
            raise "More than one episode in single mode"
        playlistNo = next(iter(self.episodes.values()))
        self.playlists[playlistNo]['count'] += 1
        self.playlistsChanged = True

    def load(self):
        if self.singleMode:
            self.playlistsFromFile()
            if len(self.playlists) == 0:
                raise "No playlists"
        else:
            # Get playlists via YouTube API
            self.playlistsFromYouTube()
            # Get all PlaylistItems now
            self.getPlaylistItems()

    def playlistsFromYouTube(self):
        playlistNo = 1

        # Get playlists
        pageToken = ''
        while pageToken is not None:
            request = self.youtube.playlists().list(
                channelId = self.channelId,
                part = 'snippet',
                maxResults = 50,
                pageToken = pageToken
            )
            response = request.execute()
            for item in response['items']:
                self.playlists[ playlistNo ] = { 'id': item['id'], 'title': item['snippet']['title'], 'count': 0 }
                playlistNo += 1
                self.playlistsChanged = True
            pageToken = response['nextPageToken'] if 'nextPageToken' in response else None

    def getPlaylistItems(self, videoId = None ):
        if len(self.playlists) == 0 and videoId:
            raise 'getPlaylistItems: playlists must be populated in only-new mode'

        self.episodes = {}

        # For each playlist
        for playlistNo, playlist in self.playlists.items():
            # Get the videos for this playlist
            pageToken = ''
            while pageToken is not None:
                request = self.youtube.playlistItems().list(
                    playlistId = playlist['id'],
                    videoId = videoId if videoId else '',
                    part = 'snippet',
                    maxResults = 50,
                    pageToken = pageToken
                )
                response = request.execute()
                for item in response['items']:
                    episodeId = self.fetcher.GetEpisodeNo(item['snippet']['title'])
                    if episodeId:
                        if episodeId in self.episodes:
                            if type(self.episodes[episodeId]) == list:
                                self.episodes[episodeId].append(playlistNo)
                            else:
                                self.episodes[episodeId] = [self.episodes[episodeId], playlistNo]
                        else:
                            self.episodes[episodeId] = playlistNo
                    if not videoId:
                        playlist['count'] += 1
                pageToken = response['nextPageToken'] if 'nextPageToken' in response else None

        # Resolve duplicates
        for episodeId, playlistNos in self.episodes.items():
            if type(playlistNos) == list:
                # This episode is on more than one playlist
                print(f"Episode {episodeId} is in multiple playlists:")
                selectedPlaylistCount = 0
                for playlistNo in playlistNos:
                    # Find the playlist with the most videos
                    print(f"\t{self.playlists[playlistNo]['title']}")
                    playlistCount = self.playlists[playlistNo]['count']
                    if selectedPlaylistCount <= playlistCount:
                        selectedPlaylistNo = playlistNo
                        selectedPlaylistCount = playlistCount
                # This video is being removed from the other playlists, so decrement their counts
                if not videoId:
                    for playlistNo in playlistNos:
                        if playlistNo != selectedPlaylistNo:
                            self.playlists[playlistNo]['count'] -= 1
                self.episodes[episodeId] = selectedPlaylistNo

        # Remove empty playlists
        if not videoId:
            playlistNos = [playlistNo for playlistNo, playlist in self.playlists.items() if playlist['count'] == 0]
            for playlistNo in playlistNos:
                del self.playlists[playlistNo]

    def playlistsFromFile(self):
        configpath = 'categories.yaml'
        if os.path.isfile(configpath):
            try:
                with open(configpath, mode='r', encoding='utf-8') as configfile:
                    self.playlists = yaml.safe_load(configfile)
            except Exception as error:
                print(f"Error reading the playlists file ({type(error).__name__}): {error}")

    def save(self):
        if self.playlistsChanged:
            with open('categories.yaml', mode='w', encoding='utf-8') as configfile:
                yaml.dump(self.playlists, configfile)
