import yaml
import os
import argparse
import datetime
import sys
import json
from transcripttotext import transcriptToText

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def CreatePage(input, output, config):
    # Get the episode data
    with open(input, 'r', encoding='utf-8') as file:
        dataDict = yaml.safe_load(file)
        file.close()

    # Select the fields to be written to the FrontMatter section
    episodeDict = {
        'title': dataDict['title'],
        'id': dataDict['id'],
        'publishDate': datetime.datetime.strptime(dataDict['published'], "%Y-%m-%d").date(),
        'excerpt': dataDict['excerpt'],
        'youtubeid': dataDict['youtubeid'],
        'image': dataDict['image'],
        'draft': False,        
    }

    # Write the file
    pagesPath = os.path.join(output, dataDict['filename'] + '.md')
    print('Writing ' + pagesPath)
    with open(pagesPath, 'w', encoding='utf-8') as file:
        file.write('---\n')
        yaml.dump(episodeDict, file)
        file.write('---\n')

        transcriptPath = os.path.join('episode', dataDict['id'], 'transcript.json')
        if (not os.path.exists(transcriptPath) ):
            file.write(dataDict['shownotes'])
        else:
            file.write('<a name="top"></a>[Jump to transcript](#transcript)\n')
            file.write('## Show notes\n')
            file.write(dataDict['shownotes'])
            file.write('\n')
            file.write('[Back to top](#top)\n')
            file.write('<a name="transcript"></a>\n')
            file.write('## Transcript\n')
            transcriptToText(transcriptPath, dataDict, config, file)
            file.write('[Back to top](#top)\n')

def CreatePages(input, output, config):
    with os.scandir(input) as episodes:
        for episode in episodes:
            path = os.path.join(input, episode.name, 'episode.yaml')
            # os.episode.name.endswith('.yaml')
            if os.path.exists(path):
                CreatePage(path, output, config)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input')
    parser.add_argument('-o', '--output')
    args = parser.parse_args()

    configfile = open('incharge-podcaster.json', mode='r', encoding='utf-8')
    config = json.load(configfile)
    configfile.close

    CreatePages(args.input, args.output, config)
