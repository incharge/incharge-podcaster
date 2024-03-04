import yaml
import os
import argparse
import datetime
import sys
import json
from transcripttotext import transcriptToText

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def GeneratePage(episodepath, config):
    # Get the episode data
    with open(episodepath, 'r', encoding='utf-8') as file:
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
    pagepath = os.path.join(config['page-folder'], dataDict['filename'] + '.md')
    if os.path.exists(pagepath):
        dataModified = os.path.getmtime(episodepath)
        pageModified = os.path.getmtime(pagepath)
        if dataModified > pageModified:
            writePage = 1
        else:
            writePage = 0
    else:
        writePage = -1

    if writePage:
        print(('Creating' if writePage < 0 else 'Updating') + ' ' + pagepath)
        with open(pagepath, 'w', encoding='utf-8') as file:
            file.write('---\n')
            yaml.dump(episodeDict, file)
            file.write('---\n')

            transcriptPath = os.path.join(config['episode-folder'], dataDict['id'], 'transcript.json')
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

def GeneratePages(config):
    createdCount = 0
    updatedCount = 0

    print(f"Generating pages from {config['episode-folder']} to {config['page-folder']}")
    with os.scandir(config['episode-folder']) as episodes:
        for episode in episodes:
            episodepath = os.path.join(config['episode-folder'], episode.name, 'episode.yaml')
            # os.episode.name.endswith('.yaml')
            if os.path.exists(episodepath):
                writePage = GeneratePage(episodepath, config)
                if writePage < 0:
                    createdCount += 1
                elif writePage > 0:
                    updatedCount += 1
                # else: Unchanged
            else:
                print(f"WARNING: Missing episode file {episodepath}")
    if createdCount > 0:
        print(str(createdCount) + ' pages created' )
    if updatedCount > 0:
        print(str(createdCount) + ' pages updated' )
    if createdCount == 0 and updatedCount == 0:
        print('No pages needed to be created or updated' )

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', '--ignore')
    args = parser.parse_args()

    configfile = open('incharge-podcaster.json', mode='r', encoding='utf-8')
    config = json.load(configfile)
    configfile.close

    # Assign defaults if no folder settings are provided and convert relative to absolute paths
    config['episode-folder'] = os.path.abspath(
        config['episode-folder'] if 'episode-folder' in config else 'episode'
    )
    config['page-folder'] = os.path.abspath(
        config['page-folder'] if 'page-folder' in config else 'page'
    )

    GeneratePages(config)
