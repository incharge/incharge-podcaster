#!/usr/bin/env bash
#set -o xtrace
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )"
cd ..
if [ ! -d .venv ]; then
    python -m venv .venv
    source .venv/Scripts/activate
    python -m pip install --upgrade pip
    python -m pip install -r incharge-podcaster/requirements.txt
fi
git config --global init.defaultBranch main
git config --global credential.helper wincred
git config pull.rebase false
