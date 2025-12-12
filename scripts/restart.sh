#!/bin/sh

AISHA_DIR=/opt/aisha-on

$AISHA_DIR/scripts/stop.sh

$AISHA_DIR/scripts/run.sh
echo "Restarted Aisha"
