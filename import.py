import argparse
import os
import json
from fetcherrss import FetcherPlugin as FetcherRss
from fetcheryoutuberss import FetcherPlugin as FetcherYoutubeRss
from fetcheryoutubeapi import FetcherPlugin as FetcherYoutubeAPI
from fetchertranscript import FetcherPlugin as FetcherTranscript

# Merge 2 dictionaries recursively, so items in sub-dictionaries are merged
# If the same item exists in both, enhancer overwrites tgt
def merge_dicts(tgt, enhancer):
    for key, val in enhancer.items():
        if key not in tgt:
            tgt[key] = val
            continue

        if isinstance(val, dict):
            if not isinstance(tgt[key], dict):
                tgt[key] = dict()
            merge_dicts(tgt[key], val)
        else:
            tgt[key] = val
    return tgt

# If implementations need to use custom fetchers then some kind of plugin system is needed
#cls = __import__("rssfetcher")
# fetcher = Fetcher.factory(source["type"], config)
def fetchSource(name, source, config):
    fetcher = None
    if not 'type' in source:
        print(f"Data source configuration '{name}' is missing the 'type': {str(source)}")
    elif 'ignore' in source and source['ignore']:
        # print(f"Ignoring source': {str(source)}")
        pass
    elif source['type'] == 'rss':
        fetcher = FetcherRss(config)
    elif source['type'] == 'youtube-rss':
            fetcher = FetcherYoutubeRss(config)
    elif source['type'] == 'youtube-api':
        fetcher = FetcherYoutubeAPI(config)
    elif source['type'] == 'transcript':
        fetcher = FetcherTranscript(config)
    else:
        print(f"Invalid data source type for source '{name}': {source['type']}")

    if fetcher:
        print(f"Fetching from data source '{name}' ({source['type']})")
        fetcher.fetch(source)

def importer():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config')
    parser.add_argument('-o', '--override', action='store_true')
    parser.add_argument('-i', '--ignore')
    args = parser.parse_args()

    config = {}

    # Process command-line config
    if args.config is not None:
        try:
            config = eval(args.config)
        except Exception as error:
            print(f"Exception processing command line parameter: config ({type(error).__name__}): {error}")
            return

    # Load the config file
    if not args.override:
        if os.path.isfile('incharge-podcaster.json'):
            try:
                with open('incharge-podcaster.json', mode='r', encoding='utf-8') as configfile:
                    # Merge the command-line config so it overwrites any file config
                    config = merge_dicts(json.load(configfile), config)
            except Exception as error:
                print(f"Error reading the configuration file ({type(error).__name__}): {error}")
                return

    # Assign default if no episode folder setting is provided and convert relative to absolute path
    config['episode-folder'] = os.path.abspath(
        config['episode-folder'] if 'episode-folder' in config else 'episode'
    )

    # Process data sources defined in the config file
    for name, source in config["source"].items():
        fetchSource(name, source, config)

if __name__ == '__main__':
    importer()
