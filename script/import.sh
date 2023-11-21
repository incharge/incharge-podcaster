#!/usr/bin/env bash
#set -o xtrace
#clear
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
DATAPATH=$SCRIPT_DIR/../data/episode

# if ls $DATAPATH/*.yaml >/dev/null 2>&1
# then 
#     echo "Removing existing yaml files from $DATAPATH"
#     rm $DATAPATH/*.yaml
# fi

python $SCRIPT_DIR/import.py \
    --spotify 'https://anchor.fm/s/822ba20/podcast/rss' \
    --youtube 'https://www.youtube.com/feeds/videos.xml?channel_id=UCTUcatGD6xu4tAcxG-1D4Bg' \
    --output "$DATAPATH"

git status
