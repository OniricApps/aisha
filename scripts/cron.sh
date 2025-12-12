#!/bin/bash

# add the following line to crontab
# */10 * * * * /opt/aisha-on/scripts/cron.sh
# crontab -e

AISHA_DIR=/opt/aisha-on
PYTHON_ENV=/opt/aisha-on/.venv/bin/activate

# activate python environment
source $PYTHON_ENV

echo `date` >> $AISHA_DIR/logs/cron.log
cd $AISHA_DIR && python $AISHA_DIR/cron.py >> $AISHA_DIR/logs/cron.log

# Optional. Sent an email to the author with new chats every cron run
#if [ -f $AISHA_DIR/logs/new_chats.txt ]; then
#    mail -s "New chats" your@email.com < $AISHA_DIR/logs/new_chats.txt
#    echo "Sending email with new chats..." >> $AISHA_DIR/logs/cron.log
#    cat $AISHA_DIR/logs/new_chats.txt >> $AISHA_DIR/logs/cron.log
#    rm $AISHA_DIR/logs/new_chats.txt
#fi
