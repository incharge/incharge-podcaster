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

    # Does the page need to be created or updated?
    pagepath = os.path.join(config['page-folder'], dataDict['filename'] + '.md')
    transcriptPath = os.path.join(config['episode-folder'], dataDict['id'], 'transcript.json')
    if os.path.exists(pagepath):
        # The page exists. Does it need to be updated?
        pageModified = os.path.getmtime(pagepath)
        # If either the episode data or transcript data has changed?
        dataModified = max(
            os.path.getmtime(transcriptPath) if os.path.exists(transcriptPath) else 0,
            os.path.getmtime(episodepath)
        )
        if dataModified > pageModified:
            writePage = 1   # The episode data has changed, so the page needs to be updated
        else:
            writePage = 0   # The episode data has not changed
    else:
        writePage = -1      # The episode data is new, so the page needs to be created

    if writePage:
        print(('Creating' if writePage < 0 else 'Updating') + ' ' + pagepath)

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

        with open(pagepath, 'w', encoding='utf-8') as file:
            file.write('---\n')
            yaml.dump(episodeDict, file)
            file.write('---\n')

            if not os.path.exists(transcriptPath):
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
        print(str(updatedCount) + ' pages updated' )
    if createdCount == 0 and updatedCount == 0:
        print('No pages needed to be created or updated' )

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--configfile')
    parser.add_argument('-x', '--ignore')
    args = parser.parse_args()

    configpath = args.configfile if args.configfile else 'incharge-podcaster.json'
    with open(configpath, mode='r', encoding='utf-8') as configfile:
        config = json.load(configfile)

    # Assign defaults if no folder settings are provided and convert relative to absolute paths
    config['episode-folder'] = os.path.abspath(
        config['episode-folder'] if 'episode-folder' in config else 'episode'
    )
    config['page-folder'] = os.path.abspath(
        config['page-folder'] if 'page-folder' in config else 'page'
    )
    if not os.path.exists(config['page-folder']):
        os.makedirs(config['page-folder'])

    GeneratePages(config)
