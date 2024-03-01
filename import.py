import argparse
import sys
import xml.etree.ElementTree as et # See https://docs.python.org/3/library/xml.etree.elementtree.html
import datetime
import re
import yaml
import os
import urllib.request
import boto3
import json

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def DownloadRss(url, path):
    print('Downloading ' + url)
    urllib.request.urlretrieve(url, path)

# See regex docs
# https://docs.python.org/3/library/re.html#re.Match.group
# https://docs.python.org/3/library/re.html#re.sub
# PyYaml
# https://pyyaml.org/wiki/PyYAMLDocumentation

# Return a list of speaker names, extracted from the title
def getSpeakers(title):
	# Remove the episode ID from the start of the title
	title = re.sub(r'^#[0-9]+ ', '', title)

	# Get up to the first space-hyphen-space, if it comes before a colon.
	# The spaces around the hyphen avoid matching hyphens in names.
	# Note: the ? makes the + lazy instead of the usual greedy,
	# because we want it to match as little as possible so we get the first occurrence of space-hyphen-space
	result, count = re.subn(r'^([^:]+?) - .*$',
			r'\1',
			title)

	if count == 0:
		# Get up to the first colon
		result, count = re.subn(r'^([^:]+):.*$',
				r'\1',
				title)

	# TODO: if count == 0: warn no delimiter was found to separate speakers from the title

	speakers = re.split(r' *[,&] *', result)
	#for speaker in speakers: speaker = speaker.split()[0]

	return speakers

def TrimShownotes(shownotes):
    # Remove 'Support the channel'
    # 426+
    shownotes = re.sub(r"------------------Support the channel------------.*enlites\.com/\n", '', shownotes, flags=re.DOTALL)
    # Up to 167-391
    shownotes = re.sub(r"------------------Support the channel------------.*anchor\.fm/thedissenter\n", '', shownotes, flags=re.DOTALL)
    # 1-145, 392-425
    shownotes = re.sub(r"------------------Support the channel------------.*twitter\.com/TheDissenterYT\n", '', shownotes, flags=re.DOTALL)

    # Remove whitespace from the start
    shownotes = re.sub(r'^[\n]*', '', shownotes)

    # Remove credits from the end
    shownotes = re.sub(r'[-]*\nA HUGE THANK YOU.*$', '', shownotes, flags=re.DOTALL)

    # Horizontal rules
    shownotes = re.sub(r'\n *-[-]+ *\n', '\n\n---\n\n', shownotes)

    # Add 2 spaces before single lime breaks, so they don't wrap
    shownotes = re.sub(r'([^\n])\n([^\n])', r'\1  \n\2', shownotes)

    # print('Trimmed shownotes: ', shownotes)
    return shownotes

def TrimShownotesHtml(shownotes):
    # Remove 'Support the channel'
    # 426+
    shownotes = re.sub(r"<p>------------------Support the channel------------</p>.*enlites\.com/</a></p>\n", '', shownotes, flags=re.DOTALL)
    # Up to 167-391
    shownotes = re.sub(r"<p>------------------Support the channel------------</p>.*anchor\.fm/thedissenter</a></p>\n", '', shownotes, flags=re.DOTALL)
    # 1-145, 392-425
    shownotes = re.sub(r"<p>------------------Support the channel------------</p>.*twitter\.com/TheDissenterYT</a></p>\n", '', shownotes, flags=re.DOTALL)

    # Remove blank lines from the start
    # \xA0 is utf-8 non-breaking-space
    shownotes = re.sub(r"^<p>[ -\xA0]*</p>\n", '', shownotes)
    shownotes = re.sub(r"^<p><br></p>\n", '', shownotes)
    shownotes = re.sub(r"^\n", '', shownotes)

    # Remove credits from the end
    shownotes = re.sub(r'<p><a href="">A HUGE THANK YOU.*$', '', shownotes, flags=re.DOTALL)
    shownotes = re.sub(r'<p>A HUGE THANK YOU.*$', '', shownotes, flags=re.DOTALL)

    # Remove blank lines from the end
    shownotes = re.sub(r'<p>[ -]*</p>\n$', '', shownotes, flags=re.DOTALL)
    # Why doesn't this work? e.g. episode 457
    shownotes = re.sub(r'\n\n$', '\n', shownotes)

    # print('Trimmed shownotes: ', shownotes)
    return shownotes

def MakeSummary(summary):
    # Don't use 'RECORDED ON' as the summary
    summary = re.sub(r"^RECORDED ON.*\n", '', summary)
    # Extract the first line
    summary = re.sub(r"\n.*$", '', summary, flags=re.DOTALL)
    # Remove HTML tags
    summary = re.sub(r"<[^>]+>", '', summary, flags=re.DOTALL)
    return summary

def TestMakeEpisodeId(title, published, expected):
    id = MakeEpisodeId(title, published)
    if not id == expected:
        print('ERROR', id, ' for ', title)
    else:
        print('OK', id, ' for ', title)

def GetEpisodeNo(title):
    # TODO - max digits?
    if title.startswith('#482 Lauren Brent'):
        return 483
    if title.startswith('731 '):
        return 731
    if title.startswith('744 '):
        return 744
        
    match = re.search(r'^#([0-9]+)', title)
    return int(match.group(1)) if match else 0

def MakeEpisodeId(episodeNo):
    return str(episodeNo)

# Replace youtube's randomly allocated load-balancing subdomains with the master
# to avoid the field's values changing and being updated.
# Replace rss feed's hqdefault.jpg with maxresdefault.jpg
# e.g.
# https://i9.ytimg.com/vi/dzbIk_j9tkKg/hqdefault.jpg
# ...with...
# https://i.ytimg.com/vi/dzbIk_j9tkKg/maxresdefault.jpg
def NormaliseImageUrl(url):
    url = re.sub(r'^(https://i)[0-9]+(\.ytimg\.com/)', r'\1\2', url)
    url = re.sub(r'^(https://i.ytimg.com/vi/[^/]+)/hqdefault\.jpg$', r'\1/maxresdefault.jpg', url)
    return url

# Create an ID that uniquely identifies this episode across rss feeds from multiple platforms
# Note: Hugo doesn't allow purly numeric data file names
# def MakeEpisodeId(title, published):
#     # Start with published date
#     id = 'd' + published

#     # Add episode number
#     match = re.search(r'^#([0-9]+)', title)
#     if ( match ):
#         id = id + '-e' + match.group(1)
#     else:
#         # Add part number
#         match = re.search(r'Part ([0-9]+)', title)
#         if match:
#             id = id + '-pt' + match.group(1)

#     return id

# episode is a dictionary containing values to be stored in the data file
# The dictionary must include id
# If isMaster is true then new files are created, otherwise they are only updated
# Returns True if it's a new episode, indicating that the import process should continue
def UpdateEpisodeDatafile(episode, isMaster = False):
    # Truth table showing how inputs determine outputs
    #   -------- Inputs --------|------- Outputs ------
    #   Exists  Changed Master  |   Write   New Episode
    #   N       x       N       |   N       Y       
    #   N       x       Y       |   Y       Y
    #   Y       N       x       |   N       N
    #   Y       Y       x       |   Y       Y

    # Get the existing episode data
    dataDir = os.path.join('episode', episode['id'])
    dataPath = os.path.join(dataDir, 'episode.yaml')
    episodeExists = os.path.isfile(dataPath)
    if os.path.isfile(dataPath) :
        with open(dataPath, 'r', encoding='utf-8') as file:
            dataDict = yaml.safe_load(file)
            file.close()
        # Merge so episode overwrites dataDict
        episode = dataDict | episode
        episodeCanged = episode != dataDict
        if episodeCanged:
            msg = 'Updating'
        else:
            msg = 'No changes to'
    else:
        if isMaster:
            dataDict = {}
            msg = 'Creating'
            os.makedirs(dataDir)
        else:
            msg = 'Missing'

    print(msg + ' '  + dataPath)
    if (episodeExists and episodeCanged) or (not episodeExists and isMaster):
        # Data has changed, so update the data file
        #DumpEpisode(episode, msg, source)
        with open(dataPath, 'w', encoding='utf-8') as file:
            yaml.dump(episode, file)
            file.close()

    return not episodeExists or episodeCanged

# def LoadEpisodeDatafile():
#     with open('C:\\Users\\Julian\\Documents\\hugo\\site\\test01\\data\\episode\\e848.yaml', 'r') as file:
#     #with open('e848.yaml', mode="r", encoding="utf-8") as file:
#         print("ha")
#         episodeData = yaml.safe_load(file)
#         print(type(episodeData))
#         for episode in episodeData:
#             print(type(episode))
#             print(episode)
#             print(episodeData[episode])

# Given a title/description, create a URL friendly file name (i.e. no need to %encode)
def NormaliseFilename(strTitle):
    # Remove non-ascii characters
    # Not neccesary as they are removed as special characters below
    #strTitle = re.sub('[^\x00-\x7F]', '', strTitle)

    # Convert punctuation to spaces
    strTitle = re.sub('[!,.?]', ' ', strTitle)
    # Remove special characters
    strTitle = re.sub('[^A-Za-z0-9- ]', '', strTitle)

    # Remove spaces from the start and end
    strTitle = strTitle.strip()
    # Convert spaces to hyphens
    strTitle = re.sub(' ', '-', strTitle)
    return strTitle

# def DumpEpisode(episode, msg, source):
#     episodeNo = GetEpisodeNo(episode['title'])
#     #+ episode['title']
#     print(str(episodeNo) + '\t'  + episode['published'] + '\t' + episode['filename'] + '\t' + msg + '\t' + source)


# https://docs.python.org/3/library/time.html#time.strftime
# %a  Locale’s abbreviated weekday name.
# %b  Locale’s abbreviated month name.
# %d  Day of the month as a decimal number [01,31].
# %Y  Year with century as a decimal number.
# %m  Month as a decimal number [01,12].
# %H  Hour (24-hour clock) as a decimal number [00,23].
# %M  Minute as a decimal number [00,59].
# %S  Second as a decimal number [00,61].
# %Z deprecated

# Convert a date to the format YYYY-MM-DD
# Input is in the format:
# Mon, 16 Oct 2023 18:00:00 GMT
# Day-of-the-week, time, and timezone are optional
def NormaliseDateFormat(strDate):
    dmyDateFormat = '%d %b %Y'
    #hugoDateFormat = '%Y-%m-%dT%H:%M:%SZ'
    normalisedDateFormat = '%Y-%m-%d'

    # Remove day-of-the-week from the start
    strDate = re.sub('^[A-Za-z]+, *', '', strDate)
    # Remove timezone from the end
    strDate = re.sub(' *[A-Z]+$', '', strDate)
    # Remove time from the end
    strDate = re.sub(' *[0-9][0-9]:[0-9][0-9]:[0-9][0-9]$', '', strDate)

    dateDate = datetime.datetime.strptime(strDate, dmyDateFormat)
    return dateDate.strftime(normalisedDateFormat)

def ExtractSpotify(root, output):
    print("Extracting episodes from Spotify feed")
    channel = root.find('channel')
    itunesNamespace = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}
    for item in channel.iter('item'):

        title = item.find('title').text.strip()
        episodeNo = GetEpisodeNo(title)
        if episodeNo != 0:
            episode = {}
            episode['title'] = title
            episode['filename'] = NormaliseFilename(title)

            publishedDate = item.find('pubDate').text
            # episode['spotifypublished'] = publishedDate
            publishedDate = NormaliseDateFormat(publishedDate)
            episode['published'] = publishedDate

            #episode['id'] = MakeEpisodeId(title, publishedDate)
            episode['id'] = MakeEpisodeId(episodeNo)

            episode['spotifyAudioUrl'] = item.find('enclosure').attrib['url']
            episode['spotifyEpisodeUrl'] = item.find('link').text
            episode['spotifyImageUrl'] = item.find('itunes:image', itunesNamespace).attrib['href']

            # # print("guid ", item.find('guid').text)
            # # print("duration: ", item.find('itunes:duration', itunesNamespace).text)

            if not UpdateEpisodeDatafile(episode, False):
                print('Done importing from Spotify')
                break

def ExtractYoutube(root, output):
    mediaNamespace = '{http://search.yahoo.com/mrss/}'
    youtubeNamespace = '{http://www.youtube.com/xml/schemas/2015}'
    defaultNamespace = '{http://www.w3.org/2005/Atom}'

    print("Extracting episodes from YouTube feed")
    for item in root.iter(defaultNamespace + 'entry'):

        title = item.find(defaultNamespace + 'title').text.strip()
        episodeNo = GetEpisodeNo(title)
        if episodeNo != 0:
            episode = {}
            episode['id'] = MakeEpisodeId(episodeNo)
            episode['title'] = title

            # 2012-09-10T15:39:02+00:00
            publishedDate = item.find(defaultNamespace + 'published').text
            #episode['youtubepublished'] = publishedDate
            publishedDate = publishedDate[0:10]
            episode['published'] = publishedDate

            mediaGroup = item.find(mediaNamespace + 'group')
            episode['shownotes'] = TrimShownotes(mediaGroup.find(mediaNamespace + 'description').text)

            episode['filename'] = NormaliseFilename(title)
            episode['excerpt'] = MakeSummary(episode['shownotes'])

            episode['youtubeid'] = item.find(youtubeNamespace + 'videoId').text
            episode['image'] = NormaliseImageUrl(mediaGroup.find(mediaNamespace + 'thumbnail').attrib['url'])

            episode['interviewee'] = getSpeakers(title)
            #intervieweeFirst = []
            #for interviewee in intervieweeFull:
            #    intervieweeFirst.append(interviewee.split()[0])
            #episode['interviewee-first'] = intervieweeFirst

            if not UpdateEpisodeDatafile(episode, True):
                print('Done importing from YouTube feed')
                break
        # print('id=(', item.find('id').text, ')')
        # print('link=(', item.find('link').attrib['href'], ')')
        # print('updated=(', item.find('updated').text, ')')
        # mediaGroup = item.find(mediaNamespace + 'group')

        # mediaElement = mediaGroup.find(mediaNamespace + 'content')
        # print('media:content[url]=(', mediaElement.attrib['url'], ')')
        # print('media:content[width]=(', mediaElement.attrib['width'], ')')
        # print('media:content[height]=(', mediaElement.attrib['height'], ')')

        # mediaElement = mediaGroup.find(mediaNamespace + 'thumbnail')
        # print('media:thumbnail[url]=(', mediaElement.attrib['url'], ')')
        # print('media:thumbnail[width]=(', mediaElement.attrib['width'], ')')
        # print('media:thumbnail[height]=(', mediaElement.attrib['height'], ')')

# Extract the video ID from a link in the format
# https://www.youtube.com/watch?v=610dKJEbbL0
# def YoutubeLinkToId(link):
#     return re.sub(r'^.*?v=', '', link)

# def ExtractAuthory(root, output):
#     # mediaNamespace = '{http://search.yahoo.com/mrss/}'
#     #youtubeNamespace = '{http://www.youtube.com/xml/schemas/2015}'
#     #defaultNamespace = '{http://www.w3.org/2005/Atom}'

#     print("Extracting episodes from Authory feed")
#     channel = root.find('channel')
#     for item in channel.iter('item'):
#         title = item.find('title').text.strip()
#         episodeNo = GetEpisodeNo(title)
#         if episodeNo != 0: # and episodeNo > 850
#             episode = {}
#             episode['id'] = MakeEpisodeId(episodeNo)
#             episode['title'] = title

#             publishedDate = item.find('pubDate').text
#             # episode['spotifypublished'] = publishedDate
#             publishedDate = NormaliseDateFormat(publishedDate)
#             episode['published'] = publishedDate

#             #episode['shownotes'] = TrimShownotes(item.find('description').text)
#             episode['shownotes'] = TrimShownotes(item.find('description').text)

#             episode['filename'] = NormaliseFilename(title)
#             episode['summary'] = MakeSummary(episode['shownotes'])

#             episode['youtubeid'] = YoutubeLinkToId(item.find('link').text)

#             UpdateEpisodeDatafile(episode, output, 'Authory', True)

def ExtractYoutubeApi(playlistId, apiKey, output):
    youtube = build('youtube', 'v3', developerKey=apiKey)

    # Equivalent to: https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=UUTUcatGD6xu4tAcxG-1D4Bg&key=<SPI_KEY>
    playlistitems_list_request = youtube.playlistItems().list(
        playlistId = playlistId,
        part = 'snippet',
        maxResults = 50
    )

    print("Extracting episodes via YouTube API")
    #print( 'Videos in list %s' % uploads_playlist_id)
    newepisodes = True
    while newepisodes and playlistitems_list_request:
        # Fetch the next page
        playlistitems_list_response = playlistitems_list_request.execute()

        for playlist_item in playlistitems_list_response['items']:
            title = playlist_item['snippet']['title'].strip()
            episodeNo = GetEpisodeNo(title)
            if episodeNo != 0: # and episodeNo > 850:
                episode = {}
                episode['id'] = MakeEpisodeId(episodeNo)
                episode['title'] = title

                publishedDate = playlist_item['snippet']['publishedAt']
                publishedDate = publishedDate[0:10]
                episode['published'] = publishedDate

                episode['shownotes'] = TrimShownotes(playlist_item['snippet']['description'])

                episode['filename'] = NormaliseFilename(title)
                episode['excerpt'] = MakeSummary(episode['shownotes'])

                episode['youtubeid'] = playlist_item['snippet']['resourceId']['videoId']
                episode['image'] = NormaliseImageUrl(playlist_item['snippet']['thumbnails']['maxres']['url'])

                episode['interviewee'] = getSpeakers(title)

                newepisodes = UpdateEpisodeDatafile(episode, True)
                if not newepisodes:
                    print('Done importing from YouTube API')
                    break

        # if episodeNo < 850:
        #     return
        # else:

        # Set up the query for the next page
        playlistitems_list_request = youtube.playlistItems().list_next(
            playlistitems_list_request, playlistitems_list_response)


def getEpisodeID(filename):
    filename = os.path.basename(filename)
    return re.sub("\.[^.]*", "", filename)

# Download transcript files from S3
def DownloadTranscript(config):
    client = boto3.client('s3')
    response = client.list_objects_v2(Bucket=config['transcript-bucket'])

    for o in response['Contents']:
        filename = o["Key"]
        episodeID = getEpisodeID(filename)
        if filename.endswith(".json") and episodeID is not None:
            filepath = os.path.join('episode', episodeID)
            if not os.path.isdir(filepath):
                os.makedirs(filepath)
            filepath = os.path.join(filepath, 'transcript.json')
            print('Getting transcript for episode ' + episodeID + ' from ' + filename + ' to ' + filepath)
            client.download_file(config['transcript-bucket'], filename, filepath)

# def DumpYoutube0(root):
#     for entry in root:
#         print('tag=(', entry.tag, '), text=(', entry.text, ')')
#         print('published=(', entry.find('published'), ')')
#         for item in entry.iter():
#             print('child tag=(', item.tag, '), text=(', item.text, ')')
#             if item.text == 'B#862 Lisa Bortolotti: Why Delusions Matter':
#                 print("Ha!")
#                 print('1:', item.tag[0])
#                 print('2:', item.tag[2])
#                 print('3:', item.tag[3])
#                 print('4:', item.tag[4])
#                 return

# def DumpYoutube(root):
#     mediaNamespace = {'media': 'http://search.yahoo.com/mrss/'}
#     for item in root.iter('entry'):
#         print('entry=(', item.tag, '), text=(', item.text, ')')
#         for subitem in root:
#             print('tag=(', subitem.tag, '), text=(', subitem.text, ')')

# Test NormaliseImageUrl
# print(NormaliseImageUrl("https://nochange/hqdefault.jpg"))
# print(NormaliseImageUrl("https://i.ytimg.com/vi/dzbIk_j9tkKg/hqdefault.jpg"))
# print(NormaliseImageUrl("https://i9.ytimg.com/vi/dzbIk_j9tkKg/maxresdefault.jpg"))
# sys.exit()

configfile = open('incharge-podcaster.json', mode='r', encoding='utf-8')
config = json.load(configfile)
configfile.close

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--spotify')
parser.add_argument('--youtubeapi')     # The ID of the Upload playlist
parser.add_argument('-y', '--youtuberss')
parser.add_argument('-o', '--output')
parser.add_argument('-a', '--authory')
args = parser.parse_args()

if args.youtubeapi is not None:
    if not 'GOOGLE_API_KEY' in os.environ:
        print("ERROR: Define environment variable: GOOGLE_API_KEY")
        sys.exit(1)
    ExtractYoutubeApi(args.youtubeapi, os.environ['GOOGLE_API_KEY'], args.output)

# if args.authory is not None:
#     #DownloadRss(args.authory, 'authory.xml')
#     tree = et.parse('authory.xml')
#     root = tree.getroot()
#     ExtractAuthory(root, args.output)

if args.youtuberss is not None:
    DownloadRss(args.youtuberss, 'youtuberss.xml')
    tree = et.parse('youtuberss.xml')
    root = tree.getroot()
    ExtractYoutube(root, args.output)

if args.spotify is not None:
    DownloadRss(args.spotify, 'spotify.xml')
    tree = et.parse('spotify.xml')
    root = tree.getroot()
    ExtractSpotify(root, args.output)

DownloadTranscript(config)

# DumpYoutube0(root)

# Test UpdateEpisodeDatafile
# episodeDict = {
#     'id': 'e100',
#     'excellence': 'yes',
#     'crap': 'no',
# }
# UpdateEpisodeDatafile(episodeDict)

# TestMakeEpisodeId('#1 whatever', '2001-01-01', '1')
# TestMakeEpisodeId('#12 whatever', '2001-01-01', '12')
# TestMakeEpisodeId('#123 whatever', '2001-01-01', '123')
# TestMakeEpisodeId('Whatever', '2001-01-01', '2001-01-01')
# TestMakeEpisodeId('Episode 1', '2001-01-01', '2001-01-01')
# TestMakeEpisodeId('4 years', '2001-01-01', '2001-01-01')

# print( NormaliseDateFormat('Mon, 16 Oct 2023 18:00:00 GMT') )
# print( NormaliseFilename('#862 Lisa Bortolotti: Why Delusions Matter') )
