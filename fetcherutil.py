import os
import re

# Get the local path of the transcript for episodeID
# Optionally create the folder if it doesn't already exist
def GetTranscriptPath(episodeID, config, create = False):
    filepath = os.path.join(config['episode-folder'], str(episodeID))
    if create and not os.path.isdir(filepath):
        os.makedirs(filepath)
    return os.path.join(filepath, 'transcript.json')

# Get the episode ID from an audio or transcript file
#   e.g. uploaded to S3: 123.m4a, 123.4.mp3
# or downloaded from S3: 123.json
def getEpisodeID(filename):
    filename = os.path.basename(filename)
    # Remove everything from the first dot
    return re.sub("\..*$", "", filename)

# Get the key of the file matching episodeID in the given bucket, or None if there isn't one
# The filename extension is ignored
def S3EpisodeExists(episodeID, bucket, prefix, client):
    # See https://www.peterbe.com/plog/fastest-way-to-find-out-if-a-file-exists-in-s3
    # https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListObjectsV2.html
    # There doesn't appear to be a way to filter (e.g. using wildcards)
    response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    if response["KeyCount"] > 0:
        for o in response['Contents']:
            if getEpisodeID(o["Key"]) == episodeID:
                #remoteModified = o["LastModified"]
                return o["Key"]
    return None
