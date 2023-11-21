#!/usr/bin/env bash
#set -o xtrace
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )"
cd ..
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r script/requirements.txt
