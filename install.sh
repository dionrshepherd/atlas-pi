#!/usr/bin/env bash
set -e

echo "source ./.bashrc"
echo "$ANCHOR_ID"
# todo if the above is not of length 4 it is borked
# todo yes no command
echo "source ./.bashrc"


apt install python3-pip
pip3 install setuptools
pip3 install awscli==1.11.18
pip3 install boto3
pip3 install pyserial

echo "run: ./.local/bin/aws configure"