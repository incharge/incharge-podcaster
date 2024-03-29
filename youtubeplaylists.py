import os
import yaml

class YouTubePlaylists():
    def __init__(self, youtubeAPI, channelId, singleMode = False):
        # self.config = config
        self.youtubeAPI = youtubeAPI
        self.channelId = channelId
        self.singleMode = singleMode
        # Dictionary of playlistNo: {id, title, count}
        self.playlists = {}
        # Dictionary of videoId: playlistNo
        self.videos = {}
        self.playlistsChanged = False

    def name(self, videoId):
        if self.singleMode:
            self.getPlaylistItems(videoId)
        # TODO: Re-load the playlists?  Maybe there's a new one
        return self.playlists[self.videos[videoId]]['title'] if videoId in self.videos else None

    def confirm(self):
        if not self.singleMode or len(self.videos) == 0:
            return
        if len(self.videos) != 1:
            raise "More than one episode in single mode"
        playlistNo = next(iter(self.videos.values()))
        self.playlists[playlistNo]['count'] += 1
        self.playlistsChanged = True

    def load(self):
        if self.singleMode:
            self.loadFromFile()
            if len(self.playlists) == 0:
                raise "No playlists"
        else:
            # Get playlists via YouTube API
            self.loadFromAPI()
            # Get all PlaylistItems now
            self.getPlaylistItems()

    def loadFromAPI(self):
        playlistNo = 1

        # Get playlists
        pageToken = ''
        while pageToken is not None:
            request = self.youtubeAPI.youtube.playlists().list(
                channelId = self.channelId,
                part = 'snippet',
                maxResults = 50,
                pageToken = pageToken
            )
            response = self.youtubeAPI.execute(request, ['channelId', 'pageToken'])

            for item in response['items']:
                self.playlists[ playlistNo ] = { 'id': item['id'], 'title': item['snippet']['title'], 'count': 0 }
                playlistNo += 1
                self.playlistsChanged = True
            pageToken = response['nextPageToken'] if 'nextPageToken' in response else None

    def getPlaylistItems(self, singleVideoId = None ):
        if len(self.playlists) == 0 and singleVideoId:
            raise 'getPlaylistItems: playlists must be populated in only-new mode'

        self.videos = {}

        # For each playlist
        for playlistNo, playlist in self.playlists.items():
            # Get the videos for this playlist
            pageToken = ''
            while pageToken is not None:
                request = self.youtubeAPI.youtube.playlistItems().list(
                    playlistId = playlist['id'],
                    videoId = singleVideoId if singleVideoId else '',
                    part = 'snippet',
                    maxResults = 50,
                    pageToken = pageToken
                )
                response = self.youtubeAPI.execute(request, ['playlistId', 'videoId', 'pageToken'])
                for item in response['items']:
                    videoId = item['snippet']['resourceId']['videoId']
                    if videoId in self.videos:
                        if type(self.videos[videoId]) == list:
                            self.videos[videoId].append(playlistNo)
                        else:
                            self.videos[videoId] = [self.videos[videoId], playlistNo]
                    else:
                        self.videos[videoId] = playlistNo
                    if not singleVideoId:
                        playlist['count'] += 1
                pageToken = response['nextPageToken'] if 'nextPageToken' in response else None

        # Resolve duplicates
        for videoId, playlistNos in self.videos.items():
            if type(playlistNos) == list:
                # This episode is on more than one playlist
                print(f"Video {videoId} is in multiple playlists:")
                selectedPlaylistCount = 0
                for playlistNo in playlistNos:
                    # Find the playlist with the most videos
                    print(f"\t{self.playlists[playlistNo]['title']}")
                    playlistCount = self.playlists[playlistNo]['count']
                    if selectedPlaylistCount <= playlistCount:
                        selectedPlaylistNo = playlistNo
                        selectedPlaylistCount = playlistCount
                # This video is being removed from the other playlists, so decrement their counts
                if not singleVideoId:
                    for playlistNo in playlistNos:
                        if playlistNo != selectedPlaylistNo:
                            self.playlists[playlistNo]['count'] -= 1
                self.videos[videoId] = selectedPlaylistNo

        # Remove empty playlists
        if not singleVideoId:
            playlistNos = [playlistNo for playlistNo, playlist in self.playlists.items() if playlist['count'] == 0]
            for playlistNo in playlistNos:
                del self.playlists[playlistNo]

    def loadFromFile(self):
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
