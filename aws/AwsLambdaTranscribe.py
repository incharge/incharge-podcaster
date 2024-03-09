import boto3
import uuid
import re
import traceback

def getTranscriptionJobArgs(event):
    try:
        record = event['Records'][0]
        inputBucketName = record['s3']['bucket']['name']
        inputKey = record['s3']['object']['key']
        print("Processing new audio event...\n" \
                f"Input bucket: {inputBucketName} ({type(inputBucketName)}\n"
                f"Input key: {inputKey} ({type(inputKey)}"
        )
    except Exception as error:
        print(f"Exception processing lambda event...\n{traceback.format_exc()}")
        return None

    try:
        # Replace from the first dot with .json e.g. xxx.0.mp3 or xxx.mp3 or xxx to xxx.json
        outputKey = re.sub(r"\..*$", '', inputKey) + ".json"

        outputBucketName = re.sub(r"episode$", "transcript", inputBucketName)
        s3Path = "s3://" + inputBucketName + "/" + inputKey
        jobName = inputKey + '-' + str(uuid.uuid4())

        # Get the maximum number of speakers from the key, if specified, otherwise default to 2
        # If the file name is in the format xxx.0.mp3, then the number is the number of speakers
        inputKeyParts = inputKey.split('.')
        maxSpeakerLabels = max(
            int(inputKeyParts[1]) if len(inputKeyParts) > 2 else 0
            , 2
        )

        transcriptionJob = {
            "TranscriptionJobName": jobName,
            "OutputKey": outputKey,
            "LanguageCode" : 'en-US',
            "MediaFormat": 'mp3',
            "Media": {
                'MediaFileUri': s3Path
            },
            "OutputBucketName": outputBucketName,
            "Settings": {
                "ShowSpeakerLabels": True,
                "MaxSpeakerLabels": maxSpeakerLabels
            }
        }
        print(f"Starting transcription job:\n{transcriptionJob}" )
    except Exception as error:
        print(f"Exception processing transcription parameters...\n{traceback.format_exc()}")
        return None

    return transcriptionJob

def lambda_handler(event, context):
    transcriptionJob = getTranscriptionJobArgs(event)

    if not transcriptionJob:
        return

    if '-dev-' in transcriptionJob["OutputBucketName"]:
        print('Not starting transcription job in dev')
        return

    try:
        client = boto3.client('transcribe')
        response = client.start_transcription_job(**transcriptionJob)
        result = {
            'TranscriptionJobName': response['TranscriptionJob']['TranscriptionJobName']
        }
    except Exception as error:
        print(f"Exception starting transcription job: config ({type(error).__name__}): {error}")
        return

    return result
