import os
import re
from datetime import datetime
from abc import ABC, abstractmethod
import urllib3
import yaml
import xml.etree.ElementTree as et # See https://docs.python.org/3/library/xml.etree.elementtree.html

class Fetcher(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def fetch(self, source):
        pass

    def HttpDownload(self, url, path):
        chunk_size = 1024 * 1024

        http = urllib3.PoolManager()
        r = http.request('GET', url, preload_content=False)
        success = r.status == 200
        if success:
            print('Downloading from ' + url + ' to ' + path)
            with open(path, 'wb') as out:
                while True:
                    data = r.read(chunk_size)
                    if not data:
                        break
                    out.write(data)
            r.release_conn()
        else:
            print('HTTP request status ' + str(r.status) + ' from url ' + url)

        return success

    # See regex docs
    # https://docs.python.org/3/library/re.html#re.Match.group
    # https://docs.python.org/3/library/re.html#re.sub
    # PyYaml
    # https://pyyaml.org/wiki/PyYAMLDocumentation

    # Return a list of speaker names, extracted from the title
    def getSpeakers(self, title):
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

    def TrimShownotes(self, shownotes):
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

    def TrimShownotesHtml(self, shownotes):
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

    def MakeSummary(self, summary):
        # Don't use 'RECORDED ON' as the summary
        summary = re.sub(r"^RECORDED ON.*\n", '', summary)
        # Extract the first line
        summary = re.sub(r"\n.*$", '', summary, flags=re.DOTALL)
        # Remove HTML tags
        summary = re.sub(r"<[^>]+>", '', summary, flags=re.DOTALL)
        return summary

    def TestMakeEpisodeId(self, title, published, expected):
        id = self.MakeEpisodeId(title, published)
        if not id == expected:
            print('ERROR', id, ' for ', title)
        else:
            print('OK', id, ' for ', title)

    def GetEpisodeNo(self, title):
        # TODO - max digits?
        if title.startswith('#482 Lauren Brent'):
            return 483
        if title.startswith('731 '):
            return 731
        if title.startswith('744 '):
            return 744
            
        match = re.search(r'^#([0-9]+)', title)
        return int(match.group(1)) if match else 0

    def MakeEpisodeId(self, episodeNo):
        return str(episodeNo)

    # Replace youtube's randomly allocated load-balancing subdomains with the master
    # to avoid the field's values changing and being updated.
    # Replace rss feed's hqdefault.jpg with maxresdefault.jpg
    # e.g.
    # https://i9.ytimg.com/vi/dzbIk_j9tkKg/hqdefault.jpg
    # ...with...
    # https://i.ytimg.com/vi/dzbIk_j9tkKg/maxresdefault.jpg
    def NormaliseImageUrl(self, url):
        url = re.sub(r'^(https://i)[0-9]+(\.ytimg\.com/)', r'\1\2', url)
        url = re.sub(r'^(https://i.ytimg.com/vi/[^/]+)/hqdefault\.jpg$', r'\1/maxresdefault.jpg', url)
        return url

    # episode is a dictionary containing values to be stored in the data file
    # The dictionary must include id
    # If isMaster is true then new files are created, otherwise they are only updated
    # Returns True if it's a new episode, indicating that the import process should continue
    def UpdateEpisodeDatafile(self, episode, isMaster = False):
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
        if episodeExists:
            with open(dataPath, 'r', encoding='utf-8') as file:
                dataDict = yaml.safe_load(file)
                file.close()
            # Merge so episode overwrites dataDict
            episode = dataDict | episode
            episodeChanged = episode != dataDict
            if episodeChanged:
                msg = 'Updating'
            else:
                msg = 'No changes to'
                #msg = None
        else:
            if isMaster:
                dataDict = {}
                msg = 'Creating'
                os.makedirs(dataDir)
            else:
                msg = 'Missing'

        if msg: print(msg + ' '  + dataPath)
        if (episodeExists and episodeChanged) or (not episodeExists and isMaster):
            # Data has changed, so update the data file
            #DumpEpisode(episode, msg, source)
            with open(dataPath, 'w', encoding='utf-8') as file:
                yaml.dump(episode, file)
                file.close()

        return not episodeExists or episodeChanged

    # Given a title/description, create a URL friendly file name (i.e. no need to %encode)
    def NormaliseFilename(self, strTitle):
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
    def NormaliseDateFormat(self, strDate):
        dmyDateFormat = '%d %b %Y'
        #hugoDateFormat = '%Y-%m-%dT%H:%M:%SZ'
        normalisedDateFormat = '%Y-%m-%d'

        # Remove day-of-the-week from the start
        strDate = re.sub('^[A-Za-z]+, *', '', strDate)
        # Remove timezone from the end
        strDate = re.sub(' *[A-Z]+$', '', strDate)
        # Remove time from the end
        strDate = re.sub(' *[0-9][0-9]:[0-9][0-9]:[0-9][0-9]$', '', strDate)

        dateDate = datetime.strptime(strDate, dmyDateFormat)
        return dateDate.strftime(normalisedDateFormat)
