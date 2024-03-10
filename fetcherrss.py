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
    def InitiateTranscription(self, episode):
        episodeID = episode['id']
        audioUrl = episode['spotifyAudioUrl']
        path = fetcherutil.GetTranscriptPath(episodeID, self.config)
        if os.path.isfile(path):
            # There is already a local transcript file for this episode
            # Maybe episode data file was deleted to force its recreation, so if the transcript remains, it's not intended to be regenerated
            print(f"Not uploading audio file already transcribed locally: Episode '{episodeID}' in '{path}")
        else:
            client = boto3.client('s3')
            if fetcherutil.S3EpisodeExists(episodeID, self.config['bucket'], self.config['transcript-prefix'], client):
                # There is already a remote transcript file for this episode
                print(f"Not uploading audio file already transcribed: Episode '{episodeID}' in bucket '{self.config['bucket']}/{self.config['transcript-prefix']}'")
            else:
                if fetcherutil.S3EpisodeExists(episodeID, self.config['bucket'], self.config['audio-prefix'], client):
                    # The audio file for this episode has already been uploaded
                    print(f"Not uploading audio file already uploaded: '{filename}' in bucket '{self.config['bucket']}/{self.config['audio-prefix']}'")
                else:
                    filename, count = re.subn(r'^.*(\.[a-z0-9]+)$', r'\1', audioUrl)
                    if count == 0: filename = '.mp3'
                    speakers = len(episode['interviewee']) + 1 if "interviewee" in episode else 0
                    filename = \
                        str(episodeID) \
                        + (('.' + str(speakers)) if speakers else "") \
                        + filename
                    print(f"Uploading audio file for transcription: '{filename}' to bucket '{self.config['bucket']}/{self.config['audio-prefix']}'")
                    path = self.HttpDownloadRss(audioUrl, filename)
                    client.upload_file(path, self.config['bucket'], self.config['audio-prefix'] + '/' + filename)

    def ExtractSpotify(self, root, source):
        print("Extracting episodes from Spotify feed")
        transcribeCount = 0
        maxTranscribeCount = self.config["transcribe-max"]

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

                if source["primary"]:
                    episode['title'] = title
                    episode['filename'] = self.NormaliseFilename(title)
                    publishedDate = item.find('pubDate').text
                    # episode['spotifypublished'] = publishedDate
                    publishedDate = self.NormaliseDateFormat(publishedDate)
                    episode['published'] = publishedDate
                    episode['shownotes'] = self.TrimShownotesHtml(item.find('description').text.strip())
                    episode['filename'] = self.NormaliseFilename(title)
                    episode['excerpt'] = self.MakeSummary(episode['shownotes'])
                    episode['image'] = item.find('itunes:image', itunesNamespace).attrib['href']
                    episode['interviewee'] = self.getSpeakers(title)

                #episode['id'] = MakeEpisodeId(title, publishedDate)
                episode['id'] = self.MakeEpisodeId(episodeNo)

                episode['spotifyAudioUrl'] = item.find('enclosure').attrib['url']
                episode['spotifyEpisodeUrl'] = item.find('link').text
                episode['spotifyImageUrl'] = item.find('itunes:image', itunesNamespace).attrib['href']

                # # print("guid ", item.find('guid').text)
                # # print("duration: ", item.find('itunes:duration', itunesNamespace).text)

                # If new then submit for transcription, if not new and we only want new then break
                # ---Condition----     ----Result----
                # new      onlynew     transcript   break
                # 0        0           0            0
                # 0        1           0            1
                # 1        0           0            0
                # 1        1           1            0
                if self.UpdateEpisodeDatafile(episode, source["primary"]):
                    # Is transcription configured?
                    if onlyNewEpisodes and 'bucket' in self.config:
                        transcribeCount += 1
                        if transcribeCount > maxTranscribeCount:
                            print(f"WARNING: Skipping transcription of episode {episode['id']} due to exceeding maximum of {maxTranscribeCount}")
                        else:
                            self.InitiateTranscription(episode)
                elif onlyNewEpisodes:
                    print('Done importing from RSS')
                    break

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
