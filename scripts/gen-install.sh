#!/bin/sh

# give execution permissions to scripts before creating tarball
chmod +x scripts/*.sh

# Compress current version files
tar -zcvf aisha-v0.7.tar.gz *.py templates/* static/* scripts/*

# Upload this tarball to the server
scp aisha-v0.7.tar.gz scripts/install.sh aisha@yourserver.com:/home/aisha/app/
# Replace 'yourserver.com' and 'aisha' with your server address and username
echo "Upload complete. Connect to your server and run install.sh to install or update Aisha."
