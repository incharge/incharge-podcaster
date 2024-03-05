import os
import re
import xml.etree.ElementTree as et # See https://docs.python.org/3/library/xml.etree.elementtree.html
import boto3

from fetcher import Fetcher
import fetcherutil

class FetcherPlugin(Fetcher):
    def __init__(self, config):
        Fetcher.__init__(self, config) 

    # 	if local transcript file doesn't exist
    # 		if remote transcript file doesn't exist
    # 			if remote audio file doesn't exist
    # 				upload to S3
    # 	else - maybe data file was deleted to force its recreation, so if the transcript remains, it's not intended to be regenerated
    def InitiateTranscription(self, episodeID, config, audioUrl):
        # Is there already a local transcript file for this episode?
        if not os.path.isfile( fetcherutil.GetTranscriptPath(episodeID, self.config) ):
            # Is there already a remote transcript file for this episode?
            client = boto3.client('s3')
            if not fetcherutil.S3EpisodeExists(episodeID, config['transcript-bucket'], client):
                # Is there already a remote audio file for this episode?
                if not fetcherutil.S3EpisodeExists(episodeID, config['audio-bucket'], client):
                    filename, count = re.subn(r'^.*(\.[a-z0-9]+)$', r'\1', audioUrl)
                    if count == 0: filename = '.mp3'
                    filename = str(episodeID) + filename
                    self.HttpDownload(audioUrl, filename)
                    client.upload_file(filename, config['audio-bucket'], filename)
        # else - maybe episode data file was deleted to force its recreation, so if the transcript remains, it's not intended to be regenerated

    def ExtractSpotify(self, root, source):
        print("Extracting episodes from Spotify feed")
        channel = root.find('channel')
        itunesNamespace = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}
        onlyNewEpisodes = source['only-new'] if 'only-new' in source else True
        if onlyNewEpisodes:
            print("Importing new episodes from RSS")
        else:
            print("Importing all episodes from RSS")
        for item in channel.iter('item'):
            title = item.find('title').text.strip()
            episodeNo = self.GetEpisodeNo(title)
            if episodeNo != 0:
                episode = {}
                episode['title'] = title
                episode['filename'] = self.NormaliseFilename(title)

                publishedDate = item.find('pubDate').text
                # episode['spotifypublished'] = publishedDate
                publishedDate = self.NormaliseDateFormat(publishedDate)
                episode['published'] = publishedDate

                #episode['id'] = MakeEpisodeId(title, publishedDate)
                episode['id'] = self.MakeEpisodeId(episodeNo)

                episode['spotifyAudioUrl'] = item.find('enclosure').attrib['url']
                episode['spotifyEpisodeUrl'] = item.find('link').text
                episode['spotifyImageUrl'] = item.find('itunes:image', itunesNamespace).attrib['href']

                # # print("guid ", item.find('guid').text)
                # # print("duration: ", item.find('itunes:duration', itunesNamespace).text)

                if onlyNewEpisodes and not self.UpdateEpisodeDatafile(episode, False):
                    print('Done importing from RSS')
                    break
                else:
                    # Is transcription configured?
                    if 'transcript-bucket' in self.config and 'audio-bucket' in self.config:
                        # Is there already a remote audio file for this episode?
                        if int(episode['id']) > 900:
                            self.InitiateTranscription(episode['id'], self.config, episode['spotifyAudioUrl'])
                        else:
                            print("WARNING: Re-importing episode from spotify: " + episode['id'])

    def fetch(self, source):
        if not 'url' in source:
            print(f"Source is missing required property 'url': {str(source)}")
            return False

        rsspath = self.HttpDownloadRss(source['url'], 'spotify.xml')
        if rsspath:
            tree = et.parse(rsspath)
            root = tree.getroot()
            self.ExtractSpotify(root, source)

        return True
