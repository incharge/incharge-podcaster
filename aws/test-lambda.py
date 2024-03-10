import unittest
import copy
from AwsLambdaTranscribe import *

# Invalid event
eventErrorInvalidEvent = None

# Invalid parameters - key is numeric
eventErrorInvalidKey = {
    "Records": [
        {
            "s3" : {
                "bucket": {
                    "name": "incharge-dev"
                },
                "object": {
                    "key": 0
                }                    
            }
        }
    ]
}

# file has an invalid speaker number
eventErrorInvalidSpeakers = {
    "Records": [
        {
            "s3" : {
                "bucket": {
                    "name": "incharge-dev"
                },
                "object": {
                    "key": "episode/123.invalid-speakers.m4a"
                }                    
            }
        }
    ]
}

# Success: typical
eventSuccessTypical = {
    "Records": [
        {
            "s3" : {
                "bucket": {
                    "name": "incharge-dev"
                },
                "object": {
                    "key": "episode/123.4.m4a"
                }                    
            }
        }
    ]
}

jobSuccessTypical = {
    "Media": {
        "MediaFileUri": "s3://incharge-dev/episode/123.4.m4a"
    },
    "OutputBucketName": "incharge-dev",
    "OutputKey": "transcript/123.json",
    "TranscriptionJobName": "123.json",
    "Settings": {
        "ShowSpeakerLabels": True,
        "MaxSpeakerLabels": 4
    },
    "LanguageCode": "en-US",
    "MediaFormat": "mp3"
}

# Success: file has no speaker number
eventSuccessNoSpeakers = {
    "Records": [
        {
            "s3" : {
                "bucket": {
                    "name": "incharge-dev"
                },
                "object": {
                    "key": "episode/123.m4a",
                }                    
            }
        }
    ]
}
#jobSuccessNoSpeakers = dict(jobSuccessTypical)
#jobSuccessNoSpeakers["Settings"]["MaxSpeakerLabels"] = 2

# OK file has no extension
eventSuccessNoExtension = {
    "Records": [
        {
            "s3" : {
                "bucket": {
                    "name": "incharge-dev"
                },
                "object": {
                    "key": "episode/123"
                }                    
            }
        }
    ]
}


# OK file has no prefix
eventSuccessNoPrefix = {
    "Records": [
        {
            "s3" : {
                "bucket": {
                    "name": "incharge-dev"
                },
                "object": {
                    "key": "123.2.m4a"
                }                    
            }
        }
    ]
}

eventSuccessInchargePodcaster2s = {
  "Records": [
    {
      "s3": {
        "bucket": {
          "name": "thedissenter-dev"
        },
        "object": {
          "key": "episode/test-incharge-podcaster-2s-mono-24000-med.mp3"
        }
      }
    }
  ]
}

# Live test
eventLiveSuccessInchargePodcaster2s = {
    "Records": [
        {
            "s3" : {
                "bucket": {
                    "name": "thedissenter-dev"
                },
                "object": {
                    "key": "episode/test-incharge-podcaster-2s-mono-24000-med.mp3"
                }                    
            }
        }
    ]
}

# event = eventErrorInvalidEvent
# event = eventErrorInvalidKey
# event = eventErrorInvalidSpeakers

#event = eventSuccessNoSpeakers
#event = eventSuccessNoExtension

# Live
#event = eventLiveErrorInvalidURI
#event = eventLiveSuccessInchargePodcaster2s

def RemoveTranscriptionRandoms(job):
    if 'TranscriptionJobName' in job:
        job['TranscriptionJobName'] = re.sub(r"-.*", '', job['TranscriptionJobName'])
    return job

class TestRemovePrefix(unittest.TestCase):

    def testRemovePrefix(self):
        #self.assertEqual(removePrefix(None), None)
        self.assertEqual(removePrefix("key"), "key")
        self.assertEqual(removePrefix("prefix/key"), "key")
        self.assertEqual(removePrefix("prefix1/prefix2/key"), "key")

    def testRemoveSuffix(self):
        self.assertEqual(removeSuffix("key"), "key")
        self.assertEqual(removeSuffix("key."), "key")
        self.assertEqual(removeSuffix("key.json"), "key")
        self.assertEqual(removeSuffix("key.m4a"), "key")
        self.assertEqual(removeSuffix("key.4.json"), "key")

    def testGetTranscriptionJobArgs(self):
        self.assertEqual(getTranscriptionJobArgs(eventErrorInvalidEvent), None)
        self.assertEqual(getTranscriptionJobArgs(eventErrorInvalidKey), None)
        self.assertEqual(getTranscriptionJobArgs(eventErrorInvalidSpeakers), None)

        self.maxDiff = 1024
        self.assertEqual(getTranscriptionJobArgs(eventSuccessTypical, True), jobSuccessTypical)
        self.assertNotEqual(getTranscriptionJobArgs(eventSuccessTypical, False), jobSuccessTypical)

        job = copy.deepcopy(jobSuccessTypical)
        job["Settings"]["MaxSpeakerLabels"] = 2
        job["Media"]["MediaFileUri"] = 's3://incharge-dev/episode/123.m4a'
        self.assertEqual(getTranscriptionJobArgs(eventSuccessNoSpeakers, True), job)
        job["Media"]["MediaFileUri"] = 's3://incharge-dev/episode/123'
        self.assertEqual(getTranscriptionJobArgs(eventSuccessNoExtension, True), job)
        job["Media"]["MediaFileUri"] = 's3://incharge-dev/123.2.m4a'
        self.assertEqual(getTranscriptionJobArgs(eventSuccessNoPrefix, True), job)

class TestGetTranscriptionJobArgs(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()

    #print( getTranscriptionJobArgs(eventSuccessInchargePodcaster2s) )
