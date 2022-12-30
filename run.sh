#! /bin/bash
ROOT_PATH="`dirname \"$0\"`"
source $ROOT_PATH/venv/bin/activate
# virtualenv is now active.
python $ROOT_PATH/main.py
