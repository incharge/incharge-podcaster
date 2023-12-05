# Import podcast episodes from rss feeds
#!/usr/bin/env bash

# To help debugging....
#set -o xtrace
#clear

# .github/workflows/import.yaml calls ./.github/workflows/hugo.yaml if IMPORT_RESULT=PUSHED
export IMPORT_RESULT=UNDEFINED
# Recreate all files from scratch.  All existing episode .yaml an .md files are deleted before recreating
RECREATE=false
#RECREATE=true
# Commit and push changes?
#DEPLOY=false
DEPLOY=true

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR/.."

# Don't accidentally commit staged files
git diff --staged --quiet
if [ $? -ne 0 ]
then
    echo "ERROR: There are staged files"
    exit
fi

# Import podcast episodes from rss feeds to yaml files
DATAPATH=$SCRIPT_DIR/../yaml
mkdir -p $DATAPATH
if $RECREATE && ls $DATAPATH/*.yaml >/dev/null 2>&1
then
    echo "Removing existing .yaml files from $DATAPATH"
    rm $DATAPATH/*.yaml
fi

if $RECREATE
then
    YOUTUBE_PARAM='--youtubeapi=UUTUcatGD6xu4tAcxG-1D4Bg'
else
    YOUTUBE_PARAM='--youtuberss=https://www.youtube.com/feeds/videos.xml?channel_id=UCTUcatGD6xu4tAcxG-1D4Bg'
fi
python $SCRIPT_DIR/import.py \
    $YOUTUBE_PARAM \
    --spotify 'https://anchor.fm/s/822ba20/podcast/rss' \
    --output "$DATAPATH"
if [ $? -ne 0 ]
then
    echo "ERROR: Failed to import episodes"
    exit
fi

# Process yaml files into md files
SITEPATH=$SCRIPT_DIR/../md
mkdir -p $SITEPATH
if $RECREATE && ls SITEPATH/*.md >/dev/null 2>&1
then 
    echo "Removing existing .md files from $SITEPATH"
    rm $SITEPATH/*.md
fi
python $SCRIPT_DIR/createpages.py \
    --input "$DATAPATH" \
    --output "$SITEPATH"

if [ $? -ne 0 ]
then
    echo "ERROR: Failed to generate pages"
    exit
fi

if $DEPLOY
then
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
fi
