# Import podcast episodes from rss feeds
#!/usr/bin/env bash

# To help debugging....
#set -o xtrace
#clear

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

DATAPATH=$SCRIPT_DIR/../data/episode
python $SCRIPT_DIR/import.py \
    --spotify 'https://anchor.fm/s/822ba20/podcast/rss' \
    --youtube 'https://www.youtube.com/feeds/videos.xml?channel_id=UCTUcatGD6xu4tAcxG-1D4Bg' \
    --output "$DATAPATH"
git add "$DATAPATH"

SITEPATH=$SCRIPT_DIR/../content/episodes
python $SCRIPT_DIR/createpages.py \
    --input "$DATAPATH" \
    --output "$SITEPATH"
git add "$SITEPATH"

git commit -m "Import podcast episodes from rss feeds"
