# Import podcast episodes from rss feeds
#!/usr/bin/env bash

# To help debugging....
#set -o xtrace
#clear
export IMPORT_RESULT=UNDEFINED

git config --global user.email "noreply@users.noreply.github.com"
git config --global user.name "import-workflow"
git config --global init.defaultBranch main

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

if git diff --staged --quiet
then
    echo "No changes"
    IMPORT_RESULT=NOCHANGES
else
    echo "Committing and pushing changes"
    git status
    git commit -m "Import podcast episodes from rss feeds"
    git push
    IMPORT_RESULT=PUSHED
fi
