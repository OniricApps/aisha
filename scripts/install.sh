#!/bin/sh

AISHA_DIR=/opt/aisha-on
OLD_VERSION=0.6
NEW_VERSION=0.7

# uninstall

# kill process
PID=$(cat $AISHA_DIR/logs/pid.txt)
echo "Killing PID: $PID"
kill -9 $PID
rm -v $AISHA_DIR/logs/pid.txt

# backup old version
echo "Backing up old version..."
tar -zcvf aisha-v$OLD_VERSION-backup.tar.gz $AISHA_DIR/*

# delete files
echo "Deleting old version files..."
rm -v $AISHA_DIR/*.py $AISHA_DIR/*.sh $AISHA_DIR/templates/* $AISHA_DIR/static/* $AISHA_DIR/scripts/*.sh

# unzip new version
echo "Unzipping new version..."
cp aisha-v$NEW_VERSION.tar.gz $AISHA_DIR
cd $AISHA_DIR && tar -zxvf aisha-v$NEW_VERSION.tar.gz

# execution permissions to scripts
echo "Setting execution permissions to scripts..."
chmod +x $AISHA_DIR/scripts/*.sh

# run
echo "Running new version..."
$AISHA_DIR/scripts/run.sh

# wait 5 seconds and check $AISHA_DIR/logs/pid.txt
echo "Wait 5 seconds and check $AISHA_DIR/logs/pid.txt"
sleep 5
PID=$(cat $AISHA_DIR/logs/pid.txt)
echo "PID: $PID"
