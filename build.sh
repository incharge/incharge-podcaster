# Use the 'withastro' action to build on GitHub and deploy on GitHub Pages https://github.com/withastro/action
# Alternatively run this script.
# It assumes npm is already installed.
#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
mkdir -p astrowind/src/content/post
cp playlists.yaml astrowind/src/
cp md/*.md astrowind/src/content/post/  
cd "$SCRIPT_DIR/../astrowind"
npm run build
