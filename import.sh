# Import podcast episodes from rss feeds
#!/usr/bin/env bash
# To help debugging....
# set -o xtrace
#clear

# .github/workflows/import.yaml calls ./.github/workflows/hugo.yaml if IMPORT_RESULT=PUSHED
export IMPORT_RESULT=UNDEFINED
# Recreate all files from scratch.  All existing episode .yaml an .md files are deleted before recreating
RECREATE=false
#RECREATE=true
# Commit and push changes?
if [ "${NODE_ENV:-production}" = "production" ]; then DEPLOY=true; else DEPLOY=false; fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR/.."

# Don't accidentally commit pre-existing changes
if $DEPLOY
then
    git diff --staged --quiet
    if [ $? -ne 0 ]
    then
        echo "ERROR: There are staged changes"
        exit
    fi
fi

# Import podcast episodes from rss feeds to yaml files
DATAPATH=$SCRIPT_DIR/../episode
mkdir -p $DATAPATH
# if $RECREATE
# then
#     echo "Removing existing episodes from $DATAPATH"
#     rm -rf $DATAPATH/
# fi

if $RECREATE
then
    python $SCRIPT_DIR/import.py "--config={ \"source\": { \"Youtube via API\": { \"ignore\": False }}}"
else
    python $SCRIPT_DIR/import.py
fi

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
python $SCRIPT_DIR/createpages.py

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
else
    echo 'Not checking for changes when not in production.'
fi
