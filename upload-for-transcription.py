# python incharge-podcaster/upload-for-transcription.py
import urllib3
import logging
import boto3
from botocore.exceptions import ClientError
import os

def download_file(url, path):
    print('Downloading ' + url + ' to ' + path)
    chunk_size = 1024 * 1024

    http = urllib3.PoolManager()
    r = http.request('GET', url, preload_content=False)

    with open(path, 'wb') as out:
        while True:
            data = r.read(chunk_size)
            if not data:
                break
            out.write(data)

    r.release_conn()


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    print('Uploading ' + file_name + ' to S3:' + bucket)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


filename = '516.m4a'
url = 'https://anchor.fm/s/822ba20/podcast/play/38730559/https%3A%2F%2Fd3ctxlq1ktw2nl.cloudfront.net%2Fstaging%2F2021-7-13%2Fbfa0c886-bad2-996c-7c50-f058142b63bc.m4a'

path = os.path.join('temp', filename)
download_file(url, path)
upload_file(path, 'thedissenter-episode', filename)

