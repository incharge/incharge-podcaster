import boto3
import uuid
import re
import traceback

def removePrefix(key):
    #parts = key.split('/')
    #return parts[len(parts)-1]
    return re.sub(r".*/", '', key)

# Replace from the first dot with .json e.g. xxx.0.mp3 or xxx.mp3 or xxx to xxx.json
def removeSuffix(key):
    return re.sub(r"\..*$", '', key)

# Get the maximum number of speakers from the key, if specified, otherwise default to 2
# e.g. If the file name is xxx.9.mp3, then the number of speakers is 9
def getSpeakerCount(key):
    inputKeyParts = key.split('.')
    return max(
        int(inputKeyParts[1]) if len(inputKeyParts) > 2 else 0
        , 2
    )

# Event is an S3 creation event.
# Returns a dict containing args for a transcription job.
# Use consistent=True for testing, otherwise the job name includes a guid
def getTranscriptionJobArgs(event, consistent=False):
    try:
        record = event['Records'][0]
        inputBucketName = record['s3']['bucket']['name']
        inputKey = record['s3']['object']['key']
        print("Creating transcription job for new S3 audio file...\n" \
                f"Input bucket: {inputBucketName} ({type(inputBucketName)}\n"
                f"Input key: {inputKey} ({type(inputKey)}"
        )
    except Exception as error:
        print(f"Exception processing lambda event...\n{traceback.format_exc()}")
        return None

    try:
        inputFile = removePrefix(inputKey)
        outputFile = removeSuffix(inputFile) + '.json'

        transcriptionJob = {
            'Media': {
                'MediaFileUri': 's3://' + inputBucketName + '/' + inputKey
            },
            'OutputBucketName': inputBucketName,
            'OutputKey': 'transcript/' + outputFile,
            'TranscriptionJobName': outputFile + ('' if consistent else '-' + str(uuid.uuid4())),
            'Settings': {
                'ShowSpeakerLabels': True,
                'MaxSpeakerLabels': getSpeakerCount(inputFile)
            },
            'LanguageCode' : 'en-US',
            'MediaFormat': 'mp3'
        }
    except Exception as error:
        print(f"Exception processing transcription parameters...\n{traceback.format_exc()}")
        return None

    return transcriptionJob

def lambda_handler(event, context):
    transcriptionJob = getTranscriptionJobArgs(event)

    if not transcriptionJob:
        return

    if transcriptionJob['OutputBucketName'].endswith('-dev'):
        print(f"Not starting transcription job in dev\n{transcriptionJob}")
        return

    try:
        client = boto3.client('transcribe')
        print(f"Starting transcription job:\n{transcriptionJob}" )
        response = client.start_transcription_job(**transcriptionJob)
        result = {
            'TranscriptionJobName': response['TranscriptionJob']['TranscriptionJobName']
        }
    except Exception as error:
        print(f"Exception starting transcription job...\n{traceback.format_exc()}")
        return

    return result
