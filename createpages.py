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

    # Does the page need to be created or updated?
    pagesPath = os.path.join(output, dataDict['filename'] + '.md')
    pageExists = os.path.exists(pagesPath)
    if pageExists:
        dataModified = os.path.getmtime(input)
        pageModified = os.path.getmtime(pagesPath)
        if dataModified > pageModified:
            writePage = 1
        else:
            writePage = 0
    else:
        writePage = -1

    if writePage:
        print(('Creating' if writePage < 0 else 'Updating') + ' ' + pagesPath)
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

    return writePage

def CreatePages(input, output, config):
    createdCount = 0
    updatedCount = 0

    input = os.path.abspath(input)
    output = os.path.abspath(output)

    print('Generating pages from ' + input + ' to ' + output)
    with os.scandir(input) as episodes:
        for episode in episodes:
            path = os.path.join(input, episode.name, 'episode.yaml')
            # os.episode.name.endswith('.yaml')
            if os.path.exists(path):
                writePage = CreatePage(path, output, config)
                if writePage < 0:
                    createdCount += 1
                elif writePage > 0:
                    updatedCount += 1
                # else: Unchanged
            else:
                print('WARNING: Missing episode file ' + path)
    if createdCount > 0:
        print(str(createdCount) + ' pages created' )
    if updatedCount > 0:
        print(str(createdCount) + ' pages updated' )
    if createdCount == 0 and updatedCount == 0:
        print('No pages needed to be created or updated' )

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input')
    parser.add_argument('-o', '--output')
    args = parser.parse_args()

    configfile = open('incharge-podcaster.json', mode='r', encoding='utf-8')
    config = json.load(configfile)
    configfile.close

    CreatePages(args.input, args.output, config)
