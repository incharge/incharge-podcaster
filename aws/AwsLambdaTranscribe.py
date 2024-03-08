import boto3
import uuid
import json
import re

def lambda_handler(event, context):

    record = event['Records'][0]
    
    s3bucket = record['s3']['bucket']['name']
    s3object = record['s3']['object']['key']
    
    s3Path = "s3://" + s3bucket + "/" + s3object
    jobName = s3object + '-' + str(uuid.uuid4())

    client = boto3.client('transcribe')
    response = client.start_transcription_job(
        TranscriptionJobName=jobName,
        OutputKey=re.sub(r"\.[^.]*$", ".json", s3object),
        LanguageCode='en-US',
        MediaFormat='mp3',
        Media={
            'MediaFileUri': s3Path
        },
        OutputBucketName = "thedissenter-transcript",
    	Settings={
    		"ShowSpeakerLabels": True,
    		"MaxSpeakerLabels": 2
    	},
    )


    return {
        'TranscriptionJobName': response['TranscriptionJob']['TranscriptionJobName']
    }
