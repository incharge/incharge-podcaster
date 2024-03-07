import os
from datetime import datetime, timezone
import boto3

import fetcherutil
from fetcher import Fetcher

# -------- S3 --------  -- Local -  Newer   Action
# audio     transcript  transcript
# N         N           N           x       0       Do nothing - import didn't upload audio for some reason
# N         N           Y           x       0       Do nothing - Transcript has already been generated
# x         Y           N           x       1       Download transcript
# x         Y           Y           N       -1      Delete from S3
# x         Y           Y           Y       2       Download transcript (overwrite)
# Y         N           N           x       0       Do nothing - Waiting for transcript to be generated
# Y         N           Y           x       0       Do nothing - Waiting for transcript to be re-generated?
class FetcherPlugin(Fetcher):
    def __init__(self, config):
        Fetcher.__init__(self, config) 

    def fetch(self, source):
        client = boto3.client('s3')
        response = client.list_objects_v2(Bucket=self.config['transcript-bucket'])
        if response["KeyCount"] > 0:
            for o in response['Contents']:
                filename = o["Key"]
                episodeID = fetcherutil.getEpisodeID(filename)
                action = 0
                if filename.endswith(".json") and episodeID is not None:
                    filepath = fetcherutil.GetTranscriptPath(episodeID, self.config, True)
                    if os.path.isfile(filepath):
                        # Get modified for both
                        remoteModified = o["LastModified"]
                        localModified = os.path.getmtime(filepath)
                        localModified = datetime.fromtimestamp(localModified, timezone.utc)
                        if remoteModified > localModified:
                            # This transcript is newer, it's been regenerated, so download it and overwrite the local version
                            action = 2
                        else:
                            # This transcript has already been imported on a previous import, so delete it
                            action = -1
                    else:
                        # This transcript is new
                        action = 1

                    if action > 0:
                        # Download the transcript
                        print('Getting transcript for episode ' + episodeID + ' from ' + filename + ' to ' + filepath)
                        client.download_file(self.config['transcript-bucket'], filename, filepath)
                    elif action < 0:
                        # Delete the remote transcript
                        print('Deleting previously imported transcript for episode ' + episodeID + ' ' + filename)
                        client.delete_object(Bucket=self.config['transcript-bucket'], Key=filename)
                        # Delete the remote audio, if it exists
                        filename = fetcherutil.S3EpisodeExists(episodeID, self.config['audio-bucket'], client)
                        if filename:
                            client.delete_object(Bucket=self.config['audio-bucket'], Key=filename)
                    # else zero action i.e. Do nothing
                # else - not a transcript file, so ignore it
        # else - There are no transcripts on S3
