#! /bin/bash
ROOT_PATH="`dirname \"$0\"`"
# Activate virtual env if exists
if [[ -d "$ROOT_PATH/.venv/" ]]; then
  source $ROOT_PATH/.venv/bin/activate
fi
python3 $ROOT_PATH/main.py "$@"  # Pass all the args
