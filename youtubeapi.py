import os
import json
from urllib.parse import urlparse, parse_qs

# https://pypi.org/project/google-api-python-client/
# https://github.com/googleapis/google-api-python-client/blob/main/docs/README.md
from googleapiclient.discovery import build, Resource

def getTestPath(url, testPath, testSet, params):
    urlParts = urlparse(url)
    queryParts = parse_qs(urlParts.query)
    call = os.path.basename(urlParts.path)
    path = os.path.abspath( os.path.join(testPath, testSet, call) )
    filename = ''
    for param in params:
        filename += (''.join(queryParts[param])[:34] if param in queryParts else '-') + '.'
    if not os.path.exists(path):
        os.makedirs(path)
    return os.path.join(path, filename + 'json')

class YouTubeAPI():
    def __init__(self, config):
        self.config = config
        apiKey = os.environ['GOOGLE_API_KEY']
        self.youtube = build('youtube', 'v3', developerKey=apiKey)

    def execute(self, request, params):
        if 'test' in self.config:
            # Test data is being loaded or saved - The path is needed in both cases
            path = getTestPath(request.uri, self.config["test-path"], 'youtube', params)
            if self.config['test'] == 'load':
                # Loading test data
                if os.path.exists(path):
                    # Load test data from file
                    with open(path, mode='r', encoding='utf-8') as file:
                        response = json.load(file)
                else:
                    # If the file doesn't exist, assume the result is empty
                    response = {
                        "kind": "youtube#testNotFoundResponse",
                        "etag": "testNotFoundEtag",
                        "items": [],
                        "pageInfo": {
                            "totalResults": 0,
                            "resultsPerPage": 50
                        }
                    }
            else:
                # Loading real data that will be saved later as test data
                response = request.execute()

            if self.config['test'] == 'save':
                if response['pageInfo']['totalResults']:
                    with open(path, mode='w', encoding='utf-8') as file:
                        json.dump(response, file, indent='\t')
                elif os.path.exists(path):
                    os.unlink(path)
            return response
        else:
            return request.execute()
