#!/usr/bin/env bash

# set the environment variables that are needed
echo "Has a new user been added?"
echo "Have you changed the hostname to the anchor ID?"
echo "/etc/hostname & /etc/hosts"

export ANCHOR_ID="$(hostname)"
echo $ANCHOR_ID

echo "run install.sh"