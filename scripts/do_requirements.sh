#!/usr/bin/env bash


REQ_FILE='../requirements.txt'

source ~/.pyenv/versions/islnd/bin/activate
pip freeze > $REQ_FILE



