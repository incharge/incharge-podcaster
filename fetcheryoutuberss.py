import xml.etree.ElementTree as et # See https://docs.python.org/3/library/xml.etree.elementtree.html

from fetcher import Fetcher

class FetcherPlugin(Fetcher):
    def __init__(self, config):
        Fetcher.__init__(self, config) 

    def fetch(self, source):
        print("Download from Youtube RSS " + source['url'])

        if self.HttpDownload(source['url'], 'youtuberss.xml'):
            tree = et.parse('youtuberss.xml')
            root = tree.getroot()
            mediaNamespace = '{http://search.yahoo.com/mrss/}'
            youtubeNamespace = '{http://www.youtube.com/xml/schemas/2015}'
            defaultNamespace = '{http://www.w3.org/2005/Atom}'

            print("Extracting episodes from YouTube feed")
            for item in root.iter(defaultNamespace + 'entry'):

                title = item.find(defaultNamespace + 'title').text.strip()
                episodeNo = self.GetEpisodeNo(title)
                if episodeNo != 0:
                    episode = {}
                    episode['id'] = self.MakeEpisodeId(episodeNo)
                    episode['title'] = title

                    # 2012-09-10T15:39:02+00:00
                    publishedDate = item.find(defaultNamespace + 'published').text
                    #episode['youtubepublished'] = publishedDate
                    publishedDate = publishedDate[0:10]
                    episode['published'] = publishedDate

                    mediaGroup = item.find(mediaNamespace + 'group')
                    episode['shownotes'] = self.TrimShownotes(mediaGroup.find(mediaNamespace + 'description').text)

                    episode['filename'] = self.NormaliseFilename(title)
                    episode['excerpt'] = self.MakeSummary(episode['shownotes'])

                    episode['youtubeid'] = item.find(youtubeNamespace + 'videoId').text
                    episode['image'] = self.NormaliseImageUrl(mediaGroup.find(mediaNamespace + 'thumbnail').attrib['url'])

                    episode['interviewee'] = self.getSpeakers(title)
                    #intervieweeFirst = []
                    #for interviewee in intervieweeFull:
                    #    intervieweeFirst.append(interviewee.split()[0])
                    #episode['interviewee-first'] = intervieweeFirst

                    if not self.UpdateEpisodeDatafile(episode, True):
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