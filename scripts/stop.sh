#!/bin/sh

AISHA_DIR=/opt/aisha-on

PID=$(cat $AISHA_DIR/logs/pid.txt)
echo "Killing PID: $PID"
kill -9 $PID
rm -v $AISHA_DIR/logs/pid.txt
