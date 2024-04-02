import os
import re
import json

from fetcher import Fetcher
import fetcherutil

class FetcherPlugin(Fetcher):
    def __init__(self, config):
        Fetcher.__init__(self, config) 


    def ExtractEpisodes(self, path, source):
        print("Extracting episodes from itunes feed")

        with open(path, mode='r', encoding='utf-8') as file:
            response = json.load(file)
        for item in response['results']:
            if item['wrapperType'] == 'podcastEpisode':
                title = item['trackName']
                episodeNo = self.GetEpisodeNo(title)
                if episodeNo != 0:
                    episode = {}
                    if source["primary"]:
                        episode['title'] = title
                        episode['filename'] = self.NormaliseFilename(title)
                        episode['shownotes'] = item['releaseDate']
                        episode['shownotes'] = self.TrimShownotesHtml(item['description'].strip())
                        episode['filename'] = self.NormaliseFilename(title)
                        episode['excerpt'] = self.MakeSummary(episode['shownotes'])
                        episode['image'] = item['artworkUrl600']
                        episode['interviewee'] = self.getSpeakers(title)

                    episode['id'] = self.MakeEpisodeId(episodeNo)
                    #episode['itunesAudioUrl'] = item['episodeUrl']
                    episode['itunesEpisodeUrl'] = item['trackViewUrl']
                    #episode['itunesImageUrl'] = item['artworkUrl600']

                    if not self.UpdateEpisodeDatafile(episode, source["primary"]) and source['only-new']:
                        print('Done importing from itunes')
                        break

    def fetch(self, source):
        if not 'id' in source:
            print(f"Source is missing required property 'id': {str(source)}")
            return False

        url = f"https://itunes.apple.com/lookup?id={source['id']}&media=podcast&entity=podcastEpisode&limit=200"
        path = self.HttpDownloadRss(url, 'itunes.json')
        if path:
            self.ExtractEpisodes(path, source)

        return True
