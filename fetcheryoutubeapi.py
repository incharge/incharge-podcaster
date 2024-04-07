import os
import sys
from youtubeplaylists import YouTubePlaylists
from youtubeapi import YouTubeAPI


from fetcher import Fetcher

class FetcherPlugin(Fetcher):
    def __init__(self, config):
        Fetcher.__init__(self, config) 

    def fetch(self, source):
        print(f"Download episodes for channel {source['channel']} via Youtube API")

        if not 'GOOGLE_API_KEY' in os.environ:
            print("ERROR: Define environment variable: GOOGLE_API_KEY")
            sys.exit(1)

        youtubeAPI = YouTubeAPI(self.config)

        playlists = YouTubePlaylists(youtubeAPI, source['channel'], source['only-new'])
        playlists.load()

        # Equivalent to: https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=UUTUcatGD6xu4tAcxG-1D4Bg&key=<SPI_KEY>
        # https://googleapis.github.io/google-api-python-client/docs/dyn/youtube_v3.playlistItems.html#list
        request = youtubeAPI.youtube.playlistItems().list(
            playlistId = source['playlist'],
            part = 'snippet',
            maxResults = 50,
            fields = 'nextPageToken,items(id,snippet(title,publishedAt,description,resourceId(videoId),thumbnails(maxres(url))))'
        )

        print("Extracting episodes via YouTube API")
        #print( 'Videos in list %s' % uploads_playlist_id)
        newepisode = True
        if not source['only-new']:
            print("Importing all episodes")
        while (not source['only-new'] or newepisode) and request:
            # Fetch the next page
            response = youtubeAPI.execute(request, ['playlistId', 'pageToken'])
            for playlist_item in response['items']:
                title = playlist_item['snippet']['title'].strip()
                episodeNo = self.GetEpisodeNo(title)
                if episodeNo != 0:
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

                    tags = playlists.names(episode['youtubeid'])
                    if tags:
                        episode['tags'] = tags
                    else:
                        print(f"Episode {episodeNo} is in no playlists")

                    newepisode = self.UpdateEpisodeDatafile(episode, source["primary"])
                    if source['only-new'] and not newepisode:
                        print('Done importing from YouTube API')
                        break

            # Set up the query for the next page
            if not source['only-new'] or newepisode:
                request = youtubeAPI.youtube.playlistItems().list_next(request, response)

        playlists.save()
