import os
import re

# Get the local path of the transcript for episodeID
# Optionally create the folder if it doesn't already exist
def GetTranscriptPath(episodeID, config, create = False):
    filepath = os.path.join(config['episode-folder'], str(episodeID))
    if create and not os.path.isdir(filepath):
        os.makedirs(filepath)
    return os.path.join(filepath, 'transcript.json')

# Get the episode ID from an audi or transcript file on S3
# i.e. remove the filename extension from 000.json or 000.m4a
def getEpisodeID(filename):
    filename = os.path.basename(filename)
    return re.sub("\.[^.]*", "", filename)

# Get the key of the file matching episodeID in the given bucket, or None if theer isn't one
# The filename extension is ignored
def S3EpisodeExists(episodeID, bucket, client):
    response = client.list_objects_v2(Bucket=bucket)
    if response["KeyCount"] > 0:
        for o in response['Contents']:
            if getEpisodeID(o["Key"]) == episodeID:
                #remoteModified = o["LastModified"]
                return o["Key"]
    return None
