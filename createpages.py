import yaml
import os
import argparse
import datetime
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def CreatePage(input, output):
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

        # file.write("{{< show " + dataDict['id'] + " >}}\n")
        if (not 'transcript' in dataDict):
            file.write(dataDict['shownotes'])
        else:
            file.write('<a name="top"></a>[Jump to transcript](#transcript)\n')
            file.write('## Show notes\n')
            file.write(dataDict['shownotes'])
            file.write('\n')
            file.write('[Back to top](#top)\n')
            file.write('<a name="transcript"></a>\n')
            file.write('## Transcript\n')
            try:
                with open(dataDict['transcript'], 'r', encoding='utf-8') as transcript:
                    for line in transcript:                
                        file.write(line)
            except IOError as e:
                eprint("I/O error({0}): {1}".format(e.errno, e.strerror))
            except: #handle other exceptions such as attribute errors
                eprint("Unexpected error:", sys.exc_info()[0])
            file.write('[Back to top](#top)\n')

def CreatePages(input, output):
    with os.scandir(input) as episodes:
        for episode in episodes:
            if episode.name.endswith('.yaml') and episode.is_file():
                CreatePage(episode.path, output)

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input')
parser.add_argument('-o', '--output')
args = parser.parse_args()

CreatePages(args.input, args.output)
