import datetime
import re
import json
import codecs

# Remove um at the start of a sentence, and capitalise the next word
def remove_first_um(text, um):
    # Remove um from the beginning of the string
    pattern = '^' + um + ',? ([A-Za-z0-9])'
    text = re.sub(
        re.compile(pattern,flags=re.IGNORECASE),
        lambda pat: pat.group(1).upper(),
        text)

    # Remove um from the beginning of sentences i.e. after sentence ending punctuation
    pattern = '([.?!:]) ' + um + ',? ([A-Za-z0-9])'
    text = re.sub(
        re.compile(pattern,flags=re.IGNORECASE),
        lambda pat: pat.group(1) + ' ' + pat.group(2).upper(),
        text)

    # Replace comma-space-um-comma with comma
    text = re.sub(', ' + um + ',', ',', text)

    return text

# Remove all Ums
def remove_all_um(text, um):
    # Replace space-um-space with space
    text = re.sub(
        re.compile(' ' + um + ',?(?= )', flags=re.IGNORECASE),
        '',
        text)

    return text

# Remove ums from the given text
def DeUm(text, ums):
    if ums is None or len(ums) == 0:
        # Nothing to do
        return text

    # Keep removing ums from the start of sentences until none are removed
    new_length = len(text)
    old_length = new_length + 1
    while new_length < old_length:
        old_length = new_length
        for um in ums:
            text = remove_first_um(text, um)
        new_length = len(text)

    for um in ums:
        text = remove_all_um(text, um)

    return text

# def getEpisodeID(filename):
#     # match = re.search("^([^-]+)-", filename) 
#     # return match
#     filename = os.path.basename(filename)
#     return re.sub("\.[^.]*", "", filename)

# def getInterviewee(episodeID):
#     #title = ''
#     # TODO: catch file not found
#     path = os.path.join('yaml', episodeID + '.yaml')
#     with open(path, 'r', encoding='utf-8') as file:
#         dataDict = yaml.safe_load(file)
#         file.close()

#     # TODO: catch item not found
#     return dataDict['interviewee']

# See https://github.com/faangbait/aws-transcribe-transcript
def transcriptToText(inputFilename, dataDict, config, outputfile):

    # ums = ['um', 'uh', 'mhm']
    ums = config['ums'] if 'ums' in config else None

    # If there is episode specific config, and this episode is present, then find it
    episode = [episode for episode in config["episodes"] if episode['episodeid']==dataDict['episodeid']] if "episodes" in config else []
    # TODO: Check that episode contains 1 item
    if len(episode) == 0:
        # There is no config for this episode. Get the speakers from the title.
        speakers = dataDict['interviewee']
    else:
        # TODO: if len(episode)>1: warn about duplicate episode config
        speakers = speakers + episode[0]["interviewee"]

    speakers = config["defaults"]["interviewer"] + speakers

    # outputFilename = os.path.basename(inputFilename) + ".txt"
    #outputFilename = re.sub(r"\.[^.]*$", ".md", inputFilename)

    print ("Converting transcript file: ", inputFilename)
    with codecs.open(inputFilename, 'r', 'utf-8') as inputfile:
        data=json.loads(inputfile.read())
        labels = data['results']['speaker_labels']['segments']
        speaker_start_times={}
        for label in labels:
            for item in label['items']:
                #speaker_start_times[item['start_time']] =item['speaker_label']
                speaker_start_times[item['start_time']] = int(item['speaker_label'][4:])
                #print(int(item['speaker_label'][4:]))
        #print(speaker_start_times)
        items = data['results']['items']
        lines=[]
        line=''
        time=0
        speaker=None
        i=0
        for item in items:
            i=i+1
            content = item['alternatives'][0]['content']
            if item.get('start_time'):
                current_speaker=speaker_start_times[item['start_time']]
            elif item['type'] == 'punctuation':
                line = line+content
            if current_speaker != speaker:
                if speaker is not None:
                    lines.append({'speaker':speaker, 'line':line, 'time':time})
                line=content
                speaker=current_speaker
                time=item['start_time']
            elif item['type'] != 'punctuation':
                line = line + ' ' + content
        lines.append({'speaker':speaker, 'line':line,'time':time})
        sorted_lines = sorted(lines,key=lambda k: float(k['time']))
        for line_data in sorted_lines:
            outputfile.write('<time>' + str(datetime.timedelta(seconds=int(round(float(line_data['time']))))) + '</time> ' \
                + speakers[line_data.get('speaker')] + ': ' \
                + DeUm(line_data.get('line'), ums) \
                + '\n\n'
            )
