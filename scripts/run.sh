#!/bin/bash

AISHA_DIR=/opt/aisha-on
PYTHON_ENV=/opt/aisha-on/.venv/bin/activate

# activate python environment
source $PYTHON_ENV

cd $AISHA_DIR && nohup python $AISHA_DIR/app.py >> /tmp/aisha-on-v0.7.log 2>&1 &
