#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SCRIPT[0]}" )" &> /dev/null && pwd )

/usr/bin/env python3 -m venv venv
$SCRIPT_DIR/venv/bin/pip3 install -r $SCRIPT_DIR/requirements.txt
$SCRIPT_DIR/venv/bin/pip3 install -e $SCRIPT_DIR

read -p "Add run.sh to PATH as grader? [y/n]" -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    ln -s $SCRIPT_DIR/run.sh $HOME/.local/bin/grader
fi

read -p "Install VS Code extension? [y/n]" -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    code --install-extension $SCRIPT_DIR/vscode-extension/grader/grader-0.0.1.vsix
fi

