# Import podcast episodes from rss feeds
#!/usr/bin/env bash

# To help debugging....
#set -o xtrace
#clear

# .github/workflows/import.yaml calls ./.github/workflows/hugo.yaml if IMPORT_RESULT=PUSHED
export IMPORT_RESULT=UNDEFINED

# Configure git
git config --global user.email "noreply@users.noreply.github.com"
git config --global user.name "import-workflow"
git config --global init.defaultBranch main

# Don't accidentally commit staged files
git diff --staged --quiet
if [ $? -ne 0 ]
then
    echo "ERROR: There are staged files"
    exit
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Import podcast episodes from rss feeds to yaml files
DATAPATH=$SCRIPT_DIR/../data/episode

# if ls $DATAPATH/*.yaml >/dev/null 2>&1
# then 
#     echo "Removing existing .yaml files from $DATAPATH"
#     rm $DATAPATH/*.yaml
# fi

python $SCRIPT_DIR/import.py \
    --spotify 'https://anchor.fm/s/822ba20/podcast/rss' \
    --youtube 'https://www.youtube.com/feeds/videos.xml?channel_id=UCTUcatGD6xu4tAcxG-1D4Bg' \
    --output "$DATAPATH"

if [ $? -ne 0 ]
then
    echo "ERROR: Failed to import episodes"
    exit
fi
exit

# Process yaml files into md files
SITEPATH=$SCRIPT_DIR/../content/episodes
python $SCRIPT_DIR/createpages.py \
    --input "$DATAPATH" \
    --output "$SITEPATH"

if [ $? -ne 0 ]
then
    echo "ERROR: Failed to generate pages"
    exit
fi

# If there are changes then commit them
git add "$DATAPATH"
git add "$SITEPATH"
if git diff --staged --quiet
then
    echo "No changes"
    IMPORT_RESULT=NOCHANGES
else
    echo "Committing and pushing changes"
    #echo "DEBUG-REMOTE"
    #git remote -v
    git commit -m "Import podcast episodes from rss feeds"
    git push
    #git remote -v
    IMPORT_RESULT=PUSHED
fi
