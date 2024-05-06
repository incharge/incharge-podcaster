# Use the 'withastro' action to build on GitHub and deploy on GitHub Pages https://github.com/withastro/action
# Alternatively run this script.
# It assumes npm is already installed.
#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo Copying .md files
mkdir -p astrowind/src/content/post
cp md/*.md astrowind/src/content/post/  

echo Copying .vtt files
mkdir -p astrowind/public/transcript
cp vtt/*.vtt astrowind/public/transcript/
cp playlists.yaml astrowind/src/

echo Building Astro
cd "$SCRIPT_DIR/../astrowind"
npm run build
